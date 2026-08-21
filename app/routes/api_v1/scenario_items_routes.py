"""
``/api/v1/scenarios/<id>/items`` — bulk import + item-level delete.

This is a thin wrapper around the same import path the one-shot create uses,
so the two surfaces stay in lockstep. Use this endpoint to add more items to
an existing scenario without re-creating it.
"""

from __future__ import annotations

import logging

from flask import g, jsonify, request

from auth.decorators import api_key_or_token_required, require_api_scope
from db import db
from db.models import EvaluationItem, RatingScenarios, ScenarioItems
from decorators.error_handler import (
    ConflictError,
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from schemas.api_v1.scenario_api import LlarsNativeEnvelope
from services.api_v1_scenario_service import _import_native_items
from services.permission_service import PermissionService

from . import api_v1_bp
from .scenarios_routes import _validate_request

logger = logging.getLogger(__name__)


def _require_owner(scenario: RatingScenarios) -> None:
    user = g.authentik_user
    if PermissionService.user_has_role(user.username, "admin"):
        return
    if scenario.created_by != user.username:
        # SECURITY (M1): non-owner ⇒ 404 (not 409) so we don't leak whether
        # the scenario ID exists. Body must match the "missing scenario"
        # branch so the two cases are indistinguishable to the caller.
        raise NotFoundError(f"Scenario {scenario.id} not found")


@api_v1_bp.route("/scenarios/<int:scenario_id>/items", methods=["POST"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.items")
def bulk_import_items(scenario_id: int):
    """
    Append items to an existing scenario.

    Body: a ``LlarsNativeEnvelope`` (same shape used inside
    ``ScenarioCreateRequest.items``). Items are appended — no dedup against
    existing scenario items by chat_id, because the v1 contract treats each
    POST as authoritative for the new items it carries.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    _require_owner(scenario)

    envelope = _validate_request(LlarsNativeEnvelope, request.get_json(silent=True))
    if not envelope.items:
        return jsonify({
            "success": True,
            "items_created": 0,
            "features_created": 0,
            "item_ids": [],
        })

    # Scenario parts (labeling phases): with resolved parts every new item
    # MUST be assigned to exactly one part — a missing part_id would silently
    # break the partition invariant the study relies on.
    from services.evaluation.scenario_parts_service import (
        PartsConfigError,
        ScenarioPartsService,
    )
    parts_cfg = ScenarioPartsService.get_parts_config(scenario)
    parts_active = bool(parts_cfg) and ScenarioPartsService.is_resolved(parts_cfg)
    if parts_active and not envelope.part_id:
        raise ApiValidationError(
            "This scenario is partitioned into parts; part_id is required "
            "when adding items (see GET /api/v1/scenarios/<id>/parts)"
        )
    if envelope.part_id and not parts_active:
        raise ApiValidationError(
            "part_id given but the scenario has no resolved parts config"
        )

    try:
        items_created, features_created = _import_native_items(
            scenario, envelope, scenario.function_type_id
        )
        # Flushed (not yet committed) — resolve the new ids now so the part
        # assignment lands in the SAME transaction as the items themselves.
        new_item_ids = list(reversed([
            si.item_id
            for si in ScenarioItems.query.filter_by(scenario_id=scenario.id)
            .order_by(ScenarioItems.id.desc())
            .limit(items_created)
            .all()
        ]))
        if parts_active:
            try:
                ScenarioPartsService.append_items_to_part(
                    scenario, envelope.part_id, new_item_ids
                )
            except PartsConfigError as exc:
                raise ApiValidationError(str(exc))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        "success": True,
        "items_created": items_created,
        "features_created": features_created,
        "item_ids": new_item_ids,
        **({"part_id": envelope.part_id} if envelope.part_id else {}),
    }), 201


@api_v1_bp.route(
    "/scenarios/<int:scenario_id>/items/<int:item_id>", methods=["DELETE"]
)
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.items")
def delete_scenario_item(scenario_id: int, item_id: int):
    """
    Detach an item from a scenario, then drop the EvaluationItem entirely
    if no other scenario references it. Mirrors the cascade behaviour of
    `DELETE /api/v1/scenarios/<id>`.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    _require_owner(scenario)

    link = ScenarioItems.query.filter_by(
        scenario_id=scenario_id, item_id=item_id
    ).first()
    if not link:
        raise NotFoundError(
            f"Item {item_id} is not linked to scenario {scenario_id}"
        )

    db.session.delete(link)
    db.session.flush()

    other_links = ScenarioItems.query.filter_by(item_id=item_id).count()
    if other_links == 0:
        # Clear children that have no ON DELETE CASCADE on item_id, then
        # drop the parent row (mirrors scenarios_routes.delete_scenario).
        from db.models import Feature, Message
        Feature.query.filter_by(item_id=item_id).delete(
            synchronize_session=False
        )
        Message.query.filter_by(item_id=item_id).delete(
            synchronize_session=False
        )
        EvaluationItem.query.filter_by(item_id=item_id).delete(
            synchronize_session=False
        )

    db.session.commit()
    return jsonify({"success": True, "deleted_item_id": item_id})
