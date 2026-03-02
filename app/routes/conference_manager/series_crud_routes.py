"""
Conference Series CRUD Routes - series management endpoints.
"""

import logging

from flask import Blueprint, jsonify, request, g

from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from services.conference_service import ConferenceSeriesService

logger = logging.getLogger(__name__)

series_crud_bp = Blueprint("series_crud", __name__)


@series_crud_bp.route("/series", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def list_series():
    """List all conference series with optional search."""
    search = request.args.get("search")
    series = ConferenceSeriesService.list_series(search=search)
    return jsonify({"success": True, "series": series}), 200


@series_crud_bp.route("/series/<int:series_id>", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def get_series(series_id):
    """Get a single conference series by ID."""
    series = ConferenceSeriesService.get_series(series_id)
    if not series:
        raise NotFoundError(f"Series {series_id} not found")
    return jsonify({"success": True, "series": series}), 200


@series_crud_bp.route("/series", methods=["POST"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def create_series():
    """Create a new conference series."""
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")
    if not data.get("name"):
        raise ValidationError("Series name is required")
    if not data.get("acronym"):
        raise ValidationError("Series acronym is required")

    username = g.authentik_user.username
    series = ConferenceSeriesService.create_series(data, username)
    return jsonify({"success": True, "series": series}), 201


@series_crud_bp.route("/series/<int:series_id>", methods=["PUT"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def update_series(series_id):
    """Update an existing conference series."""
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")

    username = g.authentik_user.username
    series = ConferenceSeriesService.update_series(series_id, data, username)
    if not series:
        raise NotFoundError(f"Series {series_id} not found")
    return jsonify({"success": True, "series": series}), 200


@series_crud_bp.route("/series/<int:series_id>", methods=["DELETE"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def delete_series(series_id):
    """Delete a conference series. Conferences keep their data but lose the FK."""
    deleted = ConferenceSeriesService.delete_series(series_id)
    if not deleted:
        raise NotFoundError(f"Series {series_id} not found")
    return jsonify({"success": True}), 200


@series_crud_bp.route("/series/find-by-acronym", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def find_series_by_acronym():
    """Find a series by its acronym (case-insensitive)."""
    acronym = request.args.get("acronym")
    if not acronym:
        raise ValidationError("Acronym parameter is required")
    series = ConferenceSeriesService.find_series_by_acronym(acronym)
    return jsonify({"success": True, "series": series}), 200


@series_crud_bp.route("/series/<int:series_id>/new-edition-defaults", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def get_new_edition_defaults(series_id):
    """Get pre-filled defaults for creating a new edition of a series."""
    defaults = ConferenceSeriesService.get_new_edition_defaults(series_id)
    if not defaults:
        raise NotFoundError(f"Series {series_id} not found")
    return jsonify({"success": True, "defaults": defaults}), 200
