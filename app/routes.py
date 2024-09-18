from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash
from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating)
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


@auth_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('api_key', str(uuid4()))

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if not api_key or not is_valid_uuid(api_key):
        return jsonify({"error": "Invalid API key"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    new_user = User(username=username)
    new_user.set_password(password)
    new_user.api_key = api_key

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "api_key": api_key}), 201


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
        'ranking': 1,
        'rating': 2,
        'rank': 1,
        'rate': 2,
        'rankings': 1,
        'ratings': 2
    }

    function_type_id = valid_function_types.get(function_type_input)

    if not function_type_id:
        return jsonify({"error": "Invalid function type"}), 400

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
            function_type_id=function_type_id
        )
        db.session.add(email_thread)
        db.session.commit()
    else:
        email_thread.subject = data.get('subject')  # Update subject if email_thread already exists
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

    threads_list = [
        {
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject
        } for thread in email_threads
    ]

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
                    type_id=feature_type_entry.type_id,
                    llm_id=llm_entry.llm_id
                ).first()

                if existing_ranking:
                    # Update the ranking content if it exists
                    existing_ranking.ranking_content = position
                else:
                    # Create a new ranking entry
                    new_ranking = UserFeatureRanking(
                        user_id=user.id,
                        feature_id=feature.feature_id,
                        ranking_content=position,
                        type_id=feature_type_entry.type_id,
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

    rankings = UserFeatureRanking.query.filter_by(user_id=user.id).join(Feature).filter(
        Feature.thread_id == thread_id).all()

    if not rankings:
        return jsonify({'warning': 'No rankings found for the given thread and user', 'rankings': []}), 200

    rankings_data = {}

    for ranking in rankings:
        feature_type_name = ranking.feature_type.name
        if feature_type_name not in rankings_data:
            rankings_data[feature_type_name] = []

        rankings_data[feature_type_name].append({
            'model_name': ranking.llm.name,
            'content': ranking.feature.content,
            'position': int(ranking.ranking_content)
        })

    formatted_rankings = [{'type': key, 'details': sorted(content, key=lambda x: x['position'])} for key, content in
                          rankings_data.items()]

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

    # Retrieve all user rankings
    rankings = UserFeatureRanking.query.all()

    # Create a string buffer to write the CSV data
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Write CSV header
    csv_writer.writerow(['User', 'Feature ID', 'LLM Name', 'Feature Type', 'Ranking Position'])

    # Write data rows
    for ranking in rankings:
        user_name = ranking.user.username
        llm_name = ranking.llm.name
        feature_type_name = ranking.feature_type.name
        ranking_position = ranking.ranking_content

        csv_writer.writerow([user_name, ranking.feature_id, llm_name, feature_type_name, ranking_position])

    # Get the CSV content from the buffer
    csv_content = csv_buffer.getvalue()
    csv_buffer.close()

    # Create a response with the CSV content
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=rankings.csv'}
    )


def configure_routes(app):
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(data_blueprint, url_prefix='/api')
