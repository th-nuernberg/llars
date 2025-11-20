"""
Mail Rating Statistics Endpoints
Admin panel statistics for mail history generation progress.
"""

import logging
from flask import jsonify, g
from auth.decorators import admin_required
from db.db import db
from db.tables import (User, EmailThread, FeatureFunctionType,
                       UserMailHistoryRating, ProgressionStatus)
from .. import data_blueprint


@data_blueprint.route('/admin/user_HistoryGeneration_stats', methods=['GET'])
@admin_required
def get_user_HistoryGeneration_stats():
    """Get progress statistics for all users on mail history generation"""
    try:
        # Authorization handled by @admin_required decorator
        # Current user available in g.keycloak_user

        user_stats = []
        mail_rating_function_type = FeatureFunctionType.query.filter_by(name='mail_rating').first()
        if not mail_rating_function_type:
            return jsonify({'error': 'Mail rating function type is missing'}), 401

        mail_rating_function_type = mail_rating_function_type.function_type_id
        total_threads = db.session.query(EmailThread).filter_by(function_type_id=mail_rating_function_type).count()

        for user in User.query.all():
            done_threads_list = []
            not_started_threads_list = []
            progressing_threads_list = []
            total_done_threads = 0
            total_progressing_threads = 0
            total_not_started_threads = 0

            for thread in EmailThread.query.filter_by(function_type_id=mail_rating_function_type).all():
                mail_rating = UserMailHistoryRating.query.filter_by(user_id=user.id,
                                                                    thread_id=thread.scenario_thread_id).order_by(
                    UserMailHistoryRating.timestamp.desc()).first()

                if mail_rating:
                    if mail_rating.status == ProgressionStatus.PROGRESSING:
                        total_progressing_threads += 1
                        progressing_threads_list.append(
                            {'thread_id': thread.scenario_thread_id, "subject": thread.subject, })
                    elif mail_rating.status == ProgressionStatus.DONE:
                        total_done_threads += 1
                        done_threads_list.append({'thread_id': thread.scenario_thread_id, "subject": thread.subject, })
                    else:
                        total_not_started_threads += 1
                        not_started_threads_list.append(
                            {'thread_id': thread.scenario_thread_id, "subject": thread.subject, })
                else:
                    total_not_started_threads += 1
                    not_started_threads_list.append(
                        {'thread_id': thread.scenario_thread_id, "subject": thread.subject, })

            user_stats.append({
                'username': user.username,
                'total_threads': total_threads,
                'done_threads': total_done_threads,
                'not_started_threads': total_not_started_threads,
                'progressing_threads': total_progressing_threads,
                'done_threads_list': done_threads_list,
                'not_started_threads_list': not_started_threads_list,
                'progressing_threads_list': progressing_threads_list
            })

        return jsonify(user_stats), 200
    except Exception as e:
        logging.error(e)
        return jsonify({"error": "Internal Server Error"}), 500
