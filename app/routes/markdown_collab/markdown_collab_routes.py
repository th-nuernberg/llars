"""
Markdown Collab API Routes

Implements the MVP described in:
docs/docs/projekte/markdown collab/markdown-collab-konzept.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request

from auth.auth_utils import AuthUtils
from db.db import db
from db.tables import MarkdownWorkspace, MarkdownDocument, MarkdownCommit, MarkdownNodeType, MarkdownWorkspaceVisibility
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ForbiddenError
from decorators.permission_decorator import require_permission
from services.permission_service import PermissionService

markdown_collab_bp = Blueprint("markdown_collab", __name__, url_prefix="/api/markdown-collab")


def _is_admin(username: Optional[str]) -> bool:
    if not username:
        return False
    return PermissionService.check_permission(username, "admin:permissions:manage")


def _require_workspace_access(workspace: MarkdownWorkspace, username: str) -> None:
    if _is_admin(username):
        return
    if workspace.owner_username != username:
        raise ForbiddenError("Kein Zugriff auf diesen Workspace")


def _require_document_access(document: MarkdownDocument, username: str) -> None:
    if _is_admin(username):
        return
    if document.workspace and document.workspace.owner_username == username:
        return
    raise ForbiddenError("Kein Zugriff auf dieses Dokument")


def _doc_to_dict(doc: MarkdownDocument) -> dict:
    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "parent_id": doc.parent_id,
        "type": doc.node_type.value if hasattr(doc.node_type, "value") else str(doc.node_type),
        "title": doc.title,
        "slug": doc.slug,
        "order_index": doc.order_index,
        "yjs_doc_id": doc.yjs_doc_id,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _workspace_to_dict(ws: MarkdownWorkspace) -> dict:
    return {
        "id": ws.id,
        "name": ws.name,
        "owner_username": ws.owner_username,
        "visibility": ws.visibility.value if hasattr(ws.visibility, "value") else str(ws.visibility),
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
    }


def _get_next_order_index(workspace_id: int, parent_id: Optional[int]) -> int:
    q = MarkdownDocument.query.filter_by(workspace_id=workspace_id, parent_id=parent_id)
    max_idx = q.with_entities(db.func.max(MarkdownDocument.order_index)).scalar()
    return int(max_idx + 1) if max_idx is not None else 0


def _resequence_children(workspace_id: int, parent_id: Optional[int]) -> None:
    siblings = (
        MarkdownDocument.query
        .filter_by(workspace_id=workspace_id, parent_id=parent_id)
        .order_by(MarkdownDocument.order_index.asc(), MarkdownDocument.id.asc())
        .all()
    )
    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx


def _insert_into_parent(node: MarkdownDocument, new_parent_id: Optional[int], new_index: int) -> None:
    siblings = (
        MarkdownDocument.query
        .filter(
            MarkdownDocument.workspace_id == node.workspace_id,
            MarkdownDocument.parent_id == new_parent_id,
            MarkdownDocument.id != node.id,
        )
        .order_by(MarkdownDocument.order_index.asc(), MarkdownDocument.id.asc())
        .all()
    )

    new_index = max(0, min(int(new_index), len(siblings)))
    siblings.insert(new_index, node)

    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx
        if sibling.id == node.id:
            sibling.parent_id = new_parent_id


@markdown_collab_bp.route("/workspaces", methods=["GET"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def list_workspaces():
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    query = MarkdownWorkspace.query.order_by(MarkdownWorkspace.updated_at.desc())
    if not _is_admin(username):
        query = query.filter(MarkdownWorkspace.owner_username == username)

    workspaces = [_workspace_to_dict(ws) for ws in query.all()]
    return jsonify({"success": True, "workspaces": workspaces}), 200


@markdown_collab_bp.route("/workspaces", methods=["POST"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def create_workspace():
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    data = request.get_json() or {}
    name = (data.get("name") or data.get("title") or "").strip()
    visibility = (data.get("visibility") or "private").strip().lower()

    if not name:
        raise ValidationError("name is required")
    if visibility not in {"private", "team", "org"}:
        raise ValidationError("visibility must be private|team|org")

    ws = MarkdownWorkspace(
        name=name,
        owner_username=username,
        visibility=MarkdownWorkspaceVisibility(visibility),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(ws)
    db.session.commit()
    return jsonify({"success": True, "workspace": _workspace_to_dict(ws)}), 201


@markdown_collab_bp.route("/workspaces/<int:workspace_id>/tree", methods=["GET"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def get_workspace_tree(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = MarkdownWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    docs = (
        MarkdownDocument.query
        .filter_by(workspace_id=workspace_id)
        .order_by(MarkdownDocument.parent_id.asc(), MarkdownDocument.order_index.asc(), MarkdownDocument.id.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "workspace": _workspace_to_dict(ws),
        "nodes": [_doc_to_dict(d) for d in docs],
    }), 200


@markdown_collab_bp.route("/documents", methods=["POST"])
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


@markdown_collab_bp.route("/documents/<int:document_id>", methods=["PATCH"])
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


@markdown_collab_bp.route("/documents/<int:document_id>", methods=["DELETE"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def delete_document(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = MarkdownDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    workspace_id = doc.workspace_id
    parent_id = doc.parent_id
    db.session.delete(doc)
    db.session.flush()

    _resequence_children(workspace_id, parent_id)
    db.session.commit()
    return jsonify({"success": True}), 200


@markdown_collab_bp.route("/documents/<int:document_id>/commits", methods=["GET"])
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


@markdown_collab_bp.route("/documents/<int:document_id>/commit", methods=["POST"])
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

    if not message:
        raise ValidationError("message is required")

    commit = MarkdownCommit(
        document_id=document_id,
        author_username=username,
        message=message,
        diff_summary=diff_summary,
        created_at=datetime.utcnow(),
    )
    db.session.add(commit)
    db.session.commit()

    return jsonify({
        "success": True,
        "commit": {
            "id": commit.id,
            "document_id": commit.document_id,
            "author_username": commit.author_username,
            "message": commit.message,
            "diff_summary": commit.diff_summary,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
        },
    }), 201
