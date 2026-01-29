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


@latex_comment_bp.route("/comments/<int:comment_id>/ai-resolve/status", methods=["GET"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def get_ai_resolve_status(comment_id: int):
    """
    Get the current status of an AI resolve stream (for reconnection support).

    Response:
        {
            "active": true,
            "content": "streamed content so far...",
            "status": "streaming|completed|error",
            "result": { ... } // only if completed
        }
    """
    from services.latex_collab.comment_ai_service import CommentAIService

    stream_state = CommentAIService.get_active_stream(comment_id)
    if not stream_state:
        return jsonify({"active": False}), 200

    return jsonify({
        "active": True,
        "content": stream_state.get("content", ""),
        "status": stream_state.get("status", "streaming"),
        "result": stream_state.get("result"),
        "old_text": stream_state.get("old_text", ""),
    }), 200


@latex_comment_bp.route("/comments/<int:comment_id>/ai-resolve", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def ai_resolve_comment(comment_id: int):
    """
    Use AI to resolve a comment by suggesting document changes.
    Now supports streaming via Socket.IO for real-time token display.

    The AI will analyze the comment and the marked text, then suggest
    a replacement and automatically create a reply from the AI assistant.

    Request body:
        {
            "model_id": "optional - specific LLM model to use",
            "auto_resolve": true,  // Whether to mark comment as resolved
            "streaming": true      // Whether to stream tokens via Socket.IO
        }

    Response (streaming=true):
        {
            "success": true,
            "streaming": true,
            "comment_id": 3,
            "document_id": 5,
            "workspace_id": 1
        }
        // Tokens are sent via Socket.IO events:
        // - latex_collab:ai_resolve:token
        // - latex_collab:ai_resolve:completed
        // - latex_collab:ai_resolve:error

    Response (streaming=false, legacy):
        {
            "success": true,
            "changes": { ... },
            "reply": { ... }
        }
    """
    from services.latex_collab.comment_ai_service import CommentAIService
    from main import socketio

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
    use_streaming = data.get("streaming", True)  # Default to streaming

    # Get AI settings
    ai_settings = CommentAIService.get_ai_settings()
    if not ai_settings['enabled']:
        raise ValidationError("AI assistant is currently disabled")

    # Check if there's already an active stream for this comment
    existing_stream = CommentAIService.get_active_stream(comment_id)
    if existing_stream and existing_stream.get("status") == "streaming":
        return jsonify({
            "success": True,
            "streaming": True,
            "already_active": True,
            "comment_id": comment_id,
            "document_id": doc.id,
            "workspace_id": doc.workspace_id,
        }), 200

    if use_streaming:
        # Streaming mode: start background thread and return immediately
        workspace_id = doc.workspace_id
        document_id = doc.id
        range_start = comment.range_start
        range_end = comment.range_end

        # Capture app reference for background thread callbacks
        app = current_app._get_current_object()

        def on_token(token: str):
            """Emit token via Socket.IO"""
            with app.app_context():
                socketio.emit('latex_collab:ai_resolve:token', {
                    'comment_id': comment_id,
                    'workspace_id': workspace_id,
                    'document_id': document_id,
                    'token': token,
                })

        def on_complete(new_text: str, ai_reply_text: str):
            """Handle completion: create reply, update comment range, emit events"""
            with app.app_context():
                # Re-fetch comment and doc in new context
                _comment = LatexComment.query.get(comment_id)
                _doc = LatexDocument.query.get(document_id)
                if not _comment or not _doc:
                    return

                # Get the old text from stream state
                stream_state = CommentAIService.get_active_stream(comment_id)
                old_text = stream_state.get("old_text", "") if stream_state else ""

                # Update comment range to match new text length
                # The start position stays the same, but end position changes
                old_range_end = _comment.range_end
                new_range_end = _comment.range_start + len(new_text) if _comment.range_start is not None else None
                if new_range_end is not None:
                    _comment.range_end = new_range_end
                    logger.info(f"Updated comment {comment_id} range_end: {old_range_end} -> {new_range_end}")

                # Create AI reply
                _ai_reply = LatexComment(
                    document_id=_comment.document_id,
                    parent_id=comment_id,
                    author_username=ai_settings['username'],
                    author_color=ai_settings['color'],
                    range_start=None,
                    range_end=None,
                    body=ai_reply_text,
                    created_at=datetime.utcnow(),
                )
                db.session.add(_ai_reply)

                # Optionally mark original comment as resolved
                if auto_resolve:
                    _comment.resolved_at = datetime.utcnow()

                db.session.commit()

                reply_dict = comment_to_dict(_ai_reply, include_replies=False)
                reply_dict["document"] = {"id": _doc.id, "title": _doc.title, "node_type": _doc.node_type.value}

                # Emit comment events
                reply_event_payload = {'parent_id': comment_id, 'reply': reply_dict}
                _emit_comment_event(_comment.document_id, 'reply_created', reply_event_payload)
                _emit_workspace_comment_event(_doc.workspace_id, 'reply_created', reply_event_payload)

                if auto_resolve:
                    comment_dict = comment_to_dict(_comment)
                    comment_dict["document"] = {"id": _doc.id, "title": _doc.title, "node_type": _doc.node_type.value}
                    _emit_comment_event(_comment.document_id, 'updated', comment_dict)
                    _emit_workspace_comment_event(_doc.workspace_id, 'updated', comment_dict)

                # Emit completion event with updated range
                socketio.emit('latex_collab:ai_resolve:completed', {
                    'comment_id': comment_id,
                    'workspace_id': workspace_id,
                    'document_id': document_id,
                    'changes': {
                        'range_start': range_start,
                        'range_end': range_end,  # Original end position (for replacement)
                        'old_text': old_text,
                        'new_text': new_text,
                        'new_range_end': new_range_end,  # New end position after replacement
                    },
                    'reply': reply_dict,
                    'comment_updated': {  # Updated comment data for frontend sync
                        'id': comment_id,
                        'range_start': range_start,
                        'range_end': new_range_end,
                    },
                })

                # Clear stream state after a delay (allow reconnecting clients to fetch result)
                import threading
                def clear_later():
                    import time
                    time.sleep(30)  # Keep result available for 30 seconds
                    CommentAIService.clear_stream(comment_id)
                threading.Thread(target=clear_later, daemon=True).start()

        def on_error(error_msg: str):
            """Emit error via Socket.IO"""
            with app.app_context():
                socketio.emit('latex_collab:ai_resolve:error', {
                    'comment_id': comment_id,
                    'workspace_id': workspace_id,
                    'document_id': document_id,
                    'error': error_msg,
                })
            # Clear stream state
            CommentAIService.clear_stream(comment_id)

        # Start streaming
        started = CommentAIService.resolve_comment_streaming(
            comment=comment,
            document=doc,
            on_token=on_token,
            on_complete=on_complete,
            on_error=on_error,
            model_id=model_id,
        )

        if not started:
            raise ValidationError("Failed to start AI streaming")

        return jsonify({
            "success": True,
            "streaming": True,
            "comment_id": comment_id,
            "document_id": doc.id,
            "workspace_id": doc.workspace_id,
        }), 200

    else:
        # Legacy non-streaming mode
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

        if auto_resolve:
            comment.resolved_at = datetime.utcnow()

        db.session.commit()

        reply_dict = comment_to_dict(ai_reply, include_replies=False)
        reply_dict["document"] = {"id": doc.id, "title": doc.title, "node_type": doc.node_type.value}

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
