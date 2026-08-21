"""
``/api/v1/chatbots/<id>/conversations`` — read-only API for chat history.

Useful for studies that want to pull conversations for analysis without
giving the analyst a UI session. Mutating conversations is intentionally
NOT exposed here — that would require its own scope (``chatbot:chat`` or
similar) and is out of scope for v1.
"""

from __future__ import annotations

import logging

from flask import g, jsonify, request

from auth.decorators import api_key_or_token_required, require_api_scope
from db.models.chatbot import (
    Chatbot,
    ChatbotConversation,
    ChatbotMessage,
)
from decorators.error_handler import NotFoundError, handle_api_errors
from services.chatbot.chatbot_access_service import ChatbotAccessService

from . import api_v1_bp

logger = logging.getLogger(__name__)


def _gate(chatbot_id: int):
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or not ChatbotAccessService.user_can_access_chatbot_id(
            user.username, chatbot_id):
        raise NotFoundError(f"Chatbot {chatbot_id} not found")
    return chatbot


def _conversation_dict(conv: ChatbotConversation) -> dict:
    return {
        "id": conv.id,
        "chatbot_id": conv.chatbot_id,
        "session_id": conv.session_id,
        "username": conv.username,
        "title": conv.title,
        "is_active": conv.is_active,
        "message_count": conv.message_count,
        "started_at": conv.started_at.isoformat() if conv.started_at else None,
        "last_message_at": (
            conv.last_message_at.isoformat() if conv.last_message_at else None
        ),
    }


def _message_dict(m: ChatbotMessage, *, include_rag: bool = False) -> dict:
    out = {
        "id": m.id,
        "conversation_id": m.conversation_id,
        "role": m.role.value if hasattr(m.role, "value") else str(m.role),
        "content": m.content,
        "tokens_input": m.tokens_input,
        "tokens_output": m.tokens_output,
        "response_time_ms": m.response_time_ms,
        "user_rating": m.user_rating,
        "user_feedback": m.user_feedback,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }
    if include_rag:
        out["rag_sources"] = m.rag_sources
        out["rag_context"] = m.rag_context
    return out


@api_v1_bp.route("/chatbots/<int:chatbot_id>/conversations", methods=["GET"])
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbots.conversations")
def list_conversations(chatbot_id: int):
    """List conversations for this chatbot.

    Admins/owners see all conversations; everyone else sees only their own
    (per ``ChatbotAccessService.user_can_manage_chatbot``).
    """
    chatbot = _gate(chatbot_id)
    user = g.authentik_user
    is_owner = ChatbotAccessService.user_can_manage_chatbot(user.username, chatbot)

    limit = min(int(request.args.get("limit", 50)), 200)
    offset = max(int(request.args.get("offset", 0)), 0)

    q = ChatbotConversation.query.filter_by(chatbot_id=chatbot_id)
    if not is_owner:
        q = q.filter_by(username=user.username)
    total = q.count()
    rows = (
        q.order_by(ChatbotConversation.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return jsonify({
        "success": True,
        "conversations": [_conversation_dict(c) for c in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@api_v1_bp.route(
    "/chatbots/<int:chatbot_id>/conversations/<int:conv_id>", methods=["GET"]
)
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbots.conversations")
def get_conversation(chatbot_id: int, conv_id: int):
    chatbot = _gate(chatbot_id)
    conv = ChatbotConversation.query.filter_by(
        id=conv_id, chatbot_id=chatbot_id,
    ).first()
    if not conv:
        raise NotFoundError(f"Conversation {conv_id} not found")
    user = g.authentik_user
    is_owner = ChatbotAccessService.user_can_manage_chatbot(user.username, chatbot)
    # F4: a NULL `conv.username` (legacy/anonymous conversations) used to
    # short-circuit the inequality check via Python falsiness, letting any
    # `chatbot:read` reader see anyone else's transcript on a shared bot.
    # Guard explicitly: non-owners get nothing unless the conversation is
    # tagged with their own username.
    if not is_owner and (not conv.username or conv.username != user.username):
        raise NotFoundError(f"Conversation {conv_id} not found")
    return jsonify({"success": True, "conversation": _conversation_dict(conv)})


@api_v1_bp.route(
    "/chatbots/<int:chatbot_id>/conversations/<int:conv_id>/messages",
    methods=["GET"],
)
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbots.conversations")
def list_messages(chatbot_id: int, conv_id: int):
    """Pull all messages of a conversation.

    Query: ``include_rag=true`` adds ``rag_sources`` and ``rag_context`` to
    each row — large; off by default to keep payloads small.
    """
    chatbot = _gate(chatbot_id)
    conv = ChatbotConversation.query.filter_by(
        id=conv_id, chatbot_id=chatbot_id,
    ).first()
    if not conv:
        raise NotFoundError(f"Conversation {conv_id} not found")
    user = g.authentik_user
    is_owner = ChatbotAccessService.user_can_manage_chatbot(user.username, chatbot)
    # F4 (see get_conversation): explicit check, falsy NULL must not pass.
    if not is_owner and (not conv.username or conv.username != user.username):
        raise NotFoundError(f"Conversation {conv_id} not found")

    include_rag = request.args.get("include_rag", "false").lower() == "true"
    rows = (
        ChatbotMessage.query.filter_by(conversation_id=conv_id)
        .order_by(ChatbotMessage.created_at.asc())
        .all()
    )
    return jsonify({
        "success": True,
        "messages": [_message_dict(m, include_rag=include_rag) for m in rows],
        "total": len(rows),
    })
