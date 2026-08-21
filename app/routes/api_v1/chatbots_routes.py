"""
``/api/v1/chatbots`` — top-level chatbot CRUD.

Auth: every route is gated by ``@api_key_or_token_required`` followed by
``@require_api_scope('chatbot:read'|'chatbot:write')``. Read endpoints use
``chatbot:read``; create/patch/delete/duplicate/tweak need ``chatbot:write``.

Mirrors the ``scenarios_routes.py`` pattern: thin glue, validation in
schemas, business logic in ``services/api_v1_chatbot_service.py``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from flask import g, jsonify, request

from auth.decorators import api_key_or_token_required, require_api_scope
from db.models.chatbot import Chatbot
from decorators.error_handler import (
    ConflictError,
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from schemas.api_v1.chatbot_api import (
    ChatbotCreateRequest,
    ChatbotPatchRequest,
    ChatbotTweakRequest,
)
from services.api_v1_chatbot_service import (
    ApiV1ChatbotConflict,
    ApiV1ChatbotError,
    ApiV1ChatbotNotFound,
    create_chatbot_one_shot,
    delete_chatbot,
    patch_chatbot,
    tweak_chatbot,
)
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.chatbot.chatbot_service import ChatbotService

from . import api_v1_bp
from .scenarios_routes import _validate_request  # reuse Pydantic→error mapping

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Visibility helpers
# ---------------------------------------------------------------------------


def _user_can_read(chatbot_id: int, user) -> bool:
    """Same gating as the legacy /api/chatbots: admin OR owner OR allowlisted.

    Returns False for unknown chatbots so the route can collapse 'no
    permission' and 'doesn't exist' into the same 404 (M1-pattern fix
    from the scenario surface — no IDOR oracle).
    """
    if user is None:
        return False
    return ChatbotAccessService.user_can_access_chatbot_id(
        user.username, chatbot_id
    )


def _user_can_manage(chatbot, user) -> bool:
    if user is None or chatbot is None:
        return False
    return ChatbotAccessService.user_can_manage_chatbot(user.username, chatbot)


def _hydrate_response(chatbot_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise the legacy ChatbotService shape into the v1 ChatbotResponse
    contract (renames where they differ; drops legacy fields)."""
    if not chatbot_dict:
        return {}
    out = dict(chatbot_dict)
    # The legacy service exposes is_public + allowed_roles at top-level
    # already; ensure allowed_usernames is present (read from access table).
    if "allowed_usernames" not in out and "id" in out:
        try:
            out["allowed_usernames"] = (
                ChatbotAccessService.get_allowed_usernames_for_chatbot(out["id"])
                or []
            )
        except Exception:
            out["allowed_usernames"] = []
    out.setdefault("allowed_roles", [])
    out.setdefault("collections", [])
    out.setdefault("job_id", None)
    return out


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@api_v1_bp.route("/chatbots", methods=["GET"])
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbots")
def list_chatbots():
    """List chatbots visible to the authenticated user.

    Pagination via ``?limit=&offset=``. Accessor admins see everything;
    everyone else sees chatbots they own + are allow-listed for.
    """
    user = g.authentik_user
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = max(int(request.args.get("offset", 0)), 0)
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    all_dicts = ChatbotService.get_all_chatbots(
        include_inactive=include_inactive, username=user.username,
    )
    total = len(all_dicts)
    page = all_dicts[offset:offset + limit]

    return jsonify({
        "success": True,
        "chatbots": [_hydrate_response(c) for c in page],
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@api_v1_bp.route("/chatbots", methods=["POST"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots")
def create_chatbot():
    """One-shot create. Body is ``ChatbotCreateRequest``.

    Set ``wizard.crawl_url`` to launch an async crawl after the row exists;
    the response then carries a ``job_id`` and the chatbot starts in
    ``build_status='crawling'``.
    """
    payload = _validate_request(
        ChatbotCreateRequest, request.get_json(silent=True),
    )
    user = g.authentik_user
    try:
        bot = create_chatbot_one_shot(payload, user.username)
    except ApiV1ChatbotConflict as exc:
        raise ConflictError(str(exc))
    except ApiV1ChatbotNotFound as exc:
        raise NotFoundError(str(exc))
    except ApiV1ChatbotError as exc:
        raise ApiValidationError(str(exc))

    return jsonify({"success": True, "chatbot": _hydrate_response(bot)}), 201


@api_v1_bp.route("/chatbots/<int:chatbot_id>", methods=["GET"])
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbots")
def get_chatbot(chatbot_id: int):
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or not _user_can_read(chatbot_id, user):
        raise NotFoundError(f"Chatbot {chatbot_id} not found")

    bot = ChatbotService.get_chatbot(chatbot_id)
    if not bot:
        raise NotFoundError(f"Chatbot {chatbot_id} not found")
    return jsonify({"success": True, "chatbot": _hydrate_response(bot)})


@api_v1_bp.route("/chatbots/<int:chatbot_id>", methods=["PATCH"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots")
def patch_chatbot_route(chatbot_id: int):
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        raise NotFoundError(f"Chatbot {chatbot_id} not found")
    if not _user_can_manage(chatbot, user):
        # M1: same 404 body as missing chatbot — no IDOR oracle.
        raise NotFoundError(f"Chatbot {chatbot_id} not found")

    payload = _validate_request(ChatbotPatchRequest, request.get_json(silent=True))
    try:
        bot = patch_chatbot(chatbot_id, payload, user.username)
    except ApiV1ChatbotNotFound as exc:
        raise NotFoundError(str(exc))
    except ApiV1ChatbotError as exc:
        raise ApiValidationError(str(exc))
    return jsonify({"success": True, "chatbot": _hydrate_response(bot)})


@api_v1_bp.route("/chatbots/<int:chatbot_id>/tweak", methods=["PATCH"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots")
def tweak_chatbot_route(chatbot_id: int):
    """Hot-tune a live chatbot. Narrower contract than PATCH — only fields
    that are safe to flip without a redeploy (system_prompt, temperature,
    model_name, rag_*).
    """
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        raise NotFoundError(f"Chatbot {chatbot_id} not found")
    if not _user_can_manage(chatbot, user):
        raise NotFoundError(f"Chatbot {chatbot_id} not found")

    payload = _validate_request(ChatbotTweakRequest, request.get_json(silent=True))
    try:
        bot = tweak_chatbot(chatbot_id, payload, user.username)
    except ApiV1ChatbotNotFound as exc:
        raise NotFoundError(str(exc))
    except ApiV1ChatbotError as exc:
        raise ApiValidationError(str(exc))
    return jsonify({"success": True, "chatbot": _hydrate_response(bot)})


@api_v1_bp.route("/chatbots/<int:chatbot_id>", methods=["DELETE"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots")
def delete_chatbot_route(chatbot_id: int):
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        raise NotFoundError(f"Chatbot {chatbot_id} not found")
    if not _user_can_manage(chatbot, user):
        raise NotFoundError(f"Chatbot {chatbot_id} not found")

    try:
        delete_chatbot(chatbot_id, user.username)
    except ApiV1ChatbotNotFound as exc:
        raise NotFoundError(str(exc))
    except ApiV1ChatbotError as exc:
        raise ApiValidationError(str(exc))

    return jsonify({"success": True, "deleted_id": chatbot_id})


@api_v1_bp.route("/chatbots/<int:chatbot_id>/duplicate", methods=["POST"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbots")
def duplicate_chatbot_route(chatbot_id: int):
    """Clone a chatbot; the duplicate is owned by the requesting user."""
    user = g.authentik_user
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot or not _user_can_read(chatbot_id, user):
        raise NotFoundError(f"Chatbot {chatbot_id} not found")

    try:
        new_bot = ChatbotService.duplicate_chatbot(chatbot_id, user.username)
    except ValueError as exc:
        raise ApiValidationError(str(exc))
    if not new_bot:
        raise NotFoundError(f"Chatbot {chatbot_id} not found")
    return jsonify({"success": True, "chatbot": _hydrate_response(new_bot)}), 201
