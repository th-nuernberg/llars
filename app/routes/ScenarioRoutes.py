import logging
import traceback
from numbers import Number
from pyexpat.errors import messages
from sre_constants import error
from tokenize import group
from unicodedata import category

from . import data_blueprint, auth_blueprint
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash
from werkzeug.exceptions import BadRequest

from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating, UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating,
                       UserGroup, UserPrompt, UserPromptShare,
                       ConsultingCategoryType, UserConsultingCategorySelection, RatingScenarios, ScenarioUsers, ScenarioThreadDistribution, ScenarioThreads, ScenarioRoles, ProgressionStatus, ComparisonSession)
from sqlalchemy import func
from uuid import uuid4
import uuid
from datetime import datetime
import json
import random
from .HelperFunctions import get_thread_progression_state
from pathlib import Path

BASE_DIR = Path(__file__).parent
PERSONAS_PATH = BASE_DIR / '../static/vikl-personas.json'



@data_blueprint.route('/admin/scenarios', methods=['GET'])
def get_scenario_list():
    # Authorization
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    admin_user = User.query.filter_by(api_key=api_key).first()
    if not admin_user:
        return jsonify({'error': 'Invalid API key'}), 401

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
            status =  'aktiv'
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
def get_scenario_details(scenario_id=None): #
    try:
        # Authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        admin_user = User.query.filter_by(api_key=api_key).first()
        if not admin_user:
            return jsonify({'error': 'Invalid API key'}), 401

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
                'chat_id':  scenario_thread.thread.chat_id,
                'institut_id':  scenario_thread.thread.institut_id,
                'sender':  scenario_thread.thread.sender,
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



@data_blueprint.route('/admin/create_scenario', methods=['POST']) # TODO: Gedanken zu Zeitzonen machen
def create_scenario():
    # Authorization
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    admin_user = User.query.filter_by(api_key=api_key).first()
    if not admin_user:
        return jsonify({'error': 'Invalid API key'}), 401

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
        "viewer" : data.get("viewer"),
        "threads": data.get('threads')
    }

    for key, value in client_data.items():
        if value is None:
            return jsonify({'error': f'Missing value for {key}'}), 400

    ### check values ###
    # function type
    function_type = FeatureFunctionType.query.filter_by(function_type_id=data.get('function_type_id')).first()
    if not function_type:
        return jsonify({'error': 'Invalid function type'}), 400

    function_type_id = function_type.function_type_id

    #datetime
    try:
        begin = datetime.fromisoformat(data.get('begin'))
        end = datetime.fromisoformat(data.get('end'))
    except ValueError:
        return jsonify({'error': 'Timestamp format is invalid'}), 400

    if end < begin:
        return jsonify({'error': 'End date must be before begin'}), 400

    ## new scenario
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

    # For Raters
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
        new_scenario_users.append({"id": user.id, "role": "Rater" })
        seen_user.add(user.id)

    # For Viewers
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

    #threads
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
    # make the lists unique
    threads_for_scenario = list(set(threads_for_scenario))

    ### add to db
    try:
        # Szenario hinzufügen und ID generieren
        db.session.add(new_scenario)
        db.session.flush()

        # Nutzer hinzufügen
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

        # Threads hinzufügen
        scenario_threads = []
        for thread_id in threads_for_scenario:
            new_scenario_thread = ScenarioThreads(thread_id=thread_id, scenario_id=new_scenario.id)
            db.session.add(new_scenario_thread)
            db.session.flush()  # ID für new_scenario_thread wird generiert
            scenario_threads.append(new_scenario_thread.id)

        # add thread distribution
        user_threads = distribute_threads_to_users(scenario_threads, scenario_rater)
        for key, value in user_threads.items():
            if key is not None:
                if isinstance(value, list):  # Mehrere Threads für einen User
                    for thread_id in value:
                        db.session.add(ScenarioThreadDistribution(
                            scenario_id=new_scenario.id,
                            scenario_thread_id=thread_id,
                            scenario_user_id=key,
                        ))
                else:  # Einzelner Thread für einen User
                    db.session.add(ScenarioThreadDistribution(
                        scenario_id=new_scenario.id,
                        scenario_thread_id=value,
                        scenario_user_id=key,
                    ))

        # Finaler Commit
        db.session.commit()

        # Für Vergleiche: Sessions für alle Personas
        if function_type.name == 'comparison':
            create_comparison_sessions_for_scenario(new_scenario.id)

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
def delete_scenario(scenario_id):
    # Authorization
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    admin_user = User.query.filter_by(api_key=api_key).first()
    if not admin_user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Versuche, das Szenario zu finden
    scenario = RatingScenarios.query.get(scenario_id)

    # Wenn das Szenario nicht gefunden wurde, gib einen Fehler zurück
    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404

    # Lösche das Szenario und alle zugehörigen Datensätze
    try:
        db.session.delete(scenario)  # Lösche das Szenario
        db.session.commit()  # Bestätige die Änderungen
        return jsonify({"message": "Scenario and associated records deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()  # Bei Fehlern rollback
        return jsonify({"error": str(e)}), 500



@data_blueprint.route('/admin/edit_scenario', methods=['POST']) # TODO: Gedanken zu Zeitzonen machen
def edit_scenario():
    try:
        # Authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        admin_user = User.query.filter_by(api_key=api_key).first()
        if not admin_user:
            return jsonify({'error': 'Invalid API key'}), 401
        if admin_user.group.name != 'Admin':
            return jsonify({'error': 'You do not have administration rights'}), 403

        # get the data
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
        # validate the data
        if not client_data['id'] or (not isinstance(client_data['id'], int)):
            return jsonify({'error': 'id of scenario is missing or invalid'}), 400

        # if no value to change is given, use the given value of db for the update clause
        scenario = RatingScenarios.query.filter_by(id=client_data['id']).first()
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

        # check if dates are in order
        if client_data['begin'] >= client_data['end']:
            return jsonify({'error': 'Stat Date must be before the endDdate'}), 400
        # update changes to db
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




@data_blueprint.route('/admin/add_threads_to_scenario', methods=['POST'])
def add_threads_to_scenario():
    try:
        # Authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        admin_user = User.query.filter_by(api_key=api_key).first()
        if not admin_user:
            return jsonify({'error': 'Invalid API key'}), 401
        if admin_user.group.name != 'Admin':
            return jsonify({'error': 'You do not have administration rights'}), 403

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
        return jsonify({'error': "internal Server errror"}), 500


@data_blueprint.route('/admin/add_viewers_to_scenario', methods=['POST'])
def add_viewers_to_scenario():
    try:
        # Authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        admin_user = User.query.filter_by(api_key=api_key).first()
        if not admin_user:
            return jsonify({'error': 'Invalid API key'}), 401
        if admin_user.group.name != 'Admin':
            return jsonify({'error': 'You do not have administration rights'}), 403

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
            if not scenario_user: # only add new users to scenario
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



@data_blueprint.route('/admin/get_function_types', methods=['GET'])
def get_function_types():
    try:
        # Authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        admin_user = User.query.filter_by(api_key=api_key).first()
        if not admin_user:
            return jsonify({'error': 'Invalid API key'}), 401
        if admin_user.group.name != 'Admin':
            return jsonify({'error': 'You do not have administration rights'}), 403

        feature_function_types = FeatureFunctionType.query.all()
        function_types = []
        for feature_function_type in feature_function_types:
            function_types.append({
                'function_type_id': feature_function_type.function_type_id,
                'name': feature_function_type.name,
            })

        return jsonify(function_types), 200

    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Internal Server Error'}), 500


@data_blueprint.route('/admin/get_users', methods=['GET'])
def get_users():
    try:
        # Authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        admin_user = User.query.filter_by(api_key=api_key).first()
        if not admin_user:
            return jsonify({'error': 'Invalid API key'}), 401
        if admin_user.group.name != 'Admin':
            return jsonify({'error': 'You do not have administration rights'}), 403

        db_users = (db.session.query(User).join(UserGroup, User.group_id == UserGroup.id)
                 .filter(UserGroup.name != "Admin").all())

        users = []
        for db_user in db_users:
            users.append({
                'id': db_user.id,
                'name': db_user.username,
            })
        return jsonify(users), 200

    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Internal Server Error'}), 500


@data_blueprint.route('/admin/get_threads_from_function_type/<int:function_type_id>', methods=['GET'])
def get_threads(function_type_id):
    try:
        # Authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        admin_user = User.query.filter_by(api_key=api_key).first()
        if not admin_user:
            return jsonify({'error': 'Invalid API key'}), 401
        if admin_user.group.name != 'Admin':
            return jsonify({'error': 'You do not have administration rights'}), 403

        validated_function_type = FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()

        if validated_function_type is None:
            return jsonify({'error': 'Function type not found'}), 404

        db_threads = EmailThread.query.filter_by(function_type_id=validated_function_type.function_type_id).all()
        threads = []
        for thread in db_threads:
            threads.append({
                'thread_id': thread.thread_id,
                'chat_id': thread.chat_id,
                'institut_id': thread.institut_id,
                'subject': thread.subject,
                'sender': thread.sender,
            })

        return jsonify(threads), 200
    except Exception as e:
        logging.error(e)
        return jsonify({'error': 'Internal Server Error'}), 500



@data_blueprint.route('/admin/scenario_progress_stats/<int:scenario_id>', methods=['GET'])
def get_scenario_user_progress_stats(scenario_id):
    # Authorization
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 401

    admin_user = User.query.filter_by(api_key=api_key).first()
    if not admin_user:
        return jsonify({'error': 'Invalid API key'}), 401
    if admin_user.group.name != 'Admin':
        return jsonify({'error': 'You do not have administration rights'}), 403

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

                progression_state = get_thread_progression_state(thread=thread, user_id=scenario_user.user_id, function_type_id=scenario.function_type_id)

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

########################################################################################################################
# Helper Functions
########################################################################################################################

def distribute_threads_to_users(thread_ids, user_ids):
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


def create_comparison_sessions_for_scenario(scenario_id):
    try:
        personas = json.loads(PERSONAS_PATH.read_text())
        
        rater_users = db.session.query(ScenarioUsers).filter_by(
            scenario_id=scenario_id, 
            role=ScenarioRoles.RATER
        ).all()
        
        for rater_user in rater_users:
            for persona in personas:
                persona_props = json.loads(persona['properties'])
                persona_json = {
                    "name": persona['name'],
                    "properties": persona_props,
                }
                
                session = ComparisonSession(
                    scenario_id=scenario_id,
                    user_id=rater_user.user_id,
                    persona_json=persona_json,
                    persona_name=persona['name']
                )
                db.session.add(session)
        
        db.session.commit()
    except Exception as e:
        logging.error(f"Error creating comparison sessions: {e}")
        db.session.rollback()
        raise


