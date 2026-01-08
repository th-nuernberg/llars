"""
Scenario statistics service.

Provides scenario progress stats and authenticity (fake/echt) stats for reuse
across HTTP routes and Socket.IO updates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from db.database import db
from db.models import (
    RatingScenarios,
    FeatureFunctionType,
    ScenarioUsers,
    ScenarioThreads,
    ScenarioThreadDistribution,
    ScenarioRoles,
    User,
    ComparisonSession,
    EmailThread,
    AuthenticityConversation,
    UserAuthenticityVote,
    ProgressionStatus,
    LLMTaskResult,
    LLMModel,
)
from decorators.error_handler import NotFoundError, ValidationError
from routes.HelperFunctions import (
    get_thread_progression_state,
    raters_receive_all_threads,
    get_scenario_distribution_mode,
    DISTRIBUTION_MODE_ALL,
)


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


def get_progress_stats(scenario_id: int) -> Dict[str, Any]:
    """Get detailed progress statistics for all users in a scenario."""
    scenario = _get_scenario_or_raise(scenario_id)
    function_type = _get_function_type_or_raise(scenario.function_type_id)
    if function_type.name == "comparison":
        return _get_comparison_progress_stats(scenario_id)

    rater_stats = []
    evaluator_stats = []

    scenario_users = (
        db.session.query(ScenarioUsers)
        .join(User, ScenarioUsers.user_id == User.id)
        .filter(ScenarioUsers.scenario_id == scenario_id)
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
            scenario_user.role == ScenarioRoles.EVALUATOR
            or (scenario_user.role == ScenarioRoles.RATER and raters_receive_all_threads(scenario))
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

        new_data = {
            "username": scenario_user.user.username,
            "total_threads": len(user_threads),
            "done_threads": total_done_threads,
            "not_started_threads": total_not_started_threads,
            "progressing_threads": total_progressing_threads,
            "done_threads_list": done_threads_list,
            "not_started_threads_list": not_started_threads_list,
            "progressing_threads_list": progressing_threads_list,
        }

        if scenario_user.role == ScenarioRoles.RATER:
            rater_stats.append(new_data)
        elif scenario_user.role == ScenarioRoles.EVALUATOR:
            evaluator_stats.append(new_data)

    if function_type.name in {"ranking", "rating", "authenticity"}:
        scenario_thread_ids = [
            row.thread_id
            for row in ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
            if row.thread_id
        ]
        config = scenario.config_json if isinstance(scenario.config_json, dict) else {}
        config_models = config.get("llm_evaluators") or []
        llm_stats = _build_llm_progress_entries(
            scenario_id=scenario_id,
            thread_ids=scenario_thread_ids,
            task_type=function_type.name,
            model_ids=config_models,
        )
        evaluator_stats.extend(llm_stats)

    return {
        "rater_stats": rater_stats,
        "evaluator_stats": evaluator_stats,
        "viewer_stats": evaluator_stats,  # backward compatibility
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

    scenario_users = (
        db.session.query(ScenarioUsers)
        .join(User, ScenarioUsers.user_id == User.id)
        .filter(ScenarioUsers.scenario_id == scenario_id)
        .all()
    )

    sessions = ComparisonSession.query.filter_by(scenario_id=scenario_id).all()
    sessions_by_user = {}
    for session in sessions:
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
            bot_pairs = [msg for msg in session.messages if msg.type == "bot_pair"]
            total_pairs_session = len(bot_pairs)
            rated_pairs_session = sum(1 for msg in bot_pairs if msg.selected is not None)

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
            "total_threads": total_pairs,
            "done_threads": total_rated_pairs,
            "not_started_threads": max(total_pairs - total_rated_pairs, 0),
            "progressing_threads": total_progressing_threads,
            "done_threads_list": done_threads_list,
            "not_started_threads_list": not_started_threads_list,
            "progressing_threads_list": progressing_threads_list,
        }

        if scenario_user.role == ScenarioRoles.RATER:
            rater_stats.append(new_data)
        elif scenario_user.role == ScenarioRoles.EVALUATOR:
            evaluator_stats.append(new_data)

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


def get_authenticity_stats(scenario_id: int) -> Dict[str, Any]:
    """Get comprehensive statistics for an authenticity scenario."""
    scenario = _get_scenario_or_raise(scenario_id)

    scenario_users = (
        db.session.query(ScenarioUsers)
        .join(User, ScenarioUsers.user_id == User.id)
        .filter(ScenarioUsers.scenario_id == scenario_id)
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
        if su.role == ScenarioRoles.RATER and distribution_mode != DISTRIBUTION_MODE_ALL:
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

        user_stats.append(
            {
                "user_id": user_id,
                "username": user.username,
                "role": su.role.value if su.role else "unknown",
                "total_threads": total_assigned,
                "voted_count": voted_count,
                "pending_count": total_assigned - voted_count,
                "progress_percent": round(voted_count / total_assigned * 100, 1) if total_assigned > 0 else 0,
                "accuracy_percent": accuracy,
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

    # Calculate Krippendorff's Alpha
    rater_ids = [u["user_id"] for u in user_stats if u["voted_count"] > 0]

    if len(rater_ids) >= 2 and len(thread_ids) >= 2:
        ratings_matrix = np.full((len(rater_ids), len(thread_ids)), np.nan)

        for i, uid in enumerate(rater_ids):
            votes_dict = user_vote_map.get(uid, {})
            for j, tid in enumerate(thread_ids):
                vote = votes_dict.get(tid)
                if vote and vote.vote:
                    # 0 = real, 1 = fake
                    ratings_matrix[i, j] = 1.0 if vote.vote.lower() == "fake" else 0.0

        alpha = _calculate_krippendorff_alpha(ratings_matrix)
    else:
        alpha = None

    # Overall vote distribution
    total_real_votes = sum(1 for v in all_votes if v.vote and v.vote.lower() == "real")
    total_fake_votes = sum(1 for v in all_votes if v.vote and v.vote.lower() == "fake")
    total_possible_votes = sum(u["total_threads"] for u in user_stats if u["role"] == "rater")
    total_pending = total_possible_votes - (total_real_votes + total_fake_votes)

    # Overall accuracy
    all_correct = sum(u["correct_count"] for u in user_stats)
    all_incorrect = sum(u["incorrect_count"] for u in user_stats)
    overall_accuracy = (
        round(all_correct / (all_correct + all_incorrect) * 100, 1)
        if (all_correct + all_incorrect) > 0
        else None
    )

    config = scenario.config_json if isinstance(scenario.config_json, dict) else {}
    llm_user_stats = _build_llm_authenticity_stats(
        scenario_id=scenario_id,
        thread_ids=thread_ids,
        ground_truth=ground_truth,
        model_ids=config.get("llm_evaluators") or [],
    )
    if llm_user_stats:
        user_stats.extend(llm_user_stats)

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

        user_stats.append({
            "user_id": f"llm:{model_id}",
            "username": display_name,
            "role": "evaluator",
            "is_llm": True,
            "model_id": model_id,
            "total_threads": total_assigned,
            "voted_count": voted_count,
            "pending_count": total_assigned - voted_count,
            "progress_percent": round(voted_count / total_assigned * 100, 1) if total_assigned > 0 else 0,
            "accuracy_percent": accuracy,
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
