"""
Scenario statistics service.

Provides scenario progress stats and authenticity (fake/echt) stats for reuse
across HTTP routes and Socket.IO updates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import json
import numpy as np

from db.database import db
from db.models import (
    RatingScenarios,
    FeatureFunctionType,
    ScenarioUsers,
    ScenarioThreads,
    ScenarioThreadDistribution,
    ScenarioRoles,
    MembershipStatus,
    User,
    ComparisonSession,
    EmailThread,
    AuthenticityConversation,
    UserAuthenticityVote,
    ProgressionStatus,
    LLMTaskResult,
    LLMModel,
    ItemDimensionRating,
    ItemLabelingEvaluation,
    UserMailHistoryRating,
)
from decorators.error_handler import NotFoundError, ValidationError
from routes.HelperFunctions import (
    get_thread_progression_state,
    raters_receive_all_threads,
    get_scenario_distribution_mode,
    DISTRIBUTION_MODE_ALL,
)
from services.user_profile_service import serialize_user_brief


def _get_scenario_or_raise(scenario_id: int) -> RatingScenarios:
    if not scenario_id:
        raise ValidationError("Scenario id is missing")
    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")
    return scenario


def _get_function_type_or_raise(function_type_id: int) -> FeatureFunctionType:
    function_type = FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()
    if not function_type:
        raise NotFoundError("Function type does not exist")
    return function_type


def get_scenario_ids_for_thread(thread_id: int) -> List[int]:
    if not thread_id:
        return []
    scenario_rows = ScenarioThreads.query.filter_by(thread_id=thread_id).all()
    return sorted({row.scenario_id for row in scenario_rows if row.scenario_id})


def _calculate_unified_pairwise_agreement(scenario_id: int, function_type_name: str) -> Dict[str, Any]:
    """
    Calculate pairwise agreement based on scenario type.

    Unified dispatcher that routes to the appropriate agreement calculation
    based on the scenario's function type.

    Returns:
        Dict with 'evaluators' list and 'agreements' dict with agreement scores.
    """
    if function_type_name == "ranking":
        return _calculate_ranking_agreement_heatmap(scenario_id)
    elif function_type_name == "labeling":
        return _calculate_labeling_pairwise_agreement(scenario_id)
    elif function_type_name == "mail_rating":
        return _calculate_mail_rating_pairwise_agreement(scenario_id)
    elif function_type_name in {"rating"}:
        return _calculate_pairwise_agreement(scenario_id)
    return {"evaluators": [], "agreements": {}}


def _calculate_ranking_agreement(
    evaluator_stats: List[Dict[str, Any]],
    scenario_id: int,
    function_type_name: str,
) -> Optional[float]:
    """
    Calculate Krippendorff's Alpha for ranking/rating scenarios.

    For ranking: compares bucket assignments across evaluators
    For rating: compares rating values across evaluators
    """
    from db.models import UserFeatureRanking, UserFeatureRating, UserMailHistoryRating

    # Get evaluators who have completed at least one thread
    active_evaluators = [e for e in evaluator_stats if e.get("done_threads", 0) > 0]
    if len(active_evaluators) < 2:
        return None

    # Get all thread IDs from the scenario
    scenario_threads = ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    thread_ids = [st.thread_id for st in scenario_threads if st.thread_id]
    if len(thread_ids) < 2:
        return None

    # Build ratings matrix based on function type
    user_ids = []
    for e in active_evaluators:
        if e.get("is_llm"):
            continue  # Skip LLM evaluators for now - different storage
        # Try to get user_id from username
        user = User.query.filter_by(username=e.get("username")).first()
        if user:
            user_ids.append(user.id)

    if len(user_ids) < 2:
        return None

    ratings_matrix = np.full((len(user_ids), len(thread_ids)), np.nan)

    if function_type_name == "ranking":
        # Get bucket assignments
        for i, user_id in enumerate(user_ids):
            rankings = UserFeatureRanking.query.filter(
                UserFeatureRanking.user_id == user_id,
                UserFeatureRanking.feature.has(thread_id=thread_ids[0]) if thread_ids else False
            ).all()
            # Map buckets to numeric values
            bucket_map = {"gut": 0, "good": 0, "mittel": 1, "medium": 1, "schlecht": 2, "bad": 2, "poor": 2}
            for ranking in rankings:
                if ranking.feature and ranking.bucket:
                    try:
                        tid = ranking.feature.thread_id
                        if tid in thread_ids:
                            j = thread_ids.index(tid)
                            bucket_val = bucket_map.get(ranking.bucket.lower())
                            if bucket_val is not None:
                                ratings_matrix[i, j] = bucket_val
                    except (ValueError, AttributeError):
                        continue

    elif function_type_name == "rating":
        # Get rating values
        for i, user_id in enumerate(user_ids):
            ratings = UserFeatureRating.query.filter_by(user_id=user_id).all()
            for rating in ratings:
                if rating.feature and rating.rating_content is not None:
                    try:
                        tid = rating.feature.thread_id
                        if tid in thread_ids:
                            j = thread_ids.index(tid)
                            ratings_matrix[i, j] = float(rating.rating_content)
                    except (ValueError, AttributeError):
                        continue

    elif function_type_name == "mail_rating":
        # Get mail ratings (use overall_rating)
        for i, user_id in enumerate(user_ids):
            ratings = UserMailHistoryRating.query.filter(
                UserMailHistoryRating.user_id == user_id,
                UserMailHistoryRating.thread_id.in_(thread_ids)
            ).all()
            for rating in ratings:
                if rating.overall_rating is not None:
                    try:
                        j = thread_ids.index(rating.thread_id)
                        ratings_matrix[i, j] = float(rating.overall_rating)
                    except (ValueError, AttributeError):
                        continue

    # Calculate alpha using ordinal metric for ratings
    return _calculate_krippendorff_alpha(ratings_matrix)


def get_progress_stats(scenario_id: int) -> Dict[str, Any]:
    """Get detailed progress statistics for all users in a scenario."""
    scenario = _get_scenario_or_raise(scenario_id)
    function_type = _get_function_type_or_raise(scenario.function_type_id)
    if function_type.name == "comparison":
        return _get_comparison_progress_stats(scenario_id)

    rater_stats = []
    evaluator_stats = []

    # Only include active members in stats
    scenario_users = (
        db.session.query(ScenarioUsers)
        .join(User, ScenarioUsers.user_id == User.id)
        .filter(
            ScenarioUsers.scenario_id == scenario_id,
            ScenarioUsers.membership_status == MembershipStatus.ACTIVE
        )
        .all()
    )

    for scenario_user in scenario_users:
        done_threads_list = []
        not_started_threads_list = []
        progressing_threads_list = []
        total_done_threads = 0
        total_progressing_threads = 0
        total_not_started_threads = 0

        use_full_threads = (
            scenario_user.role == ScenarioRoles.VIEWER
            or scenario_user.role == ScenarioRoles.OWNER
            or (scenario_user.role == ScenarioRoles.EVALUATOR and raters_receive_all_threads(scenario))
        )

        if use_full_threads:
            user_threads = (
                db.session.query(ScenarioThreads)
                .filter(ScenarioThreads.scenario_id == scenario_id)
                .all()
            )
        else:
            user_threads = (
                db.session.query(ScenarioThreads)
                .join(
                    ScenarioThreadDistribution,
                    ScenarioThreadDistribution.scenario_thread_id == ScenarioThreads.id,
                )
                .join(ScenarioUsers, ScenarioThreadDistribution.scenario_user_id == ScenarioUsers.id)
                .filter(
                    ScenarioThreads.scenario_id == scenario_id,
                    ScenarioUsers.user_id == scenario_user.user_id,
                )
                .all()
            )

        if not user_threads:
            user_threads = []

        for user_thread in user_threads:
            thread = user_thread.thread

            progression_state = get_thread_progression_state(
                thread=thread,
                user_id=scenario_user.user_id,
                function_type_id=scenario.function_type_id,
            )

            if progression_state:
                if progression_state == ProgressionStatus.PROGRESSING:
                    total_progressing_threads += 1
                    progressing_threads_list.append(
                        {
                            "thread_id": thread.thread_id,
                            "subject": thread.subject,
                            "chat_id": thread.chat_id,
                            "institut_id": thread.institut_id,
                        }
                    )
                elif progression_state == ProgressionStatus.DONE:
                    total_done_threads += 1
                    done_threads_list.append(
                        {
                            "thread_id": thread.thread_id,
                            "subject": thread.subject,
                            "chat_id": thread.chat_id,
                            "institut_id": thread.institut_id,
                        }
                    )
                else:
                    total_not_started_threads += 1
                    not_started_threads_list.append(
                        {
                            "thread_id": thread.thread_id,
                            "subject": thread.subject,
                            "chat_id": thread.chat_id,
                            "institut_id": thread.institut_id,
                        }
                    )

        avatar_data = serialize_user_brief(scenario_user.user)
        new_data = {
            "username": avatar_data.get("username") or scenario_user.user.username,
            "avatar_seed": avatar_data.get("avatar_seed"),
            "avatar_url": avatar_data.get("avatar_url"),
            "is_llm": False,  # Explicit flag for human evaluators
            "total_threads": len(user_threads),
            "done_threads": total_done_threads,
            "not_started_threads": total_not_started_threads,
            "progressing_threads": total_progressing_threads,
            "done_threads_list": done_threads_list,
            "not_started_threads_list": not_started_threads_list,
            "progressing_threads_list": progressing_threads_list,
        }

        if scenario_user.role == ScenarioRoles.EVALUATOR:
            # EVALUATOR can interact (rate/evaluate)
            rater_stats.append(new_data)
        elif scenario_user.role == ScenarioRoles.OWNER:
            # OWNER shown in stats for overview purposes
            evaluator_stats.append(new_data)
        # VIEWER: excluded from stats entirely (read-only, no evaluation)

    if function_type.name in {"ranking", "rating", "mail_rating", "authenticity", "labeling"}:
        scenario_thread_ids = [
            row.thread_id
            for row in ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
            if row.thread_id
        ]
        config = scenario.config_json
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except (json.JSONDecodeError, TypeError):
                config = {}
        if not isinstance(config, dict):
            config = {}
        config_models = config.get("llm_evaluators")
        if not config_models:
            config_models = config.get("selected_llms") or []
        normalized_models = []
        for model in config_models:
            if isinstance(model, str):
                mid = model.strip()
            elif isinstance(model, dict):
                mid = str(model.get("model_id") or "").strip()
            else:
                continue
            if mid and mid not in normalized_models:
                normalized_models.append(mid)
        config_models = normalized_models
        llm_stats = _build_llm_progress_entries(
            scenario_id=scenario_id,
            thread_ids=scenario_thread_ids,
            task_type=function_type.name,
            model_ids=config_models,
        )
        evaluator_stats.extend(llm_stats)

    # Calculate agreement metrics for ranking/rating scenarios
    all_stats = rater_stats + evaluator_stats
    alpha = None
    if function_type.name in {"ranking", "rating", "mail_rating"} and len(all_stats) >= 2:
        alpha = _calculate_ranking_agreement(all_stats, scenario_id, function_type.name)

    # Calculate distribution and agreement metrics based on scenario type
    rating_distribution = None
    dimension_averages = None
    pairwise_agreement = None
    bucket_distribution = None
    rating_alpha = None  # Krippendorff's Alpha split by evaluator type

    # Calculate pairwise agreement using unified dispatcher (works for all types)
    if function_type.name in {"rating", "mail_rating", "labeling", "ranking"}:
        pairwise_agreement = _calculate_unified_pairwise_agreement(scenario_id, function_type.name)

    if function_type.name in {"rating", "mail_rating", "labeling"}:
        rating_distribution = _calculate_rating_distribution(scenario_id)
        dimension_averages = _calculate_dimension_averages(scenario_id)
        # Calculate Krippendorff's Alpha using new rating system (ItemDimensionRating + LLMTaskResult)
        rating_alpha = _calculate_rating_krippendorff_alpha(scenario_id)
        # Use the "all" alpha as the main alpha if no legacy alpha calculated
        if alpha is None and rating_alpha and rating_alpha.get("all") is not None:
            alpha = rating_alpha["all"]
    elif function_type.name == "ranking":
        bucket_distribution = _calculate_bucket_distribution(scenario_id)

    return {
        "rater_stats": rater_stats,
        "evaluator_stats": evaluator_stats,
        "viewer_stats": evaluator_stats,  # backward compatibility
        "krippendorff_alpha": alpha,
        "alpha_interpretation": _interpret_alpha(alpha),
        "rating_alpha": rating_alpha,  # split by evaluator type {all, humans, llms}
        "rating_distribution": rating_distribution,
        "dimension_averages": dimension_averages,
        "pairwise_agreement": pairwise_agreement,
        "bucket_distribution": bucket_distribution,
        "ranking_agreement": pairwise_agreement,  # backward compatibility (deprecated)
    }


def _build_llm_progress_entries(
    *,
    scenario_id: int,
    thread_ids: List[int],
    task_type: str,
    model_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    if not thread_ids:
        return []

    results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id,
        task_type=task_type,
    ).all()
    model_ids = model_ids or []

    by_model: Dict[str, Dict[int, LLMTaskResult]] = {}
    for result in results:
        if result.thread_id not in thread_ids:
            continue
        by_model.setdefault(result.model_id, {})[result.thread_id] = result

    cleaned_model_ids = []
    for model_id in model_ids:
        if isinstance(model_id, str):
            mid = model_id.strip()
            if mid and mid not in cleaned_model_ids:
                cleaned_model_ids.append(mid)

    if not by_model and not cleaned_model_ids:
        return []

    all_model_ids = sorted(set(list(by_model.keys()) + cleaned_model_ids))
    model_meta = {
        model.model_id: model
        for model in LLMModel.query.filter(LLMModel.model_id.in_(all_model_ids)).all()
    }

    entries: List[Dict[str, Any]] = []
    for model_id in all_model_ids:
        model_results = by_model.get(model_id, {})
        display_name = model_meta.get(model_id).display_name if model_meta.get(model_id) else model_id
        done_threads_list = []
        not_started_threads_list = []
        total_done_threads = 0

        for thread_id in thread_ids:
            result = model_results.get(thread_id)
            if result and result.payload_json and not result.error:
                total_done_threads += 1
                done_threads_list.append({"thread_id": thread_id})
            else:
                not_started_threads_list.append({"thread_id": thread_id})

        entries.append({
            "username": display_name,
            "model_id": model_id,
            "is_llm": True,
            "avatar_seed": None,
            "avatar_url": None,
            "total_threads": len(thread_ids),
            "done_threads": total_done_threads,
            "not_started_threads": len(thread_ids) - total_done_threads,
            "progressing_threads": 0,
            "done_threads_list": done_threads_list,
            "not_started_threads_list": not_started_threads_list,
            "progressing_threads_list": [],
        })

    entries.sort(key=lambda entry: entry["username"].lower())
    return entries


def _get_comparison_progress_stats(scenario_id: int) -> Dict[str, Any]:
    scenario = _get_scenario_or_raise(scenario_id)

    # Only include active members in stats
    scenario_users = (
        db.session.query(ScenarioUsers)
        .join(User, ScenarioUsers.user_id == User.id)
        .filter(
            ScenarioUsers.scenario_id == scenario_id,
            ScenarioUsers.membership_status == MembershipStatus.ACTIVE
        )
        .all()
    )

    sessions = ComparisonSession.query.filter_by(scenario_id=scenario_id).all()
    sessions_by_user = {}
    session_pair_counts = {}
    for session in sessions:
        bot_pairs = [msg for msg in session.messages if msg.type == "bot_pair"]
        session_pair_counts[session.id] = len(bot_pairs)
        sessions_by_user.setdefault(session.user_id, []).append(session)

    rater_stats = []
    evaluator_stats = []

    for scenario_user in scenario_users:
        user_sessions = sessions_by_user.get(scenario_user.user_id, [])

        done_threads_list = []
        not_started_threads_list = []
        progressing_threads_list = []
        total_done_threads = 0
        total_progressing_threads = 0
        total_not_started_threads = 0
        total_pairs = 0
        total_rated_pairs = 0

        for session in user_sessions:
            total_pairs_session = session_pair_counts.get(session.id, 0)
            rated_pairs_session = sum(
                1 for msg in session.messages
                if msg.type == "bot_pair" and msg.selected is not None
            )

            total_pairs += total_pairs_session
            total_rated_pairs += rated_pairs_session

            session_info = {
                "session_id": session.id,
                "persona_name": session.persona_name,
                "total_pairs": total_pairs_session,
                "rated_pairs": rated_pairs_session,
            }

            if total_pairs_session == 0 or rated_pairs_session == 0:
                total_not_started_threads += 1
                not_started_threads_list.append(session_info)
            elif rated_pairs_session < total_pairs_session:
                total_progressing_threads += 1
                progressing_threads_list.append(session_info)
            else:
                total_done_threads += 1
                done_threads_list.append(session_info)

        new_data = {
            "username": scenario_user.user.username,
            "is_llm": False,  # Explicit flag for human evaluators
            "total_threads": total_pairs,
            "done_threads": total_rated_pairs,
            "not_started_threads": max(total_pairs - total_rated_pairs, 0),
            "progressing_threads": total_progressing_threads,
            "done_threads_list": done_threads_list,
            "not_started_threads_list": not_started_threads_list,
            "progressing_threads_list": progressing_threads_list,
        }

        if scenario_user.role == ScenarioRoles.EVALUATOR:
            # EVALUATOR can interact (rate/evaluate)
            rater_stats.append(new_data)
        elif scenario_user.role == ScenarioRoles.OWNER:
            # OWNER shown in stats for overview purposes
            evaluator_stats.append(new_data)
        # VIEWER: excluded from stats entirely (read-only, no evaluation)

    # Add LLM evaluator stats (comparison sessions)
    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    model_ids = config.get("llm_evaluators") or config.get("selected_llms") or []
    cleaned_model_ids = []
    for model_id in model_ids:
        if isinstance(model_id, str):
            mid = model_id.strip()
            if mid and mid not in cleaned_model_ids:
                cleaned_model_ids.append(mid)

    if cleaned_model_ids:
        results = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            task_type="comparison",
        ).all()

        by_model = {}
        for result in results:
            if result.thread_id not in session_pair_counts:
                continue
            evaluated_indices = []
            if result.payload_json and isinstance(result.payload_json, dict):
                evaluated_indices = result.payload_json.get("evaluated_indices", []) or []
            by_model.setdefault(result.model_id, {})[result.thread_id] = len(evaluated_indices)

        all_model_ids = sorted(set(list(by_model.keys()) + cleaned_model_ids))
        model_meta = {
            model.model_id: model
            for model in LLMModel.query.filter(LLMModel.model_id.in_(all_model_ids)).all()
        }

        total_pairs_all = sum(session_pair_counts.values())
        for model_id in all_model_ids:
            model_results = by_model.get(model_id, {})
            done_pairs = sum(model_results.get(session_id, 0) for session_id in session_pair_counts.keys())
            display_name = model_meta.get(model_id).display_name if model_meta.get(model_id) else model_id
            evaluator_stats.append({
                "username": display_name,
                "model_id": model_id,
                "is_llm": True,
                "total_threads": total_pairs_all,
                "done_threads": done_pairs,
                "not_started_threads": max(total_pairs_all - done_pairs, 0),
                "progressing_threads": 0,
                "done_threads_list": [],
                "not_started_threads_list": [],
                "progressing_threads_list": [],
            })

    return {
        "rater_stats": rater_stats,
        "evaluator_stats": evaluator_stats,
        "viewer_stats": evaluator_stats,  # backward compatibility
    }


def _calculate_krippendorff_alpha(ratings_matrix: np.ndarray) -> Optional[float]:
    """Calculate Krippendorff's Alpha for nominal data (binary)."""
    if ratings_matrix.size == 0:
        return None

    # Remove columns with all NaNs (no ratings for thread)
    valid_cols = ~np.isnan(ratings_matrix).all(axis=0)
    if not valid_cols.any():
        return None

    ratings = ratings_matrix[:, valid_cols]
    if ratings.shape[1] < 2:
        return None

    # Flatten all ratings and remove NaNs
    valid_all = ratings[~np.isnan(ratings)]
    n_total = len(valid_all)
    if n_total < 2:
        return None

    # Observed disagreement: average pairwise disagreement per unit
    D_o = 0.0
    for col in range(ratings.shape[1]):
        col_ratings = ratings[:, col]
        col_ratings = col_ratings[~np.isnan(col_ratings)]
        if len(col_ratings) < 2:
            continue
        for i in range(len(col_ratings)):
            for j in range(i + 1, len(col_ratings)):
                if col_ratings[i] != col_ratings[j]:
                    D_o += 1
    if ratings.shape[1] > 0:
        D_o = D_o / ratings.shape[1]

    # Count category frequencies
    n_real = np.sum(valid_all == 0)
    n_fake = np.sum(valid_all == 1)

    # Expected disagreement for nominal data
    D_e = (2 * n_real * n_fake) / (n_total * (n_total - 1))

    if D_e == 0:
        return 1.0 if D_o == 0 else None

    alpha = 1.0 - (D_o / D_e)
    return round(alpha, 4)


def _interpret_alpha(alpha: Optional[float]) -> str:
    """Interpret Krippendorff's Alpha value."""
    if alpha is None:
        return "Nicht berechenbar"
    if alpha >= 0.8:
        return "Sehr gut"
    if alpha >= 0.667:
        return "Akzeptabel"
    if alpha >= 0.4:
        return "Moderat"
    return "Gering"


def _calculate_rating_krippendorff_alpha(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate Krippendorff's Alpha for rating scenarios using interval metric.

    Uses ItemDimensionRating for human ratings and LLMTaskResult for LLM ratings.
    Returns alpha values split by evaluator type: all, humans, llms.

    Krippendorff's Alpha formula: α = 1 - (Do / De)
    For interval/ordinal data: δ(v, v') = (v - v')²

    Sources:
    - https://en.wikipedia.org/wiki/Krippendorff's_alpha
    - https://www.k-alpha.org/methodological-notes
    """
    # Get all thread IDs for this scenario
    scenario_threads = ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    thread_ids = [st.thread_id for st in scenario_threads if st.thread_id]
    if len(thread_ids) < 2:
        return {"all": None, "humans": None, "llms": None}

    # Collect ratings: {thread_id: {evaluator_id: score}}
    human_ratings: Dict[int, Dict[str, float]] = {tid: {} for tid in thread_ids}
    llm_ratings: Dict[int, Dict[str, float]] = {tid: {} for tid in thread_ids}

    # 1. Get human ratings from ItemDimensionRating
    human_rating_records = (
        ItemDimensionRating.query
        .filter_by(scenario_id=scenario_id).filter(ItemDimensionRating.status.in_([ProgressionStatus.DONE, ProgressionStatus.PROGRESSING]))
        .all()
    )

    for rating in human_rating_records:
        if rating.overall_score is not None and rating.item_id in thread_ids:
            evaluator_id = f"human:{rating.user_id}"
            human_ratings[rating.item_id][evaluator_id] = float(rating.overall_score)

    # 2. Get LLM ratings from LLMTaskResult (includes both rating and mail_rating)
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id
    ).filter(
        LLMTaskResult.task_type.in_(["rating", "mail_rating"]),
        LLMTaskResult.error.is_(None)
    ).all()

    for result in llm_results:
        if result.item_id not in thread_ids:
            continue

        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue

        # Extract overall_rating from payload
        overall_rating = None
        if payload.get("type") == "dimensional":
            overall_rating = payload.get("overall_rating")
        elif "overall_rating" in payload:
            overall_rating = payload.get("overall_rating")
        elif "rating" in payload:
            overall_rating = payload.get("rating")

        if overall_rating is not None:
            try:
                evaluator_id = f"llm:{result.model_id}"
                llm_ratings[result.item_id][evaluator_id] = float(overall_rating)
            except (ValueError, TypeError):
                pass

    def calculate_alpha(ratings_dict: Dict[int, Dict[str, float]]) -> Optional[float]:
        """Calculate Krippendorff's Alpha for interval data."""
        # Collect all values per unit (thread)
        units_with_values = []
        all_values = []

        for thread_id, evaluator_scores in ratings_dict.items():
            values = list(evaluator_scores.values())
            if len(values) >= 2:  # Need at least 2 raters per unit
                units_with_values.append(values)
                all_values.extend(values)

        if len(units_with_values) < 2 or len(all_values) < 4:
            return None

        # Calculate observed disagreement (Do)
        # Sum of squared differences within each unit, normalized
        do_sum = 0.0
        pair_count_observed = 0

        for values in units_with_values:
            n = len(values)
            for i in range(n):
                for j in range(i + 1, n):
                    do_sum += (values[i] - values[j]) ** 2
                    pair_count_observed += 1

        if pair_count_observed == 0:
            return None

        do = do_sum / pair_count_observed

        # Calculate expected disagreement (De)
        # Sum of squared differences across all values
        de_sum = 0.0
        n_total = len(all_values)
        pair_count_expected = 0

        for i in range(n_total):
            for j in range(i + 1, n_total):
                de_sum += (all_values[i] - all_values[j]) ** 2
                pair_count_expected += 1

        if pair_count_expected == 0:
            return None

        de = de_sum / pair_count_expected

        # Calculate alpha
        if de == 0:
            return 1.0 if do == 0 else None

        alpha = 1.0 - (do / de)
        return round(alpha, 4)

    # Combine human and LLM ratings for "all"
    all_ratings: Dict[int, Dict[str, float]] = {tid: {} for tid in thread_ids}
    for tid in thread_ids:
        all_ratings[tid].update(human_ratings.get(tid, {}))
        all_ratings[tid].update(llm_ratings.get(tid, {}))

    return {
        "all": calculate_alpha(all_ratings),
        "humans": calculate_alpha(human_ratings),
        "llms": calculate_alpha(llm_ratings),
    }


def _calculate_rating_distribution(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate rating distribution for a rating scenario.

    For scenarios with per-dimension scales, returns distribution per dimension.
    For scenarios with uniform scales, returns overall_score distribution.

    Returns dict with:
    - 'all', 'humans', 'llms': overall score distributions
    - 'by_dimension': per-dimension distributions (for mixed scales)
    - 'has_mixed_scales': boolean indicating if dimensions have different scales
    """
    # Get scenario config first to determine scales
    scenario = RatingScenarios.query.get(scenario_id)
    config = scenario.config_json if scenario else {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    # Get scale configuration - check root level, eval_config, and eval_config.config
    eval_config = config.get("eval_config", {})
    if not isinstance(eval_config, dict):
        eval_config = {}

    eval_config_inner = eval_config.get("config", {})
    if not isinstance(eval_config_inner, dict):
        eval_config_inner = {}

    # Scale can be at root level, eval_config, or eval_config.config (from wizard)
    global_min = config.get("min", eval_config.get("min", eval_config_inner.get("min", 1)))
    global_max = config.get("max", eval_config.get("max", eval_config_inner.get("max", 5)))
    global_labels = config.get("labels", eval_config.get("labels", eval_config_inner.get("labels", {})))
    dimensions = config.get("dimensions", eval_config.get("dimensions", eval_config_inner.get("dimensions", [])))

    # Check if we have mixed scales (per-dimension scales)
    has_mixed_scales = False
    dimension_scales = {}
    for dim in dimensions:
        dim_id = dim.get("id")
        if dim.get("scale"):
            has_mixed_scales = True
            dim_scale = dim["scale"]
            dimension_scales[dim_id] = {
                "min": dim_scale.get("min", global_min),
                "max": dim_scale.get("max", global_max),
                "labels": dim_scale.get("labels", {}),
                "name": dim.get("name", {})
            }
        else:
            dimension_scales[dim_id] = {
                "min": global_min,
                "max": global_max,
                "labels": global_labels,
                "name": dim.get("name", {})
            }

    # Collect dimension ratings from humans and LLMs
    human_dim_ratings: Dict[str, Dict[int, int]] = {}  # {dim_id: {score: count}}
    llm_dim_ratings: Dict[str, Dict[int, int]] = {}

    # Initialize dimension counters
    for dim_id in dimension_scales:
        human_dim_ratings[dim_id] = {}
        llm_dim_ratings[dim_id] = {}

    # 1. Get human ratings from ItemDimensionRating
    human_ratings = (
        ItemDimensionRating.query
        .filter_by(scenario_id=scenario_id).filter(ItemDimensionRating.status.in_([ProgressionStatus.DONE, ProgressionStatus.PROGRESSING]))
        .all()
    )

    for rating in human_ratings:
        dim_scores = rating.dimension_ratings
        if not dim_scores or not isinstance(dim_scores, dict):
            continue
        for dim_id, score in dim_scores.items():
            if dim_id in human_dim_ratings and score is not None:
                try:
                    score_int = round(float(score))
                    human_dim_ratings[dim_id][score_int] = human_dim_ratings[dim_id].get(score_int, 0) + 1
                except (ValueError, TypeError):
                    pass

    # 2. Get LLM ratings from LLMTaskResult (includes both rating and mail_rating)
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id
    ).filter(
        LLMTaskResult.task_type.in_(["rating", "mail_rating"]),
        LLMTaskResult.error.is_(None)
    ).all()

    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue

        # Extract dimension ratings from payload
        # Support both formats:
        # 1. {"ratings": {"dim_id": score, ...}} - legacy format
        # 2. {"dimensional_ratings": [{"dimension": "dim_id", "rating": score}, ...]} - new format
        ratings = payload.get("ratings", {})
        dimensional_ratings = payload.get("dimensional_ratings", [])

        # Handle legacy dict format
        if isinstance(ratings, dict):
            for dim_id, score in ratings.items():
                if dim_id in llm_dim_ratings and score is not None:
                    try:
                        score_int = round(float(score))
                        llm_dim_ratings[dim_id][score_int] = llm_dim_ratings[dim_id].get(score_int, 0) + 1
                    except (ValueError, TypeError):
                        pass

        # Handle new array format
        if isinstance(dimensional_ratings, list):
            for rating_item in dimensional_ratings:
                if not isinstance(rating_item, dict):
                    continue
                dim_id = rating_item.get("dimension") or rating_item.get("dimension_id")
                score = rating_item.get("rating") or rating_item.get("score") or rating_item.get("value")
                if dim_id in llm_dim_ratings and score is not None:
                    try:
                        score_int = round(float(score))
                        llm_dim_ratings[dim_id][score_int] = llm_dim_ratings[dim_id].get(score_int, 0) + 1
                    except (ValueError, TypeError):
                        pass

    def build_dimension_distribution(
        dim_id: str,
        human_counts: Dict[int, int],
        llm_counts: Dict[int, int],
        scale_info: Dict
    ) -> Dict[str, Any]:
        """Build distribution for a single dimension."""
        scale_min = scale_info["min"]
        scale_max = scale_info["max"]
        labels = scale_info["labels"]
        name = scale_info["name"]

        def build_dist(counts: Dict[int, int]) -> List[Dict[str, Any]]:
            # Always return full scale with zero counts if needed (for consistent UI display)
            total = sum(counts.values()) if counts else 0
            distribution = []
            for score in range(scale_min, scale_max + 1):
                count = counts.get(score, 0)
                label_data = labels.get(str(score), {})
                # Send both language versions to frontend for i18n selection
                if isinstance(label_data, dict):
                    label_en = label_data.get("en", str(score))
                    label_de = label_data.get("de", str(score))
                else:
                    label_en = str(label_data) if label_data else str(score)
                    label_de = label_en
                distribution.append({
                    "label": f"{score} - {label_en}" if label_en != str(score) else str(score),
                    "label_en": label_en,
                    "label_de": label_de,
                    "value": score,
                    "count": count,
                    "percentage": round((count / total) * 100) if total > 0 else 0
                })
            return distribution

        # Combine for "all"
        all_counts = {}
        for score, count in human_counts.items():
            all_counts[score] = all_counts.get(score, 0) + count
        for score, count in llm_counts.items():
            all_counts[score] = all_counts.get(score, 0) + count

        return {
            "dimension_id": dim_id,
            "dimension_name": name.get("en", name.get("de", dim_id)) if isinstance(name, dict) else str(name),
            "scale_min": scale_min,
            "scale_max": scale_max,
            "all": build_dist(all_counts),
            "humans": build_dist(human_counts),
            "llms": build_dist(llm_counts)
        }

    # Build per-dimension distributions
    by_dimension = []
    for dim_id, scale_info in dimension_scales.items():
        dim_dist = build_dimension_distribution(
            dim_id,
            human_dim_ratings.get(dim_id, {}),
            llm_dim_ratings.get(dim_id, {}),
            scale_info
        )
        by_dimension.append(dim_dist)

    # Also build overall score distribution for backwards compatibility
    human_overall: Dict[int, int] = {}
    llm_overall: Dict[int, int] = {}

    for rating in human_ratings:
        if rating.overall_score is not None:
            score = round(rating.overall_score)
            human_overall[score] = human_overall.get(score, 0) + 1

    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue
        overall_rating = payload.get("overall_rating") or payload.get("rating")
        if overall_rating is not None:
            try:
                score = round(float(overall_rating))
                llm_overall[score] = llm_overall.get(score, 0) + 1
            except (ValueError, TypeError):
                pass

    def build_overall_distribution(counts: Dict[int, int]) -> List[Dict[str, Any]]:
        # Always return full scale with zero counts if needed (for consistent UI display)
        total = sum(counts.values()) if counts else 0
        distribution = []
        # Use global scale for overall distribution
        for score in range(global_min, global_max + 1):
            count = counts.get(score, 0)
            label_data = global_labels.get(str(score), {})
            if isinstance(label_data, dict):
                label = label_data.get("en", label_data.get("de", str(score)))
            else:
                label = str(label_data) if label_data else str(score)
            distribution.append({
                "label": f"{score} - {label}" if label != str(score) else str(score),
                "value": score,
                "count": count,
                "percentage": round((count / total) * 100) if total > 0 else 0
            })
        return distribution

    all_overall = {}
    for score, count in human_overall.items():
        all_overall[score] = all_overall.get(score, 0) + count
    for score, count in llm_overall.items():
        all_overall[score] = all_overall.get(score, 0) + count

    return {
        "all": build_overall_distribution(all_overall),
        "humans": build_overall_distribution(human_overall),
        "llms": build_overall_distribution(llm_overall),
        "by_dimension": by_dimension,
        "has_mixed_scales": has_mixed_scales
    }


def _calculate_dimension_averages(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate average scores per dimension for a rating scenario.

    Returns dimension averages split by evaluator type (all, humans, LLMs).
    Includes both human ratings from ItemDimensionRating and LLM ratings from LLMTaskResult.
    """
    # Get scenario config for dimension info
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        return {}

    config = scenario.config_json if scenario else {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    # Get dimensions and eval_config from config
    # Dimensions can be at multiple locations:
    # 1. config.dimensions (direct)
    # 2. config.eval_config.dimensions (nested in eval_config)
    # 3. config.eval_config.config.dimensions (nested in eval_config.config - from wizard)
    eval_config = config.get("eval_config", {})
    if not isinstance(eval_config, dict):
        eval_config = {}

    eval_config_inner = eval_config.get("config", {})
    if not isinstance(eval_config_inner, dict):
        eval_config_inner = {}

    dimensions = config.get("dimensions", [])
    if not dimensions:
        dimensions = eval_config.get("dimensions", [])
    if not dimensions:
        dimensions = eval_config_inner.get("dimensions", [])
    if not dimensions:
        return {}

    dimension_ids = [d.get("id") for d in dimensions]

    # Collect all dimension scores: list of {dim_id: score} dicts
    from collections import defaultdict
    human_scores = []  # List of {dim_id: score} dicts
    llm_scores = []    # List of {dim_id: score} dicts

    # 1. Get human ratings from ItemDimensionRating
    human_ratings = (
        ItemDimensionRating.query
        .filter_by(scenario_id=scenario_id).filter(ItemDimensionRating.status.in_([ProgressionStatus.DONE, ProgressionStatus.PROGRESSING]))
        .all()
    )

    for rating in human_ratings:
        scores = rating.dimension_ratings or {}
        if isinstance(scores, str):
            try:
                scores = json.loads(scores)
            except (json.JSONDecodeError, TypeError):
                scores = {}
        if scores:
            human_scores.append(scores)

    # 2. Get LLM ratings from LLMTaskResult (dimensional format, includes mail_rating)
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id
    ).filter(
        LLMTaskResult.task_type.in_(["rating", "mail_rating"]),
        LLMTaskResult.error.is_(None)
    ).all()

    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue

        # Check for dimensional format: {"type": "dimensional", "dimensional_ratings": [...]}
        if payload.get("type") == "dimensional" and "dimensional_ratings" in payload:
            dim_ratings = payload.get("dimensional_ratings", [])
            scores = {}
            for dr in dim_ratings:
                dim_id = dr.get("dimension")
                rating_val = dr.get("rating")
                if dim_id and rating_val is not None:
                    scores[dim_id] = rating_val
            if scores:
                llm_scores.append(scores)

    # If no data at all, return empty
    if not human_scores and not llm_scores:
        return {
            "dimensions": [{"id": d.get("id"), "label": d.get("name", {}).get("en", d.get("id"))} for d in dimensions],
            "series": []
        }

    def calc_averages(scores_list):
        """Calculate average for each dimension from a list of score dicts."""
        dim_sums = {dim_id: 0.0 for dim_id in dimension_ids}
        dim_counts = {dim_id: 0 for dim_id in dimension_ids}

        for scores in scores_list:
            for dim_id in dimension_ids:
                if dim_id in scores and scores[dim_id] is not None:
                    dim_sums[dim_id] += float(scores[dim_id])
                    dim_counts[dim_id] += 1

        return [
            round(dim_sums[dim_id] / dim_counts[dim_id], 2) if dim_counts[dim_id] > 0 else 0
            for dim_id in dimension_ids
        ]

    series = []

    # All evaluators (humans + LLMs)
    all_scores = human_scores + llm_scores
    if all_scores:
        series.append({
            "label": "All",
            "values": calc_averages(all_scores),
            "color": "primary"
        })

    # Humans only
    if human_scores:
        series.append({
            "label": "Humans",
            "values": calc_averages(human_scores),
            "color": "secondary"
        })

    # LLMs only
    if llm_scores:
        series.append({
            "label": "LLMs",
            "values": calc_averages(llm_scores),
            "color": "accent"
        })

    # Get maxValue from config (can be at root level or in eval_config)
    max_value = config.get("max") or eval_config.get("max", 5)

    return {
        "dimensions": [
            {
                "id": d.get("id"),
                "label": d.get("name", {}).get("en", d.get("id"))
            }
            for d in dimensions
        ],
        "series": series,
        "maxValue": max_value
    }


def _calculate_pairwise_agreement(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate pairwise agreement between evaluators.

    Returns agreement scores for each pair of evaluators who have
    rated the same items. Includes both human ratings and LLM ratings.
    """
    from collections import defaultdict

    # item_id -> {evaluator_id: overall_score}
    item_ratings = defaultdict(dict)
    users_set = set()
    user_info = {}

    # 1. Get human ratings from ItemDimensionRating
    human_ratings = (
        ItemDimensionRating.query
        .filter_by(scenario_id=scenario_id).filter(ItemDimensionRating.status.in_([ProgressionStatus.DONE, ProgressionStatus.PROGRESSING]))
        .all()
    )

    for rating in human_ratings:
        item_id = rating.item_id
        user_id = rating.user_id
        users_set.add(user_id)

        # Store user info
        if user_id not in user_info:
            user = User.query.get(user_id)
            name = user.username if user else f"User {user_id}"
            user_info[user_id] = {"id": user_id, "name": name, "isLLM": False}

        if rating.overall_score is not None:
            item_ratings[item_id][user_id] = rating.overall_score

    # 2. Get LLM ratings from LLMTaskResult (includes both rating and mail_rating)
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id
    ).filter(
        LLMTaskResult.task_type.in_(["rating", "mail_rating"]),
        LLMTaskResult.error.is_(None)
    ).all()

    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue

        # Extract overall_rating from various formats:
        # 1. Dimensional format: {"type": "dimensional", "overall_rating": X}
        # 2. Overall rating field: {"overall_rating": X}
        # 3. Simple rating format (mail_rating): {"rating": X, "reasoning": "..."}
        overall_rating = None
        if payload.get("type") == "dimensional":
            overall_rating = payload.get("overall_rating")
        elif "overall_rating" in payload:
            overall_rating = payload.get("overall_rating")
        elif "rating" in payload:
            overall_rating = payload.get("rating")

        if overall_rating is not None:
            item_id = result.item_id
            model_id = result.model_id
            llm_user_id = f"llm:{model_id}"

            users_set.add(llm_user_id)

            # Store LLM info
            if llm_user_id not in user_info:
                # Get display name from LLM model if available
                llm_model = LLMModel.query.filter_by(model_id=model_id).first()
                name = llm_model.display_name if llm_model else model_id.split("/")[-1]
                user_info[llm_user_id] = {"id": llm_user_id, "name": name, "isLLM": True}

            item_ratings[item_id][llm_user_id] = overall_rating

    if not users_set:
        return {"evaluators": [], "agreements": {}}

    # Build evaluator list
    evaluators = list(user_info.values())

    # Calculate pairwise agreement (exact match after rounding)
    agreements = {}
    user_list = list(users_set)

    for i, user1 in enumerate(user_list):
        for user2 in user_list[i+1:]:
            # Find common items
            common_items = []
            for item_id, user_scores in item_ratings.items():
                if user1 in user_scores and user2 in user_scores:
                    common_items.append((user_scores[user1], user_scores[user2]))

            if len(common_items) >= 1:
                # Calculate agreement (percentage of exact matches, rounded to integers)
                agreements_count = sum(
                    1 for s1, s2 in common_items if round(s1) == round(s2)
                )
                agreement = agreements_count / len(common_items)

                # Store with sorted key for consistency
                key = f"{min(str(user1), str(user2))}-{max(str(user1), str(user2))}"
                agreements[key] = round(agreement, 3)

    return {
        "evaluators": evaluators,
        "agreements": agreements
    }


def _calculate_bucket_distribution(scenario_id: int) -> List[Dict[str, Any]]:
    """
    Calculate bucket distribution for a ranking scenario.

    Returns distribution of items across buckets. Reads bucket configuration
    from scenario config_json to support dynamic number of buckets (2, 3, 4, etc.).
    Includes both human and LLM evaluator bucket assignments.
    """
    from db.models import UserFeatureRanking, Feature, ScenarioItems, RatingScenarios

    # Get scenario to read bucket configuration
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        return []

    # Get bucket configuration from config_json
    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}

    configured_buckets = config.get("buckets", [])

    # Fallback to legacy 3-bucket system if no buckets configured
    if not configured_buckets:
        configured_buckets = [
            {"id": "gut", "name": {"de": "Gut", "en": "Good"}, "color": "#b0ca97"},
            {"id": "mittel", "name": {"de": "Mittel", "en": "Medium"}, "color": "#e8c87a"},
            {"id": "schlecht", "name": {"de": "Schlecht", "en": "Bad"}, "color": "#e8a087"},
        ]

    # Build bucket ID mapping (normalize names to IDs)
    bucket_ids = []
    bucket_info = {}
    for bucket in configured_buckets:
        bucket_id = bucket.get("id") or bucket.get("name", {}).get("de", "").lower()
        if not bucket_id:
            continue
        bucket_ids.append(bucket_id)
        bucket_info[bucket_id] = {
            "label": bucket.get("name", {}).get("de") or bucket_id,
            "color": bucket.get("color", "#88c4c8")
        }

    if not bucket_ids:
        return []

    # Initialize counts for all configured buckets
    bucket_counts = {bid: 0 for bid in bucket_ids}

    # Legacy bucket name mappings (for backwards compatibility)
    legacy_mappings = {
        "good": "gut",
        "medium": "mittel",
        "middle": "mittel",
        "bad": "schlecht",
        "poor": "schlecht",
    }

    def normalize_bucket_name(name: str) -> Optional[str]:
        """Normalize bucket name to match configured bucket IDs."""
        if not name:
            return None
        name_lower = name.lower().strip()

        # Direct match
        if name_lower in bucket_counts:
            return name_lower

        # Try legacy mapping
        if name_lower in legacy_mappings:
            mapped = legacy_mappings[name_lower]
            if mapped in bucket_counts:
                return mapped

        # Try matching by label
        for bid, info in bucket_info.items():
            if info["label"].lower() == name_lower:
                return bid

        return None

    # Get all items for this scenario
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    if not item_ids:
        return []

    # 1. Get human rankings
    human_rankings = (
        UserFeatureRanking.query
        .join(Feature, UserFeatureRanking.feature_id == Feature.feature_id)
        .filter(Feature.thread_id.in_(item_ids))
        .filter(UserFeatureRanking.bucket.isnot(None))
        .all()
    )

    for ranking in human_rankings:
        normalized = normalize_bucket_name(ranking.bucket)
        if normalized:
            bucket_counts[normalized] += 1

    # 2. Get LLM rankings from llm_task_results
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id,
        task_type="ranking"
    ).filter(LLMTaskResult.error.is_(None)).all()

    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue

        # Count items in each bucket from payload
        for key, value in payload.items():
            if isinstance(value, list):
                normalized = normalize_bucket_name(key)
                if normalized:
                    bucket_counts[normalized] += len(value)

    total = sum(bucket_counts.values())
    if total == 0:
        return []

    # Build distribution in configured bucket order
    distribution = []
    for bucket_id in bucket_ids:
        count = bucket_counts[bucket_id]
        info = bucket_info[bucket_id]
        distribution.append({
            "bucket": bucket_id,
            "label": info["label"],
            "count": count,
            "percentage": round((count / total) * 100) if total > 0 else 0,
            "color": info["color"]
        })

    return distribution


def _calculate_ranking_agreement_heatmap(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate pairwise bucket agreement between evaluators for ranking scenarios.

    Each feature (Zusammenfassung) is placed into exactly one bucket by each evaluator.
    Agreement = number of features where both evaluators chose the same bucket,
    divided by the total number of co-rated features.

    Example: 2 evaluators rated 40 features, agree on bucket for 23 → 57.5%
    """
    from db.models import UserFeatureRanking, Feature, ScenarioItems
    from collections import defaultdict

    # Get all items for this scenario
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    if not item_ids:
        return {"evaluators": [], "agreements": {}}

    # feature_id -> {evaluator_id: bucket}
    feature_buckets = defaultdict(dict)
    users_set = set()
    user_info = {}

    # Bucket name normalization map
    bucket_normalize = {
        "gut": "gut", "good": "gut",
        "mittel": "mittel", "medium": "mittel", "middle": "mittel",
        "neutral": "neutral",
        "schlecht": "schlecht", "bad": "schlecht", "poor": "schlecht",
    }
    valid_buckets = {"gut", "mittel", "neutral", "schlecht"}

    # 1. Get human rankings - each row is one feature → one bucket
    human_rankings = (
        UserFeatureRanking.query
        .join(Feature, UserFeatureRanking.feature_id == Feature.feature_id)
        .filter(Feature.item_id.in_(item_ids))
        .filter(UserFeatureRanking.bucket.isnot(None))
        .all()
    )

    for ranking in human_rankings:
        feature_id = ranking.feature_id
        user_id = ranking.user_id
        raw_bucket = ranking.bucket.lower() if ranking.bucket else None
        if not raw_bucket:
            continue
        bucket = bucket_normalize.get(raw_bucket, raw_bucket)
        if bucket not in valid_buckets:
            continue

        users_set.add(user_id)
        if user_id not in user_info:
            user = User.query.get(user_id)
            name = user.username if user else f"User {user_id}"
            user_info[user_id] = {"id": user_id, "name": name, "isLLM": False}

        feature_buckets[feature_id][user_id] = bucket

    # 2. Get LLM rankings - payload maps bucket → [feature_ids]
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id,
        task_type="ranking"
    ).filter(LLMTaskResult.error.is_(None)).all()

    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue

        model_id = result.model_id
        llm_user_id = f"llm:{model_id}"
        users_set.add(llm_user_id)

        if llm_user_id not in user_info:
            llm_model = LLMModel.query.filter_by(model_id=model_id).first()
            name = llm_model.display_name if llm_model else model_id.split("/")[-1]
            user_info[llm_user_id] = {"id": llm_user_id, "name": name, "isLLM": True}

        # Unpack: each feature_id gets its bucket directly
        for bucket_key, feature_ids in payload.items():
            normalized = bucket_normalize.get(bucket_key.lower() if isinstance(bucket_key, str) else "", None)
            if normalized is None or normalized not in valid_buckets:
                continue
            if isinstance(feature_ids, list):
                for fid in feature_ids:
                    feature_buckets[fid][llm_user_id] = normalized

    if not users_set:
        return {"evaluators": [], "agreements": {}}

    evaluators = list(user_info.values())

    # Calculate pairwise agreement at feature level
    # For each pair: % of features where both assigned the same bucket
    agreements = {}
    user_list = list(users_set)

    for i, user1 in enumerate(user_list):
        for user2 in user_list[i + 1:]:
            shared_count = 0
            agree_count = 0
            for feature_id, evaluator_buckets in feature_buckets.items():
                if user1 in evaluator_buckets and user2 in evaluator_buckets:
                    shared_count += 1
                    if evaluator_buckets[user1] == evaluator_buckets[user2]:
                        agree_count += 1

            if shared_count >= 1:
                agreement = agree_count / shared_count
                key = f"{min(str(user1), str(user2))}-{max(str(user1), str(user2))}"
                agreements[key] = round(agreement, 3)

    return {
        "evaluators": evaluators,
        "agreements": agreements
    }


def _calculate_labeling_pairwise_agreement(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate pairwise agreement between evaluators for labeling scenarios.

    Agreement is measured by how often evaluators assign the same category to an item.
    """
    from collections import defaultdict

    # Get all items for this scenario
    scenario_threads = ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [st.thread_id for st in scenario_threads if st.thread_id]

    if not item_ids:
        return {"evaluators": [], "agreements": {}}

    # item_id -> {evaluator_id: category_id}
    item_categories = defaultdict(dict)
    users_set = set()
    user_info = {}

    # 1. Get human labeling evaluations
    human_labelings = (
        ItemLabelingEvaluation.query
        .filter(
            ItemLabelingEvaluation.scenario_id == scenario_id,
            ItemLabelingEvaluation.item_id.in_(item_ids),
            ItemLabelingEvaluation.category_id.isnot(None)
        )
        .all()
    )

    for labeling in human_labelings:
        item_id = labeling.item_id
        user_id = labeling.user_id
        category_id = labeling.category_id

        if not item_id or not category_id:
            continue

        users_set.add(user_id)
        if user_id not in user_info:
            user = User.query.get(user_id)
            name = user.username if user else f"User {user_id}"
            user_info[user_id] = {"id": user_id, "name": name, "isLLM": False}

        item_categories[item_id][user_id] = category_id

    # 2. Get LLM labeling results
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id,
        task_type="labeling"
    ).filter(LLMTaskResult.error.is_(None)).all()

    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue

        model_id = result.model_id
        llm_user_id = f"llm:{model_id}"
        item_id = result.item_id

        if item_id not in item_ids:
            continue

        # Extract category from payload
        category_id = payload.get("category_id") or payload.get("category") or payload.get("label")
        if not category_id:
            continue

        users_set.add(llm_user_id)
        if llm_user_id not in user_info:
            llm_model = LLMModel.query.filter_by(model_id=model_id).first()
            name = llm_model.display_name if llm_model else model_id.split("/")[-1]
            user_info[llm_user_id] = {"id": llm_user_id, "name": name, "isLLM": True}

        item_categories[item_id][llm_user_id] = category_id

    if not users_set:
        return {"evaluators": [], "agreements": {}}

    evaluators = list(user_info.values())

    # Calculate pairwise agreement (percentage of items with same category)
    agreements = {}
    user_list = list(users_set)

    for i, user1 in enumerate(user_list):
        for user2 in user_list[i+1:]:
            common_items = []
            for item_id, user_cats in item_categories.items():
                if user1 in user_cats and user2 in user_cats:
                    common_items.append((user_cats[user1], user_cats[user2]))

            if len(common_items) >= 1:
                # Calculate agreement (percentage with same category)
                agreements_count = sum(1 for c1, c2 in common_items if c1 == c2)
                agreement = agreements_count / len(common_items)

                key = f"{min(str(user1), str(user2))}-{max(str(user1), str(user2))}"
                agreements[key] = round(agreement, 3)

    return {
        "evaluators": evaluators,
        "agreements": agreements
    }


def _calculate_mail_rating_pairwise_agreement(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate pairwise agreement between evaluators for mail_rating scenarios.

    Includes both new ItemDimensionRating and legacy UserMailHistoryRating data.
    Agreement is calculated using overall_score/overall_rating (exact match after rounding).
    """
    from collections import defaultdict

    # Get all items for this scenario
    scenario_threads = ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [st.thread_id for st in scenario_threads if st.thread_id]

    if not item_ids:
        return {"evaluators": [], "agreements": {}}

    # item_id -> {evaluator_id: overall_score}
    item_ratings = defaultdict(dict)
    users_set = set()
    user_info = {}

    # 1. Get ratings from ItemDimensionRating (new system)
    new_ratings = (
        ItemDimensionRating.query
        .filter_by(scenario_id=scenario_id)
        .filter(ItemDimensionRating.status.in_([ProgressionStatus.DONE, ProgressionStatus.PROGRESSING]))
        .all()
    )

    for rating in new_ratings:
        item_id = rating.item_id
        user_id = rating.user_id

        if item_id not in item_ids:
            continue

        users_set.add(user_id)
        if user_id not in user_info:
            user = User.query.get(user_id)
            name = user.username if user else f"User {user_id}"
            user_info[user_id] = {"id": user_id, "name": name, "isLLM": False}

        if rating.overall_score is not None:
            item_ratings[item_id][user_id] = rating.overall_score

    # 2. Get ratings from UserMailHistoryRating (legacy system)
    legacy_ratings = (
        UserMailHistoryRating.query
        .filter(
            UserMailHistoryRating.item_id.in_(item_ids),
            UserMailHistoryRating.overall_rating.isnot(None),
            UserMailHistoryRating.status.in_([ProgressionStatus.DONE, ProgressionStatus.PROGRESSING])
        )
        .all()
    )

    for rating in legacy_ratings:
        item_id = rating.item_id
        user_id = rating.user_id

        # Check if this item belongs to this scenario
        if item_id not in item_ids:
            continue

        users_set.add(user_id)
        if user_id not in user_info:
            user = User.query.get(user_id)
            name = user.username if user else f"User {user_id}"
            user_info[user_id] = {"id": user_id, "name": name, "isLLM": False}

        # Only add if not already present from new system
        if user_id not in item_ratings.get(item_id, {}):
            item_ratings[item_id][user_id] = float(rating.overall_rating)

    # 3. Get LLM ratings from LLMTaskResult
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id,
        task_type="mail_rating"
    ).filter(LLMTaskResult.error.is_(None)).all()

    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue

        model_id = result.model_id
        llm_user_id = f"llm:{model_id}"
        item_id = result.item_id

        if item_id not in item_ids:
            continue

        # Extract overall_rating from payload
        overall_rating = None
        if payload.get("type") == "dimensional":
            overall_rating = payload.get("overall_rating")
        elif "overall_rating" in payload:
            overall_rating = payload.get("overall_rating")
        elif "rating" in payload:
            overall_rating = payload.get("rating")

        if overall_rating is not None:
            users_set.add(llm_user_id)
            if llm_user_id not in user_info:
                llm_model = LLMModel.query.filter_by(model_id=model_id).first()
                name = llm_model.display_name if llm_model else model_id.split("/")[-1]
                user_info[llm_user_id] = {"id": llm_user_id, "name": name, "isLLM": True}

            item_ratings[item_id][llm_user_id] = float(overall_rating)

    if not users_set:
        return {"evaluators": [], "agreements": {}}

    evaluators = list(user_info.values())

    # Calculate pairwise agreement (exact match after rounding)
    agreements = {}
    user_list = list(users_set)

    for i, user1 in enumerate(user_list):
        for user2 in user_list[i+1:]:
            common_items = []
            for item_id, user_scores in item_ratings.items():
                if user1 in user_scores and user2 in user_scores:
                    common_items.append((user_scores[user1], user_scores[user2]))

            if len(common_items) >= 1:
                # Calculate agreement (exact match after rounding to integers)
                agreements_count = sum(1 for s1, s2 in common_items if round(s1) == round(s2))
                agreement = agreements_count / len(common_items)

                key = f"{min(str(user1), str(user2))}-{max(str(user1), str(user2))}"
                agreements[key] = round(agreement, 3)

    return {
        "evaluators": evaluators,
        "agreements": agreements
    }


def _calculate_authenticity_pairwise_agreement(
    *,
    user_stats: List[Dict],
    llm_user_stats: List[Dict],
    user_vote_map: Dict[int, Dict],
    llm_vote_map: Dict[str, Dict],
    thread_ids: List[int],
) -> Dict[str, Any]:
    """
    Calculate pairwise agreement between evaluators for authenticity scenarios.

    Agreement is calculated as the percentage of threads where two evaluators
    gave the same vote (both "real" or both "fake").

    Returns:
        Dict with 'evaluators' list and 'agreements' dict with agreement scores.
    """
    evaluators = []
    all_raters = []  # List of (rater_id, is_llm, vote_dict)

    # Add human evaluators
    for u in user_stats:
        if u.get("is_llm"):
            continue  # Skip LLMs already in user_stats
        user_id = u.get("user_id")
        if user_id and u.get("voted_count", 0) > 0:
            evaluators.append({
                "id": user_id,
                "name": u.get("username", f"User {user_id}"),
                "isLLM": False
            })
            # Convert user_vote_map values to simple vote strings
            vote_dict = {}
            for tid, vote_obj in user_vote_map.get(user_id, {}).items():
                if vote_obj and vote_obj.vote:
                    vote_dict[tid] = vote_obj.vote.lower()
            all_raters.append((user_id, False, vote_dict))

    # Add LLM evaluators
    for llm_stat in llm_user_stats:
        model_id = llm_stat.get("model_id")
        if model_id and llm_stat.get("voted_count", 0) > 0:
            llm_id = f"llm:{model_id}"
            evaluators.append({
                "id": llm_id,
                "name": llm_stat.get("username", model_id.split("/")[-1]),
                "isLLM": True
            })
            # Convert llm_vote_map to lowercase
            vote_dict = {
                tid: vote.lower()
                for tid, vote in llm_vote_map.get(model_id, {}).items()
            }
            all_raters.append((llm_id, True, vote_dict))

    if len(all_raters) < 2:
        return {"evaluators": evaluators, "agreements": {}}

    # Calculate pairwise agreement
    agreements = {}

    for i, (rater1_id, is_llm1, votes1) in enumerate(all_raters):
        for rater2_id, is_llm2, votes2 in all_raters[i + 1:]:
            # Find common threads both evaluators voted on
            common_threads = set(votes1.keys()) & set(votes2.keys())

            if len(common_threads) >= 1:
                # Count agreements (both voted same)
                agreements_count = sum(
                    1 for tid in common_threads
                    if votes1[tid] == votes2[tid]
                )
                agreement = agreements_count / len(common_threads)

                # Store with sorted key for consistency
                key = f"{min(str(rater1_id), str(rater2_id))}-{max(str(rater1_id), str(rater2_id))}"
                agreements[key] = round(agreement, 3)

    return {
        "evaluators": evaluators,
        "agreements": agreements
    }


def get_authenticity_stats(scenario_id: int) -> Dict[str, Any]:
    """Get comprehensive statistics for an authenticity scenario."""
    scenario = _get_scenario_or_raise(scenario_id)

    # Only include active members in stats
    scenario_users = (
        db.session.query(ScenarioUsers)
        .join(User, ScenarioUsers.user_id == User.id)
        .filter(
            ScenarioUsers.scenario_id == scenario_id,
            ScenarioUsers.membership_status == MembershipStatus.ACTIVE
        )
        .all()
    )

    scenario_threads = (
        db.session.query(ScenarioThreads)
        .filter(ScenarioThreads.scenario_id == scenario_id)
        .all()
    )
    thread_ids = [st.thread.thread_id for st in scenario_threads if st.thread]

    if not thread_ids:
        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario.scenario_name,
            "total_threads": 0,
            "total_users": len(scenario_users),
            "user_stats": [],
            "krippendorff_alpha": None,
            "alpha_interpretation": "Keine Daten",
            "vote_distribution": {"real": 0, "fake": 0, "pending": 0},
            "accuracy": None,
            "ground_truth_stats": {"fake_count": 0, "real_count": 0},
        }

    # Get ground truth from AuthenticityConversation
    ground_truth = {}
    auth_convs = AuthenticityConversation.query.filter(
        AuthenticityConversation.thread_id.in_(thread_ids)
    ).all()
    for ac in auth_convs:
        ground_truth[ac.thread_id] = ac.is_fake

    fake_count = sum(1 for v in ground_truth.values() if v)
    real_count = sum(1 for v in ground_truth.values() if not v)

    # Get all votes for these threads
    all_votes = UserAuthenticityVote.query.filter(
        UserAuthenticityVote.thread_id.in_(thread_ids)
    ).all()

    distribution_mode = get_scenario_distribution_mode(scenario, scenario.function_type_id)

    # Build user stats
    user_stats = []
    user_vote_map = {}  # user_id -> {thread_id -> vote}

    thread_subjects = {
        thread.thread_id: thread.subject
        for thread in EmailThread.query.filter(EmailThread.thread_id.in_(thread_ids)).all()
    }

    for su in scenario_users:
        user = su.user
        user_id = user.id

        # Get threads assigned to this user (for RATER role) or all threads (for EVALUATOR)
        if su.role == ScenarioRoles.EVALUATOR and distribution_mode != DISTRIBUTION_MODE_ALL:
            user_thread_ids = [
                dist.scenario_thread.thread.thread_id
                for dist in (
                    ScenarioThreadDistribution.query
                    .join(ScenarioUsers, ScenarioThreadDistribution.scenario_user_id == ScenarioUsers.id)
                    .join(ScenarioThreads, ScenarioThreadDistribution.scenario_thread_id == ScenarioThreads.id)
                    .filter(ScenarioUsers.user_id == user_id, ScenarioUsers.scenario_id == scenario_id)
                    .all()
                )
                if dist.scenario_thread and dist.scenario_thread.thread
            ]
        else:
            user_thread_ids = thread_ids

        if not user_thread_ids:
            user_thread_ids = thread_ids  # Fallback

        # Get user's votes
        user_votes = [v for v in all_votes if v.user_id == user_id and v.thread_id in user_thread_ids]
        votes_by_thread = {v.thread_id: v for v in user_votes}
        user_vote_map[user_id] = votes_by_thread

        # Calculate progress
        voted_count = len([v for v in user_votes if v.vote is not None])
        total_assigned = len(user_thread_ids)

        # Calculate accuracy against ground truth with fake/real breakdown
        correct = 0
        incorrect = 0
        fake_correct = 0  # User said "fake" and it was fake
        fake_incorrect = 0  # User said "fake" but it was real
        real_correct = 0  # User said "real" and it was real
        real_incorrect = 0  # User said "real" but it was fake
        for tid in user_thread_ids:
            vote = votes_by_thread.get(tid)
            if vote and vote.vote and tid in ground_truth:
                vote_is_fake = vote.vote.lower() == "fake"
                thread_is_fake = ground_truth[tid]
                if vote_is_fake == thread_is_fake:
                    correct += 1
                    if vote_is_fake:
                        fake_correct += 1
                    else:
                        real_correct += 1
                else:
                    incorrect += 1
                    if vote_is_fake:
                        fake_incorrect += 1
                    else:
                        real_incorrect += 1

        accuracy = round(correct / (correct + incorrect) * 100, 1) if (correct + incorrect) > 0 else None

        # Calculate F1 Score (fake is positive class)
        # TP = fake_correct, FP = fake_incorrect, FN = real_incorrect
        precision = fake_correct / (fake_correct + fake_incorrect) if (fake_correct + fake_incorrect) > 0 else 0
        recall = fake_correct / (fake_correct + real_incorrect) if (fake_correct + real_incorrect) > 0 else 0
        f1_score = round(2 * precision * recall / (precision + recall) * 100, 1) if (precision + recall) > 0 else None

        # Detailed vote lists
        voted_threads = []
        pending_threads = []
        for tid in user_thread_ids:
            thread_info = {"thread_id": tid}
            subject = thread_subjects.get(tid)
            if subject:
                thread_info["subject"] = subject

            vote = votes_by_thread.get(tid)
            if vote and vote.vote:
                thread_info["vote"] = vote.vote
                thread_info["confidence"] = vote.confidence
                thread_info["is_correct"] = (vote.vote.lower() == "fake") == ground_truth.get(tid, False)
                voted_threads.append(thread_info)
            else:
                pending_threads.append(thread_info)

        avatar_data = serialize_user_brief(user)
        user_stats.append(
            {
                "user_id": user_id,
                "username": avatar_data.get("username") or user.username,
                "avatar_seed": avatar_data.get("avatar_seed"),
                "avatar_url": avatar_data.get("avatar_url"),
                "role": su.role.value if su.role else "unknown",
                "is_llm": False,  # Explicit flag for human evaluators
                "total_threads": total_assigned,
                "voted_count": voted_count,
                "pending_count": total_assigned - voted_count,
                "progress_percent": round(voted_count / total_assigned * 100, 1) if total_assigned > 0 else 0,
                "accuracy_percent": accuracy,
                "f1_score_percent": f1_score,
                "correct_count": correct,
                "incorrect_count": incorrect,
                "fake_correct": fake_correct,
                "fake_incorrect": fake_incorrect,
                "real_correct": real_correct,
                "real_incorrect": real_incorrect,
                "voted_threads": voted_threads,
                "pending_threads": pending_threads,
            }
        )

    # Get LLM evaluator stats first (so we can include in alpha calculation)
    config = scenario.config_json
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}
    config_models = config.get("llm_evaluators")
    if not config_models:
        config_models = config.get("selected_llms") or []
    normalized_models = []
    for model in config_models:
        if isinstance(model, str):
            mid = model.strip()
        elif isinstance(model, dict):
            mid = str(model.get("model_id") or "").strip()
        else:
            continue
        if mid and mid not in normalized_models:
            normalized_models.append(mid)

    llm_user_stats = _build_llm_authenticity_stats(
        scenario_id=scenario_id,
        thread_ids=thread_ids,
        ground_truth=ground_truth,
        model_ids=normalized_models,
    )

    # Build vote map for LLM evaluators too
    llm_vote_map = {}  # model_id -> {thread_id -> vote_string}
    for llm_stat in llm_user_stats:
        model_id = llm_stat.get("model_id")
        if model_id:
            votes = {}
            for vt in llm_stat.get("voted_threads", []):
                if vt.get("vote"):
                    votes[vt["thread_id"]] = vt["vote"]
            llm_vote_map[model_id] = votes

    # Calculate Krippendorff's Alpha (including both human and LLM evaluators)
    # Collect all raters: human users + LLM evaluators
    all_raters = []
    rater_vote_sources = []  # List of (rater_id, is_llm, vote_data)

    # Add human raters
    for u in user_stats:
        if u["voted_count"] > 0:
            all_raters.append(u["user_id"])
            rater_vote_sources.append((u["user_id"], False, user_vote_map.get(u["user_id"], {})))

    # Add LLM raters
    for llm_stat in llm_user_stats:
        if llm_stat.get("voted_count", 0) > 0:
            model_id = llm_stat.get("model_id")
            all_raters.append(f"llm:{model_id}")
            rater_vote_sources.append((model_id, True, llm_vote_map.get(model_id, {})))

    if len(all_raters) >= 2 and len(thread_ids) >= 2:
        ratings_matrix = np.full((len(all_raters), len(thread_ids)), np.nan)

        for i, (rater_id, is_llm, vote_data) in enumerate(rater_vote_sources):
            for j, tid in enumerate(thread_ids):
                if is_llm:
                    # LLM vote data is {thread_id: vote_string}
                    vote_str = vote_data.get(tid)
                    if vote_str:
                        ratings_matrix[i, j] = 1.0 if vote_str.lower() == "fake" else 0.0
                else:
                    # Human vote data is {thread_id: vote_object}
                    vote = vote_data.get(tid)
                    if vote and vote.vote:
                        ratings_matrix[i, j] = 1.0 if vote.vote.lower() == "fake" else 0.0

        alpha = _calculate_krippendorff_alpha(ratings_matrix)
    else:
        alpha = None

    # Add LLM stats to user_stats
    if llm_user_stats:
        user_stats.extend(llm_user_stats)

    # Overall vote distribution (human votes only for backwards compatibility)
    total_real_votes = sum(1 for v in all_votes if v.vote and v.vote.lower() == "real")
    total_fake_votes = sum(1 for v in all_votes if v.vote and v.vote.lower() == "fake")

    # Add LLM votes to distribution
    for llm_stat in llm_user_stats:
        for vt in llm_stat.get("voted_threads", []):
            if vt.get("vote"):
                if vt["vote"].lower() == "real":
                    total_real_votes += 1
                elif vt["vote"].lower() == "fake":
                    total_fake_votes += 1

    total_possible_votes = sum(u["total_threads"] for u in user_stats)
    total_pending = total_possible_votes - (total_real_votes + total_fake_votes)

    # Overall accuracy (including LLM evaluators)
    all_correct = sum(u.get("correct_count", 0) for u in user_stats)
    all_incorrect = sum(u.get("incorrect_count", 0) for u in user_stats)
    overall_accuracy = (
        round(all_correct / (all_correct + all_incorrect) * 100, 1)
        if (all_correct + all_incorrect) > 0
        else None
    )

    # Calculate pairwise agreement between evaluators
    pairwise_agreement = _calculate_authenticity_pairwise_agreement(
        user_stats=user_stats,
        llm_user_stats=llm_user_stats,
        user_vote_map=user_vote_map,
        llm_vote_map=llm_vote_map,
        thread_ids=thread_ids,
    )

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.scenario_name,
        "total_threads": len(thread_ids),
        "total_users": len(scenario_users),
        "user_stats": user_stats,
        "krippendorff_alpha": alpha,
        "alpha_interpretation": _interpret_alpha(alpha),
        "vote_distribution": {
            "real": total_real_votes,
            "fake": total_fake_votes,
            "pending": max(0, total_pending),
        },
        "overall_accuracy": overall_accuracy,
        "ground_truth_stats": {
            "fake_count": fake_count,
            "real_count": real_count,
        },
        "pairwise_agreement": pairwise_agreement,
    }


def get_scenario_stats_payload(scenario_id: int) -> Dict[str, Any]:
    scenario = _get_scenario_or_raise(scenario_id)
    function_type = _get_function_type_or_raise(scenario.function_type_id)
    if function_type.name == "authenticity":
        stats = get_authenticity_stats(scenario_id)
        kind = "authenticity"
    else:
        stats = get_progress_stats(scenario_id)
        kind = "progress"
    return {
        "scenario_id": scenario_id,
        "function_type": function_type.name,
        "kind": kind,
        "stats": stats,
    }


def _build_llm_authenticity_stats(
    *,
    scenario_id: int,
    thread_ids: List[int],
    ground_truth: Dict[int, bool],
    model_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    if not thread_ids:
        return []

    results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id,
        task_type="authenticity",
    ).all()
    model_ids = model_ids or []

    by_model: Dict[str, Dict[int, LLMTaskResult]] = {}
    for result in results:
        if result.thread_id not in thread_ids:
            continue
        by_model.setdefault(result.model_id, {})[result.thread_id] = result

    cleaned_model_ids = []
    for model_id in model_ids:
        if isinstance(model_id, str):
            mid = model_id.strip()
            if mid and mid not in cleaned_model_ids:
                cleaned_model_ids.append(mid)

    if not by_model and not cleaned_model_ids:
        return []

    all_model_ids = sorted(set(list(by_model.keys()) + cleaned_model_ids))
    model_meta = {
        model.model_id: model
        for model in LLMModel.query.filter(LLMModel.model_id.in_(all_model_ids)).all()
    }

    thread_subjects = {
        thread.thread_id: thread.subject
        for thread in EmailThread.query.filter(EmailThread.thread_id.in_(thread_ids)).all()
    }

    user_stats = []
    for model_id in all_model_ids:
        model_results = by_model.get(model_id, {})
        display_name = model_meta.get(model_id).display_name if model_meta.get(model_id) else model_id
        voted_threads = []
        pending_threads = []
        voted_count = 0
        correct = 0
        incorrect = 0
        fake_correct = 0
        fake_incorrect = 0
        real_correct = 0
        real_incorrect = 0

        for tid in thread_ids:
            result = model_results.get(tid)
            payload = result.payload_json if result and result.payload_json and not result.error else None
            if payload:
                vote = str(payload.get("vote") or "").lower()
            else:
                vote = None

            thread_info = {"thread_id": tid}
            subject = thread_subjects.get(tid)
            if subject:
                thread_info["subject"] = subject

            if vote in {"real", "fake"}:
                voted_count += 1
                thread_info["vote"] = vote
                confidence_raw = payload.get("confidence") if payload else None
                try:
                    confidence = int(confidence_raw) if confidence_raw is not None else None
                except Exception:
                    confidence = None
                if confidence is not None:
                    confidence = max(1, min(5, confidence))
                    thread_info["confidence"] = confidence * 20

                is_fake = ground_truth.get(tid)
                if is_fake is not None:
                    vote_is_fake = vote == "fake"
                    is_correct = vote_is_fake == is_fake
                    thread_info["is_correct"] = is_correct
                    if is_correct:
                        correct += 1
                        if vote_is_fake:
                            fake_correct += 1
                        else:
                            real_correct += 1
                    else:
                        incorrect += 1
                        if vote_is_fake:
                            fake_incorrect += 1
                        else:
                            real_incorrect += 1

                voted_threads.append(thread_info)
            else:
                pending_threads.append(thread_info)

        total_assigned = len(thread_ids)
        accuracy = round(correct / (correct + incorrect) * 100, 1) if (correct + incorrect) > 0 else None

        # Calculate F1 Score (fake is positive class)
        precision = fake_correct / (fake_correct + fake_incorrect) if (fake_correct + fake_incorrect) > 0 else 0
        recall = fake_correct / (fake_correct + real_incorrect) if (fake_correct + real_incorrect) > 0 else 0
        f1_score = round(2 * precision * recall / (precision + recall) * 100, 1) if (precision + recall) > 0 else None

        user_stats.append({
            "user_id": f"llm:{model_id}",
            "username": display_name,
            "role": "evaluator",
            "is_llm": True,
            "avatar_seed": None,
            "avatar_url": None,
            "model_id": model_id,
            "total_threads": total_assigned,
            "voted_count": voted_count,
            "pending_count": total_assigned - voted_count,
            "progress_percent": round(voted_count / total_assigned * 100, 1) if total_assigned > 0 else 0,
            "accuracy_percent": accuracy,
            "f1_score_percent": f1_score,
            "correct_count": correct,
            "incorrect_count": incorrect,
            "fake_correct": fake_correct,
            "fake_incorrect": fake_incorrect,
            "real_correct": real_correct,
            "real_incorrect": real_incorrect,
            "voted_threads": voted_threads,
            "pending_threads": pending_threads,
        })

    user_stats.sort(key=lambda entry: entry["username"].lower())
    return user_stats
