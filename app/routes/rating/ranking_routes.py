"""
Ranking Routes

Provides endpoints for ranking features across evaluation items.

NOTE: Diese Endpoints verwenden den SchemaAdapter Service für einheitliche
Datenformate. Neue Frontend-Komponenten sollten die /schema Endpoints nutzen.

Legacy-Endpoints werden für Abwärtskompatibilität beibehalten.
"""

import logging

from flask import jsonify, request, g, current_app

from auth.decorators import authentik_required, admin_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from db.database import db
from db.models import EvaluationItem, ScenarioItems, ScenarioUsers
from routes.auth import data_bp
from services.evaluation.schema_adapter_service import SchemaAdapter
from services.feature_service import FeatureService
from services.ranking_service import RankingService
from services.scenario_stats_service import get_scenario_ids_for_thread
from services.thread_service import ThreadService


logger = logging.getLogger(__name__)


def _emit_scenario_stats_updates(thread_id: int) -> None:
    """Emit scenario stats updates via SocketIO."""
    socketio = current_app.extensions.get('socketio')
    if not socketio:
        return
    try:
        from socketio_handlers.events_scenarios import emit_scenario_stats_updated
        for scenario_id in get_scenario_ids_for_thread(thread_id):
            emit_scenario_stats_updated(socketio, scenario_id)
    except Exception:
        pass


def _check_item_access(item_id: int, user_id: int) -> bool:
    """Check if user has access to an evaluation item."""
    # First try new EvaluationItem model
    eval_item = EvaluationItem.query.get(item_id)
    if eval_item:
        scenario = SchemaAdapter.check_scenario_access(item_id, user_id)
        return scenario is not None

    # Fallback to legacy ThreadService check
    return ThreadService.can_user_access_thread(user_id, item_id, 1)


@data_bp.route('/email_threads/rankings', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def list_email_threads_for_rankings():
    """
    List all evaluation items available for ranking.

    Returns legacy format for backwards compatibility.
    New clients should use /api/scenarios/{id}/schema endpoints.
    """
    user = g.authentik_user

    # Use FeatureService to get function type
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        raise NotFoundError('Ranking function type not found')

    # Try new EvaluationItem model first
    from db.models import RatingScenarios
    scenarios = RatingScenarios.query.filter_by(function_type_id=1).all()

    threads_list = []
    seen_items = set()

    for scenario in scenarios:
        # Check if user has access to this scenario
        scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id,
            user_id=user.id
        ).first()
        if not scenario_user:
            continue

        # Get items for this scenario
        scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario.id).all()
        for si in scenario_items:
            if si.item_id in seen_items:
                continue
            seen_items.add(si.item_id)

            eval_item = EvaluationItem.query.get(si.item_id)
            if eval_item:
                ranked = RankingService.has_user_fully_ranked_thread(user.id, si.item_id)
                threads_list.append({
                    'thread_id': eval_item.item_id,
                    'chat_id': eval_item.chat_id,
                    'institut_id': getattr(eval_item, 'institut_id', None),
                    'subject': eval_item.subject,
                    'sender': getattr(eval_item, 'sender', None),
                    'ranked': ranked
                })

    # Fallback: Also include legacy threads if available
    try:
        email_threads = ThreadService.get_threads_for_user(user.id, ranking_function_type.function_type_id)
        for thread in email_threads:
            if thread.thread_id not in seen_items:
                ranked = RankingService.has_user_fully_ranked_thread(user.id, thread.thread_id)
                threads_list.append({
                    'thread_id': thread.thread_id,
                    'chat_id': thread.chat_id,
                    'institut_id': thread.institut_id,
                    'subject': thread.subject,
                    'sender': thread.sender,
                    'ranked': ranked
                })
    except Exception:
        pass  # Legacy table might not exist

    return jsonify(threads_list), 200


@data_bp.route('/email_threads/feature_ranking_list', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def list_ranking_threads():
    """
    List ranking threads (simplified, without ranked status).

    Returns legacy format for backwards compatibility.
    """
    user = g.authentik_user

    # Use FeatureService to get function type
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        raise NotFoundError('Ranking function type not found')

    # Try new EvaluationItem model first
    from db.models import RatingScenarios
    scenarios = RatingScenarios.query.filter_by(function_type_id=1).all()

    threads_list = []
    seen_items = set()

    for scenario in scenarios:
        scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id,
            user_id=user.id
        ).first()
        if not scenario_user:
            continue

        scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario.id).all()
        for si in scenario_items:
            if si.item_id in seen_items:
                continue
            seen_items.add(si.item_id)

            eval_item = EvaluationItem.query.get(si.item_id)
            if eval_item:
                threads_list.append({
                    'thread_id': eval_item.item_id,
                    'chat_id': eval_item.chat_id,
                    'institut_id': getattr(eval_item, 'institut_id', None),
                    'subject': eval_item.subject
                })

    # Fallback to legacy
    try:
        email_threads = ThreadService.get_threads_for_user(user.id, ranking_function_type.function_type_id)
        for thread in email_threads:
            if thread.thread_id not in seen_items:
                threads_list.append({
                    'thread_id': thread.thread_id,
                    'chat_id': thread.chat_id,
                    'institut_id': thread.institut_id,
                    'subject': thread.subject
                })
    except Exception:
        pass

    return jsonify(threads_list), 200


@data_bp.route('/email_threads/rankings/<int:thread_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def get_email_thread_for_rankings(thread_id):
    """
    Get evaluation item with features for ranking.

    Supports query param ?schema=true for new schema format.
    Default returns legacy format for backwards compatibility.

    New clients should use: GET /api/scenarios/{id}/items/{item_id}/schema
    """
    user = g.authentik_user
    use_schema = request.args.get('schema', 'false').lower() == 'true'

    # Check access
    eval_item = EvaluationItem.query.get(thread_id)
    if eval_item:
        scenario = SchemaAdapter.check_scenario_access(thread_id, user.id)
        if not scenario:
            raise ValidationError('Access denied')

        # Return new schema format if requested
        if use_schema:
            schema_data = SchemaAdapter.get_schema_data(scenario, thread_id)
            return jsonify(schema_data.model_dump()), 200

        # Return legacy format using SchemaAdapter
        thread_data = SchemaAdapter.get_ranking_thread_data(thread_id, user.id)
        if not thread_data:
            raise NotFoundError('Item not found')

        return jsonify(thread_data), 200

    # Fallback to legacy EmailThread model
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        raise NotFoundError('Ranking function type not found')

    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        raise ValidationError('Access denied')

    email_thread = ThreadService.get_thread_by_id(thread_id, ranking_function_type.function_type_id)
    if not email_thread:
        raise NotFoundError('Email thread not found or not for ranking')

    ranked = RankingService.has_user_fully_ranked_thread(user.id, email_thread.thread_id)

    thread_data = {
        'chat_id': email_thread.chat_id,
        'institut_id': email_thread.institut_id,
        'subject': email_thread.subject,
        'ranked': ranked,
        'messages': [
            {
                'message_id': msg.message_id,
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
            } for msg in email_thread.messages
        ],
        'features': [
            {
                'model_name': feature.llm.name if feature.llm else 'Unknown',
                'type': feature.feature_type.name if feature.feature_type else 'Summary',
                'content': feature.content,
                'feature_id': feature.feature_id
            } for feature in email_thread.features
        ]
    }

    return jsonify(thread_data), 200


@data_bp.route('/email_threads/<int:thread_id>/current_ranking', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def get_current_ranking(thread_id):
    """Get current ranking for a thread/item."""
    user = g.authentik_user

    # Check access
    if not _check_item_access(thread_id, user.id):
        raise ValidationError('Access denied')

    # Use RankingService to get current rankings organized by type
    rankings_data = RankingService.get_current_rankings_by_type(user.id, thread_id)

    # Format the output as expected by frontend
    formatted_rankings = [
        {
            "type": feature_type,
            "details": data["details"],
            "neutralList": data["neutralList"]
        }
        for feature_type, data in rankings_data.items()
    ]

    return jsonify(formatted_rankings), 200


@data_bp.route('/save_ranking/<int:thread_id>', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='ranking')
def save_ranking(thread_id):
    """Save rankings for a thread."""
    user = g.authentik_user

    # Check access
    if not _check_item_access(thread_id, user.id):
        raise ValidationError('Access denied')

    try:
        data = request.get_json() or []

        # Replace semantics: clear previous rankings first.
        # This ensures moving an item back to Neutral actually removes the ranking row.
        success, error_msg = RankingService.clear_rankings_for_thread(user.id, thread_id, commit=False)
        if not success:
            raise ValidationError(error_msg)

        for feature_type in data:
            type_name = feature_type['type']
            for detail in feature_type['details']:
                model_name = detail['model_name']
                content = detail['content']
                position = detail['position']
                bucket = detail['bucket']

                # Use FeatureService to find the FeatureType
                feature_type_entry = FeatureService.get_feature_type_by_name(type_name)
                if not feature_type_entry:
                    raise NotFoundError(f'Feature type {type_name} not found')

                # Use FeatureService to find the LLM
                llm_entry = FeatureService.get_llm_by_name(model_name)
                if not llm_entry:
                    raise NotFoundError(f'LLM {model_name} not found')

                # Use FeatureService to find the feature
                feature = FeatureService.get_feature_by_attributes(
                    thread_id=thread_id,
                    type_id=feature_type_entry.type_id,
                    llm_id=llm_entry.llm_id,
                    content=content
                )

                if feature:
                    # Use RankingService to save the ranking
                    success, error_msg = RankingService.save_ranking(
                        user_id=user.id,
                        thread_id=thread_id,
                        feature_id=feature.feature_id,
                        type_id=feature_type_entry.type_id,
                        llm_id=llm_entry.llm_id,
                        position=position,
                        bucket=bucket,
                        commit=False
                    )

                    if not success:
                        raise ValidationError(error_msg)

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    _emit_scenario_stats_updates(thread_id)

    return jsonify({'status': 'Ranking saved successfully'}), 201


@data_bp.route('/admin/user_ranking_stats', methods=['GET'])
@admin_required
@handle_api_errors(logger_name='ranking')
def get_user_ranking_stats():
    """Get ranking statistics for all users (admin only)."""
    # Use RankingService to get user ranking stats
    user_stats = RankingService.get_user_ranking_stats_for_all_users()

    return jsonify(user_stats), 200
