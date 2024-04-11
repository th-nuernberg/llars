from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash
from db.db import db
from db.tables import User, EmailThread, Message, Feature, FeatureType, LLM
from datetime import datetime
import json

# Authentifizierungs-Blueprint
auth_blueprint = Blueprint('auth', __name__)
data_blueprint = Blueprint('data', __name__)

@auth_blueprint.route('/register', methods=['POST'])
def register():
    # print("register")
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Check if username and password are provided
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    # Create new user
    new_user = User(username=username)
    new_user.set_password(password)

    # Add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_blueprint.route('/health_check', methods=['GET'])
def health_check():
    return jsonify({"message": "Server is running"}), 200

@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        # Create JWT token
        access_token = create_access_token(identity=username)
        # login_user(user=user)
        return jsonify(access_token=access_token, username=username), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@auth_blueprint.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully"}), 200


@data_blueprint.route('/email_threads', methods=['POST'])
def create_email_thread():
    data = request.get_json()

    # Überprüfen, ob der Thread bereits existiert
    email_thread = EmailThread.query.filter_by(
        chat_id=data.get('chat_id'),
        institut_id=data.get('institut_id')
    ).first()

    if not email_thread:
        # Erstellen eines neuen EmailThread-Eintrags, falls nicht vorhanden
        email_thread = EmailThread(
            chat_id=data.get('chat_id'),
            institut_id=data.get('institut_id'),
            subject=data.get('subject')
        )
        db.session.add(email_thread)
        db.session.commit()

    # Hinzufügen von Nachrichten zum EmailThread, falls neu
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

    # Hinzufügen von Features zum EmailThread, falls neu
    for model_name, features in data.get('generated_features', {}).items():
        # Überprüfen, ob das LLM-Modell existiert; falls nicht, erstellen
        llm = LLM.query.filter_by(name=model_name).first()
        if not llm:
            llm = LLM(name=model_name)
            db.session.add(llm)
            db.session.commit()

        for feature_key, feature_value in features.items():
            # Überprüfen, ob der FeatureType existiert; falls nicht, erstellen
            feature_type = FeatureType.query.filter_by(name=feature_key).first()
            if not feature_type:
                feature_type = FeatureType(name=feature_key)
                db.session.add(feature_type)
                db.session.commit()

            # Überprüfen, ob das Feature bereits existiert; falls nicht, hinzufügen
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
    # Einen spezifischen EmailThread anhand seiner ID finden
    email_thread = EmailThread.query.get(thread_id)
    if not email_thread:
        return jsonify({'error': 'Email thread not found'}), 404

    # Datenstruktur für das Frontend vorbereiten
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
    # Alle EmailThreads aus der Datenbank holen
    email_threads = EmailThread.query.all()

    # Eine Liste von Dictionaries vorbereiten, die grundlegende Informationen zu jedem Thread enthalten
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
    data = request.get_json()
    return jsonify(data), 200


def configure_routes(app):
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(data_blueprint, url_prefix='/api')