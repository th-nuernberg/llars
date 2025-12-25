"""
LaTeX Collab API Routes

Provides workspace, document, asset, commit, compile, and comment endpoints.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
from io import BytesIO
from typing import Optional

from flask import Blueprint, jsonify, request, current_app, send_file
from sqlalchemy import or_

from auth.auth_utils import AuthUtils
from db.db import db
from db.tables import (
    LatexWorkspace,
    LatexWorkspaceMember,
    LatexDocument,
    LatexAsset,
    LatexCommit,
    LatexCompileJob,
    LatexComment,
    LatexNodeType,
    LatexWorkspaceVisibility,
    User,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ForbiddenError
from decorators.permission_decorator import require_permission
from services.permission_service import PermissionService
from services.latex_compile_service import (
    build_workspace_snapshot,
    run_compile_job,
    synctex_forward_search,
    synctex_inverse_search,
    LatexCompileError,
)

latex_collab_bp = Blueprint("latex_collab", __name__, url_prefix="/api/latex-collab")


def _is_admin(username: Optional[str]) -> bool:
    if not username:
        return False
    return PermissionService.check_permission(username, "admin:permissions:manage")


def _require_workspace_access(workspace: LatexWorkspace, username: str) -> None:
    if _is_admin(username):
        return
    if workspace.owner_username != username:
        member = LatexWorkspaceMember.query.filter_by(workspace_id=workspace.id, username=username).first()
        if not member:
            raise ForbiddenError("Kein Zugriff auf diesen Workspace")


def _require_workspace_manage(workspace: LatexWorkspace, username: str) -> None:
    if _is_admin(username):
        return
    if workspace.owner_username != username:
        raise ForbiddenError("Kein Zugriff auf diesen Workspace")


def _require_document_access(document: LatexDocument, username: str) -> None:
    if _is_admin(username):
        return
    if document.workspace and document.workspace.owner_username == username:
        return
    member = LatexWorkspaceMember.query.filter_by(workspace_id=document.workspace_id, username=username).first()
    if member:
        return
    raise ForbiddenError("Kein Zugriff auf dieses Dokument")


def _ensure_safe_title(title: str) -> None:
    if "/" in title or "\\" in title:
        raise ValidationError("Dateiname darf keine Pfad-Trenner enthalten")
    if ".." in title:
        raise ValidationError("Dateiname darf keine relativen Pfade enthalten")


def _doc_to_dict(doc: LatexDocument) -> dict:
    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "parent_id": doc.parent_id,
        "type": doc.node_type.value if hasattr(doc.node_type, "value") else str(doc.node_type),
        "title": doc.title,
        "slug": doc.slug,
        "order_index": doc.order_index,
        "yjs_doc_id": doc.yjs_doc_id,
        "asset_id": doc.asset_id,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _workspace_to_dict(ws: LatexWorkspace) -> dict:
    return {
        "id": ws.id,
        "name": ws.name,
        "owner_username": ws.owner_username,
        "visibility": ws.visibility.value if hasattr(ws.visibility, "value") else str(ws.visibility),
        "main_document_id": ws.main_document_id,
        "latest_compile_job_id": ws.latest_compile_job_id,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
    }


def _comment_to_dict(comment: LatexComment) -> dict:
    return {
        "id": comment.id,
        "document_id": comment.document_id,
        "author_username": comment.author_username,
        "range_start": comment.range_start,
        "range_end": comment.range_end,
        "body": comment.body,
        "resolved_at": comment.resolved_at.isoformat() if comment.resolved_at else None,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


def _get_next_order_index(workspace_id: int, parent_id: Optional[int]) -> int:
    q = LatexDocument.query.filter_by(workspace_id=workspace_id, parent_id=parent_id)
    max_idx = q.with_entities(db.func.max(LatexDocument.order_index)).scalar()
    return int(max_idx + 1) if max_idx is not None else 0


def _resequence_children(workspace_id: int, parent_id: Optional[int]) -> None:
    siblings = (
        LatexDocument.query
        .filter_by(workspace_id=workspace_id, parent_id=parent_id)
        .order_by(LatexDocument.order_index.asc(), LatexDocument.id.asc())
        .all()
    )
    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx


def _insert_into_parent(node: LatexDocument, new_parent_id: Optional[int], new_index: int) -> None:
    siblings = (
        LatexDocument.query
        .filter(
            LatexDocument.workspace_id == node.workspace_id,
            LatexDocument.parent_id == new_parent_id,
            LatexDocument.id != node.id,
        )
        .order_by(LatexDocument.order_index.asc(), LatexDocument.id.asc())
        .all()
    )

    new_index = max(0, min(int(new_index), len(siblings)))
    siblings.insert(new_index, node)

    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx
        if sibling.id == node.id:
            sibling.parent_id = new_parent_id


@latex_collab_bp.route("/workspaces", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_workspaces():
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    query = LatexWorkspace.query.order_by(LatexWorkspace.updated_at.desc())
    if not _is_admin(username):
        member_rows = LatexWorkspaceMember.query.filter_by(username=username).all()
        member_workspace_ids = {r.workspace_id for r in member_rows}
        if member_workspace_ids:
            query = query.filter(or_(
                LatexWorkspace.owner_username == username,
                LatexWorkspace.id.in_(member_workspace_ids),
            ))
        else:
            query = query.filter(LatexWorkspace.owner_username == username)

    workspaces = [_workspace_to_dict(ws) for ws in query.all()]
    return jsonify({"success": True, "workspaces": workspaces}), 200


@latex_collab_bp.route("/workspaces", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
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

    ws = LatexWorkspace(
        name=name,
        owner_username=username,
        visibility=LatexWorkspaceVisibility(visibility),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(ws)
    db.session.flush()

    # Seed a minimal main.tex file for better UX
    template_text = (
        "\\documentclass{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\title{New Document}\n"
        "\\author{LLARS}\n"
        "\\date{\\today}\n\n"
        "\\begin{document}\n"
        "\\maketitle\n\n"
        "Hello from LaTeX Collab.\n"
        "\\end{document}\n"
    )
    doc = LatexDocument(
        workspace_id=ws.id,
        parent_id=None,
        node_type=LatexNodeType.file,
        title="main.tex",
        order_index=0,
        content_text=template_text,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(doc)
    db.session.flush()
    doc.yjs_doc_id = f"latex_{doc.id}"
    ws.main_document_id = doc.id

    db.session.commit()
    return jsonify({"success": True, "workspace": _workspace_to_dict(ws)}), 201


@latex_collab_bp.route("/workspaces/<int:workspace_id>/members", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_workspace_members(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    members = (
        LatexWorkspaceMember.query
        .filter_by(workspace_id=workspace_id)
        .order_by(LatexWorkspaceMember.username.asc())
        .all()
    )

    member_usernames = [m.username for m in members]
    users_by_name = {u.username: u for u in User.query.filter(User.username.in_(member_usernames)).all()}

    def build_member_dict(m):
        user = users_by_name.get(m.username)
        avatar_url = None
        avatar_seed = None
        collab_color = None
        if user:
            if user.avatar_public_id and user.avatar_file:
                avatar_url = f"/api/users/avatar/{user.avatar_public_id}"
            avatar_seed = user.avatar_seed
            collab_color = user.collab_color
        return {
            "username": m.username,
            "added_at": m.added_at.isoformat() if m.added_at else None,
            "added_by": m.added_by,
            "avatar_url": avatar_url,
            "avatar_seed": avatar_seed,
            "collab_color": collab_color,
        }

    owner_user = User.query.filter_by(username=ws.owner_username).first()
    owner_dict = {
        "username": ws.owner_username,
        "avatar_url": None,
        "avatar_seed": owner_user.avatar_seed if owner_user else None,
        "collab_color": owner_user.collab_color if owner_user else None,
    }
    if owner_user and owner_user.avatar_public_id and owner_user.avatar_file:
        owner_dict["avatar_url"] = f"/api/users/avatar/{owner_user.avatar_public_id}"

    return jsonify({
        "success": True,
        "owner": owner_dict,
        "members": [build_member_dict(m) for m in members],
    }), 200


@latex_collab_bp.route("/workspaces/<int:workspace_id>/members", methods=["POST"])
@require_permission("feature:latex_collab:share")
@handle_api_errors(logger_name="latex_collab")
def add_workspace_member(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_manage(ws, username)

    data = request.get_json() or {}
    member_username = (data.get("username") or "").strip()
    if not member_username:
        raise ValidationError("username is required")
    if member_username == ws.owner_username:
        raise ValidationError("Owner is already a member")

    user = User.query.filter_by(username=member_username).first()
    if not user:
        raise NotFoundError("User not found")

    existing = LatexWorkspaceMember.query.filter_by(workspace_id=workspace_id, username=member_username).first()
    if existing:
        raise ValidationError("User is already a member")

    member = LatexWorkspaceMember(
        workspace_id=workspace_id,
        username=member_username,
        added_by=username,
        added_at=datetime.utcnow(),
    )
    db.session.add(member)
    db.session.commit()

    socketio = current_app.extensions.get('socketio')
    if socketio:
        try:
            from socketio_handlers.events_latex_collab import emit_workspace_shared
            emit_workspace_shared(socketio, user.id, _workspace_to_dict(ws))
        except Exception:
            pass

    return jsonify({"success": True, "member": {"username": member_username}}), 201


@latex_collab_bp.route("/workspaces/<int:workspace_id>/members/<member_username>", methods=["DELETE"])
@require_permission("feature:latex_collab:share")
@handle_api_errors(logger_name="latex_collab")
def remove_workspace_member(workspace_id: int, member_username: str):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_manage(ws, username)

    member = LatexWorkspaceMember.query.filter_by(workspace_id=workspace_id, username=member_username).first()
    if not member:
        raise NotFoundError("Mitglied nicht gefunden")

    db.session.delete(member)
    db.session.commit()
    return jsonify({"success": True}), 200


@latex_collab_bp.route("/workspaces/<int:workspace_id>", methods=["DELETE"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def delete_workspace(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_manage(ws, username)

    db.session.delete(ws)
    db.session.commit()
    return jsonify({"success": True}), 200


@latex_collab_bp.route("/workspaces/<int:workspace_id>/leave", methods=["POST"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def leave_workspace(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")

    if ws.owner_username == username:
        raise ValidationError("Owner kann den Workspace nicht verlassen")

    member = LatexWorkspaceMember.query.filter_by(workspace_id=workspace_id, username=username).first()
    if not member:
        raise NotFoundError("Sie sind kein Mitglied dieses Workspaces")

    db.session.delete(member)
    db.session.commit()
    return jsonify({"success": True, "message": "Workspace verlassen"}), 200


@latex_collab_bp.route("/workspaces/<int:workspace_id>/tree", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_workspace_tree(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    docs = (
        LatexDocument.query
        .filter_by(workspace_id=workspace_id)
        .order_by(LatexDocument.parent_id.asc(), LatexDocument.order_index.asc(), LatexDocument.id.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "workspace": _workspace_to_dict(ws),
        "nodes": [_doc_to_dict(d) for d in docs],
    }), 200


@latex_collab_bp.route("/workspaces/<int:workspace_id>/main", methods=["PATCH"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def set_main_document(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    data = request.get_json() or {}
    document_id = data.get("document_id")
    if not document_id:
        raise ValidationError("document_id is required")

    doc = LatexDocument.query.get(int(document_id))
    if not doc or doc.workspace_id != ws.id:
        raise ValidationError("Invalid document_id")
    if (doc.node_type.value if hasattr(doc.node_type, "value") else str(doc.node_type)) != "file":
        raise ValidationError("document_id must reference a file")

    ws.main_document_id = doc.id
    ws.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"success": True, "workspace": _workspace_to_dict(ws)}), 200


@latex_collab_bp.route("/documents", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_document():
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    data = request.get_json() or {}
    workspace_id = data.get("workspace_id")
    parent_id = data.get("parent_id")
    title = (data.get("title") or "").strip()
    node_type = (data.get("type") or data.get("node_type") or "file").strip().lower()
    asset_id = data.get("asset_id")
    initial_content = data.get("initial_content")

    if not workspace_id:
        raise ValidationError("workspace_id is required")
    if not title:
        raise ValidationError("title is required")
    if node_type not in {"file", "folder"}:
        raise ValidationError("type must be file|folder")
    _ensure_safe_title(title)

    ws = LatexWorkspace.query.get(int(workspace_id))
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    if parent_id is not None:
        parent_id = int(parent_id)
        parent = LatexDocument.query.get(parent_id)
        if not parent or parent.workspace_id != ws.id:
            raise ValidationError("Invalid parent_id")
        if (parent.node_type.value if hasattr(parent.node_type, "value") else str(parent.node_type)) != "folder":
            raise ValidationError("parent_id must reference a folder")

    existing = LatexDocument.query.filter_by(workspace_id=ws.id, parent_id=parent_id, title=title).first()
    if existing:
        raise ValidationError("A node with this title already exists in the selected folder")

    asset_ref = None
    if asset_id:
        asset_ref = LatexAsset.query.get(int(asset_id))
        if not asset_ref or asset_ref.workspace_id != ws.id:
            raise ValidationError("Invalid asset_id")

    doc = LatexDocument(
        workspace_id=ws.id,
        parent_id=parent_id,
        node_type=LatexNodeType.folder if node_type == "folder" else LatexNodeType.file,
        title=title,
        order_index=_get_next_order_index(ws.id, parent_id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    if asset_ref:
        doc.asset_id = asset_ref.id
    if isinstance(initial_content, str) and node_type == "file" and not asset_ref:
        doc.content_text = initial_content

    db.session.add(doc)
    db.session.flush()

    if node_type == "file" and not asset_ref:
        doc.yjs_doc_id = f"latex_{doc.id}"

    db.session.commit()
    return jsonify({"success": True, "node": _doc_to_dict(doc)}), 201


@latex_collab_bp.route("/documents/<int:document_id>", methods=["PATCH"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def update_document(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
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
        _ensure_safe_title(new_title)
        existing = LatexDocument.query.filter_by(
            workspace_id=doc.workspace_id,
            parent_id=new_parent_id,
            title=new_title,
        ).filter(LatexDocument.id != doc.id).first()
        if existing:
            raise ValidationError("A node with this title already exists in the selected folder")
        doc.title = new_title

    old_parent_id = doc.parent_id
    if new_parent_id is not None:
        parent = LatexDocument.query.get(int(new_parent_id))
        if not parent or parent.workspace_id != doc.workspace_id:
            raise ValidationError("Invalid parent_id")
        if (parent.node_type.value if hasattr(parent.node_type, "value") else str(parent.node_type)) != "folder":
            raise ValidationError("parent_id must reference a folder")
        if parent.id == doc.id:
            raise ValidationError("A node cannot be its own parent")

        cursor = parent
        while cursor and cursor.parent_id is not None:
            if cursor.parent_id == doc.id:
                raise ValidationError("Cannot move a node into its own subtree")
            cursor = LatexDocument.query.get(cursor.parent_id)

    if new_order_index is None:
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


@latex_collab_bp.route("/documents/<int:document_id>", methods=["DELETE"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def delete_document(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    workspace_id = doc.workspace_id
    parent_id = doc.parent_id
    if doc.workspace and doc.workspace.main_document_id == doc.id:
        doc.workspace.main_document_id = None

    db.session.delete(doc)
    db.session.flush()

    _resequence_children(workspace_id, parent_id)
    db.session.commit()
    return jsonify({"success": True}), 200


@latex_collab_bp.route("/documents/<int:document_id>/commits", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_commits(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    commits = (
        LatexCommit.query
        .filter_by(document_id=document_id)
        .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
        .limit(200)
        .all()
    )

    return jsonify({
        "success": True,
        "commits": [
            {
                "id": c.id,
                "document_id": c.document_id,
                "workspace_id": c.workspace_id,
                "author_username": c.author_username,
                "message": c.message,
                "diff_summary": c.diff_summary,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in commits
        ],
    }), 200


@latex_collab_bp.route("/documents/<int:document_id>/commits/<int:commit_id>", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_commit(document_id: int, commit_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    commit = LatexCommit.query.filter_by(document_id=document_id, id=commit_id).first()
    if not commit:
        raise NotFoundError("Commit not found")

    return jsonify({
        "success": True,
        "commit": {
            "id": commit.id,
            "document_id": commit.document_id,
            "workspace_id": commit.workspace_id,
            "author_username": commit.author_username,
            "message": commit.message,
            "diff_summary": commit.diff_summary,
            "content_snapshot": commit.content_snapshot,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
        },
    }), 200


@latex_collab_bp.route("/documents/<int:document_id>/commit", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_commit(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    diff_summary = data.get("diff_summary")
    content_snapshot = data.get("content_snapshot")
    workspace_snapshot = data.get("workspace_snapshot")

    if not message:
        raise ValidationError("message is required")

    if not workspace_snapshot:
        workspace_snapshot = build_workspace_snapshot(doc.workspace_id)
    if isinstance(content_snapshot, str) and workspace_snapshot:
        for node in workspace_snapshot.get("nodes", []):
            if node.get("id") == doc.id and node.get("node_type") == "file" and not node.get("asset_id"):
                node["content_text"] = content_snapshot
                break

    commit = LatexCommit(
        workspace_id=doc.workspace_id,
        document_id=doc.id,
        author_username=username,
        message=message,
        diff_summary=diff_summary,
        content_snapshot=content_snapshot,
        workspace_snapshot=workspace_snapshot,
        created_at=datetime.utcnow(),
    )
    db.session.add(commit)
    db.session.commit()

    socketio = current_app.extensions.get('socketio')
    if socketio:
        try:
            from socketio_handlers.events_latex_collab import emit_commit_created
            emit_commit_created(socketio, document_id, {
                "id": commit.id,
                "document_id": commit.document_id,
                "workspace_id": commit.workspace_id,
                "author_username": commit.author_username,
                "message": commit.message,
                "diff_summary": commit.diff_summary,
                "content_snapshot": commit.content_snapshot,
                "created_at": commit.created_at.isoformat() if commit.created_at else None,
            })
        except Exception:
            pass

    return jsonify({
        "success": True,
        "commit": {
            "id": commit.id,
            "document_id": commit.document_id,
            "workspace_id": commit.workspace_id,
            "author_username": commit.author_username,
            "message": commit.message,
            "diff_summary": commit.diff_summary,
            "content_snapshot": commit.content_snapshot,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
        },
    }), 201


@latex_collab_bp.route("/documents/<int:document_id>/baseline", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_baseline(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    latest_commit = (
        LatexCommit.query
        .filter_by(document_id=document_id)
        .filter(LatexCommit.content_snapshot.isnot(None))
        .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
        .first()
    )

    if not latest_commit:
        return jsonify({
            "success": True,
            "baseline": None,
            "commit_id": None,
            "message": "No commits with content snapshot found",
        }), 200

    return jsonify({
        "success": True,
        "baseline": latest_commit.content_snapshot,
        "commit_id": latest_commit.id,
        "commit_message": latest_commit.message,
        "commit_author": latest_commit.author_username,
        "commit_date": latest_commit.created_at.isoformat() if latest_commit.created_at else None,
    }), 200


@latex_collab_bp.route("/documents/<int:document_id>/comments", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_comments(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    comments = (
        LatexComment.query
        .filter_by(document_id=document_id)
        .order_by(LatexComment.created_at.asc(), LatexComment.id.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "comments": [_comment_to_dict(c) for c in comments],
    }), 200


@latex_collab_bp.route("/documents/<int:document_id>/comments", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_comment(document_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

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

    return jsonify({"success": True, "comment": _comment_to_dict(comment)}), 201


@latex_collab_bp.route("/comments/<int:comment_id>", methods=["PATCH"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def update_comment(comment_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    comment = LatexComment.query.get(comment_id)
    if not comment:
        raise NotFoundError("Comment not found")

    doc = LatexDocument.query.get(comment.document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

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
    return jsonify({"success": True, "comment": _comment_to_dict(comment)}), 200


@latex_collab_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def delete_comment(comment_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    comment = LatexComment.query.get(comment_id)
    if not comment:
        raise NotFoundError("Comment not found")

    doc = LatexDocument.query.get(comment.document_id)
    if not doc:
        raise NotFoundError("Document not found")
    _require_document_access(doc, username)

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"success": True}), 200


@latex_collab_bp.route("/workspaces/<int:workspace_id>/assets", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def upload_asset(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    file = request.files.get("file")
    if not file:
        raise ValidationError("file is required")

    parent_id = request.form.get("parent_id")
    if parent_id is not None:
        parent_id = int(parent_id)
        parent = LatexDocument.query.get(parent_id)
        if not parent or parent.workspace_id != ws.id:
            raise ValidationError("Invalid parent_id")
        if (parent.node_type.value if hasattr(parent.node_type, "value") else str(parent.node_type)) != "folder":
            raise ValidationError("parent_id must reference a folder")

    filename = (file.filename or "").strip()
    if not filename:
        raise ValidationError("filename is required")
    _ensure_safe_title(filename)

    existing = LatexDocument.query.filter_by(workspace_id=ws.id, parent_id=parent_id, title=filename).first()
    if existing:
        raise ValidationError("A node with this title already exists in the selected folder")

    data = file.read()
    sha256 = hashlib.sha256(data).hexdigest() if data else None
    asset = LatexAsset(
        workspace_id=ws.id,
        filename=filename,
        mime_type=file.mimetype,
        file_size_bytes=len(data),
        sha256=sha256,
        data=data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(asset)
    db.session.flush()

    doc = LatexDocument(
        workspace_id=ws.id,
        parent_id=parent_id,
        node_type=LatexNodeType.file,
        title=filename,
        order_index=_get_next_order_index(ws.id, parent_id),
        asset_id=asset.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({"success": True, "asset_id": asset.id, "node": _doc_to_dict(doc)}), 201


@latex_collab_bp.route("/assets/<int:asset_id>", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_asset(asset_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    asset = LatexAsset.query.get(asset_id)
    if not asset:
        raise NotFoundError("Asset not found")

    ws = LatexWorkspace.query.get(asset.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    return send_file(
        BytesIO(asset.data),
        mimetype=asset.mime_type or "application/octet-stream",
        download_name=asset.filename,
        as_attachment=False,
    )


@latex_collab_bp.route("/workspaces/<int:workspace_id>/compile", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def compile_workspace(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    data = request.get_json() or {}
    commit_id = data.get("commit_id")
    if commit_id:
        commit = LatexCommit.query.get(int(commit_id))
        if not commit or commit.workspace_id != ws.id:
            raise ValidationError("Invalid commit_id")

    job = LatexCompileJob(
        workspace_id=ws.id,
        commit_id=int(commit_id) if commit_id else None,
        status="queued",
        created_at=datetime.utcnow(),
    )
    db.session.add(job)
    db.session.flush()

    ws.latest_compile_job_id = job.id
    ws.updated_at = datetime.utcnow()
    db.session.commit()

    socketio = current_app.extensions.get('socketio')
    if socketio:
        app = current_app._get_current_object()
        socketio.start_background_task(_run_compile_background, app, job.id)
    else:
        run_compile_job(job.id)

    return jsonify({
        "success": True,
        "job": {
            "id": job.id,
            "workspace_id": job.workspace_id,
            "commit_id": job.commit_id,
            "status": job.status,
        },
    }), 202


def _run_compile_background(app, job_id: int) -> None:
    with app.app_context():
        run_compile_job(job_id)


@latex_collab_bp.route("/compile/<int:job_id>", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_compile_job(job_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    job = LatexCompileJob.query.get(job_id)
    if not job:
        raise NotFoundError("Compile job not found")

    ws = LatexWorkspace.query.get(job.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    return jsonify({
        "success": True,
        "job": {
            "id": job.id,
            "workspace_id": job.workspace_id,
            "commit_id": job.commit_id,
            "status": job.status,
            "error_message": job.error_message,
            "log_text": job.log_text,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "has_pdf": job.pdf_blob is not None,
            "has_synctex": job.synctex_blob is not None,
        },
    }), 200


@latex_collab_bp.route("/compile/<int:job_id>/synctex/forward", methods=["POST"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def synctex_forward(job_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    job = LatexCompileJob.query.get(job_id)
    if not job:
        raise NotFoundError("Compile job not found")

    ws = LatexWorkspace.query.get(job.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    data = request.get_json() or {}
    document_id = data.get("document_id")
    line = data.get("line")
    column = data.get("column", 1)

    if not document_id:
        raise ValidationError("document_id is required")
    if not isinstance(line, int) or line <= 0:
        raise ValidationError("line must be a positive integer")
    if not isinstance(column, int) or column <= 0:
        raise ValidationError("column must be a positive integer")

    if job.status != "success" or not job.pdf_blob or not job.synctex_blob:
        return jsonify({"success": False, "location": None, "error": "SyncTeX data not available"}), 200

    try:
        location = synctex_forward_search(job_id, int(document_id), line, column)
    except LatexCompileError as exc:
        msg = str(exc)
        if "no location" in msg.lower():
            return jsonify({"success": False, "location": None, "error": msg}), 200
        raise ValidationError(msg) from exc

    return jsonify({"success": True, "location": location}), 200


@latex_collab_bp.route("/compile/<int:job_id>/synctex/inverse", methods=["POST"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def synctex_inverse(job_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    job = LatexCompileJob.query.get(job_id)
    if not job:
        raise NotFoundError("Compile job not found")

    ws = LatexWorkspace.query.get(job.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    data = request.get_json() or {}
    page = data.get("page")
    x = data.get("x")
    y = data.get("y")

    if not isinstance(page, int) or page <= 0:
        raise ValidationError("page must be a positive integer")
    if x is None or y is None:
        raise ValidationError("x and y are required")

    if job.status != "success" or not job.pdf_blob or not job.synctex_blob:
        return jsonify({"success": False, "location": None, "error": "SyncTeX data not available"}), 200

    try:
        location = synctex_inverse_search(job_id, int(page), float(x), float(y))
    except LatexCompileError as exc:
        msg = str(exc)
        if "no source location" in msg.lower() or "no location" in msg.lower():
            return jsonify({"success": False, "location": None, "error": msg}), 200
        raise ValidationError(msg) from exc

    return jsonify({"success": True, "location": location}), 200


@latex_collab_bp.route("/workspaces/<int:workspace_id>/pdf", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_latest_pdf(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    job_id = request.args.get("job_id")
    if job_id:
        job = LatexCompileJob.query.get(int(job_id))
        if not job or job.workspace_id != ws.id:
            raise NotFoundError("Compile job not found")
    else:
        job = (
            LatexCompileJob.query
            .filter_by(workspace_id=ws.id)
            .filter(LatexCompileJob.pdf_blob.isnot(None))
            .order_by(LatexCompileJob.finished_at.desc(), LatexCompileJob.id.desc())
            .first()
        )

    if not job or not job.pdf_blob:
        raise NotFoundError("No compiled PDF available")

    return send_file(
        BytesIO(job.pdf_blob),
        mimetype="application/pdf",
        download_name=f"workspace_{ws.id}.pdf",
        as_attachment=False,
    )
