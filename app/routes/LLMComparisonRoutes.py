import random
import json
from pathlib import Path

from flask import request, jsonify

from . import data_blueprint
from db.db import db
from db.tables import (
    User,
    ComparisonSession,
    ComparisonMessage,
    FeatureFunctionType,
    RatingScenarios
)
from .HelperFunctions import get_user_scenarios

BASE_DIR = Path(__file__).parent
PERSONAS_PATH = BASE_DIR / '../static/vikl-personas.json'


def current_user():
    api_key = request.headers.get("Authorization")
    return User.query.filter_by(api_key=api_key).first()


def require_user():
    user = current_user()
    if not user:
        return jsonify({"error": "Invalid or missing API-Key"}), 401
    return user


@data_blueprint.route('/comparison/sessions', methods=['GET'])
def list_sessions_for_comparison():
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    comparison_function_type = FeatureFunctionType.query.filter_by(name='comparison').first()
    if not comparison_function_type:
        return jsonify({'error': 'Comparison function type not found'}), 404

    comparison_scenarios = get_user_scenarios(user.id, comparison_function_type.function_type_id)

    scenarios_list = [{'id': scenario.id} for scenario in comparison_scenarios]
    return jsonify(scenarios_list), 200


@data_blueprint.route('/comparison/create_session', methods=['POST'])
def create_session():
    user = require_user()
    if isinstance(user, tuple):
        return user

    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Invalid JSON'}), 400
    scenario_id = data.get('scenario_id')

    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        return jsonify({"error": "Session not found"}), 404

    # Choose persona
    personas = json.loads(PERSONAS_PATH.read_text())
    persona = random.choice(personas)
    persona_props = json.loads(persona['properties'])
    persona_json = {
        "name": persona['name'],
        "properties": persona_props,
    }

    session = ComparisonSession(
        scenario_id=scenario_id,
        persona_json=persona_json,
        messages=[]
    )
    db.session.add(session)
    db.session.commit()
    session_serializable = {
        "id": session.id,
        "scenario_id": session.scenario_id,
        "persona_json": session.persona_json,
        "messages": []
    }

    return jsonify(session_serializable), 200


@data_blueprint.route('/comparison/session/<int:session_id>', methods=['GET'])
def get_session(session_id):
    user = require_user()
    if isinstance(user, tuple):
        return user

    session = ComparisonSession.query.filter_by(id=session_id).first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    messages = (
        ComparisonMessage
        .query
        .filter_by(session_id=session_id)
        .order_by(ComparisonMessage.idx)
        .all()
    )
    serialized_messages = [
        {
            'id': m.id,
            'idx': m.idx,
            'type': m.type,
            'content': m.content,
            'selected': m.selected,
            'timestamp': m.timestamp.isoformat()
        }
        for m in messages
    ]

    session_serializable = {
        'id': session.id,
        'scenario_id': session.scenario_id,
        'persona_json': session.persona_json,
        'messages': serialized_messages
    }
    return jsonify(session_serializable), 200
