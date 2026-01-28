"""
Rating Routes

Provides endpoints for rating evaluation items and features.

NOTE: Diese Endpoints verwenden den SchemaAdapter Service für einheitliche
Datenformate. Neue Frontend-Komponenten sollten die /schema Endpoints nutzen.
"""

import logging

from flask import jsonify, request, g, current_app

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from routes.auth import data_bp
from db.database import db
from db.models import (
    FeatureType, UserFeatureRating, Feature, Message,
    EvaluationItem, ScenarioItems, ScenarioUsers, RatingScenarios
)
from services.evaluation.schema_adapter_service import SchemaAdapter
from services.feature_rating_service import FeatureRatingService
from services.scenario_stats_service import get_scenario_ids_for_thread


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


def _check_rating_access(item_id: int, user_id: int) -> bool:
    """Check if user has access to a rating item."""
    # First try new EvaluationItem model
    eval_item = EvaluationItem.query.get(item_id)
    if eval_item:
        scenario = SchemaAdapter.check_scenario_access(item_id, user_id)
        return scenario is not None

    # Fallback to legacy check
    from routes.HelperFunctions import can_access_thread
    return can_access_thread(user_id, item_id, 2)


@data_bp.route('/email_threads/ratings/<int:thread_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_email_thread_for_ratings(thread_id):
    """
    Get evaluation item with features for rating.

    Supports query param ?schema=true for new schema format.
    Default returns legacy format for backwards compatibility.
    """
    user = g.authentik_user
    use_schema = request.args.get('schema', 'false').lower() == 'true'

    # First try new EvaluationItem model
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
        thread_data = SchemaAdapter.get_rating_thread_data(thread_id, user.id)
        if not thread_data:
            raise NotFoundError('Item not found')

        # Add rating status
        rated = FeatureRatingService.has_user_fully_rated_thread(user.id, thread_id)
        ratings_by_feature_id = FeatureRatingService.get_user_ratings_map_for_thread(user.id, thread_id)

        thread_data['rated'] = rated

        # Add user ratings to features
        features = Feature.query.filter_by(item_id=thread_id).all()
        thread_data['features'] = [
            {
                'model_name': feature.llm.name if feature.llm else 'Unknown',
                'type': feature.feature_type.name if feature.feature_type else 'Summary',
                'content': feature.content,
                'user_rating': ratings_by_feature_id.get(feature.feature_id).rating_content
                if ratings_by_feature_id.get(feature.feature_id) else None,
                'feature_id': feature.feature_id
            } for feature in features
        ]

        return jsonify(thread_data), 200

    # Fallback to legacy EmailThread model
    from routes.HelperFunctions import can_access_thread
    if not can_access_thread(user.id, thread_id, 2):
        raise ValidationError('Access denied')

    from db.tables import FeatureFunctionType, EmailThread
    rating_function_type = FeatureFunctionType.query.filter_by(name='rating').first()
    if not rating_function_type:
        raise NotFoundError('Rating function type not found')

    email_thread = EmailThread.query.filter_by(
        thread_id=thread_id,
        function_type_id=rating_function_type.function_type_id
    ).first()
    if not email_thread:
        raise NotFoundError('Email thread not found or not for rating')

    rated = FeatureRatingService.has_user_fully_rated_thread(user.id, email_thread.thread_id)
    ratings_by_feature_id = FeatureRatingService.get_user_ratings_map_for_thread(user.id, email_thread.thread_id)

    thread_data = {
        'chat_id': email_thread.chat_id,
        'institut_id': email_thread.institut_id,
        'subject': email_thread.subject,
        'rated': rated,
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
                'user_rating': ratings_by_feature_id.get(feature.feature_id).rating_content
                if ratings_by_feature_id.get(feature.feature_id) else None,
                'feature_id': feature.feature_id
            } for feature in email_thread.features
        ]
    }

    return jsonify(thread_data), 200


@data_bp.route('/email_threads/ratings/<int:thread_id>/<int:feature_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_feature_and_messages(thread_id, feature_id):
    """Get specific feature and messages for a thread."""
    user = g.authentik_user

    if not _check_rating_access(thread_id, user.id):
        raise ValidationError('Access denied')

    # Try item_id first (new model), then thread_id (legacy)
    feature = Feature.query.filter_by(item_id=thread_id, feature_id=feature_id).first()
    if not feature:
        feature = Feature.query.filter_by(thread_id=thread_id, feature_id=feature_id).first()
    if not feature:
        raise NotFoundError('Feature not found')

    # Get messages - try item_id first
    messages = Message.query.filter_by(item_id=thread_id).all()
    if not messages:
        messages = Message.query.filter_by(thread_id=thread_id).all()
    if not messages:
        raise NotFoundError('No messages found for the given thread_id')

    feature_data = {
        'model_name': feature.llm.name if feature.llm else 'Unknown',
        'type': feature.feature_type.name if feature.feature_type else 'Summary',
        'content': feature.content,
        'feature_id': feature.feature_id
    }

    messages_data = [
        {
            'message_id': msg.message_id,
            'sender': msg.sender,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
        } for msg in messages
    ]

    return jsonify({
        'feature': feature_data,
        'messages': messages_data
    }), 200


@data_bp.route('/email_threads/ratings', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def list_email_threads_for_ratings():
    """List all evaluation items available for rating."""
    user = g.authentik_user

    # Try new EvaluationItem model first (rating function_type_id = 2)
    scenarios = RatingScenarios.query.filter_by(function_type_id=2).all()

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
                rated = FeatureRatingService.has_user_fully_rated_thread(user.id, si.item_id)
                threads_list.append({
                    'thread_id': eval_item.item_id,
                    'chat_id': eval_item.chat_id,
                    'institut_id': getattr(eval_item, 'institut_id', None),
                    'subject': eval_item.subject,
                    'rated': rated
                })

    # Fallback to legacy EmailThread
    try:
        from db.tables import FeatureFunctionType
        from routes.HelperFunctions import get_user_threads

        rating_function_type = FeatureFunctionType.query.filter_by(name='rating').first()
        if rating_function_type:
            email_threads = get_user_threads(user.id, 2)
            for thread in email_threads:
                if thread.thread_id not in seen_items:
                    threads_list.append({
                        'thread_id': thread.thread_id,
                        'chat_id': thread.chat_id,
                        'institut_id': thread.institut_id,
                        'subject': thread.subject,
                        'rated': FeatureRatingService.has_user_fully_rated_thread(user.id, thread.thread_id)
                    })
    except Exception:
        pass  # Legacy table might not exist

    return jsonify(threads_list), 200


@data_bp.route('/feature_type_mapping', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_feature_type_mapping():
    """Get mapping of feature types."""
    feature_types = FeatureType.query.all()

    if not feature_types:
        raise NotFoundError('No feature types found')

    mapping = {
        'by_name': {ft.name: ft.type_id for ft in feature_types},
        'by_id': {ft.type_id: ft.name for ft in feature_types}
    }

    return jsonify(mapping), 200


@data_bp.route('/feature_type_mapping/<identifier>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_feature_type(identifier):
    """Get specific feature type by ID or name."""
    if identifier.isdigit():
        feature_type = FeatureType.query.filter_by(type_id=int(identifier)).first()
        if not feature_type:
            raise NotFoundError(f'Feature type ID {identifier} not found')
        return jsonify({'name': feature_type.name}), 200
    else:
        feature_type = FeatureType.query.filter_by(name=identifier).first()
        if not feature_type:
            raise NotFoundError(f'Feature type name {identifier} not found')
        return jsonify({'type_id': feature_type.type_id}), 200


@data_bp.route('/save_rating/<int:thread_id>/<int:feature_id>', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='rating')
def save_rating(thread_id, feature_id):
    """Save a rating for a feature."""
    user = g.authentik_user

    if not _check_rating_access(thread_id, user.id):
        raise ValidationError('Access denied')

    data = request.get_json()
    rating_content = data.get('rating_content')
    edited_feature = data.get('edited_feature')

    if rating_content is None or edited_feature is None:
        raise ValidationError('Rating content and edited feature are required')

    # Find or create the feature rating
    feature_rating = UserFeatureRating.query.filter_by(
        user_id=user.id,
        feature_id=feature_id
    ).first()

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
    _emit_scenario_stats_updates(thread_id)

    return jsonify({'status': 'Rating saved successfully'}), 201


@data_bp.route('/get_rating/<int:thread_id>/<int:feature_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_rating(thread_id, feature_id):
    """Get a saved rating for a feature."""
    user = g.authentik_user

    if not _check_rating_access(thread_id, user.id):
        raise ValidationError('Access denied')

    feature_rating = UserFeatureRating.query.filter_by(
        user_id=user.id,
        feature_id=feature_id
    ).first()

    if not feature_rating:
        raise NotFoundError('Rating not found')

    return jsonify({
        'rating_content': feature_rating.rating_content,
        'edited_feature': feature_rating.edited_feature
    }), 200
