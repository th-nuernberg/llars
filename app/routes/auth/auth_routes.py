"""
Authentication Routes

Provides user registration, login, logout, and health check endpoints.
Integrates with Authentik for authentication.
"""

import hmac
import logging
import os
from uuid import uuid4

from flask import jsonify, request
from flask_jwt_extended import jwt_required

from routes.auth import auth_bp
from services.user_service import UserService
from auth.decorators import authentik_required, public_endpoint
from decorators.error_handler import (
    handle_api_errors, ValidationError, ConflictError, UnauthorizedError
)

logger = logging.getLogger(__name__)


@auth_bp.route('/register', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='auth')
def register():
    """
    Register a new user.

    Security: This endpoint is disabled in production.
    User registration should go through Authentik OIDC flow.
    """
    from flask import current_app
    if current_app.config.get('ENV') == 'production' or os.environ.get('PROJECT_STATE') == 'production':
        logger.warning("[Auth] Registration endpoint called in production - blocked")
        raise UnauthorizedError("Registration is disabled. Use Authentik for account creation.")

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('api_key', str(uuid4()))
    group_name = data.get('group')

    if not username or not password:
        raise ValidationError("Username and password are required")

    if not api_key or not UserService.validate_uuid(api_key):
        raise ValidationError("Invalid API key")

    # Use UserService to create user
    success, new_user, error_msg = UserService.create_user(
        username=username,
        password=password,
        api_key=api_key,
        group_name=group_name
    )

    if not success:
        # Determine appropriate status code based on error
        if "already exists" in error_msg:
            raise ConflictError(error_msg)
        elif "does not exist" in error_msg:
            raise ValidationError(error_msg)
        else:
            raise ValidationError(error_msg)

    return jsonify({
        "success": True,
        "message": "User registered successfully",
        "data": {
            "api_key": api_key,  # Return the plaintext key once (stored hashed)
            "group": new_user.group.name
        }
    }), 201


@auth_bp.route('/health_check', methods=['GET'])
@public_endpoint
@handle_api_errors(logger_name='auth')
def health_check():
    """Health check endpoint"""
    return jsonify({"success": True, "message": "Server is running"}), 200


@auth_bp.route('/login', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='auth')
def login():
    """
    Login endpoint - delegates to Authentik authentication.
    Uses the Authentik Flow Executor API and returns RS256 signed JWT tokens.
    """
    # Import and delegate to Authentik login implementation
    from routes.authentik_routes import login as authentik_login
    return authentik_login()


@auth_bp.route('/logout', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='auth')
def logout():
    """Logout endpoint"""
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@auth_bp.route('/register_admin', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='auth')
def register_admin():
    """Register an admin user with admin registration key."""
    # Security: Block in production if key is not changed from default placeholder
    ADMIN_REGISTRATION_KEY = os.environ.get('ADMIN_REGISTRATION_KEY', '').strip()
    project_state = os.environ.get('PROJECT_STATE', 'development')
    default_placeholder = 'CHANGE_ME_GENERATE_NEW_UUID_FOR_PRODUCTION'
    if project_state == 'production' and (
        not ADMIN_REGISTRATION_KEY or ADMIN_REGISTRATION_KEY == default_placeholder
    ):
        logger.error("[Auth] Admin registration blocked: ADMIN_REGISTRATION_KEY is default/empty in production")
        raise UnauthorizedError("Admin registration is not available.")

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('api_key', str(uuid4()))
    admin_registration_key = data.get('admin_registration_key', '')

    # Security: Require non-empty admin registration key
    if not ADMIN_REGISTRATION_KEY:
        logger.error("[Auth] ADMIN_REGISTRATION_KEY not set - admin registration blocked")
        raise UnauthorizedError("Admin registration is not configured.")

    # Verify admin registration key with timing-safe comparison
    if not isinstance(admin_registration_key, str) or not hmac.compare_digest(
        admin_registration_key.encode('utf-8'),
        ADMIN_REGISTRATION_KEY.encode('utf-8')
    ):
        raise UnauthorizedError("Unauthorized. Invalid admin registration key.")

    if not username or not password:
        raise ValidationError("Username and password are required")

    # Use UserService to create admin user
    success, new_user, error_msg = UserService.create_user(
        username=username,
        password=password,
        api_key=api_key,
        group_name="Admin"
    )

    if not success:
        # Determine appropriate status code
        if "already exists" in error_msg:
            raise ConflictError(error_msg)
        else:
            raise ValidationError(error_msg)

    return jsonify({
        "success": True,
        "message": "Admin user registered successfully",
        "data": {
            "api_key": api_key,  # Return the plaintext key once (stored hashed)
            "group": new_user.group.name
        }
    }), 201
