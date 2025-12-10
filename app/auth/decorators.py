"""
OIDC Authentication Decorators for Flask (Authentik-backed)
Provides decorators for protecting routes with bearer tokens
"""

import os
import uuid
import logging
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


def get_or_create_user(username: str):
    """
    Get existing user from database or create a new one.

    Args:
        username: The username from Authentik token

    Returns:
        User object from database
    """
    from db.db import db
    from db.tables import User, UserGroup

    user = User.query.filter_by(username=username).first()
    if not user:
        # Get default user group
        default_group = UserGroup.query.filter_by(name='Standard').first()
        group_id = default_group.id if default_group else 1

        # Create new user
        user = User(
            username=username,
            password_hash='',  # Auth via Authentik, no local password
            api_key=str(uuid.uuid4()),
            group_id=group_id
        )
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created new user from Authentik login: {username}")

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
