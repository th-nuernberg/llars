import random
import json
from pathlib import Path

from flask import request, jsonify

from . import data_blueprint
from db.database import db
from db.tables import (
    User,
    ComparisonSession,
    ComparisonMessage,
    FeatureFunctionType,
    RatingScenarios
)
from routes.HelperFunctions import get_user_scenarios
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, UnauthorizedError

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
@handle_api_errors(logger_name='comparison')
def list_sessions_for_comparison():
    api_key = request.headers.get('Authorization')
    if not api_key:
        raise UnauthorizedError('API key is missing')

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        raise UnauthorizedError('Invalid API key')

    comparison_function_type = FeatureFunctionType.query.filter_by(name='comparison').first()
    if not comparison_function_type:
        raise NotFoundError('Comparison function type not found')

    comparison_scenarios = get_user_scenarios(user.id, comparison_function_type.function_type_id)

    all_sessions = []
    for scenario in comparison_scenarios:
        sessions = ComparisonSession.query.filter_by(
            scenario_id=scenario.scenario_id,
            user_id=user.id
        ).all()
        
        for session in sessions:
            rated_messages = sum(1 for msg in session.messages if msg.selected is not None)
            
            if rated_messages == 0:
                status = 'not_started'
                color = 'grey'
            elif rated_messages < 30:
                status = 'progressing'
                color = 'yellow'
            else:
                status = 'completed'
                color = 'green'
            
            all_sessions.append({
                'id': session.id,
                'scenario_id': session.scenario_id,
                'persona_name': session.persona_name,
                'persona_json': session.persona_json,
                'rated_messages': rated_messages,
                'status': status,
                'color': color
            })

    return jsonify(all_sessions), 200


@data_blueprint.route('/comparison/session/<int:session_id>', methods=['GET'])
@handle_api_errors(logger_name='comparison')
def get_session(session_id):
    user = require_user()
    if isinstance(user, tuple):
        return user

    session = ComparisonSession.query.filter_by(id=session_id, user_id=user.id).first()
    if not session:
        raise NotFoundError('Session not found')

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
        'persona_name': session.persona_name,
        'messages': serialized_messages
    }
    return jsonify(session_serializable), 200
