"""
Paper CRUD Routes - paper management and author endpoints.
"""

import logging

from flask import Blueprint, jsonify, request

from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from services.conference_service import ConferenceService

logger = logging.getLogger(__name__)

paper_crud_bp = Blueprint("paper_crud", __name__)


@paper_crud_bp.route("/papers", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def list_papers():
    """List all papers with optional filters."""
    status = request.args.get("status")
    conference_id = request.args.get("conference_id", type=int)
    search = request.args.get("search")

    papers = ConferenceService.list_papers(
        status=status, conference_id=conference_id, search=search
    )
    return jsonify({"success": True, "papers": papers}), 200


@paper_crud_bp.route("/papers/<int:paper_id>", methods=["GET"])
@require_permission("feature:conference_manager:view")
@handle_api_errors(logger_name="conference_manager")
def get_paper(paper_id):
    """Get a single paper by ID."""
    paper = ConferenceService.get_paper(paper_id)
    if not paper:
        raise NotFoundError(f"Paper {paper_id} not found")
    return jsonify({"success": True, "paper": paper}), 200


@paper_crud_bp.route("/papers", methods=["POST"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def create_paper():
    """Create a new paper."""
    from flask import g
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")
    if not data.get("title"):
        raise ValidationError("Paper title is required")

    username = g.authentik_user.username
    paper = ConferenceService.create_paper(data, username)
    return jsonify({"success": True, "paper": paper}), 201


@paper_crud_bp.route("/papers/<int:paper_id>", methods=["PUT"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def update_paper(paper_id):
    """Update an existing paper."""
    from flask import g
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")

    username = g.authentik_user.username
    paper = ConferenceService.update_paper(paper_id, data, username)
    if not paper:
        raise NotFoundError(f"Paper {paper_id} not found")
    return jsonify({"success": True, "paper": paper}), 200


@paper_crud_bp.route("/papers/<int:paper_id>/status", methods=["PATCH"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def update_paper_status(paper_id):
    """Lightweight status update for Kanban drag-and-drop."""
    from flask import g
    data = request.get_json()
    if not data or not data.get("status"):
        raise ValidationError("Status is required")

    username = g.authentik_user.username
    paper = ConferenceService.update_paper_status(paper_id, data["status"], username)
    if not paper:
        raise NotFoundError(f"Paper {paper_id} not found")
    return jsonify({"success": True, "paper": paper}), 200


@paper_crud_bp.route("/papers/<int:paper_id>", methods=["DELETE"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def delete_paper(paper_id):
    """Delete a paper."""
    deleted = ConferenceService.delete_paper(paper_id)
    if not deleted:
        raise NotFoundError(f"Paper {paper_id} not found")
    return jsonify({"success": True}), 200


@paper_crud_bp.route("/papers/<int:paper_id>/authors", methods=["PUT"])
@require_permission("feature:conference_manager:edit")
@handle_api_errors(logger_name="conference_manager")
def set_paper_authors(paper_id):
    """Replace all authors for a paper."""
    from flask import g
    data = request.get_json()
    if not data or "authors" not in data:
        raise ValidationError("Authors list is required")

    username = g.authentik_user.username
    authors = ConferenceService.set_paper_authors(paper_id, data["authors"], username)
    return jsonify({"success": True, "authors": authors}), 200
