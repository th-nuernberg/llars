# latex_comment_routes.py
"""
LaTeX Collab Comment API Routes.
Handles document comments (annotations) for collaborative review.
Real-time sync via Socket.IO events.
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app

from auth.auth_utils import AuthUtils
from db.database import db
from db.tables import LatexDocument, LatexComment, LatexWorkspace
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.latex_collab.latex_helpers import (
    require_document_access,
    require_workspace_access,
    comment_to_dict,
)

logger = logging.getLogger(__name__)


def _emit_comment_event(document_id: int, action: str, comment_dict: dict = None):
    """Emit comment change event to all document subscribers."""
    try:
        socketio = current_app.extensions.get('socketio')
        if socketio:
            from socketio_handlers.events_latex_collab import emit_comment_changed
            emit_comment_changed(socketio, document_id, action, comment_dict)
    except Exception as e:
        logger.warning(f"Failed to emit comment event: {e}")


def _emit_workspace_comment_event(workspace_id: int, action: str, comment_dict: dict = None):
    """Emit comment change event to all workspace subscribers."""
    try:
        socketio = current_app.extensions.get('socketio')
        if socketio:
            from socketio_handlers.events_latex_collab import emit_workspace_comment_changed
            emit_workspace_comment_changed(socketio, workspace_id, action, comment_dict)
    except Exception as e:
        logger.warning(f"Failed to emit workspace comment event: {e}")

latex_comment_bp = Blueprint("latex_comment", __name__, url_prefix="/api/latex-collab")


@latex_comment_bp.route("/workspaces/<int:workspace_id>/comments", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_workspace_comments(workspace_id: int):
    """
    List all comments for a workspace across all documents.

    Returns comments grouped by document, with document info for navigation.
    This enables a global comments panel that shows all workspace comments.
    """
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    workspace = LatexWorkspace.query.get(workspace_id)
    if not workspace:
        raise NotFoundError("Workspace not found")
    require_workspace_access(workspace, username)

    # Get all document IDs in this workspace
    document_ids = (
        db.session.query(LatexDocument.id)
        .filter(
            LatexDocument.workspace_id == workspace_id,
            LatexDocument.deleted_at.is_(None),
        )
        .all()
    )
    doc_ids = [d[0] for d in document_ids]

    if not doc_ids:
        return jsonify({"success": True, "comments": []}), 200

    # Fetch all top-level comments for these documents
    comments = (
        LatexComment.query
        .filter(
            LatexComment.document_id.in_(doc_ids),
            LatexComment.parent_id.is_(None),
        )
        .order_by(LatexComment.created_at.desc(), LatexComment.id.desc())
        .all()
    )

    # Build document info lookup for efficient access
    documents = LatexDocument.query.filter(LatexDocument.id.in_(doc_ids)).all()
    doc_info = {
        d.id: {"id": d.id, "title": d.title, "node_type": d.node_type.value}
        for d in documents
    }

    # Convert to dict with document info
    result = []
    for c in comments:
        comment_dict = comment_to_dict(c, include_replies=True)
        comment_dict["document"] = doc_info.get(c.document_id, {})
        result.append(comment_dict)

    return jsonify({
        "success": True,
        "comments": result,
    }), 200


@latex_comment_bp.route("/documents/<int:document_id>/comments", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_comments(document_id: int):
    """List all top-level comments for a document with nested replies."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    # Only fetch top-level comments (replies are loaded via relationship)
    comments = (
        LatexComment.query
        .filter_by(document_id=document_id, parent_id=None)
        .order_by(LatexComment.created_at.asc(), LatexComment.id.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "comments": [comment_to_dict(c, include_replies=True) for c in comments],
    }), 200


@latex_comment_bp.route("/documents/<int:document_id>/comments", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_comment(document_id: int):
    """Create a top-level comment on a document (on a text range)."""
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
    author_color = data.get("author_color")  # Hex color e.g. #ff5733

    if range_start is None or range_end is None:
        raise ValidationError("range_start and range_end are required")
    if not isinstance(range_start, int) or not isinstance(range_end, int):
        raise ValidationError("range_start and range_end must be integers")
    if range_start < 0 or range_end <= range_start:
        raise ValidationError("Invalid comment range")
    if not body:
        raise ValidationError("body is required")

    # Validate color format if provided
    if author_color and not (isinstance(author_color, str) and len(author_color) == 7 and author_color.startswith('#')):
        author_color = None  # Ignore invalid colors

    comment = LatexComment(
        document_id=document_id,
        author_username=username,
        author_color=author_color,
        range_start=range_start,
        range_end=range_end,
        body=body,
        created_at=datetime.utcnow(),
    )
    db.session.add(comment)
    db.session.commit()

    comment_dict = comment_to_dict(comment, include_replies=False)
    # Add document info for workspace-level display
    comment_dict["document"] = {"id": doc.id, "title": doc.title, "node_type": doc.node_type.value}

    _emit_comment_event(document_id, 'created', comment_dict)
    _emit_workspace_comment_event(doc.workspace_id, 'created', comment_dict)

    return jsonify({"success": True, "comment": comment_dict}), 201


@latex_comment_bp.route("/comments/<int:comment_id>/replies", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_reply(comment_id: int):
    """Create a reply to an existing comment."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    parent_comment = LatexComment.query.get(comment_id)
    if not parent_comment:
        raise NotFoundError("Parent comment not found")

    doc = LatexDocument.query.get(parent_comment.document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    author_color = data.get("author_color")  # Hex color e.g. #ff5733

    if not body:
        raise ValidationError("body is required")

    # Validate color format if provided
    if author_color and not (isinstance(author_color, str) and len(author_color) == 7 and author_color.startswith('#')):
        author_color = None

    reply = LatexComment(
        document_id=parent_comment.document_id,
        parent_id=comment_id,
        author_username=username,
        author_color=author_color,
        range_start=None,  # Replies don't have ranges
        range_end=None,
        body=body,
        created_at=datetime.utcnow(),
    )
    db.session.add(reply)
    db.session.commit()

    reply_dict = comment_to_dict(reply, include_replies=False)
    # Add document info for workspace-level display
    reply_dict["document"] = {"id": doc.id, "title": doc.title, "node_type": doc.node_type.value}

    event_payload = {'parent_id': comment_id, 'reply': reply_dict}
    _emit_comment_event(parent_comment.document_id, 'reply_created', event_payload)
    _emit_workspace_comment_event(doc.workspace_id, 'reply_created', event_payload)

    return jsonify({"success": True, "reply": reply_dict}), 201


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

    comment_dict = comment_to_dict(comment)
    # Add document info for workspace-level display
    comment_dict["document"] = {"id": doc.id, "title": doc.title, "node_type": doc.node_type.value}

    _emit_comment_event(comment.document_id, 'updated', comment_dict)
    _emit_workspace_comment_event(doc.workspace_id, 'updated', comment_dict)

    return jsonify({"success": True, "comment": comment_dict}), 200


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

    document_id = comment.document_id
    workspace_id = doc.workspace_id
    comment_id_to_delete = comment.id
    db.session.delete(comment)
    db.session.commit()

    delete_payload = {'id': comment_id_to_delete, 'document_id': document_id}
    _emit_comment_event(document_id, 'deleted', delete_payload)
    _emit_workspace_comment_event(workspace_id, 'deleted', delete_payload)

    return jsonify({"success": True}), 200


@latex_comment_bp.route("/comments/<int:comment_id>/ai-resolve", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def ai_resolve_comment(comment_id: int):
    """
    Use AI to resolve a comment by suggesting document changes.

    The AI will analyze the comment and the marked text, then suggest
    a replacement and automatically create a reply from the AI assistant.

    Request body:
        {
            "model_id": "optional - specific LLM model to use",
            "auto_resolve": true  // Whether to mark comment as resolved
        }

    Response:
        {
            "success": true,
            "changes": {
                "range_start": 150,
                "range_end": 200,
                "old_text": "...",
                "new_text": "..."
            },
            "reply": {
                "id": 42,
                "author_username": "LLARS KI",
                "author_color": "#b0ca97",
                "body": "..."
            }
        }
    """
    from services.latex_collab.comment_ai_service import CommentAIService

    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    comment = LatexComment.query.get(comment_id)
    if not comment:
        raise NotFoundError("Comment not found")

    # Only allow AI resolve on top-level comments (not replies)
    if comment.parent_id is not None:
        raise ValidationError("AI resolve is only available for top-level comments")

    doc = LatexDocument.query.get(comment.document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    data = request.get_json() or {}
    model_id = data.get("model_id")
    auto_resolve = data.get("auto_resolve", True)

    # Get AI settings
    ai_settings = CommentAIService.get_ai_settings()
    if not ai_settings['enabled']:
        raise ValidationError("AI assistant is currently disabled")

    # Call AI service
    result = CommentAIService.resolve_comment(
        comment=comment,
        document=doc,
        model_id=model_id,
    )

    if not result.success:
        raise ValidationError(result.error or "AI resolution failed")

    # Create AI reply
    ai_reply = LatexComment(
        document_id=comment.document_id,
        parent_id=comment_id,
        author_username=ai_settings['username'],
        author_color=ai_settings['color'],
        range_start=None,
        range_end=None,
        body=result.ai_reply,
        created_at=datetime.utcnow(),
    )
    db.session.add(ai_reply)

    # Optionally mark original comment as resolved
    if auto_resolve:
        comment.resolved_at = datetime.utcnow()

    db.session.commit()

    reply_dict = comment_to_dict(ai_reply, include_replies=False)
    # Add document info for workspace-level display
    reply_dict["document"] = {"id": doc.id, "title": doc.title, "node_type": doc.node_type.value}

    # Emit events
    reply_event_payload = {'parent_id': comment_id, 'reply': reply_dict}
    _emit_comment_event(comment.document_id, 'reply_created', reply_event_payload)
    _emit_workspace_comment_event(doc.workspace_id, 'reply_created', reply_event_payload)

    if auto_resolve:
        comment_dict = comment_to_dict(comment)
        comment_dict["document"] = {"id": doc.id, "title": doc.title, "node_type": doc.node_type.value}
        _emit_comment_event(comment.document_id, 'updated', comment_dict)
        _emit_workspace_comment_event(doc.workspace_id, 'updated', comment_dict)

    return jsonify({
        "success": True,
        "changes": {
            "document_id": doc.id,
            "range_start": comment.range_start,
            "range_end": comment.range_end,
            "old_text": result.old_text,
            "new_text": result.new_text,
        },
        "reply": reply_dict,
    }), 200
