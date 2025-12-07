"""
Data Management Routes

Provides endpoints for managing email threads, rankings CSV export,
consulting categories, and admin operations.
"""

import csv
import logging
from io import StringIO

from flask import Response, jsonify, request

from routes.auth import data_bp
from services.ranking_service import RankingService
from services.thread_service import ThreadService
from services.user_service import UserService
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, UnauthorizedError
)


@data_bp.route('/email_threads', methods=['POST'])
@handle_api_errors(logger_name='auth')
def create_email_thread():
    """Create or update an email thread with messages and features"""
    data = request.get_json()

    # Get and validate function_type from the request payload using ThreadService
    function_type_input = data.get('type', '').lower()
    function_type_id = ThreadService.map_function_type_input(function_type_input)

    if not function_type_id:
        raise ValidationError("Invalid function type")

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
        raise ValidationError(error_msg)

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

    return jsonify({'success': True, 'status': 'success', 'data': {'thread_id': email_thread.thread_id}}), 201


@data_bp.route('/rankings/csv', methods=['GET'])
@handle_api_errors(logger_name='auth')
def download_rankings_csv():
    """Download rankings as CSV file"""
    api_key = request.headers.get('Authorization')
    if not api_key:
        raise UnauthorizedError('API key is missing')

    # Use UserService for authentication
    is_valid, user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        raise UnauthorizedError(error_msg)

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


@data_bp.route('/email_threads/consulting_category_types', methods=['GET'])
@handle_api_errors(logger_name='auth')
def get_consulting_category_types():
    """Get all consulting category types"""
    # Use UserService for authentication
    api_key = request.headers.get('Authorization')
    if not api_key:
        raise UnauthorizedError('API key is missing')

    is_valid, user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        raise UnauthorizedError(error_msg)

    # Use ThreadService to get consulting category types
    categories = ThreadService.get_consulting_category_types()

    if not categories:
        raise NotFoundError('No consulting category types found')

    return jsonify({'success': True, 'data': categories}), 200


@data_bp.route('/admin/change_user_group', methods=['POST'])
@handle_api_errors(logger_name='auth')
def change_user_group():
    """Change a user's group (admin only)"""
    api_key = request.headers.get('Authorization')

    if not api_key:
        raise UnauthorizedError('API key is missing')

    # Use UserService for authentication
    is_valid, admin_user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        raise UnauthorizedError(error_msg)

    data = request.get_json()
    username = data.get('username')
    new_group_name = data.get('new_group')

    if not username or not new_group_name:
        raise ValidationError('Username and new group are required')

    # Use UserService to change user group
    success, error_msg = UserService.change_user_group(username, new_group_name, admin_user)

    if not success:
        # Determine appropriate status code
        if "not found" in error_msg or "does not exist" in error_msg:
            raise NotFoundError(error_msg)
        elif "permission" in error_msg:
            raise UnauthorizedError(error_msg)
        else:
            raise ValidationError(error_msg)

    return jsonify({'success': True, 'message': f"User '{username}' has been moved to group '{new_group_name}'"}), 200


@data_bp.route('/users/check/<username>', methods=['GET'])
@handle_api_errors(logger_name='auth')
def check_user_exists(username):
    """Check if a user exists"""
    api_key = request.headers.get('Authorization')
    if not api_key:
        raise UnauthorizedError('API key is missing')

    # Use UserService for authentication
    is_valid, requesting_user, error_msg = UserService.validate_api_key(api_key)
    if not is_valid:
        raise UnauthorizedError(error_msg)

    # Use UserService to check if user exists
    exists = UserService.user_exists(username)
    if exists:
        return jsonify({'success': True, 'exists': True}), 200
    return jsonify({'success': True, 'exists': False}), 404
