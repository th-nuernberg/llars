"""
Scenario Management Operations
Handles thread distribution and user assignment to scenarios.
"""

import logging
import random
from flask import jsonify, request, g
from werkzeug.exceptions import BadRequest
from auth.decorators import admin_required
from db.db import db
from db.tables import (RatingScenarios, EmailThread, ScenarioThreads,
                       ScenarioUsers, ScenarioRoles, ScenarioThreadDistribution)
from .. import data_blueprint


@data_blueprint.route('/admin/add_threads_to_scenario', methods=['POST'])
@admin_required
def add_threads_to_scenario():
    """Add threads to an existing scenario and distribute them to raters"""
    try:
        # Authorization handled by @admin_required decorator
        # Current user available in g.keycloak_user

        try:
            data = request.get_json()
        except BadRequest:
            return jsonify({'error': 'Invalid JSON format'}), 400

        # Validate scenario_id
        scenario_id = data.get('scenario_id')
        if scenario_id is None or not isinstance(scenario_id, int):
            return jsonify({'error': 'Scenario id is missing or invalid'}), 400

        scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404

        # Validate threads
        threads = data.get('thread_ids')
        if not threads or not all(isinstance(thread_id, int) for thread_id in threads):
            return jsonify({'error': 'List of thread ids is missing or contains invalid entries'}), 400

        validated_threads = []
        failed_threads = []
        for thread_id in threads:
            thread = EmailThread.query.filter_by(thread_id=thread_id,
                                                 function_type_id=scenario.function_type_id).first()
            if thread is None:
                failed_threads.append(thread_id)
            else:
                # check if thread already belongs to scenario (no duplicates allowed in db)
                if not ScenarioThreads.query.filter_by(thread_id=thread_id,
                                                       scenario_id=scenario_id).first():
                    validated_threads.append(thread.thread_id)

        # Add threads and distribute
        try:
            thread_scenarios = []
            for thread_id in validated_threads:
                new_scenario_thread = ScenarioThreads(scenario_id=scenario.id, thread_id=thread_id)
                db.session.add(new_scenario_thread)
                db.session.flush()
                thread_scenarios.append(new_scenario_thread.id)

            scenario_users_ids = [
                user_id[0] for user_id in ScenarioUsers.query.with_entities(ScenarioUsers.id).filter_by(
                    scenario_id=scenario.id, role=ScenarioRoles.RATER).all()
            ]

            if not thread_scenarios or not scenario_users_ids:
                return jsonify({'error': 'No threads or users available for distribution'}), 400

            user_threads = distribute_threads_to_users(thread_scenarios, scenario_users_ids)
            for user_id, thread_ids in user_threads.items():
                for thread_id in thread_ids:
                    db.session.add(ScenarioThreadDistribution(
                        scenario_id=scenario.id,
                        scenario_thread_id=thread_id,
                        scenario_user_id=user_id,
                    ))

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error while adding threads to scenario: {e}")
            return jsonify({'error': 'An error occurred while adding the threads to the db'}), 500

        return jsonify({'message': 'Successfully added threads to the db', 'not_found_threads': failed_threads}), 200
    except Exception as e:
        logging.error(e)
        logging.exception(e)
        return jsonify({'error': "internal Server error"}), 500


@data_blueprint.route('/admin/add_viewers_to_scenario', methods=['POST'])
@admin_required
def add_viewers_to_scenario():
    """Add or update viewers for a scenario"""
    try:
        # Authorization handled by @admin_required decorator
        # Current user available in g.keycloak_user

        try:
            data = request.get_json()
        except BadRequest:
            return jsonify({'error': 'Invalid JSON format'}), 400

        # Validate scenario_id
        scenario_id = data.get('scenario_id')
        if scenario_id is None or not isinstance(scenario_id, int):
            return jsonify({'error': 'Scenario id is missing or invalid'}), 400

        scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404

        viewers = data.get('user_ids')
        if not viewers or not all(isinstance(user_id, int) for user_id in viewers):
            return jsonify({'error': 'List of viewers is missing or contains invalid entries'}), 400

        for viewer_id in viewers:
            scenario_user = ScenarioUsers.query.filter_by(user_id=viewer_id, scenario_id=scenario_id).first()
            if not scenario_user:  # only add new users to scenario
                db.session.add(ScenarioUsers(user_id=viewer_id, scenario_id=scenario_id, role=ScenarioRoles.VIEWER))
                db.session.commit()
            else:
                scenario_user.role = ScenarioRoles.VIEWER
                db.session.commit()

        return jsonify({'message': 'Successfully added viewers to the db'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify({'error': 'Internal Server Error'}), 500


def distribute_threads_to_users(thread_ids, user_ids):
    """
    Distribute threads to users in a round-robin fashion.

    Args:
        thread_ids: List of thread IDs to distribute
        user_ids: List of user IDs to receive threads

    Returns:
        Dictionary mapping user_id to list of thread_ids
    """
    if not thread_ids or not user_ids:
        return {}

    # Randomize the thread IDs to ensure a random distribution
    random.shuffle(thread_ids)
    random.shuffle(user_ids)

    # Create a dictionary to store the distribution
    user_threads = {user_id: [] for user_id in user_ids}

    # Distribute the threads round-robin style
    for i, thread_id in enumerate(thread_ids):
        user_id = user_ids[i % len(user_ids)]
        user_threads[user_id].append(thread_id)

    return user_threads
