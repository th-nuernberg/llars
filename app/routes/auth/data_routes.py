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


@data_bp.route('/email_threads', methods=['POST'])
def create_email_thread():
    """Create or update an email thread with messages and features"""
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


@data_bp.route('/rankings/csv', methods=['GET'])
def download_rankings_csv():
    """Download rankings as CSV file"""
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


@data_bp.route('/email_threads/consulting_category_types', methods=['GET'])
def get_consulting_category_types():
    """Get all consulting category types"""
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


@data_bp.route('/admin/change_user_group', methods=['POST'])
def change_user_group():
    """Change a user's group (admin only)"""
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


@data_bp.route('/users/check/<username>', methods=['GET'])
def check_user_exists(username):
    """Check if a user exists"""
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
