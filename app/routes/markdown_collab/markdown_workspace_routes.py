# markdown_workspace_routes.py
"""
Markdown Collab Workspace Routes - workspace and member management.
"""

from __future__ import annotations

from datetime import datetime
from difflib import unified_diff

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import or_

from auth.auth_utils import AuthUtils
from db.db import db
from db.tables import (
    MarkdownWorkspace,
    MarkdownWorkspaceMember,
    MarkdownDocument,
    MarkdownCommit,
    MarkdownWorkspaceVisibility,
    MarkdownNodeType,
    User,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ForbiddenError
from decorators.permission_decorator import require_permission
from .markdown_collab_helpers import (
    _is_admin,
    _require_workspace_access,
    _require_workspace_manage,
    _workspace_to_dict,
)

markdown_workspace_bp = Blueprint("markdown_workspace", __name__)


@markdown_workspace_bp.route("/workspaces", methods=["GET"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def list_workspaces():
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    query = MarkdownWorkspace.query.order_by(MarkdownWorkspace.updated_at.desc())
    if not _is_admin(username):
        member_rows = MarkdownWorkspaceMember.query.filter_by(username=username).all()
        member_workspace_ids = {r.workspace_id for r in member_rows}
        if member_workspace_ids:
            query = query.filter(or_(
                MarkdownWorkspace.owner_username == username,
                MarkdownWorkspace.id.in_(member_workspace_ids),
            ))
        else:
            query = query.filter(MarkdownWorkspace.owner_username == username)

    workspaces = [_workspace_to_dict(ws) for ws in query.all()]
    return jsonify({"success": True, "workspaces": workspaces}), 200


@markdown_workspace_bp.route("/workspaces", methods=["POST"])
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


@markdown_workspace_bp.route("/workspaces/<int:workspace_id>/members", methods=["GET"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def list_workspace_members(workspace_id: int):
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = MarkdownWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    members = (
        MarkdownWorkspaceMember.query
        .filter_by(workspace_id=workspace_id)
        .order_by(MarkdownWorkspaceMember.username.asc())
        .all()
    )

    # Fetch user records for avatar info
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
            "added_by": m.added_by,
            "added_at": m.added_at.isoformat() if m.added_at else None,
            "avatar_url": avatar_url,
            "avatar_seed": avatar_seed,
            "collab_color": collab_color,
        }

    payload = [build_member_dict(m) for m in members]

    # Also get owner info
    owner_user = User.query.filter_by(username=ws.owner_username).first()
    owner_avatar_url = None
    owner_avatar_seed = None
    owner_collab_color = None
    if owner_user:
        if owner_user.avatar_public_id and owner_user.avatar_file:
            owner_avatar_url = f"/api/users/avatar/{owner_user.avatar_public_id}"
        owner_avatar_seed = owner_user.avatar_seed
        owner_collab_color = owner_user.collab_color

    return jsonify({
        "success": True,
        "workspace_id": workspace_id,
        "owner_username": ws.owner_username,
        "owner_avatar_url": owner_avatar_url,
        "owner_avatar_seed": owner_avatar_seed,
        "owner_collab_color": owner_collab_color,
        "members": payload,
        "count": len(payload),
    }), 200


@markdown_workspace_bp.route("/workspaces/<int:workspace_id>/members", methods=["POST"])
@require_permission("feature:markdown_collab:share")
@handle_api_errors(logger_name="markdown_collab")
def add_workspace_members(workspace_id: int):
    """Invite/share workspace with other users (owner/admin only)."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = MarkdownWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_manage(ws, username)

    data = request.get_json() or {}
    raw = data.get("usernames") or data.get("members") or data.get("username")
    if raw is None:
        raise ValidationError("username(s) is required")

    if isinstance(raw, str):
        usernames = [raw]
    elif isinstance(raw, (list, tuple, set)):
        usernames = list(raw)
    else:
        raise ValidationError("username(s) must be a string or list")

    normalized = sorted({str(u).strip() for u in usernames if u and str(u).strip()})
    normalized = [u for u in normalized if u != ws.owner_username]
    if not normalized:
        raise ValidationError("No valid usernames provided")

    existing_rows = MarkdownWorkspaceMember.query.filter(
        MarkdownWorkspaceMember.workspace_id == workspace_id,
        MarkdownWorkspaceMember.username.in_(normalized),
    ).all()
    existing_usernames = {r.username for r in existing_rows}

    created = 0
    created_usernames = []
    for u in normalized:
        if u in existing_usernames:
            continue
        db.session.add(MarkdownWorkspaceMember(
            workspace_id=workspace_id,
            username=u,
            added_by=username,
            added_at=datetime.utcnow(),
        ))
        created += 1
        created_usernames.append(u)

    if created:
        ws.updated_at = datetime.utcnow()
    db.session.commit()

    if created_usernames:
        socketio = current_app.extensions.get('socketio')
        if socketio:
            try:
                from socketio_handlers.events_markdown_collab import emit_workspace_shared
                workspace_payload = _workspace_to_dict(ws)
                for u in created_usernames:
                    user = User.query.filter_by(username=u).first()
                    if user:
                        emit_workspace_shared(socketio, user.id, workspace_payload)
            except Exception:
                # Do not fail the request if socket emission fails
                pass

    members = (
        MarkdownWorkspaceMember.query
        .filter_by(workspace_id=workspace_id)
        .order_by(MarkdownWorkspaceMember.username.asc())
        .all()
    )
    return jsonify({
        "success": True,
        "workspace_id": workspace_id,
        "owner_username": ws.owner_username,
        "members": [
            {
                "username": m.username,
                "added_by": m.added_by,
                "added_at": m.added_at.isoformat() if m.added_at else None,
            }
            for m in members
        ],
        "added": created,
        "count": len(members),
    }), 200


@markdown_workspace_bp.route("/workspaces/<int:workspace_id>/members/<member_username>", methods=["DELETE"])
@require_permission("feature:markdown_collab:share")
@handle_api_errors(logger_name="markdown_collab")
def remove_workspace_member(workspace_id: int, member_username: str):
    """Remove a shared workspace member (owner/admin only)."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = MarkdownWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_manage(ws, username)

    member = MarkdownWorkspaceMember.query.filter_by(
        workspace_id=workspace_id,
        username=member_username,
    ).first()
    if member:
        db.session.delete(member)
        ws.updated_at = datetime.utcnow()
        db.session.commit()

    members = (
        MarkdownWorkspaceMember.query
        .filter_by(workspace_id=workspace_id)
        .order_by(MarkdownWorkspaceMember.username.asc())
        .all()
    )
    return jsonify({
        "success": True,
        "workspace_id": workspace_id,
        "owner_username": ws.owner_username,
        "members": [
            {
                "username": m.username,
                "added_by": m.added_by,
                "added_at": m.added_at.isoformat() if m.added_at else None,
            }
            for m in members
        ],
        "count": len(members),
    }), 200


@markdown_workspace_bp.route("/workspaces/<int:workspace_id>", methods=["DELETE"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def delete_workspace(workspace_id: int):
    """Delete a workspace (owner/admin only). Cascades to all documents and members."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = MarkdownWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")

    # Only owner or admin can delete
    if not _is_admin(username) and ws.owner_username != username:
        raise ForbiddenError("Nur der Besitzer kann diesen Workspace löschen")

    # Get all document IDs first for commit deletion
    doc_ids = [d.id for d in MarkdownDocument.query.filter_by(workspace_id=workspace_id).all()]

    # Delete commits first (foreign key to documents)
    if doc_ids:
        MarkdownCommit.query.filter(MarkdownCommit.document_id.in_(doc_ids)).delete(synchronize_session=False)

    # Delete all documents
    MarkdownDocument.query.filter_by(workspace_id=workspace_id).delete(synchronize_session=False)

    # Delete all members
    MarkdownWorkspaceMember.query.filter_by(workspace_id=workspace_id).delete(synchronize_session=False)

    # Delete the workspace
    db.session.delete(ws)
    db.session.commit()

    return jsonify({"success": True, "message": "Workspace gelöscht"}), 200


@markdown_workspace_bp.route("/workspaces/<int:workspace_id>/leave", methods=["POST"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def leave_workspace(workspace_id: int):
    """Leave a workspace (for invited members only, not the owner)."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = MarkdownWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")

    # Owner cannot leave their own workspace
    if ws.owner_username == username:
        raise ValidationError("Der Besitzer kann den Workspace nicht verlassen. Löschen Sie den Workspace stattdessen.")

    # Check if user is a member
    member = MarkdownWorkspaceMember.query.filter_by(
        workspace_id=workspace_id,
        username=username,
    ).first()

    if not member:
        raise NotFoundError("Sie sind kein Mitglied dieses Workspaces")

    db.session.delete(member)
    db.session.commit()

    return jsonify({"success": True, "message": "Workspace verlassen"}), 200


@markdown_workspace_bp.route("/workspaces/<int:workspace_id>/tree", methods=["GET"])
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

    from .markdown_collab_helpers import _doc_to_dict
    docs = (
        MarkdownDocument.query
        .filter_by(workspace_id=workspace_id)
        .filter(MarkdownDocument.deleted_at.is_(None))  # Exclude soft-deleted documents
        .order_by(MarkdownDocument.parent_id.asc(), MarkdownDocument.order_index.asc(), MarkdownDocument.id.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "workspace": _workspace_to_dict(ws),
        "nodes": [_doc_to_dict(d) for d in docs],
    }), 200


@markdown_workspace_bp.route("/workspaces/<int:workspace_id>/changes", methods=["GET"])
@require_permission("feature:markdown_collab:view")
@handle_api_errors(logger_name="markdown_collab")
def get_workspace_changes(workspace_id: int):
    """Get uncommitted changes for all files in a workspace, including deleted files."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = MarkdownWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    from .markdown_collab_helpers import _doc_to_dict
    from db.tables import MarkdownNodeType

    # Get all active file documents (not folders)
    docs = (
        MarkdownDocument.query
        .filter_by(workspace_id=workspace_id)
        .filter(MarkdownDocument.deleted_at.is_(None))
        .filter(MarkdownDocument.node_type == MarkdownNodeType.file)
        .all()
    )

    # Get soft-deleted files (for restore functionality)
    deleted_docs = (
        MarkdownDocument.query
        .filter_by(workspace_id=workspace_id)
        .filter(MarkdownDocument.deleted_at.isnot(None))
        .filter(MarkdownDocument.node_type == MarkdownNodeType.file)
        .all()
    )

    changes = []
    for doc in docs:
        # Get the latest commit with content snapshot
        latest_commit = (
            MarkdownCommit.query
            .filter_by(document_id=doc.id)
            .filter(MarkdownCommit.content_snapshot.isnot(None))
            .order_by(MarkdownCommit.created_at.desc(), MarkdownCommit.id.desc())
            .first()
        )

        current_content = doc.content_text or ""
        baseline_commit = latest_commit
        if latest_commit and (latest_commit.content_snapshot or "") == "":
            non_empty_commit = (
                MarkdownCommit.query
                .filter_by(document_id=doc.id)
                .filter(MarkdownCommit.content_snapshot.isnot(None))
                .filter(MarkdownCommit.content_snapshot != "")
                .order_by(MarkdownCommit.created_at.desc(), MarkdownCommit.id.desc())
                .first()
            )
            if non_empty_commit and current_content == (non_empty_commit.content_snapshot or ""):
                baseline_commit = non_empty_commit

        baseline_content = baseline_commit.content_snapshot if baseline_commit else ""

        if current_content != baseline_content:
            # Calculate diff stats using unified_diff
            current_lines = current_content.split('\n') if current_content else []
            baseline_lines = baseline_content.split('\n') if baseline_content else []
            diff_lines = list(unified_diff(baseline_lines, current_lines, lineterm=''))
            insertions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
            deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

            changes.append({
                "id": doc.id,  # Use 'id' to match LatexCollab structure
                "title": doc.title,
                "path": doc.title,
                "status": "A" if not baseline_commit else "M",  # A=Added (new file), M=Modified
                "insertions": insertions,  # Match LatexCollab field names
                "deletions": deletions,
                "has_baseline": baseline_commit is not None,
            })

    # Add deleted files
    deleted_files = []
    for doc in deleted_docs:
        deleted_files.append({
            "id": doc.id,  # Use 'id' to match LatexCollab structure
            "title": doc.title,
            "path": doc.title,
            "status": "D",
            "deleted_at": doc.deleted_at.isoformat() if doc.deleted_at else None,
        })

    return jsonify({
        "success": True,
        "workspace_id": workspace_id,
        "changed_files": changes,  # Match LatexCollab field name
        "deleted_files": deleted_files,
        "total_changes": len(changes),
        "total_deleted": len(deleted_files),
    }), 200


@markdown_workspace_bp.route("/workspaces/<int:workspace_id>/commit", methods=["POST"])
@require_permission("feature:markdown_collab:edit")
@handle_api_errors(logger_name="markdown_collab")
def create_workspace_commit(workspace_id: int):
    """Create commits for multiple files at once."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = MarkdownWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    _require_workspace_access(ws, username)

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    document_ids = data.get("document_ids", [])

    if not message:
        raise ValidationError("message is required")
    if not document_ids:
        raise ValidationError("document_ids is required (at least one document must be committed)")

    doc_ids = [int(doc_id) for doc_id in document_ids]
    docs = MarkdownDocument.query.filter(
        MarkdownDocument.id.in_(doc_ids),
        MarkdownDocument.workspace_id == workspace_id,
        MarkdownDocument.node_type == MarkdownNodeType.file,
    ).all()

    valid_doc_ids = {d.id for d in docs}
    invalid_ids = [doc_id for doc_id in doc_ids if doc_id not in valid_doc_ids]
    if invalid_ids:
        raise ValidationError(f"Invalid document IDs: {invalid_ids}")

    created_commits = []
    for doc in docs:
        content_snapshot = doc.content_text or ""

        latest_commit = (
            MarkdownCommit.query
            .filter_by(document_id=doc.id)
            .filter(MarkdownCommit.content_snapshot.isnot(None))
            .order_by(MarkdownCommit.created_at.desc(), MarkdownCommit.id.desc())
            .first()
        )
        baseline = latest_commit.content_snapshot if latest_commit else ""

        baseline_lines = baseline.split('\n') if baseline else []
        current_lines = content_snapshot.split('\n') if content_snapshot else []
        diff_lines = list(unified_diff(baseline_lines, current_lines, lineterm=''))
        insertions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

        diff_summary = {
            "insertions": insertions,
            "deletions": deletions
        }

        commit = MarkdownCommit(
            document_id=doc.id,
            author_username=username,
            message=message,
            diff_summary=diff_summary,
            content_snapshot=content_snapshot,
            created_at=datetime.utcnow(),
        )
        db.session.add(commit)
        created_commits.append((doc.id, commit))

    db.session.commit()

    socketio = current_app.extensions.get('socketio')
    if socketio:
        try:
            from socketio_handlers.events_markdown_collab import emit_commit_created
            for doc_id, commit in created_commits:
                emit_commit_created(socketio, doc_id, {
                    "id": commit.id,
                    "document_id": commit.document_id,
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
        "commits": [
            {
                "id": commit.id,
                "document_id": commit.document_id,
                "message": commit.message,
            }
            for _, commit in created_commits
        ],
        "total_committed": len(created_commits),
    }), 201
