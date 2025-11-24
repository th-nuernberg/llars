"""
OIDC Authentication Decorators for Flask (Authentik-backed)
Provides decorators for protecting routes with bearer tokens
"""

from functools import wraps
from flask import request, jsonify, g
from .oidc_validator import (
    validate_token,
    get_token_from_request,
    has_role,
    get_username,
    get_user_id
)


def authentik_required(f):
    """
    Decorator to require valid Authentik authentication

    Usage:
        @app.route('/protected')
        @authentik_required
        def protected_route():
            username = g.authentik_user
            return jsonify({'message': f'Hello {username}'})
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
        g.authentik_user = get_username(token_payload)
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
                g.authentik_user = get_username(token_payload)
                g.authentik_user_id = get_user_id(token_payload)

        return f(*args, **kwargs)

    return decorated_function
