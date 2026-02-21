"""
Authentication Routes

Provides user registration, login, logout, and health check endpoints.
Integrates with Authentik for authentication.
"""

import os
from uuid import uuid4

from flask import jsonify, request
from flask_jwt_extended import jwt_required

from routes.auth import auth_bp
from services.user_service import UserService
from auth.decorators import public_endpoint
from decorators.error_handler import (
    handle_api_errors, ValidationError, ConflictError, UnauthorizedError
)


@auth_bp.route('/register', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='auth')
def register():
    """Register a new user"""
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
            "api_key": new_user.api_key,
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
@jwt_required()
@handle_api_errors(logger_name='auth')
def logout():
    """Logout endpoint"""
    return jsonify({"success": True, "message": "Logged out successfully"}), 200


@auth_bp.route('/register_admin', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='auth')
def register_admin():
    """Register an admin user with admin registration key"""
    ADMIN_REGISTRATION_KEY = os.environ.get('ADMIN_REGISTRATION_KEY', '')
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('api_key', str(uuid4()))
    admin_registration_key = data.get('admin_registration_key')

    # Verify admin registration key
    if admin_registration_key != ADMIN_REGISTRATION_KEY:
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
            "api_key": new_user.api_key,
            "group": new_user.group.name
        }
    }), 201
