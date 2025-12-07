"""
Ranking Routes

Provides endpoints for ranking features across email threads.
"""

import logging

from flask import jsonify, request, g

from auth.decorators import authentik_required, admin_required
from routes.auth import data_bp
from services.feature_service import FeatureService
from services.ranking_service import RankingService
from services.thread_service import ThreadService


logger = logging.getLogger(__name__)


@data_bp.route('/email_threads/rankings', methods=['GET'])
@authentik_required
def list_email_threads_for_rankings():
    """List all email threads available for ranking"""
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Use FeatureService to get function type
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    # Use ThreadService to get user threads
    email_threads = ThreadService.get_threads_for_user(user.id, ranking_function_type.function_type_id)

    threads_list = []
    for thread in email_threads:
        # Use RankingService to check if user has ranked this thread
        ranked = RankingService.has_user_ranked_thread(user.id, thread.thread_id)

        threads_list.append({
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject,
            'sender': thread.sender,
            'ranked': ranked
        })

    return jsonify(threads_list), 200


@data_bp.route('/email_threads/feature_ranking_list', methods=['GET'])
@authentik_required
def list_ranking_threads():
    """List ranking threads (simplified)"""
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Use FeatureService to get function type
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    # Use ThreadService to get user threads
    email_threads = ThreadService.get_threads_for_user(user.id, ranking_function_type.function_type_id)

    threads_list = [
        {
            'thread_id': thread.thread_id,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id,
            'subject': thread.subject
        } for thread in email_threads
    ]

    return jsonify(threads_list), 200


@data_bp.route('/email_threads/rankings/<int:thread_id>', methods=['GET'])
@authentik_required
def get_email_thread_for_rankings(thread_id):
    """Get email thread with features for ranking"""
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Use FeatureService to get function type
    ranking_function_type = FeatureService.get_function_type_by_name('ranking')
    if not ranking_function_type:
        return jsonify({'error': 'Ranking function type not found'}), 404

    # Use ThreadService to check access
    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        return jsonify({'error': 'Access denied'}), 401

    # Use ThreadService to get thread by id
    email_thread = ThreadService.get_thread_by_id(thread_id, ranking_function_type.function_type_id)
    if not email_thread:
        return jsonify({'error': 'Email thread not found or not for ranking'}), 404

    # Use RankingService to check if user has ranked this thread
    ranked = RankingService.has_user_ranked_thread(user.id, email_thread.thread_id)

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


@data_bp.route('/email_threads/<int:thread_id>/current_ranking', methods=['GET'])
@authentik_required
def get_current_ranking(thread_id):
    """Get current ranking for a thread"""
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Use ThreadService to check access
    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        return jsonify({'error': 'Access denied'}), 401

    # Use RankingService to get current rankings organized by type
    rankings_data = RankingService.get_current_rankings_by_type(user.id, thread_id)

    # Format the output as expected by frontend
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


@data_bp.route('/save_ranking/<int:thread_id>', methods=['POST'])
@authentik_required
def save_ranking(thread_id):
    """Save rankings for a thread"""
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Use ThreadService to check access
    if not ThreadService.can_user_access_thread(user.id, thread_id, 1):
        return jsonify({'error': 'Access denied'}), 401

    data = request.get_json()

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
                return jsonify({'error': f'Feature type {type_name} not found'}), 404

            # Use FeatureService to find the LLM
            llm_entry = FeatureService.get_llm_by_name(model_name)
            if not llm_entry:
                return jsonify({'error': f'LLM {model_name} not found'}), 404

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
                    bucket=bucket
                )

                if not success:
                    return jsonify({'error': error_msg}), 400

    return jsonify({'status': 'Ranking saved successfully'}), 201


@data_bp.route('/admin/user_ranking_stats', methods=['GET'])
@admin_required
def get_user_ranking_stats():
    """Get ranking statistics for all users (admin only)"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    # Use RankingService to get user ranking stats
    user_stats = RankingService.get_user_ranking_stats_for_all_users()

    return jsonify(user_stats), 200
