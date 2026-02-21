"""
OIDC Authentication Decorators for Flask (Authentik-backed)
Provides decorators for protecting routes with bearer tokens
"""

import os
import uuid
import logging
from datetime import datetime
from functools import wraps
from flask import request, jsonify, g
from .oidc_validator import (
    validate_token,
    get_token_from_request,
    has_role,
    get_username,
    get_user_id
)

logger = logging.getLogger(__name__)


def _check_user_account_state(user):
    """
    Deny access for locked/deleted users based on DB state.

    Returns:
        (response, status_code) tuple if access should be denied, otherwise None.
    """
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


def _ensure_default_evaluator_role(username: str) -> None:
    """
    Ensure a newly created user has at least the evaluator role so basic features work.
    Falls back to legacy viewer role if evaluator is missing.
    """
    if not username:
        return
    from db.database import db
    from db.tables import Role, UserRole

    existing_role = UserRole.query.filter_by(username=username).first()
    if existing_role:
        return

    evaluator_role = Role.query.filter_by(role_name='evaluator').first()
    if not evaluator_role:
        try:
            from db.seeders.permissions import initialize_permissions

            initialize_permissions(db)
        except Exception as exc:
            logger.warning(f"Failed to seed permissions while assigning evaluator role: {exc}")
        evaluator_role = Role.query.filter_by(role_name='evaluator').first()
    if not evaluator_role:
        evaluator_role = Role.query.filter_by(role_name='viewer').first()
    if not evaluator_role:
        logger.warning(f"Evaluator role missing; cannot auto-assign for {username}")
        return

    try:
        db.session.add(UserRole(
            username=username,
            role_id=evaluator_role.id,
            assigned_by='system',
            assigned_at=datetime.utcnow()
        ))
        db.session.commit()
        logger.info(f"Assigned evaluator role to new user {username}")
    except Exception:
        db.session.rollback()


def get_or_create_user(username: str):
    """
    Get existing user from database or create a new one.

    Args:
        username: The username from Authentik token

    Returns:
        User object from database
    """
    from db.database import db
    from db.tables import User, UserGroup
    from services.user_profile_service import pick_collab_color

    user = User.query.filter_by(username=username).first()
    if not user:
        # Get default user group
        default_group = UserGroup.query.filter_by(name='Standard').first()
        group_id = default_group.id if default_group else 1

        # Assign unique collab color - prefer one that's not already in use
        collab_color = pick_collab_color()

        # Create new user
        user = User(
            username=username,
            password_hash='',  # Auth via Authentik, no local password
            api_key=str(uuid.uuid4()),
            group_id=group_id,
            collab_color=collab_color
        )
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created new user from Authentik login: {username} with collab_color={collab_color}")
        try:
            from services.system_event_service import SystemEventService

            SystemEventService.log_event(
                event_type="user.created",
                severity="info",
                username=username,
                entity_type="user",
                entity_id=username,
                message=f"User '{username}' created from Authentik login",
                details={"source": "authentik"},
            )
        except Exception:
            # Never block auth flow on telemetry
            pass

    changed = False
    if not user.collab_color:
        user.collab_color = pick_collab_color()
        changed = True
    if hasattr(user, "get_avatar_seed") and not user.avatar_seed:
        user.get_avatar_seed()
        changed = True
    if changed:
        db.session.commit()
    _ensure_default_evaluator_role(username)
    return user

# System Admin API Key (loaded from environment)
SYSTEM_ADMIN_API_KEY = os.environ.get('SYSTEM_ADMIN_API_KEY')
SYSTEM_ADMIN_USERNAME = 'admin'  # The username this API key is linked to


def authentik_required(f):
    """
    Decorator to require valid Authentik authentication.

    Sets g.authentik_user to the User object from database (not just username string).

    Usage:
        @app.route('/protected')
        @authentik_required
        def protected_route():
            user = g.authentik_user  # User object with .id, .username, etc.
            return jsonify({'message': f'Hello {user.username}'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract token from Authorization header
        token = get_token_from_request()

        if not token:
            return jsonify({
                'error': 'Missing authorization token',
                'message': 'Authorization header with Bearer token is required'
            }), 401

        # Validate token
        token_payload = validate_token(token)

        if not token_payload:
            return jsonify({
                'error': 'Invalid or expired token',
                'message': 'Please log in again'
            }), 401

        # Store token payload in Flask's g object for access in route
        g.authentik_token = token_payload
        username = get_username(token_payload)
        g.authentik_user = get_or_create_user(username)  # User object from DB
        g.authentik_user_id = get_user_id(token_payload)

        denied = _check_user_account_state(g.authentik_user)
        if denied is not None:
            return denied

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Decorator to require admin role

    Usage:
        @app.route('/admin/users')
        @admin_required
        def admin_route():
            return jsonify({'message': 'Admin access granted'})
    """
    @wraps(f)
    @authentik_required  # First check if authenticated
    def decorated_function(*args, **kwargs):
        token_payload = g.authentik_token

        # Check for admin role
        if not has_role(token_payload, 'admin'):
            return jsonify({
                'error': 'Insufficient permissions',
                'message': 'Admin role required'
            }), 403

        return f(*args, **kwargs)

    return decorated_function


def roles_required(*required_roles):
    """
    Decorator to require one or more specific roles

    Usage:
        @app.route('/rater/features')
        @roles_required('rater', 'admin')
        def rater_route():
            return jsonify({'message': 'Rater access granted'})
    """
    def decorator(f):
        @wraps(f)
        @authentik_required  # First check if authenticated
        def decorated_function(*args, **kwargs):
            token_payload = g.authentik_token

            # Check if user has any of the required roles
            user_has_role = any(has_role(token_payload, role) for role in required_roles)

            if not user_has_role:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'One of the following roles is required: {", ".join(required_roles)}'
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def public_endpoint(f):
    """
    Decorator to explicitly mark a route as public (no auth required).

    This is used by security tests to ensure every route is either protected
    or intentionally public.
    """
    setattr(f, "_public_endpoint", True)
    return f


def optional_auth(f):
    """
    Decorator for routes that work with or without authentication
    If token is present and valid, user info is added to g object
    If token is missing or invalid, the route still proceeds

    Usage:
        @app.route('/public')
        @optional_auth
        def public_route():
            if hasattr(g, 'authentik_user'):
                return jsonify({'message': f'Hello {g.authentik_user}'})
            else:
                return jsonify({'message': 'Hello guest'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()

        if token:
            token_payload = validate_token(token)
            if token_payload:
                g.authentik_token = token_payload
                username = get_username(token_payload)
                g.authentik_user = get_or_create_user(username)  # User object from DB
                g.authentik_user_id = get_user_id(token_payload)
                denied = _check_user_account_state(g.authentik_user)
                if denied is not None:
                    return denied

        return f(*args, **kwargs)

    return decorated_function


def system_api_key_required(f):
    """
    Decorator to require valid System Admin API Key for debug/admin endpoints.

    The API key should be passed via:
    - Header: X-API-Key: <key>
    - Or Query param: ?api_key=<key>

    This decorator sets g.authentik_user to 'admin' for compatibility
    with existing code that uses the username.

    Usage:
        @app.route('/debug/something')
        @system_api_key_required
        def debug_route():
            return jsonify({'message': 'Debug access granted'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if API key is configured
        if not SYSTEM_ADMIN_API_KEY:
            logger.error("SYSTEM_ADMIN_API_KEY not configured in environment")
            return jsonify({
                'error': 'Server configuration error',
                'message': 'System API key not configured'
            }), 500

        # Get API key from request (header or query param)
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not api_key:
            return jsonify({
                'error': 'Missing API key',
                'message': 'X-API-Key header or api_key query parameter is required'
            }), 401

        # Validate API key
        if api_key != SYSTEM_ADMIN_API_KEY:
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401

        # Set user context for compatibility with existing code
        g.authentik_user = get_or_create_user(SYSTEM_ADMIN_USERNAME)  # User object from DB
        g.authentik_user_id = SYSTEM_ADMIN_USERNAME
        g.is_system_api_key = True

        denied = _check_user_account_state(g.authentik_user)
        if denied is not None:
            return denied

        logger.debug(f"System API key authenticated for {request.path}")
        return f(*args, **kwargs)

    return decorated_function


def debug_route_protected(f):
    """
    Decorator specifically for debug routes.
    - In development: Requires System Admin API Key
    - In production: Completely disabled (returns 403)

    Usage:
        @app.route('/debug/something')
        @debug_route_protected
        def debug_route():
            return jsonify({'message': 'Debug access granted'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        flask_env = os.environ.get('FLASK_ENV', 'production')

        # Completely disable in production
        if flask_env != 'development':
            return jsonify({
                'error': 'Debug endpoint disabled',
                'message': 'This endpoint is only available in development mode'
            }), 403

        # In development, require API key
        return system_api_key_required(f)(*args, **kwargs)

    return decorated_function


def api_key_or_token_required(f):
    """
    Decorator that accepts either:
    1. User's personal API key (X-API-Key header or api_key query param)
    2. System Admin API key
    3. OAuth Bearer token

    This is useful for programmatic access to the API.

    The user's API key is stored in the users.api_key field.

    Usage:
        @app.route('/api/something')
        @api_key_or_token_required
        def api_route():
            user = g.authentik_user  # User object
            return jsonify({'message': f'Hello {user.username}'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from db.models import User

        # 1. Try API Key first (header or query param)
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if api_key:
            # Check if it's the System Admin API Key
            if SYSTEM_ADMIN_API_KEY and api_key == SYSTEM_ADMIN_API_KEY:
                g.authentik_user = get_or_create_user(SYSTEM_ADMIN_USERNAME)
                g.authentik_user_id = SYSTEM_ADMIN_USERNAME
                g.is_system_api_key = True
                g.auth_method = 'system_api_key'

                denied = _check_user_account_state(g.authentik_user)
                if denied is not None:
                    return denied

                logger.debug(f"System API key authenticated for {request.path}")
                return f(*args, **kwargs)

            # Check if it's a user's personal API key
            user = User.query.filter_by(api_key=api_key).first()
            if user:
                denied = _check_user_account_state(user)
                if denied is not None:
                    return denied

                g.authentik_user = user
                g.authentik_user_id = user.id
                g.is_system_api_key = False
                g.auth_method = 'user_api_key'

                logger.debug(f"User API key authenticated: {user.username} for {request.path}")
                return f(*args, **kwargs)

            # Invalid API key
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401

        # 2. Try OAuth Bearer token
        token = get_token_from_request()

        if token:
            token_payload = validate_token(token)
            if token_payload:
                g.authentik_token = token_payload
                username = get_username(token_payload)
                g.authentik_user = get_or_create_user(username)
                g.authentik_user_id = get_user_id(token_payload)
                g.auth_method = 'oauth_token'

                denied = _check_user_account_state(g.authentik_user)
                if denied is not None:
                    return denied

                return f(*args, **kwargs)

        # 3. No valid authentication provided
        return jsonify({
            'error': 'Authentication required',
            'message': 'Provide either X-API-Key header, api_key query param, or Authorization Bearer token'
        }), 401

    return decorated_function
