"""
Admin User Management API

DB is the single source of truth for user lifecycle states (active/locked/deleted).
Authentication still happens via Authentik (OIDC), but access can be denied
based on DB state.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from flask import jsonify, request
from sqlalchemy import select

from auth.auth_utils import AuthUtils
from decorators.error_handler import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
    handle_api_errors,
)
from decorators.permission_decorator import require_permission
from db.database import db
from db.models import Role, User, UserGroup, UserPermission, UserRole
from routes.auth import data_bp
from services.permission_service import PermissionService
from services.user_profile_service import build_avatar_url, is_valid_collab_color, pick_collab_color


def _serialize_user(user: User, roles: List[dict]) -> Dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "group": user.group.name if getattr(user, "group", None) else None,
        "is_active": bool(getattr(user, "is_active", True)),
        "deleted_at": user.deleted_at.isoformat() if getattr(user, "deleted_at", None) else None,
        "avatar_seed": user.get_avatar_seed() if hasattr(user, "get_avatar_seed") else None,
        "avatar_url": build_avatar_url(user),
        "collab_color": user.collab_color,
        "roles": roles or [],
    }


def _get_roles_by_username(usernames: List[str]) -> Dict[str, List[dict]]:
    if not usernames:
        return {}

    rows = db.session.execute(
        select(UserRole.username, Role.id, Role.role_name, Role.display_name)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.username.in_(usernames))
        .order_by(UserRole.username)
    ).all()

    roles_by_username: Dict[str, List[dict]] = {u: [] for u in usernames}
    for username, role_id, role_name, display_name in rows:
        if role_name == "viewer":
            role_name = "evaluator"
            display_name = "Evaluator"
        roles_by_username.setdefault(username, []).append(
            {
                "id": role_id,
                "role_name": role_name,
                "display_name": display_name,
            }
        )
    return roles_by_username


@data_bp.route("/admin/users", methods=["GET"])
@require_permission("admin:users:manage")
@handle_api_errors(logger_name="admin_users")
def list_admin_users():
    include_deleted = request.args.get("include_deleted", "false").lower() == "true"
    query = request.args.get("q", "").strip()

    users_query = User.query
    if not include_deleted:
        users_query = users_query.filter(User.deleted_at.is_(None))
    if query:
        users_query = users_query.filter(User.username.ilike(f"%{query}%"))

    users = users_query.order_by(User.username.asc()).all()
    usernames = [u.username for u in users]
    roles_by_username = _get_roles_by_username(usernames)

    payload = [_serialize_user(u, roles_by_username.get(u.username, [])) for u in users]
    return jsonify({"success": True, "users": payload, "data": payload}), 200


@data_bp.route("/admin/users", methods=["POST"])
@require_permission("admin:users:manage")
@handle_api_errors(logger_name="admin_users")
def create_admin_user():
    """
    Create a new user.

    If email and password are provided, also creates the user in Authentik.
    Otherwise, only creates a local LLARS database record.
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    is_active = bool(data.get("is_active", True))
    role_names = data.get("role_names") or data.get("roles") or []
    collab_color = (data.get("collab_color") or "").strip() or None
    avatar_seed = (data.get("avatar_seed") or "").strip() or None

    # Optional Authentik fields
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or data.get("name") or "").strip()
    create_in_authentik = bool(data.get("create_in_authentik", True))

    if not username:
        raise ValidationError("username is required")
    if collab_color and not is_valid_collab_color(collab_color):
        raise ValidationError("collab_color must be a valid hex color (#RRGGBB format)")
    if avatar_seed and len(avatar_seed) > 32:
        raise ValidationError("avatar_seed must be <= 32 characters")

    # If creating in Authentik, email and password are required
    authentik_user_created = False
    authentik_warning = None

    if email and password and create_in_authentik:
        from services.authentik_admin_service import AuthentikAdminService

        try:
            success, error_msg, authentik_data = AuthentikAdminService.create_user(
                username=username,
                email=email,
                password=password,
                name=display_name or username,
                is_active=is_active
            )

            if success:
                authentik_user_created = True
                if error_msg:  # Warning (e.g., password not set)
                    authentik_warning = error_msg
            elif "already exists" in (error_msg or ""):
                # User exists in Authentik, that's fine - continue with local creation
                authentik_warning = f"User existiert bereits in Authentik. Nur lokaler LLARS-Account wird erstellt."
            else:
                # Authentik creation failed - log warning but continue with local user
                authentik_warning = f"Authentik-Erstellung fehlgeschlagen: {error_msg}. Lokaler LLARS-Account wurde erstellt - Login nur möglich wenn User manuell in Authentik angelegt wird."
        except Exception as e:
            # Don't fail the whole operation if Authentik is unreachable
            authentik_warning = f"Authentik nicht erreichbar: {str(e)}. Lokaler LLARS-Account wurde erstellt."

    existing = User.query.filter_by(username=username).first()
    if existing and existing.deleted_at is None:
        raise ConflictError(f"User '{username}' already exists")

    default_group = UserGroup.query.filter_by(name="Standard").first()
    group_id = default_group.id if default_group else 1

    if existing and existing.deleted_at is not None:
        user = existing
        user.deleted_at = None
        user.is_active = is_active
        if not user.api_key:
            user.api_key = str(uuid.uuid4())
        if not user.group_id:
            user.group_id = group_id
    else:
        user = User(
            username=username,
            password_hash="",
            api_key=str(uuid.uuid4()),
            group_id=group_id,
            is_active=is_active,
            deleted_at=None,
        )
        db.session.add(user)

    if collab_color:
        user.collab_color = collab_color
    elif not user.collab_color:
        user.collab_color = pick_collab_color()

    if avatar_seed:
        user.avatar_seed = avatar_seed
    elif hasattr(user, "get_avatar_seed") and not user.avatar_seed:
        user.get_avatar_seed()

    db.session.commit()

    # Optional: assign initial roles (creates audit log entries)
    if role_names:
        admin_username = AuthUtils.extract_username_without_validation() or "admin"
        for role_name in role_names:
            ok = PermissionService.assign_role(username=username, role_name=role_name, admin_username=admin_username)
            if not ok:
                raise ValidationError(f"Unknown role: {role_name}")

    try:
        from services.system_event_service import SystemEventService

        acting_username = AuthUtils.extract_username_without_validation() or "admin"
        SystemEventService.log_event(
            event_type="admin.user_created",
            severity="info",
            username=acting_username,
            entity_type="user",
            entity_id=username,
            message=f"User '{username}' created by '{acting_username}'",
            details={"roles": role_names or []},
        )
    except Exception:
        pass

    roles_by_username = _get_roles_by_username([username])
    payload = _serialize_user(user, roles_by_username.get(username, []))
    payload["authentik_created"] = authentik_user_created

    response_data = {"success": True, "user": payload, "data": payload}
    if authentik_warning:
        response_data["warning"] = authentik_warning

    return jsonify(response_data), 201


@data_bp.route("/admin/users/<username>", methods=["PATCH"])
@require_permission("admin:users:manage")
@handle_api_errors(logger_name="admin_users")
def update_admin_user(username: str):
    data = request.get_json() or {}

    user = User.query.filter_by(username=username).first()
    if not user or user.deleted_at is not None:
        raise NotFoundError(f"User '{username}' not found")

    acting_username = AuthUtils.extract_username_without_validation() or "admin"
    if username == "admin":
        raise ForbiddenError("The bootstrap admin user cannot be modified")
    if username == acting_username and "is_active" in data and bool(data.get("is_active")) is False:
        raise ForbiddenError("You cannot lock your own account")

    if "is_active" in data:
        new_is_active = bool(data.get("is_active"))
        old_is_active = bool(getattr(user, "is_active", True))
        user.is_active = new_is_active

    db.session.commit()

    try:
        from services.system_event_service import SystemEventService

        if "is_active" in data and old_is_active != new_is_active:
            event_type = "admin.user_unlocked" if new_is_active else "admin.user_locked"
            SystemEventService.log_event(
                event_type=event_type,
                severity="warning" if not new_is_active else "info",
                username=acting_username,
                entity_type="user",
                entity_id=username,
                message=f"User '{username}' {'unlocked' if new_is_active else 'locked'} by '{acting_username}'",
                details={"is_active": new_is_active},
            )
    except Exception:
        pass

    roles_by_username = _get_roles_by_username([username])
    payload = _serialize_user(user, roles_by_username.get(username, []))
    return jsonify({"success": True, "user": payload, "data": payload}), 200


@data_bp.route("/admin/users/<username>", methods=["DELETE"])
@require_permission("admin:users:manage")
@handle_api_errors(logger_name="admin_users")
def delete_admin_user(username: str):
    user = User.query.filter_by(username=username).first()
    if not user:
        raise NotFoundError(f"User '{username}' not found")

    acting_username = AuthUtils.extract_username_without_validation() or "admin"
    if username == "admin":
        raise ForbiddenError("The bootstrap admin user cannot be deleted")
    if username == acting_username:
        raise ForbiddenError("You cannot delete your own account")

    if user.deleted_at is None:
        user.deleted_at = datetime.utcnow()
    user.is_active = False

    # Remove permissions/roles (keep other references for auditing)
    db.session.execute(UserRole.__table__.delete().where(UserRole.username == username))
    db.session.execute(UserPermission.__table__.delete().where(UserPermission.username == username))
    db.session.commit()

    try:
        from services.system_event_service import SystemEventService

        SystemEventService.log_event(
            event_type="admin.user_deleted",
            severity="warning",
            username=acting_username,
            entity_type="user",
            entity_id=username,
            message=f"User '{username}' deleted by '{acting_username}'",
        )
    except Exception:
        pass

    return jsonify({"success": True, "message": f"User '{username}' deleted"}), 200
