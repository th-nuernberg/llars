
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



def get_user_threads(user_id, function_type_id):
    # Aktuellen Zeitpunkt ermitteln
    current_time = datetime.utcnow()

    # Alle Szenarien, in denen der User eine Rolle hat und deren Zeitraum gültig ist
    scenario_users = db.session.query(ScenarioUsers).join(RatingScenarios).filter(
        ScenarioUsers.user_id == user_id,
        RatingScenarios.begin <= current_time,
        RatingScenarios.end >= current_time
    ).all()

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