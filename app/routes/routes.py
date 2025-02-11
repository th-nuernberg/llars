# routes.py

import logging
from numbers import Number
from pyexpat.errors import messages
from unicodedata import category

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash
from . import data_blueprint
from . import auth_blueprint
from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating,  UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       FeatureFunctionType, UserFeatureRating, UserMessageRating,
                       UserGroup, UserPrompt, UserPromptShare,
                       ConsultingCategoryType, UserConsultingCategorySelection)
from sqlalchemy import func
from uuid import uuid4
import uuid
from dateutil import parser
from datetime import datetime
import json


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
        return str(uuid_obj) == uuid_to_test
    except ValueError:
        return False


def get_or_create_default_group():
    default_group = UserGroup.query.filter_by(name="Standard").first()
    if not default_group:
        default_group = UserGroup(name="Standard")
        db.session.add(default_group)
        db.session.commit()
    return default_group


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

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    new_user = User(username=username)
    new_user.set_password(password)
    new_user.api_key = api_key

    # Assign user to a group
    if group_name:
        group = UserGroup.query.filter_by(name=group_name).first()
        if not group:
            return jsonify({"error": f"Group '{group_name}' does not exist"}), 400
    else:
        group = get_or_create_default_group()

    new_user.group = group

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "api_key": api_key,
        "group": group.name
    }), 201


@auth_blueprint.route('/health_check', methods=['GET'])
def health_check():
    return jsonify({"message": "Server is running"}), 200


@auth_blueprint.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            additional_claims = {"api_key": user.api_key}
            access_token = create_access_token(identity=username, additional_claims=additional_claims)
            return jsonify({
                "access_token": access_token,
                "username": username
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        logging.exception(e)
        return jsonify({"error": str(e)}), 500


@auth_blueprint.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully"}), 200




@data_blueprint.route('/email_threads', methods=['POST'])
def create_email_thread():
    data = request.get_json()

    # Get and validate function_type from the request payload
    function_type_input = data.get('type', '').lower()
    valid_function_types = {
        '1': 1,
        '2': 2,
        '3': 3,  # Neue Zahl für mail_rating hinzugefügt
        'ranking': 1,
        'rating': 2,
        'mail_rating': 3,  # Neue Bezeichnung für mail_rating hinzugefügt
        'rank': 1,
        'rate': 2,
        'rankings': 1,
        'ratings': 2,
        'mail_ratings': 3  # Neue Bezeichnung für mail_rating im Plural
    }

    function_type_id = valid_function_types.get(function_type_input)
    if not function_type_id:
        return jsonify({"error": "Invalid function type"}), 400

    sender = data.get('sender', 'Alias')

    email_thread = EmailThread.query.filter_by(
        chat_id=data.get('chat_id'),
        institut_id=data.get('institut_id'),
        function_type_id=function_type_id
    ).first()

    if not email_thread:
        email_thread = EmailThread(
            chat_id=data.get('chat_id'),
            institut_id=data.get('institut_id'),
            subject=data.get('subject'),
            sender=sender,
            function_type_id=function_type_id
        )
        db.session.add(email_thread)
        db.session.commit()
    else:
        email_thread.subject = data.get('subject')
        email_thread.sender = sender
        db.session.commit()

    # Funktion zur Reparatur oder Validierung von Timestamps
    def fix_timestamp(timestamp_str):
        try:
            # Versuchen, den Timestamp direkt zu parsen
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Wenn das Format nicht passt, versuchen wir es mit einem flexiblen Parser (z.B. dateutil)
                return parser.parse(timestamp_str)
            except ValueError:
                # Wenn nicht mal das klappt, Timestamp ignorieren oder Standardwert setzen
                return None

    for msg in data.get('messages', []):
        # Repariere den Timestamp
        raw_timestamp = msg.get('timestamp')
        msg_timestamp = fix_timestamp(raw_timestamp)  # Versuchen, den Timestamp zu korrigieren

        if not msg_timestamp:
            # Falls der Timestamp nicht reparierbar ist, überspringen
            continue

        msg_content = msg.get('content')
        generated_by = msg.get('generated_by', 'human')

        # Prüfen, ob es eine Nachricht mit demselben Inhalt und Timestamp gibt
        existing_message = Message.query.filter_by(
            thread_id=email_thread.thread_id,
            timestamp=msg_timestamp,
            content=msg_content
        ).first()

        if not existing_message:
            message = Message(
                thread_id=email_thread.thread_id,
                sender=msg.get('sender'),
                content=msg_content,
                timestamp=msg_timestamp,
                generated_by=generated_by if generated_by else "Human"
            )
            db.session.add(message)

    for model_name, features in data.get('generated_features', {}).items():
        llm = LLM.query.filter_by(name=model_name).first()
        if not llm:
            llm = LLM(name=model_name)
            db.session.add(llm)
            db.session.commit()

        for feature_key, feature_content in features.items():
            feature_type = FeatureType.query.filter_by(name=feature_key).first()
            if not feature_type:
                feature_type = FeatureType(name=feature_key)
                db.session.add(feature_type)
                db.session.commit()

            existing_feature = Feature.query.filter_by(
                thread_id=email_thread.thread_id,
                type_id=feature_type.type_id,
                llm_id=llm.llm_id
            ).first()

            if not existing_feature:
                feature = Feature(
                    thread_id=email_thread.thread_id,
                    type_id=feature_type.type_id,
                    llm_id=llm.llm_id,
                    content=json.dumps(feature_content)
                )
                db.session.add(feature)

    db.session.commit()

    return jsonify({'status': 'success', 'thread_id': email_thread.thread_id}), 201





import csv
from io import StringIO
from flask import Response


@data_blueprint.route('/rankings/csv', methods=['GET'])
def download_rankings_csv():
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Retrieve all user rankings and sort them by FeatureType, Thread ID, and then by Bucket
    rankings = UserFeatureRanking.query.join(Feature).join(EmailThread).order_by(Feature.thread_id, Feature.type_id,
                                                                                 UserFeatureRanking.user_id,
                                                                                 UserFeatureRanking.bucket,
                                                                                 UserFeatureRanking.ranking_content).all()

    # Prepare a dictionary to hold rankings by feature type, thread, and user
    feature_type_rankings = {}

    # Group rankings by thread_id, feature_type, and user
    for ranking in rankings:
        key = (ranking.feature.email_thread.thread_id, ranking.feature_type.name, ranking.user.username)
        if key not in feature_type_rankings:
            feature_type_rankings[key] = {
                'Gut': [],
                'Mittel': [],
                'Schlecht': []
            }
        feature_type_rankings[key][ranking.bucket].append(ranking)

    # Create a string buffer to write the CSV data
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Write CSV header
    csv_writer.writerow([
        'Thread ID', 'Feature Type', 'User', 'Complete Feature Ranking', 'Bucket', 'Bucket Position', 'Feature ID',
        'Chat ID', 'Institut ID', 'LLM Name'
    ])

    # Iterate over each feature type, thread, and user to generate the complete ranking
    for (thread_id, feature_type_name, username), bucket_rankings in feature_type_rankings.items():
        complete_ranking_position = 1

        # Go through the buckets in order
        for bucket in ['Gut', 'Mittel', 'Schlecht']:
            # Sort the features within the bucket by their ranking_content
            bucket_rankings[bucket].sort(key=lambda x: x.ranking_content)

            # Assign a complete ranking and bucket position within the thread, feature type, and user
            for bucket_position, ranking in enumerate(bucket_rankings[bucket], start=1):
                csv_writer.writerow([
                    thread_id,  # The Thread ID
                    feature_type_name,  # The type of the feature (e.g., situation_summary)
                    username,  # The user who ranked the feature
                    complete_ranking_position,
                    # The complete ranking across all buckets for this thread, feature type, and user
                    bucket,  # The bucket the feature belongs to
                    bucket_position,  # Position within the bucket
                    ranking.feature_id,  # The ID of the feature
                    ranking.feature.email_thread.chat_id,  # The chat ID associated with the thread
                    ranking.feature.email_thread.institut_id,  # The institution ID
                    ranking.llm.name  # The LLM that generated the feature
                ])
                complete_ranking_position += 1

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
    # authorization
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    consulting_categories_types = ConsultingCategoryType.query.all()

    if not consulting_categories_types:
        return jsonify({'error': 'No consulting category types found'}), 401

    response = []
    for consulting_category_type in consulting_categories_types:
        response.append({
            "id": consulting_category_type.id,
            "name": consulting_category_type.name,
            "description": consulting_category_type.description,
        })
    return jsonify({'consulting_category_types': response}), 200




@data_blueprint.route('/admin/change_user_group', methods=['POST'])
def change_user_group():
    api_key = request.headers.get('Authorization')

    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    # Verifiziere den Admin-User
    admin_user = User.query.filter_by(api_key=api_key).first()
    if not admin_user:
        return jsonify({'error': 'Invalid API key'}), 401

    if admin_user.group.name != 'Admin':
        return jsonify({'error': 'You do not have permission to change user groups'}), 403

    data = request.get_json()
    username = data.get('username')
    new_group_name = data.get('new_group')

    if not username or not new_group_name:
        return jsonify({'error': 'Username and new group are required'}), 400

    # Finde den User
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Finde die neue Gruppe
    new_group = UserGroup.query.filter_by(name=new_group_name).first()
    if not new_group:
        return jsonify({'error': f"Group '{new_group_name}' does not exist"}), 404

    # Update die Gruppe des Benutzers
    user.group = new_group
    db.session.commit()

    return jsonify({'message': f"User '{username}' has been moved to group '{new_group_name}'"}), 200


def get_or_create_admin_group():
    admin_group = UserGroup.query.filter_by(name="Admin").first()
    if not admin_group:
        admin_group = UserGroup(name="Admin")
        db.session.add(admin_group)
        db.session.commit()
    return admin_group


@auth_blueprint.route('/register_admin', methods=['POST'])
def register_admin():
    HARD_CODED_ADMIN_API_KEY = "73525abb-3336-4553-8e54-751c9c1b965c"
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('api_key', str(uuid4()))
    admin_registration_key = data.get('admin_registration_key')

    # Überprüfen, ob der übergebene Registrierungsschlüssel korrekt ist
    if admin_registration_key != HARD_CODED_ADMIN_API_KEY:
        return jsonify({"error": "Unauthorized. Invalid admin registration key."}), 403

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    new_user = User(username=username)
    new_user.set_password(password)
    new_user.api_key = api_key

    # Admin-Gruppe zuweisen
    admin_group = get_or_create_admin_group()
    new_user.group = admin_group

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Admin user registered successfully",
        "api_key": api_key,
        "group": new_user.group.name
    }), 201

from flask_jwt_extended import jwt_required


@data_blueprint.route('/users/check/<username>', methods=['GET'])
def check_user_exists(username):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    requesting_user = User.query.filter_by(api_key=api_key).first()
    if not requesting_user:
        return jsonify({'error': 'Invalid API key'}), 401

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'exists': True}), 200
    return jsonify({'exists': False}), 404


