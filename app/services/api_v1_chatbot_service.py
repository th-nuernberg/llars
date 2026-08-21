"""
Service orchestrator for the public LLARS v1 chatbot API.

Translates validated ``ChatbotCreateRequest`` / ``WizardQuickbuildRequest``
into the underlying DB rows + jobs, by composing existing services:

    ChatbotService            — create row + assign collections + prompt settings
    ChatbotAccessService      — set allowlist / role-share
    ChatbotBuilderService     — wizard lifecycle (crawl → field-gen → finalize)
    ChatService               — chat orchestration with RAG
    ChatbotActivityService    — audit-log every mutation

Same shape as ``services/api_v1_scenario_service.py``: thin transactional
wrapper, custom ApiV1* exception types so route layer can map cleanly to
HTTP statuses without leaking SQLAlchemy / Pydantic internals.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional

from flask import current_app

from db import db
from db.models.chatbot import Chatbot
from schemas.api_v1.chatbot_api import (
    ChatbotCreateRequest,
    ChatbotPatchRequest,
    ChatbotTweakRequest,
    WizardQuickbuildRequest,
)
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.chatbot.chatbot_builder_service import ChatbotBuilderService
from services.chatbot.chatbot_service import ChatbotService
from services.chatbot_activity_service import ChatbotActivityService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions — mirror the scenario surface so routes can `except` cleanly.
# ---------------------------------------------------------------------------


class ApiV1ChatbotError(Exception):
    """Validation / business-rule failure inside the chatbot orchestrator."""


class ApiV1ChatbotNotFound(ApiV1ChatbotError):
    """Referenced entity does not exist."""


class ApiV1ChatbotConflict(ApiV1ChatbotError):
    """Conflict (e.g. unique-constraint violation, name already taken)."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _drop_none(d: Dict[str, Any]) -> Dict[str, Any]:
    """Strip None values — partial-update semantics for PATCH/Tweak.

    Without this, ChatbotService.update_chatbot would clobber existing values
    with None when callers leave a field unset.
    """
    return {k: v for k, v in d.items() if v is not None}


def _payload_to_create_data(
    payload: ChatbotCreateRequest,
) -> Dict[str, Any]:
    """Convert the v1 Pydantic payload into the dict shape ChatbotService.create_chatbot()
    expects. Maps `collections[].collection_id` to the legacy `collection_ids`
    list (priority is the array index, is_primary is positional)."""
    data: Dict[str, Any] = {
        "name": payload.name,
        "display_name": payload.display_name,
        "description": payload.description,
        "icon": payload.icon,
        "color": payload.color,
        "avatar_url": payload.avatar_url,
        "system_prompt": payload.system_prompt,
        "welcome_message": payload.welcome_message,
        "fallback_message": payload.fallback_message,
        "model_name": payload.model_name,
        "temperature": payload.temperature,
        "max_tokens": payload.max_tokens,
        "top_p": payload.top_p,
        "rag_enabled": payload.rag_enabled,
        "rag_retrieval_k": payload.rag_retrieval_k,
        "rag_min_relevance": payload.rag_min_relevance,
        "rag_include_sources": payload.rag_include_sources,
        "rag_reranker_model": payload.rag_reranker_model,
        "rag_use_cross_encoder": payload.rag_use_cross_encoder,
        "max_context_messages": payload.max_context_messages,
        "is_active": payload.is_active,
        "is_public": payload.access.is_public,
        "allowed_roles": payload.access.allowed_roles or None,
    }

    # Order of collections drives priority: index 0 → primary, etc.
    # ChatbotService.create_chatbot uses this convention.
    if payload.collections:
        data["collection_ids"] = [c.collection_id for c in payload.collections]

    if payload.prompt_settings is not None:
        # Pass the dict UNDER `prompt_settings`, not flattened. The legacy
        # `_upsert_prompt_settings` checks `data.get('prompt_settings')`
        # first; flattening into the top-level data was the silent-drop
        # bug — non-flat-key fields (agent_mode, tools_enabled, …) were
        # never seen by the upsert path.
        data["prompt_settings"] = payload.prompt_settings.model_dump(
            exclude_none=True, mode="json"
        )

    return data


# ---------------------------------------------------------------------------
# Public entrypoints
# ---------------------------------------------------------------------------


def create_chatbot_one_shot(
    payload: ChatbotCreateRequest,
    requesting_username: str,
) -> Dict[str, Any]:
    """
    Create a chatbot with optional crawl-trigger in a single transaction.

    Returns the same shape as ``ChatbotService.get_chatbot(id)`` plus an
    optional ``job_id`` when a wizard branch was provided.
    """
    try:
        data = _payload_to_create_data(payload)
        # ChatbotService.create_chatbot already does its own commit, so
        # subsequent steps run in fresh transactions. We accept that vs.
        # rewriting create_chatbot to be atomic — the worst case is a
        # chatbot row without an access list, which is recoverable via
        # the dedicated /access endpoint.
        chatbot_dict = ChatbotService.create_chatbot(data, requesting_username)
    except ValueError as exc:
        msg = str(exc).lower()
        if "already exists" in msg:
            raise ApiV1ChatbotConflict(str(exc))
        raise ApiV1ChatbotError(str(exc))

    chatbot_id = chatbot_dict["id"]

    # Set explicit user-allowlist if any were given (roles are already on
    # the row via allowed_roles JSON; usernames need a separate table).
    if payload.access.allowed_usernames:
        try:
            ChatbotAccessService.set_chatbot_access(
                chatbot_id=chatbot_id,
                usernames=payload.access.allowed_usernames,
                role_names=payload.access.allowed_roles,
                granted_by=requesting_username,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort, chatbot still exists
            logger.warning(
                "[api_v1.chatbots] set_chatbot_access failed for new chatbot %s: %s",
                chatbot_id, exc,
            )

    # Optional async crawl
    job_id: Optional[str] = None
    if payload.wizard is not None:
        try:
            crawl = ChatbotBuilderService.start_crawl(
                chatbot_id=chatbot_id,
                max_pages=payload.wizard.max_pages,
                max_depth=payload.wizard.max_depth,
                use_playwright=payload.wizard.use_playwright,
                use_vision_llm=payload.wizard.use_vision_llm,
                take_screenshots=payload.wizard.take_screenshots,
            )
            job_id = crawl.get("job_id")
        except Exception as exc:  # noqa: BLE001 — chatbot still exists, crawl failed
            logger.error(
                "[api_v1.chatbots] start_crawl failed for new chatbot %s: %s",
                chatbot_id, exc,
            )

    # Audit
    try:
        ChatbotActivityService.log_chatbot_created(
            chatbot_id=chatbot_id,
            chatbot_name=chatbot_dict.get("name"),
            display_name=chatbot_dict.get("display_name"),
            username=requesting_username,
            via_wizard=bool(payload.wizard),
            source_url=payload.wizard.crawl_url if payload.wizard else None,
        )
    except Exception:  # never fail user create on audit
        pass

    chatbot_dict["job_id"] = job_id
    return chatbot_dict


def patch_chatbot(
    chatbot_id: int,
    payload: ChatbotPatchRequest,
    requesting_username: str,
) -> Dict[str, Any]:
    """Forward a partial update to ChatbotService.update_chatbot, drop None fields."""
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        raise ApiV1ChatbotNotFound(f"Chatbot {chatbot_id} not found")

    data = _drop_none(payload.model_dump(exclude_none=True, mode="json"))
    # Keep prompt_settings nested — see create_chatbot_one_shot. Flattening
    # would silently drop fields outside the legacy 5 flat-keys allowlist.

    try:
        result = ChatbotService.update_chatbot(chatbot_id, data, requesting_username)
    except ValueError as exc:
        raise ApiV1ChatbotError(str(exc))
    if result is None:
        raise ApiV1ChatbotNotFound(f"Chatbot {chatbot_id} not found")

    try:
        ChatbotActivityService.log_chatbot_updated(
            chatbot_id=chatbot_id,
            chatbot_name=result.get("name"),
            username=requesting_username,
            changed_fields=list(data.keys()),
        )
    except Exception:
        pass
    return result


def tweak_chatbot(
    chatbot_id: int,
    payload: ChatbotTweakRequest,
    requesting_username: str,
) -> Dict[str, Any]:
    """Tighter PATCH for hot-tuning. Same downstream call, narrower contract."""
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        raise ApiV1ChatbotNotFound(f"Chatbot {chatbot_id} not found")

    data = _drop_none(payload.model_dump(exclude_none=True, mode="json"))
    if not data:
        # No-op — return the unchanged chatbot rather than a 400.
        return ChatbotService.get_chatbot(chatbot_id)

    try:
        result = ChatbotService.update_chatbot(chatbot_id, data, requesting_username)
    except ValueError as exc:
        raise ApiV1ChatbotError(str(exc))
    if result is None:
        raise ApiV1ChatbotNotFound(f"Chatbot {chatbot_id} not found")
    try:
        ChatbotActivityService.log_chatbot_updated(
            chatbot_id=chatbot_id,
            chatbot_name=result.get("name"),
            username=requesting_username,
            changed_fields=list(data.keys()),
        )
    except Exception:
        pass
    return result


def delete_chatbot(chatbot_id: int, requesting_username: str) -> bool:
    """Reuse ChatbotService.delete_chatbot — defaults: don't drop collections
    (they may be shared with other bots). Caller can DELETE them via the
    collection sub-resource separately."""
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        raise ApiV1ChatbotNotFound(f"Chatbot {chatbot_id} not found")

    chatbot_name = chatbot.name
    try:
        ok = ChatbotService.delete_chatbot(chatbot_id, delete_collections=False)
    except ValueError as exc:
        raise ApiV1ChatbotError(str(exc))
    if not ok:
        raise ApiV1ChatbotNotFound(f"Chatbot {chatbot_id} not found")

    try:
        ChatbotActivityService.log_chatbot_deleted(
            chatbot_id=chatbot_id,
            chatbot_name=chatbot_name,
            username=requesting_username,
            with_collections=False,
        )
    except Exception:
        pass
    return True


def _auto_finalize_in_background(
    app,
    chatbot_id: int,
    name_override: Optional[str],
    display_name_override: Optional[str],
    requesting_username: str,
    poll_interval_seconds: float = 3.0,
    timeout_seconds: float = 600.0,
) -> None:
    """Daemon-thread workhorse for quickbuild auto-finalize.

    Polls ``ChatbotBuilderService.get_build_status`` until the chatbot
    reaches ``configuring`` (the LLM-generation-ready state), then runs
    ``generate_field('all')`` + ``finalize_chatbot`` so the caller gets
    a ready chatbot without a second round-trip. Stops on terminal
    states (``ready``, ``error``, ``paused``) or on the overall timeout.

    A daemon thread is appropriate here because: the operation is
    fire-and-forget from the caller's perspective; the chat pipeline
    survives gunicorn-worker restarts (state lives on ``Chatbot.build_status``);
    a missed auto-finalize means the user can still call ``/finalize``
    manually. We never block the originating HTTP response on this thread.
    """
    deadline = time.time() + timeout_seconds
    status = "unknown"  # set below; defined here so the timeout branch can reference it
    with app.app_context():
        while time.time() < deadline:
            # MariaDB defaults to REPEATABLE-READ, which means once a
            # SELECT runs in the daemon's session, every subsequent
            # SELECT inside the same transaction returns the same MVCC
            # snapshot — so the daemon would see its initial
            # `crawling`/existence-True snapshot forever, regardless of
            # what other workers wrote. `expire_all()` only clears the
            # identity map; it does NOT end the transaction. We need a
            # full `rollback()` (read-only "rollback" on a session with
            # no writes is just a transaction-end). After this, the next
            # query opens a fresh snapshot and sees real-world state.
            try:
                db.session.rollback()
            except Exception:
                pass

            # H2: terminate cleanly if the caller deleted the chatbot.
            # MUST come after rollback() so the existence check sees a
            # current snapshot.
            if Chatbot.query.get(chatbot_id) is None:
                logger.info(
                    "[auto-finalize %s] chatbot deleted; aborting daemon",
                    chatbot_id,
                )
                return
            try:
                bot = Chatbot.query.get(chatbot_id)
                status = bot.build_status if bot is not None else "unknown"
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[auto-finalize %s] status read failed: %s",
                    chatbot_id, exc,
                )
                return
            if status == "ready":
                logger.info(
                    "[auto-finalize %s] already ready, nothing to do",
                    chatbot_id,
                )
                return
            if status in ("error", "paused"):
                logger.warning(
                    "[auto-finalize %s] aborted: terminal status=%s",
                    chatbot_id, status,
                )
                return
            if status == "configuring":
                break
            time.sleep(poll_interval_seconds)
        else:
            logger.warning(
                "[auto-finalize %s] timed out waiting for configuring "
                "after %.0fs (last status=%s)",
                chatbot_id, timeout_seconds, status,
            )
            return

        # configuring — drive the field generation + finalize chain
        finalize_data: Dict[str, Any] = {}
        for field in ("name", "display_name", "system_prompt",
                      "icon", "welcome_message"):
            try:
                gen = ChatbotBuilderService.generate_field(
                    chatbot_id=chatbot_id, field=field,
                    context=None, force_llm=True,
                )
                if isinstance(gen, dict) and gen.get(field):
                    finalize_data[field] = gen[field]
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[auto-finalize %s] generate_field(%s) failed: %s",
                    chatbot_id, field, exc,
                )

        # User overrides take precedence over LLM suggestions
        if name_override:
            finalize_data["name"] = name_override
        if display_name_override:
            finalize_data["display_name"] = display_name_override

        try:
            ChatbotBuilderService.finalize_chatbot(chatbot_id, finalize_data)
            logger.info(
                "[auto-finalize %s] finalized via quickbuild auto-flow "
                "(user=%s)", chatbot_id, requesting_username,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "[auto-finalize %s] finalize failed: %s",
                chatbot_id, exc,
            )


def quickbuild_one_shot(
    payload: WizardQuickbuildRequest,
    requesting_username: str,
) -> Dict[str, Any]:
    """
    One-call wrapper for the full wizard chain:
        create_wizard_chatbot(url) → start_crawl(...) → wait for
        ``configuring`` → generate_field('all') → finalize_chatbot

    Returns immediately with the chatbot_id + job_id (so the caller can
    poll ``GET /api/v1/chatbot-wizard/sessions/{id}/status``) and kicks
    off the auto-finalize chain in a daemon thread. On success the bot
    transitions to ``build_status='ready'``; on timeout/error the bot
    stays at ``configuring`` and the caller can call ``/finalize``
    manually with custom values.
    """
    # M1 (race-on-duplicate-URL): the underlying creator does an INSERT
    # with a UNIQUE name derived from the URL. Two parallel quickbuilds
    # for the same URL collide on a SQLAlchemy IntegrityError that used
    # to surface as a raw 500 + leaked SQL traceback. Catch it and turn
    # it into a clean 409 Conflict.
    try:
        create = ChatbotBuilderService.create_wizard_chatbot(
            url=str(payload.crawl.crawl_url),
            username=requesting_username,
        )
    except Exception as exc:  # noqa: BLE001 — wrap-all for race
        # Detect IntegrityError without importing sqlalchemy at module
        # top-level (keeps import cycles tame).
        cls_name = type(exc).__name__
        if cls_name in ("IntegrityError", "FlushError"):
            try:
                db.session.rollback()
            except Exception:
                pass
            raise ApiV1ChatbotConflict(
                "A chatbot is already being built from this URL — "
                "wait for the existing build to complete or pick a new URL."
            )
        raise ApiV1ChatbotError(str(exc))
    if not create.get("success", True) and create.get("error"):
        # Service-level failure surfaces as a dict — also possibly a race
        # message; map "already exists" to Conflict for consistency.
        msg = str(create.get("error") or "")
        if "already exists" in msg.lower():
            raise ApiV1ChatbotConflict(msg)
        raise ApiV1ChatbotError(msg)
    chatbot_id = create.get("chatbot", {}).get("id") or create.get("id")
    if not chatbot_id:
        raise ApiV1ChatbotError(
            "create_wizard_chatbot did not return a chatbot id"
        )

    # If the caller pinned a model, set it now so generate_field can use it
    # for the LLM-backed name/system_prompt suggestions.
    if payload.model_name:
        try:
            ChatbotService.update_chatbot(
                chatbot_id, {"model_name": payload.model_name},
                requesting_username,
            )
        except Exception:
            pass

    # Auth list (best-effort)
    if payload.access.allowed_usernames or payload.access.allowed_roles:
        try:
            ChatbotAccessService.set_chatbot_access(
                chatbot_id=chatbot_id,
                usernames=payload.access.allowed_usernames,
                role_names=payload.access.allowed_roles,
                granted_by=requesting_username,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[api_v1.quickbuild] set_chatbot_access failed for %s: %s",
                chatbot_id, exc,
            )

    crawl = ChatbotBuilderService.start_crawl(
        chatbot_id=chatbot_id,
        max_pages=payload.crawl.max_pages,
        max_depth=payload.crawl.max_depth,
        use_playwright=payload.crawl.use_playwright,
        use_vision_llm=payload.crawl.use_vision_llm,
        take_screenshots=payload.crawl.take_screenshots,
    )
    if isinstance(crawl, dict) and crawl.get("error"):
        raise ApiV1ChatbotError(crawl["error"])
    job_id = (crawl or {}).get("job_id")

    try:
        ChatbotActivityService.log_wizard_started(
            chatbot_id=chatbot_id,
            source_url=str(payload.crawl.crawl_url),
            username=requesting_username,
        )
    except Exception:
        pass

    # Auto-finalize: spawn a daemon thread that watches for the
    # `configuring` state and runs generate-field+finalize so the
    # caller actually gets a ready bot from "quickbuild". We capture
    # the Flask app object explicitly because daemon threads start
    # with no Flask context.
    try:
        app = current_app._get_current_object()  # type: ignore[attr-defined]
        threading.Thread(
            target=_auto_finalize_in_background,
            args=(app, chatbot_id, payload.name_override,
                  payload.display_name_override, requesting_username),
            daemon=True,
            name=f"quickbuild-auto-finalize-{chatbot_id}",
        ).start()
        auto_finalize_started = True
    except Exception as exc:  # noqa: BLE001 — best effort
        logger.warning(
            "[api_v1.quickbuild] could not spawn auto-finalize thread for %s: %s",
            chatbot_id, exc,
        )
        auto_finalize_started = False

    return {
        "chatbot_id": chatbot_id,
        "session_id": chatbot_id,  # the wizard uses chatbot_id as session_id
        "build_status": "crawling",
        "job_id": job_id,
        "polling_url": f"/api/v1/chatbot-wizard/sessions/{chatbot_id}/status",
        "auto_finalize": auto_finalize_started,
    }
