"""
``/api/v1/scenarios/<id>/referral-link`` — sync a referral link to a scenario.

The endpoint is intentionally idempotent: re-POSTing with the same slug
re-points it at the scenario. Useful for ``llars-seeder`` style flows where
you want the URL ``/r/<slug>`` to follow the latest seed of a study.
"""

from __future__ import annotations

import logging

from flask import g, jsonify, request

from auth.decorators import api_key_or_token_required, require_api_scope
from db.models import RatingScenarios, ReferralLink
from decorators.error_handler import (
    ConflictError,
    NotFoundError,
    handle_api_errors,
)
from schemas.api_v1.scenario_api import ReferralLinkResponse, ReferralLinkSpec
from services.api_v1_scenario_service import _sync_referral_link
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


def _link_to_dict(link: ReferralLink) -> dict:
    return ReferralLinkResponse(
        id=link.id,
        slug=link.slug,
        code=link.code,
        label=link.label,
        role_name=link.role_name,
        target_scenario_id=link.target_scenario_id,
        is_active=link.is_active,
    ).model_dump(mode="json")


@api_v1_bp.route(
    "/scenarios/<int:scenario_id>/referral-link", methods=["POST"]
)
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.referral")
def sync_referral_link(scenario_id: int):
    """
    Create or update a ReferralLink so its ``target_scenario_id`` points at
    ``scenario_id``. Body is a ``ReferralLinkSpec``.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    _require_owner(scenario)

    spec = _validate_request(ReferralLinkSpec, request.get_json(silent=True))

    try:
        link = _sync_referral_link(scenario, spec, g.authentik_user.username)
        from db import db
        db.session.commit()
    except Exception:
        from db import db as _db
        _db.session.rollback()
        raise

    return jsonify({"success": True, "referral_link": _link_to_dict(link)})


@api_v1_bp.route(
    "/scenarios/<int:scenario_id>/referral-link", methods=["GET"]
)
@api_key_or_token_required
@require_api_scope("scenario:read")
@handle_api_errors(logger_name="api_v1.referral")
def get_referral_link(scenario_id: int):
    """Read the link currently pointing at this scenario, if any."""
    link = ReferralLink.query.filter_by(target_scenario_id=scenario_id).first()
    if not link:
        return jsonify({"success": True, "referral_link": None})
    return jsonify({"success": True, "referral_link": _link_to_dict(link)})


@api_v1_bp.route(
    "/scenarios/<int:scenario_id>/referral-link", methods=["DELETE"]
)
@api_key_or_token_required
@require_api_scope("scenario:write")
@handle_api_errors(logger_name="api_v1.referral")
def detach_referral_link(scenario_id: int):
    """
    Detach the link from the scenario without deleting the link itself —
    so the slug stays usable for a different scenario later. To fully
    delete the campaign use the existing referral admin routes.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    _require_owner(scenario)

    link = ReferralLink.query.filter_by(target_scenario_id=scenario_id).first()
    if not link:
        raise NotFoundError(
            f"No referral link is attached to scenario {scenario_id}"
        )

    link.target_scenario_id = None
    from db import db
    db.session.commit()
    return jsonify({"success": True, "detached_link_id": link.id})
