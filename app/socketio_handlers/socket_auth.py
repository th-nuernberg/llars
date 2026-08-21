"""
Shared authentication + authorization helpers for Socket.IO event handlers.

Socket clients pass their OIDC token as a ``?token=`` query parameter at connect
time (see ``llars-frontend/src/services/socketService.js`` — ``query.token``).
Several realtime handlers (judge sessions, LLM-evaluation progress, generation
jobs) historically joined rooms / returned data with NO authentication and NO
per-resource authorization, so any connected client could subscribe to another
user's live evaluation results, reasoning and progress (information disclosure).

This module centralises:

- ``socket_user(error_event)`` — validate the socket token, resolve the DB user
  and enforce account state (locked/deleted). Emits ``error_event`` and returns
  ``None`` when unauthenticated/forbidden.
- ``socket_authorize(check, *args, error_event=...)`` — run one of the canonical
  ``auth.access_control`` resource checks (the SAME checks the HTTP routes use,
  so socket authz can never diverge from HTTP authz) and translate its
  Forbidden/NotFound exception into a socket error.

Handlers should call ``user = socket_user('<ns>:error'); if user is None: return``
then ``if not socket_authorize(require_x, resource_id, user, error_event='<ns>:error'): return``.
"""

import logging

from flask import request
from flask_socketio import emit

from auth.oidc_validator import validate_token, get_username

logger = logging.getLogger(__name__)


def socket_user(error_event: str = "error"):
    """Return the authenticated DB ``User`` for the current socket, or ``None``.

    Validates the ``?token=`` query JWT, resolves the user and enforces account
    state (deleted/locked). On any failure emits ``error_event`` with a neutral
    message and returns ``None`` — callers must ``return`` immediately.
    """
    token = str(request.args.get("token") or "").strip()
    payload = validate_token(token) if token else None
    if not payload:
        emit(error_event, {"error": "Unauthorized", "message": "Authentifizierung erforderlich"})
        return None

    username = get_username(payload)
    if not username:
        emit(error_event, {"error": "Unauthorized", "message": "Authentifizierung erforderlich"})
        return None

    try:
        from auth.decorators import get_or_create_user, _check_user_account_state
        user = get_or_create_user(username)
        if _check_user_account_state(user) is not None:
            emit(error_event, {"error": "Forbidden", "message": "Konto gesperrt oder gelöscht"})
            return None
        return user
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[SocketAuth] user resolution failed: %s", exc)
        emit(error_event, {"error": "Unauthorized", "message": "Authentifizierung fehlgeschlagen"})
        return None


def socket_authorize(check, *args, error_event: str = "error") -> bool:
    """Run a canonical ``auth.access_control`` resource check for a socket.

    ``check`` is e.g. ``require_scenario_membership`` and ``args`` its positional
    arguments (resource_id, user). Returns ``True`` when access is allowed;
    on Forbidden/NotFound emits ``error_event`` and returns ``False``.
    """
    from decorators.error_handler import ForbiddenError, NotFoundError
    try:
        check(*args)
        return True
    except (ForbiddenError, NotFoundError):
        emit(error_event, {"error": "Forbidden", "message": "Kein Zugriff auf diese Ressource"})
        return False
    except Exception as exc:  # pragma: no cover - defensive: fail closed
        logger.warning("[SocketAuth] authorization check errored, denying: %s", exc)
        emit(error_event, {"error": "Forbidden", "message": "Kein Zugriff auf diese Ressource"})
        return False
