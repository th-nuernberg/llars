"""
``/api/v1/chatbots/<id>/collections`` — RAG collection assignment for a chatbot.

Wraps the existing ChatbotService collection methods. Read uses
``chatbot:read``; mutate operations require ``chatbot:write``.
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
from schemas.api_v1.chatbot_api import (
    ChatbotCollectionAssign,
    ChatbotCollectionPatch,
)
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.chatbot.chatbot_service import ChatbotService

from . import api_v1_bp
from .scenarios_routes import _validate_request

logger = logging.getLogger(__name__)


def _gate(chatbot_id: int, *, require_manage: bool):
    """Lookup + access check. Raises NotFoundError when invisible/missing."""
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


@api_v1_bp.route("/chatbots/<int:chatbot_id>/collections", methods=["GET"])
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbots.collections")
def list_collections(chatbot_id: int):
    _gate(chatbot_id, require_manage=False)
    cols = ChatbotService.get_collections(chatbot_id) or []
    return jsonify({"success": True, "collections": cols, "total": len(cols)})


@api_v1_bp.route("/chatbots/<int:chatbot_id>/collections", methods=["POST"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots.collections")
def assign_collection(chatbot_id: int):
    _gate(chatbot_id, require_manage=True)
    user = g.authentik_user

    payload = _validate_request(ChatbotCollectionAssign, request.get_json(silent=True))
    try:
        result = ChatbotService.assign_collection(
            chatbot_id=chatbot_id,
            collection_id=payload.collection_id,
            username=user.username,
            priority=payload.priority,
            weight=payload.weight,
            is_primary=payload.is_primary,
        )
    except ValueError as exc:
        raise ApiValidationError(str(exc))
    if not result:
        raise NotFoundError(
            f"Collection {payload.collection_id} not found or already assigned"
        )
    return jsonify({"success": True, "collection": result}), 201


@api_v1_bp.route(
    "/chatbots/<int:chatbot_id>/collections/<int:coll_id>", methods=["PATCH"]
)
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots.collections")
def update_collection(chatbot_id: int, coll_id: int):
    _gate(chatbot_id, require_manage=True)
    payload = _validate_request(ChatbotCollectionPatch, request.get_json(silent=True))
    data = payload.model_dump(exclude_none=True, mode="json")
    try:
        result = ChatbotService.update_collection_assignment(
            chatbot_id=chatbot_id, collection_id=coll_id, **data,
        )
    except ValueError as exc:
        raise ApiValidationError(str(exc))
    if not result:
        raise NotFoundError(
            f"Collection {coll_id} not assigned to chatbot {chatbot_id}"
        )
    return jsonify({"success": True, "collection": result})


@api_v1_bp.route(
    "/chatbots/<int:chatbot_id>/collections/<int:coll_id>", methods=["DELETE"]
)
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots.collections")
def remove_collection(chatbot_id: int, coll_id: int):
    _gate(chatbot_id, require_manage=True)
    try:
        ok = ChatbotService.remove_collection(chatbot_id, coll_id)
    except ValueError as exc:
        raise ApiValidationError(str(exc))
    if not ok:
        raise NotFoundError(
            f"Collection {coll_id} not assigned to chatbot {chatbot_id}"
        )
    return jsonify({"success": True, "removed_collection_id": coll_id})
