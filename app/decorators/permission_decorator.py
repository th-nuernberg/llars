"""
Permission Decorator

Provides @require_permission decorator for protecting Flask routes with permissions.

Usage:
    @app.route('/api/protected')
    @require_permission('feature:mail_rating:view')
    def protected_route():
        return {'message': 'Access granted'}

The decorator:
1. Extracts username from the OIDC JWT (Authentik)
2. Checks if user has the required permission via PermissionService
3. Returns 403 Forbidden if permission is denied
4. Returns 401 Unauthorized if not authenticated
"""

from functools import wraps
from flask import request, jsonify
from services.permission_service import PermissionService
import jwt
import os


def require_permission(permission_key: str):
    """
    Decorator to require a specific permission for a route.

    Args:
        permission_key: The permission key required (e.g., 'feature:mail_rating:view')

    Returns:
        Decorated function that checks permission before executing

    Example:
        @app.route('/api/mail-rating')
        @require_permission('feature:mail_rating:view')
        def mail_rating():
            return {'data': [...]}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract token from Authorization header
            auth_header = request.headers.get('Authorization')

            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'No valid authorization token provided'
                }), 401

            token = auth_header.split(' ')[1]

            try:
                # Decode token to get username
                # Note: In production, verify the token signature!
                # For now, we just decode without verification (Authentik handles verification)
                decoded_token = jwt.decode(token, options={"verify_signature": False})

                # Try standard OIDC claims first, then Authentik-specific, then fallback to uid
                username = (decoded_token.get('preferred_username') or
                           decoded_token.get('username') or
                           decoded_token.get('name') or
                           decoded_token.get('uid') or  # Authentik user ID
                           (decoded_token.get('sub')[:16] if decoded_token.get('sub') else None))

                if not username:
                    return jsonify({
                        'error': 'Unauthorized',
                        'message': 'Invalid token: no username found'
                    }), 401

            except jwt.DecodeError:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Invalid token format'
                }), 401
            except Exception as e:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': f'Token validation error: {str(e)}'
                }), 401

            # Check permission
            has_permission = PermissionService.check_permission(username, permission_key)

            if not has_permission:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Permission denied: {permission_key} required',
                    'required_permission': permission_key
                }), 403

            # Permission granted, execute the route
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_any_permission(*permission_keys):
    """
    Decorator to require ANY of the specified permissions (OR logic).

    Args:
        *permission_keys: Variable number of permission keys

    Returns:
        Decorated function that checks if user has at least one permission

    Example:
        @app.route('/api/view-data')
        @require_any_permission('feature:mail_rating:view', 'feature:ranking:view')
        def view_data():
            return {'data': [...]}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')

            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'No valid authorization token provided'
                }), 401

            token = auth_header.split(' ')[1]

            try:
                decoded_token = jwt.decode(token, options={"verify_signature": False})
                username = decoded_token.get('preferred_username')

                if not username:
                    return jsonify({
                        'error': 'Unauthorized',
                        'message': 'Invalid token: no username found'
                    }), 401

            except jwt.DecodeError:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Invalid token format'
                }), 401
            except Exception as e:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': f'Token validation error: {str(e)}'
                }), 401

            # Check if user has ANY of the required permissions
            has_any_permission = False
            for perm_key in permission_keys:
                if PermissionService.check_permission(username, perm_key):
                    has_any_permission = True
                    break

            if not has_any_permission:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Permission denied: one of {permission_keys} required',
                    'required_permissions': list(permission_keys)
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_all_permissions(*permission_keys):
    """
    Decorator to require ALL of the specified permissions (AND logic).

    Args:
        *permission_keys: Variable number of permission keys

    Returns:
        Decorated function that checks if user has all permissions

    Example:
        @app.route('/api/admin/export')
        @require_all_permissions('data:export', 'admin:system:configure')
        def admin_export():
            return {'data': [...]}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')

            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'No valid authorization token provided'
                }), 401

            token = auth_header.split(' ')[1]

            try:
                decoded_token = jwt.decode(token, options={"verify_signature": False})
                username = decoded_token.get('preferred_username')

                if not username:
                    return jsonify({
                        'error': 'Unauthorized',
                        'message': 'Invalid token: no username found'
                    }), 401

            except jwt.DecodeError:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Invalid token format'
                }), 401
            except Exception as e:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': f'Token validation error: {str(e)}'
                }), 401

            # Check if user has ALL of the required permissions
            missing_permissions = []
            for perm_key in permission_keys:
                if not PermissionService.check_permission(username, perm_key):
                    missing_permissions.append(perm_key)

            if missing_permissions:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Permission denied: all of {permission_keys} required',
                    'required_permissions': list(permission_keys),
                    'missing_permissions': missing_permissions
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator
