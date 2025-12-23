"""
Scenario Statistics and Progress Tracking
Provides progress and completion statistics for scenarios.
"""

import logging
from flask import jsonify, g
from auth.decorators import admin_required, authentik_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from db.db import db
from db.tables import (RatingScenarios, FeatureFunctionType, ScenarioUsers,
                       ScenarioThreads, ScenarioRoles, User, ScenarioThreadDistribution,
                       ProgressionStatus)
from ..HelperFunctions import get_thread_progression_state, raters_receive_all_threads, get_user_threads
from .. import data_blueprint


@data_blueprint.route('/admin/scenario_progress_stats/<int:scenario_id>', methods=['GET'])
@admin_required
@handle_api_errors(logger_name='scenarios')
def get_scenario_user_progress_stats(scenario_id):
    """Get detailed progress statistics for all users in a scenario"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    # check if scenario id is valid
    if not scenario_id:
        raise ValidationError('Scenario id is missing')

    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        raise NotFoundError('Scenario does not exist')

    if not db.session.query(FeatureFunctionType).filter(
            FeatureFunctionType.function_type_id == scenario.function_type_id):
        raise NotFoundError('Function type does not exist')

    rater_stats = []
    viewer_stats = []

    scenario_users = (db.session.query(ScenarioUsers).join(User, ScenarioUsers.user_id == User.id)
                     .filter(ScenarioUsers.scenario_id == scenario_id).all())

    for scenario_user in scenario_users:
        done_threads_list = []
        not_started_threads_list = []
        progressing_threads_list = []
        total_done_threads = 0
        total_progressing_threads = 0
        total_not_started_threads = 0

        use_full_threads = (
            scenario_user.role == ScenarioRoles.VIEWER
            or (scenario_user.role == ScenarioRoles.RATER and raters_receive_all_threads(scenario))
        )

        if use_full_threads:
            user_threads = (
                db.session.query(ScenarioThreads)
                .filter(ScenarioThreads.scenario_id == scenario_id)
                .all()
            )
        else:
            user_threads = (
                db.session.query(ScenarioThreads)
                .join(
                    ScenarioThreadDistribution,
                    ScenarioThreadDistribution.scenario_thread_id == ScenarioThreads.id
                )
                .join(ScenarioUsers, ScenarioThreadDistribution.scenario_user_id == ScenarioUsers.id)
                .filter(
                    ScenarioThreads.scenario_id == scenario_id,
                    ScenarioUsers.user_id == scenario_user.user_id
                )
                .all()
            )
        if not user_threads:
            user_threads = []

        for user_thread in user_threads:
            thread = user_thread.thread

            progression_state = get_thread_progression_state(thread=thread, user_id=scenario_user.user_id,
                                                             function_type_id=scenario.function_type_id)

            if progression_state:
                if progression_state == ProgressionStatus.PROGRESSING:
                    total_progressing_threads += 1
                    progressing_threads_list.append({
                        'thread_id': thread.thread_id,
                        'subject': thread.subject,
                        'chat_id': thread.chat_id,
                        'institut_id': thread.institut_id,
                    })
                elif progression_state == ProgressionStatus.DONE:
                    total_done_threads += 1
                    done_threads_list.append({
                        'thread_id': thread.thread_id,
                        'subject': thread.subject,
                        'chat_id': thread.chat_id,
                        'institut_id': thread.institut_id,
                    })
                else:
                    total_not_started_threads += 1
                    not_started_threads_list.append({
                        'thread_id': thread.thread_id,
                        'subject': thread.subject,
                        'chat_id': thread.chat_id,
                        'institut_id': thread.institut_id,
                    })

        new_data = {
            'username': scenario_user.user.username,
            'total_threads': len(user_threads),
            'done_threads': total_done_threads,
            'not_started_threads': total_not_started_threads,
            'progressing_threads': total_progressing_threads,
            'done_threads_list': done_threads_list,
            'not_started_threads_list': not_started_threads_list,
            'progressing_threads_list': progressing_threads_list
        }

        if scenario_user.role == ScenarioRoles.RATER:
            rater_stats.append(new_data)
        elif scenario_user.role == ScenarioRoles.VIEWER:
            viewer_stats.append(new_data)

    return jsonify({'rater_stats': rater_stats, "viewer_stats": viewer_stats}), 200


@data_blueprint.route('/evaluation/thread_counts', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenarios')
def get_user_thread_counts():
    """
    Get the count of assigned threads per function_type for the current user.
    Used by EvaluationHub to show which tools have scenarios available.

    Returns:
        {
            "counts": {
                "ranking": 3,
                "rating": 0,
                "mail_rating": 2,
                "comparison": 0,
                "authenticity": 1
            }
        }
    """
    user = g.authentik_user

    # Get all function types
    function_types = db.session.query(FeatureFunctionType).all()

    counts = {}
    for ft in function_types:
        threads = get_user_threads(user.id, ft.function_type_id)
        counts[ft.name] = len(threads)

    return jsonify({'counts': counts}), 200
