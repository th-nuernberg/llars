# latex_comment_routes.py
"""
LaTeX Collab Comment API Routes.
Handles document comments (annotations) for collaborative review.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.auth_utils import AuthUtils
from db.db import db
from db.tables import LatexDocument, LatexComment
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.latex_collab.latex_helpers import (
    require_document_access,
    comment_to_dict,
)

latex_comment_bp = Blueprint("latex_comment", __name__, url_prefix="/api/latex-collab")


@latex_comment_bp.route("/documents/<int:document_id>/comments", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_comments(document_id: int):
    """List all comments for a document."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    comments = (
        LatexComment.query
        .filter_by(document_id=document_id)
        .order_by(LatexComment.created_at.asc(), LatexComment.id.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "comments": [comment_to_dict(c) for c in comments],
    }), 200


@latex_comment_bp.route("/documents/<int:document_id>/comments", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_comment(document_id: int):
    """Create a comment on a document."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    data = request.get_json() or {}
    range_start = data.get("range_start")
    range_end = data.get("range_end")
    body = (data.get("body") or "").strip()

    if range_start is None or range_end is None:
        raise ValidationError("range_start and range_end are required")
    if not isinstance(range_start, int) or not isinstance(range_end, int):
        raise ValidationError("range_start and range_end must be integers")
    if range_start < 0 or range_end <= range_start:
        raise ValidationError("Invalid comment range")
    if not body:
        raise ValidationError("body is required")

    comment = LatexComment(
        document_id=document_id,
        author_username=username,
        range_start=range_start,
        range_end=range_end,
        body=body,
        created_at=datetime.utcnow(),
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({"success": True, "comment": comment_to_dict(comment)}), 201


@latex_comment_bp.route("/comments/<int:comment_id>", methods=["PATCH"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def update_comment(comment_id: int):
    """Update a comment's body or resolve status."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    comment = LatexComment.query.get(comment_id)
    if not comment:
        raise NotFoundError("Comment not found")

    doc = LatexDocument.query.get(comment.document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    data = request.get_json() or {}
    body = data.get("body")
    resolved = data.get("resolved")

    if body is not None:
        body = str(body).strip()
        if not body:
            raise ValidationError("body cannot be empty")
        comment.body = body

    if resolved is not None:
        if bool(resolved):
            comment.resolved_at = datetime.utcnow()
        else:
            comment.resolved_at = None

    db.session.commit()
    return jsonify({"success": True, "comment": comment_to_dict(comment)}), 200


@latex_comment_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def delete_comment(comment_id: int):
    """Delete a comment."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    comment = LatexComment.query.get(comment_id)
    if not comment:
        raise NotFoundError("Comment not found")

    doc = LatexDocument.query.get(comment.document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"success": True}), 200
