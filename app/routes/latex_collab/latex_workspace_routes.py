# latex_workspace_routes.py
"""
LaTeX Collab Workspace API Routes.
Handles workspace CRUD and member management.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import or_

from auth.auth_utils import AuthUtils
from db.database import db
from db.tables import (
    LatexWorkspace,
    LatexWorkspaceMember,
    LatexDocument,
    LatexNodeType,
    LatexWorkspaceVisibility,
    User,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.latex_collab.latex_helpers import (
    is_admin,
    require_workspace_access,
    require_workspace_manage,
    workspace_to_dict,
)

latex_workspace_bp = Blueprint("latex_workspace", __name__, url_prefix="/api/latex-collab")


# ============================================================================
# Workspace CRUD
# ============================================================================

@latex_workspace_bp.route("/workspaces", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_workspaces():
    """List all workspaces the user has access to."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    query = LatexWorkspace.query.order_by(LatexWorkspace.updated_at.desc())
    if not is_admin(username):
        member_rows = LatexWorkspaceMember.query.filter_by(username=username).all()
        member_workspace_ids = {r.workspace_id for r in member_rows}
        if member_workspace_ids:
            query = query.filter(or_(
                LatexWorkspace.owner_username == username,
                LatexWorkspace.id.in_(member_workspace_ids),
            ))
        else:
            query = query.filter(LatexWorkspace.owner_username == username)

    workspaces = [workspace_to_dict(ws) for ws in query.all()]
    return jsonify({"success": True, "workspaces": workspaces}), 200


@latex_workspace_bp.route("/workspaces", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_workspace():
    """Create a new workspace with a default main.tex file."""
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
    return jsonify({"success": True, "workspace": workspace_to_dict(ws)}), 201


@latex_workspace_bp.route("/workspaces/<int:workspace_id>", methods=["DELETE"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def delete_workspace(workspace_id: int):
    """Delete a workspace (owner or admin only)."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_manage(ws, username)

    db.session.delete(ws)
    db.session.commit()
    return jsonify({"success": True}), 200


@latex_workspace_bp.route("/workspaces/<int:workspace_id>/leave", methods=["POST"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def leave_workspace(workspace_id: int):
    """Leave a workspace (for non-owners)."""
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


# ============================================================================
# Member Management
# ============================================================================

@latex_workspace_bp.route("/workspaces/<int:workspace_id>/members", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_workspace_members(workspace_id: int):
    """List all members of a workspace."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

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


@latex_workspace_bp.route("/workspaces/<int:workspace_id>/members", methods=["POST"])
@require_permission("feature:latex_collab:share")
@handle_api_errors(logger_name="latex_collab")
def add_workspace_member(workspace_id: int):
    """Add a member to a workspace."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_manage(ws, username)

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
            emit_workspace_shared(socketio, user.id, workspace_to_dict(ws))
        except Exception:
            pass

    return jsonify({"success": True, "member": {"username": member_username}}), 201


@latex_workspace_bp.route("/workspaces/<int:workspace_id>/members/<member_username>", methods=["DELETE"])
@require_permission("feature:latex_collab:share")
@handle_api_errors(logger_name="latex_collab")
def remove_workspace_member(workspace_id: int, member_username: str):
    """Remove a member from a workspace."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_manage(ws, username)

    member = LatexWorkspaceMember.query.filter_by(workspace_id=workspace_id, username=member_username).first()
    if not member:
        raise NotFoundError("Mitglied nicht gefunden")

    db.session.delete(member)
    db.session.commit()
    return jsonify({"success": True}), 200
