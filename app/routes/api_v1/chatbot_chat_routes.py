"""
``/api/v1/chatbots/<id>/chat`` + ``/capabilities`` — programmatic chat surface.

Wraps the existing ChatService / AgentChatService. Supports JSON response
(default) or Server-Sent Events (``stream=true``) for token-by-token output.
File uploads are intentionally NOT supported here — multipart-with-file
belongs to the browser-bound ``/api/chatbots/<id>/chat`` endpoint where
``FileProcessor`` is wired up. CI / programmatic clients send text-only.
"""

from __future__ import annotations

import json
import logging
import uuid

from flask import Response, g, jsonify, request, stream_with_context

from auth.decorators import api_key_or_token_required, require_api_scope
from db.models.chatbot import Chatbot
from decorators.error_handler import (
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from schemas.api_v1.chatbot_api import ChatMessageRequest
from services.chatbot.chat_service import ChatService
from services.chatbot.chatbot_access_service import ChatbotAccessService

from . import api_v1_bp
from .scenarios_routes import _validate_request

logger = logging.getLogger(__name__)


@api_v1_bp.route("/chatbots/<int:chatbot_id>/capabilities", methods=["GET"])
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbots.chat")
def chat_capabilities(chatbot_id: int):
    """Expose vision/RAG support + accepted file extensions for the bot."""
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or not ChatbotAccessService.user_can_access_chatbot_id(
            user.username, chatbot_id):
        raise NotFoundError(f"Chatbot {chatbot_id} not found")

    # FileProcessor lives in services.chatbot — defer the import so the
    # capability route doesn't import the whole chat service for non-chat
    # callers.
    from services.chatbot.file_processor import FileProcessor

    chat_service = ChatService(chatbot_id)
    vision = chat_service.supports_vision()
    return jsonify({
        "success": True,
        "capabilities": {
            "vision": vision,
            "rag": bool(chat_service.chatbot.rag_enabled),
            "supported_file_types": {
                "images": list(FileProcessor.SUPPORTED_IMAGES) if vision else [],
                "documents": list(FileProcessor.SUPPORTED_DOCUMENTS),
            },
        },
    })


@api_v1_bp.route("/chatbots/<int:chatbot_id>/chat", methods=["POST"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots.chat")
def chat(chatbot_id: int):
    """Send a message to the chatbot.

    JSON body matches ``ChatMessageRequest``. Set ``stream=true`` to get
    Server-Sent Events instead of a single JSON response.
    """
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or not ChatbotAccessService.user_can_access_chatbot_id(
            user.username, chatbot_id):
        raise NotFoundError(f"Chatbot {chatbot_id} not found")

    payload = _validate_request(ChatMessageRequest, request.get_json(silent=True))

    # Generate a session id when the caller didn't pin one — keeps every
    # CI run isolated from prior conversations.
    session_id = payload.session_id or f"api-v1-{uuid.uuid4().hex[:12]}"

    chat_service = ChatService(chatbot_id)

    if not payload.stream:
        try:
            result = chat_service.chat(
                message=payload.message,
                session_id=session_id,
                username=user.username,
                include_sources=payload.include_sources,
                conversation_id=payload.conversation_id,
            )
        except ValueError as exc:
            raise ApiValidationError(str(exc))
        return jsonify({"success": True, **result})

    # SSE path — reuse test_chat_stream's per-chunk format. Note: the
    # streaming helper inside ChatService doesn't persist the conversation
    # (matches /test_chat behaviour). For persistent streaming we'd need a
    # bigger refactor; for the v1 surface "stream=true" is positioned as
    # a low-latency preview and the caller does a non-stream POST when
    # they need the conversation saved.
    def event_stream():
        try:
            for chunk in chat_service.test_chat_stream(payload.message):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:  # noqa: BLE001 — surface to the SSE client
            logger.error("[api_v1.chat] streaming failed: %s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    response = Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"  # nginx: do not buffer SSE
    return response
