"""
Permission Management Routes

Provides API endpoints for managing permissions, roles, and user permissions.
All routes are protected with admin permissions.

Routes:
    GET  /api/permissions - List all permissions
    GET  /api/permissions/roles - List all roles
    GET  /api/permissions/user/<username> - Get user permissions and roles
    POST /api/permissions/grant - Grant permission to user
    POST /api/permissions/revoke - Revoke permission from user
    POST /api/permissions/assign-role - Assign role to user
    POST /api/permissions/unassign-role - Unassign role from user
"""

from flask import Blueprint, request, jsonify, current_app
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, UnauthorizedError
)
from services.permission_service import PermissionService
from routes import data_blueprint
from auth.auth_utils import AuthUtils


@data_blueprint.route('/permissions', methods=['GET'])
@require_permission('admin:permissions:manage')
@handle_api_errors(logger_name='auth')
def get_all_permissions():
    """Get all available permissions in the system"""
    permissions = PermissionService.get_all_permissions()
    return jsonify({
        'success': True,
        # Preferred (frontend expects this)
        'permissions': permissions,
        # Backwards compatibility
        'data': permissions
    }), 200


@data_blueprint.route('/permissions/roles', methods=['GET'])
@require_permission('admin:permissions:manage')
@handle_api_errors(logger_name='auth')
def get_all_roles():
    """Get all available roles in the system"""
    roles = PermissionService.get_all_roles()
    return jsonify({
        'success': True,
        # Preferred (frontend expects this)
        'roles': roles,
        # Backwards compatibility
        'data': roles
    }), 200


@data_blueprint.route('/permissions/roles', methods=['POST'])
@require_permission('admin:roles:manage')
@handle_api_errors(logger_name='auth')
def create_role():
    """Create a new role (admin only)."""
    data = request.get_json() or {}
    role_name = data.get('role_name') or data.get('name')
    display_name = data.get('display_name') or data.get('title')
    description = data.get('description')
    permission_keys = data.get('permission_keys') or data.get('permissions') or []

    if not role_name or not display_name:
        raise ValidationError('role_name and display_name are required')

    admin_username = AuthUtils.extract_username_without_validation()
    role = PermissionService.create_role(
        role_name=role_name,
        display_name=display_name,
        description=description,
        permission_keys=permission_keys,
        admin_username=admin_username,
    )

    return jsonify({'success': True, 'role': role, 'data': role}), 201


@data_blueprint.route('/permissions/roles/<role_name>/permissions', methods=['PUT'])
@require_permission('admin:roles:manage')
@handle_api_errors(logger_name='auth')
def set_role_permissions(role_name: str):
    """Replace the permissions for a role (admin only)."""
    data = request.get_json() or {}
    permission_keys = data.get('permission_keys') or data.get('permissions') or []

    admin_username = AuthUtils.extract_username_without_validation()
    role = PermissionService.set_role_permissions(
        role_name=role_name,
        permission_keys=permission_keys,
        admin_username=admin_username,
    )

    return jsonify({'success': True, 'role': role, 'data': role}), 200


@data_blueprint.route('/permissions/user/<username>', methods=['GET'])
@require_permission('admin:permissions:manage')
@handle_api_errors(logger_name='auth')
def get_user_permissions(username):
    """Get all permissions and roles for a specific user"""
    permissions = PermissionService.get_user_permissions(username)
    roles = PermissionService.get_user_roles(username)

    payload = {
        'username': username,
        'permissions': permissions,
        'roles': roles
    }

    return jsonify({
        'success': True,
        **payload,
        # Backwards compatibility
        'data': payload
    }), 200


@data_blueprint.route('/permissions/users-with-roles', methods=['GET'])
@require_permission('admin:permissions:manage')
@handle_api_errors(logger_name='auth')
def get_users_with_roles():
    """Get all users that have at least one role assigned"""
    users = PermissionService.get_all_users_with_roles()
    return jsonify({
        'success': True,
        # Preferred (frontend expects this)
        'users': users,
        # Backwards compatibility
        'data': users
    }), 200


@data_blueprint.route('/permissions/my-permissions', methods=['GET'])
@handle_api_errors(logger_name='auth')
def get_my_permissions():
    """Get current user's permissions (no admin permission required)"""
    # Extract username from token
    username = AuthUtils.extract_username_without_validation()

    if not username:
        raise UnauthorizedError('Invalid token')

    permissions = PermissionService.get_user_permissions(username)
    roles = PermissionService.get_user_roles(username)

    payload = {'username': username, 'permissions': permissions, 'roles': roles}
    return jsonify({'success': True, 'data': payload, **payload}), 200


@data_blueprint.route('/permissions/audit-log', methods=['GET'])
@require_permission('admin:permissions:manage')
@handle_api_errors(logger_name='auth')
def get_audit_log():
    """Get recent permission change audit log entries."""
    from db.tables import PermissionAuditLog

    limit = request.args.get('limit', 200, type=int)
    limit = max(1, min(limit, 500))

    rows = (
        PermissionAuditLog.query
        .order_by(PermissionAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    def format_details(entry: PermissionAuditLog) -> str:
        if entry.permission_key:
            return entry.permission_key
        if entry.role_name:
            return f"role: {entry.role_name}"
        details = entry.details or {}
        if isinstance(details, dict):
            role_name = details.get('role_name')
            if role_name:
                return f"role: {role_name}"
            return ", ".join([f"{k}={v}" for k, v in details.items()]) if details else ''
        return str(details) if details else ''

    entries = [
        {
            'id': r.id,
            'action': r.action,
            'performed_by': r.admin_username,
            'target_username': r.target_username,
            'details': format_details(r),
            'raw_details': r.details,
            'timestamp': r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

    return jsonify({
        'success': True,
        'entries': entries,
        # Backwards compatibility
        'data': entries
    }), 200


@data_blueprint.route('/permissions/grant', methods=['POST'])
@require_permission('admin:permissions:manage')
@handle_api_errors(logger_name='auth')
def grant_permission():
    """
    Grant a permission to a user

    Request body:
        {
            "username": "target_user",
            "permission_key": "feature:mail_rating:view"
        }
    """
    data = request.get_json()
    username = data.get('username')
    permission_key = data.get('permission_key')

    if not username or not permission_key:
        raise ValidationError('username and permission_key are required')

    # Get admin username from token
    admin_username = AuthUtils.extract_username_without_validation()

    success = PermissionService.grant_permission(
        username=username,
        permission_key=permission_key,
        admin_username=admin_username
    )

    if not success:
        raise ValidationError('Failed to grant permission')

    return jsonify({
        'success': True,
        'message': f'Permission {permission_key} granted to {username}'
    }), 200


@data_blueprint.route('/permissions/revoke', methods=['POST'])
@require_permission('admin:permissions:manage')
@handle_api_errors(logger_name='auth')
def revoke_permission():
    """
    Revoke a permission from a user

    Request body:
        {
            "username": "target_user",
            "permission_key": "feature:mail_rating:view"
        }
    """
    data = request.get_json()
    username = data.get('username')
    permission_key = data.get('permission_key')

    if not username or not permission_key:
        raise ValidationError('username and permission_key are required')

    # Get admin username from token
    admin_username = AuthUtils.extract_username_without_validation()

    success = PermissionService.revoke_permission(
        username=username,
        permission_key=permission_key,
        admin_username=admin_username
    )

    if not success:
        raise ValidationError('Failed to revoke permission')

    return jsonify({
        'success': True,
        'message': f'Permission {permission_key} revoked from {username}'
    }), 200


@data_blueprint.route('/permissions/assign-role', methods=['POST'])
@require_permission('admin:roles:manage')
@handle_api_errors(logger_name='auth')
def assign_role():
    """
    Assign a role to a user

    Request body:
        {
            "username": "target_user",
            "role_name": "researcher"
        }
    """
    data = request.get_json()
    username = data.get('username')
    role_name = data.get('role_name')

    if not username or not role_name:
        raise ValidationError('username and role_name are required')

    # Get admin username from token
    admin_username = AuthUtils.extract_username_without_validation()

    success = PermissionService.assign_role(
        username=username,
        role_name=role_name,
        admin_username=admin_username
    )

    if not success:
        raise ValidationError('Failed to assign role')

    return jsonify({
        'success': True,
        'message': f'Role {role_name} assigned to {username}'
    }), 200


@data_blueprint.route('/permissions/unassign-role', methods=['POST'])
@require_permission('admin:roles:manage')
@handle_api_errors(logger_name='auth')
def unassign_role():
    """
    Unassign a role from a user

    Request body:
        {
            "username": "target_user",
            "role_name": "researcher"
        }
    """
    data = request.get_json()
    username = data.get('username')
    role_name = data.get('role_name')

    if not username or not role_name:
        raise ValidationError('username and role_name are required')

    # Get admin username from token
    admin_username = AuthUtils.extract_username_without_validation()

    success = PermissionService.unassign_role(
        username=username,
        role_name=role_name,
        admin_username=admin_username
    )

    if not success:
        raise ValidationError('Failed to unassign role')

    return jsonify({
        'success': True,
        'message': f'Role {role_name} unassigned from {username}'
    }), 200
