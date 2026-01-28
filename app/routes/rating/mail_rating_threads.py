"""
Mail Rating Thread Endpoints

Handles thread retrieval and listing for mail rating functionality.

NOTE: Diese Endpoints verwenden den SchemaAdapter Service für einheitliche
Datenformate. Neue Frontend-Komponenten sollten die /schema Endpoints nutzen.
"""

import logging

from flask import jsonify, g, request
from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from db.database import db
from db.models import (
    EvaluationItem, Message, ScenarioItems, ScenarioUsers,
    RatingScenarios, UserMailHistoryRating, ProgressionStatus
)
from services.evaluation.schema_adapter_service import SchemaAdapter
from .. import data_blueprint


logger = logging.getLogger(__name__)


def _check_mail_rating_access(item_id: int, user_id: int) -> bool:
    """Check if user has access to a mail rating item."""
    eval_item = EvaluationItem.query.get(item_id)
    if eval_item:
        scenario = SchemaAdapter.check_scenario_access(item_id, user_id)
        return scenario is not None

    # Fallback to legacy check
    from db.tables import EmailThread
    thread = EmailThread.query.filter_by(thread_id=item_id).first()
    return thread is not None


@data_blueprint.route('/email_threads/generations/<int:thread_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_email_thread_details(thread_id):
    """
    Get detailed message content for an evaluation item.

    Supports query param ?schema=true for new schema format.
    """
    user = g.authentik_user
    use_schema = request.args.get('schema', 'false').lower() == 'true'

    # First try new EvaluationItem model
    eval_item = EvaluationItem.query.get(thread_id)
    if eval_item:
        scenario = SchemaAdapter.check_scenario_access(thread_id, user.id)

        # Return new schema format if requested
        if use_schema and scenario:
            schema_data = SchemaAdapter.get_schema_data(scenario, thread_id)
            return jsonify(schema_data.model_dump()), 200

        # Return legacy format using SchemaAdapter
        thread_data = SchemaAdapter.get_mail_rating_thread_data(thread_id, user.id)
        if thread_data:
            return jsonify({'messages': thread_data['messages']}), 200

    # Fallback to legacy EmailThread model
    from db.tables import EmailThread
    email_thread = EmailThread.query.filter_by(thread_id=thread_id).first()
    if not email_thread:
        raise NotFoundError('Email thread not found')

    messages = Message.query.filter_by(thread_id=email_thread.thread_id).all()
    if not messages:
        raise NotFoundError('No messages found for this thread')

    messages_data = [
        {
            'message_id': msg.message_id,
            'sender': msg.sender,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
        } for msg in messages
    ]

    return jsonify({'messages': messages_data}), 200


@data_blueprint.route('/email_threads/mailhistory_ratings', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def list_email_threads_for_mail_ratings():
    """Get list of all threads assigned to user for mail rating with progression status."""
    user = g.authentik_user

    # Try new EvaluationItem model first (mail_rating function_type_id = 3)
    scenarios = RatingScenarios.query.filter_by(function_type_id=3).all()

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
                # Check for existing UserMailHistoryRating
                mail_rating = (
                    db.session.query(UserMailHistoryRating)
                    .filter_by(user_id=user.id, thread_id=si.item_id)
                    .order_by(UserMailHistoryRating.timestamp.desc())
                    .first()
                )

                status = mail_rating.status if mail_rating else ProgressionStatus.NOT_STARTED

                threads_list.append({
                    'thread_id': eval_item.item_id,
                    'chat_id': eval_item.chat_id,
                    'institut_id': getattr(eval_item, 'institut_id', None),
                    'subject': eval_item.subject,
                    'sender': getattr(eval_item, 'sender', None),
                    'progression_status': status.value,
                })

    # Fallback to legacy EmailThread
    try:
        from db.tables import FeatureFunctionType
        from ..HelperFunctions import get_user_threads

        mail_rating_function_type = FeatureFunctionType.query.filter_by(name='mail_rating').first()
        if mail_rating_function_type:
            accessible_threads = get_user_threads(user.id, mail_rating_function_type.function_type_id)

            for thread in accessible_threads:
                if thread.thread_id in seen_items:
                    continue
                seen_items.add(thread.thread_id)

                mail_rating = (
                    db.session.query(UserMailHistoryRating)
                    .filter_by(user_id=user.id, thread_id=thread.thread_id)
                    .order_by(UserMailHistoryRating.timestamp.desc())
                    .first()
                )

                status = mail_rating.status if mail_rating else ProgressionStatus.NOT_STARTED

                threads_list.append({
                    'thread_id': thread.thread_id,
                    'chat_id': thread.chat_id,
                    'institut_id': thread.institut_id,
                    'subject': thread.subject,
                    'sender': thread.sender,
                    'progression_status': status.value,
                })
    except Exception:
        pass  # Legacy table might not exist

    return jsonify({'threads': threads_list}), 200
