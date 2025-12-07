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


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('api_key', str(uuid4()))
    group_name = data.get('group')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if not api_key or not UserService.validate_uuid(api_key):
        return jsonify({"error": "Invalid API key"}), 400

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
            return jsonify({"error": error_msg}), 409
        elif "does not exist" in error_msg:
            return jsonify({"error": error_msg}), 400
        else:
            return jsonify({"error": error_msg}), 400

    return jsonify({
        "message": "User registered successfully",
        "api_key": new_user.api_key,
        "group": new_user.group.name
    }), 201


@auth_bp.route('/health_check', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"message": "Server is running"}), 200


@auth_bp.route('/login', methods=['POST'])
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
def logout():
    """Logout endpoint"""
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route('/register_admin', methods=['POST'])
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
        return jsonify({"error": "Unauthorized. Invalid admin registration key."}), 403

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

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
            return jsonify({"error": error_msg}), 409
        else:
            return jsonify({"error": error_msg}), 400

    return jsonify({
        "message": "Admin user registered successfully",
        "api_key": new_user.api_key,
        "group": new_user.group.name
    }), 201
