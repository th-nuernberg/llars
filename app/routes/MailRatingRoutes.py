import traceback
from venv import logger
import logging
from . import data_blueprint, auth_blueprint
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash
from werkzeug.exceptions import BadRequest

from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating, UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       UserGroup, UserPrompt, UserPromptShare,
                       ConsultingCategoryType, UserConsultingCategorySelection, RatingScenarios, ScenarioUsers, ScenarioThreadDistribution, ScenarioThreads, ScenarioRoles, ProgressionStatus)
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import joinedload
from uuid import uuid4
import uuid
from datetime import datetime
import json
import random

from .HelperFunctions import get_user_threads, can_access_thread


# Get the Thread for the Rating
@data_blueprint.route('/email_threads/generations/<int:thread_id>', methods=['GET'])
def get_email_thread_details(thread_id):
    try:
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # Hole den E-Mail-Thread basierend auf der thread_id
        email_thread = EmailThread.query.filter_by(thread_id=thread_id).first()
        if not email_thread:
            return jsonify({'error': 'Email thread not found'}), 404

        # Hole alle Nachrichten in diesem E-Mail-Thread
        messages = Message.query.filter_by(thread_id=email_thread.thread_id).all()

        if not messages:
            return jsonify({'error': 'No messages found for this thread'}), 404

        # Erstelle eine Liste von Nachrichten, die zurückgegeben werden soll
        messages_data = [
            {
                'message_id': msg.message_id,
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages
        ]

        return jsonify({'messages': messages_data}), 200
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal Server Error"}), 500


# get meta_data of all assigned threads
@data_blueprint.route('/email_threads/mailhistory_ratings', methods=['GET'])
def list_email_threads_for_mail_ratings():
    try:
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        # get user
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # get function type
        mail_rating_function_type = FeatureFunctionType.query.filter_by(name='mail_rating').first().function_type_id
        if not mail_rating_function_type:
            return jsonify({'error': 'Mail Rating function type not found'}), 404

        # get all threads the user is supposed to see
        accessible_threads = get_user_threads(user.id, mail_rating_function_type)

        threads_list = [] # this is for returning
        seen_threads = set() # Avoiding duplicate Threads
        for thread in accessible_threads:
            #check for duplicates
            if thread.thread_id in seen_threads:
                continue
            seen_threads.add(thread.thread_id)

            # Check for existing UserMailHistoryRating for the user and thread
            mail_rating = (
                db.session.query(UserMailHistoryRating)
                .filter_by(user_id=user.id, thread_id=thread.thread_id).order_by(
                UserMailHistoryRating.timestamp.desc()).first()
                .first()
            )

            # Determine progression status
            status = mail_rating.status if mail_rating else ProgressionStatus.NOT_STARTED

            # Append thread details to the result list
            threads_list.append({
                'thread_id': thread.thread_id,
                'chat_id': thread.chat_id,
                'institut_id': thread.institut_id,
                'subject': thread.subject,
                'sender': thread.sender,
                'progression_status': status.value,
            })

        return jsonify({'threads': threads_list}), 200

    except Exception as e:
        logging.exception(e)
        return jsonify({'error': str(e)}), 500


# get the most recent mail history ratings of the user
@data_blueprint.route('/email_threads/mailhistory_ratings/<int:thread_id>', methods=['GET'])
def get_mail_rating(thread_id):
    try:
        # authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401


        # check if user can access thread
        if not can_access_thread(user.id, thread_id, 3):
            return jsonify({'error': 'Access denied'}), 401

        ### Start of Logik ###
        # retrieve the most recent mail history(thread) rating of user
        mail_rating = UserMailHistoryRating.query.filter_by(user_id=user.id, thread_id=thread_id).order_by(
            UserMailHistoryRating.timestamp.desc()).first()
        selected_consulting_category = UserConsultingCategorySelection.query.filter_by(user_id=user.id,
                                                                                       thread_id=thread_id).order_by(
            UserConsultingCategorySelection.timestamp.desc()).first()
        if selected_consulting_category:
            consulting_category = ConsultingCategoryType.query.filter_by(
                id=selected_consulting_category.consulting_category_type_id).first()
        else:
            consulting_category = None

        # prepare data for json format (if no rating found use null values)
        rating_data = {
            'rating': {
                'counsellor_coherence_rating': mail_rating.counsellor_coherence_rating if mail_rating else None,
                'client_coherence_rating': mail_rating.client_coherence_rating if mail_rating else None,
                'quality_rating': mail_rating.quality_rating if mail_rating else None,
                'overall_rating': mail_rating.overall_rating if mail_rating else None,
                'feedback': mail_rating.feedback if mail_rating else None,
                'rating_status': mail_rating.status.value if mail_rating else ProgressionStatus.NOT_STARTED.value,
            },
            "consulting_category": {
                "consulting_category_type_id": consulting_category.id if consulting_category else None,
                "consulting_category_note": selected_consulting_category.notes if selected_consulting_category else None,
            }
        }
        return jsonify(rating_data), 200

    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal Server Error"}), 500





@data_blueprint.route('/email_threads/save_mailhistory_rating/<int:thread_id>', methods=['POST'])
def save_mail_rating(thread_id):
    try:
        # Authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401


        # check if user can access thread
        if not can_access_thread(user.id, thread_id, 3):
            return jsonify({'error': 'Access denied'}), 401

        ### Start of Logik ###
        data = request.get_json()

        # Values sent from the client

        client_data = {
            "counsellor_coherence_rating": data.get('counsellor_coherence_rating'),
            "client_coherence_rating": data.get('client_coherence_rating'),
            "quality_rating": data.get('quality_rating'),
            "overall_rating": data.get('overall_rating')}
        selected_consulting_category_id = data.get("consulting_category_id")
        consulting_category_notes = data.get("consulting_category_notes")
        consider_category_for_status = data.get("consider_category_for_status", False)
        feedback = data.get('feedback')

        # check if category id exists
        if isinstance(selected_consulting_category_id, int) and selected_consulting_category_id > 0:
            consulting_category_type = ConsultingCategoryType.query.filter_by(
                id=selected_consulting_category_id).first()
            if not consulting_category_type:
                return jsonify({'error': 'Consulting category does not exist'}), 404
        elif selected_consulting_category_id is None:
            consulting_category_type = None
        else:
            return jsonify({'error': 'invalid consulting category id'}), 400

        # retrieve most recent mail history rating and category
        existing_rating = UserMailHistoryRating.query.filter_by(user_id=user.id, thread_id=thread_id).order_by(
            UserMailHistoryRating.timestamp.desc()).first()

        existing_category_selection = UserConsultingCategorySelection.query.filter_by(user_id=user.id,
                                                                                      thread_id=thread_id).order_by(
            UserConsultingCategorySelection.timestamp.desc()).first()

        # check if any likert scale got rated, a category got chosen or a feedback was written.
        is_category_filled = consulting_category_type is not None or consulting_category_notes is not None
        if all(v is None for v in [
            client_data["counsellor_coherence_rating"],
            client_data["client_coherence_rating"],
            client_data["quality_rating"],
            client_data["overall_rating"],
            feedback,
            consulting_category_type,
            consulting_category_notes,
        ]) and not existing_category_selection and not existing_rating:  # skip because no rating of the history happened
            return jsonify({'status': ' Ratings and Category saved successfully'}), 201

        # logic to determine the rating/progression status
        max_values_to_fill = 4
        filled_values_counter = 0

        if consider_category_for_status:
            max_values_to_fill += 1
            if consulting_category_type is not None:
                filled_values_counter += 1

        for key, value in client_data.items():
            if value is not None:
                filled_values_counter += 1

        if filled_values_counter == 0:
            rating_status = ProgressionStatus.NOT_STARTED
        elif filled_values_counter < max_values_to_fill:
            rating_status = ProgressionStatus.PROGRESSING
        else:
            rating_status = ProgressionStatus.DONE

        # if a rating or category already exists, check if changes occurred
        if existing_rating:
            has_rating_changes = not (
                    existing_rating.counsellor_coherence_rating == client_data["counsellor_coherence_rating"] and
                    existing_rating.client_coherence_rating == client_data["client_coherence_rating"] and
                    existing_rating.quality_rating == client_data["quality_rating"] and
                    existing_rating.overall_rating == client_data["overall_rating"] and
                    existing_rating.feedback == feedback and
                    existing_rating.status == rating_status
            )
        else:
            has_rating_changes = True  # Es ist eine neue Bewertung

        if existing_category_selection:
            has_category_changes = not (
                    existing_category_selection.consulting_category_type_id == selected_consulting_category_id and
                    existing_category_selection.notes == consulting_category_notes
            )
        else:
            has_category_changes = is_category_filled  # Es ist eine neue Kategorieauswahl, wurden auch Werte ausgefüllt?

        if not has_rating_changes and not has_category_changes:
            return jsonify({'status': 'Message ratings saved successfully'}), 201

        # Changes happened in rating, or it is the first rating
        if has_rating_changes:
            # Create a new mail rating with feedback and save it into the db with current timestamp
            new_mail_rating = UserMailHistoryRating(
                user_id=user.id,
                thread_id=thread_id,
                counsellor_coherence_rating=client_data["counsellor_coherence_rating"],
                client_coherence_rating=client_data["client_coherence_rating"],
                quality_rating=client_data["quality_rating"],
                overall_rating=client_data["overall_rating"],
                feedback=feedback,
                status=rating_status
            )
            db.session.add(new_mail_rating)

        if has_category_changes:
            new_selected_category = UserConsultingCategorySelection(
                user_id=user.id,
                thread_id=thread_id,
                consulting_category_type_id=selected_consulting_category_id,
                notes=consulting_category_notes,
            )
            db.session.add(new_selected_category)

        db.session.commit()

        return jsonify({'status': 'Mail rating and feedback saved successfully'}), 201
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500




# Get the user ratings for the messages of a thread
@data_blueprint.route('/email_threads/message_ratings/<int:thread_id>', methods=['GET'])
def get_email_thread_message_ratings(thread_id):
    try:
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401


        # check if user can access thread
        if not can_access_thread(user.id, thread_id, 3):
                return jsonify({'error': 'Access denied'}), 401

        ### Start of Logik ###
        # Load Ratings of messages
        ## Unterabfrage, um den neuesten Timestamp pro message_id zu ermitteln
        subquery = db.session.query(
            UserMessageRating.message_id,
            func.max(UserMessageRating.timestamp).label('latest_timestamp')
        ).filter_by(
            user_id=user.id,
            thread_id=thread_id
        ).group_by(
            UserMessageRating.message_id
        ).subquery()

        ## Hauptabfrage, die den entsprechenden Datensatz für jede message_id mit dem neuesten Timestamp auswählt
        msg_ratings = db.session.query(UserMessageRating).join(
            subquery,
            (UserMessageRating.message_id == subquery.c.message_id) &
            (UserMessageRating.timestamp == subquery.c.latest_timestamp)
        ).filter(
            UserMessageRating.user_id == user.id,
            UserMessageRating.thread_id == thread_id
        ).all()

        rating_list = [
            {
                'message_id': msg_rating.message_id,
                'rating': msg_rating.rating,
            } for msg_rating in msg_ratings
        ]

        return jsonify(rating_list), 200

    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal Server Error"}), 500

# Route for saving the rating of each message (up or down) from the generated mail historys
@data_blueprint.route('/email_threads/save_message_ratings/<int:thread_id>', methods=['POST'])
def save_message_ratings(thread_id):
    try:
        # authorization
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401

        # check if user can access thread
        if not can_access_thread(user.id, thread_id, 3):
            return jsonify({'error': 'Access denied'}), 401

        ### Start of Logik ###

        # retrieve data send from user
        data = request.get_json()
        message_ratings = data.get('message_ratings', [])

        # Loop through all message ratings send from user
        for rating_data in message_ratings:
            message_id = rating_data.get('message_id')
            rating = rating_data.get('rating')

            # check if the most recent message rating of this user is equal to the one send (avoiding duplicates in the db)
            existing_message_rating = (
                UserMessageRating.query
                .filter_by(user_id=user.id, thread_id=thread_id, message_id=message_id)
                .order_by(UserMessageRating.timestamp.desc())
                .first()
            )

            if existing_message_rating:
                # check if the new message rating is a duplicate of the most recent in db. If yes skip this message (applies for null values too)
                if existing_message_rating.rating == rating:
                    continue
            elif rating is None:  # if message didnt get ratet and no rating for this message existed in the db --> skip
                continue

            # either first rating for the message, or a change occured.
            # create and safe new entry into the db with current time stamp
            new_message_rating = UserMessageRating(
                user_id=user.id,
                thread_id=thread_id,
                message_id=message_id,
                rating=rating
            )
            db.session.add(new_message_rating)

        # commit all changes to the db
        db.session.commit()
        return jsonify({'status': 'Message ratings saved successfully'}), 201
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal Server Error"}), 500

# Shows the admin Panel of every MailHistoryRating
@data_blueprint.route('/admin/user_HistoryGeneration_stats', methods=['GET'])
def get_user_HistoryGeneration_stats():
    try:
        api_key = request.headers.get('Authorization')

        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401

        admin_user = User.query.filter_by(api_key=api_key).first()
        if not admin_user:
            return jsonify({'error': 'Invalid API key'}), 401

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
        logger.error(e)
        return jsonify({"error": "Internal Server Error"}), 500



@data_blueprint.route('/admin/user_HistoryGeneration_stats/<int:scenario_id>', methods=['GET'])
def get_scenario_HistoryGeneration_stats(scenario_id):
    try:
        # Validate if scenario has function_type_id = 3
        scenario_function_type = (
            db.session.query(FeatureFunctionType)
            .join(ScenarioThreads, FeatureFunctionType.function_type_id == ScenarioThreads.scenario_id)
            .filter(ScenarioThreads.scenario_id == scenario_id, FeatureFunctionType.name == 'mail_rating')
            .first()
        )

        if not scenario_function_type or scenario_function_type.function_type_id != 3:
            return jsonify({'error': 'Scenario does not have function_type_id = 3'}), 400

        user_stats = []
        threads_in_scenario = (
            db.session.query(ScenarioThreads)
            .filter_by(scenario_id=scenario_id)
            .all()
        )

        for user in db.session.query(ScenarioUsers).filter_by(scenario_id=scenario_id).all():
            done_threads_list = []
            not_started_threads_list = []
            progressing_threads_list = []
            total_done_threads = 0
            total_progressing_threads = 0
            total_not_started_threads = 0

            for scenario_thread in threads_in_scenario:
                thread = scenario_thread.thread
                mail_rating = (
                    db.session.query(UserMailHistoryRating)
                    .filter_by(user_id=user.user_id, thread_id=thread.thread_id)
                    .first()
                )

                if mail_rating:
                    if mail_rating.status == ProgressionStatus.PROGRESSING:
                        total_progressing_threads += 1
                        progressing_threads_list.append({
                            'thread_id': thread.thread_id,
                            'subject': thread.subject
                        })
                    elif mail_rating.status == ProgressionStatus.DONE:
                        total_done_threads += 1
                        done_threads_list.append({
                            'thread_id': thread.thread_id,
                            'subject': thread.subject
                        })
                else:
                    total_not_started_threads += 1
                    not_started_threads_list.append({
                        'thread_id': thread.thread_id,
                        'subject': thread.subject
                    })

            user_stats.append({
                'username': user.user.username,
                'total_threads': len(threads_in_scenario),
                'done_threads': total_done_threads,
                'not_started_threads': total_not_started_threads,
                'progressing_threads': total_progressing_threads,
                'done_threads_list': done_threads_list,
                'not_started_threads_list': not_started_threads_list,
                'progressing_threads_list': progressing_threads_list
            })

        return jsonify({'user_stats': user_stats}), 200

    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal Server Error"}), 500