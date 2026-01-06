"""
Scenario CRUD Operations
Handles basic Create, Read, Update, Delete operations for rating scenarios.

Ownership Rules:
- Admins can manage all scenarios
- Researchers can only manage scenarios they created (created_by field)
- Evaluators can only participate in scenarios they're assigned to
"""

import logging
from datetime import datetime
from flask import jsonify, request, g
from auth.decorators import admin_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, ForbiddenError
)
from decorators.permission_decorator import require_permission, has_role
from db.database import db
from db.tables import (RatingScenarios, FeatureFunctionType, ScenarioUsers,
                       EmailThread, ScenarioThreads, ScenarioRoles, User,
                       ScenarioThreadDistribution)
from .. import data_blueprint
from .scenario_utils import distribute_threads_to_users, check_scenario_ownership, is_scenario_owner
from ..HelperFunctions import (
    ALLOWED_DISTRIBUTION_MODES,
    ALLOWED_ORDER_MODES,
    DISTRIBUTION_MODE_ALL,
    get_scenario_distribution_mode,
)


@data_blueprint.route('/admin/scenarios', methods=['GET'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def get_scenario_list():
    """
    Get list of scenarios with their status.

    - Admins see all scenarios
    - Researchers see only their own scenarios (created_by)
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    is_admin = has_role(user, 'admin')

    # Admins see all, researchers see only their own
    if is_admin:
        scenarios = RatingScenarios.query.all()
    else:
        scenarios = RatingScenarios.query.filter_by(created_by=username).all()

    if not scenarios:
        return jsonify({'scenarios': []}), 200

    formatted_scenarios = {
        'scenarios': []
    }

    current_time = datetime.utcnow()
    for scenario in scenarios:
        func_type = FeatureFunctionType.query.filter_by(function_type_id=scenario.function_type_id).first().name

        if current_time > scenario.begin and current_time < scenario.end:
            status = 'aktiv'
        elif current_time > scenario.end and current_time > scenario.begin:
            status = 'beendet'
        elif current_time < scenario.begin and current_time < scenario.end:
            status = 'ausstehend'
        else:
            status = 'Fehlerhafte Start/Endzeit'

        # Count users by role
        user_count = ScenarioUsers.query.filter_by(scenario_id=scenario.id).count()

        formatted_scenario = {
            'scenario_id': scenario.id,
            'name': scenario.scenario_name,
            'function_type_id': scenario.function_type_id,
            'function_type_name': func_type if func_type else None,
            'begin_date': scenario.begin,
            'end_date': scenario.end,
            'status': status,
            'created_by': scenario.created_by,
            'user_count': user_count,
        }
        formatted_scenarios['scenarios'].append(formatted_scenario)

    status_order = {
        'ausstehend': 2,
        'aktiv': 1,
        'beendet': 3,
        'Fehlerhafte Start/Endzeit': 0
    }

    # Sort the scenarios based on the status order
    formatted_scenarios['scenarios'] = sorted(
        formatted_scenarios['scenarios'],
        key=lambda x: status_order.get(x['status'], 99)
    )

    return jsonify(formatted_scenarios), 200


@data_blueprint.route('/admin/scenarios/<int:scenario_id>', methods=['GET'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def get_scenario_details(scenario_id=None):
    """Get detailed information about a specific scenario"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    # check if scenario id is valid
    if not scenario_id:
        raise ValidationError('Scenario id is missing')

    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        raise NotFoundError('Scenario does not exist')

    func_type = FeatureFunctionType.query.filter_by(function_type_id=scenario.function_type_id).first().name

    # get all users
    scenario_users = (db.session.query(ScenarioUsers).join(User, ScenarioUsers.user_id == User.id)
                      .filter(ScenarioUsers.scenario_id == scenario_id).all())

    # divide the users into the roles
    scenario_raters = []
    scenario_evaluators = []
    scenario_owner = None
    for scenario_user in scenario_users:
        user_info = {
            'user_id': scenario_user.user_id,
            'username': scenario_user.user.username,
            'role': scenario_user.role.value,
        }

        if scenario_user.role == ScenarioRoles.OWNER:
            scenario_owner = user_info
        elif scenario_user.role == ScenarioRoles.RATER:
            scenario_raters.append(user_info)
        elif scenario_user.role == ScenarioRoles.EVALUATOR:
            scenario_evaluators.append(user_info)

    # get all the threads of the scenario
    scenario_threads = (db.session.query(ScenarioThreads)
                        .join(EmailThread, EmailThread.thread_id == ScenarioThreads.thread_id)
                        .filter(ScenarioThreads.scenario_id == scenario_id).all())
    threads = []
    for scenario_thread in scenario_threads:
        threads.append({
            'thread_id': scenario_thread.thread_id,
            'subject': scenario_thread.thread.subject,
            'chat_id': scenario_thread.thread.chat_id,
            'institut_id': scenario_thread.thread.institut_id,
            'sender': scenario_thread.thread.sender,
        })

    scenario_details = {
        'scenario_id': scenario_id,
        'scenario_name': scenario.scenario_name,
        'function_type_id': scenario.function_type_id,
        'func_type': func_type,
        'begin_date': scenario.begin.isoformat(),
        'end_date': scenario.end.isoformat(),
        'created_by': scenario.created_by,
        'llm1_model': getattr(scenario, 'llm1_model', None),
        'llm2_model': getattr(scenario, 'llm2_model', None),
        'config_json': getattr(scenario, 'config_json', None),
        'threads': threads,
        'owner': scenario_owner,
        'raters': scenario_raters,
        'evaluators': scenario_evaluators,
    }
    return jsonify(scenario_details), 200


@data_blueprint.route('/admin/create_scenario', methods=['POST'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def create_scenario():
    """
    Create a new rating scenario with users and threads.

    The creating user is automatically set as OWNER.
    """
    user = g.authentik_user
    creating_username = getattr(user, 'username', str(user))

    try:
        data = request.get_json()
    except (ValueError, TypeError) as e:
        raise ValidationError('Invalid JSON')

    config_json = data.get("config_json")
    if config_json is None:
        config_json = data.get("config")
    if config_json is not None and not isinstance(config_json, dict):
        raise ValidationError("config_json must be an object")
    if config_json is not None:
        distribution_mode = config_json.get("distribution_mode")
        order_mode = config_json.get("order_mode")
        if distribution_mode is not None and distribution_mode not in ALLOWED_DISTRIBUTION_MODES:
            raise ValidationError("Invalid distribution_mode")
        if order_mode is not None and order_mode not in ALLOWED_ORDER_MODES:
            raise ValidationError("Invalid order_mode")

    # Accept both 'evaluator' (new) and 'viewer' (legacy) field names
    evaluators_list = data.get('evaluator') or data.get('evaluators') or data.get('viewer') or []

    client_data = {
        "scenario_name": data.get('scenario_name'),
        "func_type_id": data.get('function_type_id'),
        "begin": data.get('begin'),
        "end": data.get('end'),
        "rater": data.get('rater') or data.get('raters') or [],
        "evaluator": evaluators_list,
        "threads": data.get('threads') or []
    }

    # Validate required fields
    if not client_data['scenario_name']:
        raise ValidationError('Missing value for scenario_name')
    if not client_data['func_type_id']:
        raise ValidationError('Missing value for function_type_id')
    if not client_data['begin']:
        raise ValidationError('Missing value for begin')
    if not client_data['end']:
        raise ValidationError('Missing value for end')

    # Validate function type
    function_type = FeatureFunctionType.query.filter_by(function_type_id=data.get('function_type_id')).first()
    if not function_type:
        raise ValidationError('Invalid function type')

    function_type_id = function_type.function_type_id

    # Validate datetime
    try:
        begin = datetime.fromisoformat(data.get('begin'))
        end = datetime.fromisoformat(data.get('end'))
    except ValueError:
        raise ValidationError('Timestamp format is invalid')

    if end < begin:
        raise ValidationError('End date must be before begin')

    # Create new scenario with created_by
    new_scenario = RatingScenarios(
        scenario_name=client_data['scenario_name'],
        function_type_id=function_type_id,
        begin=begin,
        end=end,
        created_by=creating_username,
        llm1_model=(str(data.get("llm1_model")).strip() if data.get("llm1_model") else None),
        llm2_model=(str(data.get("llm2_model")).strip() if data.get("llm2_model") else None),
        config_json=config_json,
    )

    rater_error_list = []
    evaluator_error_list = []
    new_scenario_users = []
    seen_user = set()

    # Add the creating user as OWNER
    creating_user = User.query.filter_by(username=creating_username).first()
    if creating_user:
        new_scenario_users.append({"id": creating_user.id, "role": ScenarioRoles.OWNER})
        seen_user.add(creating_user.id)

    # Validate and collect raters
    rater_list = client_data['rater']
    if not isinstance(rater_list, list):
        rater_list = []
    for user_id in rater_list:
        if not isinstance(user_id, int):
            continue
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            rater_error_list.append(user_id)
            continue
        if user.id in seen_user:
            continue
        new_scenario_users.append({"id": user.id, "role": ScenarioRoles.RATER})
        seen_user.add(user.id)

    # Validate and collect evaluators
    evaluator_list = client_data['evaluator']
    if not isinstance(evaluator_list, list):
        evaluator_list = []
    for user_id in evaluator_list:
        if not isinstance(user_id, int):
            continue
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            evaluator_error_list.append(user_id)
            continue
        if user.id in seen_user:
            continue
        new_scenario_users.append({"id": user.id, "role": ScenarioRoles.EVALUATOR})
        seen_user.add(user.id)

    # Validate threads
    thread_error_list = []
    threads_for_scenario = []
    if not isinstance(client_data['threads'], list):
        raise ValidationError('threads is not a list')
    for thread_id in client_data['threads']:
        if not isinstance(thread_id, int):
            continue
        thread = EmailThread.query.filter_by(thread_id=thread_id, function_type_id=function_type_id).first()
        if thread is None:
            thread_error_list.append(thread_id)
            continue
        threads_for_scenario.append(thread.thread_id)

    # Make the lists unique
    threads_for_scenario = list(set(threads_for_scenario))

    # Add to database
    try:
        # Add scenario and generate ID
        db.session.add(new_scenario)
        db.session.flush()

        # Add users
        scenario_rater = []
        for scenario_user in new_scenario_users:
            new_scenario_user = ScenarioUsers(
                scenario_id=new_scenario.id,
                user_id=scenario_user["id"],
                role=scenario_user["role"],
            )
            db.session.add(new_scenario_user)
            db.session.flush()
            if new_scenario_user.role == ScenarioRoles.RATER:
                scenario_rater.append(new_scenario_user.id)

        # Add threads
        scenario_threads = []
        for thread_id in threads_for_scenario:
            new_scenario_thread = ScenarioThreads(thread_id=thread_id, scenario_id=new_scenario.id)
            db.session.add(new_scenario_thread)
            db.session.flush()
            scenario_threads.append(new_scenario_thread.id)

        distribution_mode = get_scenario_distribution_mode(new_scenario, function_type_id)
        if distribution_mode != DISTRIBUTION_MODE_ALL:
            # Distribute threads to raters
            user_threads = distribute_threads_to_users(scenario_threads, scenario_rater)
            for key, value in user_threads.items():
                if key is not None:
                    if isinstance(value, list):
                        for thread_id in value:
                            db.session.add(ScenarioThreadDistribution(
                                scenario_id=new_scenario.id,
                                scenario_thread_id=thread_id,
                                scenario_user_id=key,
                            ))
                    else:
                        db.session.add(ScenarioThreadDistribution(
                            scenario_id=new_scenario.id,
                            scenario_thread_id=value,
                            scenario_user_id=key,
                        ))

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        raise Exception(f'Scenario couldn\'t be added: {e}')

    try:
        from services.system_event_service import SystemEventService

        SystemEventService.log_event(
            event_type="admin.scenario_created",
            severity="info",
            username=creating_username,
            entity_type="scenario",
            entity_id=str(new_scenario.id),
            message=f"Scenario '{new_scenario.scenario_name}' created by '{creating_username}'",
            details={
                "scenario_id": int(new_scenario.id),
                "function_type_id": int(function_type_id),
                "begin": begin.isoformat(),
                "end": end.isoformat(),
                "raters": len(rater_list),
                "evaluators": len(evaluator_list),
                "threads": len(threads_for_scenario),
            },
        )
    except Exception:
        pass

    return_msg = {
        'notification': 'successfully created scenario',
        'scenario_id': new_scenario.id,
        'created_by': creating_username,
        'not_found_users': evaluator_error_list + rater_error_list,
        'not_found_threads': thread_error_list,
    }
    return jsonify(return_msg), 201


@data_blueprint.route('/admin/delete_scenario/<int:scenario_id>', methods=['DELETE'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def delete_scenario(scenario_id):
    """
    Delete a scenario and all associated records.

    Only the scenario owner or admin can delete.
    """
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError('Scenario not found')

    # Check ownership - raises ForbiddenError if not authorized
    check_scenario_ownership(scenario, g.authentik_user)

    try:
        scenario_name = getattr(scenario, "scenario_name", None)
        db.session.delete(scenario)
        db.session.commit()
        try:
            from services.system_event_service import SystemEventService

            acting_username = getattr(g.authentik_user, "username", None) or str(g.authentik_user)
            SystemEventService.log_event(
                event_type="admin.scenario_deleted",
                severity="warning",
                username=acting_username,
                entity_type="scenario",
                entity_id=str(scenario_id),
                message=f"Scenario '{scenario_name or scenario_id}' deleted by '{acting_username}'",
                details={"scenario_id": int(scenario_id), "scenario_name": scenario_name},
            )
        except Exception:
            pass
        return jsonify({"message": "Scenario and associated records deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        raise


@data_blueprint.route('/admin/edit_scenario', methods=['POST'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenarios')
def edit_scenario():
    """
    Edit an existing scenario's name and dates.

    Only the scenario owner or admin can edit.
    """
    try:
        data = request.get_json()
    except (ValueError, TypeError) as e:
        raise ValidationError('JSON not valid')

    client_data = {
        "id": data.get('id'),
        "name": data.get('new_name'),
        "begin": data.get('new_begin'),
        "end": data.get('new_end')
    }

    # Validate scenario ID
    if not client_data['id'] or (not isinstance(client_data['id'], int)):
        raise ValidationError('id of scenario is missing or invalid')

    # Get existing scenario
    scenario = RatingScenarios.query.filter_by(id=client_data['id']).first()
    if not scenario:
        raise NotFoundError('Scenario not found')

    # Check ownership - raises ForbiddenError if not authorized
    check_scenario_ownership(scenario, g.authentik_user)

    # Use existing values if new ones not provided
    if not client_data['name']:
        client_data['name'] = scenario.scenario_name
    if not client_data['begin']:
        client_data['begin'] = scenario.begin
    else:
        client_data['begin'] = datetime.fromisoformat(client_data['begin'])
    if not client_data['end']:
        client_data['end'] = scenario.end
    else:
        client_data['end'] = datetime.fromisoformat(client_data['end'])

    # Validate dates
    if client_data['begin'] >= client_data['end']:
        raise ValidationError('Start Date must be before the end date')

    # Update scenario
    try:
        old_name = scenario.scenario_name
        old_begin = scenario.begin.isoformat() if getattr(scenario, "begin", None) else None
        old_end = scenario.end.isoformat() if getattr(scenario, "end", None) else None

        scenario.scenario_name = client_data['name']
        scenario.begin = client_data['begin']
        scenario.end = client_data['end']
        db.session.commit()

        try:
            from services.system_event_service import SystemEventService

            acting_username = getattr(g.authentik_user, "username", None) or str(g.authentik_user)
            SystemEventService.log_event(
                event_type="admin.scenario_updated",
                severity="info",
                username=acting_username,
                entity_type="scenario",
                entity_id=str(scenario.id),
                message=f"Scenario '{scenario.id}' updated by '{acting_username}'",
                details={
                    "scenario_id": int(scenario.id),
                    "old": {"name": old_name, "begin": old_begin, "end": old_end},
                    "new": {
                        "name": scenario.scenario_name,
                        "begin": scenario.begin.isoformat() if getattr(scenario, "begin", None) else None,
                        "end": scenario.end.isoformat() if getattr(scenario, "end", None) else None,
                    },
                },
            )
        except Exception:
            pass
    except Exception as e:
        db.session.rollback()
        raise

    return jsonify({'message': 'Scenario edited successfully'}), 200
