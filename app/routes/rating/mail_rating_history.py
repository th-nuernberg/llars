"""
Mail Rating History Endpoints
Handles getting and saving mail history (thread-level) ratings.
"""

import logging
import traceback
from datetime import datetime
from flask import jsonify, request, g
from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from db.db import db
from db.tables import (UserMailHistoryRating, ConsultingCategoryType,
                       UserConsultingCategorySelection, ProgressionStatus)
from .. import data_blueprint
from ..HelperFunctions import can_access_thread, get_thread_progression_state, raters_receive_all_threads


@data_blueprint.route('/email_threads/mailhistory_ratings/<int:thread_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='rating')
def get_mail_rating(thread_id):
    """Get the most recent mail history rating for a thread"""
    user = g.authentik_user

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 3):
        raise ValidationError('Access denied')

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


@data_blueprint.route('/email_threads/save_mailhistory_rating/<int:thread_id>', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='rating')
def save_mail_rating(thread_id):
    """Save mail history rating with consulting category selection"""
    user = g.authentik_user

    # check if user can access thread
    if not can_access_thread(user.id, thread_id, 3):
        raise ValidationError('Access denied')

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
            raise ValidationError('Consulting category does not exist')
    elif selected_consulting_category_id is None:
        consulting_category_type = None
    else:
        raise ValidationError('invalid consulting category id')

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

    became_done = (
        rating_status == ProgressionStatus.DONE and
        (existing_rating is None or existing_rating.status != ProgressionStatus.DONE)
    )

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

    if became_done:
        try:
            from services.system_event_service import SystemEventService

            SystemEventService.log_event(
                event_type="rating.thread_completed",
                severity="info",
                username=user.username,
                entity_type="thread",
                entity_id=str(thread_id),
                message=f"User '{user.username}' completed thread {thread_id} (mail rating)",
                details={"thread_id": int(thread_id), "function_type_id": 3},
            )
        except Exception:
            pass

        # Scenario completion (only for active scenarios where the user is a rater)
        try:
            from db.tables import RatingScenarios, ScenarioRoles, ScenarioThreads, ScenarioThreadDistribution, ScenarioUsers
            from services.system_event_service import SystemEventService

            current_time = datetime.utcnow()
            scenario_users = (
                db.session.query(ScenarioUsers)
                .join(RatingScenarios, RatingScenarios.id == ScenarioUsers.scenario_id)
                .filter(
                    ScenarioUsers.user_id == user.id,
                    ScenarioUsers.role == ScenarioRoles.RATER,
                    RatingScenarios.begin <= current_time,
                    RatingScenarios.end >= current_time,
                )
                .all()
            )

            for scenario_user in scenario_users:
                scenario = getattr(scenario_user, "rating_scenario", None)
                if not scenario:
                    continue

                scenario_thread = (
                    db.session.query(ScenarioThreads)
                    .filter(
                        ScenarioThreads.scenario_id == scenario_user.scenario_id,
                        ScenarioThreads.thread_id == thread_id
                    )
                    .first()
                )
                if not scenario_thread:
                    continue

                if not raters_receive_all_threads(scenario):
                    distribution = (
                        db.session.query(ScenarioThreadDistribution)
                        .filter(
                            ScenarioThreadDistribution.scenario_user_id == scenario_user.id,
                            ScenarioThreadDistribution.scenario_id == scenario_user.scenario_id,
                            ScenarioThreadDistribution.scenario_thread_id == scenario_thread.id,
                        )
                        .first()
                    )
                    if not distribution:
                        continue

                if raters_receive_all_threads(scenario):
                    scenario_threads = (
                        db.session.query(ScenarioThreads)
                        .filter(ScenarioThreads.scenario_id == scenario_user.scenario_id)
                        .all()
                    )
                else:
                    scenario_threads = [
                        dist.scenario_thread
                        for dist in db.session.query(ScenarioThreadDistribution)
                        .filter(
                            ScenarioThreadDistribution.scenario_user_id == scenario_user.id,
                            ScenarioThreadDistribution.scenario_id == scenario_user.scenario_id,
                        )
                        .all()
                        if dist.scenario_thread
                    ]

                total_threads = 0
                done_threads = 0
                for scenario_thread in scenario_threads:
                    thread = getattr(scenario_thread, "thread", None)
                    if not thread:
                        continue
                    total_threads += 1
                    if get_thread_progression_state(thread, user.id, scenario.function_type_id) == ProgressionStatus.DONE:
                        done_threads += 1

                if total_threads > 0 and done_threads == total_threads:
                    SystemEventService.log_event(
                        event_type="scenario.completed",
                        severity="success",
                        username=user.username,
                        entity_type="scenario",
                        entity_id=str(scenario.id),
                        message=f"User '{user.username}' completed scenario '{scenario.scenario_name}'",
                        details={
                            "scenario_id": int(scenario.id),
                            "scenario_name": scenario.scenario_name,
                            "function_type_id": int(scenario.function_type_id),
                            "total_threads": total_threads,
                        },
                        dedupe=True,
                    )
        except Exception:
            pass

    return jsonify({'status': 'Mail rating and feedback saved successfully'}), 201
