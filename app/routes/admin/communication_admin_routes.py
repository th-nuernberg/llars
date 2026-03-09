"""
Admin routes for communication (messaging) management.

Provides endpoints for:
- Viewing global communication settings
- Managing per-user communication permissions
- Viewing privacy-safe communication statistics
"""

import logging

from flask import jsonify, request, g

from decorators.error_handler import handle_api_errors, ValidationError
from decorators.permission_decorator import require_permission
from auth.auth_utils import AuthUtils
from routes.auth import data_bp
from services import communication_admin_service as svc

logger = logging.getLogger(__name__)


@data_bp.get("/admin/communication/users")
@require_permission("admin:system:configure")
@handle_api_errors(logger_name="communication_admin")
def get_communication_users():
    """Get all users with their communication permission states."""
    users = svc.get_all_users_communication_permissions()
    return jsonify({'success': True, 'users': users})


@data_bp.put("/admin/communication/users/<username>")
@require_permission("admin:system:configure")
@handle_api_errors(logger_name="communication_admin")
def set_communication_user_permissions(username):
    """Set communication permissions for a single user."""
    payload = request.get_json(silent=True) or {}
    permissions = payload.get('permissions', {})

    if not isinstance(permissions, dict):
        raise ValidationError("permissions must be a dict of permission_key -> bool")

    admin_username = AuthUtils.extract_username_without_validation() or "admin"
    updated = svc.set_user_communication_permissions(username, permissions, admin_username)

    # Notify all clients in real-time to re-fetch permissions
    if updated:
        try:
            from main import socketio
            socketio.emit('communication:permissions_changed', {
                'username': username,
            })
            logger.info(f"[Communication] Emitted permissions_changed for {username}")
        except Exception as e:
            logger.warning(f"[Communication] Failed to emit permissions_changed: {e}")

    return jsonify({
        'success': True,
        'updated': updated,
        'username': username,
    })


@data_bp.post("/admin/communication/users/bulk")
@require_permission("admin:system:configure")
@handle_api_errors(logger_name="communication_admin")
def bulk_set_communication_permissions():
    """Bulk enable/disable communication permissions for multiple users."""
    payload = request.get_json(silent=True) or {}
    usernames = payload.get('usernames', [])
    permissions = payload.get('permissions', {})

    if not isinstance(usernames, list) or not usernames:
        raise ValidationError("usernames must be a non-empty list")
    if not isinstance(permissions, dict):
        raise ValidationError("permissions must be a dict of permission_key -> bool")

    admin_username = AuthUtils.extract_username_without_validation() or "admin"
    result = svc.bulk_set_permissions(usernames, permissions, admin_username)

    # Notify all clients in real-time
    try:
        from main import socketio
        socketio.emit('communication:permissions_changed', {
            'usernames': usernames,
        })
        logger.info(f"[Communication] Emitted bulk permissions_changed for {len(usernames)} users")
    except Exception as e:
        logger.warning(f"[Communication] Failed to emit bulk permissions_changed: {e}")

    return jsonify({'success': True, **result})


@data_bp.get("/admin/communication/stats")
@require_permission("admin:system:configure")
@handle_api_errors(logger_name="communication_admin")
def get_communication_stats():
    """Get aggregate communication statistics (no content, privacy-safe)."""
    stats = svc.get_communication_stats()
    user_stats = svc.get_user_stats()

    return jsonify({
        'success': True,
        'stats': stats,
        'user_stats': user_stats,
    })
