"""
Socket.IO event handlers for "Gegenüberstellung" (Comparison).

Events (default namespace):
    Client → Server:
        - join_comparison_session   { sessionId }
        - comparison_message        { sessionId, message }
        - rate_response             { sessionId, messageId, selection }
        - generate_suggestion       { sessionId }
        - submit_justification      { messageId, justification }

    Server → Client:
        - messages_loaded           { messages }
        - message_created           { ...message }
        - message_updated           { message, ai_evaluation?, requires_justification? }
        - streaming_*              (see LLMResponseGenerator)
        - suggestion_generated      { suggestion }
        - suggestion_error          { message }
        - error                     { message }
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from flask import request
from flask_socketio import emit, join_room

from auth.decorators import get_or_create_user
from auth.oidc_validator import get_username, validate_token
from services.permission_service import PermissionService
from services.comparison.session_service import ComparisonSessionService
from services.comparison.response_generator import LLMResponseGenerator
from services.comparison.evaluation_service import ComparisonEvaluationService

logger = logging.getLogger(__name__)


def _require_user(permission_key: str) -> Optional[object]:
    token = str(request.args.get("token") or "").strip()
    payload = validate_token(token) if token else None
    if not payload:
        emit("error", {"message": "Unauthorized"})
        return None

    username = get_username(payload)
    if not username:
        emit("error", {"message": "Unauthorized"})
        return None

    if permission_key and not PermissionService.check_permission(username, permission_key):
        emit("error", {"message": "Forbidden"})
        return None

    return get_or_create_user(username)


def register_comparison_events(socketio) -> None:
    @socketio.on("join_comparison_session")
    def handle_join_comparison_session(data: Optional[Dict[str, Any]] = None):
        data = data or {}
        session_id = data.get("sessionId")
        client_id = request.sid

        user = _require_user("feature:comparison:view")
        if not user:
            return

        if not session_id:
            emit("error", {"message": "Session ID required"}, room=client_id)
            return

        try:
            session_id = int(session_id)
        except Exception:
            emit("error", {"message": "Invalid session ID"}, room=client_id)
            return

        session = ComparisonSessionService.get_session_by_id(session_id)
        if not session or session.user_id != user.id:
            emit("error", {"message": "Session not found"}, room=client_id)
            return

        room = f"comparison_{session_id}"
        join_room(room)
        logger.info(f"[Comparison] Client {client_id} joined session {session_id} ({user.username})")

        try:
            messages = ComparisonSessionService.get_all_messages(session_id)
            emit(
                "messages_loaded",
                {"messages": [ComparisonSessionService.serialize_message(m) for m in messages]},
                room=client_id,
            )

            if not messages:
                message_id = ComparisonSessionService.add_message(
                    session_id=session_id,
                    idx=0,
                    message_type="bot_pair",
                    content='{"llm1": "", "llm2": ""}',
                )
                created = ComparisonSessionService.get_message(message_id, session_id)
                if created:
                    emit("message_created", ComparisonSessionService.serialize_message(created), room=client_id)

                LLMResponseGenerator().generate_comparison_responses(
                    session=session,
                    message_id=message_id,
                    socketio=socketio,
                    client_id=client_id,
                )

        except Exception as e:
            logger.error(f"[Comparison] Error loading messages: {e}")
            emit("error", {"message": "Failed to load messages"}, room=client_id)

    @socketio.on("comparison_message")
    def handle_comparison_message(data: Optional[Dict[str, Any]] = None):
        data = data or {}
        session_id = data.get("sessionId")
        message = str(data.get("message") or "")
        client_id = request.sid

        user = _require_user("feature:comparison:edit")
        if not user:
            return

        if not session_id or not message.strip():
            emit("error", {"message": "Missing required data"}, room=client_id)
            return

        try:
            session_id = int(session_id)
        except Exception:
            emit("error", {"message": "Invalid session ID"}, room=client_id)
            return

        try:
            session = ComparisonSessionService.get_session_by_id(session_id)
            if not session or session.user_id != user.id:
                emit("error", {"message": "Session not found"}, room=client_id)
                return

            existing = ComparisonSessionService.get_all_messages(session_id)
            user_message_id = ComparisonSessionService.add_message(
                session_id=session_id,
                idx=len(existing),
                message_type="user",
                content=message,
            )

            existing = ComparisonSessionService.get_all_messages(session_id)
            bot_message_id = ComparisonSessionService.add_message(
                session_id=session_id,
                idx=len(existing),
                message_type="bot_pair",
                content='{"llm1": "", "llm2": ""}',
            )

            user_message = ComparisonSessionService.get_message(user_message_id, session_id)
            bot_message = ComparisonSessionService.get_message(bot_message_id, session_id)
            if user_message:
                emit("message_created", ComparisonSessionService.serialize_message(user_message), room=client_id)
            if bot_message:
                emit("message_created", ComparisonSessionService.serialize_message(bot_message), room=client_id)

            LLMResponseGenerator().generate_comparison_responses(
                session=session,
                message_id=bot_message_id,
                socketio=socketio,
                client_id=client_id,
            )

        except Exception as e:
            logger.error(f"[Comparison] Error handling message: {e}")
            emit("error", {"message": "Failed to process message"}, room=client_id)

    @socketio.on("rate_response")
    def handle_rate_response(data: Optional[Dict[str, Any]] = None):
        data = data or {}
        session_id = data.get("sessionId")
        message_id = data.get("messageId")
        selection = str(data.get("selection") or "").strip()
        client_id = request.sid

        user = _require_user("feature:comparison:edit")
        if not user:
            return

        if not session_id or not message_id or not selection:
            emit("error", {"message": "Missing required data"}, room=client_id)
            return

        try:
            session_id = int(session_id)
            message_id = int(message_id)
        except Exception:
            emit("error", {"message": "Invalid IDs"}, room=client_id)
            return

        session = ComparisonSessionService.get_session_by_id(session_id)
        if not session or session.user_id != user.id:
            emit("error", {"message": "Session not found"}, room=client_id)
            return

        try:
            if not ComparisonSessionService.set_message_selected(message_id, session_id, selection):
                emit("error", {"message": "Failed to save rating"}, room=client_id)
                return

            updated = ComparisonSessionService.get_message(message_id, session_id)
            if not updated:
                emit("error", {"message": "Message not found"}, room=client_id)
                return

            try:
                from socketio_handlers.events_scenarios import emit_scenario_stats_updated
                if session.scenario_id:
                    emit_scenario_stats_updated(socketio, session.scenario_id)
            except Exception:
                pass

            matches, ai_evaluation = ComparisonEvaluationService.perform_evaluation(
                message_id=message_id,
                session_id=session_id,
                user_selection=selection,
            )

            emit(
                "message_updated",
                {
                    "message": ComparisonSessionService.serialize_message(updated),
                    "ai_evaluation": ai_evaluation,
                    "requires_justification": bool(ai_evaluation is not None and not matches),
                },
                room=client_id,
            )

        except Exception as e:
            logger.error(f"[Comparison] Error saving rating: {e}")
            emit("error", {"message": "Failed to save rating"}, room=client_id)

    @socketio.on("generate_suggestion")
    def handle_generate_suggestion(data: Optional[Dict[str, Any]] = None):
        data = data or {}
        session_id = data.get("sessionId")
        client_id = request.sid

        user = _require_user("feature:comparison:edit")
        if not user:
            return

        if not session_id:
            emit("suggestion_error", {"message": "Missing session ID"}, room=client_id)
            return

        try:
            session_id = int(session_id)
        except Exception:
            emit("suggestion_error", {"message": "Invalid session ID"}, room=client_id)
            return

        try:
            session = ComparisonSessionService.get_session_by_id(session_id)
            if not session or session.user_id != user.id:
                emit("suggestion_error", {"message": "Session not found"}, room=client_id)
                return

            suggestion = LLMResponseGenerator.generate_counselor_suggestion(session)
            emit("suggestion_generated", {"suggestion": suggestion}, room=client_id)

        except Exception as e:
            logger.error(f"[Comparison] Error generating suggestion: {e}")
            emit("suggestion_error", {"message": "Failed to generate suggestion"}, room=client_id)

    @socketio.on("submit_justification")
    def handle_submit_justification(data: Optional[Dict[str, Any]] = None):
        data = data or {}
        message_id = data.get("messageId")
        justification = str(data.get("justification") or "")
        client_id = request.sid

        user = _require_user("feature:comparison:edit")
        if not user:
            return

        if not message_id:
            emit("error", {"message": "Missing message ID"}, room=client_id)
            return

        try:
            message_id = int(message_id)
        except Exception:
            emit("error", {"message": "Invalid message ID"}, room=client_id)
            return

        try:
            if ComparisonEvaluationService.save_user_justification(message_id, justification):
                emit("justification_saved", {"message": "Begründung gespeichert"}, room=client_id)
            else:
                emit("error", {"message": "Failed to save justification"}, room=client_id)
        except Exception as e:
            logger.error(f"[Comparison] Error saving justification: {e}")
            emit("error", {"message": "Failed to save justification"}, room=client_id)
