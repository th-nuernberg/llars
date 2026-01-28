"""
Authenticity (Fake/Echt) Evaluation Routes

User workflow:
1) List accessible threads (scenario-based access control)
2) Open a thread and read the conversation
3) Vote if it is real or fake

NOTE: Diese Endpoints verwenden den SchemaAdapter Service für einheitliche
Datenformate. Neue Frontend-Komponenten sollten die /schema Endpoints nutzen.
"""

from __future__ import annotations

import logging

from flask import jsonify, request, g, current_app

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.evaluation.schema_adapter_service import SchemaAdapter
from services.feature_service import FeatureService
from services.scenario_stats_service import get_scenario_ids_for_thread
from services.thread_service import ThreadService
from db.database import db
from db.models import (
    Message, UserAuthenticityVote, EvaluationItem,
    ScenarioItems, ScenarioUsers, RatingScenarios
)


logger = logging.getLogger(__name__)


def _emit_scenario_stats_updates(thread_id: int) -> None:
    """Emit scenario stats updates via SocketIO."""
    socketio = current_app.extensions.get('socketio')
    if not socketio:
        return
    try:
        from socketio_handlers.events_scenarios import emit_scenario_stats_updated
        for scenario_id in get_scenario_ids_for_thread(thread_id):
            emit_scenario_stats_updated(socketio, scenario_id)
    except Exception:
        pass


def _normalize_vote(value: str) -> str:
    """Normalize vote value to 'real' or 'fake'."""
    v = str(value or "").strip().lower()
    if v in {"echt", "real", "human", "mensch"}:
        return "real"
    if v in {"fake", "falsch", "synthetic", "ki"}:
        return "fake"
    return ""


def _check_authenticity_access(item_id: int, user_id: int) -> bool:
    """Check if user has access to an authenticity item."""
    eval_item = EvaluationItem.query.get(item_id)
    if eval_item:
        scenario = SchemaAdapter.check_scenario_access(item_id, user_id)
        return scenario is not None

    # Fallback to legacy check
    function_type = FeatureService.get_function_type_by_name("authenticity")
    if not function_type:
        return False
    return ThreadService.can_user_access_thread(user_id, item_id, function_type.function_type_id)


@data_bp.route("/email_threads/authenticity", methods=["GET"])
@authentik_required
@require_permission("feature:authenticity:view")
@handle_api_errors(logger_name="authenticity")
def list_authenticity_threads():
    """List all evaluation items available for Fake/Echt evaluation."""
    user = g.authentik_user

    # Try new EvaluationItem model first (authenticity function_type_id = 5)
    scenarios = RatingScenarios.query.filter_by(function_type_id=5).all()

    threads_list = []
    seen_items = set()
    item_ids = []

    for scenario in scenarios:
        scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id,
            user_id=user.id
        ).first()
        if not scenario_user:
            continue

        scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario.id).all()
        for si in scenario_items:
            if si.item_id in seen_items:
                continue
            seen_items.add(si.item_id)
            item_ids.append(si.item_id)

            eval_item = EvaluationItem.query.get(si.item_id)
            if eval_item:
                threads_list.append({
                    'thread_id': eval_item.item_id,
                    'chat_id': eval_item.chat_id,
                    'institut_id': getattr(eval_item, 'institut_id', None),
                    'subject': eval_item.subject,
                    'sender': getattr(eval_item, 'sender', None),
                })

    # Fallback to legacy ThreadService
    try:
        function_type = FeatureService.get_function_type_by_name("authenticity")
        if function_type:
            threads = ThreadService.get_threads_for_user(user.id, function_type.function_type_id)
            for t in threads:
                if t.thread_id not in seen_items:
                    seen_items.add(t.thread_id)
                    item_ids.append(t.thread_id)
                    threads_list.append({
                        "thread_id": t.thread_id,
                        "chat_id": t.chat_id,
                        "institut_id": t.institut_id,
                        "subject": t.subject,
                        "sender": t.sender,
                    })
    except Exception:
        pass

    # Get votes for all items
    votes = {}
    if item_ids:
        rows = (
            db.session.query(UserAuthenticityVote)
            .filter(
                UserAuthenticityVote.user_id == user.id,
                UserAuthenticityVote.thread_id.in_(item_ids)
            )
            .all()
        )
        votes = {v.thread_id: v for v in rows}

    # Add vote info to threads
    result = []
    for t in threads_list:
        tid = t['thread_id']
        result.append({
            **t,
            "voted": tid in votes,
            "vote": votes[tid].vote if tid in votes else None,
            "confidence": votes[tid].confidence if tid in votes else None,
        })

    return jsonify(result), 200


@data_bp.route("/email_threads/authenticity/<int:thread_id>", methods=["GET"])
@authentik_required
@require_permission("feature:authenticity:view")
@handle_api_errors(logger_name="authenticity")
def get_authenticity_thread(thread_id: int):
    """
    Get one thread conversation for authenticity evaluation.

    Supports query param ?schema=true for new schema format.
    Default returns legacy format for backwards compatibility.
    """
    user = g.authentik_user
    use_schema = request.args.get('schema', 'false').lower() == 'true'

    # First try new EvaluationItem model
    eval_item = EvaluationItem.query.get(thread_id)
    if eval_item:
        scenario = SchemaAdapter.check_scenario_access(thread_id, user.id)
        if not scenario:
            raise ValidationError("Access denied")

        # Return new schema format if requested
        if use_schema:
            schema_data = SchemaAdapter.get_schema_data(scenario, thread_id)
            return jsonify(schema_data.model_dump()), 200

        # Return legacy format using SchemaAdapter
        thread_data = SchemaAdapter.get_authenticity_thread_data(thread_id, user.id)
        if thread_data:
            return jsonify(thread_data), 200

    # Fallback to legacy ThreadService
    function_type = FeatureService.get_function_type_by_name("authenticity")
    if not function_type:
        raise NotFoundError("Authenticity function type not found")

    if not ThreadService.can_user_access_thread(user.id, thread_id, function_type.function_type_id):
        raise ValidationError("Access denied")

    thread = ThreadService.get_thread_by_id(thread_id, function_type.function_type_id)
    if not thread:
        raise NotFoundError("Email thread not found or not for authenticity")

    messages = (
        Message.query.filter_by(thread_id=thread_id)
        .order_by(Message.timestamp.asc(), Message.message_id.asc())
        .all()
    )

    vote = UserAuthenticityVote.query.filter_by(user_id=user.id, thread_id=thread_id).first()

    return jsonify({
        "thread_id": thread.thread_id,
        "subject": thread.subject,
        "sender": thread.sender,
        "messages": [
            {
                "message_id": m.message_id,
                "sender": m.sender,
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in messages
        ],
        "vote": (
            {
                "vote": vote.vote,
                "confidence": vote.confidence,
                "notes": vote.notes,
                "updated_at": vote.updated_at.isoformat() if getattr(vote, "updated_at", None) else None,
            }
            if vote
            else None
        ),
    }), 200


@data_bp.route("/email_threads/authenticity/<int:thread_id>/vote", methods=["POST"])
@authentik_required
@require_permission("feature:authenticity:edit")
@handle_api_errors(logger_name="authenticity")
def save_authenticity_vote(thread_id: int):
    """Create or update the current user's vote for a thread."""
    user = g.authentik_user

    if not _check_authenticity_access(thread_id, user.id):
        raise ValidationError("Access denied")

    data = request.get_json(silent=True) or {}
    vote_value = _normalize_vote(data.get("vote"))
    if vote_value not in {"real", "fake"}:
        raise ValidationError("vote must be 'real' or 'fake'")

    confidence = data.get("confidence", None)
    if confidence is not None:
        try:
            confidence = int(confidence)
        except Exception:
            raise ValidationError("confidence must be an integer (0-100)")
        confidence = max(0, min(100, confidence))

    notes = data.get("notes", None)
    if notes is not None:
        notes = str(notes)
        if len(notes) > 4000:
            raise ValidationError("notes too long (max 4000 chars)")

    # Use item_id for new model, thread_id for legacy
    row = UserAuthenticityVote.query.filter_by(user_id=user.id, thread_id=thread_id).first()
    if not row:
        row = UserAuthenticityVote.query.filter_by(user_id=user.id, item_id=thread_id).first()

    if row:
        row.vote = vote_value
        row.confidence = confidence
        row.notes = notes
    else:
        row = UserAuthenticityVote(
            user_id=user.id,
            thread_id=thread_id,
            item_id=thread_id,  # Set both for compatibility
            vote=vote_value,
            confidence=confidence,
            notes=notes,
        )
        db.session.add(row)

    db.session.commit()
    _emit_scenario_stats_updates(thread_id)

    return jsonify({"ok": True, "thread_id": thread_id, "vote": vote_value, "confidence": confidence}), 200


@data_bp.route("/email_threads/authenticity/<int:thread_id>/metadata", methods=["PATCH"])
@authentik_required
@require_permission("feature:authenticity:edit")
@handle_api_errors(logger_name="authenticity")
def update_authenticity_metadata(thread_id: int):
    """
    Update confidence and/or notes without requiring a vote.

    Creates a placeholder record if none exists (vote will be null until user votes).
    """
    user = g.authentik_user

    if not _check_authenticity_access(thread_id, user.id):
        raise ValidationError("Access denied")

    data = request.get_json(silent=True) or {}

    confidence = data.get("confidence")
    notes = data.get("notes")

    if confidence is not None:
        try:
            confidence = int(confidence)
        except Exception:
            raise ValidationError("confidence must be an integer (0-100)")
        confidence = max(0, min(100, confidence))

    if notes is not None:
        notes = str(notes)
        if len(notes) > 4000:
            raise ValidationError("notes too long (max 4000 chars)")

    # Check both thread_id and item_id
    row = UserAuthenticityVote.query.filter_by(user_id=user.id, thread_id=thread_id).first()
    if not row:
        row = UserAuthenticityVote.query.filter_by(user_id=user.id, item_id=thread_id).first()

    if row:
        if confidence is not None:
            row.confidence = confidence
        if notes is not None:
            row.notes = notes
    else:
        row = UserAuthenticityVote(
            user_id=user.id,
            thread_id=thread_id,
            item_id=thread_id,
            vote=None,
            confidence=confidence,
            notes=notes,
        )
        db.session.add(row)

    db.session.commit()
    _emit_scenario_stats_updates(thread_id)

    return jsonify({
        "ok": True,
        "thread_id": thread_id,
        "confidence": row.confidence,
        "notes": row.notes
    }), 200
