"""
``/api/v1/chatbot-wizard/*`` — multi-step session API + one-shot quickbuild.

Two complementary entry points:
    POST /api/v1/chatbot-wizard/quickbuild
        — one POST starts crawl + auto-deploys; returns chatbot_id + job_id
    POST /api/v1/chatbot-wizard/sessions  → /sessions/{id}/crawl  →
        /sessions/{id}/generate-field  → /sessions/{id}/finalize
        — per-step session API for interactive clients

Both wrap ``ChatbotBuilderService`` (which delegates to ``ChatbotCreator``).
"""

from __future__ import annotations

import json
import logging

from flask import Response, g, jsonify, request, stream_with_context

from auth.decorators import api_key_or_token_required, require_api_scope
from db.models.chatbot import Chatbot
from decorators.error_handler import (
    ConflictError,
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from schemas.api_v1.chatbot_api import (
    WizardCrawlRequest,
    WizardFinalizeRequest,
    WizardGenerateFieldRequest,
    WizardQuickbuildRequest,
    WizardSessionCreateRequest,
)
from services.api_v1_chatbot_service import (
    ApiV1ChatbotConflict,
    ApiV1ChatbotError,
    ApiV1ChatbotNotFound,
    quickbuild_one_shot,
)
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.chatbot.chatbot_builder_service import ChatbotBuilderService

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


# ---------------------------------------------------------------------------
# One-shot quickbuild
# ---------------------------------------------------------------------------


@api_v1_bp.route("/chatbot-wizard/quickbuild", methods=["POST"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbot_wizard")
def quickbuild():
    """One-call wrapper: URL → crawled, embedded, deployed chatbot.

    Returns immediately with chatbot_id + polling URL; the build runs
    asynchronously via the existing socket pipeline. Use the returned
    ``polling_url`` to wait for ``build_status='ready'``.
    """
    payload = _validate_request(WizardQuickbuildRequest, request.get_json(silent=True))
    user = g.authentik_user
    try:
        result = quickbuild_one_shot(payload, user.username)
    except ApiV1ChatbotNotFound as exc:
        raise NotFoundError(str(exc))
    except ApiV1ChatbotConflict as exc:
        raise ConflictError(str(exc))
    except ApiV1ChatbotError as exc:
        raise ApiValidationError(str(exc))
    return jsonify({"success": True, **result}), 201


# ---------------------------------------------------------------------------
# Multi-step sessions
# ---------------------------------------------------------------------------


@api_v1_bp.route("/chatbot-wizard/sessions", methods=["POST"])
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbot_wizard")
def create_session():
    """Step 1: create the wizard's stub chatbot.

    Returns chatbot_id (= session_id throughout the wizard) and the initial
    ``build_status='draft'``. Caller's next move is the
    ``/sessions/{id}/crawl`` endpoint.
    """
    payload = _validate_request(
        WizardSessionCreateRequest, request.get_json(silent=True),
    )
    user = g.authentik_user
    try:
        result = ChatbotBuilderService.create_wizard_chatbot(
            url=str(payload.crawl_url), username=user.username,
        )
    except Exception as exc:  # noqa: BLE001
        raise ApiValidationError(str(exc))
    if isinstance(result, dict) and result.get("error"):
        raise ApiValidationError(result["error"])

    chatbot_id = (
        (result or {}).get("chatbot", {}).get("id")
        or (result or {}).get("id")
    )
    if not chatbot_id:
        raise ApiValidationError("create_wizard_chatbot returned no id")
    return jsonify({
        "success": True,
        "chatbot_id": chatbot_id,
        "session_id": chatbot_id,
        "build_status": "draft",
    }), 201


@api_v1_bp.route(
    "/chatbot-wizard/sessions/<int:chatbot_id>", methods=["GET"]
)
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbot_wizard")
def get_session(chatbot_id: int):
    _gate(chatbot_id, require_manage=False)
    status = ChatbotBuilderService.get_build_status(chatbot_id)
    return jsonify({"success": True, **(status or {})})


@api_v1_bp.route(
    "/chatbot-wizard/sessions/<int:chatbot_id>", methods=["DELETE"]
)
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbot_wizard")
def cancel_session(chatbot_id: int):
    """Cancel an in-progress build (sets ``build_status='paused'``).

    NOTE: this does NOT delete the chatbot row — the underlying
    ``ChatbotBuilderService.cancel_build`` only flips the status. To
    fully discard a draft, the caller must follow up with
    ``DELETE /api/v1/chatbots/{id}``. We surface the underlying error
    properly: a ``draft`` status (or any other non-cancellable state)
    used to return ``200`` with ``success=false`` — now that's a 409
    Conflict, matching the rest of the v1 surface.
    """
    _gate(chatbot_id, require_manage=True)
    try:
        result = ChatbotBuilderService.cancel_build(chatbot_id)
    except Exception as exc:  # noqa: BLE001
        raise ApiValidationError(str(exc))
    if isinstance(result, dict) and result.get("success") is False:
        # Underlying service returns success=false with an error message
        # for "Cannot cancel build in status: X". Surface as 409 instead
        # of pretending it succeeded.
        raise ConflictError(
            result.get("error") or
            f"Cannot cancel session for chatbot {chatbot_id} in current state"
        )
    return jsonify({"success": True, **(result or {})})


@api_v1_bp.route(
    "/chatbot-wizard/sessions/<int:chatbot_id>/status", methods=["GET"]
)
@api_key_or_token_required
@require_api_scope("chatbot:read")
@handle_api_errors(logger_name="api_v1.chatbot_wizard")
def session_status(chatbot_id: int):
    """Polling endpoint — same shape as GET /sessions/{id}, kept separate so
    the URL reads like a status check rather than a session read."""
    _gate(chatbot_id, require_manage=False)
    status = ChatbotBuilderService.get_build_status(chatbot_id)
    return jsonify({"success": True, **(status or {})})


@api_v1_bp.route(
    "/chatbot-wizard/sessions/<int:chatbot_id>/crawl", methods=["POST"]
)
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbot_wizard")
def session_crawl(chatbot_id: int):
    _gate(chatbot_id, require_manage=True)
    payload = _validate_request(
        WizardCrawlRequest, request.get_json(silent=True),
    )
    cfg = payload.crawler_config
    try:
        result = ChatbotBuilderService.start_crawl(
            chatbot_id=chatbot_id,
            max_pages=cfg.max_pages,
            max_depth=cfg.max_depth,
            use_playwright=cfg.use_playwright,
            use_vision_llm=cfg.use_vision_llm,
            take_screenshots=cfg.take_screenshots,
        )
    except Exception as exc:  # noqa: BLE001
        raise ApiValidationError(str(exc))
    if isinstance(result, dict) and result.get("error"):
        raise ApiValidationError(result["error"])
    return jsonify({"success": True, **(result or {})})


@api_v1_bp.route(
    "/chatbot-wizard/sessions/<int:chatbot_id>/generate-field", methods=["POST"]
)
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbot_wizard")
def session_generate_field(chatbot_id: int):
    """LLM-suggest ``name`` / ``system_prompt`` / ``welcome_message`` etc.

    With ``stream=true`` the response is SSE; otherwise a single JSON.
    """
    _gate(chatbot_id, require_manage=True)
    payload = _validate_request(
        WizardGenerateFieldRequest, request.get_json(silent=True),
    )

    if not payload.stream:
        try:
            result = ChatbotBuilderService.generate_field(
                chatbot_id=chatbot_id,
                field=payload.field,
                context=payload.context,
                force_llm=payload.force_llm,
            )
        except Exception as exc:  # noqa: BLE001
            raise ApiValidationError(str(exc))
        if isinstance(result, dict) and result.get("error"):
            raise ApiValidationError(result["error"])
        return jsonify({"success": True, **(result or {})})

    def event_stream():
        try:
            gen = ChatbotBuilderService.generate_field(
                chatbot_id=chatbot_id,
                field=payload.field,
                context=payload.context,
                force_llm=payload.force_llm,
            )
            # generate_field returns dict in non-stream mode and a generator
            # when the underlying creator decides to stream. Normalize:
            if hasattr(gen, "__iter__") and not isinstance(gen, dict):
                for chunk in gen:
                    yield f"data: {json.dumps(chunk)}\n\n"
            else:
                yield f"data: {json.dumps(gen)}\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.error("[api_v1.chatbot_wizard] generate-field stream failed: %s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    response = Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@api_v1_bp.route(
    "/chatbot-wizard/sessions/<int:chatbot_id>/finalize", methods=["POST"]
)
@api_key_or_token_required
@require_api_scope("chatbot:write")
@handle_api_errors(logger_name="api_v1.chatbot_wizard")
def session_finalize(chatbot_id: int):
    """Step 5 — pin the final config + flip ``build_status='ready'``."""
    _gate(chatbot_id, require_manage=True)
    payload = _validate_request(
        WizardFinalizeRequest, request.get_json(silent=True),
    )
    data = payload.model_dump(exclude_none=True, mode="json")
    # Lift access_spec out — finalize_chatbot doesn't know about it; we
    # apply it via ChatbotAccessService after.
    access = data.pop("access", None)

    try:
        result = ChatbotBuilderService.finalize_chatbot(chatbot_id, data)
    except Exception as exc:  # noqa: BLE001
        raise ApiValidationError(str(exc))
    if isinstance(result, dict) and result.get("error"):
        raise ApiValidationError(result["error"])

    if access:
        try:
            ChatbotAccessService.set_chatbot_access(
                chatbot_id=chatbot_id,
                usernames=access.get("allowed_usernames") or [],
                role_names=access.get("allowed_roles") or [],
                granted_by=g.authentik_user.username,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[api_v1.chatbot_wizard] post-finalize access apply failed for %s: %s",
                chatbot_id, exc,
            )

    return jsonify({"success": True, **(result or {})})
