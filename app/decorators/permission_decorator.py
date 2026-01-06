"""
Permission Decorator

Provides @require_permission decorator for protecting Flask routes with permissions.

Usage:
    @app.route('/api/protected')
    @require_permission('feature:mail_rating:view')
    def protected_route():
        return {'message': 'Access granted'}

The decorator:
1. Checks for System Admin API Key (X-API-Key header) - bypasses permission check
2. Extracts username from the OIDC JWT (Authentik)
3. Checks if user has the required permission via PermissionService
4. Returns 403 Forbidden if permission is denied
5. Returns 401 Unauthorized if not authenticated
"""

from functools import wraps
from flask import request, jsonify, g
from services.permission_service import PermissionService
from auth.auth_utils import AuthUtils
import os
import logging

logger = logging.getLogger(__name__)

# System Admin API Key (loaded from environment)
SYSTEM_ADMIN_API_KEY = os.environ.get('SYSTEM_ADMIN_API_KEY')
SYSTEM_ADMIN_USERNAME = 'admin'


def _check_system_api_key() -> bool:
    """
    Check if request contains a valid System Admin API Key.

    Returns:
        True if valid API key provided, False otherwise
    """
    if not SYSTEM_ADMIN_API_KEY:
        return False

    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key:
        return False

    if api_key == SYSTEM_ADMIN_API_KEY:
        logger.debug(f"System API key authenticated for {request.path}")
        return True

    return False


def _deny_if_user_locked(username: str):
    """
    Ensure the authenticated user exists in DB and is allowed to access the system.

    Returns:
        A Flask (json, status) tuple if access should be denied, otherwise None.
    """
    from auth.decorators import get_or_create_user

    user = get_or_create_user(username)
    if user is None:
        return None

    if getattr(user, 'deleted_at', None) is not None:
        return jsonify({
            'error': 'Forbidden',
            'message': 'Account has been deleted',
            'code': 'ACCOUNT_DELETED'
        }), 403

    if not bool(getattr(user, 'is_active', True)):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Account is locked',
            'code': 'ACCOUNT_LOCKED'
        }), 403

    return None


def require_permission(permission_key: str):
    """
    Decorator to require a specific permission for a route.

    Supports two authentication methods:
    1. System Admin API Key (X-API-Key header) - bypasses permission check, uses admin user
    2. OIDC JWT token (Authorization: Bearer) - checks permission via PermissionService

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
            # Check for System Admin API Key first (bypasses permission check)
            if _check_system_api_key():
                from auth.decorators import get_or_create_user
                g.authentik_user = get_or_create_user(SYSTEM_ADMIN_USERNAME)
                g.is_system_api_key = True
                return f(*args, **kwargs)

            # Extract username from token using centralized AuthUtils
            username = AuthUtils.extract_username_from_token()

            if not username:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'No valid authorization token provided or username not found'
                }), 401

            denied = _deny_if_user_locked(username)
            if denied is not None:
                return denied

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
            # Extract username from token using centralized AuthUtils
            username = AuthUtils.extract_username_from_token()

            if not username:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'No valid authorization token provided or username not found'
                }), 401

            denied = _deny_if_user_locked(username)
            if denied is not None:
                return denied

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


def has_role(user, role_name: str) -> bool:
    """
    Check if a user has a specific system role.

    Args:
        user: User object or username (from g.authentik_user)
        role_name: The role name to check (e.g., 'admin', 'researcher', 'evaluator')

    Returns:
        True if user has the role, False otherwise

    Example:
        if has_role(g.authentik_user, 'admin'):
            # Admin-only logic
    """
    username = getattr(user, 'username', str(user)) if user else None
    if not username:
        return False

    return PermissionService.user_has_role(username, role_name)


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
            # Extract username from token using centralized AuthUtils
            username = AuthUtils.extract_username_from_token()

            if not username:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'No valid authorization token provided or username not found'
                }), 401

            denied = _deny_if_user_locked(username)
            if denied is not None:
                return denied

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
