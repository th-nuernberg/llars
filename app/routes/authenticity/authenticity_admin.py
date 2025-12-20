"""
Authenticity (Fake/Echt) Admin Routes

Provides an import endpoint for dataset items in the format:
{
  "metadata": {...},
  "messages": [...]
}
"""

from __future__ import annotations

import hashlib
import json
import logging
import zlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import jsonify, request

from flask import g
import numpy as np

from auth.decorators import authentik_required, admin_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.feature_service import FeatureService
from db.db import db
from db.models import EmailThread, Message, AuthenticityConversation, UserAuthenticityVote
from db.tables import (RatingScenarios, ScenarioUsers, ScenarioThreads,
                       ScenarioThreadDistribution, ScenarioRoles, User)


logger = logging.getLogger(__name__)


def _parse_int(value: Any, *, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _build_sample_key(metadata: Dict[str, Any]) -> str:
    """
    Create a stable unique key for the imported sample.

    We hash a normalized subset of metadata to keep key length small and stable.
    """
    normalized = {
        "format_version": metadata.get("format_version"),
        "conversation_id": metadata.get("conversation_id"),
        "augmentation_type": metadata.get("augmentation_type"),
        "replaced_positions": sorted(metadata.get("replaced_positions") or []),
        "num_replacements": metadata.get("num_replacements"),
        "total_messages": metadata.get("total_messages"),
        "saeule": metadata.get("saeule"),
        "split": metadata.get("split"),
        "model": metadata.get("model"),
        "model_short": metadata.get("model_short"),
        "generated_at": metadata.get("generated_at"),
    }
    raw = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    version = str(metadata.get("format_version") or "v6")
    return f"{version}:{digest}"


def _pick_chat_id(sample_key: str, *, institut_id: int, function_type_id: int) -> int:
    """
    Pick a chat_id that is stable for this sample_key and does not collide with existing rows.
    """
    base = zlib.crc32(sample_key.encode("utf-8")) & 0x7FFFFFFF
    if base == 0:
        base = 1

    for offset in range(0, 1000):
        chat_id = (base + offset) & 0x7FFFFFFF
        existing_thread = EmailThread.query.filter_by(
            chat_id=chat_id,
            institut_id=institut_id,
            function_type_id=function_type_id,
        ).first()

        if not existing_thread:
            return chat_id

        existing_meta = AuthenticityConversation.query.filter_by(thread_id=existing_thread.thread_id).first()
        if existing_meta and existing_meta.sample_key == sample_key:
            return chat_id

    raise ConflictError("Could not allocate unique chat_id for this dataset item")


def _validate_item(item: Any) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not isinstance(item, dict):
        raise ValidationError("Item must be an object with keys: metadata, messages")

    metadata = item.get("metadata")
    messages = item.get("messages")

    if not isinstance(metadata, dict):
        raise ValidationError("metadata must be an object")
    if not isinstance(messages, list) or not all(isinstance(m, dict) for m in messages):
        raise ValidationError("messages must be a list of objects")
    if len(messages) == 0:
        raise ValidationError("messages must not be empty")

    return metadata, messages


@data_bp.route("/admin/authenticity/import", methods=["POST"])
@authentik_required
@require_permission("data:import")
@handle_api_errors(logger_name="authenticity")
def import_authenticity_dataset():
    """
    Import one or many authenticity samples.

    Body:
      - single item object, or
      - list of item objects
    """
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValidationError("Invalid JSON body")

    items = payload if isinstance(payload, list) else [payload]
    if not items:
        raise ValidationError("No items provided")

    function_type = FeatureService.get_function_type_by_name("authenticity")
    if not function_type:
        raise NotFoundError("Authenticity function type not found")

    results = {
        "ok": True,
        "imported": 0,
        "skipped_existing": 0,
        "errors": [],
        "thread_ids": [],
    }

    for idx, item in enumerate(items):
        try:
            metadata, messages = _validate_item(item)

            sample_key = _build_sample_key(metadata)
            existing = AuthenticityConversation.query.filter_by(sample_key=sample_key).first()
            if existing:
                results["skipped_existing"] += 1
                results["thread_ids"].append(int(existing.thread_id))
                continue

            institut_id = _parse_int(metadata.get("saeule"), default=0)
            chat_id = _pick_chat_id(sample_key, institut_id=institut_id, function_type_id=function_type.function_type_id)

            generated_at = _parse_datetime(metadata.get("generated_at"))
            base_time = generated_at or (datetime.utcnow() - timedelta(seconds=len(messages)))

            # Create EmailThread (function_type_id=authenticity)
            thread = EmailThread(
                chat_id=chat_id,
                institut_id=institut_id,
                subject="Fake/Echt – Import",
                sender="LLARS Import",
                function_type_id=function_type.function_type_id,
            )
            db.session.add(thread)
            db.session.flush()  # assign thread_id

            thread.subject = f"Fake/Echt – Fall #{thread.thread_id}"

            # Create messages
            is_fake = False
            for i, m in enumerate(messages):
                role = str(m.get("role") or m.get("sender") or m.get("from") or "Unbekannt")
                content = m.get("content")
                if content is None:
                    raise ValidationError("Each message requires 'content'")
                content = str(content)

                msg_is_synth = bool(m.get("is_synthetic", False))
                is_fake = is_fake or msg_is_synth

                generated_by = m.get("generated_by")
                if msg_is_synth:
                    generated_by = str(generated_by or metadata.get("model") or "Synthetic")
                else:
                    generated_by = "Human"

                ts = _parse_datetime(m.get("timestamp")) or (base_time + timedelta(seconds=i))

                db.session.add(
                    Message(
                        thread_id=thread.thread_id,
                        sender=role,
                        content=content,
                        timestamp=ts,
                        generated_by=generated_by,
                    )
                )

            # Fallback: trust metadata counters if present (definition: fake if >=1 replacement)
            if _parse_int(metadata.get("num_replacements"), default=0) > 0:
                is_fake = True

            # Persist metadata
            db.session.add(
                AuthenticityConversation(
                    thread_id=thread.thread_id,
                    sample_key=sample_key,
                    conversation_id=_parse_int(metadata.get("conversation_id"), default=0) or None,
                    augmentation_type=str(metadata.get("augmentation_type") or "") or None,
                    replaced_positions=metadata.get("replaced_positions") or None,
                    num_replacements=_parse_int(metadata.get("num_replacements"), default=0) or None,
                    total_messages=_parse_int(metadata.get("total_messages"), default=len(messages)) or None,
                    saeule=str(metadata.get("saeule") or "") or None,
                    split=str(metadata.get("split") or "") or None,
                    model=str(metadata.get("model") or "") or None,
                    model_short=str(metadata.get("model_short") or "") or None,
                    generated_at=generated_at,
                    format_version=str(metadata.get("format_version") or "") or None,
                    is_fake=bool(is_fake),
                    metadata_json=metadata,
                )
            )

            db.session.commit()

            results["imported"] += 1
            results["thread_ids"].append(int(thread.thread_id))

        except Exception as exc:
            db.session.rollback()
            results["ok"] = False
            results["errors"].append({"index": idx, "error": str(exc)})

    return jsonify(results), 200


def _calculate_krippendorff_alpha(ratings_matrix: np.ndarray) -> Optional[float]:
    """
    Calculate Krippendorff's Alpha for nominal data.

    Args:
        ratings_matrix: 2D array where rows are raters, columns are items
                       Values: 0 = real, 1 = fake, np.nan = no rating

    Returns:
        Alpha coefficient or None if not calculable
    """
    if ratings_matrix.size == 0:
        return None

    # Flatten and remove NaN
    n_items = ratings_matrix.shape[1]
    n_raters = ratings_matrix.shape[0]

    if n_items < 2 or n_raters < 2:
        return None

    # Count observed disagreement
    D_o = 0.0
    n_pairs = 0

    for col in range(n_items):
        values = ratings_matrix[:, col]
        valid_values = values[~np.isnan(values)]
        n_valid = len(valid_values)

        if n_valid < 2:
            continue

        # Count disagreements within this item
        for i in range(n_valid):
            for j in range(i + 1, n_valid):
                if valid_values[i] != valid_values[j]:
                    D_o += 1
                n_pairs += 1

    if n_pairs == 0:
        return None

    D_o = D_o / n_pairs

    # Calculate expected disagreement
    all_values = ratings_matrix.flatten()
    valid_all = all_values[~np.isnan(all_values)]
    n_total = len(valid_all)

    if n_total < 2:
        return None

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


@data_bp.route("/admin/scenario/<int:scenario_id>/user_stats", methods=["GET"])
@admin_required
@handle_api_errors(logger_name="authenticity")
def get_authenticity_scenario_stats(scenario_id: int):
    """
    Get comprehensive statistics for an authenticity scenario.

    Returns user progress, inter-rater reliability (Krippendorff's Alpha),
    accuracy against ground truth, and vote distribution.
    """
    scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    # Get all scenario users
    scenario_users = (
        db.session.query(ScenarioUsers)
        .join(User, ScenarioUsers.user_id == User.id)
        .filter(ScenarioUsers.scenario_id == scenario_id)
        .all()
    )

    # Get all threads in this scenario
    scenario_threads = (
        db.session.query(ScenarioThreads)
        .filter(ScenarioThreads.scenario_id == scenario_id)
        .all()
    )
    thread_ids = [st.thread.thread_id for st in scenario_threads if st.thread]

    if not thread_ids:
        return jsonify({
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
        }), 200

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

    # Build user stats
    user_stats = []
    user_vote_map = {}  # user_id -> {thread_id -> vote}

    for su in scenario_users:
        user = su.user
        user_id = user.id

        # Get threads assigned to this user (for RATER role) or all threads (for VIEWER)
        if su.role == ScenarioRoles.RATER:
            user_thread_ids = [
                dist.scenario_thread.thread.thread_id
                for dist in ScenarioThreadDistribution.query
                .join(ScenarioUsers, ScenarioThreadDistribution.scenario_user_id == ScenarioUsers.id)
                .join(ScenarioThreads, ScenarioThreadDistribution.scenario_thread_id == ScenarioThreads.id)
                .filter(ScenarioUsers.user_id == user_id, ScenarioUsers.scenario_id == scenario_id)
                .all()
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

        # Calculate accuracy against ground truth
        correct = 0
        incorrect = 0
        for tid in user_thread_ids:
            vote = votes_by_thread.get(tid)
            if vote and vote.vote and tid in ground_truth:
                vote_is_fake = vote.vote.lower() == "fake"
                if vote_is_fake == ground_truth[tid]:
                    correct += 1
                else:
                    incorrect += 1

        accuracy = round(correct / (correct + incorrect) * 100, 1) if (correct + incorrect) > 0 else None

        # Detailed vote lists
        voted_threads = []
        pending_threads = []
        for tid in user_thread_ids:
            thread_info = {"thread_id": tid}
            # Get thread subject
            thread = EmailThread.query.filter_by(thread_id=tid).first()
            if thread:
                thread_info["subject"] = thread.subject

            vote = votes_by_thread.get(tid)
            if vote and vote.vote:
                thread_info["vote"] = vote.vote
                thread_info["confidence"] = vote.confidence
                thread_info["is_correct"] = (vote.vote.lower() == "fake") == ground_truth.get(tid, False)
                voted_threads.append(thread_info)
            else:
                pending_threads.append(thread_info)

        user_stats.append({
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
            "voted_threads": voted_threads,
            "pending_threads": pending_threads,
        })

    # Calculate Krippendorff's Alpha
    # Build ratings matrix: rows = users with votes, cols = threads
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
    total_pending = len(thread_ids) * len([u for u in user_stats if u["role"] == "rater"]) - (total_real_votes + total_fake_votes)

    # Overall accuracy
    all_correct = sum(u["correct_count"] for u in user_stats)
    all_incorrect = sum(u["incorrect_count"] for u in user_stats)
    overall_accuracy = round(all_correct / (all_correct + all_incorrect) * 100, 1) if (all_correct + all_incorrect) > 0 else None

    return jsonify({
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
    }), 200
