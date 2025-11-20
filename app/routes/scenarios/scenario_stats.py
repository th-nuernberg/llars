"""
Scenario Statistics and Progress Tracking
Provides progress and completion statistics for scenarios.
"""

import logging
from flask import jsonify, g
from auth.decorators import admin_required
from db.db import db
from db.tables import (RatingScenarios, FeatureFunctionType, ScenarioUsers,
                       ScenarioThreads, ScenarioRoles, User, ScenarioThreadDistribution,
                       ProgressionStatus)
from ..HelperFunctions import get_thread_progression_state
from .. import data_blueprint


@data_blueprint.route('/admin/scenario_progress_stats/<int:scenario_id>', methods=['GET'])
@admin_required
def get_scenario_user_progress_stats(scenario_id):
    """Get detailed progress statistics for all users in a scenario"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.keycloak_user

    # check if scenario id is valid
    if not scenario_id:
        return jsonify({'error': 'Scenario id is missing'}), 400

    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        return jsonify({'error': 'Scenario does not exist'}), 404

    try:
        if not db.session.query(FeatureFunctionType).filter(
                FeatureFunctionType.function_type_id == scenario.function_type_id):
            return jsonify({'error': 'Function type does not exist'}), 503

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

            if scenario_user.role == ScenarioRoles.RATER:
                user_threads = (
                    db.session.query(ScenarioThreads)
                    .join(ScenarioThreadDistribution,
                          ScenarioThreadDistribution.scenario_thread_id == ScenarioThreads.id)
                    .join(ScenarioUsers, ScenarioThreadDistribution.scenario_user_id == ScenarioUsers.id)
                    .filter(ScenarioThreads.scenario_id == scenario_id,
                            ScenarioUsers.user_id == scenario_user.user_id)
                    .all()
                )
            else:
                user_threads = (
                    db.session.query(ScenarioThreads)
                    .filter(ScenarioThreads.scenario_id == scenario_id)
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

    except Exception as e:
        logging.error(e)
        return jsonify({"error": "Internal Server Error"}), 500
