"""
``/api/v1/scenarios/<id>/assessors`` — invite, patch, remove.

Mirrors the team-management UI under Scenarios → Settings → Team. The
endpoints accept the same 2-axis role model (manager_role × evaluation_role)
that ``ScenarioUsers`` already uses.
"""

from __future__ import annotations

import logging
from datetime import datetime

from flask import g, jsonify, request

from auth.decorators import api_key_or_token_required, require_api_scope
from db import db
from db.models import RatingScenarios, ScenarioUsers, User
from db.models.scenario import (
    InvitationStatus,
    MembershipStatus,
    ScenarioRoles,
)
from decorators.error_handler import (
    ConflictError,
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from schemas.api_v1.scenario_api import AssessorInvite, AssessorResponse
from services.permission_service import PermissionService

from . import api_v1_bp
from .scenarios_routes import _validate_request

logger = logging.getLogger(__name__)


def _require_owner(scenario: RatingScenarios) -> None:
    user = g.authentik_user
    if PermissionService.user_has_role(user.username, "admin"):
        return
    if scenario.created_by != user.username:
        # SECURITY (M1): mask non-owner access as 404 to avoid leaking
        # scenario-ID validity (matches the 'scenario not found' body).
        raise NotFoundError(f"Scenario {scenario.id} not found")


def _membership_to_dict(su: ScenarioUsers) -> dict:
    return AssessorResponse(
        user_id=su.user_id,
        username=su.user.username if su.user else "",
        manager_role=su.manager_role,
        evaluation_role=su.evaluation_role,
        invitation_status=(
            su.invitation_status.value if su.invitation_status else "accepted"
        ),
    ).model_dump(mode="json")


@api_v1_bp.route("/scenarios/<int:scenario_id>/assessors", methods=["GET"])
@api_key_or_token_required
@require_api_scope("scenario:read")
@handle_api_errors(logger_name="api_v1.assessors")
def list_assessors(scenario_id: int):
    """List all members of a scenario with their role assignments."""
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    rows = ScenarioUsers.query.filter_by(scenario_id=scenario_id).all()
    return jsonify({
        "success": True,
        "assessors": [_membership_to_dict(s) for s in rows],
        "total": len(rows),
    })


@api_v1_bp.route("/scenarios/<int:scenario_id>/assessors", methods=["POST"])
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.assessors")
def invite_assessor(scenario_id: int):
    """Add a single user to the scenario. 409 if they're already a member."""
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    _require_owner(scenario)

    invite = _validate_request(AssessorInvite, request.get_json(silent=True))
    user = User.query.filter_by(username=invite.username).first()
    if not user:
        raise NotFoundError(f"User '{invite.username}' not found")

    existing = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id, user_id=user.id
    ).first()
    if existing:
        raise ConflictError(
            f"User '{invite.username}' is already a member of this scenario"
        )

    membership = ScenarioUsers(
        scenario_id=scenario_id,
        user_id=user.id,
        role=ScenarioRoles.EVALUATOR,
        access_level="MEMBER",
        manager_role=invite.manager_role,
        evaluation_role=invite.evaluation_role,
        is_assessor=invite.evaluation_role == "assessor",
        is_viewer=invite.evaluation_role == "viewer",
        invitation_status=InvitationStatus(invite.invitation_status),
        membership_status=MembershipStatus.ACTIVE,
        invited_at=datetime.utcnow(),
        invited_by=g.authentik_user.username,
    )
    db.session.add(membership)
    db.session.commit()
    return jsonify({"success": True, "assessor": _membership_to_dict(membership)}), 201


@api_v1_bp.route(
    "/scenarios/<int:scenario_id>/assessors/<int:user_id>", methods=["PATCH"]
)
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.assessors")
def patch_assessor(scenario_id: int, user_id: int):
    """Update an existing membership's roles or invitation status.

    Refuses to demote the last `manager_role='owner'` — leaving a scenario
    ownerless puts it in a state the UI can't recover from. Caller sees a
    409 in that case."""
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    _require_owner(scenario)

    membership = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id, user_id=user_id
    ).first()
    if not membership:
        raise NotFoundError(
            f"User {user_id} is not a member of scenario {scenario_id}"
        )

    data = request.get_json(silent=True) or {}
    new_manager_role = data.get("manager_role")
    new_eval_role = data.get("evaluation_role")
    new_status = data.get("invitation_status")

    if new_manager_role and new_manager_role not in ("owner", "editor", "viewer", "none"):
        raise ApiValidationError(f"Invalid manager_role: {new_manager_role}")
    if new_eval_role and new_eval_role not in ("assessor", "viewer", "none"):
        raise ApiValidationError(f"Invalid evaluation_role: {new_eval_role}")
    if new_status and new_status not in ("accepted", "rejected", "pending"):
        raise ApiValidationError(f"Invalid invitation_status: {new_status}")

    # Last-owner guard.
    if (
        membership.manager_role == "owner"
        and new_manager_role
        and new_manager_role != "owner"
    ):
        owners_left = (
            ScenarioUsers.query.filter_by(
                scenario_id=scenario_id, manager_role="owner"
            )
            .filter(ScenarioUsers.user_id != user_id)
            .count()
        )
        if owners_left == 0:
            raise ConflictError(
                "Cannot demote the last owner of a scenario"
            )

    if new_manager_role is not None:
        membership.manager_role = new_manager_role
    if new_eval_role is not None:
        membership.evaluation_role = new_eval_role
        membership.is_assessor = new_eval_role == "assessor"
        membership.is_viewer = new_eval_role == "viewer"
    if new_status is not None:
        membership.invitation_status = InvitationStatus(new_status)
        membership.responded_at = datetime.utcnow()

    db.session.commit()
    return jsonify({
        "success": True,
        "assessor": _membership_to_dict(membership),
    })


@api_v1_bp.route(
    "/scenarios/<int:scenario_id>/assessors/<int:user_id>", methods=["DELETE"]
)
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.assessors")
def remove_assessor(scenario_id: int, user_id: int):
    """Hard-remove a membership row. Refuses to remove the last owner."""
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    _require_owner(scenario)

    membership = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id, user_id=user_id
    ).first()
    if not membership:
        raise NotFoundError(
            f"User {user_id} is not a member of scenario {scenario_id}"
        )

    if membership.manager_role == "owner":
        owners_left = (
            ScenarioUsers.query.filter_by(
                scenario_id=scenario_id, manager_role="owner"
            )
            .filter(ScenarioUsers.user_id != user_id)
            .count()
        )
        if owners_left == 0:
            raise ConflictError(
                "Cannot remove the last owner of a scenario"
            )

    db.session.delete(membership)
    db.session.commit()
    return jsonify({"success": True, "removed_user_id": user_id})
