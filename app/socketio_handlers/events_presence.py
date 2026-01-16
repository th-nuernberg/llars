"""
Presence Socket.IO Events

Tracks heartbeats/activities and streams live presence updates to admins.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from flask import request
from flask_socketio import emit, join_room, leave_room

from auth.decorators import get_or_create_user
from auth.oidc_validator import get_username, validate_token
from services.permission_service import PermissionService
from services.presence_service import get_presence_service


ADMIN_ROOM = "presence_admin"


def _require_user(permission_key: Optional[str] = None):
    token = str(request.args.get("token") or "").strip()
    payload = validate_token(token) if token else None
    if not payload:
        emit("presence:error", {"message": "Unauthorized"})
        return None

    username = get_username(payload)
    if not username:
        emit("presence:error", {"message": "Unauthorized"})
        return None

    if permission_key and not PermissionService.check_permission(username, permission_key):
        emit("presence:error", {"message": "Forbidden"})
        return None

    return get_or_create_user(username)


def register_presence_events(socketio) -> None:
    @socketio.on("presence:subscribe")
    def handle_subscribe(_data: Optional[Dict[str, Any]] = None):
        user = _require_user("admin:system:configure")
        if not user:
            return

        join_room(ADMIN_ROOM)
        service = get_presence_service()
        emit("presence:state", {"users": service.list_users()}, room=request.sid)

    @socketio.on("presence:unsubscribe")
    def handle_unsubscribe(_data: Optional[Dict[str, Any]] = None):
        leave_room(ADMIN_ROOM)

    @socketio.on("presence:heartbeat")
    def handle_heartbeat(_data: Optional[Dict[str, Any]] = None):
        user = _require_user()
        if not user:
            return

        service = get_presence_service()
        payload = service.record_seen(user, request.sid)
        socketio.emit("presence:update", payload, room=ADMIN_ROOM)

    @socketio.on("presence:activity")
    def handle_activity(_data: Optional[Dict[str, Any]] = None):
        user = _require_user()
        if not user:
            return

        service = get_presence_service()
        payload = service.record_active(user, request.sid)
        socketio.emit("presence:update", payload, room=ADMIN_ROOM)
