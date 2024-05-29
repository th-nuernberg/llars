from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash
from db.db import db
from db.tables import User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking
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
    email_thread = EmailThread.query.filter_by(
        chat_id=data.get('chat_id'),
        institut_id=data.get('institut_id')
    ).first()

    if not email_thread:
        email_thread = EmailThread(
            chat_id=data.get('chat_id'),
            institut_id=data.get('institut_id'),
            subject=data.get('subject')
        )
        db.session.add(email_thread)
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

        for feature_key, feature_value in features.items():
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
                    value=feature_value
                )
                db.session.add(feature)

    db.session.commit()

    return jsonify({'status': 'success', 'thread_id': email_thread.thread_id}), 201

@data_blueprint.route('/email_threads/<int:thread_id>', methods=['GET'])
def get_email_thread(thread_id):
    email_thread = EmailThread.query.get(thread_id)
    if not email_thread:
        return jsonify({'error': 'Email thread not found'}), 404

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
                'value': feature.value
            } for feature in email_thread.features
        ]
    }

    return jsonify(thread_data), 200

@data_blueprint.route('/email_threads', methods=['GET'])
def list_email_threads():
    email_threads = EmailThread.query.all()

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
            value = detail['value']
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
                value=value
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
                    # Update the ranking value if it exists
                    existing_ranking.ranking_value = position
                else:
                    # Create a new ranking entry
                    new_ranking = UserFeatureRanking(
                        user_id=user.id,
                        feature_id=feature.feature_id,
                        ranking_value=position,
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
            'value': ranking.feature.value,
            'position': int(ranking.ranking_value)
        })

    formatted_rankings = [{'type': key, 'details': sorted(value, key=lambda x: x['position'])} for key, value in
                          rankings_data.items()]

    return jsonify(formatted_rankings), 200


def configure_routes(app):
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(data_blueprint, url_prefix='/api')
