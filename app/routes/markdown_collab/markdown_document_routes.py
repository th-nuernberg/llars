# markdown_document_routes.py
"""
Markdown Collab Document Routes - document CRUD and commits.
"""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request, current_app

from auth.auth_utils import AuthUtils
from db.db import db
from db.tables import (
    MarkdownWorkspace,
    MarkdownDocument,
    MarkdownCommit,
    MarkdownNodeType,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError
from decorators.permission_decorator import require_permission
from .markdown_collab_helpers import (
    _require_workspace_access,
    _require_document_access,
    _doc_to_dict,
    _get_next_order_index,
    _resequence_children,
    _insert_into_parent,
)

markdown_document_bp = Blueprint("markdown_document", __name__)


@markdown_document_bp.route("/documents", methods=["POST"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def create_document():
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    data = request.get_json() or {}
    workspace_id = data.get("workspace_id")
    parent_id = data.get("parent_id")
    title = (data.get("title") or "").strip()
    node_type = (data.get("type") or data.get("node_type") or "file").strip().lower()

    if not workspace_id:
        raise ValidationError("workspace_id is required")
    if not title:
        raise ValidationError("title is required")
    if node_type not in {"file", "folder"}:
        raise ValidationError("type must be file|folder")

    ws = MarkdownWorkspace.query.get(int(workspace_id))
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    if parent_id is not None:
        parent_id = int(parent_id)
        parent = MarkdownDocument.query.get(parent_id)
        if not parent or parent.workspace_id != ws.id:
            raise ValidationError("Invalid parent_id")
        if (parent.node_type.value if hasattr(parent.node_type, "value") else str(parent.node_type)) != "folder":
            raise ValidationError("parent_id must reference a folder")

    existing = MarkdownDocument.query.filter_by(workspace_id=ws.id, parent_id=parent_id, title=title).first()
    if existing:
        raise ValidationError("A node with this title already exists in the selected folder")

    doc = MarkdownDocument(
        workspace_id=ws.id,
        parent_id=parent_id,
        node_type=MarkdownNodeType.folder if node_type == "folder" else MarkdownNodeType.file,
        title=title,
        order_index=_get_next_order_index(ws.id, parent_id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(doc)
    db.session.flush()

    if node_type == "file":
        doc.yjs_doc_id = f"markdown_{doc.id}"

    db.session.commit()
    return jsonify({"success": True, "node": _doc_to_dict(doc)}), 201


@markdown_document_bp.route("/documents/<int:document_id>", methods=["PATCH"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def update_document(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    data = request.get_json() or {}
    new_title = data.get("title")
    new_parent_id = data.get("parent_id", doc.parent_id)
    new_order_index = data.get("order_index")

    if new_parent_id is not None:
        new_parent_id = int(new_parent_id)

    if new_title is not None:
        new_title = str(new_title).strip()
        if not new_title:
            raise ValidationError("title cannot be empty")
        existing = MarkdownDocument.query.filter_by(
            workspace_id=doc.workspace_id,
            parent_id=new_parent_id,
            title=new_title,
        ).filter(MarkdownDocument.id != doc.id).first()
        if existing:
            raise ValidationError("A node with this title already exists in the selected folder")
        doc.title = new_title

    old_parent_id = doc.parent_id
    if new_parent_id is not None:
        parent = MarkdownDocument.query.get(int(new_parent_id))
        if not parent or parent.workspace_id != doc.workspace_id:
            raise ValidationError("Invalid parent_id")
        if (parent.node_type.value if hasattr(parent.node_type, "value") else str(parent.node_type)) != "folder":
            raise ValidationError("parent_id must reference a folder")
        if parent.id == doc.id:
            raise ValidationError("A node cannot be its own parent")

        # Prevent cycles: do not allow moving a node into its own subtree
        cursor = parent
        while cursor and cursor.parent_id is not None:
            if cursor.parent_id == doc.id:
                raise ValidationError("Cannot move a node into its own subtree")
            cursor = MarkdownDocument.query.get(cursor.parent_id)

    if new_order_index is None:
        # If parent changed, append to the end of the new parent.
        if new_parent_id != old_parent_id:
            doc.parent_id = new_parent_id
            doc.order_index = _get_next_order_index(doc.workspace_id, new_parent_id)
            _resequence_children(doc.workspace_id, old_parent_id)
            _resequence_children(doc.workspace_id, new_parent_id)
    else:
        _insert_into_parent(doc, new_parent_id, int(new_order_index))
        if new_parent_id != old_parent_id:
            _resequence_children(doc.workspace_id, old_parent_id)

    doc.updated_at = datetime.utcnow()
    doc.last_editor_username = username
    db.session.commit()
    return jsonify({"success": True, "node": _doc_to_dict(doc)}), 200


@markdown_document_bp.route("/documents/<int:document_id>", methods=["DELETE"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def delete_document(document_id: int):
    """Delete a document or folder.

    For files with commits: soft-delete (set deleted_at) to allow restore via git panel.
    For folders or files without commits: hard-delete.
    """
    from datetime import timezone

    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    workspace_id = doc.workspace_id
    parent_id = doc.parent_id

    # Check if this is a file with commits (can be soft-deleted)
    is_file = doc.node_type == MarkdownNodeType.file
    has_commits = MarkdownCommit.query.filter_by(document_id=doc.id).first() is not None

    if is_file and has_commits:
        # Soft-delete: mark as deleted but keep in DB for restore
        doc.deleted_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({"success": True, "soft_deleted": True}), 200

    # Hard-delete for folders or files without commits
    db.session.delete(doc)
    db.session.flush()

    _resequence_children(workspace_id, parent_id)
    db.session.commit()
    return jsonify({"success": True}), 200


@markdown_document_bp.route("/documents/<int:document_id>/commits", methods=["GET"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def list_commits(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    commits = (
        MarkdownCommit.query
        .filter_by(document_id=document_id)
        .order_by(MarkdownCommit.created_at.desc(), MarkdownCommit.id.desc())
        .limit(200)
        .all()
    )

    return jsonify({
        "success": True,
        "commits": [
            {
                "id": c.id,
                "document_id": c.document_id,
                "author_username": c.author_username,
                "message": c.message,
                "diff_summary": c.diff_summary,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in commits
        ],
    }), 200


@markdown_document_bp.route("/documents/<int:document_id>/commits/<int:commit_id>", methods=["GET"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def get_commit(document_id: int, commit_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    commit = MarkdownCommit.query.filter_by(document_id=document_id, id=commit_id).first()
    if not commit:
        raise NotFoundError("Commit not found")

    return jsonify({
        "success": True,
        "commit": {
            "id": commit.id,
            "document_id": commit.document_id,
            "author_username": commit.author_username,
            "message": commit.message,
            "diff_summary": commit.diff_summary,
            "content_snapshot": commit.content_snapshot,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
        },
    }), 200


@markdown_document_bp.route("/documents/<int:document_id>/commit", methods=["POST"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def create_commit(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    diff_summary = data.get("diff_summary")
    content_snapshot = data.get("content_snapshot")

    if not message:
        raise ValidationError("message is required")

    commit = MarkdownCommit(
        document_id=document_id,
        author_username=username,
        message=message,
        diff_summary=diff_summary,
        content_snapshot=content_snapshot,
        created_at=datetime.utcnow(),
    )
    db.session.add(commit)
    db.session.commit()

    socketio = current_app.extensions.get('socketio')
    if socketio:
        try:
            from socketio_handlers.events_markdown_collab import emit_commit_created
            emit_commit_created(socketio, document_id, {
                "id": commit.id,
                "document_id": commit.document_id,
                "author_username": commit.author_username,
                "message": commit.message,
                "diff_summary": commit.diff_summary,
                "content_snapshot": commit.content_snapshot,
                "created_at": commit.created_at.isoformat() if commit.created_at else None,
            })
        except Exception:
            # Do not fail the request if socket emission fails
            pass

    return jsonify({
        "success": True,
        "commit": {
            "id": commit.id,
            "document_id": commit.document_id,
            "author_username": commit.author_username,
            "message": commit.message,
            "diff_summary": commit.diff_summary,
            "content_snapshot": commit.content_snapshot,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
        },
    }), 201


@markdown_document_bp.route("/documents/<int:document_id>/baseline", methods=["GET"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def get_baseline(document_id: int):
    """Get the content snapshot from the latest commit for diff comparison."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    # Get the latest commit with a content_snapshot
    latest_commit = (
        MarkdownCommit.query
        .filter_by(document_id=document_id)
        .filter(MarkdownCommit.content_snapshot.isnot(None))
        .order_by(MarkdownCommit.created_at.desc(), MarkdownCommit.id.desc())
        .first()
    )

    if not latest_commit:
        return jsonify({
            "success": True,
            "baseline": None,
            "commit_id": None,
            "message": "No commits with content snapshot found",
        }), 200

    current_content = doc.content_text or ""
    baseline_commit = latest_commit
    if (latest_commit.content_snapshot or "") == "":
        non_empty_commit = (
            MarkdownCommit.query
            .filter_by(document_id=document_id)
            .filter(MarkdownCommit.content_snapshot.isnot(None))
            .filter(MarkdownCommit.content_snapshot != "")
            .order_by(MarkdownCommit.created_at.desc(), MarkdownCommit.id.desc())
            .first()
        )
        if non_empty_commit and current_content == (non_empty_commit.content_snapshot or ""):
            baseline_commit = non_empty_commit

    return jsonify({
        "success": True,
        "baseline": baseline_commit.content_snapshot,
        "commit_id": baseline_commit.id,
        "commit_message": baseline_commit.message,
        "commit_author": baseline_commit.author_username,
        "commit_date": baseline_commit.created_at.isoformat() if baseline_commit.created_at else None,
    }), 200


@markdown_document_bp.route("/documents/<int:document_id>/rollback", methods=["POST"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def rollback_document(document_id: int):
    """Rollback a document to its last committed state."""
    import logging
    logger = logging.getLogger("markdown_collab")

    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    latest_commit = (
        MarkdownCommit.query
        .filter_by(document_id=document_id)
        .filter(MarkdownCommit.content_snapshot.isnot(None))
        .order_by(MarkdownCommit.created_at.desc(), MarkdownCommit.id.desc())
        .first()
    )

    if not latest_commit:
        raise NotFoundError("No commits found for this document - nothing to rollback to")

    data = request.get_json() or {}
    force = bool(data.get("force"))
    non_empty_commit = (
        MarkdownCommit.query
        .filter_by(document_id=document_id)
        .filter(MarkdownCommit.content_snapshot.isnot(None))
        .filter(MarkdownCommit.content_snapshot != "")
        .order_by(MarkdownCommit.created_at.desc(), MarkdownCommit.id.desc())
        .first()
    )
    target_commit = latest_commit
    if not force and (latest_commit.content_snapshot or "") == "" and non_empty_commit:
        target_commit = non_empty_commit

    baseline_content = target_commit.content_snapshot or ""
    current_content = doc.content_text or ""

    if baseline_content == "" and current_content and not force:
        raise ConflictError(
            "Rollback baseline is empty. Set force=true to confirm clearing the document.",
            details={
                "requires_force": True,
                "baseline_empty": True,
                "commit_id": target_commit.id,
                "commit_message": target_commit.message,
            },
        )

    if current_content == baseline_content:
        return jsonify({
            "success": True,
            "message": "Document already matches baseline - no rollback needed",
            "rolled_back": False,
        }), 200

    doc.content_text = baseline_content
    # Clear cached Yjs JSON so server reload uses the new baseline text.
    doc.content = None
    doc.updated_at = datetime.utcnow()
    db.session.commit()

    logger.info(f"[MarkdownCollab] Document {document_id} rolled back by {username}")

    return jsonify({
        "success": True,
        "message": "Document rolled back to last committed state",
        "rolled_back": True,
        "commit_id": target_commit.id,
        "commit_message": target_commit.message,
        "commit_author": target_commit.author_username,
        "baseline": baseline_content,
    }), 200


@markdown_document_bp.route("/documents/<int:document_id>/restore", methods=["POST"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def restore_document(document_id: int):
    """Restore a soft-deleted document."""
    import logging
    from datetime import timezone
    logger = logging.getLogger("markdown_collab")

    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")

    if doc.deleted_at is None:
        return jsonify({
            "success": True,
            "message": "Document is not deleted - nothing to restore",
            "restored": False,
        }), 200

    _require_document_access(doc, username)

    # Restore the document
    doc.deleted_at = None
    doc.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info(f"[MarkdownCollab] Document {document_id} restored by {username}")

    return jsonify({
        "success": True,
        "message": "Document restored successfully",
        "restored": True,
        "document": {
            "id": doc.id,
            "title": doc.title,
            "workspace_id": doc.workspace_id,
        },
    }), 200
