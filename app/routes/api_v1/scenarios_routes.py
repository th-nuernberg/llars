"""
``/api/v1/scenarios`` — top-level scenario CRUD.

Auth: every route is gated by ``@api_key_or_token_required`` (sets
``g.api_key_scopes``) followed by ``@require_api_scope(...)``. List/read
require ``scenario:read``; create/patch/delete require ``scenario:write``.

This is intentionally a thin glue layer:
    - request validation lives in ``schemas/api_v1/scenario_api.py``
    - business logic lives in ``services/api_v1_scenario_service.py``
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import g, jsonify, request
from pydantic import ValidationError

from auth.decorators import api_key_or_token_required, require_api_scope
from db import db
from db.models import RatingScenarios, ReferralLink, ScenarioItems, ScenarioUsers
from decorators.error_handler import (
    ConflictError,
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from schemas.api_v1.scenario_api import (
    ItemImportResponse,
    ReferralLinkResponse,
    ScenarioCreateRequest,
    ScenarioPatchRequest,
    ScenarioResponse,
)
from schemas.evaluation_data_schemas import EvaluationType
from services.api_v1_scenario_service import (
    ApiV1Error,
    ApiV1NotFound,
    create_scenario_one_shot,
)

from . import api_v1_bp

logger = logging.getLogger(__name__)


# ===========================================================================
# Helpers
# ===========================================================================

# Mirror of services._TYPE_TO_FUNCTION_ID, inverted.
_FUNCTION_ID_TO_TYPE = {
    1: EvaluationType.RANKING,
    2: EvaluationType.RATING,
    3: EvaluationType.MAIL_RATING,
    4: EvaluationType.COMPARISON,
    5: EvaluationType.AUTHENTICITY,
    7: EvaluationType.LABELING,
    # 8 was missing here for a long time: the forward map in the service had it
    # but this inverse one did not, so the v1 serializer silently reported
    # communication_comparison scenarios as "rating". Fixed together with 9 —
    # both directions must always be updated as a pair.
    8: EvaluationType.COMMUNICATION_COMPARISON,
    9: EvaluationType.CONVERSATION_LABELING,
}


def _validate_request(model_cls, raw):
    """Run a Pydantic model on the incoming JSON and turn validation errors
    into the project-standard 400 the error_handler decorator emits.

    We re-raise as the project's ``ValidationError`` so the response shape
    matches every other v0 endpoint (single error envelope, no Pydantic
    leakage)."""
    try:
        return model_cls.model_validate(raw or {})
    except ValidationError as exc:
        # `exc.errors()` may carry non-JSON-safe values inside `ctx`
        # (e.g. the original ValueError from a `field_validator`). Strip
        # those before passing to ApiValidationError, otherwise the
        # error_handler decorator's jsonify() blows up with a
        # TypeError ("Object of type ValueError is not JSON serializable")
        # and the client gets an HTML 500 instead of our structured 400.
        safe_errors = []
        for err in exc.errors():
            safe = {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            ctx = err.get("ctx") or {}
            if ctx:
                safe["ctx"] = {k: str(v) for k, v in ctx.items()}
            safe_errors.append(safe)

        first = safe_errors[0] if safe_errors else {}
        loc = ".".join(str(x) for x in first.get("loc", []))
        msg = first.get("msg", "validation error")
        detail = f"{loc}: {msg}" if loc else msg
        raise ApiValidationError(
            f"Invalid request body — {detail}",
            details={"errors": safe_errors},
        )


def _scenario_to_response(
    scenario: RatingScenarios,
    *,
    referral_link: Optional[ReferralLink] = None,
    items_imported: Optional[tuple[int, int]] = None,
    item_ids: Optional[list[int]] = None,
) -> dict:
    """Serialize a RatingScenarios row into the v1 response shape."""
    eval_type = _FUNCTION_ID_TO_TYPE.get(
        scenario.function_type_id, EvaluationType.RATING
    )
    config_json = scenario.config_json or {}

    item_count = ScenarioItems.query.filter_by(scenario_id=scenario.id).count()
    assessor_count = (
        ScenarioUsers.query
        .filter_by(scenario_id=scenario.id)
        .filter(ScenarioUsers.evaluation_role == "assessor")
        .count()
    )

    referral_resp = None
    if referral_link is not None:
        referral_resp = ReferralLinkResponse(
            id=referral_link.id,
            slug=referral_link.slug,
            code=referral_link.code,
            label=referral_link.label,
            role_name=referral_link.role_name,
            target_scenario_id=referral_link.target_scenario_id,
            is_active=referral_link.is_active,
        )

    items_resp = None
    if items_imported is not None:
        created, features = items_imported
        items_resp = ItemImportResponse(
            items_created=created,
            features_created=features,
            item_ids=item_ids or [],
        )

    resp = ScenarioResponse(
        id=scenario.id,
        name=scenario.scenario_name,
        description=config_json.get("description"),
        function_type_id=scenario.function_type_id,
        evaluation_type=eval_type,
        created_by=scenario.created_by,
        config_json=config_json,
        item_count=item_count,
        assessor_count=assessor_count,
        archived=bool(config_json.get("archived", False)),
        created_at=(
            scenario.timestamp.isoformat() if scenario.timestamp else None
        ),
        llm1_model=scenario.llm1_model,
        llm2_model=scenario.llm2_model,
        referral_link=referral_resp,
        items_imported=items_resp,
    )
    return resp.model_dump(mode="json")


def _cascade_cleanup_for_scenario(scenario_id: int, item_ids: list[int]) -> None:
    """Bulk-delete every child row that would otherwise block a hard
    delete of ``rating_scenarios.id = scenario_id``.

    Why this exists
    ---------------
    Several tables declare ``scenario_id`` as ``NOT NULL`` with a plain
    FK (no ``ondelete='CASCADE'`` and no SQLAlchemy session-level
    cascade). When SQLAlchemy processes ``db.session.delete(scenario)``
    it tries to detach each related row by setting their ``scenario_id``
    to NULL — which fails with ``IntegrityError: Column 'scenario_id'
    cannot be null``. Same class of bug for ``user_feature_rankings``
    and ``user_feature_ratings``, which point at ``features.feature_id``
    and would block the orphan-item sweep that runs after the delete.

    The cure is to issue plain ``DELETE`` statements in the right order
    before asking SQLAlchemy to drop the parent rows. We do bulk DELETEs
    with ``synchronize_session=False`` because we don't need ORM-level
    cascade events here — the scenario is on its way out anyway.

    The list of child tables was derived from the
    ``information_schema.KEY_COLUMN_USAGE`` view (see also CLAUDE.md
    troubleshooting section) plus the prod incident on 2026-05-12 where
    the v1 DELETE endpoint kept tripping on
    ``user_feature_rankings_ibfk_2``.
    """
    from db.models.scenario import (
        Feature,
        ItemComparisonEvaluation,
        ItemDimensionRating,
        ItemLabelingEvaluation,
        ScenarioItemDistribution,
        ScenarioItems,
        ScenarioUsers,
        UserFeatureRanking,
        UserFeatureRating,
    )

    # ---- 1) Feature-bound user rows (block the orphan-feature sweep)
    if item_ids:
        feature_ids = [
            fid for (fid,) in db.session.query(Feature.feature_id)
            .filter(Feature.item_id.in_(item_ids)).all()
        ]
        if feature_ids:
            UserFeatureRanking.query.filter(
                UserFeatureRanking.feature_id.in_(feature_ids)
            ).delete(synchronize_session=False)
            UserFeatureRating.query.filter(
                UserFeatureRating.feature_id.in_(feature_ids)
            ).delete(synchronize_session=False)

    # ---- 2) Evaluation rows that have NOT NULL scenario_id
    #
    # These would otherwise trigger the
    # "UPDATE … SET scenario_id=NULL" SQLAlchemy emits on parent delete.
    ItemComparisonEvaluation.query.filter_by(
        scenario_id=scenario_id
    ).delete(synchronize_session=False)
    ItemLabelingEvaluation.query.filter_by(
        scenario_id=scenario_id
    ).delete(synchronize_session=False)
    ItemDimensionRating.query.filter_by(
        scenario_id=scenario_id
    ).delete(synchronize_session=False)

    # ---- 3) Optional auxiliary tables. Wrapped in best-effort so the
    # delete doesn't bomb in environments where the table doesn't exist
    # yet (older schemas) or the model isn't loaded.
    _bulk_delete_by_scenario(
        scenario_id,
        [
            ("comparison_sessions", "scenario_id"),
            ("llm_usage_tracking", "scenario_id"),
            ("llm_task_results", "scenario_id"),
            ("llm_eval_runs", "scenario_id"),
            ("scenario_stats_jobs", "scenario_id"),
        ],
    )

    # ---- 4) Distribution / membership / item-link rows.
    ScenarioItemDistribution.query.filter_by(
        scenario_id=scenario_id
    ).delete(synchronize_session=False)
    ScenarioUsers.query.filter_by(
        scenario_id=scenario_id
    ).delete(synchronize_session=False)
    ScenarioItems.query.filter_by(
        scenario_id=scenario_id
    ).delete(synchronize_session=False)

    # ---- 5) Detach (don't delete) generation / pipeline records that
    # only *reference* the scenario as a source — those belong to a
    # separate lifecycle and shouldn't disappear with the scenario.
    _bulk_null_by_scenario(
        scenario_id,
        [
            ("generation_jobs", "source_scenario_id"),
            ("generation_jobs", "target_scenario_id"),
            ("pipeline_iterations", "eval_scenario_id"),
            ("pipeline_runs", "source_scenario_id"),
        ],
    )


def _bulk_delete_by_scenario(scenario_id: int, table_columns: list[tuple[str, str]]) -> None:
    """Best-effort ``DELETE FROM <table> WHERE <col> = scenario_id``.

    Uses raw SQL so we don't need to import + keep in sync every model
    class. Silently no-ops if the table is missing (older schemas).
    """
    from sqlalchemy import text
    for table, column in table_columns:
        try:
            db.session.execute(
                text(f"DELETE FROM {table} WHERE {column} = :sid"),
                {"sid": scenario_id},
            )
        except Exception as exc:
            logger.debug("cascade-cleanup skipped %s.%s: %s", table, column, exc)
            # Re-raise on schema-shape errors so we don't silently leak data;
            # only swallow "table missing" style ones via the rollback below.
            db.session.rollback()


def _bulk_null_by_scenario(scenario_id: int, table_columns: list[tuple[str, str]]) -> None:
    """Best-effort ``UPDATE <table> SET <col>=NULL WHERE <col> = scenario_id``.

    For tables where the scenario is just a back-reference and the row
    itself shouldn't disappear (e.g. generation_jobs, pipeline_runs).
    """
    from sqlalchemy import text
    for table, column in table_columns:
        try:
            db.session.execute(
                text(
                    f"UPDATE {table} SET {column} = NULL WHERE {column} = :sid"
                ),
                {"sid": scenario_id},
            )
        except Exception as exc:
            logger.debug("cascade-detach skipped %s.%s: %s", table, column, exc)
            db.session.rollback()


def _user_can_read_scenario(scenario: RatingScenarios, user) -> bool:
    """Anyone with scenario:read can list, but reading a specific scenario
    requires either being its creator, an assessor on it, or holding the
    admin role. This mirrors the UI's access-control model."""
    if user is None:
        return False
    from services.permission_service import PermissionService
    if PermissionService.user_has_role(user.username, "admin"):
        return True
    if scenario.created_by == user.username:
        return True
    membership = ScenarioUsers.query.filter_by(
        scenario_id=scenario.id, user_id=user.id
    ).first()
    return membership is not None


# ===========================================================================
# Routes
# ===========================================================================


@api_v1_bp.route("/scenarios", methods=["GET"])
@api_key_or_token_required
@require_api_scope("scenario:read")
@handle_api_errors(logger_name="api_v1.scenarios")
def list_scenarios():
    """
    List scenarios visible to the authenticated user.

    Admins see everything; everyone else sees scenarios they created or
    are members of. Pagination is offset-based via ``?limit=&offset=``.
    """
    user = g.authentik_user
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = max(int(request.args.get("offset", 0)), 0)

    from services.permission_service import PermissionService
    is_admin = PermissionService.user_has_role(user.username, "admin")

    base_q = RatingScenarios.query
    if not is_admin:
        # Owner OR member-via-ScenarioUsers.
        member_subq = (
            db.session.query(ScenarioUsers.scenario_id)
            .filter(ScenarioUsers.user_id == user.id)
            .subquery()
        )
        base_q = base_q.filter(
            db.or_(
                RatingScenarios.created_by == user.username,
                RatingScenarios.id.in_(member_subq),
            )
        )

    total = base_q.count()
    rows = (
        base_q.order_by(RatingScenarios.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return jsonify({
        "success": True,
        "scenarios": [_scenario_to_response(s) for s in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@api_v1_bp.route("/scenarios", methods=["POST"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.scenarios")
def create_scenario():
    """
    One-shot scenario create.

    Body is ``ScenarioCreateRequest``. Returns 201 with the materialised
    scenario including referral-link details and import counts.
    """
    payload = _validate_request(ScenarioCreateRequest, request.get_json(silent=True))
    user = g.authentik_user

    try:
        scenario = create_scenario_one_shot(payload, user.username)
    except ApiV1NotFound as exc:
        raise NotFoundError(str(exc))
    except ApiV1Error as exc:
        raise ApiValidationError(str(exc))

    items_imported = getattr(scenario, "_api_v1_items_imported", None)
    item_ids = [
        si.item_id for si in
        ScenarioItems.query.filter_by(scenario_id=scenario.id).all()
    ] if items_imported else []

    referral_link = None
    if payload.referral_link is not None:
        referral_link = (
            ReferralLink.query
            .filter_by(slug=payload.referral_link.slug.lower())
            .first()
        )

    return jsonify({
        "success": True,
        "scenario": _scenario_to_response(
            scenario,
            referral_link=referral_link,
            items_imported=items_imported,
            item_ids=item_ids,
        ),
    }), 201


@api_v1_bp.route("/scenarios/<int:scenario_id>", methods=["GET"])
@api_key_or_token_required
@require_api_scope("scenario:read")
@handle_api_errors(logger_name="api_v1.scenarios")
def get_scenario(scenario_id: int):
    """Read a single scenario by ID. 404 if invisible to the caller."""
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario or not _user_can_read_scenario(scenario, g.authentik_user):
        raise NotFoundError(f"Scenario {scenario_id} not found")

    referral_link = (
        ReferralLink.query.filter_by(target_scenario_id=scenario.id).first()
    )
    return jsonify({
        "success": True,
        "scenario": _scenario_to_response(scenario, referral_link=referral_link),
    })


@api_v1_bp.route("/scenarios/<int:scenario_id>", methods=["PATCH"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.scenarios")
def patch_scenario(scenario_id: int):
    """
    Partial update. Only the scenario owner (or admin) may PATCH.

    `eval_config` is intentionally NOT patchable here — see the
    ``ScenarioPatchRequest`` docstring.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    user = g.authentik_user
    from services.permission_service import PermissionService
    is_admin = PermissionService.user_has_role(user.username, "admin")
    if not is_admin and scenario.created_by != user.username:
        # SECURITY (M1): non-owners must see the same response as for a
        # nonexistent scenario, otherwise a 409 vs 404 differential leaks
        # whether `scenario_id` is a real ID owned by someone else.
        raise NotFoundError(f"Scenario {scenario_id} not found")

    payload = _validate_request(ScenarioPatchRequest, request.get_json(silent=True))

    if payload.name is not None:
        scenario.scenario_name = payload.name
    if payload.llm1_model is not None:
        scenario.llm1_model = payload.llm1_model
    if payload.llm2_model is not None:
        scenario.llm2_model = payload.llm2_model

    cfg = dict(scenario.config_json or {})
    if payload.description is not None:
        cfg["description"] = payload.description
    if payload.archived is not None:
        cfg["archived"] = payload.archived
    scenario.config_json = cfg

    db.session.commit()
    return jsonify({
        "success": True,
        "scenario": _scenario_to_response(scenario),
    })


@api_v1_bp.route("/scenarios/<int:scenario_id>", methods=["DELETE"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.scenarios")
def delete_scenario(scenario_id: int):
    """
    Hard-delete a scenario (cascade-deletes ScenarioUsers, ScenarioItems,
    distributions, comparison sessions). Orphan EvaluationItems are cleaned
    up by the existing scenario_crud.delete path; we replicate the trim
    here to keep the v1 service self-contained.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    user = g.authentik_user
    from services.permission_service import PermissionService
    is_admin = PermissionService.user_has_role(user.username, "admin")
    if not is_admin and scenario.created_by != user.username:
        # SECURITY (M1): mask non-owner access as 404, see patch handler.
        raise NotFoundError(f"Scenario {scenario_id} not found")

    # Remember the items we owned so we can drop the ones now orphaned.
    item_ids = [
        si.item_id
        for si in ScenarioItems.query.filter_by(scenario_id=scenario.id).all()
    ]

    # ------------------------------------------------------------------
    # Full cascade cleanup. Several child tables have a NOT NULL
    # `scenario_id` FK without a session-level ON DELETE rule, so
    # ``db.session.delete(scenario)`` would otherwise emit
    # ``UPDATE child SET scenario_id=NULL`` and bomb with IntegrityError
    # ("Column 'scenario_id' cannot be null"). Same class of bug for
    # ``user_feature_rankings`` / ``user_feature_ratings`` which point
    # at ``features.feature_id`` and block the orphan-item sweep below.
    # We bulk-delete everything in dependency order *before* asking
    # SQLAlchemy to drop the scenario row.
    # ------------------------------------------------------------------
    _cascade_cleanup_for_scenario(scenario.id, item_ids)

    # Detach any referral link that auto-enrolled into this scenario.
    ReferralLink.query.filter_by(target_scenario_id=scenario.id).update(
        {"target_scenario_id": None}, synchronize_session=False
    )

    db.session.delete(scenario)
    db.session.flush()

    # Sweep orphan EvaluationItems (no remaining ScenarioItems link).
    # `features` and `messages` have no ON DELETE CASCADE on item_id, so we
    # have to clear them ourselves before dropping the parent rows.
    if item_ids:
        from db.models import EvaluationItem, Feature, Message
        still_linked = {
            r[0] for r in
            db.session.query(ScenarioItems.item_id)
            .filter(ScenarioItems.item_id.in_(item_ids))
            .all()
        }
        orphans = [iid for iid in item_ids if iid not in still_linked]
        if orphans:
            Feature.query.filter(
                Feature.item_id.in_(orphans)
            ).delete(synchronize_session=False)
            Message.query.filter(
                Message.item_id.in_(orphans)
            ).delete(synchronize_session=False)
            EvaluationItem.query.filter(
                EvaluationItem.item_id.in_(orphans)
            ).delete(synchronize_session=False)

    db.session.commit()
    return jsonify({"success": True, "deleted_id": scenario_id})


@api_v1_bp.route("/scenarios/<int:scenario_id>/archive", methods=["POST"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.scenarios")
def archive_scenario(scenario_id: int):
    """Soft-archive (toggle the ``config_json.archived`` flag). Idempotent."""
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    user = g.authentik_user
    from services.permission_service import PermissionService
    is_admin = PermissionService.user_has_role(user.username, "admin")
    if not is_admin and scenario.created_by != user.username:
        # SECURITY (M1): mask non-owner access as 404, see patch handler.
        raise NotFoundError(f"Scenario {scenario_id} not found")

    cfg = dict(scenario.config_json or {})
    archived = bool((request.get_json(silent=True) or {}).get("archived", True))
    cfg["archived"] = archived
    scenario.config_json = cfg
    db.session.commit()
    return jsonify({
        "success": True,
        "scenario": _scenario_to_response(scenario),
    })
