"""
Conference CRUD Routes - conference management endpoints.
"""

import logging

from flask import Blueprint, jsonify, request

from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from services.conference_service import ConferenceService

logger = logging.getLogger(__name__)

conference_crud_bp = Blueprint("conference_crud", __name__)


@conference_crud_bp.route("/conferences", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def list_conferences():
    """List all conferences with optional filters."""
    year = request.args.get("year", type=int)
    core_ranking = request.args.get("core_ranking")
    search = request.args.get("search")
    group_id = request.args.get("group_id", type=int)

    conferences = ConferenceService.list_conferences(
        year=year, core_ranking=core_ranking, search=search, group_id=group_id
    )
    return jsonify({"success": True, "conferences": conferences}), 200


@conference_crud_bp.route("/conferences/<int:conference_id>", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def get_conference(conference_id):
    """Get a single conference by ID."""
    conference = ConferenceService.get_conference(conference_id)
    if not conference:
        raise NotFoundError(f"Conference {conference_id} not found")
    return jsonify({"success": True, "conference": conference}), 200


@conference_crud_bp.route("/conferences", methods=["POST"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def create_conference():
    """Create a new conference."""
    from flask import g
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")
    if not data.get("name"):
        raise ValidationError("Conference name is required")
    if not data.get("acronym"):
        raise ValidationError("Conference acronym is required")
    if not data.get("year"):
        raise ValidationError("Conference year is required")

    username = g.authentik_user.username
    conference = ConferenceService.create_conference(data, username)
    return jsonify({"success": True, "conference": conference}), 201


@conference_crud_bp.route("/conferences/<int:conference_id>", methods=["PUT"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def update_conference(conference_id):
    """Update an existing conference."""
    from flask import g
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")

    username = g.authentik_user.username
    conference = ConferenceService.update_conference(conference_id, data, username)
    if not conference:
        raise NotFoundError(f"Conference {conference_id} not found")
    return jsonify({"success": True, "conference": conference}), 200


@conference_crud_bp.route("/conferences/<int:conference_id>", methods=["DELETE"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def delete_conference(conference_id):
    """Delete a conference."""
    deleted = ConferenceService.delete_conference(conference_id)
    if not deleted:
        raise NotFoundError(f"Conference {conference_id} not found")
    return jsonify({"success": True}), 200


@conference_crud_bp.route("/stats", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def get_stats():
    """Get aggregated statistics."""
    group_id = request.args.get("group_id", type=int)
    stats = ConferenceService.get_stats(group_id=group_id)
    return jsonify({"success": True, "stats": stats}), 200
