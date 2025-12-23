"""
Scenario Management Operations
Handles thread distribution and user assignment to scenarios.
"""

import logging
import random
from flask import jsonify, request, g
from werkzeug.exceptions import BadRequest
from auth.decorators import admin_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from db.db import db
from db.tables import (RatingScenarios, EmailThread, ScenarioThreads,
                       ScenarioUsers, ScenarioRoles, ScenarioThreadDistribution)
from .. import data_blueprint
from ..HelperFunctions import get_scenario_distribution_mode, DISTRIBUTION_MODE_ALL


@data_blueprint.route('/admin/add_threads_to_scenario', methods=['POST'])
@admin_required
@handle_api_errors(logger_name='scenarios')
def add_threads_to_scenario():
    """Add threads to an existing scenario and distribute them to raters"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    try:
        data = request.get_json()
    except BadRequest:
        raise ValidationError('Invalid JSON format')

    # Validate scenario_id
    scenario_id = data.get('scenario_id')
    if scenario_id is None or not isinstance(scenario_id, int):
        raise ValidationError('Scenario id is missing or invalid')

    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        raise NotFoundError('Scenario not found')

    # Validate threads
    threads = data.get('thread_ids')
    if not threads or not all(isinstance(thread_id, int) for thread_id in threads):
        raise ValidationError('List of thread ids is missing or contains invalid entries')

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

        distribution_mode = get_scenario_distribution_mode(scenario, scenario.function_type_id)

        if not thread_scenarios:
            raise ValidationError('No threads available for distribution')

        if distribution_mode != DISTRIBUTION_MODE_ALL and not scenario_users_ids:
            raise ValidationError('No users available for distribution')

        if distribution_mode != DISTRIBUTION_MODE_ALL:
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
        raise

    return jsonify({'message': 'Successfully added threads to the db', 'not_found_threads': failed_threads}), 200


@data_blueprint.route('/admin/add_viewers_to_scenario', methods=['POST'])
@admin_required
@handle_api_errors(logger_name='scenarios')
def add_viewers_to_scenario():
    """Add or update viewers for a scenario"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    try:
        data = request.get_json()
    except BadRequest:
        raise ValidationError('Invalid JSON format')

    # Validate scenario_id
    scenario_id = data.get('scenario_id')
    if scenario_id is None or not isinstance(scenario_id, int):
        raise ValidationError('Scenario id is missing or invalid')

    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        raise NotFoundError('Scenario not found')

    viewers = data.get('user_ids')
    if not viewers or not all(isinstance(user_id, int) for user_id in viewers):
        raise ValidationError('List of viewers is missing or contains invalid entries')

    for viewer_id in viewers:
        scenario_user = ScenarioUsers.query.filter_by(user_id=viewer_id, scenario_id=scenario_id).first()
        if not scenario_user:  # only add new users to scenario
            db.session.add(ScenarioUsers(user_id=viewer_id, scenario_id=scenario_id, role=ScenarioRoles.VIEWER))
            db.session.commit()
        else:
            scenario_user.role = ScenarioRoles.VIEWER
            db.session.commit()

    return jsonify({'message': 'Successfully added viewers to the db'}), 200


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
