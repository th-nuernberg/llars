"""
Scenario statistics service.

Provides scenario progress stats and authenticity (fake/echt) stats for reuse
across HTTP routes and Socket.IO updates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from collections import defaultdict
import json
import time
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
    ItemComparisonEvaluation,
    ItemLabelingEvaluation,
    UserMailHistoryRating,
    Feature,
    UserFeatureRanking,
    UserFeatureRating,
    ScenarioItems,
)
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from decorators.error_handler import NotFoundError, ValidationError
from routes.HelperFunctions import (
    get_thread_progression_state,
    raters_receive_all_threads,
    get_scenario_distribution_mode,
    DISTRIBUTION_MODE_ALL,
)
from services.user_profile_service import serialize_user_brief
from services.evaluation.dimensional_rating_service import DimensionalRatingService
from services.llm_registry_service import resolve_model_registry


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


# Simple TTL cache for expensive stats computations.
# Key: scenario_id, Value: (timestamp, result_dict)
_stats_cache: Dict[int, tuple] = {}
_STATS_CACHE_TTL = 120  # seconds


def _get_cached_stats(scenario_id: int) -> Optional[Dict]:
    """Return cached stats if still valid, else None."""
    entry = _stats_cache.get(scenario_id)
    if entry and (time.time() - entry[0]) < _STATS_CACHE_TTL:
        return entry[1]
    return None


def _set_cached_stats(scenario_id: int, data: Dict) -> None:
    """Cache stats result. Evict old entries if cache grows too large."""
    if len(_stats_cache) > 100:
        cutoff = time.time() - _STATS_CACHE_TTL
        to_remove = [k for k, (ts, _) in _stats_cache.items() if ts < cutoff]
        for k in to_remove:
            del _stats_cache[k]
    _stats_cache[scenario_id] = (time.time(), data)


def invalidate_stats_cache(scenario_id: int) -> None:
    """Invalidate cached stats for a scenario (call after rating/ranking changes)."""
    _stats_cache.pop(scenario_id, None)


_DEFAULT_BUCKET_COLOR_PALETTE = [
    "#b0ca97",
    "#d8bf8f",
    "#88c4c8",
    "#e8a087",
    "#c07a7a",
]


def _normalize_bucket_lookup_key(value: Any) -> str:
    """Normalize bucket identifiers/labels for robust lookups."""
    if value is None:
        return ""

    text = str(value).strip().lower()
    if not text:
        return ""

    text = " ".join(text.split())
    text = text.replace("-", "_").replace(" ", "_")
    return text


def _humanize_bucket_identifier(value: str) -> str:
    normalized = _normalize_bucket_lookup_key(value)
    if not normalized:
        return "Bucket"
    words = [part for part in normalized.split("_") if part]
    if not words:
        return "Bucket"
    return " ".join(word[:1].upper() + word[1:] for word in words)


def _normalize_provenance_text(value: Any) -> str:
    """Normalize generated text/content for resilient provenance matching."""
    if value is None:
        return ""
    return " ".join(str(value).split())


def _normalize_model_identity(value: Any) -> str:
    """Normalize model labels to alphanumeric lowercase for fuzzy matching."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    return "".join(ch for ch in text if ch.isalnum())


def _extract_ranking_bucket_config(config: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract ranking bucket definitions from all supported config paths.

    Supported locations:
    - config.buckets
    - config.eval_config.buckets
    - config.eval_config.config.buckets
    - config.config.buckets
    """
    candidate_lists: List[Any] = []
    candidate_lists.append(config.get("buckets"))

    eval_config = config.get("eval_config") if isinstance(config.get("eval_config"), dict) else {}
    if eval_config:
        candidate_lists.append(eval_config.get("buckets"))
        nested_eval_config = eval_config.get("config") if isinstance(eval_config.get("config"), dict) else {}
        if nested_eval_config:
            candidate_lists.append(nested_eval_config.get("buckets"))

    nested_config = config.get("config") if isinstance(config.get("config"), dict) else {}
    if nested_config:
        candidate_lists.append(nested_config.get("buckets"))

    configured_buckets: List[Any] = []
    for candidate in candidate_lists:
        if isinstance(candidate, list) and len(candidate) > 0:
            configured_buckets = candidate
            break

    # Fallback for legacy scenarios without explicit bucket config.
    if not configured_buckets:
        configured_buckets = [
            {"id": "gut", "name": {"de": "Gut", "en": "Good"}, "color": "#b0ca97"},
            {"id": "mittel", "name": {"de": "Mittel", "en": "Medium"}, "color": "#e8c87a"},
            {"id": "schlecht", "name": {"de": "Schlecht", "en": "Bad"}, "color": "#e8a087"},
        ]

    bucket_order: List[Dict[str, str]] = []
    seen_ids = set()

    for idx, bucket in enumerate(configured_buckets):
        fallback_color = _DEFAULT_BUCKET_COLOR_PALETTE[idx % len(_DEFAULT_BUCKET_COLOR_PALETTE)]

        if isinstance(bucket, str):
            raw_label = bucket.strip()
            if not raw_label:
                continue
            bucket_id = _normalize_bucket_lookup_key(raw_label) or f"bucket_{idx + 1}"
            label_de = raw_label
            label_en = raw_label
            color = fallback_color
        elif isinstance(bucket, dict):
            raw_id = bucket.get("id") or bucket.get("value")
            name_value = bucket.get("name")
            label_value = bucket.get("label")
            label_de_value = bucket.get("label_de")
            label_en_value = bucket.get("label_en")

            if isinstance(name_value, dict):
                label_de = str(
                    name_value.get("de")
                    or name_value.get("en")
                    or label_de_value
                    or label_value
                    or raw_id
                    or f"Bucket {idx + 1}"
                ).strip()
                label_en = str(
                    name_value.get("en")
                    or name_value.get("de")
                    or label_en_value
                    or label_value
                    or raw_id
                    or f"Bucket {idx + 1}"
                ).strip()
            elif isinstance(name_value, str):
                fallback_name = name_value.strip()
                label_de = str(label_de_value or fallback_name or label_value or raw_id or f"Bucket {idx + 1}").strip()
                label_en = str(label_en_value or fallback_name or label_value or raw_id or f"Bucket {idx + 1}").strip()
            else:
                label_de = str(label_de_value or label_value or raw_id or f"Bucket {idx + 1}").strip()
                label_en = str(label_en_value or label_de or raw_id or f"Bucket {idx + 1}").strip()

            if not label_de:
                label_de = label_en or f"Bucket {idx + 1}"
            if not label_en:
                label_en = label_de

            bucket_id = str(raw_id or label_en or label_de).strip().lower()
            if not bucket_id:
                bucket_id = _normalize_bucket_lookup_key(label_en or label_de or f"bucket_{idx + 1}")

            color = str(bucket.get("color") or fallback_color).strip() or fallback_color
        else:
            continue

        bucket_id = str(bucket_id).strip().lower()
        if not bucket_id or bucket_id in seen_ids:
            continue
        seen_ids.add(bucket_id)

        bucket_order.append(
            {
                "id": bucket_id,
                "label": label_de or label_en or _humanize_bucket_identifier(bucket_id),
                "label_de": label_de or label_en or _humanize_bucket_identifier(bucket_id),
                "label_en": label_en or label_de or _humanize_bucket_identifier(bucket_id),
                "color": color,
            }
        )

    return bucket_order


def _build_bucket_id_resolver(bucket_order: List[Dict[str, str]]):
    """Create a resolver for bucket ids from ids/labels with legacy alias support."""
    lookup: Dict[str, str] = {}
    for entry in bucket_order:
        bucket_id = entry.get("id")
        if not bucket_id:
            continue
        for candidate in [bucket_id, entry.get("label"), entry.get("label_de"), entry.get("label_en")]:
            key = _normalize_bucket_lookup_key(candidate)
            if key and key not in lookup:
                lookup[key] = bucket_id

    legacy_aliases = {
        "good": "gut",
        "very_good": "sehr_gut",
        "excellent": "sehr_gut",
        "medium": "mittel",
        "middle": "mittel",
        "bad": "schlecht",
        "poor": "schlecht",
        "very_poor": "sehr_schlecht",
    }

    def _resolve_bucket_id(raw_name: Any) -> Optional[str]:
        key = _normalize_bucket_lookup_key(raw_name)
        if not key:
            return None
        if key in lookup:
            return lookup[key]

        alias = legacy_aliases.get(key)
        if not alias:
            return None

        alias_key = _normalize_bucket_lookup_key(alias)
        return lookup.get(alias_key)

    return _resolve_bucket_id


def _extract_rating_scale_bounds(config: Dict[str, Any]) -> Dict[str, float]:
    """Extract rating scale min/max from all supported config paths."""
    if not isinstance(config, dict):
        config = {}

    eval_config = config.get("eval_config")
    if not isinstance(eval_config, dict):
        eval_config = {}

    eval_config_inner = eval_config.get("config")
    if not isinstance(eval_config_inner, dict):
        eval_config_inner = {}

    raw_min = config.get("min", eval_config.get("min", eval_config_inner.get("min", 1)))
    raw_max = config.get("max", eval_config.get("max", eval_config_inner.get("max", 5)))

    try:
        scale_min = float(raw_min)
    except (TypeError, ValueError):
        scale_min = 1.0

    try:
        scale_max = float(raw_max)
    except (TypeError, ValueError):
        scale_max = 5.0

    if scale_max <= scale_min:
        scale_min, scale_max = 1.0, 5.0

    return {"min": scale_min, "max": scale_max}


def _extract_overall_rating_from_payload(payload: Any) -> Optional[float]:
    """Extract overall rating from supported rating payload formats."""
    if not payload:
        return None
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            return None
    if not isinstance(payload, dict):
        return None

    overall_rating = None
    if payload.get("type") == "dimensional":
        overall_rating = payload.get("overall_rating")
    elif "overall_rating" in payload:
        overall_rating = payload.get("overall_rating")
    elif "rating" in payload:
        overall_rating = payload.get("rating")

    if overall_rating is None:
        return None

    try:
        return float(overall_rating)
    except (TypeError, ValueError):
        return None


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
    elif function_type_name == "comparison":
        return _calculate_comparison_pairwise_agreement(scenario_id)
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
    from db.models import LLMTaskResult, Feature

    # Get evaluators who have completed at least one thread
    active_evaluators = [e for e in evaluator_stats if e.get("done_threads", 0) > 0]
    if len(active_evaluators) < 2:
        return None

    # Get all thread IDs from the scenario
    scenario_threads = ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    thread_ids = [st.thread_id for st in scenario_threads if st.thread_id]
    if len(thread_ids) < 2:
        return None

    # Collect human evaluator user_ids
    human_user_ids = []
    for e in active_evaluators:
        if e.get("is_llm"):
            continue
        user = User.query.filter_by(username=e.get("username")).first()
        if user:
            human_user_ids.append(user.id)

    # Collect LLM evaluator model_ids for ranking scenarios
    llm_model_ids = []
    if function_type_name == "ranking":
        for e in active_evaluators:
            if e.get("is_llm") and e.get("model_id"):
                llm_model_ids.append(e["model_id"])

    total_evaluators = len(human_user_ids) + len(llm_model_ids)
    if total_evaluators < 2:
        return None

    ratings_matrix = np.full((total_evaluators, len(thread_ids)), np.nan)

    if function_type_name == "ranking":
        # Build bucket ordinal map from scenario config for consistent numeric mapping.
        # _extract_ranking_bucket_config returns [{id, label_de, ...}, ...] ordered by rank.
        scenario = RatingScenarios.query.get(scenario_id)
        bucket_config = _extract_ranking_bucket_config(
            scenario.config_json if scenario else {}
        )
        # Ordinal map: bucket_id → numeric value (0, 1, 2, ...)
        bucket_ordinal = {}
        for idx, b in enumerate(bucket_config):
            bucket_ordinal[b["id"]] = idx
        resolve_bucket = _build_bucket_id_resolver(bucket_config)

        # Human rankings from UserFeatureRanking
        # Build feature_id → thread_id map for all features in this scenario
        feature_thread_map = {}
        features = (
            Feature.query
            .filter(Feature.item_id.in_(thread_ids))
            .with_entities(Feature.feature_id, Feature.item_id)
            .all()
        )
        for f_id, t_id in features:
            feature_thread_map[f_id] = t_id

        thread_id_to_idx = {tid: j for j, tid in enumerate(thread_ids)}

        for i, user_id in enumerate(human_user_ids):
            rankings = (
                UserFeatureRanking.query
                .filter(
                    UserFeatureRanking.user_id == user_id,
                    UserFeatureRanking.feature_id.in_(list(feature_thread_map.keys())),
                    UserFeatureRanking.bucket.isnot(None),
                )
                .all()
            )
            for ranking in rankings:
                tid = feature_thread_map.get(ranking.feature_id)
                if tid is None:
                    continue
                j = thread_id_to_idx.get(tid)
                if j is None:
                    continue
                resolved = resolve_bucket(ranking.bucket)
                if resolved and resolved in bucket_ordinal:
                    ratings_matrix[i, j] = bucket_ordinal[resolved]

        # LLM rankings from LLMTaskResult (payload_json = {bucket: [feature_ids]})
        for li, model_id in enumerate(llm_model_ids):
            row_idx = len(human_user_ids) + li
            results = (
                LLMTaskResult.query
                .filter_by(scenario_id=scenario_id, model_id=model_id, task_type="ranking")
                .filter(LLMTaskResult.error.is_(None))
                .all()
            )
            for result in results:
                payload = result.payload_json
                if not payload:
                    continue
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except (json.JSONDecodeError, TypeError):
                        continue
                if not isinstance(payload, dict):
                    continue
                for bucket_name, feature_ids in payload.items():
                    resolved = resolve_bucket(bucket_name)
                    if not resolved or resolved not in bucket_ordinal or not isinstance(feature_ids, list):
                        continue
                    for fid in feature_ids:
                        try:
                            fid_int = int(fid)
                        except (TypeError, ValueError):
                            continue
                        tid = feature_thread_map.get(fid_int)
                        if tid is None:
                            continue
                        j = thread_id_to_idx.get(tid)
                        if j is not None:
                            ratings_matrix[row_idx, j] = bucket_ordinal[resolved]

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


def _batch_get_progression_states(
    thread_ids: List[int],
    user_ids: List[int],
    function_type_id: int,
    scenario_id: int,
) -> Dict[tuple, ProgressionStatus]:
    """Batch-load progression states for all (thread_id, user_id) combinations.

    Returns dict of {(thread_id, user_id): ProgressionStatus}.
    Replaces N+1 per-item calls to get_thread_progression_state().
    """
    if not thread_ids or not user_ids:
        return {}

    result = {}

    if function_type_id == 1:
        # RANKING: count features per item, count ranked features per (item, user)
        feature_counts = dict(
            db.session.query(Feature.item_id, func.count(Feature.feature_id))
            .filter(Feature.item_id.in_(thread_ids))
            .group_by(Feature.item_id)
            .all()
        )
        for uid in user_ids:
            ranked_counts = dict(
                db.session.query(Feature.item_id, func.count(UserFeatureRanking.ranking_id))
                .join(Feature, UserFeatureRanking.feature_id == Feature.feature_id)
                .filter(
                    UserFeatureRanking.user_id == uid,
                    Feature.item_id.in_(thread_ids),
                )
                .group_by(Feature.item_id)
                .all()
            )
            for tid in thread_ids:
                total = feature_counts.get(tid, 0)
                ranked = ranked_counts.get(tid, 0)
                if ranked == 0:
                    result[(tid, uid)] = ProgressionStatus.NOT_STARTED
                elif ranked < total:
                    result[(tid, uid)] = ProgressionStatus.PROGRESSING
                else:
                    result[(tid, uid)] = ProgressionStatus.DONE

    elif function_type_id in (2, 7):
        # RATING / LABELING: check ItemDimensionRating first, fallback to feature ratings
        dim_ratings = {}
        for row in (
            db.session.query(
                ItemDimensionRating.item_id,
                ItemDimensionRating.user_id,
                ItemDimensionRating.status,
            )
            .filter(
                ItemDimensionRating.scenario_id == scenario_id,
                ItemDimensionRating.user_id.in_(user_ids),
                ItemDimensionRating.item_id.in_(thread_ids),
            )
            .all()
        ):
            dim_ratings[(row.item_id, row.user_id)] = row.status

        # Find items without dim_rating per user (for rating fallback)
        missing_items_by_user = defaultdict(list)
        for uid in user_ids:
            for tid in thread_ids:
                key = (tid, uid)
                if key in dim_ratings:
                    status = dim_ratings[key]
                    result[key] = status if status else ProgressionStatus.NOT_STARTED
                else:
                    missing_items_by_user[uid].append(tid)

        # Fallback for rating: feature-based rating check
        if function_type_id == 2 and missing_items_by_user:
            all_missing = list({tid for tids in missing_items_by_user.values() for tid in tids})
            feature_counts = dict(
                db.session.query(Feature.item_id, func.count(Feature.feature_id))
                .filter(Feature.item_id.in_(all_missing))
                .group_by(Feature.item_id)
                .all()
            ) if all_missing else {}

            for uid, tids in missing_items_by_user.items():
                if not tids:
                    continue
                rated_counts = dict(
                    db.session.query(Feature.item_id, func.count(UserFeatureRating.rating_id))
                    .join(Feature, UserFeatureRating.feature_id == Feature.feature_id)
                    .filter(
                        UserFeatureRating.user_id == uid,
                        Feature.item_id.in_(tids),
                    )
                    .group_by(Feature.item_id)
                    .all()
                )
                for tid in tids:
                    total = feature_counts.get(tid, 0)
                    rated = rated_counts.get(tid, 0)
                    if rated == 0:
                        result[(tid, uid)] = ProgressionStatus.NOT_STARTED
                    elif rated < total:
                        result[(tid, uid)] = ProgressionStatus.PROGRESSING
                    else:
                        result[(tid, uid)] = ProgressionStatus.DONE
        elif function_type_id == 7:
            # Labeling: no fallback, items without dim_rating are NOT_STARTED
            for uid, tids in missing_items_by_user.items():
                for tid in tids:
                    result[(tid, uid)] = ProgressionStatus.NOT_STARTED

    elif function_type_id == 3:
        # MAIL_RATING: check UserMailHistoryRating
        for uid in user_ids:
            mail_ratings = (
                db.session.query(
                    UserMailHistoryRating.thread_id,
                    UserMailHistoryRating.status,
                )
                .filter(
                    UserMailHistoryRating.user_id == uid,
                    UserMailHistoryRating.thread_id.in_(thread_ids),
                )
                .order_by(UserMailHistoryRating.timestamp.desc())
                .all()
            )
            seen = set()
            for row in mail_ratings:
                if row.thread_id not in seen:
                    seen.add(row.thread_id)
                    result[(row.thread_id, uid)] = row.status if row.status else ProgressionStatus.NOT_STARTED
            for tid in thread_ids:
                if (tid, uid) not in result:
                    result[(tid, uid)] = ProgressionStatus.NOT_STARTED

    elif function_type_id == 5:
        # AUTHENTICITY: existence of vote = DONE
        votes = set(
            db.session.query(
                UserAuthenticityVote.thread_id,
                UserAuthenticityVote.user_id,
            )
            .filter(
                UserAuthenticityVote.user_id.in_(user_ids),
                UserAuthenticityVote.thread_id.in_(thread_ids),
            )
            .all()
        )
        for uid in user_ids:
            for tid in thread_ids:
                if (tid, uid) in votes:
                    result[(tid, uid)] = ProgressionStatus.DONE
                else:
                    result[(tid, uid)] = ProgressionStatus.NOT_STARTED

    elif function_type_id == 4:
        # COMPARISON (pairwise): existence of ItemComparisonEvaluation = DONE
        evals = set(
            db.session.query(
                ItemComparisonEvaluation.item_id,
                ItemComparisonEvaluation.user_id,
            )
            .filter(
                ItemComparisonEvaluation.user_id.in_(user_ids),
                ItemComparisonEvaluation.item_id.in_(thread_ids),
                ItemComparisonEvaluation.scenario_id == scenario_id,
            )
            .all()
        )
        for uid in user_ids:
            for tid in thread_ids:
                if (tid, uid) in evals:
                    result[(tid, uid)] = ProgressionStatus.DONE
                else:
                    result[(tid, uid)] = ProgressionStatus.NOT_STARTED

    return result


def get_user_progress_counts(scenario_id: int) -> Dict[str, Dict[str, int]]:
    """Get lightweight per-user progress counts (done/progressing/total).

    Returns dict of {username: {done, progressing, total}}.
    Much faster than get_progress_stats() — no agreement metrics computed.
    Use this when you only need progress bars, not full stats.
    """
    scenario = _get_scenario_or_raise(scenario_id)
    function_type = _get_function_type_or_raise(scenario.function_type_id)

    if function_type.name == "comparison":
        # Chat-based comparison: return empty (uses ComparisonSession)
        has_sessions = ComparisonSession.query.filter_by(scenario_id=scenario_id).first() is not None
        if has_sessions:
            return {}
        # Pairwise comparison: fall through to standard item-based flow

    scenario_users = (
        db.session.query(ScenarioUsers)
        .join(User, ScenarioUsers.user_id == User.id)
        .filter(
            ScenarioUsers.scenario_id == scenario_id,
            ScenarioUsers.membership_status == MembershipStatus.ACTIVE
        )
        .all()
    )

    all_scenario_threads = (
        db.session.query(ScenarioThreads)
        .filter(ScenarioThreads.scenario_id == scenario_id)
        .all()
    )
    all_thread_ids = [st.thread_id for st in all_scenario_threads if st.thread_id]
    all_user_ids = [su.user_id for su in scenario_users]

    progression_cache = _batch_get_progression_states(
        thread_ids=all_thread_ids,
        user_ids=all_user_ids,
        function_type_id=scenario.function_type_id,
        scenario_id=scenario_id,
    )

    result = {}
    for su in scenario_users:
        use_full = (
            su.manager_role != 'none'
            or (su.evaluation_role == 'assessor' and raters_receive_all_threads(scenario))
        )
        user_thread_ids = all_thread_ids if use_full else []
        if not use_full:
            # Would need distribution lookup — for simplicity use all threads
            user_thread_ids = all_thread_ids

        done = 0
        progressing = 0
        for tid in user_thread_ids:
            state = progression_cache.get((tid, su.user_id), ProgressionStatus.NOT_STARTED)
            if state == ProgressionStatus.DONE:
                done += 1
            elif state == ProgressionStatus.PROGRESSING:
                progressing += 1

        username = su.user.username if su.user else f"user_{su.user_id}"
        result[username] = {
            'done': done,
            'progressing': progressing,
            'total': len(user_thread_ids),
        }

    return result


def get_progress_stats(scenario_id: int, *, skip_provenance: bool = False) -> Dict[str, Any]:
    """Get detailed progress statistics for all users in a scenario.

    WARNING: This is expensive for large scenarios (computes agreement metrics,
    heatmaps, etc.). Use get_user_progress_counts() when you only need
    progress bars.

    Args:
        skip_provenance: If True, skip expensive provenance analysis.
            Used for synchronous cold-start to avoid blocking gevent workers.
            Background threads should call with skip_provenance=False.

    Caching is handled by scenario_stats_cache_service (DB-backed + in-memory).
    This function always performs the full computation.
    """
    scenario = _get_scenario_or_raise(scenario_id)
    function_type = _get_function_type_or_raise(scenario.function_type_id)

    # Chat-based comparison uses ComparisonSession; pairwise comparison
    # (created via wizard/generation) uses ItemComparisonEvaluation and
    # the standard item-based flow below.
    if function_type.name == "comparison":
        has_sessions = ComparisonSession.query.filter_by(scenario_id=scenario_id).first() is not None
        if has_sessions:
            return _get_comparison_progress_stats(scenario_id)
        # Otherwise fall through to standard item-based flow

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

    # Pre-load all scenario threads and thread objects to avoid N+1
    all_scenario_threads = (
        db.session.query(ScenarioThreads)
        .options(joinedload(ScenarioItems.item))
        .filter(ScenarioThreads.scenario_id == scenario_id)
        .all()
    )
    all_thread_ids = [st.thread_id for st in all_scenario_threads if st.thread_id]
    all_user_ids = [su.user_id for su in scenario_users]

    # Batch-load all progression states in a few queries instead of per-item
    progression_cache = _batch_get_progression_states(
        thread_ids=all_thread_ids,
        user_ids=all_user_ids,
        function_type_id=scenario.function_type_id,
        scenario_id=scenario_id,
    )

    # Build a lookup for distributed threads per user
    distributed_thread_ids_by_user = defaultdict(set)
    if any(
        su.evaluation_role == 'assessor' and not raters_receive_all_threads(scenario)
        for su in scenario_users
    ):
        distributions = (
            db.session.query(
                ScenarioUsers.user_id,
                ScenarioThreadDistribution.scenario_thread_id,
            )
            .join(ScenarioUsers, ScenarioThreadDistribution.scenario_user_id == ScenarioUsers.id)
            .filter(ScenarioUsers.scenario_id == scenario_id)
            .all()
        )
        st_id_to_thread_id = {st.id: st.thread_id for st in all_scenario_threads}
        for uid, st_id in distributions:
            tid = st_id_to_thread_id.get(st_id)
            if tid:
                distributed_thread_ids_by_user[uid].add(tid)

    for scenario_user in scenario_users:
        total_done_threads = 0
        total_progressing_threads = 0
        total_not_started_threads = 0

        use_full_threads = (
            scenario_user.manager_role != 'none'
            or (scenario_user.evaluation_role == 'assessor' and raters_receive_all_threads(scenario))
        )

        if use_full_threads:
            user_threads = all_scenario_threads
        else:
            user_dist_ids = distributed_thread_ids_by_user.get(scenario_user.user_id, set())
            user_threads = [st for st in all_scenario_threads if st.thread_id in user_dist_ids]

        for user_thread in user_threads:
            thread = user_thread.thread
            if not thread:
                continue

            progression_state = progression_cache.get(
                (thread.thread_id, scenario_user.user_id),
                ProgressionStatus.NOT_STARTED,
            )

            if progression_state:
                if progression_state == ProgressionStatus.PROGRESSING:
                    total_progressing_threads += 1
                elif progression_state == ProgressionStatus.DONE:
                    total_done_threads += 1
                else:
                    total_not_started_threads += 1

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
            "done_threads_list": [],
            "not_started_threads_list": [],
            "progressing_threads_list": [],
        }

        if scenario_user.evaluation_role == 'assessor':
            # ASSESSOR can interact (rate/evaluate)
            rater_stats.append(new_data)
        elif scenario_user.can_manage and scenario_user.evaluation_role != 'assessor':
            # OWNER/EDITOR shown in stats for overview purposes
            evaluator_stats.append(new_data)
        # Viewers without assessor role: excluded from stats entirely

    if function_type.name in {"ranking", "rating", "mail_rating", "authenticity", "labeling", "comparison"}:
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
    import logging as _logging
    _perf_log = _logging.getLogger('stats_perf')

    all_stats = rater_stats + evaluator_stats
    alpha = None
    if function_type.name in {"ranking", "rating", "mail_rating"} and len(all_stats) >= 2:
        _t = time.time()
        alpha = _calculate_ranking_agreement(all_stats, scenario_id, function_type.name)
        _perf_log.info("[StatsPerf] scenario=%s _calculate_ranking_agreement: %.3fs", scenario_id, time.time() - _t)

    # Calculate distribution and agreement metrics based on scenario type
    rating_distribution = None
    dimension_averages = None
    pairwise_agreement = None
    bucket_distribution = None
    provenance_analysis = None
    rating_provenance_analysis = None
    conversation_provenance = None
    rating_alpha = None  # Krippendorff's Alpha split by evaluator type

    # Calculate pairwise agreement using unified dispatcher (works for all types)
    if function_type.name in {"rating", "mail_rating", "labeling", "ranking", "comparison"}:
        _t = time.time()
        pairwise_agreement = _calculate_unified_pairwise_agreement(scenario_id, function_type.name)
        _perf_log.info("[StatsPerf] scenario=%s _calculate_pairwise_agreement: %.3fs", scenario_id, time.time() - _t)

    if function_type.name in {"rating", "mail_rating"}:
        rating_distribution = _calculate_rating_distribution(scenario_id)
        dimension_averages = _calculate_dimension_averages(scenario_id)
        rating_alpha = _calculate_rating_krippendorff_alpha(scenario_id)
        if not skip_provenance:
            rating_provenance_analysis = _calculate_rating_provenance_analysis(scenario_id)
        if function_type.name == "mail_rating":
            if not skip_provenance:
                conversation_provenance = _calculate_mail_rating_conversation_provenance(scenario_id)
        if alpha is None and rating_alpha and rating_alpha.get("all") is not None:
            alpha = rating_alpha["all"]
    elif function_type.name == "labeling":
        rating_distribution = _calculate_labeling_distribution(scenario_id)
    elif function_type.name == "comparison":
        rating_distribution = _calculate_comparison_choice_distribution(scenario_id)
    elif function_type.name == "ranking":
        _t = time.time()
        bucket_distribution = _calculate_bucket_distribution(scenario_id)
        _perf_log.info("[StatsPerf] scenario=%s _calculate_bucket_distribution: %.3fs", scenario_id, time.time() - _t)
        # Provenance analysis: skipped on synchronous cold-start, computed in background thread.
        if not skip_provenance:
            _t = time.time()
            provenance_analysis = _calculate_ranking_provenance_analysis(scenario_id)
            _perf_log.info("[StatsPerf] scenario=%s _calculate_ranking_provenance: %.3fs", scenario_id, time.time() - _t)
        else:
            _perf_log.info("[StatsPerf] scenario=%s _calculate_ranking_provenance: SKIPPED (cold start)", scenario_id)

    # Build model_registry for all LLM model_ids in evaluator_stats
    all_model_ids = [e['model_id'] for e in evaluator_stats if e.get('model_id')]
    # Also collect LLM labels from provenance analyses
    for analysis in (rating_provenance_analysis, provenance_analysis):
        if analysis and isinstance(analysis, dict):
            for segment in (analysis.get('segments') or {}).values():
                if isinstance(segment, dict):
                    for entry in segment.get('by_llm', []):
                        if entry.get('id'):
                            all_model_ids.append(entry['id'])
    model_registry = resolve_model_registry(all_model_ids) if all_model_ids else {}

    # Strip heavy pair_details from pairwise_agreement for the stats payload.
    # pair_details contains per-item agreement data which can be 1+ MB for large scenarios.
    # It's still available on-demand via the full pairwise_agreement endpoint.
    pairwise_summary = pairwise_agreement
    if isinstance(pairwise_agreement, dict) and "pair_details" in pairwise_agreement:
        pairwise_summary = {k: v for k, v in pairwise_agreement.items() if k != "pair_details"}

    result = {
        "rater_stats": rater_stats,
        "evaluator_stats": evaluator_stats,
        "viewer_stats": evaluator_stats,  # backward compatibility
        "krippendorff_alpha": alpha,
        "alpha_interpretation": _interpret_alpha(alpha),
        "rating_alpha": rating_alpha,  # split by evaluator type {all, humans, llms}
        "rating_distribution": rating_distribution,
        "dimension_averages": dimension_averages,
        "rating_provenance_analysis": rating_provenance_analysis,
        "conversation_provenance": conversation_provenance,
        "pairwise_agreement": pairwise_summary,
        "bucket_distribution": bucket_distribution,
        "provenance_analysis": provenance_analysis,
        "ranking_agreement": pairwise_summary,  # backward compatibility (deprecated)
        "model_registry": model_registry,
    }
    return result


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
        total_done = 0
        total_errors = 0
        total_not_started = 0
        recent_errors: List[Dict[str, Any]] = []

        for thread_id in thread_ids:
            result = model_results.get(thread_id)
            if result and result.payload_json and not result.error:
                total_done += 1
            elif result and result.error:
                total_errors += 1
                recent_errors.append({
                    "thread_id": thread_id,
                    "error": (result.error or "")[:200],
                })
            else:
                total_not_started += 1

        entries.append({
            "username": display_name,
            "model_id": model_id,
            "is_llm": True,
            "avatar_seed": None,
            "avatar_url": None,
            "total_threads": len(thread_ids),
            "done_threads": total_done,
            "not_started_threads": total_not_started,
            "error_threads": total_errors,
            "recent_errors": recent_errors[-3:],
            "progressing_threads": 0,
            "done_threads_list": [],
            "not_started_threads_list": [],
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

            if total_pairs_session == 0 or rated_pairs_session == 0:
                total_not_started_threads += 1
            elif rated_pairs_session < total_pairs_session:
                total_progressing_threads += 1
            else:
                total_done_threads += 1

        new_data = {
            "username": scenario_user.user.username,
            "is_llm": False,  # Explicit flag for human evaluators
            "total_threads": total_pairs,
            "done_threads": total_rated_pairs,
            "not_started_threads": max(total_pairs - total_rated_pairs, 0),
            "progressing_threads": total_progressing_threads,
            "done_threads_list": [],
            "not_started_threads_list": [],
            "progressing_threads_list": [],
        }

        if scenario_user.evaluation_role == 'assessor':
            # ASSESSOR can interact (rate/evaluate)
            rater_stats.append(new_data)
        elif scenario_user.can_manage and scenario_user.evaluation_role != 'assessor':
            # OWNER/EDITOR shown in stats for overview purposes
            evaluator_stats.append(new_data)
        # Viewers without assessor role: excluded from stats entirely

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
    # Use DimensionalRatingService.get_scenario_config() for consistent dimension resolution.
    # This ensures the same dimension IDs used by the rating UI are used for stats.
    # Without this, wizard-created scenarios can have mismatched dimension IDs
    # (eval_config.dimensions vs DEFAULT_DIMENSIONS) causing all-zero distributions.
    config = DimensionalRatingService.get_scenario_config(scenario_id)
    if not isinstance(config, dict) or 'error' in config:
        config = {}

    global_min = config.get("min", 1)
    global_max = config.get("max", 5)
    global_labels = config.get("labels", {})
    dimensions = config.get("dimensions", [])

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


def _calculate_labeling_distribution(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate label distribution for a labeling scenario.

    Returns distribution of category labels from both human and LLM evaluations.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        return {}

    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    categories = config.get("categories", [])
    if not categories:
        return {}

    # Build category lookup
    cat_lookup = {c.get("id"): c for c in categories if c.get("id")}

    # Count human labels from ItemLabelingEvaluation
    human_counts: Dict[str, int] = {}
    human_evals = (
        ItemLabelingEvaluation.query
        .filter(
            ItemLabelingEvaluation.scenario_id == scenario_id,
            ItemLabelingEvaluation.category_id.isnot(None)
        )
        .all()
    )
    for ev in human_evals:
        cat_id = ev.category_id
        if cat_id:
            human_counts[cat_id] = human_counts.get(cat_id, 0) + 1

    # Count LLM labels from LLMTaskResult
    llm_counts: Dict[str, int] = {}
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
        label = payload.get("label")
        if label:
            llm_counts[label] = llm_counts.get(label, 0) + 1

    def build_dist(counts: Dict[str, int]) -> List[Dict[str, Any]]:
        total = sum(counts.values()) if counts else 0
        distribution = []
        for cat in categories:
            cat_id = cat.get("id", "")
            cat_name = cat.get("name", cat_id)
            if isinstance(cat_name, dict):
                cat_name = cat_name.get("en", cat_name.get("de", cat_id))
            count = counts.get(cat_id, 0)
            distribution.append({
                "label": cat_name,
                "value": cat_id,
                "count": count,
                "percentage": round((count / total) * 100) if total > 0 else 0
            })
        return distribution

    # Combine for "all"
    all_counts: Dict[str, int] = {}
    for cat_id, count in human_counts.items():
        all_counts[cat_id] = all_counts.get(cat_id, 0) + count
    for cat_id, count in llm_counts.items():
        all_counts[cat_id] = all_counts.get(cat_id, 0) + count

    return {
        "all": build_dist(all_counts),
        "humans": build_dist(human_counts),
        "llms": build_dist(llm_counts),
    }


def _calculate_comparison_choice_distribution(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate choice distribution for a comparison scenario.

    Counts A/B/tie choices from both human (ItemComparisonEvaluation)
    and LLM (LLMTaskResult with task_type="comparison") evaluations.
    """
    # Fixed categories for comparison
    categories = [
        {"id": "A", "label": "A"},
        {"id": "B", "label": "B"},
        {"id": "tie", "label": "Tie"},
    ]

    # 1. Count human choices from ItemComparisonEvaluation
    human_counts: Dict[str, int] = {}
    human_evals = (
        ItemComparisonEvaluation.query
        .filter(
            ItemComparisonEvaluation.scenario_id == scenario_id,
            ItemComparisonEvaluation.choice.isnot(None)
        )
        .all()
    )
    for ev in human_evals:
        choice = ev.choice.upper() if ev.choice else None
        if choice == "TIE":
            choice = "tie"
        if choice in {"A", "B", "tie"}:
            human_counts[choice] = human_counts.get(choice, 0) + 1

    # 2. Count LLM choices from LLMTaskResult
    llm_counts: Dict[str, int] = {}
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id,
        task_type="comparison"
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

        # Item-based comparison: payload has direct "winner" field
        winner = payload.get("winner")
        if winner:
            w = winner.upper() if isinstance(winner, str) else None
            if w == "TIE":
                w = "tie"
            if w in {"A", "B", "tie"}:
                llm_counts[w] = llm_counts.get(w, 0) + 1

        # Session-based comparison: payload has "results" array with per-pair winners
        for sub in (payload.get("results") or []):
            if isinstance(sub, dict):
                sw = sub.get("winner")
                if sw:
                    sw = sw.upper() if isinstance(sw, str) else None
                    if sw == "TIE":
                        sw = "tie"
                    if sw in {"A", "B", "tie"}:
                        llm_counts[sw] = llm_counts.get(sw, 0) + 1

    def build_dist(counts: Dict[str, int]) -> List[Dict[str, Any]]:
        total = sum(counts.values()) if counts else 0
        distribution = []
        for cat in categories:
            cat_id = cat["id"]
            count = counts.get(cat_id, 0)
            distribution.append({
                "label": cat["label"],
                "value": cat_id,
                "count": count,
                "percentage": round((count / total) * 100) if total > 0 else 0
            })
        return distribution

    # Combine for "all"
    all_counts: Dict[str, int] = {}
    for cat_id, count in human_counts.items():
        all_counts[cat_id] = all_counts.get(cat_id, 0) + count
    for cat_id, count in llm_counts.items():
        all_counts[cat_id] = all_counts.get(cat_id, 0) + count

    return {
        "all": build_dist(all_counts),
        "humans": build_dist(human_counts),
        "llms": build_dist(llm_counts),
    }


def _calculate_dimension_averages(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate average scores per dimension for a rating scenario.

    Returns dimension averages split by evaluator type (all, humans, LLMs).
    Includes both human ratings from ItemDimensionRating and LLM ratings from LLMTaskResult.
    """
    # Use DimensionalRatingService.get_scenario_config() for consistent dimension resolution.
    # This ensures the same dimension IDs used by the rating UI are used for averages.
    config = DimensionalRatingService.get_scenario_config(scenario_id)
    if not isinstance(config, dict) or 'error' in config:
        return {}

    dimensions = config.get("dimensions", [])
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


def _calculate_rating_provenance_analysis(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate provenance analysis for rating scenarios.

    Links each rating assignment (human + LLM) to its generation origin
    (generation LLM + prompt) and reports which origins achieve the strongest
    normalized rating scores.
    """
    from db.models import (
        ScenarioItems,
        Message,
        GeneratedOutput,
        GeneratedOutputStatus,
        PromptTemplate,
    )

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        return {}

    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    scale_bounds = _extract_rating_scale_bounds(config)
    scale_min = scale_bounds["min"]
    scale_max = scale_bounds["max"]
    scale_span = scale_max - scale_min
    high_score_threshold_normalized = 0.8
    high_score_threshold_percent = round(high_score_threshold_normalized * 100, 1)

    def _normalize_score(raw_score: Any) -> Optional[float]:
        if raw_score is None:
            return None
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            return None

        if scale_span <= 0:
            return None

        normalized = (score - scale_min) / scale_span
        return max(0.0, min(1.0, normalized))

    def _empty_segment() -> Dict[str, Any]:
        return {
            "total_assignments": 0,
            "by_llm": [],
            "by_prompt": [],
            "by_combination": [],
            "best_llm": None,
            "best_prompt": None,
            "best_combination": None,
        }

    try:
        source_generation_job_id = (
            int(config.get("source_generation_job_id"))
            if config.get("source_generation_job_id") is not None
            else None
        )
    except (TypeError, ValueError):
        source_generation_job_id = None

    response: Dict[str, Any] = {
        "scale": {"min": scale_min, "max": scale_max},
        "metric_definition": {
            "primary": "avg_normalized_score",
            "secondary": "high_score_rate",
            "secondary_count": "high_score_count/total",
            "high_score_threshold_normalized": high_score_threshold_normalized,
            "high_score_threshold_percent": high_score_threshold_percent,
            "normalization_formula": "((score - min) / (max - min)) * 100",
        },
        "source_generation_job_id": source_generation_job_id,
        "matched_generation_items": 0,
        "total_items": 0,
        "segments": {
            "all": _empty_segment(),
            "human": _empty_segment(),
            "llm": _empty_segment(),
        },
    }

    scenario_items = (
        ScenarioItems.query
        .filter_by(scenario_id=scenario_id)
        .order_by(ScenarioItems.id.asc())
        .all()
    )
    item_ids = [row.item_id for row in scenario_items if row.item_id is not None]
    response["total_items"] = len(item_ids)
    if not item_ids:
        return response

    item_provenance: Dict[int, Dict[str, Any]] = {}
    if source_generation_job_id:
        outputs = (
            GeneratedOutput.query
            .filter_by(job_id=source_generation_job_id, status=GeneratedOutputStatus.COMPLETED)
            .order_by(GeneratedOutput.id.asc())
            .all()
        )

        if outputs:
            template_ids = {o.prompt_template_id for o in outputs if o.prompt_template_id}
            template_names: Dict[int, str] = {}
            if template_ids:
                template_names = {
                    tpl.id: tpl.name
                    for tpl in PromptTemplate.query.filter(PromptTemplate.id.in_(template_ids)).all()
                }

            def _serialize_output(output: GeneratedOutput, source: str = "generation_output") -> Dict[str, Any]:
                model_label = (output.llm_model_name or "").strip() or "Unknown LLM"
                variant_name = (output.prompt_variant_name or "").strip()
                template_name = (template_names.get(output.prompt_template_id) or "").strip()

                if variant_name and template_name and variant_name.lower() != template_name.lower():
                    prompt_label = f"{variant_name} / {template_name}"
                else:
                    prompt_label = variant_name or template_name or "Unknown prompt"

                prompt_key = variant_name or template_name or "unknown_prompt"
                return {
                    "llm_key": model_label,
                    "llm_label": model_label,
                    "prompt_key": prompt_key,
                    "prompt_label": prompt_label,
                    "source": source,
                }

            # Preferred path for generation-exported scenarios: stable output ordering.
            if len(outputs) == len(item_ids):
                for item_id, output in zip(item_ids, outputs):
                    item_provenance[item_id] = _serialize_output(output)
            else:
                output_lookup: Dict[tuple, List[GeneratedOutput]] = defaultdict(list)
                for output in outputs:
                    lookup_key = (
                        (output.llm_model_name or "").strip().lower(),
                        (output.generated_content or "").strip(),
                    )
                    output_lookup[lookup_key].append(output)

                messages = (
                    Message.query
                    .filter(Message.item_id.in_(item_ids))
                    .order_by(Message.item_id.asc(), Message.message_id.desc())
                    .all()
                )

                generated_message_by_item: Dict[int, Dict[str, str]] = {}
                for message in messages:
                    if message.item_id in generated_message_by_item:
                        continue

                    generated_by = (message.generated_by or "").strip()
                    sender = (message.sender or "").strip()
                    if generated_by and generated_by.lower() != "human" and not generated_by.lower().startswith("generation job"):
                        model_name = generated_by
                    else:
                        model_name = sender

                    if not model_name:
                        continue

                    generated_message_by_item[message.item_id] = {
                        "model_name": model_name,
                        "content": (message.content or "").strip(),
                    }

                used_output_ids = set()
                for item_id in item_ids:
                    message_info = generated_message_by_item.get(item_id)
                    if not message_info:
                        continue

                    lookup_key = (
                        message_info["model_name"].lower(),
                        message_info["content"],
                    )
                    candidates = output_lookup.get(lookup_key, [])
                    match = next((candidate for candidate in candidates if candidate.id not in used_output_ids), None)
                    if match:
                        used_output_ids.add(match.id)
                        item_provenance[item_id] = _serialize_output(match)

    response["matched_generation_items"] = sum(
        1 for entry in item_provenance.values() if entry.get("source") == "generation_output"
    )

    unresolved_item_ids = [item_id for item_id in item_ids if item_id not in item_provenance]
    if unresolved_item_ids:
        messages = (
            Message.query
            .filter(Message.item_id.in_(unresolved_item_ids))
            .order_by(Message.item_id.asc(), Message.message_id.desc())
            .all()
        )
        fallback_by_item: Dict[int, Dict[str, str]] = {}
        ignored_model_markers = {
            "human",
            "source",
            "client",
            "user",
            "system",
            "berater",
            "counsellor",
            "counselor",
        }
        for message in messages:
            if message.item_id in fallback_by_item:
                continue

            generated_by = (message.generated_by or "").strip()
            sender = (message.sender or "").strip()
            if generated_by and generated_by.lower() != "human" and not generated_by.lower().startswith("generation job"):
                model_name = generated_by
            else:
                model_name = sender

            model_name = (model_name or "").strip()
            if not model_name:
                continue
            if model_name.lower() in ignored_model_markers:
                continue

            fallback_by_item[message.item_id] = {
                "llm_key": model_name,
                "llm_label": model_name,
                "prompt_key": "unknown_prompt",
                "prompt_label": "Unknown prompt",
                "source": "message_fallback",
            }

        item_provenance.update(fallback_by_item)

    # Provenance analysis only makes sense with 2+ distinct generators OR 2+ distinct prompts.
    # With a single source, there is nothing to compare.
    if item_provenance:
        distinct_llms = {entry.get("llm_key") for entry in item_provenance.values()}
        distinct_prompts = {entry.get("prompt_key") for entry in item_provenance.values()}
        if len(distinct_llms) < 2 and len(distinct_prompts) < 2:
            return response

    assignments: List[tuple] = []

    human_ratings = (
        ItemDimensionRating.query
        .filter_by(scenario_id=scenario_id)
        .filter(ItemDimensionRating.status.in_([ProgressionStatus.DONE, ProgressionStatus.PROGRESSING]))
        .all()
    )
    for rating in human_ratings:
        score = rating.overall_score
        if score is None:
            dim_scores = rating.dimension_ratings or {}
            if isinstance(dim_scores, str):
                try:
                    dim_scores = json.loads(dim_scores)
                except (json.JSONDecodeError, TypeError):
                    dim_scores = {}
            if isinstance(dim_scores, dict) and dim_scores:
                numeric_scores = []
                for raw_value in dim_scores.values():
                    try:
                        numeric_scores.append(float(raw_value))
                    except (TypeError, ValueError):
                        continue
                if numeric_scores:
                    score = sum(numeric_scores) / len(numeric_scores)

        normalized_score = _normalize_score(score)
        if normalized_score is None:
            continue
        assignments.append((rating.item_id, float(score), normalized_score, "human"))

    llm_results = (
        LLMTaskResult.query
        .filter_by(scenario_id=scenario_id)
        .filter(
            LLMTaskResult.task_type.in_(["rating", "mail_rating"]),
            LLMTaskResult.error.is_(None),
        )
        .all()
    )
    for result in llm_results:
        score = _extract_overall_rating_from_payload(result.payload_json)
        normalized_score = _normalize_score(score)
        if normalized_score is None:
            continue
        assignments.append((result.item_id, float(score), normalized_score, "llm"))

    if not assignments:
        return response

    def _new_entity(entity_id: str, label: str) -> Dict[str, Any]:
        return {
            "id": str(entity_id),
            "label": label,
            "total": 0,
            "sum_score": 0.0,
            "avg_score": 0.0,
            "sum_normalized_score": 0.0,
            "avg_normalized_score": 0.0,
            "high_score_count": 0,
            "high_score_rate": 0.0,
        }

    segments_internal = {
        "all": {"total_assignments": 0, "by_llm": {}, "by_prompt": {}, "by_combination": {}},
        "human": {"total_assignments": 0, "by_llm": {}, "by_prompt": {}, "by_combination": {}},
        "llm": {"total_assignments": 0, "by_llm": {}, "by_prompt": {}, "by_combination": {}},
    }

    def _increment_entity(
        segment: Dict[str, Any],
        key_name: str,
        entity_id: str,
        label: str,
        score: float,
        normalized_score: float,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        entity_map = segment[key_name]
        row = entity_map.get(entity_id)
        if row is None:
            row = _new_entity(entity_id, label)
            if meta:
                row.update(meta)
            entity_map[entity_id] = row

        row["total"] += 1
        row["sum_score"] += score
        row["sum_normalized_score"] += normalized_score
        if normalized_score >= high_score_threshold_normalized:
            row["high_score_count"] += 1

    for item_id, score, normalized_score, evaluator_type in assignments:
        provenance = item_provenance.get(item_id) or {
            "llm_key": "unknown_llm",
            "llm_label": "Unknown LLM",
            "prompt_key": "unknown_prompt",
            "prompt_label": "Unknown prompt",
        }
        llm_key = provenance.get("llm_key") or "unknown_llm"
        llm_label = provenance.get("llm_label") or "Unknown LLM"
        prompt_key = provenance.get("prompt_key") or "unknown_prompt"
        prompt_label = provenance.get("prompt_label") or "Unknown prompt"
        combination_key = f"{prompt_key}|||{llm_key}"
        combination_label = f"{prompt_label} x {llm_label}"

        for segment_key in ("all", evaluator_type):
            segment = segments_internal[segment_key]
            segment["total_assignments"] += 1
            _increment_entity(
                segment=segment,
                key_name="by_llm",
                entity_id=llm_key,
                label=llm_label,
                score=score,
                normalized_score=normalized_score,
            )
            _increment_entity(
                segment=segment,
                key_name="by_prompt",
                entity_id=prompt_key,
                label=prompt_label,
                score=score,
                normalized_score=normalized_score,
            )
            _increment_entity(
                segment=segment,
                key_name="by_combination",
                entity_id=combination_key,
                label=combination_label,
                score=score,
                normalized_score=normalized_score,
                meta={
                    "prompt_label": prompt_label,
                    "llm_label": llm_label,
                },
            )

    def _finalize_rows(entity_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows = list(entity_map.values())
        for row in rows:
            total = row["total"]
            if total > 0:
                row["avg_score"] = round(row["sum_score"] / total, 2)
                row["avg_normalized_score"] = round((row["sum_normalized_score"] / total) * 100, 1)
                row["high_score_rate"] = round((row["high_score_count"] / total) * 100, 1)
            else:
                row["avg_score"] = 0.0
                row["avg_normalized_score"] = 0.0
                row["high_score_rate"] = 0.0

            row["sum_score"] = round(row["sum_score"], 3)
            row.pop("sum_normalized_score", None)

        rows.sort(
            key=lambda entry: (
                -entry["avg_normalized_score"],
                -entry["high_score_rate"],
                -entry["high_score_count"],
                -entry["total"],
                (entry["label"] or "").lower(),
            )
        )
        return rows

    finalized_segments = {}
    for segment_key, segment_data in segments_internal.items():
        by_llm = _finalize_rows(segment_data["by_llm"])
        by_prompt = _finalize_rows(segment_data["by_prompt"])
        by_combination = _finalize_rows(segment_data["by_combination"])
        finalized_segments[segment_key] = {
            "total_assignments": segment_data["total_assignments"],
            "by_llm": by_llm,
            "by_prompt": by_prompt,
            "by_combination": by_combination,
            "best_llm": by_llm[0] if by_llm else None,
            "best_prompt": by_prompt[0] if by_prompt else None,
            "best_combination": by_combination[0] if by_combination else None,
        }

    response["segments"] = finalized_segments
    return response


def _calculate_mail_rating_conversation_provenance(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate conversation partner provenance analysis for mail_rating scenarios.

    Derives counselor and client source (Human, Claude, Mistral, etc.)
    from Message.generated_by for each thread, then aggregates ratings
    by counselor source, client source, and their combination.
    """
    from db.models import ScenarioItems, Message

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        return {}

    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    scale_bounds = _extract_rating_scale_bounds(config)
    scale_min = scale_bounds["min"]
    scale_max = scale_bounds["max"]
    scale_span = scale_max - scale_min
    high_score_threshold_normalized = 0.8
    high_score_threshold_percent = round(high_score_threshold_normalized * 100, 1)

    def _normalize_score(raw_score):
        if raw_score is None:
            return None
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            return None
        if scale_span <= 0:
            return None
        return max(0.0, min(1.0, (score - scale_min) / scale_span))

    response = {
        "scale": {"min": scale_min, "max": scale_max},
        "metric_definition": {
            "primary": "avg_normalized_score",
            "secondary": "high_score_rate",
            "high_score_threshold_normalized": high_score_threshold_normalized,
            "high_score_threshold_percent": high_score_threshold_percent,
            "normalization_formula": "((score - min) / (max - min)) * 100",
        },
        "total_items": 0,
        "segments": {},
    }

    # Get all items (threads) in this scenario
    scenario_items = (
        ScenarioItems.query
        .filter_by(scenario_id=scenario_id)
        .order_by(ScenarioItems.id.asc())
        .all()
    )
    item_ids = [row.item_id for row in scenario_items if row.item_id is not None]
    response["total_items"] = len(item_ids)
    if not item_ids:
        return response

    # Derive counselor_source and client_source per thread from Message.generated_by
    messages = (
        Message.query
        .filter(Message.thread_id.in_(item_ids))
        .order_by(Message.thread_id.asc(), Message.message_id.asc())
        .all()
    )

    counselor_senders = {"berater", "beratende person", "counselor", "counsellor"}
    client_senders = {"klient", "ratsuchende person", "client"}

    thread_provenance = {}  # item_id -> {counselor_source, client_source}
    from collections import Counter
    thread_messages = defaultdict(list)
    for msg in messages:
        thread_messages[msg.thread_id].append(msg)

    for item_id in item_ids:
        msgs = thread_messages.get(item_id, [])
        counselor_sources = []
        client_sources = []
        for msg in msgs:
            sender_lower = (msg.sender or "").strip().lower()
            generated_by = (msg.generated_by or "Human").strip()
            if sender_lower in counselor_senders:
                counselor_sources.append(generated_by)
            elif sender_lower in client_senders:
                client_sources.append(generated_by)

        # Most common source for each role
        counselor_source = Counter(counselor_sources).most_common(1)[0][0] if counselor_sources else "Human"
        client_source = Counter(client_sources).most_common(1)[0][0] if client_sources else "Human"
        thread_provenance[item_id] = {
            "counselor_source": counselor_source,
            "client_source": client_source,
        }

    # Provenance analysis only makes sense with 2+ distinct counselor OR 2+ distinct client sources.
    if thread_provenance:
        distinct_counselors = {entry["counselor_source"] for entry in thread_provenance.values()}
        distinct_clients = {entry["client_source"] for entry in thread_provenance.values()}
        if len(distinct_counselors) < 2 and len(distinct_clients) < 2:
            return response

    # Collect all ratings (human + LLM) per thread
    assignments = []  # (item_id, score, normalized_score, evaluator_type)

    # Human ratings from UserMailHistoryRating
    human_ratings = (
        UserMailHistoryRating.query
        .filter(UserMailHistoryRating.thread_id.in_(item_ids))
        .all()
    )
    for rating in human_ratings:
        score = rating.overall_rating
        if score is None:
            # Average from individual dimensions
            dims = [rating.counsellor_coherence_rating, rating.client_coherence_rating, rating.quality_rating]
            valid_dims = [d for d in dims if d is not None]
            if valid_dims:
                score = sum(valid_dims) / len(valid_dims)
        normalized = _normalize_score(score)
        if normalized is not None:
            assignments.append((rating.thread_id, float(score), normalized, "human"))

    # Human ratings from ItemDimensionRating (if used for mail_rating)
    human_dim_ratings = (
        ItemDimensionRating.query
        .filter_by(scenario_id=scenario_id)
        .filter(ItemDimensionRating.status.in_([ProgressionStatus.DONE, ProgressionStatus.PROGRESSING]))
        .all()
    )
    for rating in human_dim_ratings:
        score = rating.overall_score
        if score is None:
            dim_scores = rating.dimension_ratings or {}
            if isinstance(dim_scores, str):
                try:
                    dim_scores = json.loads(dim_scores)
                except (json.JSONDecodeError, TypeError):
                    dim_scores = {}
            if isinstance(dim_scores, dict) and dim_scores:
                numeric = [float(v) for v in dim_scores.values() if v is not None]
                if numeric:
                    score = sum(numeric) / len(numeric)
        normalized = _normalize_score(score)
        if normalized is not None:
            assignments.append((rating.item_id, float(score), normalized, "human"))

    # LLM ratings from LLMTaskResult
    llm_results = (
        LLMTaskResult.query
        .filter_by(scenario_id=scenario_id)
        .filter(
            LLMTaskResult.task_type.in_(["rating", "mail_rating"]),
            LLMTaskResult.error.is_(None),
        )
        .all()
    )
    for result in llm_results:
        score = _extract_overall_rating_from_payload(result.payload_json)
        normalized = _normalize_score(score)
        if normalized is not None:
            assignments.append((result.item_id, float(score), normalized, "llm"))

    if not assignments:
        return response

    # Aggregate by counselor_source, client_source, and combination
    def _new_entity(entity_id, label):
        return {
            "id": str(entity_id),
            "label": label,
            "total": 0,
            "sum_score": 0.0,
            "avg_score": 0.0,
            "sum_normalized_score": 0.0,
            "avg_normalized_score": 0.0,
            "high_score_count": 0,
            "high_score_rate": 0.0,
        }

    segments_internal = {
        "all": {"total_assignments": 0, "by_counselor_source": {}, "by_client_source": {}, "by_combination": {}},
        "human": {"total_assignments": 0, "by_counselor_source": {}, "by_client_source": {}, "by_combination": {}},
        "llm": {"total_assignments": 0, "by_counselor_source": {}, "by_client_source": {}, "by_combination": {}},
    }

    def _increment(segment, key_name, entity_id, label, score, normalized, meta=None):
        entity_map = segment[key_name]
        row = entity_map.get(entity_id)
        if row is None:
            row = _new_entity(entity_id, label)
            if meta:
                row.update(meta)
            entity_map[entity_id] = row
        row["total"] += 1
        row["sum_score"] += score
        row["sum_normalized_score"] += normalized
        if normalized >= high_score_threshold_normalized:
            row["high_score_count"] += 1

    for item_id, score, normalized, evaluator_type in assignments:
        prov = thread_provenance.get(item_id)
        if not prov:
            continue

        counselor = prov["counselor_source"]
        client = prov["client_source"]
        combo_key = f"{counselor}|||{client}"
        combo_label = f"{counselor} \u00d7 {client}"

        for seg_key in ("all", evaluator_type):
            segment = segments_internal[seg_key]
            segment["total_assignments"] += 1
            _increment(segment, "by_counselor_source", counselor, counselor, score, normalized)
            _increment(segment, "by_client_source", client, client, score, normalized)
            _increment(segment, "by_combination", combo_key, combo_label, score, normalized, meta={
                "counselor_source": counselor,
                "client_source": client,
            })

    def _finalize(entity_map):
        rows = list(entity_map.values())
        for row in rows:
            total = row["total"]
            if total > 0:
                row["avg_score"] = round(row["sum_score"] / total, 2)
                row["avg_normalized_score"] = round((row["sum_normalized_score"] / total) * 100, 1)
                row["high_score_rate"] = round((row["high_score_count"] / total) * 100, 1)
            row["sum_score"] = round(row["sum_score"], 3)
            row.pop("sum_normalized_score", None)
        rows.sort(key=lambda e: (-e["avg_normalized_score"], -e["total"], (e["label"] or "").lower()))
        return rows

    finalized = {}
    for seg_key, seg_data in segments_internal.items():
        by_counselor = _finalize(seg_data["by_counselor_source"])
        by_client = _finalize(seg_data["by_client_source"])
        by_combo = _finalize(seg_data["by_combination"])
        finalized[seg_key] = {
            "total_assignments": seg_data["total_assignments"],
            "by_counselor_source": by_counselor,
            "by_client_source": by_client,
            "by_combination": by_combo,
            "best_counselor_source": by_counselor[0] if by_counselor else None,
            "best_client_source": by_client[0] if by_client else None,
            "best_combination": by_combo[0] if by_combo else None,
        }

    response["segments"] = finalized
    return response


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

    bucket_order = _extract_ranking_bucket_config(config)
    if not bucket_order:
        return []

    bucket_ids = [entry["id"] for entry in bucket_order]
    bucket_info = {entry["id"]: entry for entry in bucket_order}
    resolve_bucket_id = _build_bucket_id_resolver(bucket_order)

    # Initialize counts for all configured buckets
    bucket_counts = {bid: 0 for bid in bucket_ids}

    # Get all items for this scenario
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    if not item_ids:
        return []

    # 1. Get human rankings (only from active scenario members)
    active_user_ids = {
        su.user_id for su in
        ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            membership_status=MembershipStatus.ACTIVE,
        ).all()
    }
    human_rankings = (
        UserFeatureRanking.query
        .join(Feature, UserFeatureRanking.feature_id == Feature.feature_id)
        .filter(Feature.thread_id.in_(item_ids))
        .filter(UserFeatureRanking.bucket.isnot(None))
        .filter(UserFeatureRanking.user_id.in_(active_user_ids))
        .all()
    )

    for ranking in human_rankings:
        normalized = resolve_bucket_id(ranking.bucket)
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
                normalized = resolve_bucket_id(key)
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
            "label": info.get("label") or info.get("label_de") or info.get("label_en") or bucket_id,
            "label_de": info.get("label_de"),
            "label_en": info.get("label_en"),
            "count": count,
            "percentage": round((count / total) * 100) if total > 0 else 0,
            "color": info.get("color") or "#88c4c8",
        })

    return distribution


def _calculate_ranking_provenance_analysis(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate provenance analysis for ranking scenarios.

    The analysis links evaluator bucket assignments back to generation provenance
    (origin LLM + prompt) and reports which origins appear most frequently in the
    top bucket.
    """
    from db.models import (
        ScenarioItems,
        UserFeatureRanking,
        Feature,
        Message,
        GeneratedOutput,
        GeneratedOutputStatus,
        PromptTemplate,
    )

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        return {}

    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    bucket_order = _extract_ranking_bucket_config(config)
    if not bucket_order:
        return {}

    bucket_ids = [entry["id"] for entry in bucket_order]
    bucket_info = {entry["id"]: entry for entry in bucket_order}
    resolve_bucket_id = _build_bucket_id_resolver(bucket_order)
    top_bucket_id = bucket_ids[0]
    top_bucket_meta = bucket_info[top_bucket_id]
    top_bucket_label = top_bucket_meta.get("label") or top_bucket_meta.get("label_de") or top_bucket_id

    def _empty_segment() -> Dict[str, Any]:
        return {
            "total_assignments": 0,
            "by_llm": [],
            "by_prompt": [],
            "by_combination": [],
            "best_llm": None,
            "best_prompt": None,
            "best_combination": None,
        }

    try:
        source_generation_job_id = int(config.get("source_generation_job_id")) if config.get("source_generation_job_id") is not None else None
    except (TypeError, ValueError):
        source_generation_job_id = None

    response: Dict[str, Any] = {
        "top_bucket": {
            "id": top_bucket_id,
            "label": top_bucket_label,
            "label_de": top_bucket_meta.get("label_de"),
            "label_en": top_bucket_meta.get("label_en"),
        },
        "bucket_order": bucket_order,
        "metric_definition": {
            "numerator": "top_bucket_count",
            "denominator": "origin_assignments",
            "display_format": "top_bucket_count/total",
        },
        "source_generation_job_id": source_generation_job_id,
        "matched_generation_items": 0,
        "total_items": 0,
        "segments": {
            "all": _empty_segment(),
            "human": _empty_segment(),
            "llm": _empty_segment(),
        },
    }

    scenario_items = (
        ScenarioItems.query
        .filter_by(scenario_id=scenario_id)
        .order_by(ScenarioItems.id)
        .all()
    )
    item_ids = [entry.item_id for entry in scenario_items if entry.item_id is not None]
    response["total_items"] = len(item_ids)
    if not item_ids:
        return response

    item_provenance: Dict[int, Dict[str, Any]] = {}
    outputs: List[GeneratedOutput] = []
    template_names: Dict[int, str] = {}

    def _serialize_output_provenance(output: GeneratedOutput, source: str = "generation_output") -> Dict[str, Any]:
        model_label = (output.llm_model_name or "").strip() or "Unknown LLM"
        variant_name = (output.prompt_variant_name or "").strip()
        template_name = (template_names.get(output.prompt_template_id) or "").strip()

        if variant_name and template_name and variant_name.lower() != template_name.lower():
            prompt_label = f"{variant_name} / {template_name}"
        else:
            prompt_label = variant_name or template_name or "Unknown prompt"

        prompt_key = variant_name or template_name or "unknown_prompt"

        return {
            "llm_key": model_label,
            "llm_label": model_label,
            "prompt_key": prompt_key,
            "prompt_label": prompt_label,
            "source": source,
        }

    if source_generation_job_id:
        outputs = (
            GeneratedOutput.query
            .filter_by(job_id=source_generation_job_id, status=GeneratedOutputStatus.COMPLETED)
            .order_by(GeneratedOutput.id)
            .all()
        )

        if outputs:
            template_ids = {o.prompt_template_id for o in outputs if o.prompt_template_id}
            if template_ids:
                template_names = {
                    tpl.id: tpl.name
                    for tpl in PromptTemplate.query.filter(PromptTemplate.id.in_(template_ids)).all()
                }

            if len(outputs) == len(item_ids):
                for item_id, output in zip(item_ids, outputs):
                    item_provenance[item_id] = _serialize_output_provenance(output)
            else:
                output_lookup: Dict[tuple, List[GeneratedOutput]] = defaultdict(list)
                for output in outputs:
                    output_key = (
                        (output.llm_model_name or "").strip().lower(),
                        (output.generated_content or "").strip(),
                    )
                    output_lookup[output_key].append(output)

                messages = (
                    Message.query
                    .filter(Message.item_id.in_(item_ids))
                    .order_by(Message.item_id.asc(), Message.message_id.desc())
                    .all()
                )

                generated_message_by_item: Dict[int, Dict[str, str]] = {}
                for message in messages:
                    if message.item_id in generated_message_by_item:
                        continue

                    generated_by = (message.generated_by or "").strip()
                    sender = (message.sender or "").strip()
                    if generated_by and generated_by.lower() != "human" and not generated_by.lower().startswith("generation job"):
                        model_name = generated_by
                    else:
                        model_name = sender

                    if not model_name:
                        continue

                    generated_message_by_item[message.item_id] = {
                        "model_name": model_name,
                        "content": (message.content or "").strip(),
                    }

                used_output_ids = set()
                for item_id in item_ids:
                    message_info = generated_message_by_item.get(item_id)
                    if not message_info:
                        continue

                    lookup_key = (
                        message_info["model_name"].lower(),
                        message_info["content"],
                    )
                    candidates = output_lookup.get(lookup_key, [])
                    match = next((candidate for candidate in candidates if candidate.id not in used_output_ids), None)
                    if match:
                        used_output_ids.add(match.id)
                        item_provenance[item_id] = _serialize_output_provenance(match)

                # Last fallback: keep model provenance even when prompt cannot be matched.
                for item_id in item_ids:
                    if item_id in item_provenance:
                        continue
                    message_info = generated_message_by_item.get(item_id)
                    if not message_info:
                        continue
                    model_name = message_info["model_name"]
                    item_provenance[item_id] = {
                        "llm_key": model_name,
                        "llm_label": model_name,
                        "prompt_key": "unknown_prompt",
                        "prompt_label": "Unknown prompt",
                        "source": "message_fallback",
                    }

    response["matched_generation_items"] = sum(
        1 for entry in item_provenance.values() if entry.get("source") == "generation_output"
    )

    features = (
        Feature.query
        .options(joinedload(Feature.feature_type))
        .filter(Feature.item_id.in_(item_ids))
        .all()
    )
    if not features:
        return response

    outputs_by_content: Dict[str, List[GeneratedOutput]] = defaultdict(list)
    for output in outputs:
        normalized_content = _normalize_provenance_text(output.generated_content)
        if normalized_content:
            outputs_by_content[normalized_content].append(output)
    used_output_ids_for_feature = set()

    def _find_output_for_feature(feature: Feature) -> Optional[GeneratedOutput]:
        normalized_feature_content = _normalize_provenance_text(feature.content)
        if not normalized_feature_content:
            return None

        candidates = outputs_by_content.get(normalized_feature_content, [])
        if not candidates:
            return None

        feature_item_id = getattr(feature, "item_id", None)
        if feature_item_id is not None:
            item_matches = [
                candidate
                for candidate in candidates
                if candidate.source_item_id is not None and str(candidate.source_item_id) == str(feature_item_id)
            ]
            if item_matches:
                candidates = item_matches

        unused_candidates = [candidate for candidate in candidates if candidate.id not in used_output_ids_for_feature]
        if unused_candidates:
            candidates = unused_candidates

        feature_model_key = _normalize_model_identity(feature.model_id or "")
        if feature_model_key:
            model_matches = [
                candidate
                for candidate in candidates
                if feature_model_key in _normalize_model_identity(candidate.llm_model_name)
            ]
            if model_matches:
                candidates = model_matches

        match = candidates[0]
        used_output_ids_for_feature.add(match.id)
        return match

    feature_provenance: Dict[int, Dict[str, str]] = {}
    for feature in features:
        item_meta = item_provenance.get(feature.item_id)
        # Only trust item-level provenance when it was matched to real generation outputs.
        # Message fallback (e.g. sender='source') can otherwise collapse provenance into
        # "source / Unknown prompt" for all features.
        if item_meta and item_meta.get("source") == "generation_output":
            llm_key = item_meta["llm_key"]
            llm_label = item_meta["llm_label"]
            prompt_key = item_meta["prompt_key"]
            prompt_label = item_meta["prompt_label"]
            combination_key = f"{prompt_key}|||{llm_key}"
            combination_label = f"{prompt_label} x {llm_label}"
            feature_provenance[feature.feature_id] = {
                "llm_key": llm_key,
                "llm_label": llm_label,
                "prompt_key": prompt_key,
                "prompt_label": prompt_label,
                "combination_key": combination_key,
                "combination_label": combination_label,
            }
            continue

        direct_output_match = _find_output_for_feature(feature)
        if direct_output_match:
            feature_meta = _serialize_output_provenance(
                direct_output_match,
                source="generation_output_feature_match",
            )
            llm_key = feature_meta["llm_key"]
            llm_label = feature_meta["llm_label"]
            prompt_key = feature_meta["prompt_key"]
            prompt_label = feature_meta["prompt_label"]
            combination_key = f"{prompt_key}|||{llm_key}"
            combination_label = f"{prompt_label} x {llm_label}"
            feature_provenance[feature.feature_id] = {
                "llm_key": llm_key,
                "llm_label": llm_label,
                "prompt_key": prompt_key,
                "prompt_label": prompt_label,
                "combination_key": combination_key,
                "combination_label": combination_label,
            }
            continue

        llm_name = feature.model_id or "Unknown LLM"
        prompt_name = feature.feature_type.name if feature.feature_type else "Unknown prompt"
        combination_key = f"{prompt_name}|||{llm_name}"
        combination_label = f"{prompt_name} x {llm_name}"
        feature_provenance[feature.feature_id] = {
            "llm_key": llm_name,
            "llm_label": llm_name,
            "prompt_key": prompt_name,
            "prompt_label": prompt_name,
            "combination_key": combination_key,
            "combination_label": combination_label,
        }

    if not feature_provenance:
        return response

    # Track whether we have multiple generators for the ranking tables.
    # Even with a single source, we still collect assignments for the top-bucket
    # summary — provenance breakdown by LLM/prompt is only shown when 2+ exist.
    distinct_llms = {entry.get("llm_key") for entry in feature_provenance.values()}
    distinct_prompts = {entry.get("prompt_key") for entry in feature_provenance.values()}
    has_multiple_sources = len(distinct_llms) >= 2 or len(distinct_prompts) >= 2

    assignments: List[tuple] = []

    # Only include rankings from active scenario members
    active_user_ids = {
        su.user_id for su in
        ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            membership_status=MembershipStatus.ACTIVE,
        ).all()
    }
    human_rankings = (
        UserFeatureRanking.query
        .filter(UserFeatureRanking.feature_id.in_(list(feature_provenance.keys())))
        .filter(UserFeatureRanking.bucket.isnot(None))
        .filter(UserFeatureRanking.user_id.in_(active_user_ids))
        .all()
    )
    for ranking in human_rankings:
        normalized_bucket = resolve_bucket_id(ranking.bucket)
        if not normalized_bucket:
            continue
        assignments.append((ranking.feature_id, normalized_bucket, "human"))

    llm_results = (
        LLMTaskResult.query
        .filter_by(scenario_id=scenario_id, task_type="ranking")
        .filter(LLMTaskResult.error.is_(None))
        .all()
    )
    for result in llm_results:
        payload = result.payload_json
        if not payload:
            continue
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                continue
        if not isinstance(payload, dict):
            continue

        for bucket_name, feature_ids in payload.items():
            normalized_bucket = resolve_bucket_id(bucket_name)
            if not normalized_bucket or not isinstance(feature_ids, list):
                continue
            for feature_id in feature_ids:
                try:
                    normalized_feature_id = int(feature_id)
                except (TypeError, ValueError):
                    normalized_feature_id = feature_id
                if normalized_feature_id not in feature_provenance:
                    continue
                assignments.append((normalized_feature_id, normalized_bucket, "llm"))

    if not assignments:
        return response

    def _new_entity(entity_id: str, label: str) -> Dict[str, Any]:
        return {
            "id": str(entity_id),
            "label": label,
            "total": 0,
            "top_bucket_count": 0,
            "top_bucket_rate": 0.0,
            "bucket_counts": {bucket_id: 0 for bucket_id in bucket_ids},
            "bucket_percentages": {bucket_id: 0.0 for bucket_id in bucket_ids},
        }

    segments_internal = {
        "all": {"total_assignments": 0, "by_llm": {}, "by_prompt": {}, "by_combination": {}},
        "human": {"total_assignments": 0, "by_llm": {}, "by_prompt": {}, "by_combination": {}},
        "llm": {"total_assignments": 0, "by_llm": {}, "by_prompt": {}, "by_combination": {}},
    }

    def _increment_entity(
        segment: Dict[str, Any],
        key_name: str,
        entity_id: str,
        label: str,
        bucket_id: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        entity_map = segment[key_name]
        row = entity_map.get(entity_id)
        if row is None:
            row = _new_entity(entity_id, label)
            if meta:
                row.update(meta)
            entity_map[entity_id] = row

        row["total"] += 1
        row["bucket_counts"][bucket_id] = row["bucket_counts"].get(bucket_id, 0) + 1
        if bucket_id == top_bucket_id:
            row["top_bucket_count"] += 1

    for feature_id, bucket_id, evaluator_type in assignments:
        provenance = feature_provenance.get(feature_id)
        if not provenance:
            continue

        for segment_key in ("all", evaluator_type):
            segment = segments_internal[segment_key]
            segment["total_assignments"] += 1
            _increment_entity(
                segment=segment,
                key_name="by_llm",
                entity_id=provenance["llm_key"],
                label=provenance["llm_label"],
                bucket_id=bucket_id,
            )
            _increment_entity(
                segment=segment,
                key_name="by_prompt",
                entity_id=provenance["prompt_key"],
                label=provenance["prompt_label"],
                bucket_id=bucket_id,
            )
            _increment_entity(
                segment=segment,
                key_name="by_combination",
                entity_id=provenance["combination_key"],
                label=provenance["combination_label"],
                bucket_id=bucket_id,
                meta={
                    "prompt_label": provenance["prompt_label"],
                    "llm_label": provenance["llm_label"],
                },
            )

    def _finalize_rows(entity_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows = list(entity_map.values())
        for row in rows:
            total = row["total"]
            if total > 0:
                row["top_bucket_rate"] = round((row["top_bucket_count"] / total) * 100, 1)
                row["bucket_percentages"] = {
                    bucket_id: round((row["bucket_counts"].get(bucket_id, 0) / total) * 100, 1)
                    for bucket_id in bucket_ids
                }
            else:
                row["top_bucket_rate"] = 0.0
                row["bucket_percentages"] = {bucket_id: 0.0 for bucket_id in bucket_ids}

        rows.sort(
            key=lambda entry: (
                -entry["top_bucket_rate"],
                -entry["top_bucket_count"],
                -entry["total"],
                (entry["label"] or "").lower(),
            )
        )
        return rows

    finalized_segments = {}
    for segment_key, segment_data in segments_internal.items():
        by_llm = _finalize_rows(segment_data["by_llm"])
        by_prompt = _finalize_rows(segment_data["by_prompt"])
        by_combination = _finalize_rows(segment_data["by_combination"])
        finalized_segments[segment_key] = {
            "total_assignments": segment_data["total_assignments"],
            "by_llm": by_llm,
            "by_prompt": by_prompt,
            "by_combination": by_combination,
            "best_llm": by_llm[0] if by_llm else None,
            "best_prompt": by_prompt[0] if by_prompt else None,
            "best_combination": by_combination[0] if by_combination else None,
        }

    response["segments"] = finalized_segments
    return response


def _calculate_ranking_agreement_heatmap(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate pairwise bucket agreement between evaluators for ranking scenarios.

    Each feature (Zusammenfassung) is placed into exactly one bucket by each evaluator.
    Agreement = number of features where both evaluators chose the same bucket,
    divided by the total number of co-rated features.

    Example: 2 evaluators rated 40 features, agree on bucket for 23 → 57.5%
    """
    from db.models import UserFeatureRanking, Feature, ScenarioItems, RatingScenarios
    from collections import defaultdict

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        return {"evaluators": [], "agreements": {}}

    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    bucket_order = _extract_ranking_bucket_config(config)
    if not bucket_order:
        return {"evaluators": [], "agreements": {}}

    resolve_bucket_id = _build_bucket_id_resolver(bucket_order)

    # Get all items for this scenario
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    if not item_ids:
        return {"evaluators": [], "agreements": {}}

    # feature_id -> {evaluator_id: bucket}
    feature_buckets = defaultdict(dict)
    users_set = set()
    user_info = {}

    def _normalize_id(value: Any) -> Any:
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    # 1. Get human rankings - each row is one feature → one bucket (active members only)
    active_user_ids = {
        su.user_id for su in
        ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            membership_status=MembershipStatus.ACTIVE,
        ).all()
    }
    human_rankings = (
        UserFeatureRanking.query
        .join(Feature, UserFeatureRanking.feature_id == Feature.feature_id)
        .filter(Feature.item_id.in_(item_ids))
        .filter(UserFeatureRanking.bucket.isnot(None))
        .filter(UserFeatureRanking.user_id.in_(active_user_ids))
        .all()
    )

    for ranking in human_rankings:
        feature_id = ranking.feature_id
        user_id = ranking.user_id
        bucket = resolve_bucket_id(ranking.bucket)
        if not bucket:
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
            normalized_bucket = resolve_bucket_id(bucket_key)
            if not normalized_bucket or not isinstance(feature_ids, list):
                continue
            for fid in feature_ids:
                feature_buckets[_normalize_id(fid)][llm_user_id] = normalized_bucket

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
        "agreements": agreements,
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


def _calculate_comparison_pairwise_agreement(scenario_id: int) -> Dict[str, Any]:
    """
    Calculate pairwise agreement between evaluators for comparison scenarios.

    Agreement is measured by how often evaluators choose the same option (A/B/tie) for an item.
    Handles both item-based (ItemComparisonEvaluation) and session-based (LLMTaskResult) comparisons.
    """
    from collections import defaultdict

    # Get all items for this scenario
    scenario_threads = ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [st.thread_id for st in scenario_threads if st.thread_id]

    if not item_ids:
        return {"evaluators": [], "agreements": {}}

    # item_id -> {evaluator_id: choice}
    item_choices = defaultdict(dict)
    users_set = set()
    user_info = {}

    # 1. Human evaluations from ItemComparisonEvaluation
    human_evals = (
        ItemComparisonEvaluation.query
        .filter(
            ItemComparisonEvaluation.scenario_id == scenario_id,
            ItemComparisonEvaluation.item_id.in_(item_ids),
            ItemComparisonEvaluation.choice.isnot(None)
        )
        .all()
    )

    for ev in human_evals:
        item_id = ev.item_id
        user_id = ev.user_id
        choice = ev.choice.upper() if ev.choice else None
        if choice == "TIE":
            choice = "tie"
        if not choice or choice not in {"A", "B", "tie"}:
            continue

        users_set.add(user_id)
        if user_id not in user_info:
            user = User.query.get(user_id)
            name = user.username if user else f"User {user_id}"
            user_info[user_id] = {"id": user_id, "name": name, "isLLM": False}

        item_choices[item_id][user_id] = choice

    # 2. LLM evaluations from LLMTaskResult
    llm_results = LLMTaskResult.query.filter_by(
        scenario_id=scenario_id,
        task_type="comparison"
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
        item_id = result.thread_id

        if item_id not in item_ids:
            continue

        # Item-based: direct winner field
        winner = payload.get("winner")
        if winner:
            w = winner.upper() if isinstance(winner, str) else None
            if w == "TIE":
                w = "tie"
            if w in {"A", "B", "tie"}:
                users_set.add(llm_user_id)
                if llm_user_id not in user_info:
                    llm_model = LLMModel.query.filter_by(model_id=model_id).first()
                    name = llm_model.display_name if llm_model else model_id.split("/")[-1]
                    user_info[llm_user_id] = {"id": llm_user_id, "name": name, "isLLM": True}
                item_choices[item_id][llm_user_id] = w

    if not users_set:
        return {"evaluators": [], "agreements": {}}

    evaluators = list(user_info.values())

    # Calculate pairwise agreement (percentage of items with same choice)
    agreements = {}
    user_list = list(users_set)

    for i, user1 in enumerate(user_list):
        for user2 in user_list[i+1:]:
            common_items = []
            for item_id, user_cats in item_choices.items():
                if user1 in user_cats and user2 in user_cats:
                    common_items.append((user_cats[user1], user_cats[user2]))

            if len(common_items) >= 1:
                agreements_count = sum(1 for c1, c2 in common_items if c1 == c2)
                agreement = agreements_count / len(common_items)

                key = f"{min(str(user1), str(user2))}-{max(str(user1), str(user2))}"
                agreements[key] = round(agreement, 3)

    return {
        "evaluators": evaluators,
        "agreements": agreements,
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

        # Get threads assigned to this user (distributed assessors) or all threads
        if su.evaluation_role == 'assessor' and distribution_mode != DISTRIBUTION_MODE_ALL:
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
        "authenticity_provenance": _calculate_authenticity_provenance(
            thread_ids=thread_ids,
            ground_truth=ground_truth,
            user_stats=user_stats,
            user_vote_map=user_vote_map,
            llm_vote_map=llm_vote_map,
        ),
    }


def get_scenario_stats_payload(scenario_id: int) -> Dict[str, Any]:
    scenario = _get_scenario_or_raise(scenario_id)
    function_type = _get_function_type_or_raise(scenario.function_type_id)
    if function_type.name == "authenticity":
        stats = get_authenticity_stats(scenario_id)
        kind = "authenticity"
    else:
        from services.scenario_stats_cache_service import get_cached_stats
        stats = get_cached_stats(scenario_id)
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


def _calculate_authenticity_provenance(
    *,
    thread_ids: List[int],
    ground_truth: Dict[int, bool],
    user_stats: List[Dict[str, Any]],
    user_vote_map: Dict[int, Dict],
    llm_vote_map: Dict[str, Dict],
) -> Optional[Dict[str, Any]]:
    """Calculate provenance analysis for authenticity scenarios.

    Groups threads by their generation source (Human vs each LLM model) and
    calculates:
    - For fake sources: fool_rate (% of evaluator votes that said "real")
    - For real sources: false_positive_rate (% of votes that said "fake")
    """
    if not thread_ids:
        return None

    # Load AuthenticityConversation rows to get model per thread
    auth_convs = AuthenticityConversation.query.filter(
        AuthenticityConversation.thread_id.in_(thread_ids)
    ).all()

    if not auth_convs:
        return None

    # Map thread_id -> source model (None = Human)
    thread_source = {}
    for ac in auth_convs:
        thread_source[ac.thread_id] = ac.model  # None for real, model name for fake

    # Group thread_ids by source
    source_threads: Dict[str, List[int]] = defaultdict(list)
    for tid in thread_ids:
        source = thread_source.get(tid)
        label = source if source else "Human"
        source_threads[label].append(tid)

    # Collect all evaluator votes per thread (human + LLM)
    def _get_vote_string(vote_obj) -> Optional[str]:
        if vote_obj is None:
            return None
        if isinstance(vote_obj, str):
            return vote_obj.lower()
        if hasattr(vote_obj, 'vote') and vote_obj.vote:
            return vote_obj.vote.lower()
        return None

    # Build unified vote list: [(thread_id, vote_string), ...]
    all_votes_by_thread: Dict[int, List[str]] = defaultdict(list)

    for uid, votes_dict in user_vote_map.items():
        for tid, vote_obj in votes_dict.items():
            vote_str = _get_vote_string(vote_obj)
            if vote_str:
                all_votes_by_thread[tid].append(vote_str)

    for model_id, votes_dict in llm_vote_map.items():
        for tid, vote_str in votes_dict.items():
            if vote_str:
                all_votes_by_thread[tid].append(vote_str.lower())

    by_source = []
    for source_label, tids in source_threads.items():
        is_fake = source_label != "Human"
        source_type = "llm" if is_fake else "human"
        total_votes = 0
        fooled_votes = 0  # said "real" on fake content
        detected_votes = 0  # said "fake" on fake content
        correct_votes = 0  # said "real" on real content
        false_positive_votes = 0  # said "fake" on real content

        for tid in tids:
            for vote_str in all_votes_by_thread.get(tid, []):
                total_votes += 1
                if is_fake:
                    if vote_str == "real":
                        fooled_votes += 1
                    else:
                        detected_votes += 1
                else:
                    if vote_str == "real":
                        correct_votes += 1
                    else:
                        false_positive_votes += 1

        entry = {
            "source": source_label,
            "source_type": source_type,
            "is_fake": is_fake,
            "thread_count": len(tids),
            "total_votes": total_votes,
        }

        if is_fake:
            entry["fooled_votes"] = fooled_votes
            entry["detected_votes"] = detected_votes
            entry["fool_rate"] = round(fooled_votes / total_votes * 100, 1) if total_votes > 0 else 0.0
        else:
            entry["correct_votes"] = correct_votes
            entry["false_positive_votes"] = false_positive_votes
            entry["false_positive_rate"] = round(false_positive_votes / total_votes * 100, 1) if total_votes > 0 else 0.0

        by_source.append(entry)

    # Sort: fake sources by fool_rate descending, human sources at end
    fake_sources = sorted(
        [s for s in by_source if s["is_fake"]],
        key=lambda s: s.get("fool_rate", 0),
        reverse=True,
    )
    human_sources = [s for s in by_source if not s["is_fake"]]
    by_source_sorted = fake_sources + human_sources

    # Summary
    best_fooling = fake_sources[0] if fake_sources else None
    human_fp_rate = human_sources[0].get("false_positive_rate") if human_sources else None

    return {
        "by_source": by_source_sorted,
        "summary": {
            "best_fooling_source": best_fooling["source"] if best_fooling else None,
            "best_fool_rate": best_fooling.get("fool_rate") if best_fooling else None,
            "human_false_positive_rate": human_fp_rate,
            "total_sources": len(by_source_sorted),
        },
    }
