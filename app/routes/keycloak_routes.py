"""
Keycloak-compatible Authentication Routes
These routes provide compatibility with the frontend while using Keycloak for authentication
"""

from flask import Blueprint, jsonify, request, g, current_app
from auth.decorators import keycloak_required, admin_required
from auth.keycloak_validator import get_token_from_request, validate_token, get_username, get_user_id
from functools import wraps

# Create blueprint for Keycloak-specific routes
keycloak_auth_blueprint = Blueprint('keycloak_auth', __name__)


def rate_limit(limit_string):
    """Custom rate limit decorator that works with blueprints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Rate limiting wird durch Flask-Limiter auf App-Level gehandhabt
            # Hier nur als Dokumentation der Limits
            return f(*args, **kwargs)
        decorated_function._rate_limit = limit_string
        return decorated_function
    return decorator


@keycloak_auth_blueprint.route('/health_check', methods=['GET'])
def health_check():
    """Health check endpoint - no authentication required"""
    return jsonify({"message": "Server is running with Keycloak authentication"}), 200


@keycloak_auth_blueprint.route('/me', methods=['GET'])
@keycloak_required
@rate_limit("100 per hour")
def get_current_user():
    """
    Get current authenticated user information
    Uses Keycloak token to return user details
    Rate limit: 100 requests per hour per IP
    """
    return jsonify({
        "username": g.keycloak_user,
        "user_id": g.keycloak_user_id,
        "roles": g.keycloak_token.get('realm_access', {}).get('roles', []),
        "email": g.keycloak_token.get('email'),
        "name": g.keycloak_token.get('name'),
        "preferred_username": g.keycloak_token.get('preferred_username')
    }), 200


@keycloak_auth_blueprint.route('/validate', methods=['GET'])
@rate_limit("200 per hour")
def validate_token_endpoint():
    """
    Validate token endpoint - for frontend to check if token is still valid
    Rate limit: 200 requests per hour per IP
    """
    token = get_token_from_request()

    if not token:
        return jsonify({'valid': False, 'error': 'No token provided'}), 401

    token_payload = validate_token(token)

    if token_payload:
        return jsonify({
            'valid': True,
            'username': get_username(token_payload),
            'user_id': get_user_id(token_payload),
            'roles': token_payload.get('realm_access', {}).get('roles', [])
        }), 200
    else:
        return jsonify({'valid': False, 'error': 'Invalid or expired token'}), 401


@keycloak_auth_blueprint.route('/admin/check', methods=['GET'])
@admin_required
def check_admin():
    """
    Admin check endpoint - returns 200 if user is admin, 403 otherwise
    """
    return jsonify({
        "message": "User has admin privileges",
        "username": g.keycloak_user
    }), 200
