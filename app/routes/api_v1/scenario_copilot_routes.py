"""
``/api/v1/scenarios/<id>/copilot`` — labeling co-pilot configuration + control.

API-key counterpart of the owner panel under Scenarios → Settings → Co-Pilot,
so studies can be operated headlessly (the UI routes are session-only):

- GET    → generation status (counts, prompt_version, running)
- PUT    → update the user-editable config subset; prompt versioning and the
           hidden-control salt are handled server-side by
           LabelingCopilotService.normalize_config_on_write (same as the UI)
- POST /generate → clear error records and enqueue (re-)generation; items
           cached for the CURRENT prompt version are skipped by the runner

``PUT /api/v1/scenarios/<id>/labeling-config`` lives here too: it switches
question-first labeling (``questions``) and the second choice
(``second_choice``) on/off headlessly. The generic scenario PUT is
session-only and the v1 PATCH refuses ``eval_config``, so study scripts had
no API-key path to these settings (VRM study, 2026-09-15).
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
from services.evaluation.labeling_copilot_service import LabelingCopilotService
from services.evaluation.labeling_types import is_labeling_type
from services.permission_service import PermissionService

from . import api_v1_bp

logger = logging.getLogger(__name__)

LABELING_FUNCTION_TYPE_ID = 7

# The user-editable subset; prompt_version/prompt_history/hidden_control_salt
# are server-managed and deliberately NOT accepted from clients.
_EDITABLE_FIELDS = {
    "enabled", "model_id", "prompt", "codebook", "top_k", "hidden_control_ratio",
}


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
            "The co-pilot is only available for labeling scenarios"
        )
    return scenario


@api_v1_bp.route("/scenarios/<int:scenario_id>/copilot", methods=["GET"])
@api_key_or_token_required
@require_api_scope("scenario:read")
@handle_api_errors(logger_name="api_v1.copilot")
def get_copilot_status_v1(scenario_id: int):
    scenario = _get_labeling_scenario(scenario_id)
    return jsonify({"success": True, "copilot": LabelingCopilotService.get_status(scenario)})


@api_v1_bp.route("/scenarios/<int:scenario_id>/copilot", methods=["PUT"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.copilot")
def update_copilot_config_v1(scenario_id: int):
    """Merge the provided fields into the scenario's copilot config.

    Prompt/codebook changes bump prompt_version server-side; the response
    reports the resulting version so callers know whether a re-generation
    (POST .../copilot/generate) is due.
    """
    scenario = _get_labeling_scenario(scenario_id)

    body = request.get_json(silent=True) or {}
    unknown = set(body.keys()) - _EDITABLE_FIELDS
    if unknown:
        raise ApiValidationError(
            f"Unknown fields: {sorted(unknown)}. Editable: {sorted(_EDITABLE_FIELDS)}"
        )
    if "top_k" in body and body["top_k"] not in (1, 2):
        raise ApiValidationError("top_k must be 1 or 2")
    if "hidden_control_ratio" in body:
        try:
            ratio = float(body["hidden_control_ratio"])
        except (TypeError, ValueError):
            raise ApiValidationError("hidden_control_ratio must be a number")
        if not 0.0 <= ratio <= 0.5:
            raise ApiValidationError("hidden_control_ratio must be within 0.0-0.5")
        body["hidden_control_ratio"] = ratio
    if "enabled" in body and not isinstance(body["enabled"], bool):
        raise ApiValidationError("enabled must be a boolean")

    previous_config = scenario.config_json or {}
    # Deep-ish copy via JSON round trip so normalize sees a distinct "previous"
    import json as _json
    next_config = _json.loads(_json.dumps(previous_config))

    inner = LabelingCopilotService.locate_inner_config(next_config)
    if not inner:
        raise ApiValidationError("Scenario has no labeling config to attach a copilot to")
    copilot = dict(inner.get("copilot") or {})
    copilot.update(body)
    inner["copilot"] = copilot
    # v1-created scenarios duplicate the inner config at config.config —
    # keep both copies in sync (same mirroring as the settings-tab UI).
    if isinstance(next_config.get("config"), dict):
        next_config["config"]["copilot"] = copilot

    next_config = LabelingCopilotService.normalize_config_on_write(
        next_config, previous_config
    )
    scenario.config_json = next_config
    db.session.commit()

    status = LabelingCopilotService.get_status(scenario)
    logger.info(
        "[api_v1.copilot] Updated copilot config for scenario %s (prompt v%s)",
        scenario_id, status.get("prompt_version"),
    )
    return jsonify({"success": True, "copilot": status})


@api_v1_bp.route("/scenarios/<int:scenario_id>/copilot/generate", methods=["POST"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.copilot")
def generate_copilot_suggestions_v1(scenario_id: int):
    scenario = _get_labeling_scenario(scenario_id)
    result = LabelingCopilotService.start_generation(scenario)
    if not result.get("queued"):
        raise ApiValidationError(
            f"Co-pilot generation not startable: {result.get('reason')}"
        )
    return jsonify({"success": True, "scenario_id": scenario_id, **result})


@api_v1_bp.route("/scenarios/<int:scenario_id>/labeling-config", methods=["PUT"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.copilot")
def update_labeling_config_v1(scenario_id: int):
    """Merge ``questions`` / ``second_choice`` into the labeling config.

    Validation + mirroring in LabelingCopilotService.update_labeling_settings;
    the copilot prompt_version bumps automatically when the questions change
    (they are part of the effective co-pilot prompt), same as via the UI.
    """
    scenario = _get_labeling_scenario(scenario_id)
    body = request.get_json(silent=True) or {}
    previous_config = scenario.config_json or {}
    try:
        next_config = LabelingCopilotService.update_labeling_settings(previous_config, body)
    except ValueError as exc:
        raise ApiValidationError(str(exc))
    next_config = LabelingCopilotService.normalize_config_on_write(
        next_config, previous_config
    )
    scenario.config_json = next_config
    db.session.commit()

    inner = LabelingCopilotService.locate_inner_config(scenario.config_json)
    logger.info(
        "[api_v1.copilot] Updated labeling settings for scenario %s: %s",
        scenario_id, sorted(body.keys()),
    )
    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        "labeling": {
            "questions": inner.get("questions"),
            "second_choice": bool(inner.get("second_choice")),
        },
        "copilot": LabelingCopilotService.get_status(scenario),
    })
