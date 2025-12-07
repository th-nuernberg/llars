# routes.py

import logging
import os

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash
from . import data_blueprint
from . import auth_blueprint
from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating, UserGroup, ConsultingCategoryType,
                       UserConsultingCategorySelection, UserMessageRating, UserPrompt, UserPromptShare)
from sqlalchemy import func
from uuid import uuid4
import uuid
from dateutil import parser
from datetime import datetime
import json

# Import service layer
from services.user_service import UserService
from services.thread_service import ThreadService
from services.ranking_service import RankingService
from services.feature_service import FeatureService


def is_valid_uuid(uuid_to_test, version=4):
    """Validate if a string is a valid UUID - delegates to UserService"""
    return UserService.validate_uuid(uuid_to_test, version)


def get_or_create_default_group():
    """Get or create default user group - delegates to UserService"""
    return UserService.get_or_create_default_group()


@auth_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('api_key', str(uuid4()))
    group_name = data.get('group')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if not api_key or not is_valid_uuid(api_key):
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


@auth_blueprint.route('/health_check', methods=['GET'])
def health_check():
    return jsonify({"message": "Server is running"}), 200


@auth_blueprint.route('/login', methods=['POST'])
def login():
    """
    Login endpoint - delegates to Authentik authentication.
    Uses the Authentik Flow Executor API and returns RS256 signed JWT tokens.
    """
    # Import and delegate to Authentik login implementation
    from routes.authentik_routes import login as authentik_login
    return authentik_login()


@auth_blueprint.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully"}), 200




@data_blueprint.route('/email_threads', methods=['POST'])
def create_email_thread():
    data = request.get_json()

    # Get and validate function_type from the request payload using ThreadService
    function_type_input = data.get('type', '').lower()
    function_type_id = ThreadService.map_function_type_input(function_type_input)

    if not function_type_id:
        return jsonify({"error": "Invalid function type"}), 400

    sender = data.get('sender', 'Alias')

    # Use ThreadService to create or update thread
    success, email_thread, error_msg = ThreadService.create_or_update_thread(
        chat_id=data.get('chat_id'),
        institut_id=data.get('institut_id'),
        function_type_id=function_type_id,
        subject=data.get('subject'),
        sender=sender
    )

    if not success:
        return jsonify({"error": error_msg}), 400

    # Process messages using ThreadService
    for msg in data.get('messages', []):
        raw_timestamp = msg.get('timestamp')
        msg_timestamp = ThreadService.parse_timestamp(raw_timestamp)

        if not msg_timestamp:
            # Skip messages with invalid timestamps
            continue

        msg_content = msg.get('content')
        generated_by = msg.get('generated_by', 'human')

        # Use ThreadService to add message
        success, message, error_msg = ThreadService.add_message_to_thread(
            thread_id=email_thread.thread_id,
            sender=msg.get('sender'),
            content=msg_content,
            timestamp=msg_timestamp,
            generated_by=generated_by
        )

        if not success:
            # Log error but continue processing
            logging.warning(f"Failed to add message: {error_msg}")

    # Process features using ThreadService
    for model_name, features in data.get('generated_features', {}).items():
        for feature_key, feature_content in features.items():
            # Use ThreadService to add feature
            success, feature, error_msg = ThreadService.add_feature_to_thread(
                thread_id=email_thread.thread_id,
                llm_name=model_name,
                feature_type_name=feature_key,
                content=feature_content
            )

            if not success:
                # Log error but continue processing
                logging.warning(f"Failed to add feature: {error_msg}")

    return jsonify({'status': 'success', 'thread_id': email_thread.thread_id}), 201





import csv
from io import StringIO
from flask import Response


@data_blueprint.route('/rankings/csv', methods=['GET'])
def download_rankings_csv():
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    # Use UserService for authentication
    is_valid, user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        return jsonify({'error': error_msg}), 401

    # Use RankingService to generate CSV data
    csv_rows = RankingService.generate_rankings_csv_data()

    # Create a string buffer to write the CSV data
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Write all rows (including header)
    csv_writer.writerows(csv_rows)

    # Get the CSV content from the buffer before closing it
    csv_content = csv_buffer.getvalue()
    csv_buffer.close()

    # Create a response with the CSV content
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=rankings.csv'}
    )




@data_blueprint.route('/email_threads/consulting_category_types', methods=['GET'])
def get_consulting_category_types():
    # Use UserService for authentication
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    is_valid, user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        return jsonify({'error': error_msg}), 401

    # Use ThreadService to get consulting category types
    categories = ThreadService.get_consulting_category_types()

    if not categories:
        return jsonify({'error': 'No consulting category types found'}), 401

    return jsonify({'consulting_category_types': categories}), 200




@data_blueprint.route('/admin/change_user_group', methods=['POST'])
def change_user_group():
    api_key = request.headers.get('Authorization')

    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    # Use UserService for authentication
    is_valid, admin_user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        return jsonify({'error': error_msg}), 401

    data = request.get_json()
    username = data.get('username')
    new_group_name = data.get('new_group')

    if not username or not new_group_name:
        return jsonify({'error': 'Username and new group are required'}), 400

    # Use UserService to change user group
    success, error_msg = UserService.change_user_group(username, new_group_name, admin_user)

    if not success:
        # Determine appropriate status code
        if "not found" in error_msg or "does not exist" in error_msg:
            return jsonify({'error': error_msg}), 404
        elif "permission" in error_msg:
            return jsonify({'error': error_msg}), 403
        else:
            return jsonify({'error': error_msg}), 400

    return jsonify({'message': f"User '{username}' has been moved to group '{new_group_name}'"}), 200


def get_or_create_admin_group():
    """Get or create admin user group - delegates to UserService"""
    return UserService.get_or_create_group("Admin")


@auth_blueprint.route('/register_admin', methods=['POST'])
def register_admin():
    ADMIN_REGISTRATION_KEY = os.environ.get('ADMIN_REGISTRATION_KEY', '')
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('api_key', str(uuid4()))
    admin_registration_key = data.get('admin_registration_key')

    # Überprüfen, ob der übergebene Registrierungsschlüssel korrekt ist
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

from flask_jwt_extended import jwt_required


@data_blueprint.route('/users/check/<username>', methods=['GET'])
def check_user_exists(username):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    # Use UserService for authentication
    is_valid, requesting_user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        return jsonify({'error': error_msg}), 401

    # Use UserService to check if user exists
    exists = UserService.user_exists(username)
    if exists:
        return jsonify({'exists': True}), 200
    return jsonify({'exists': False}), 404


