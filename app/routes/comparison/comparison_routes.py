from flask import jsonify, g

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError
from decorators.permission_decorator import require_permission
from routes.HelperFunctions import get_user_scenarios
from routes.auth import data_bp as data_blueprint
from db.tables import ComparisonSession, ComparisonMessage, FeatureFunctionType


@data_blueprint.route('/comparison/sessions', methods=['GET'])
@authentik_required
@require_permission("feature:comparison:view")
@handle_api_errors(logger_name='comparison')
def list_sessions_for_comparison():
    user = g.authentik_user

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
            total_pairs = sum(1 for msg in session.messages if msg.type == "bot_pair")
            rated_messages = sum(1 for msg in session.messages if msg.type == "bot_pair" and msg.selected is not None)

            if total_pairs == 0 or rated_messages == 0:
                status = 'not_started'
                color = 'grey'
            elif rated_messages < total_pairs:
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
                'total_pairs': total_pairs,
                'status': status,
                'color': color
            })

    return jsonify(all_sessions), 200


@data_blueprint.route('/comparison/session/<int:session_id>', methods=['GET'])
@authentik_required
@require_permission("feature:comparison:view")
@handle_api_errors(logger_name='comparison')
def get_session(session_id):
    user = g.authentik_user

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
