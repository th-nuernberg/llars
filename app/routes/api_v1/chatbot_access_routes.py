"""
``/api/v1/chatbots/<id>/access`` — read + set the chatbot allowlist.
"""

from __future__ import annotations

import logging

from flask import g, jsonify, request

from auth.decorators import api_key_or_token_required, require_api_scope
from db.models.chatbot import Chatbot
from decorators.error_handler import (
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from schemas.api_v1.chatbot_api import ChatbotAccessSpec
from services.chatbot.chatbot_access_service import ChatbotAccessService

from . import api_v1_bp
from .scenarios_routes import _validate_request

logger = logging.getLogger(__name__)


def _gate(chatbot_id: int, *, require_manage: bool):
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        raise NotFoundError(f"Chatbot {chatbot_id} not found")
    if require_manage:
        if not ChatbotAccessService.user_can_manage_chatbot(user.username, chatbot):
            raise NotFoundError(f"Chatbot {chatbot_id} not found")
    else:
        if not ChatbotAccessService.user_can_access_chatbot_id(user.username, chatbot_id):
            raise NotFoundError(f"Chatbot {chatbot_id} not found")
    return chatbot


@api_v1_bp.route("/chatbots/<int:chatbot_id>/access", methods=["GET"])
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbots.access")
def get_access(chatbot_id: int):
    chatbot = _gate(chatbot_id, require_manage=False)
    return jsonify({
        "success": True,
        "is_public": bool(chatbot.is_public),
        "allowed_usernames": ChatbotAccessService.get_allowed_usernames_for_chatbot(
            chatbot_id) or [],
        "allowed_roles": ChatbotAccessService.get_allowed_roles_for_chatbot(
            chatbot_id) or list(chatbot.allowed_roles or []),
    })


@api_v1_bp.route("/chatbots/<int:chatbot_id>/access", methods=["PUT"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots.access")
def set_access(chatbot_id: int):
    """Replace the access list. Roles are validated client-side by Pydantic
    via ``ChatbotAccessSpec`` (admin role rejected)."""
    chatbot = _gate(chatbot_id, require_manage=True)
    user = g.authentik_user
    payload = _validate_request(ChatbotAccessSpec, request.get_json(silent=True))

    # Toggle is_public on the row directly (not via set_chatbot_access).
    from db import db
    chatbot.is_public = bool(payload.is_public)
    db.session.commit()

    try:
        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=chatbot_id,
            usernames=payload.allowed_usernames,
            role_names=payload.allowed_roles,
            granted_by=user.username,
        )
    except ValueError as exc:
        raise ApiValidationError(str(exc))

    return jsonify({
        "success": True,
        "is_public": chatbot.is_public,
        "allowed_usernames": result.get("usernames", payload.allowed_usernames),
        "allowed_roles": result.get("role_names", payload.allowed_roles),
    })
