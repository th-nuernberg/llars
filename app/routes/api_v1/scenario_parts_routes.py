"""
``/api/v1/scenarios/<id>/parts`` — Teile/Phasen eines Labeling-Szenarios.

API-key counterpart of the owner panel under Scenarios → Settings → Parts,
so calibration studies can be operated headlessly (unlock the next phase
after the alignment meeting / IRR gate without opening the UI):

- GET  → status of all parts (item counts, per-assessor progress, locked,
         copilot flag, resolved state)
- PUT /<part_id> → partial update: locked / copilot / name / order.
         item_ids are deliberately NOT editable here (partition invariant —
         see design doc §4); adding items goes through
         POST /api/v1/scenarios/<id>/items with part_id.

Assessor invisibility is not a concern on these routes: they are owner-only
(non-owners get a 404, same masking as the copilot routes).
"""

from __future__ import annotations

import logging

from flask import g, jsonify, request

from auth.decorators import api_key_or_token_required, require_api_scope
from db import db
from db.models import RatingScenarios
from decorators.error_handler import (
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from services.evaluation.labeling_types import is_labeling_type
from services.evaluation.scenario_parts_service import (
    PartsConfigError,
    ScenarioPartsService,
)
from services.permission_service import PermissionService

from . import api_v1_bp

logger = logging.getLogger(__name__)

LABELING_FUNCTION_TYPE_ID = 7


def _require_owner(scenario: RatingScenarios) -> None:
    user = g.authentik_user
    if PermissionService.user_has_role(user.username, "admin"):
        return
    if scenario.created_by != user.username:
        # SECURITY (M1): mask non-owner access as 404 (no scenario-ID oracle)
        raise NotFoundError(f"Scenario {scenario.id} not found")


def _get_labeling_scenario(scenario_id: int) -> RatingScenarios:
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    _require_owner(scenario)
    if not is_labeling_type(scenario.function_type_id):
        raise ApiValidationError(
            "Parts are only available for labeling scenarios"
        )
    return scenario


@api_v1_bp.route("/scenarios/<int:scenario_id>/parts", methods=["GET"])
@api_key_or_token_required
@require_api_scope("scenario:read")
@handle_api_errors(logger_name="api_v1.parts")
def get_parts_status_v1(scenario_id: int):
    scenario = _get_labeling_scenario(scenario_id)
    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        **ScenarioPartsService.get_parts_status(scenario),
    })


@api_v1_bp.route(
    "/scenarios/<int:scenario_id>/parts/<part_id>", methods=["PUT"]
)
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.parts")
def update_part_v1(scenario_id: int, part_id: str):
    """Partial update of one part (unlock a phase, toggle its copilot, …).

    Unlocking is the study gate: the next calibration phase becomes visible
    to assessors on their next session load — for them it just looks like
    new items arrived.
    """
    scenario = _get_labeling_scenario(scenario_id)
    body = request.get_json(silent=True) or {}
    if not body:
        raise ApiValidationError(
            "Request body must contain at least one editable field "
            "(locked, copilot, name, order)"
        )
    try:
        ScenarioPartsService.update_part(scenario, part_id, body)
    except PartsConfigError as exc:
        raise ApiValidationError(str(exc))
    db.session.commit()

    # Progress caches key on item visibility — mark dirty so the hub/stats
    # pick up the newly unlocked items promptly.
    try:
        from services.scenario_stats_cache_service import mark_dirty
        mark_dirty(scenario_id)
    except Exception:
        pass

    logger.info(
        "[api_v1.parts] Updated part '%s' of scenario %s: %s",
        part_id, scenario_id, body,
    )
    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        **ScenarioPartsService.get_parts_status(scenario),
    })
