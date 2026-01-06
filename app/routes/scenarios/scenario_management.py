"""
Scenario Management Operations
Handles thread distribution and user assignment to scenarios.

Supports both admin and researcher access:
- Admins can manage all scenarios
- Researchers can manage only their own scenarios (via check_scenario_ownership)
"""

import logging
from flask import jsonify, request, g
from werkzeug.exceptions import BadRequest
from auth.decorators import admin_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, ForbiddenError
)
from decorators.permission_decorator import require_permission, has_role
from db.database import db
from db.tables import (RatingScenarios, EmailThread, ScenarioThreads,
                       ScenarioUsers, ScenarioRoles, ScenarioThreadDistribution, User)
from .. import data_blueprint
from ..HelperFunctions import get_scenario_distribution_mode, DISTRIBUTION_MODE_ALL
from .scenario_utils import check_scenario_ownership, distribute_threads_to_users


@data_blueprint.route('/admin/add_threads_to_scenario', methods=['POST'])
@require_permission('data:manage_scenarios')
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
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def add_viewers_to_scenario():
    """
    Add or update evaluators for a scenario (legacy endpoint, uses 'viewer' for compatibility).

    Deprecated: Use /admin/invite_users_to_scenario instead.
    """
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

    # Check ownership
    check_scenario_ownership(scenario, g.authentik_user)

    viewers = data.get('user_ids')
    if not viewers or not all(isinstance(user_id, int) for user_id in viewers):
        raise ValidationError('List of viewers is missing or contains invalid entries')

    for viewer_id in viewers:
        scenario_user = ScenarioUsers.query.filter_by(user_id=viewer_id, scenario_id=scenario_id).first()
        if not scenario_user:  # only add new users to scenario
            db.session.add(ScenarioUsers(user_id=viewer_id, scenario_id=scenario_id, role=ScenarioRoles.EVALUATOR))
            db.session.commit()
        else:
            scenario_user.role = ScenarioRoles.EVALUATOR
            db.session.commit()

    return jsonify({'message': 'Successfully added evaluators to the db'}), 200


@data_blueprint.route('/admin/invite_users_to_scenario', methods=['POST'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def invite_users_to_scenario():
    """
    Invite users to a scenario with a specific role.

    Only the scenario owner or admin can invite users.

    Request body:
        {
            "scenario_id": 123,
            "users": [
                {"user_id": 1, "role": "rater"},
                {"user_id": 2, "role": "evaluator"}
            ]
        }

    Roles:
        - "rater": Can rate/rank items in the scenario
        - "evaluator": Can view and participate in evaluations
    """
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

    # Check ownership - raises ForbiddenError if not authorized
    check_scenario_ownership(scenario, g.authentik_user)

    users_to_invite = data.get('users', [])
    if not users_to_invite:
        raise ValidationError('No users provided')

    added_users = []
    updated_users = []
    failed_users = []

    for user_data in users_to_invite:
        user_id = user_data.get('user_id')
        role_str = user_data.get('role', 'evaluator').lower()

        if not isinstance(user_id, int):
            failed_users.append({'user_id': user_id, 'reason': 'Invalid user_id'})
            continue

        # Validate user exists
        user = User.query.filter_by(id=user_id).first()
        if not user:
            failed_users.append({'user_id': user_id, 'reason': 'User not found'})
            continue

        # Map role string to enum
        if role_str == 'rater':
            role = ScenarioRoles.RATER
        elif role_str in ('evaluator', 'viewer'):  # Accept 'viewer' for backwards compat
            role = ScenarioRoles.EVALUATOR
        else:
            failed_users.append({'user_id': user_id, 'reason': f'Invalid role: {role_str}'})
            continue

        # Check if user already in scenario
        scenario_user = ScenarioUsers.query.filter_by(user_id=user_id, scenario_id=scenario_id).first()

        if not scenario_user:
            # Add new user
            db.session.add(ScenarioUsers(user_id=user_id, scenario_id=scenario_id, role=role))
            added_users.append({'user_id': user_id, 'username': user.username, 'role': role.value})
        else:
            # Update existing user's role (unless they're OWNER)
            if scenario_user.role != ScenarioRoles.OWNER:
                scenario_user.role = role
                updated_users.append({'user_id': user_id, 'username': user.username, 'role': role.value})

    db.session.commit()

    return jsonify({
        'message': 'Users invited successfully',
        'added': added_users,
        'updated': updated_users,
        'failed': failed_users
    }), 200


@data_blueprint.route('/admin/remove_user_from_scenario', methods=['POST'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def remove_user_from_scenario():
    """
    Remove a user from a scenario.

    Only the scenario owner or admin can remove users.
    Cannot remove the scenario owner.

    Request body:
        {
            "scenario_id": 123,
            "user_id": 456
        }
    """
    try:
        data = request.get_json()
    except BadRequest:
        raise ValidationError('Invalid JSON format')

    scenario_id = data.get('scenario_id')
    user_id = data.get('user_id')

    if not scenario_id or not isinstance(scenario_id, int):
        raise ValidationError('Scenario id is missing or invalid')
    if not user_id or not isinstance(user_id, int):
        raise ValidationError('User id is missing or invalid')

    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        raise NotFoundError('Scenario not found')

    # Check ownership
    check_scenario_ownership(scenario, g.authentik_user)

    # Find the scenario user
    scenario_user = ScenarioUsers.query.filter_by(user_id=user_id, scenario_id=scenario_id).first()
    if not scenario_user:
        raise NotFoundError('User not found in scenario')

    # Cannot remove owner
    if scenario_user.role == ScenarioRoles.OWNER:
        raise ValidationError('Cannot remove the scenario owner')

    # Also remove any thread distributions for this user
    ScenarioThreadDistribution.query.filter_by(
        scenario_id=scenario_id,
        scenario_user_id=scenario_user.id
    ).delete()

    db.session.delete(scenario_user)
    db.session.commit()

    return jsonify({'message': 'User removed from scenario successfully'}), 200


@data_blueprint.route('/admin/available_users_for_scenario', methods=['GET'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def get_available_users_for_scenario():
    """
    Get list of users that can be invited to scenarios.

    Query params:
        - scenario_id (optional): If provided, excludes users already in this scenario

    Returns list of users with their ID, username, and current roles.
    """
    scenario_id = request.args.get('scenario_id', type=int)

    # Get all active users
    users = User.query.filter(
        User.deleted_at.is_(None),
        User.is_active == True
    ).all()

    result = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
        }

        # If scenario_id provided, check if user is already in scenario
        if scenario_id:
            scenario_user = ScenarioUsers.query.filter_by(
                user_id=user.id,
                scenario_id=scenario_id
            ).first()
            if scenario_user:
                user_data['in_scenario'] = True
                user_data['scenario_role'] = scenario_user.role.value
            else:
                user_data['in_scenario'] = False

        result.append(user_data)

    return jsonify({'users': result}), 200
