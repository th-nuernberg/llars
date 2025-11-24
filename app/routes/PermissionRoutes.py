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
import jwt
from decorators.permission_decorator import require_permission
from services.permission_service import PermissionService
from routes import data_blueprint


@data_blueprint.route('/permissions', methods=['GET'])
@require_permission('admin:permissions:manage')
def get_all_permissions():
    """Get all available permissions in the system"""
    try:
        permissions = PermissionService.get_all_permissions()
        return jsonify({
            'success': True,
            'permissions': permissions
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_blueprint.route('/permissions/roles', methods=['GET'])
@require_permission('admin:permissions:manage')
def get_all_roles():
    """Get all available roles in the system"""
    try:
        roles = PermissionService.get_all_roles()
        return jsonify({
            'success': True,
            'roles': roles
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_blueprint.route('/permissions/user/<username>', methods=['GET'])
@require_permission('admin:permissions:manage')
def get_user_permissions(username):
    """Get all permissions and roles for a specific user"""
    try:
        permissions = PermissionService.get_user_permissions(username)
        roles = PermissionService.get_user_roles(username)

        return jsonify({
            'success': True,
            'username': username,
            'permissions': permissions,
            'roles': roles
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_blueprint.route('/permissions/my-permissions', methods=['GET'])
def get_my_permissions():
    """Get current user's permissions (no admin permission required)"""
    try:
        # Extract username from token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 401

        token = auth_header.split(' ')[1]
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        username = decoded_token.get('preferred_username')

        if not username:
            return jsonify({
                'success': False,
                'error': 'Invalid token'
            }), 401

        permissions = PermissionService.get_user_permissions(username)
        roles = PermissionService.get_user_roles(username)

        return jsonify({
            'success': True,
            'username': username,
            'permissions': permissions,
            'roles': roles
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_my_permissions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_blueprint.route('/permissions/grant', methods=['POST'])
@require_permission('admin:permissions:manage')
def grant_permission():
    """
    Grant a permission to a user

    Request body:
        {
            "username": "target_user",
            "permission_key": "feature:mail_rating:view"
        }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        permission_key = data.get('permission_key')

        if not username or not permission_key:
            return jsonify({
                'success': False,
                'error': 'username and permission_key are required'
            }), 400

        # Get admin username from token
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        admin_username = decoded_token.get('preferred_username')

        success = PermissionService.grant_permission(
            username=username,
            permission_key=permission_key,
            admin_username=admin_username
        )

        if success:
            return jsonify({
                'success': True,
                'message': f'Permission {permission_key} granted to {username}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to grant permission'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_blueprint.route('/permissions/revoke', methods=['POST'])
@require_permission('admin:permissions:manage')
def revoke_permission():
    """
    Revoke a permission from a user

    Request body:
        {
            "username": "target_user",
            "permission_key": "feature:mail_rating:view"
        }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        permission_key = data.get('permission_key')

        if not username or not permission_key:
            return jsonify({
                'success': False,
                'error': 'username and permission_key are required'
            }), 400

        # Get admin username from token
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        admin_username = decoded_token.get('preferred_username')

        success = PermissionService.revoke_permission(
            username=username,
            permission_key=permission_key,
            admin_username=admin_username
        )

        if success:
            return jsonify({
                'success': True,
                'message': f'Permission {permission_key} revoked from {username}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to revoke permission'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_blueprint.route('/permissions/assign-role', methods=['POST'])
@require_permission('admin:roles:manage')
def assign_role():
    """
    Assign a role to a user

    Request body:
        {
            "username": "target_user",
            "role_name": "researcher"
        }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        role_name = data.get('role_name')

        if not username or not role_name:
            return jsonify({
                'success': False,
                'error': 'username and role_name are required'
            }), 400

        # Get admin username from token
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        admin_username = decoded_token.get('preferred_username')

        success = PermissionService.assign_role(
            username=username,
            role_name=role_name,
            admin_username=admin_username
        )

        if success:
            return jsonify({
                'success': True,
                'message': f'Role {role_name} assigned to {username}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to assign role'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_blueprint.route('/permissions/unassign-role', methods=['POST'])
@require_permission('admin:roles:manage')
def unassign_role():
    """
    Unassign a role from a user

    Request body:
        {
            "username": "target_user",
            "role_name": "researcher"
        }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        role_name = data.get('role_name')

        if not username or not role_name:
            return jsonify({
                'success': False,
                'error': 'username and role_name are required'
            }), 400

        # Get admin username from token
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        admin_username = decoded_token.get('preferred_username')

        success = PermissionService.unassign_role(
            username=username,
            role_name=role_name,
            admin_username=admin_username
        )

        if success:
            return jsonify({
                'success': True,
                'message': f'Role {role_name} unassigned from {username}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to unassign role'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
