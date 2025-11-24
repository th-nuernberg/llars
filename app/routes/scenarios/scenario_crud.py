"""
Scenario CRUD Operations
Handles basic Create, Read, Update, Delete operations for rating scenarios.
"""

import logging
from datetime import datetime
from flask import jsonify, request, g
from auth.decorators import admin_required
from db.db import db
from db.tables import (RatingScenarios, FeatureFunctionType, ScenarioUsers,
                       EmailThread, ScenarioThreads, ScenarioRoles, User,
                       ScenarioThreadDistribution)
from .. import data_blueprint
from .scenario_management import distribute_threads_to_users


@data_blueprint.route('/admin/scenarios', methods=['GET'])
@admin_required
def get_scenario_list():
    """Get list of all scenarios with their status"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    scenarios = RatingScenarios.query.all()

    if not scenarios:
        return jsonify({'scenarios': ['No scenarios available']}), 200

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

        formatted_scenario = {
            'scenario_id': scenario.id,
            'name': scenario.scenario_name,
            'function_type_id': scenario.function_type_id,
            'function_type_name': func_type if func_type else None,
            'begin_date': scenario.begin,
            'end_date': scenario.end,
            'status': status,
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
@admin_required
def get_scenario_details(scenario_id=None):
    """Get detailed information about a specific scenario"""
    try:
        # Authorization handled by @admin_required decorator
        # Current user available in g.authentik_user

        # check if scenario id is valid
        if not scenario_id:
            return jsonify({'error': 'Scenario id is missing'}), 400

        scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
        if not scenario:
            return jsonify({'error': 'Scenario does not exist'}), 404

        func_type = FeatureFunctionType.query.filter_by(function_type_id=scenario.function_type_id).first().name

        # get all users
        scenario_users = (db.session.query(ScenarioUsers).join(User, ScenarioUsers.user_id == User.id)
                          .filter(ScenarioUsers.scenario_id == scenario_id).all())

        # divide the users into the roles
        scenario_raters = []
        scenario_viewers = []
        for scenario_user in scenario_users:
            if scenario_user.role == ScenarioRoles.RATER:
                scenario_raters.append(
                    {
                        'user_id': scenario_user.user_id,
                        'username': scenario_user.user.username,
                        'role': scenario_user.role.value,
                    }
                )

            if scenario_user.role == ScenarioRoles.VIEWER:
                scenario_viewers.append(
                    {
                        'user_id': scenario_user.user_id,
                        'username': scenario_user.user.username,
                        'role': scenario_user.role.value,
                    }
                )

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
            'threads': threads,
            'raters': scenario_raters,
            'viewers': scenario_viewers,
        }
        return jsonify(scenario_details), 200
    except Exception as e:
        logging.exception(e)
        return jsonify({'error': "Internal Server Error"}), 500


@data_blueprint.route('/admin/create_scenario', methods=['POST'])
@admin_required
def create_scenario():
    """Create a new rating scenario with users and threads"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Invalid JSON'}), 400

    client_data = {
        "scenario_name": data.get('scenario_name'),
        "func_type_id": data.get('function_type_id'),
        "begin": data.get('begin'),
        "end": data.get('end'),
        "rater": data.get('rater'),
        "viewer": data.get("viewer"),
        "threads": data.get('threads')
    }

    for key, value in client_data.items():
        if value is None:
            return jsonify({'error': f'Missing value for {key}'}), 400

    # Validate function type
    function_type = FeatureFunctionType.query.filter_by(function_type_id=data.get('function_type_id')).first()
    if not function_type:
        return jsonify({'error': 'Invalid function type'}), 400

    function_type_id = function_type.function_type_id

    # Validate datetime
    try:
        begin = datetime.fromisoformat(data.get('begin'))
        end = datetime.fromisoformat(data.get('end'))
    except ValueError:
        return jsonify({'error': 'Timestamp format is invalid'}), 400

    if end < begin:
        return jsonify({'error': 'End date must be before begin'}), 400

    # Create new scenario
    new_scenario = RatingScenarios(
        scenario_name=client_data['scenario_name'],
        function_type_id=function_type_id,
        begin=begin,
        end=end,
    )

    rater_error_list = []
    viewer_error_list = []
    new_scenario_users = []
    seen_user = set()

    # Validate and collect raters
    if not isinstance(client_data['rater'], list):
        return jsonify({'error': 'rater is not a list'}), 400
    for user_id in client_data['rater']:
        if not isinstance(user_id, int):
            continue
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            rater_error_list.append(user_id)
            continue
        if user.id in seen_user:
            continue
        new_scenario_users.append({"id": user.id, "role": "Rater"})
        seen_user.add(user.id)

    # Validate and collect viewers
    if not isinstance(client_data['viewer'], list):
        return jsonify({'error': 'viewer is not a list'}), 400
    for user_id in client_data['viewer']:
        if not isinstance(user_id, int):
            continue
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            viewer_error_list.append(user_id)
            continue
        if user.id in seen_user:
            continue
        new_scenario_users.append({"id": user.id, "role": "Viewer"})
        seen_user.add(user.id)

    # Validate threads
    thread_error_list = []
    threads_for_scenario = []
    if not isinstance(client_data['threads'], list):
        return jsonify({'error': 'threads is not a list'}), 400
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
            if new_scenario_user.role == "Rater":
                scenario_rater.append(new_scenario_user.id)

        # Add threads
        scenario_threads = []
        for thread_id in threads_for_scenario:
            new_scenario_thread = ScenarioThreads(thread_id=thread_id, scenario_id=new_scenario.id)
            db.session.add(new_scenario_thread)
            db.session.flush()
            scenario_threads.append(new_scenario_thread.id)

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
        return jsonify({'error': f'Scenario couldn\'t be added: {e}'}), 500

    return_msg = {
        'notification': 'successfully created scenarios',
        'not_found_users': viewer_error_list + rater_error_list,
        'not_found_threads': thread_error_list,
    }
    return jsonify(return_msg), 200


@data_blueprint.route('/admin/delete_scenario/<int:scenario_id>', methods=['DELETE'])
@admin_required
def delete_scenario(scenario_id):
    """Delete a scenario and all associated records"""
    # Authorization handled by @admin_required decorator
    # Current user available in g.authentik_user

    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404

    try:
        db.session.delete(scenario)
        db.session.commit()
        return jsonify({"message": "Scenario and associated records deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@data_blueprint.route('/admin/edit_scenario', methods=['POST'])
@admin_required
def edit_scenario():
    """Edit an existing scenario's name and dates"""
    try:
        # Authorization handled by @admin_required decorator
        # Current user available in g.authentik_user

        try:
            data = request.get_json()
        except:
            return jsonify({'error': 'JSON not valid'}), 400

        client_data = {
            "id": data.get('id'),
            "name": data.get('new_name'),
            "begin": data.get('new_begin'),
            "end": data.get('new_end')
        }

        # Validate scenario ID
        if not client_data['id'] or (not isinstance(client_data['id'], int)):
            return jsonify({'error': 'id of scenario is missing or invalid'}), 400

        # Get existing scenario
        scenario = RatingScenarios.query.filter_by(id=client_data['id']).first()
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404

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
            return jsonify({'error': 'Start Date must be before the end date'}), 400

        # Update scenario
        try:
            scenario.scenario_name = client_data['name']
            scenario.begin = client_data['begin']
            scenario.end = client_data['end']
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(e)
            return jsonify({'error': 'Scenario couldn\'t be updated'}), 500

        return jsonify({'message': 'Scenario edited successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        logging.exception(e)
        return jsonify({'error': "internal Server error"}), 500
