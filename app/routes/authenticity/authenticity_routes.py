"""
Authenticity (Fake/Echt) Evaluation Routes

User workflow:
1) List accessible threads (scenario-based access control)
2) Open a thread and read the conversation
3) Vote if it is real or fake
"""

from __future__ import annotations

from flask import jsonify, request, g

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.feature_service import FeatureService
from services.thread_service import ThreadService
from db.database import db
from db.models import Message, UserAuthenticityVote


def _normalize_vote(value: str) -> str:
    v = str(value or "").strip().lower()
    if v in {"echt", "real", "human", "mensch"}:
        return "real"
    if v in {"fake", "falsch", "synthetic", "ki"}:
        return "fake"
    return ""


@data_bp.route("/email_threads/authenticity", methods=["GET"])
@authentik_required
@require_permission("feature:authenticity:view")
@handle_api_errors(logger_name="authenticity")
def list_authenticity_threads():
    """List all email threads available for Fake/Echt evaluation."""
    user = g.authentik_user

    function_type = FeatureService.get_function_type_by_name("authenticity")
    if not function_type:
        raise NotFoundError("Authenticity function type not found")

    threads = ThreadService.get_threads_for_user(user.id, function_type.function_type_id)
    thread_ids = [t.thread_id for t in threads]

    votes = {}
    if thread_ids:
        rows = (
            db.session.query(UserAuthenticityVote)
            .filter(UserAuthenticityVote.user_id == user.id, UserAuthenticityVote.thread_id.in_(thread_ids))
            .all()
        )
        votes = {v.thread_id: v for v in rows}

    return jsonify([
        {
            "thread_id": t.thread_id,
            "chat_id": t.chat_id,
            "institut_id": t.institut_id,
            "subject": t.subject,
            "sender": t.sender,
            "voted": t.thread_id in votes,
            "vote": votes[t.thread_id].vote if t.thread_id in votes else None,
            "confidence": votes[t.thread_id].confidence if t.thread_id in votes else None,
        }
        for t in threads
    ]), 200


@data_bp.route("/email_threads/authenticity/<int:thread_id>", methods=["GET"])
@authentik_required
@require_permission("feature:authenticity:view")
@handle_api_errors(logger_name="authenticity")
def get_authenticity_thread(thread_id: int):
    """Get one thread conversation (without revealing synthetic markers)."""
    user = g.authentik_user

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

    return jsonify(
        {
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
        }
    ), 200


@data_bp.route("/email_threads/authenticity/<int:thread_id>/vote", methods=["POST"])
@authentik_required
@require_permission("feature:authenticity:edit")
@handle_api_errors(logger_name="authenticity")
def save_authenticity_vote(thread_id: int):
    """Create or update the current user's vote for a thread."""
    user = g.authentik_user

    function_type = FeatureService.get_function_type_by_name("authenticity")
    if not function_type:
        raise NotFoundError("Authenticity function type not found")

    if not ThreadService.can_user_access_thread(user.id, thread_id, function_type.function_type_id):
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

    row = UserAuthenticityVote.query.filter_by(user_id=user.id, thread_id=thread_id).first()
    if row:
        row.vote = vote_value
        row.confidence = confidence
        row.notes = notes
    else:
        row = UserAuthenticityVote(
            user_id=user.id,
            thread_id=thread_id,
            vote=vote_value,
            confidence=confidence,
            notes=notes,
        )
        db.session.add(row)

    db.session.commit()

    return jsonify({"ok": True, "thread_id": thread_id, "vote": vote_value, "confidence": confidence}), 200


@data_bp.route("/email_threads/authenticity/<int:thread_id>/metadata", methods=["PATCH"])
@authentik_required
@require_permission("feature:authenticity:edit")
@handle_api_errors(logger_name="authenticity")
def update_authenticity_metadata(thread_id: int):
    """Update confidence and/or notes without requiring a vote.

    Creates a placeholder record if none exists (vote will be null until user votes).
    This allows saving slider position and notes in real-time.
    """
    user = g.authentik_user

    function_type = FeatureService.get_function_type_by_name("authenticity")
    if not function_type:
        raise NotFoundError("Authenticity function type not found")

    if not ThreadService.can_user_access_thread(user.id, thread_id, function_type.function_type_id):
        raise ValidationError("Access denied")

    data = request.get_json(silent=True) or {}

    confidence = data.get("confidence")
    notes = data.get("notes")

    # Validate confidence if provided
    if confidence is not None:
        try:
            confidence = int(confidence)
        except Exception:
            raise ValidationError("confidence must be an integer (0-100)")
        confidence = max(0, min(100, confidence))

    # Validate notes if provided
    if notes is not None:
        notes = str(notes)
        if len(notes) > 4000:
            raise ValidationError("notes too long (max 4000 chars)")

    row = UserAuthenticityVote.query.filter_by(user_id=user.id, thread_id=thread_id).first()

    if row:
        # Update existing record
        if confidence is not None:
            row.confidence = confidence
        if notes is not None:
            row.notes = notes
    else:
        # Create new record with null vote (user hasn't decided yet)
        row = UserAuthenticityVote(
            user_id=user.id,
            thread_id=thread_id,
            vote=None,  # No vote yet
            confidence=confidence,
            notes=notes,
        )
        db.session.add(row)

    db.session.commit()

    return jsonify({
        "ok": True,
        "thread_id": thread_id,
        "confidence": row.confidence,
        "notes": row.notes
    }), 200

