
from db.database import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating, UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       FeatureFunctionType, UserFeatureRating, UserMailHistoryRating, UserMessageRating,
                       UserGroup, UserPrompt, UserPromptShare,
                       UserAuthenticityVote,
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
import hashlib

from db.tables import ProgressionStatus
from db.models.scenario import InvitationStatus

MAIL_RATING_FUNCTION_TYPE_ID = 3

DISTRIBUTION_MODE_ALL = "all"
DISTRIBUTION_MODE_ROUND_ROBIN = "round_robin"

ORDER_MODE_NONE = "none"
ORDER_MODE_SHUFFLE_SAME = "shuffle_same"
ORDER_MODE_SHUFFLE_PER_USER = "shuffle_per_user"

ALLOWED_DISTRIBUTION_MODES = {DISTRIBUTION_MODE_ALL, DISTRIBUTION_MODE_ROUND_ROBIN}
ALLOWED_ORDER_MODES = {ORDER_MODE_NONE, ORDER_MODE_SHUFFLE_SAME, ORDER_MODE_SHUFFLE_PER_USER}


def _get_scenario_config(scenario):
    if scenario is None:
        return {}
    config = getattr(scenario, "config_json", None)
    return config if isinstance(config, dict) else {}


def get_scenario_distribution_mode(scenario, function_type_id=None):
    config = _get_scenario_config(scenario)
    mode = config.get("distribution_mode")
    if mode in ALLOWED_DISTRIBUTION_MODES:
        return mode

    if function_type_id is None and scenario is not None:
        function_type_id = scenario.function_type_id

    if function_type_id == MAIL_RATING_FUNCTION_TYPE_ID:
        return DISTRIBUTION_MODE_ALL

    return DISTRIBUTION_MODE_ROUND_ROBIN


def get_scenario_order_mode(scenario):
    config = _get_scenario_config(scenario)
    mode = config.get("order_mode")
    if mode in ALLOWED_ORDER_MODES:
        return mode
    return ORDER_MODE_SHUFFLE_SAME


def raters_receive_all_threads(scenario, function_type_id=None):
    return get_scenario_distribution_mode(scenario, function_type_id) == DISTRIBUTION_MODE_ALL


def _scenario_user_seed(scenario_id, user_id):
    digest = hashlib.sha256(f"{scenario_id}:{user_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def order_threads_for_user(threads, scenario_id, order_mode, user_id):
    threads_sorted = sorted(threads, key=lambda t: t.thread_id)

    if order_mode == ORDER_MODE_NONE:
        return threads_sorted

    if order_mode == ORDER_MODE_SHUFFLE_PER_USER:
        seed = _scenario_user_seed(scenario_id, user_id)
    else:
        seed = scenario_id

    return deterministic_shuffle(threads_sorted, seed)


def deterministic_shuffle(items, seed):
    """
    Shuffle items deterministically using a seed.

    This ensures all users see the same shuffled order for the same seed.
    The seed is typically the scenario_id, so all users in a scenario
    see threads in the same (shuffled) order.

    Args:
        items: List of items to shuffle
        seed: Integer seed for random generator (e.g., scenario_id)

    Returns:
        New list with items in deterministically shuffled order
    """
    rng = random.Random(seed)
    shuffled = list(items)
    rng.shuffle(shuffled)
    return shuffled



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


def get_progression_authenticity(thread: EmailThread, user_id: int) -> ProgressionStatus:
    """ Fortschritt für Fake/Echt (function_type_id=5): DONE sobald eine Stimme existiert. """
    vote = db.session.query(UserAuthenticityVote).filter_by(
        user_id=user_id, thread_id=thread.thread_id
    ).first()
    return ProgressionStatus.DONE if vote else ProgressionStatus.NOT_STARTED



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
        scenario = getattr(scenario_user, "rating_scenario", None)
        if scenario is None:
            scenario = RatingScenarios.query.filter_by(id=scenario_id).first()

        if role == ScenarioRoles.EVALUATOR or raters_receive_all_threads(scenario, function_type_id):
            # Evaluator oder All-Distribution-Rater sehen alle Threads des Szenarios
            if db.session.query(ScenarioThreads).join(
                RatingScenarios, RatingScenarios.id == ScenarioThreads.scenario_id
            ).filter(
                ScenarioThreads.scenario_id == scenario_id,
                ScenarioThreads.thread_id == thread_id,
                RatingScenarios.begin <= current_time, # TODO: Gedanken zu Zeitzonen machen
                RatingScenarios.end >= current_time
            ).first():
                return True

        elif role == ScenarioRoles.RATER:
            # Wenn der User Rater ist, muss der Thread zugeordnet sein
            if (
                db.session.query(ScenarioThreadDistribution)
                .join(ScenarioThreads, ScenarioThreads.id==ScenarioThreadDistribution.scenario_thread_id)
                .join(RatingScenarios, RatingScenarios.id == ScenarioThreadDistribution.scenario_id)
                .filter(
                    ScenarioThreadDistribution.scenario_user_id == scenario_user.id,
                    ScenarioThreads.thread_id == thread_id,
                    RatingScenarios.begin <= current_time, # TODO: Gedanken zu Zeitzonen machen
                    RatingScenarios.end >= current_time
                )
                .first()
            ):
                return True
    logging.error("Abgelehnt")
    return False


def get_user_scenarios(user_id, function_type_id):
  """
  Get all scenarios where the user has an active role and accepted invitation.

  Args:
      user_id: The user ID
      function_type_id: The function type ID

  Returns:
      List of ScenarioUsers objects for accepted scenarios within valid timeframe
  """
  # Aktuellen Zeitpunkt ermitteln
  current_time = datetime.utcnow()

  # Alle Szenarien, in denen der User eine Rolle hat, die Einladung akzeptiert wurde
  # und deren Zeitraum gültig ist
  return db.session.query(ScenarioUsers).join(RatingScenarios).filter(
      ScenarioUsers.user_id == user_id,
      ScenarioUsers.invitation_status == InvitationStatus.ACCEPTED,
      RatingScenarios.begin <= current_time,
      RatingScenarios.end >= current_time,
      RatingScenarios.function_type_id == function_type_id
  ).all()


def get_user_threads(user_id, function_type_id):
    """
    Get all threads accessible by a user for a specific function type.

    Thread order is controlled by scenario config (order_mode):
    - none: sorted by thread_id
    - shuffle_same: deterministic shuffle for all users (seed = scenario_id)
    - shuffle_per_user: deterministic shuffle per user (seed = scenario_id:user_id)

    Args:
        user_id: The user ID
        function_type_id: The function type ID

    Returns:
        List of EmailThread objects in deterministically shuffled order
    """
    # Aktuellen Zeitpunkt ermitteln
    current_time = datetime.utcnow()

    scenario_users = get_user_scenarios(user_id, function_type_id)

    # Group threads by scenario for deterministic ordering
    scenario_threads_map = {}
    scenario_order_modes = {}

    # Durchlaufe alle Szenarien und deren zugeordnete Threads
    for scenario_user in scenario_users:
        scenario_id = scenario_user.scenario_id
        role = scenario_user.role
        scenario = getattr(scenario_user, "rating_scenario", None)
        if scenario is None:
            scenario = RatingScenarios.query.filter_by(id=scenario_id).first()

        if scenario_id not in scenario_threads_map:
            scenario_threads_map[scenario_id] = []

        if scenario_id not in scenario_order_modes:
            scenario_order_modes[scenario_id] = get_scenario_order_mode(scenario)

        if role == ScenarioRoles.EVALUATOR or raters_receive_all_threads(scenario, function_type_id):
            # Evaluator oder All-Distribution-Rater sehen alle Threads im Szenario
            threads = (
                db.session.query(EmailThread)
                .join(ScenarioThreads, ScenarioThreads.thread_id == EmailThread.thread_id)
                .filter(
                    ScenarioThreads.scenario_id == scenario_id,
                    EmailThread.function_type_id == function_type_id,
                )
                .all()
            )
            scenario_threads_map[scenario_id].extend(threads)

        elif role == ScenarioRoles.RATER:
            # Rater mit Thread-Zuweisung sehen nur ihre zugeordneten Threads
            thread_distributions = (
                db.session.query(ScenarioThreadDistribution)
                .join(ScenarioThreads, ScenarioThreadDistribution.scenario_thread_id == ScenarioThreads.id)
                .join(EmailThread, ScenarioThreads.thread_id == EmailThread.thread_id)
                .filter(
                    ScenarioThreadDistribution.scenario_user_id == scenario_user.id,
                    ScenarioThreadDistribution.scenario_id == scenario_id,
                    EmailThread.function_type_id == function_type_id,
                )
                .all()
            )

            for distribution in thread_distributions:
                scenario_threads_map[scenario_id].append(distribution.scenario_thread.thread)

    # Build result with deterministic ordering per scenario
    # Process scenarios in sorted order for consistency
    allowed_threads = []
    seen_thread_ids = set()  # Avoid duplicates if user is in multiple scenarios

    for scenario_id in sorted(scenario_threads_map.keys()):
        threads = scenario_threads_map[scenario_id]
        order_mode = scenario_order_modes.get(scenario_id, ORDER_MODE_SHUFFLE_SAME)
        threads_shuffled = order_threads_for_user(threads, scenario_id, order_mode, user_id)

        # Add threads, avoiding duplicates
        for thread in threads_shuffled:
            if thread.thread_id not in seen_thread_ids:
                seen_thread_ids.add(thread.thread_id)
                allowed_threads.append(thread)

    return allowed_threads


def get_thread_progression_state(thread: EmailThread, user_id: int, function_type_id: int) -> ProgressionStatus:
    """ Dynamische Auswahl der Progressionslogik basierend auf function_type_id """
    PROGRESSION_HANDLERS = {
        1: get_progression_ranking,
        2: get_progression_rating,
        3: get_progression_mail_rating,
        5: get_progression_authenticity,
    }
    handler = PROGRESSION_HANDLERS.get(function_type_id)

    if handler is None:
        raise NotImplementedError(f"Function Type {function_type_id} ist nicht implementiert!")

    return handler(thread, user_id)
