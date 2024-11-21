import logging
from pyexpat.errors import messages

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash
from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating,
                       UserGroup, UserPrompt, UserPromptShare)
from sqlalchemy import func
from uuid import uuid4
import uuid
from datetime import datetime
import json

auth_blueprint = Blueprint('auth', __name__)
data_blueprint = Blueprint('data', __name__)


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

    # Get the sender, if not provided use an alias
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
            sender=sender,  # Store the sender
            function_type_id=function_type_id
        )
        db.session.add(email_thread)
        db.session.commit()
    else:
        email_thread.subject = data.get('subject')  # Update subject if email_thread already exists
        email_thread.sender = sender  # Update the sender if email_thread already exists
        db.session.commit()

    existing_message_ids = {msg.message_id for msg in email_thread.messages}
    for msg in data.get('messages', []):
        if msg.get('message_id') not in existing_message_ids:
            message = Message(
                thread_id=email_thread.thread_id,
                sender=msg.get('sender'),
                content=msg.get('content'),
                timestamp=datetime.strptime(msg.get('timestamp'), '%Y-%m-%d %H:%M:%S')
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

            # Store the entire feature content as JSON in the database
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
                    content=json.dumps(feature_content)  # Store as JSON string
                )
                db.session.add(feature)

    db.session.commit()

    return jsonify({'status': 'success', 'thread_id': email_thread.thread_id}), 201


@data_blueprint.route('/email_threads/rankings/<int:thread_id>', methods=['GET'])
def get_email_thread_for_rankings(thread_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    ranking_function_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    email_thread = EmailThread.query.filter_by(thread_id=thread_id,
                                               function_type_id=ranking_function_type.function_type_id).first()
    if not email_thread:
        return jsonify({'error': 'Email thread not found or not for ranking'}), 404

    # Überprüfe, ob der Benutzer bereits Rankings für diesen Thread hat
    user_rankings = UserFeatureRanking.query.filter_by(user_id=user.id).join(Feature).filter(
        Feature.thread_id == email_thread.thread_id
    ).first()

    ranked = True if user_rankings else False

    thread_data = {
        'chat_id': email_thread.chat_id,
        'institut_id': email_thread.institut_id,
        'subject': email_thread.subject,
        'ranked': ranked,  # Füge den Ranked-Status hinzu
        'messages': [
            {
                'message_id': msg.message_id,
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            } for msg in email_thread.messages
        ],
        'features': [
            {
                'model_name': feature.llm.name,
                'type': feature.feature_type.name,
                'content': feature.content,
                'feature_id': feature.feature_id
            } for feature in email_thread.features
        ]
    }

    return jsonify(thread_data), 200


@data_blueprint.route('/email_threads/ratings/<int:thread_id>', methods=['GET'])
def get_email_thread_for_ratings(thread_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    rating_function_type = FeatureFunctionType.query.filter_by(name='rating').first()
    if not rating_function_type:
        return jsonify({'error': 'Rating function type not found'}), 404

    email_thread = EmailThread.query.filter_by(thread_id=thread_id,
                                               function_type_id=rating_function_type.function_type_id).first()
    if not email_thread:
        return jsonify({'error': 'Email thread not found or not for rating'}), 404

    thread_data = {
        'chat_id': email_thread.chat_id,
        'institut_id': email_thread.institut_id,
        'subject': email_thread.subject,
        'messages': [
            {
                'message_id': msg.message_id,
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            } for msg in email_thread.messages
        ],
        'features': [
            {
                'model_name': feature.llm.name,
                'type': feature.feature_type.name,
                'content': feature.content,
                'feature_id': feature.feature_id  # Include the feature_id here
            } for feature in email_thread.features
        ]
    }

    return jsonify(thread_data), 200


@data_blueprint.route('/email_threads/ratings/<int:thread_id>/<int:feature_id>', methods=['GET'])
def get_feature_and_messages(thread_id, feature_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Get the feature by thread_id and feature_id
    feature = Feature.query.filter_by(thread_id=thread_id, feature_id=feature_id).first()
    if not feature:
        return jsonify({'error': 'Feature not found'}), 404

    # Get the messages for the thread_id
    messages = Message.query.filter_by(thread_id=thread_id).all()
    if not messages:
        return jsonify({'error': 'No messages found for the given thread_id'}), 404

    feature_data = {
        'model_name': feature.llm.name,
        'type': feature.feature_type.name,
        'content': feature.content,
        'feature_id': feature.feature_id
    }

    messages_data = [
        {
            'message_id': msg.message_id,
            'sender': msg.sender,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat()
        } for msg in messages
    ]

    response_data = {
        'feature': feature_data,
        'messages': messages_data
    }

    return jsonify(response_data), 200


@data_blueprint.route('/email_threads/rankings', methods=['GET'])
def list_email_threads_for_rankings():
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    ranking_function_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    email_threads = EmailThread.query.filter_by(function_type_id=ranking_function_type.function_type_id).all()

    threads_list = []
    for thread in email_threads:
        # Check if the user has ranked features in this thread
        user_rankings = UserFeatureRanking.query.filter_by(user_id=user.id).join(Feature).filter(
            Feature.thread_id == thread.thread_id
        ).first()

        ranked = True if user_rankings else False

        threads_list.append({
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject,
            'sender': thread.sender,  # Hier wird der Sender hinzugefügt
            'ranked': ranked
        })

    return jsonify(threads_list), 200


@data_blueprint.route('/email_threads/ratings', methods=['GET'])
def list_email_threads_for_ratings():
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    rating_function_type = FeatureFunctionType.query.filter_by(name='rating').first()
    if not rating_function_type:
        return jsonify({'error': 'Rating function type not found'}), 404

    email_threads = EmailThread.query.filter_by(function_type_id=rating_function_type.function_type_id).all()

    threads_list = [
        {
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject
        } for thread in email_threads
    ]

    return jsonify(threads_list), 200


@data_blueprint.route('/save_ranking/<int:thread_id>', methods=['POST'])
def save_ranking(thread_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.get_json()

    for feature_type in data:
        type_name = feature_type['type']
        for detail in feature_type['details']:
            model_name = detail['model_name']
            content = detail['content']
            position = detail['position']
            bucket = detail['bucket']  # Bucket Information

            # Find the FeatureType ID
            feature_type_entry = FeatureType.query.filter_by(name=type_name).first()
            if not feature_type_entry:
                return jsonify({'error': f'Feature type {type_name} not found'}), 404

            # Find the LLM ID
            llm_entry = LLM.query.filter_by(name=model_name).first()
            if not llm_entry:
                return jsonify({'error': f'LLM {model_name} not found'}), 404

            # Find the feature_id for the given thread_id, feature_type_id, and llm_id
            feature = Feature.query.filter_by(
                thread_id=thread_id,
                type_id=feature_type_entry.type_id,
                llm_id=llm_entry.llm_id,
                content=content
            ).first()

            if feature:
                # Check if the ranking already exists
                existing_ranking = UserFeatureRanking.query.filter_by(
                    user_id=user.id,
                    feature_id=feature.feature_id,
                    type_id=feature_type_entry.type_id,  # Stelle sicher, dass der Typ jetzt auch gespeichert wird
                    llm_id=llm_entry.llm_id
                ).first()

                if existing_ranking:
                    # Update the ranking content and bucket if it exists
                    existing_ranking.ranking_content = position
                    existing_ranking.bucket = bucket
                else:
                    # Create a new ranking entry with the bucket information
                    new_ranking = UserFeatureRanking(
                        user_id=user.id,
                        feature_id=feature.feature_id,
                        ranking_content=position,
                        bucket=bucket,  # Save the bucket
                        type_id=feature_type_entry.type_id,  # Speichere den Feature-Typ
                        llm_id=llm_entry.llm_id
                    )
                    db.session.add(new_ranking)

    db.session.commit()

    return jsonify({'status': 'Ranking saved successfully'}), 201


@data_blueprint.route('/email_threads/<int:thread_id>/current_ranking', methods=['GET'])
def get_current_ranking(thread_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Holen Sie alle Rankings für den gegebenen Thread und Benutzer
    rankings = UserFeatureRanking.query.filter_by(user_id=user.id).join(Feature).filter(
        Feature.thread_id == thread_id).all()

    # Holen Sie alle Feature-Typen aus der Datenbank
    feature_types = FeatureType.query.all()

    # Dynamisch die Datenstruktur für die Rankings basierend auf den Feature-Typen aufbauen
    rankings_data = {feature_type.name: {"goodList": [], "averageList": [], "badList": [], "neutralList": []} for feature_type in feature_types}

    # Iteriere durch die Rankings und sortiere sie in die entsprechenden Buckets
    for ranking in rankings:
        feature_data = {
            'model_name': ranking.llm.name,
            'content': ranking.feature.content,
            'feature_id': ranking.feature_id,
            'position': int(ranking.ranking_content),
            'minimized': True  # Beispielwert, du kannst dies nach Bedarf ändern
        }

        # Bestimme den Feature-Typ (dynamisch basierend auf dem Ranking)
        feature_type = ranking.feature_type.name

        # Ordne die Feature-Daten dem richtigen Bucket und Typ zu
        if feature_type in rankings_data:
            if ranking.bucket == 'Gut':
                rankings_data[feature_type]['goodList'].append(feature_data)
            elif ranking.bucket == 'Mittel':
                rankings_data[feature_type]['averageList'].append(feature_data)
            elif ranking.bucket == 'Schlecht':
                rankings_data[feature_type]['badList'].append(feature_data)
            else:
                rankings_data[feature_type]['neutralList'].append(feature_data)

    # Holen Sie alle Features für den Thread, die noch nicht vom Benutzer gerankt wurden
    ranked_feature_ids = [ranking.feature_id for ranking in rankings]
    all_features = Feature.query.filter_by(thread_id=thread_id).all()

    for feature in all_features:
        if feature.feature_id not in ranked_feature_ids:
            feature_data = {
                'model_name': feature.llm.name,
                'content': feature.content,
                'feature_id': feature.feature_id,
                'position': None,  # Ungerankte Features haben keine Position
                'minimized': True  # Beispielwert, du kannst dies nach Bedarf ändern
            }

            # Ordne das Feature dem neutralen Bucket des entsprechenden Feature-Typs zu
            feature_type = feature.feature_type.name
            if feature_type in rankings_data:
                rankings_data[feature_type]['neutralList'].append(feature_data)

    # Sortiere die Listen innerhalb der Buckets nach der Position
    for feature_type, data in rankings_data.items():
        data['goodList'] = sorted(data['goodList'], key=lambda x: x['position'] if x['position'] is not None else float('inf'))
        data['averageList'] = sorted(data['averageList'], key=lambda x: x['position'] if x['position'] is not None else float('inf'))
        data['badList'] = sorted(data['badList'], key=lambda x: x['position'] if x['position'] is not None else float('inf'))
        data['neutralList'] = sorted(data['neutralList'], key=lambda x: x['position'] if x['position'] is not None else float('inf'))

    # Die finale Ausgabe im dynamischen Format
    formatted_rankings = [
        {
            "type": feature_type,
            "goodList": data["goodList"],
            "averageList": data["averageList"],
            "badList": data["badList"],
            "neutralList": data["neutralList"]
        }
        for feature_type, data in rankings_data.items()
    ]

    return jsonify(formatted_rankings), 200


@data_blueprint.route('/feature_type_mapping', methods=['GET'])
def get_feature_type_mapping():
    feature_types = FeatureType.query.all()

    if not feature_types:
        return jsonify({'error': 'No feature types found'}), 404

    mapping = {
        'by_name': {ft.name: ft.type_id for ft in feature_types},
        'by_id': {ft.type_id: ft.name for ft in feature_types}
    }

    return jsonify(mapping), 200

@data_blueprint.route('/feature_type_mapping/<identifier>', methods=['GET'])
def get_feature_type(identifier):
    if identifier.isdigit():
        # Wenn der Identifier eine Zahl ist, gehe davon aus, dass es eine FeatureType-ID ist
        feature_type = FeatureType.query.filter_by(type_id=int(identifier)).first()
        if not feature_type:
            return jsonify({'error': f'Feature type ID {identifier} not found'}), 404
        return jsonify({'name': feature_type.name}), 200
    else:
        # Andernfalls gehe davon aus, dass es sich um einen FeatureType-Namen handelt
        feature_type = FeatureType.query.filter_by(name=identifier).first()
        if not feature_type:
            return jsonify({'error': f'Feature type name {identifier} not found'}), 404
        return jsonify({'type_id': feature_type.type_id}), 200

@data_blueprint.route('/save_rating/<int:thread_id>/<int:feature_id>', methods=['POST'])
def save_rating(thread_id, feature_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.get_json()
    rating_content = data.get('rating_content')
    edited_feature = data.get('edited_feature')

    if rating_content is None or edited_feature is None:
        return jsonify({'error': 'Rating content and edited feature are required'}), 400

    # Find or create the feature rating
    feature_rating = UserFeatureRating.query.filter_by(user_id=user.id, feature_id=feature_id).first()

    if feature_rating:
        feature_rating.rating_content = rating_content
        feature_rating.edited_feature = edited_feature
    else:
        new_rating = UserFeatureRating(
            user_id=user.id,
            feature_id=feature_id,
            rating_content=rating_content,
            edited_feature=edited_feature
        )
        db.session.add(new_rating)

    db.session.commit()

    return jsonify({'status': 'Rating saved successfully'}), 201


@data_blueprint.route('/get_rating/<int:thread_id>/<int:feature_id>', methods=['GET'])
def get_rating(thread_id, feature_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    feature_rating = UserFeatureRating.query.filter_by(user_id=user.id, feature_id=feature_id).first()

    if not feature_rating:
        return jsonify({'error': 'Rating not found'}), 404

    rating_data = {
        'rating_content': feature_rating.rating_content,
        'edited_feature': feature_rating.edited_feature
    }

    return jsonify(rating_data), 200

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


@data_blueprint.route('/admin/user_ranking_stats', methods=['GET'])
def get_user_ranking_stats():
    api_key = request.headers.get('Authorization')

    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    admin_user = User.query.filter_by(api_key=api_key).first()
    if not admin_user:
        return jsonify({'error': 'Invalid API key'}), 401

    user_stats = []

    # Hole die Anzahl der gesamten Email Threads mit function_type_id = 1
    total_threads = db.session.query(EmailThread).filter_by(function_type_id=1).count()

    for user in User.query.all():
        ranked_threads_list = []
        unranked_threads_list = []
        total_ranked_threads = 0

        # Iteriere nur über die Email Threads mit function_type_id = 1
        for thread in EmailThread.query.filter_by(function_type_id=1).all():
            # Zähle alle Features in diesem Thread
            total_features_in_thread = db.session.query(Feature).filter_by(thread_id=thread.thread_id).count()

            # Zähle die Anzahl der vom Benutzer gerankten Features in diesem Thread
            ranked_features_count = db.session.query(UserFeatureRanking).join(Feature).filter(
                UserFeatureRanking.user_id == user.id,
                Feature.thread_id == thread.thread_id
            ).count()

            if ranked_features_count == total_features_in_thread and total_features_in_thread > 0:
                # Wenn alle Features eines Threads gerankt wurden, zähle den Thread als vollständig gerankt
                total_ranked_threads += 1
                ranked_threads_list.append({
                    'thread_id': thread.thread_id,
                    'chat_id': thread.chat_id,
                    'institut_id': thread.institut_id,
                    'subject': thread.subject,
                    'ranked_features_count': ranked_features_count,
                    'total_features_in_thread': total_features_in_thread
                })
            else:
                # Wenn der Benutzer diesen Thread noch nicht vollständig gerankt hat
                unranked_threads_list.append({
                    'thread_id': thread.thread_id,
                    'chat_id': thread.chat_id,
                    'institut_id': thread.institut_id,
                    'subject': thread.subject,
                    'ranked_features_count': ranked_features_count,
                    'total_features_in_thread': total_features_in_thread
                })

        # Füge die Statistiken für diesen Benutzer hinzu
        user_stats.append({
            'username': user.username,
            'ranked_threads_count': total_ranked_threads,  # Anzahl der vollständig gerankten Threads
            'total_threads': total_threads,  # Gesamtzahl der relevanten Threads (mit function_type_id = 1)
            'ranked_threads': ranked_threads_list,  # Liste der vollständig gerankten Threads
            'unranked_threads': unranked_threads_list  # Liste der unvollständig gerankten/unbearbeiteten Threads
        })

    return jsonify(user_stats), 200


@data_blueprint.route('/email_threads/feature_ranking_list', methods=['GET'])
def list_ranking_threads():
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Hole alle Threads mit function_type_id = 1 (Ranking)
    ranking_function_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    # Nur Ranking-Threads zurückgeben
    email_threads = EmailThread.query.filter_by(function_type_id=ranking_function_type.function_type_id).all()

    threads_list = [
        {
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject
        } for thread in email_threads
    ]

    return jsonify(threads_list), 200

@data_blueprint.route('/email_threads/mailhistory_ratings', methods=['GET'])
def list_email_threads_for_mail_ratings(thread_id=None):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    mail_rating_function_type = FeatureFunctionType.query.filter_by(name='mail_rating').first()
    if not mail_rating_function_type:
        return jsonify({'error': 'Mail Rating function type not found'}), 404


    # Abrufen aller E-Mail-Threads für die Bewertungen
    email_threads = EmailThread.query.filter_by(function_type_id=mail_rating_function_type.function_type_id).all()

    threads_list = []
    for thread in email_threads:
        mail_rating = UserMailHistoryRating.query.filter_by(user_id=user.id, thread_id=thread.thread_id).order_by(
            UserMailHistoryRating.timestamp.desc()).first()
        rating_status = "Not Rated"

        if mail_rating:
            if (mail_rating.coherence_rating is  None and
                    mail_rating.quality_rating is None and
                    mail_rating.overall_rating  is None and
                    mail_rating.plausibility_rating is None):
                rating_status = "Not Rated" # In case all likert scales get unmarked
            elif (mail_rating.coherence_rating is not None and
                    mail_rating.quality_rating is not None and
                    mail_rating.overall_rating is not None and
                    mail_rating.plausibility_rating is not None):
                rating_status = "Rated"
            else:
                rating_status = "Partly Rated"

        threads_list.append({
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject,
            'sender': thread.sender,
            'rating_status': rating_status,
        })

    return jsonify(threads_list), 200



@data_blueprint.route('/email_threads/generations/<int:thread_id>', methods=['GET'])
def get_email_thread_details(thread_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Hole den E-Mail-Thread basierend auf der thread_id
    email_thread = EmailThread.query.filter_by(thread_id=thread_id).first()
    if not email_thread:
        return jsonify({'error': 'Email thread not found'}), 404

    # Hole alle Nachrichten in diesem E-Mail-Thread
    messages = Message.query.filter_by(thread_id=email_thread.thread_id).all()

    if not messages:
        return jsonify({'error': 'No messages found for this thread'}), 404

    # Erstelle eine Liste von Nachrichten, die zurückgegeben werden soll
    messages_data = [
        {
            'message_id': msg.message_id,
            'sender': msg.sender,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat()  # Konvertiere das Datum in ISO-Format
        } for msg in messages
    ]

    return jsonify({'messages': messages_data}), 200


# Get the user ratings for the messages of a thread
@data_blueprint.route('/email_threads/message_ratings/<int:thread_id>', methods=['GET'])
def get_email_thread_message_ratings(thread_id):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Load Ratings of messages
    ## Unterabfrage, um den neuesten Timestamp pro message_id zu ermitteln
    subquery = db.session.query(
        UserMessageRating.message_id,
        func.max(UserMessageRating.timestamp).label('latest_timestamp')
    ).filter_by(
        user_id=user.id,
        thread_id=thread_id
    ).group_by(
        UserMessageRating.message_id
    ).subquery()

    ## Hauptabfrage, die den entsprechenden Datensatz für jede message_id mit dem neuesten Timestamp auswählt
    msg_ratings = db.session.query(UserMessageRating).join(
        subquery,
        (UserMessageRating.message_id == subquery.c.message_id) &
        (UserMessageRating.timestamp == subquery.c.latest_timestamp)
    ).filter(
        UserMessageRating.user_id == user.id,
        UserMessageRating.thread_id == thread_id
    ).all()

    rating_list = [
        {
            'message_id': msg_rating.message_id,
            'rating': msg_rating.rating,
        } for msg_rating in msg_ratings
    ]

    return jsonify(rating_list), 200


# Route to save the ratings and feedback of the whole
@data_blueprint.route('/email_threads/save_mailhistory_rating/<int:thread_id>', methods=['POST'])
def save_mail_rating(thread_id):
    # Authorization
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.get_json()

    # Values sent from the client
    plausibility_rating = data.get('plausibility_rating')
    coherence_rating = data.get('coherence_rating')
    quality_rating = data.get('quality_rating')
    overall_rating = data.get('overall_rating')
    feedback = data.get('feedback', '')

    # retrieve most recent mail history rating
    existing_rating = UserMailHistoryRating.query.filter_by(user_id=user.id, thread_id=thread_id).order_by(
        UserMailHistoryRating.timestamp.desc()).first()

    # check if any likert scale got rated or a feedback was written.
    if plausibility_rating is None and coherence_rating is None and quality_rating is None and overall_rating is None and feedback is None:
        # if not, check if a existing rating got "deleted". If yes, save values of new version as null in the db, else skip
        if not existing_rating: # skip because no rating of the history happened
            return jsonify({'status': 'Message ratings saved successfully'}), 201

    # if a rating already exists, check if changes occurred
    if existing_rating:
        if(existing_rating.plausibility_rating == plausibility_rating
            and existing_rating.coherence_rating == coherence_rating
            and existing_rating.quality_rating == quality_rating
            and existing_rating.overall_rating == overall_rating
            and existing_rating.feedback == feedback):
            return jsonify({'status': 'Message ratings saved successfully'}), 201

    # Changes happened, or it is the first rating
    # Create a new mail rating with feedback and save it into the db with current timestamp
    new_mail_rating = UserMailHistoryRating(
        user_id=user.id,
        thread_id=thread_id,
        plausibility_rating=plausibility_rating,
        coherence_rating=coherence_rating,
        quality_rating=quality_rating,
        overall_rating=overall_rating,
        feedback=feedback
    )
    db.session.add(new_mail_rating)

    db.session.commit()

    return jsonify({'status': 'Mail rating and feedback saved successfully'}), 201


# Route for saving the rating of each message (up or down) from the generated mail historys
@data_blueprint.route('/email_threads/save_message_ratings/<int:thread_id>', methods=['POST'])
def save_message_ratings(thread_id):
    # authorization
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # retrieve data send from user
    data = request.get_json()
    message_ratings = data.get('message_ratings', [])

    # Loop through all message ratings send from user
    for rating_data in message_ratings:
        message_id = rating_data.get('message_id')
        rating = rating_data.get('rating')

        # check if the most recent message rating of this user is equal to the one send (avoiding duplicates in the db)
        existing_message_rating = (
            UserMessageRating.query
            .filter_by(user_id=user.id, thread_id=thread_id, message_id=message_id)
            .order_by(UserMessageRating.timestamp.desc())
            .first()
        )

        if existing_message_rating:
            # check if the new message rating is a duplicate of the most recent in db. If yes skip this message (applies for null values too)
            if existing_message_rating.rating == rating:
                continue
        elif rating is None: # if message didnt get ratet and no rating for this message existed in the db --> skip
            continue

        # either first rating for the message, or a change occured.
        # create and safe new entry into the db with current time stamp
        new_message_rating = UserMessageRating(
            user_id=user.id,
            thread_id=thread_id,
            message_id=message_id,
            rating=rating
        )
        db.session.add(new_message_rating)

    # commit all changes to the db
    db.session.commit()
    return jsonify({'status': 'Message ratings saved successfully'}), 201


# get the most recent mail history ratings of the user
@data_blueprint.route('/email_threads/mailhistory_ratings/<int:thread_id>', methods=['GET'])
def get_mail_rating(thread_id):
    # authorization
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # retrieve the most recent mail history(thread) rating of user
    mail_rating = UserMailHistoryRating.query.filter_by(user_id=user.id, thread_id=thread_id).order_by(UserMailHistoryRating.timestamp.desc()).first()


    # prepare data for json format (if no rating found use null values)
    rating_data = {
        'rating': {
                'plausibility_rating': mail_rating.plausibility_rating if mail_rating else None,
                'coherence_rating': mail_rating.coherence_rating if mail_rating else None,
                'quality_rating': mail_rating.quality_rating if mail_rating else None,
                'overall_rating': mail_rating.overall_rating if mail_rating else None,
                'feedback': mail_rating.feedback if mail_rating else None
            }
    }
    return jsonify(rating_data), 200


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

@data_blueprint.route('/prompts', methods=['POST'])
def save_user_prompt():
    """
    Route zum Speichern eines neuen Prompts für den angemeldeten Benutzer.
    """
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.get_json()
    prompt_name = data.get('name')
    prompt_content = data.get('content')

    if not prompt_name or not prompt_content:
        return jsonify({'error': 'Prompt name and content are required'}), 400

    # Prüfen, ob ein Prompt mit dem gleichen Namen bereits existiert
    existing_prompt = UserPrompt.query.filter_by(user_id=user.id, name=prompt_name).first()
    if existing_prompt:
        return jsonify({'error': f'A prompt with the name "{prompt_name}" already exists'}), 409

    # Neuen Prompt speichern
    new_prompt = UserPrompt(
        user_id=user.id,
        name=prompt_name,
        content=prompt_content
    )
    db.session.add(new_prompt)
    db.session.commit()

    return jsonify({
        'message': 'Prompt saved successfully',
        'prompt': {
            'id': new_prompt.prompt_id,
            'name': new_prompt.name,
            'content': new_prompt.content,
            'created_at': new_prompt.created_at.isoformat(),
            'updated_at': new_prompt.updated_at.isoformat()
        }
    }), 201


@data_blueprint.route('/prompts', methods=['GET'])
def get_user_prompts():
    """
    Route zum Abrufen aller Prompts des angemeldeten Benutzers.
    """
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Alle Prompts des Benutzers abrufen inkl. Sharing-Informationen
    user_prompts = UserPrompt.query.filter_by(user_id=user.id).all()

    # Rückgabe der Prompts als JSON mit Sharing-Informationen
    prompts_data = []
    for prompt in user_prompts:
        # Sharing-Informationen abrufen
        shared_users = db.session.query(User.username) \
            .join(UserPromptShare, User.id == UserPromptShare.shared_with_user_id) \
            .filter(UserPromptShare.prompt_id == prompt.prompt_id) \
            .all()

        shared_with = [user[0] for user in shared_users]

        prompt_data = {
            'id': prompt.prompt_id,
            'name': prompt.name,
            'content': prompt.content,
            'created_at': prompt.created_at.isoformat(),
            'updated_at': prompt.updated_at.isoformat(),
            'shared_with': shared_with  # Liste der Benutzernamen
        }
        prompts_data.append(prompt_data)

    return jsonify({'prompts': prompts_data}), 200

@data_blueprint.route('/prompts/<int:prompt_id>', methods=['GET'])
def get_user_prompt(prompt_id):
    """
    Route zum Abrufen eines einzelnen Prompts für den Benutzer.
    Berücksichtigt sowohl eigene als auch geteilte Prompts.
    """
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Prompt abrufen (eigene und geteilte)
    prompt = UserPrompt.query.filter(
        (UserPrompt.prompt_id == prompt_id) &
        ((UserPrompt.user_id == user.id) |  # Eigene Prompts
         (UserPrompt.prompt_id.in_(  # Geteilte Prompts
             db.session.query(UserPromptShare.prompt_id)
             .filter_by(shared_with_user_id=user.id)
         )))
    ).first()

    if not prompt:
        return jsonify({'error': 'Prompt not found or you do not have permission to view it'}), 404

    # Überprüfen, ob es ein geteiltes Prompt ist
    is_shared = prompt.user_id != user.id

    # Besitzer-Informationen hinzufügen
    owner = prompt.user.username

    # Liste der Benutzer mit denen das Prompt geteilt wurde abrufen
    # (nur wenn der aktuelle Benutzer der Besitzer ist)
    shared_with = []
    if prompt.user_id == user.id:
        shared_users = db.session.query(User.username)\
            .join(UserPromptShare, User.id == UserPromptShare.shared_with_user_id)\
            .filter(UserPromptShare.prompt_id == prompt_id)\
            .all()
        shared_with = [user[0] for user in shared_users]

    return jsonify({
        'id': prompt.prompt_id,
        'name': prompt.name,
        'content': prompt.content,
        'created_at': prompt.created_at.isoformat(),
        'updated_at': prompt.updated_at.isoformat(),
        'is_shared': is_shared,
        'owner': owner,
        'shared_with': shared_with  # Liste der Benutzernamen
    }), 200

@data_blueprint.route('/prompts/<int:prompt_id>', methods=['PUT'])
def update_user_prompt(prompt_id):
    """
    Route zum Aktualisieren eines Prompts für den Benutzer.
    """
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Prompt abrufen und prüfen, ob es dem Benutzer gehört
    prompt = UserPrompt.query.filter_by(prompt_id=prompt_id, user_id=user.id).first()
    if not prompt:
        return jsonify({'error': 'Prompt not found or you do not have permission to edit it'}), 404

    data = request.get_json()
    content = data.get('content')

    if not isinstance(content, dict):
        return jsonify({'error': 'Content must be a valid JSON object'}), 400

    # Prompt-Inhalt aktualisieren
    prompt.content = content
    prompt.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Prompt updated successfully',
        'prompt': {
            'id': prompt.prompt_id,
            'name': prompt.name,
            'content': prompt.content,
            'updated_at': prompt.updated_at.isoformat(),
        }
    }), 200


@data_blueprint.route('/prompts/<int:prompt_id>/share', methods=['POST'])
def share_prompt(prompt_id):
    """
    Route zum Freigeben eines Prompts für einen anderen Benutzer.
    """
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.get_json()
    shared_with_username = data.get('shared_with')

    if not shared_with_username:
        return jsonify({'error': 'Username to share with is required'}), 400

    # Prompt abrufen und prüfen, ob es dem Benutzer gehört
    prompt = UserPrompt.query.filter_by(prompt_id=prompt_id, user_id=user.id).first()
    if not prompt:
        return jsonify({'error': 'Prompt not found or you do not have permission to share it'}), 404

    # Zielbenutzer abrufen
    shared_with_user = User.query.filter_by(username=shared_with_username).first()
    if not shared_with_user:
        return jsonify({'error': f'User "{shared_with_username}" not found'}), 404

    # Prüfen, ob das Prompt bereits freigegeben wurde
    existing_share = UserPromptShare.query.filter_by(prompt_id=prompt_id, shared_with_user_id=shared_with_user.id).first()
    if existing_share:
        return jsonify({'error': f'Prompt is already shared with "{shared_with_username}"'}), 409

    # Freigabe erstellen
    new_share = UserPromptShare(prompt_id=prompt_id, shared_with_user_id=shared_with_user.id)
    db.session.add(new_share)
    db.session.commit()

    return jsonify({'message': f'Prompt shared with "{shared_with_username}" successfully'}), 201


@data_blueprint.route('/prompts/shared', methods=['GET'])
def get_shared_prompts():
    """
    Route zum Abrufen aller für den Benutzer freigegebenen Prompts.
    """
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Freigegebene Prompts mit Sharing-Zeitstempel abrufen
    shared_prompts = db.session.query(
        UserPrompt, UserPromptShare.created_at.label('shared_at')
    ).join(
        UserPromptShare, UserPrompt.prompt_id == UserPromptShare.prompt_id
    ).filter(
        UserPromptShare.shared_with_user_id == user.id
    ).all()

    # Freigegebene Prompts formatieren
    prompts_data = [
        {
            'id': prompt.prompt_id,
            'name': prompt.name,
            'content': prompt.content,
            'owner': prompt.user.username,
            'shared_at': shared_at.isoformat() if shared_at else None
        }
        for prompt, shared_at in shared_prompts
    ]

    return jsonify({'shared_prompts': prompts_data}), 200


@data_blueprint.route('/prompts/<int:prompt_id>/download', methods=['GET'])
def download_prompt_json(prompt_id):
    """
    Route zum Herunterladen eines Prompts als formatierte JSON-Datei.
    """
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Prompt abrufen und prüfen, ob der Benutzer Zugriff hat
    prompt = UserPrompt.query.filter(
        (UserPrompt.prompt_id == prompt_id) &
        ((UserPrompt.user_id == user.id) |
         (UserPrompt.prompt_id.in_(
             db.session.query(UserPromptShare.prompt_id)
             .filter_by(shared_with_user_id=user.id)
         )))
    ).first()

    if not prompt:
        return jsonify({'error': 'Prompt not found or you do not have permission to access it'}), 404

    # Formatierte JSON erstellen
    formatted_content = {}

    if isinstance(prompt.content, dict) and 'blocks' in prompt.content:
        # Sortiere die Blöcke nach ihrer Position
        blocks_sorted = sorted(
            prompt.content['blocks'].items(),
            key=lambda x: x[1].get('position', float('inf'))
        )

        # Erstelle das formatierte Dictionary
        formatted_content = {
            block_name: block_data['content']
            for block_name, block_data in blocks_sorted
        }

    # JSON-Response mit Download-Header
    response = Response(
        json.dumps(formatted_content, indent=4, ensure_ascii=False),
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=prompt_{prompt.name}.json'
        }
    )

    return response


def configure_routes(app):
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(data_blueprint, url_prefix='/api')
