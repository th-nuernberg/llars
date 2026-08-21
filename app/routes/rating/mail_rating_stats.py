"""
Mail Rating Statistics Endpoints
Admin panel statistics for mail history generation progress.
"""

import logging
from flask import jsonify, g
from auth.decorators import admin_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from db.database import db
from db.tables import (User, EmailThread, FeatureFunctionType,
                       UserMailHistoryRating, ProgressionStatus)
from .. import data_blueprint


@data_blueprint.route('/admin/user_HistoryGeneration_stats', methods=['GET'])
@admin_required
@handle_api_errors(logger_name='rating')
def get_user_HistoryGeneration_stats():
    """Get progress statistics for all users on mail history generation.

    Uses a single batch query for ratings instead of N*M individual queries,
    reducing O(users * threads) DB calls to O(1) queries.
    """
    mail_rating_function_type = FeatureFunctionType.query.filter_by(name='mail_rating').first()
    if not mail_rating_function_type:
        raise NotFoundError('Mail rating function type is missing')

    ft_id = mail_rating_function_type.function_type_id
    threads = EmailThread.query.filter_by(function_type_id=ft_id).all()
    total_threads = len(threads)
    users = User.query.all()

    # Batch: fetch latest rating per (user, thread) in one query using a subquery
    from sqlalchemy import func
    latest_ts = db.session.query(
        UserMailHistoryRating.user_id,
        UserMailHistoryRating.thread_id,
        func.max(UserMailHistoryRating.timestamp).label('max_ts')
    ).group_by(
        UserMailHistoryRating.user_id,
        UserMailHistoryRating.thread_id
    ).subquery()

    all_ratings = db.session.query(UserMailHistoryRating).join(
        latest_ts,
        db.and_(
            UserMailHistoryRating.user_id == latest_ts.c.user_id,
            UserMailHistoryRating.thread_id == latest_ts.c.thread_id,
            UserMailHistoryRating.timestamp == latest_ts.c.max_ts
        )
    ).all()

    # Index ratings by (user_id, thread_id) for O(1) lookup
    ratings_map = {}
    for r in all_ratings:
        ratings_map[(r.user_id, r.thread_id)] = r

    user_stats = []
    for user in users:
        done_list, progressing_list, not_started_list = [], [], []

        for thread in threads:
            thread_info = {'thread_id': thread.scenario_thread_id, 'subject': thread.subject}
            rating = ratings_map.get((user.id, thread.scenario_thread_id))

            if rating and rating.status == ProgressionStatus.DONE:
                done_list.append(thread_info)
            elif rating and rating.status == ProgressionStatus.PROGRESSING:
                progressing_list.append(thread_info)
            else:
                not_started_list.append(thread_info)

        user_stats.append({
            'username': user.username,
            'total_threads': total_threads,
            'done_threads': len(done_list),
            'not_started_threads': len(not_started_list),
            'progressing_threads': len(progressing_list),
            'done_threads_list': done_list,
            'not_started_threads_list': not_started_list,
            'progressing_threads_list': progressing_list
        })

    return jsonify(user_stats), 200
