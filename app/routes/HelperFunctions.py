
from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating, UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating,
                       UserGroup, UserPrompt, UserPromptShare,
                       ConsultingCategoryType, UserConsultingCategorySelection, RatingScenarios, ScenarioUsers, ScenarioThreadDistribution, ScenarioThreads, ScenarioRoles)
from sqlalchemy import func
from uuid import uuid4
import uuid
from datetime import datetime
import json
import random
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import joinedload
import logging

from db.tables import ProgressionStatus



def get_progression_ranking(thread: EmailThread, user_id: int) -> ProgressionStatus:
    """ Berechnet den Fortschritt für das Feature Ranking (function_type_id=1) """
    total_features = db.session.query(Feature).filter_by(thread_id=thread.thread_id).count()
    ranked_features = db.session.query(UserFeatureRanking).join(Feature).filter(
        UserFeatureRanking.user_id == user_id,
        Feature.thread_id == thread.thread_id
    ).count()

    if ranked_features == 0:
        return ProgressionStatus.NOT_STARTED
    if ranked_features < total_features:
        return ProgressionStatus.PROGRESSING
    return ProgressionStatus.DONE


def get_progression_rating(thread: EmailThread, user_id: int) -> ProgressionStatus:
    """ Berechnet den Fortschritt für das Feature Rating (function_type_id=2) """
    total_features = db.session.query(Feature).filter_by(thread_id=thread.thread_id).count()
    rated_features = db.session.query(UserMessageRating).join(Feature).filter(
        UserMessageRating.user_id == user_id,
        Feature.thread_id == thread.thread_id
    ).count()

    if rated_features == 0:
        return ProgressionStatus.NOT_STARTED
    if rated_features < total_features:
        return ProgressionStatus.PROGRESSING
    return ProgressionStatus.DONE


def get_progression_mail_rating(thread: EmailThread, user_id: int) -> ProgressionStatus:
    """ Berechnet den Fortschritt für das Mail Rating (function_type_id=3) """
    mail_rating = db.session.query(UserMailHistoryRating).filter_by(
        user_id=user_id, thread_id=thread.thread_id
    ).order_by(UserMailHistoryRating.timestamp.desc()).first()

    return mail_rating.status if mail_rating else ProgressionStatus.NOT_STARTED



def can_access_thread(user_id, thread_id, function_type_id):
    # Aktuellen Zeitpunkt ermitteln
    current_time = datetime.utcnow()

    # Hole den Thread, um das Szenario zu bestimmen
    email_thread = db.session.query(EmailThread).filter(EmailThread.thread_id == thread_id,
                                                        EmailThread.function_type_id==function_type_id).first()
    if not email_thread:
        logging.error("Existiert nicht")
        return False  # Thread existiert nicht


    # Alle Szenarien, in denen der User eine Rolle hat und deren Zeitraum gültig ist
    scenario_users = db.session.query(ScenarioUsers).join(RatingScenarios, RatingScenarios.id==ScenarioUsers.scenario_id).filter(
        ScenarioUsers.user_id == user_id,
        RatingScenarios.begin <= current_time, # TODO: Gedanken zu Zeitzonen machen
        RatingScenarios.end >= current_time
    ).all()

    for scenario_user in scenario_users:
        scenario_id = scenario_user.scenario_id
        role = scenario_user.role

        if role == ScenarioRoles.VIEWER:
            # Wenn der User Viewer ist, darf er alle Threads des Szenarios sehen
            if db.session.query(ScenarioThreads).join(RatingScenarios, RatingScenarios.id == ScenarioThreads.scenario_id).filter(
                    ScenarioThreads.scenario_id == scenario_id,
                    ScenarioThreads.thread_id == thread_id,
                    RatingScenarios.begin <= current_time, # TODO: Gedanken zu Zeitzonen machen
                    RatingScenarios.end >= current_time
            ).first():
                return True

        elif role == ScenarioRoles.RATER:
            # Wenn der User Rater ist, muss der Thread zugeordnet sein
            if (db.session.query(ScenarioThreadDistribution).join(ScenarioThreads, ScenarioThreads.id==ScenarioThreadDistribution.scenario_thread_id)
                    .join(RatingScenarios, RatingScenarios.id == ScenarioThreadDistribution.scenario_id)
                    .filter(
                    ScenarioThreadDistribution.scenario_user_id == scenario_user.id,
                    ScenarioThreads.thread_id == thread_id,
                    RatingScenarios.begin <= current_time, # TODO: Gedanken zu Zeitzonen machen
                    RatingScenarios.end >= current_time
            ).first()):
                return True
    logging.error("Abgelehnt")
    return False


def get_user_scenarios(user_id, function_type_id):
  # Aktuellen Zeitpunkt ermitteln
  current_time = datetime.utcnow()

  # Alle Szenarien, in denen der User eine Rolle hat und deren Zeitraum gültig ist
  return db.session.query(ScenarioUsers).join(RatingScenarios).filter(
      ScenarioUsers.user_id == user_id,
      RatingScenarios.begin <= current_time,
      RatingScenarios.end >= current_time,
      RatingScenarios.function_type_id == function_type_id
  ).all()


def get_user_threads(user_id, function_type_id):
    # Aktuellen Zeitpunkt ermitteln
    current_time = datetime.utcnow()

    scenario_users = get_user_scenarios(user_id, function_type_id)

    # Alle EmailThreads, die der User sehen darf
    allowed_threads = []

    # Durchlaufe alle Szenarien und deren zugeordnete Threads
    for scenario_user in scenario_users:
        scenario_id = scenario_user.scenario_id
        role = scenario_user.role

        if role == ScenarioRoles.VIEWER:
            # Wenn der User Viewer ist, darf er alle Threads des Szenarios sehen
            threads = db.session.query(EmailThread).join(ScenarioThreads).filter(
                ScenarioThreads.scenario_id == scenario_id,
                ScenarioThreads.thread_id == EmailThread.thread_id,
                EmailThread.function_type_id == function_type_id,
                RatingScenarios.begin <= current_time,
                RatingScenarios.end >= current_time
            ).all()
            allowed_threads.extend(threads)

        elif role == ScenarioRoles.RATER:
            # Wenn der User Rater ist, darf er nur zugeordnete Threads sehen
            thread_distributions = (db.session.query(ScenarioThreadDistribution)
                                    .join(ScenarioThreads, ScenarioThreadDistribution.scenario_thread_id == ScenarioThreads.id)
                                    .join(EmailThread, ScenarioThreads.thread_id == EmailThread.thread_id).filter(
                ScenarioThreadDistribution.scenario_user_id == scenario_user.id,
                EmailThread.function_type_id == function_type_id,


            ).all())

            for distribution in thread_distributions:
                allowed_threads.append(distribution.scenario_thread.thread)

    return allowed_threads


def get_thread_progression_state(thread: EmailThread, user_id: int, function_type_id: int) -> ProgressionStatus:
    """ Dynamische Auswahl der Progressionslogik basierend auf function_type_id """
    PROGRESSION_HANDLERS = {
        1: get_progression_ranking,
        2: get_progression_rating,
        3: get_progression_mail_rating
    }
    handler = PROGRESSION_HANDLERS.get(function_type_id)

    if handler is None:
        raise NotImplementedError(f"Function Type {function_type_id} ist nicht implementiert!")

    return handler(thread, user_id)


