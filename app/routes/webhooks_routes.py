"""
Inbound provider webhooks (currently: Brevo transactional events).

``POST /api/webhooks/brevo``
    Receives Brevo (Sendinblue) transactional-event callbacks and stamps
    ``opened_at`` / ``clicked_at`` onto the matching ``email_log`` row so the
    Admin Mail-Center can show per-recipient open / click engagement.

Why this blueprint is *unauthenticated* (no Authentik / session)
----------------------------------------------------------------
Brevo calls this endpoint server-to-server with no LLARS session, so the
normal auth decorators cannot apply. Instead it is guarded by a **shared
secret token** (env ``BREVO_WEBHOOK_TOKEN``) that must arrive either as the
``?token=`` query param or the ``X-Webhook-Token`` header. Without a
configured token the endpoint refuses every request (fail-closed) so a
forgotten env var can never silently open it to the world.

Robustness contract
-------------------
- Always answer **200 quickly** on an authenticated call (even on no-match)
  so Brevo does not retry-storm us; matching/DB work is best-effort.
- **Idempotent**: re-delivered events for an already-stamped row are no-ops
  (first-occurrence-wins in ``MailCenterService.record_engagement_event``).
- A 401 is only returned for a missing / wrong token.

See app/services/mail/mail_center_service.py (``record_engagement_event``)
and app/services/email_service.py (``_new_message_id`` — how the Message-ID
that these events reference is assigned at send time).
"""

from __future__ import annotations

import hmac
import logging
import os

from flask import Blueprint, jsonify, request

from auth.decorators import public_endpoint
from decorators.error_handler import handle_api_errors

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')

# Brevo event names we act on. ``opened``/``unique_opened`` → opened_at,
# ``click`` → clicked_at. Everything else (delivered, soft_bounce, …) is
# accepted with 200 but ignored.
_OPEN_EVENTS = {'opened', 'unique_opened', 'first_opening'}
_CLICK_EVENTS = {'click', 'clicked'}


def _token_ok() -> bool:
    """Constant-time compare of the request token against ``BREVO_WEBHOOK_TOKEN``.

    Fail-closed: returns False when no token is configured, so a missing env
    var locks the endpoint rather than opening it. Accepts the token from the
    ``X-Webhook-Token`` header or the ``?token=`` query param.
    """
    expected = (os.getenv('BREVO_WEBHOOK_TOKEN') or '').strip()
    if not expected:
        logger.warning("[webhook] BREVO_WEBHOOK_TOKEN not set — rejecting call")
        return False
    provided = (
        request.headers.get('X-Webhook-Token')
        or request.args.get('token')
        or ''
    ).strip()
    if not provided:
        return False
    # hmac.compare_digest avoids leaking the token length/prefix via timing.
    return hmac.compare_digest(provided, expected)


def _extract_events(payload):
    """Normalise Brevo's payload into a flat list of event dicts.

    Brevo posts one event per request for transactional webhooks, but some
    setups batch them under an ``events``/``items`` array — handle both so we
    never silently drop a batched delivery.
    """
    if isinstance(payload, list):
        return [e for e in payload if isinstance(e, dict)]
    if isinstance(payload, dict):
        for key in ('events', 'items'):
            if isinstance(payload.get(key), list):
                return [e for e in payload[key] if isinstance(e, dict)]
        return [payload]
    return []


@webhooks_bp.route('/brevo', methods=['POST'])
@public_endpoint  # intentionally session-less: guarded by the BREVO_WEBHOOK_TOKEN shared secret (see _token_ok)
@handle_api_errors(logger_name='webhooks')
def brevo_webhook():
    """Stamp open/click engagement onto email_log from a Brevo event.

    Token-guarded (see ``_token_ok``); never requires an LLARS session. Returns
    200 for any authenticated call so Brevo does not retry, with a small JSON
    summary of how many events matched a log row.
    """
    if not _token_ok():
        # 401, not 403, so Brevo's webhook tester shows an auth problem clearly.
        return jsonify({'ok': False, 'error': 'invalid or missing token'}), 401

    from services.mail.mail_center_service import MailCenterService

    payload = request.get_json(silent=True)
    events = _extract_events(payload)

    processed = 0
    matched = 0
    for ev in events:
        event_name = (ev.get('event') or ev.get('type') or '').strip().lower()
        if event_name not in _OPEN_EVENTS and event_name not in _CLICK_EVENTS:
            continue  # delivered / bounce / spam / etc. — accepted but ignored
        processed += 1

        # Brevo field names vary slightly by integration; accept the common
        # aliases for the message id, recipient and subject.
        message_id = (
            ev.get('message-id') or ev.get('message_id')
            or ev.get('messageId') or ev.get('X-Mailin-custom')
        )
        recipient = ev.get('email') or ev.get('recipient') or ev.get('to')
        subject = ev.get('subject')
        event_ts = ev.get('date') or ev.get('ts_event') or ev.get('ts')

        result = MailCenterService.record_engagement_event(
            event=event_name,
            provider_message_id=message_id,
            recipient_email=recipient,
            subject=subject,
            event_ts=event_ts,
        )
        if result.get('matched'):
            matched += 1

    # Always 200 on an authenticated call to avoid Brevo retry storms.
    return jsonify({
        'ok': True,
        'received': len(events),
        'processed': processed,
        'matched': matched,
    }), 200
