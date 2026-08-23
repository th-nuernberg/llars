"""
Minimal SMTP-based email service for transactional mails (registration
confirmations, etc.).

Design choices
--------------
- Pure stdlib (``smtplib``, ``email.message``) — no new dependencies and
  no Flask-Mail. The send volume is small (one email per new user, plus
  occasional admin notifications) and latency is fire-and-forget.
- Configuration is read from the environment so a deployment without
  SMTP credentials gracefully no-ops with a warning instead of raising.
  A registration must never fail because the mail server is misconfigured.
- Sent in a daemon thread so the HTTP response is never blocked on SMTP
  handshake / TLS negotiation latency.

Environment variables
---------------------
SMTP_HOST            — required to send; e.g. ``smtp.gmail.com``
SMTP_PORT            — default ``587`` (STARTTLS)
SMTP_USERNAME        — optional auth user
SMTP_PASSWORD        — optional auth password
SMTP_USE_TLS         — ``true`` (default) wraps STARTTLS; ``false`` for plaintext
SMTP_USE_SSL         — ``true`` for SMTPS (port 465); overrides USE_TLS
SMTP_FROM            — sender envelope/header. Defaults to the username
                        if unset; if both are unset, sending is disabled.
SMTP_FROM_NAME       — display name (defaults to "LLARS")
SMTP_REPLY_TO        — optional Reply-To header
LLARS_PUBLIC_URL     — used when building login links in mail bodies;
                        falls back to a generic placeholder
"""

from __future__ import annotations

import logging
import os
import re
import smtplib
import threading
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _new_message_id() -> str:
    """Generate a unique RFC 5322 ``Message-ID`` for an outbound mail.

    We mint the id ourselves (rather than letting the MTA assign one) so the
    *exact* value can be stored in ``email_log.provider_message_id`` BEFORE the
    async send completes. Brevo references transactional events by this same
    ``Message-ID`` header, so a self-assigned id gives the webhook a
    deterministic match — no recipient+subject heuristic needed in the common
    case. See app/routes/webhooks_routes.py.
    """
    domain = (os.getenv("MAIL_MESSAGE_ID_DOMAIN")
              or os.getenv("SMTP_FROM", "").split("@")[-1]
              or "llars.e-beratungsinstitut.de")
    return make_msgid(domain=domain or "llars.e-beratungsinstitut.de")


def _is_configured() -> bool:
    """SMTP send is enabled when at least HOST + FROM (or HOST + USERNAME) is set."""
    if not os.getenv("SMTP_HOST"):
        return False
    return bool(os.getenv("SMTP_FROM") or os.getenv("SMTP_USERNAME"))


def _resolve_from(sender: Optional[str] = None) -> str:
    """Return the effective From: address, or empty string if not set.

    An explicit ``sender`` override (e.g. a per-mail-type address) wins over
    the ``SMTP_FROM`` environment default; the display-name formatting is
    applied identically in both cases.
    """
    sender = sender or os.getenv("SMTP_FROM") or os.getenv("SMTP_USERNAME") or ""
    name = os.getenv("SMTP_FROM_NAME", "LLARS")
    if sender and name and "<" not in sender:
        return f"{name} <{sender}>"
    return sender


def _from_notify() -> str:
    """From: for welcome / invitation mails (read at call time)."""
    return os.getenv("MAIL_FROM_NOTIFY", "team@llars.e-beratungsinstitut.de")


def _from_noreply() -> str:
    """From: for password-reset mails (read at call time)."""
    return os.getenv("MAIL_FROM_NOREPLY", "noreply@llars.e-beratungsinstitut.de")


def _reply_to_addr() -> str:
    """Reply-To: for all transactional mails (read at call time)."""
    return os.getenv("MAIL_REPLY_TO", "llars@e-beratungsinstitut.de")


def _send_sync(to_email: str, subject: str, body_text: str,
               body_html: Optional[str] = None,
               from_addr: Optional[str] = None,
               reply_to: Optional[str] = None,
               message_id: Optional[str] = None) -> bool:
    """Blocking send. Returns True on success, False on any error.

    ``message_id`` (optional) is set as the outgoing ``Message-ID`` header so a
    later Brevo open/click webhook can be matched to this exact send. See
    ``_new_message_id`` and app/routes/webhooks_routes.py.
    """
    if not _is_configured():
        logger.info(
            "[email] SMTP not configured (SMTP_HOST/SMTP_FROM); "
            "skipping send to %s", to_email
        )
        return False

    host = os.getenv("SMTP_HOST")
    port_raw = os.getenv("SMTP_PORT", "587")
    try:
        port = int(port_raw)
    except ValueError:
        logger.error("[email] invalid SMTP_PORT=%r — aborting send", port_raw)
        return False

    use_ssl = os.getenv("SMTP_USE_SSL", "false").strip().lower() in ("1", "true", "yes")
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes")
    user = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_addr = _resolve_from(from_addr)
    reply_to = reply_to or os.getenv("SMTP_REPLY_TO")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    if reply_to:
        msg["Reply-To"] = reply_to
    if message_id:
        # Self-assigned so it matches the value stored in email_log; Brevo
        # echoes this Message-ID back in its open/click webhook events.
        msg["Message-ID"] = message_id
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10) as smtp:
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as smtp:
                if use_tls:
                    smtp.starttls()
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
        logger.info("[email] sent %r → %s", subject, to_email)
        return True
    except Exception as exc:  # noqa: BLE001 — wrap-all for fire-and-forget
        logger.warning("[email] send to %s failed: %s", to_email, exc)
        return False


def send_async(to_email: str, subject: str, body_text: str,
               body_html: Optional[str] = None,
               from_addr: Optional[str] = None,
               reply_to: Optional[str] = None,
               message_id: Optional[str] = None) -> None:
    """Fire-and-forget wrapper. Never raises, never blocks the caller."""
    if not to_email:
        return
    t = threading.Thread(
        target=_send_sync,
        args=(to_email, subject, body_text, body_html, from_addr, reply_to, message_id),
        daemon=True,
        name=f"smtp-send-{to_email[:30]}",
    )
    t.start()


# ---------------------------------------------------------------------------
# Central mail logging — the "everything comes together" instrumentation
# ---------------------------------------------------------------------------
#
# Every outbound mail (automatic OR manual) flows through ``record_and_send``
# so exactly one ``email_log`` row is written per send attempt. The call site
# only passes ``mail_type`` + light context; the privacy rules
# (no full bodies, never a reset token) are enforced by the *callers* that
# decide what — if anything — to put into ``meta``. See app/db/models/email_log.py.


def _write_email_log(*, mail_type: str, recipient_email: str, subject: str,
                     status: str, error: Optional[str] = None,
                     recipient_user_id: Optional[int] = None,
                     triggered_by_user_id: Optional[int] = None,
                     referral_link_id: Optional[int] = None,
                     scenario_id: Optional[int] = None,
                     meta: Optional[Dict[str, Any]] = None,
                     provider_message_id: Optional[str] = None) -> Optional[int]:
    """Persist one ``email_log`` row. Best-effort — never raises.

    Returns the new row id (so the invitation flow can link it), or ``None`` if
    logging failed (e.g. no app context in a unit test). A logging failure must
    never break the actual send, so all errors are swallowed with a warning.

    Runs its own short-lived DB session/commit because the most common caller
    is a daemon SMTP thread with no request-scoped session.
    """
    try:
        from db.database import db
        from db.models.email_log import EmailLog

        row = EmailLog(
            mail_type=mail_type,
            recipient_email=(recipient_email or '')[:320],
            recipient_user_id=recipient_user_id,
            subject=(subject or '')[:512],
            status=status,
            error=(error or None),
            triggered_by_user_id=triggered_by_user_id,
            referral_link_id=referral_link_id,
            scenario_id=scenario_id,
            meta_json=meta or None,
            provider_message_id=(provider_message_id or None),
        )
        db.session.add(row)
        db.session.commit()
        return row.id
    except Exception as exc:  # noqa: BLE001 — logging must never break sending
        logger.warning("[email] failed to write email_log row: %s", exc)
        try:
            from db.database import db
            db.session.rollback()
        except Exception:
            pass
        return None


def record_and_send(*, mail_type: str, to_email: str, subject: str,
                    body_text: str, body_html: Optional[str] = None,
                    from_addr: Optional[str] = None,
                    reply_to: Optional[str] = None,
                    recipient_user_id: Optional[int] = None,
                    triggered_by_user_id: Optional[int] = None,
                    referral_link_id: Optional[int] = None,
                    scenario_id: Optional[int] = None,
                    meta: Optional[Dict[str, Any]] = None,
                    async_send: bool = True) -> Dict[str, Any]:
    """Send a mail AND write its ``email_log`` row. The single audit choke point.

    Behaviour:
    - No real inbox (empty / ``@noemail.invalid``) → status ``skipped``, no send.
    - ``async_send=True`` (default): send fire-and-forget in a daemon thread and
      optimistically log status ``sent`` (matches the existing transactional
      mails, which already never blocked on SMTP). A subsequent SMTP failure is
      logged by ``_send_sync`` to the application log.
    - ``async_send=False``: block on the send and record the true ``sent`` /
      ``failed`` outcome — used for small manual lists where the admin wants a
      truthful per-recipient result in the UI.

    Returns ``{'status': ..., 'log_id': ...}``.
    """
    # Mint the Message-ID up front so the SAME value is both set on the
    # outgoing mail AND persisted in email_log — letting the Brevo open/click
    # webhook match the event deterministically. See _new_message_id().
    message_id = _new_message_id()

    log_kwargs = dict(
        mail_type=mail_type, recipient_email=to_email, subject=subject,
        recipient_user_id=recipient_user_id,
        triggered_by_user_id=triggered_by_user_id,
        referral_link_id=referral_link_id, scenario_id=scenario_id, meta=meta,
    )

    if not _is_real_inbox(to_email):
        # Nothing sent → no provider_message_id to store.
        log_id = _write_email_log(status='skipped', error='no real inbox', **log_kwargs)
        return {'status': 'skipped', 'log_id': log_id}

    if async_send:
        send_async(to_email, subject, body_text, body_html, from_addr, reply_to,
                   message_id=message_id)
        log_id = _write_email_log(status='sent', provider_message_id=message_id,
                                  **log_kwargs)
        return {'status': 'sent', 'log_id': log_id}

    ok = _send_sync(to_email, subject, body_text, body_html, from_addr, reply_to,
                    message_id=message_id)
    status = 'sent' if ok else 'failed'
    log_id = _write_email_log(
        status=status,
        error=None if ok else 'SMTP send failed (see application log)',
        # Only store the id when the send actually went out, so the webhook
        # never matches against a mail that was never delivered.
        provider_message_id=message_id if ok else None,
        **log_kwargs,
    )
    return {'status': status, 'log_id': log_id}


# ---------------------------------------------------------------------------
# Specific transactional templates
# ---------------------------------------------------------------------------


def _public_url() -> str:
    return os.getenv("LLARS_PUBLIC_URL", "https://llars.example.org").rstrip("/")


def _is_real_inbox(email: str) -> bool:
    """True only for an address we can actually deliver to.

    Synthetic ``@noemail.invalid`` addresses (minted for email-less referral
    signups, RFC 6761 §6.4 — guaranteed non-resolvable) and empty values are
    never deliverable, so we skip them rather than bouncing into the void.
    """
    addr = (email or "").strip().lower()
    return bool(addr) and not addr.endswith("@noemail.invalid")


def _html_escape(text: str) -> str:
    """Minimal HTML escaping for values interpolated into the mail body."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_welcome(
    *,
    username: str,
    scenario_id: Optional[int] = None,
    referral_label: Optional[str] = None,
) -> Dict[str, str]:
    """Build the branded post-registration welcome mail (subject + text + html).

    Pure render — NO send. Shared by ``send_registration_confirmation`` and the
    admin ``/templates`` preview endpoint so the preview is byte-identical to
    what gets sent. All body-building lives here; the send function only adds
    the recipient address and the ``email_log`` instrumentation.

    Puts the username prominently in BOTH subject and body (people forget which
    username they picked), links to the study (the auto-enrolled scenario if
    present, otherwise login), and carries the "Kann KI Beratung?" /
    KI-Zentrum Bayern project framing. German only, signed by the study lead.
    """
    base = _public_url()
    study_link = (
        f"{base}/scenarios/{scenario_id}/evaluate" if scenario_id else f"{base}/login"
    )
    # New green-wave logo, served from the frontend public/ root.
    logo_url = f"{base}/android-chrome-192x192.png"

    # NOTE: referral_label is the per-link recruiting-source tag (e.g. "Institut
    # für E-Beratung"), NOT the study. The study is "Kann KI Beratung?" (named in
    # the body). We therefore do NOT surface the link label to participants.
    subject = f"Willkommen bei „Kann KI Beratung?\" — {username}"

    body_text = (
        "Hallo,\n\n"
        "schön, dass Sie beim Forschungsprojekt „Kann KI Beratung?\" des "
        "KI-Zentrums Bayern (TH Nürnberg) mitmachen.\n"
        "Ihre Registrierung war erfolgreich.\n\n"
        f"Benutzername: {username}\n"
        f"\nDirekter Link zur Studie: {study_link}\n\n"
        "In der Studie vergleichen Sie jeweils zwei anonymisierte "
        "Beratungs-Antworten und sagen uns, welche Sie besser finden. "
        "Damit helfen Sie einzuschätzen, wo KI eine Beratung sinnvoll "
        "unterstützen kann.\n\n"
        "Falls Sie sich erneut anmelden möchten, brauchen Sie den Benutzernamen "
        "oben und das Passwort, das Sie bei der Registrierung gesetzt haben.\n\n"
        "Vielen Dank, dass Sie teilnehmen.\n\n"
        "Fragen? Schreiben Sie uns an llars@e-beratungsinstitut.de.\n\n"
        "Mit kollegialen Grüßen\n\n"
        "Philipp Steigerwald\n"
        "KI-Zentrum Bayern\n"
    )

    safe_user = _html_escape(username)

    body_html = f"""\
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:28px 24px;">
            <img src="{logo_url}" width="64" height="64" alt="Kann KI Beratung?" style="display:block;border:0;margin-bottom:10px;border-radius:12px;">
            <div style="font-size:20px;font-weight:600;color:#ffffff;">Kann KI Beratung?</div>
            <div style="font-size:13px;color:#ffffff;opacity:0.9;margin-top:2px;">KI-Zentrum Bayern · TH Nürnberg</div>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 28px 8px;">
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">Hallo,</p>
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">schön, dass Sie beim Forschungsprojekt <strong>„Kann KI Beratung?"</strong> des KI-Zentrums Bayern (TH Nürnberg) mitmachen. Ihre Registrierung war erfolgreich.</p>
            <div style="background:#f7f9f4;border-radius:10px 3px 10px 3px;padding:14px 18px;margin:0 0 18px;line-height:1.4;">
              <div style="font-size:12px;color:#8a9580;margin:0 0 4px;">Ihr Benutzername</div>
              <div style="font-size:19px;font-weight:600;color:#2c3320;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;word-break:break-all;">{safe_user}</div>
            </div>
            <p style="margin:0 0 18px;font-size:15px;line-height:1.55;">In der Studie vergleichen Sie jeweils zwei anonymisierte Beratungs-Antworten und sagen uns, welche Sie besser finden. Damit helfen Sie einzuschätzen, wo KI eine Beratung sinnvoll unterstützen kann.</p>
            <p style="margin:0 0 24px;text-align:center;">
              <a href="{study_link}" style="display:inline-block;background:#b0ca97;color:#2c3320;text-decoration:none;font-weight:600;font-size:15px;padding:12px 28px;border-radius:10px 3px 10px 3px;">Zur Studie</a>
            </p>
            <p style="margin:0 0 14px;font-size:13px;line-height:1.5;color:#5a6650;">Falls Sie sich erneut anmelden möchten, brauchen Sie den Benutzernamen oben und das Passwort, das Sie bei der Registrierung gesetzt haben.</p>
            <p style="margin:0 0 14px;font-size:13px;line-height:1.5;color:#5a6650;">Fragen? Schreiben Sie uns an <a href="mailto:llars@e-beratungsinstitut.de" style="color:#3f7d6b;">llars@e-beratungsinstitut.de</a>.</p>
            <p style="margin:18px 0 0;font-size:14px;line-height:1.55;color:#2c3320;">Mit kollegialen Grüßen</p>
            <p style="margin:14px 0 0;font-size:14px;line-height:1.55;color:#2c3320;">Philipp Steigerwald<br>KI-Zentrum Bayern</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    return {'subject': subject, 'body_text': body_text, 'body_html': body_html}


def send_registration_confirmation(
    *,
    username: str,
    email: str,
    scenario_id: Optional[int] = None,
    referral_label: Optional[str] = None,
    referral_link_id: Optional[int] = None,
    recipient_user_id: Optional[int] = None,
) -> None:
    """Send the branded post-registration welcome email.

    Thin send wrapper over ``render_welcome`` (which owns the body-building).
    Every attempt — including the ``skipped`` case for email-less signups —
    writes one ``email_log`` row (mail_type ``welcome``) via ``record_and_send``,
    so the Mail-Center shows who received a welcome mail.
    """
    rendered = render_welcome(
        username=username,
        scenario_id=scenario_id,
        referral_label=referral_label,
    )
    record_and_send(
        mail_type='welcome',
        to_email=email,
        subject=rendered['subject'],
        body_text=rendered['body_text'],
        body_html=rendered['body_html'],
        from_addr=_from_notify(),
        reply_to=_reply_to_addr(),
        recipient_user_id=recipient_user_id,
        referral_link_id=referral_link_id,
        scenario_id=scenario_id,
        # Welcome mails carry no privacy-sensitive token; a short preview is
        # safe and useful for recognising the mail in the log.
        meta={'username': username} if username else None,
    )


# Placeholders available in standard/custom welcome templates. Filled with
# safe fallbacks so a half-configured link never produces "{study}" literals.
WELCOME_PLACEHOLDERS = ("{name}", "{username}", "{study}", "{study_link}", "{link_label}")


def _fill_welcome_placeholders(template: str, mapping: Dict[str, str]) -> str:
    """Replace {name}/{username}/{study}/{study_link}/{link_label} verbatim.

    Plain str.replace (NOT str.format): custom templates are user-authored
    free text and may contain arbitrary braces.
    """
    out = template
    for key, value in mapping.items():
        out = out.replace('{' + key + '}', value or '')
    return out


def _welcome_shell_html(*, header_title: str, body_inner_html: str, logo_alt: str = "LLARS") -> str:
    """Branded HTML shell shared by the standard + custom welcome mails."""
    logo_url = f"{_public_url()}/android-chrome-192x192.png"
    return f"""\
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:28px 24px;">
            <img src="{logo_url}" width="64" height="64" alt="{_html_escape(logo_alt)}" style="display:block;border:0;margin-bottom:10px;border-radius:12px;">
            <div style="font-size:20px;font-weight:600;color:#ffffff;">{_html_escape(header_title)}</div>
            <div style="font-size:13px;color:#ffffff;opacity:0.9;margin-top:2px;">LLARS · KI-Zentrum Bayern · TH Nürnberg</div>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 28px 20px;">
{body_inner_html}
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def render_standard_welcome(
    *,
    username: str,
    display_name: Optional[str] = None,
    study_name: Optional[str] = None,
    scenario_id: Optional[int] = None,
) -> Dict[str, str]:
    """Generic, study-agnostic welcome mail (the DEFAULT for referral links).

    Auto-fills the participant name, username and the study they actually
    joined (target scenario name resp. link label) — replaces the historical
    behavior where the "Kann KI Beratung?" study mail went out for EVERY link.
    Pure render — no send.
    """
    base = _public_url()
    study_link = (
        f"{base}/scenarios/{scenario_id}/evaluate" if scenario_id else f"{base}/login"
    )
    study = (study_name or '').strip()
    greeting_name = (display_name or '').strip() or username

    subject = (
        f"Willkommen bei „{study}“ — {username}" if study
        else f"Willkommen bei LLARS — {username}"
    )
    study_line = (
        f"schön, dass Sie bei „{study}“ mitmachen. Ihre Registrierung war erfolgreich."
        if study else
        "schön, dass Sie dabei sind. Ihre Registrierung war erfolgreich."
    )

    body_text = (
        f"Hallo {greeting_name},\n\n"
        f"{study_line}\n\n"
        f"Benutzername: {username}\n"
        f"\nDirekter Link: {study_link}\n\n"
        "Falls Sie sich erneut anmelden möchten, brauchen Sie den Benutzernamen "
        "oben und das Passwort, das Sie bei der Registrierung gesetzt haben.\n\n"
        "Fragen? Schreiben Sie uns an llars@e-beratungsinstitut.de.\n\n"
        "Viele Grüße\n"
        "Das LLARS-Team\n"
        "KI-Zentrum Bayern · TH Nürnberg\n"
    )

    inner = f"""\
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">Hallo {_html_escape(greeting_name)},</p>
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">{_html_escape(study_line)}</p>
            <div style="background:#f7f9f4;border-radius:10px 3px 10px 3px;padding:14px 18px;margin:0 0 18px;line-height:1.4;">
              <div style="font-size:12px;color:#8a9580;margin:0 0 4px;">Ihr Benutzername</div>
              <div style="font-size:19px;font-weight:600;color:#2c3320;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;word-break:break-all;">{_html_escape(username)}</div>
            </div>
            <p style="margin:0 0 24px;text-align:center;">
              <a href="{study_link}" style="display:inline-block;background:#b0ca97;color:#2c3320;text-decoration:none;font-weight:600;font-size:15px;padding:12px 28px;border-radius:10px 3px 10px 3px;">{_html_escape('Zur Studie' if study else 'Zu LLARS')}</a>
            </p>
            <p style="margin:0 0 14px;font-size:13px;line-height:1.5;color:#5a6650;">Falls Sie sich erneut anmelden möchten, brauchen Sie den Benutzernamen oben und das Passwort, das Sie bei der Registrierung gesetzt haben.</p>
            <p style="margin:0 0 14px;font-size:13px;line-height:1.5;color:#5a6650;">Fragen? Schreiben Sie uns an <a href="mailto:llars@e-beratungsinstitut.de" style="color:#3f7d6b;">llars@e-beratungsinstitut.de</a>.</p>
            <p style="margin:18px 0 0;font-size:14px;line-height:1.55;color:#2c3320;">Viele Grüße<br>Das LLARS-Team<br>KI-Zentrum Bayern · TH Nürnberg</p>"""

    body_html = _welcome_shell_html(
        header_title=study or 'Willkommen bei LLARS',
        body_inner_html=inner,
    )
    return {'subject': subject, 'body_text': body_text, 'body_html': body_html}


def render_custom_welcome(
    *,
    subject_template: str,
    body_template: str,
    mapping: Dict[str, str],
    header_title: str,
) -> Dict[str, str]:
    """Per-link custom welcome: fill {placeholders}, wrap body in the branded
    shell (plain text -> escaped + <br>). Pure render — no send."""
    subject = _fill_welcome_placeholders(subject_template, mapping).strip()
    body_text = _fill_welcome_placeholders(body_template, mapping)
    inner = (
        '            <p style="margin:0;font-size:15px;line-height:1.6;">'
        + _html_escape(body_text).replace('\n', '<br>')
        + '</p>'
    )
    body_html = _welcome_shell_html(header_title=header_title, body_inner_html=inner)
    return {'subject': subject, 'body_text': body_text, 'body_html': body_html}


def send_link_welcome(
    *,
    link,
    username: str,
    email: str,
    scenario_id: Optional[int] = None,
    display_name: Optional[str] = None,
    recipient_user_id: Optional[int] = None,
) -> None:
    """Route + send the welcome mail for a referral sign-up/enrollment.

    Routing by link.welcome_template:
      'custom'  -> welcome_subject/welcome_body with {placeholders}
      'kkb'     -> legacy "Kann KI Beratung?" study mail (render_welcome)
      otherwise -> standard generic welcome (render_standard_welcome)
    The ijcai/demo-* slug specials are handled by the CALLERS (they need
    extra inputs like language or magic-login links).
    """
    study_name = None
    if scenario_id:
        try:
            from db.models import RatingScenarios
            scenario = RatingScenarios.query.get(scenario_id)
            study_name = scenario.scenario_name if scenario else None
        except Exception:
            study_name = None
    # Fallback: the link label often carries the study/recruiting context.
    study_name = study_name or (getattr(link, 'label', None) or None)

    template = (getattr(link, 'welcome_template', None) or 'standard').lower()
    base = _public_url()
    study_link = (
        f"{base}/scenarios/{scenario_id}/evaluate" if scenario_id else f"{base}/login"
    )

    if template == 'custom' and (getattr(link, 'welcome_body', None) or '').strip():
        mapping = {
            'name': (display_name or '').strip() or username,
            'username': username,
            'study': study_name or 'LLARS',
            'study_link': study_link,
            'link_label': getattr(link, 'label', None) or '',
        }
        rendered = render_custom_welcome(
            subject_template=(link.welcome_subject or 'Willkommen — {username}'),
            body_template=link.welcome_body,
            mapping=mapping,
            header_title=study_name or 'Willkommen bei LLARS',
        )
        template_used = 'custom'
    elif template == 'kkb':
        rendered = render_welcome(
            username=username,
            scenario_id=scenario_id,
            referral_label=getattr(link, 'label', None),
        )
        template_used = 'kkb'
    else:
        rendered = render_standard_welcome(
            username=username,
            display_name=display_name,
            study_name=study_name,
            scenario_id=scenario_id,
        )
        template_used = 'standard'

    record_and_send(
        mail_type='welcome',
        to_email=email,
        subject=rendered['subject'],
        body_text=rendered['body_text'],
        body_html=rendered['body_html'],
        from_addr=_from_notify(),
        reply_to=_reply_to_addr(),
        recipient_user_id=recipient_user_id,
        referral_link_id=getattr(link, 'id', None),
        scenario_id=scenario_id,
        meta={'username': username, 'welcome_template': template_used},
    )


def render_ijcai_welcome(*, username: str, auto_login_url: Optional[str] = None) -> Dict[str, str]:
    """Build the ENGLISH welcome mail for the IJCAI 2026 demo link.

    Distinct from render_welcome (the German "Kann KI Beratung?" study mail):
    the IJCAI link is a product demo for an international audience, so this mail
    is in English and frames the platform, not the counselling study.

    CONTENT CONTRACT: the "what's in your account" list must mirror what the
    /join/ijcai link actually provisions — 7 shared scenarios (one per
    evaluation type) from ``scripts/seed_ijcai_demo.py`` plus the cloned prompts
    and shared generation jobs from the link's ``provision_json``. If that
    provisioning changes, update this copy (text AND html) with it.

    When ``auto_login_url`` is given (a re-usable magic-login link, valid 7
    days — see ``_make_magic_login_url``), the CTA logs
    the user straight in without a password; otherwise it links to the hub.
    Pure render — no send. Shares the branded shell + logo.
    """
    base = _public_url()
    hub_link = f"{base}/evaluation"
    cta_link = auto_login_url or hub_link
    logo_url = f"{base}/android-chrome-192x192.png"
    safe_user = _html_escape(username)

    subject = "Your LLARS demo is ready — one-click sign-in (valid 7 days)"

    body_text = (
        "Hello,\n\n"
        "thanks for trying LLARS, the LLM-Assisted Research System, at IJCAI 2026.\n"
        "Your personal demo account is ready.\n\n"
        f"Username: {username}\n\n"
        "What's already in your account:\n\n"
        "1) Seven shared evaluation scenarios — one per evaluation type "
        "(rating, ranking, mail rating, comparison, communication comparison, "
        "authenticity and labeling), each with 20 English counselling items. "
        "Everyone who joins rates the same items, so a scenario's analysis in "
        "the Scenario Manager shows live, aggregated inter-rater agreement "
        "across all participants.\n"
        "2) Two ready-made prompt templates in Prompt Engineering — your own "
        "editable copies, not read-only samples.\n"
        "3) Two completed batch generations that run those prompts over the "
        "same counselling cases with Mistral Small 3.2 (24B) and Mistral "
        "Medium 3.5 (128B), so you can read both models side by side.\n"
        "4) Both models unlocked for your own runs — edit a prompt, start a "
        "generation and compare the output yourself.\n\n"
        f"Open your demo (one-click sign-in): {cta_link}\n\n"
        "This is your personal one-click sign-in link — no password needed, and "
        "it stays valid for 7 days.\n\n"
        "If you'd like to use LLARS in your own research, we'd be happy to support "
        "you and explore how we might collaborate — reach out anytime at "
        "llars@e-beratungsinstitut.de.\n\n"
        "Enjoy exploring!\n\n"
        "The LLARS team\n"
        "KI-Zentrum Bayern · TH Nürnberg\n"
    )

    body_html = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:28px 24px;">
            <img src="{logo_url}" width="64" height="64" alt="LLARS" style="display:block;border:0;margin-bottom:10px;border-radius:12px;">
            <div style="font-size:20px;font-weight:600;color:#ffffff;">LLARS — Demo</div>
            <div style="font-size:13px;color:#ffffff;opacity:0.9;margin-top:2px;">IJCAI 2026 · KI-Zentrum Bayern</div>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 28px 8px;">
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">Hello,</p>
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">thanks for trying <strong>LLARS</strong> (the LLM-Assisted Research System) at IJCAI 2026. Your personal demo account is ready.</p>
            <div style="background:#f7f9f4;border-radius:10px 3px 10px 3px;padding:14px 18px;margin:0 0 18px;line-height:1.4;">
              <div style="font-size:12px;color:#8a9580;margin:0 0 4px;">Your username</div>
              <div style="font-size:19px;font-weight:600;color:#2c3320;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;word-break:break-all;">{safe_user}</div>
            </div>
            <p style="margin:0 0 10px;font-size:15px;line-height:1.55;">What's already in your account:</p>
            <ul style="margin:0 0 18px;padding-left:20px;font-size:15px;line-height:1.55;">
              <li style="margin:0 0 8px;"><strong>Seven shared evaluation scenarios</strong> — one per evaluation type (rating, ranking, mail rating, comparison, communication comparison, authenticity and labeling), each with 20 English counselling items. Everyone who joins rates the same items, so a scenario's analysis shows live, aggregated inter-rater agreement across all participants.</li>
              <li style="margin:0 0 8px;"><strong>Two ready-made prompt templates</strong> in Prompt Engineering — your own editable copies, not read-only samples.</li>
              <li style="margin:0 0 8px;"><strong>Two completed batch generations</strong> that run those prompts over the same counselling cases with Mistral Small 3.2 (24B) and Mistral Medium 3.5 (128B), so you can read both models side by side.</li>
              <li style="margin:0;"><strong>Both models unlocked for your own runs</strong> — edit a prompt, start a generation and compare the output yourself.</li>
            </ul>
            <p style="margin:0 0 10px;text-align:center;">
              <a href="{cta_link}" style="display:inline-block;background:#5d7a4a;color:#ffffff;text-decoration:none;font-size:15px;font-weight:600;padding:12px 26px;border-radius:14px 4px 14px 4px;">Open my demo — sign in →</a>
            </p>
            <p style="margin:0 0 18px;font-size:13px;line-height:1.5;color:#6b7563;text-align:center;">This is your personal one-click sign-in link — no password needed, and it stays valid for 7 days.</p>
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">If you'd like to use LLARS in your own research, we'd be happy to support you and explore how we might collaborate — reach out anytime at <a href="mailto:llars@e-beratungsinstitut.de" style="color:#5d7a4a;font-weight:600;text-decoration:none;">llars@e-beratungsinstitut.de</a>.</p>
            <p style="margin:0 0 4px;font-size:15px;line-height:1.55;">Enjoy exploring!</p>
            <p style="margin:0 0 18px;font-size:15px;line-height:1.55;">The LLARS team<br>KI-Zentrum Bayern · TH Nürnberg</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return {'subject': subject, 'body_text': body_text, 'body_html': body_html}


def _make_magic_login_url(username: str, ttl_hours: int = 168) -> Optional[str]:
    """Mint a magic-login token for ``username`` and return the public
    /auto-login/<token> URL (passwordless sign-in). 7-day TTL by default — long
    enough that a conference attendee can use the welcome-mail link later.

    The link is deliberately MULTI-USE inside that window (product decision):
    a participant scans the QR once, gets this mail and clicks the same link
    again whenever they come back. ``POST /auth/magic-login`` therefore does
    not consume it; the bounds are the TTL, hashing at rest and being
    superseded by the next mint (below). See the PURPOSE_* block in
    db/models/password_reset.py.

    Returns None on any failure (the mail still sends, just without the link).
    """
    try:
        from datetime import datetime
        from db.models.password_reset import PasswordResetToken, PURPOSE_MAGIC
        from db.database import db as _db

        # Build the row first (pure Python) so a failure here cannot leave the
        # invalidation below half-applied in the caller's open transaction.
        token = PasswordResetToken.create_for(
            username, ttl_hours=ttl_hours, purpose=PURPOSE_MAGIC
        )

        # Retire any still-valid older MAGIC links for this account so only the
        # newest mailed link works. Mirrors request_password_reset() (see
        # routes/auth/password_reset_routes.py) — keeps live tokens from
        # accumulating per account and limits the blast radius if an earlier
        # mail leaked. Runs BEFORE the add() so the fresh token, which is not
        # in the session yet, cannot be swept up by the bulk UPDATE.
        #
        # Scoped to purpose='magic': a welcome/sign-in mail must NOT kill a
        # password-reset link the same user requested moments earlier (and the
        # reset flow returns the favour by scoping its own UPDATE to 'reset').
        PasswordResetToken.query.filter(
            PasswordResetToken.username == username,
            PasswordResetToken.purpose == PURPOSE_MAGIC,
            PasswordResetToken.used_at.is_(None),
        ).update({PasswordResetToken.used_at: datetime.utcnow()},
                 synchronize_session=False)

        _db.session.add(token)
        _db.session.commit()
        # The URL MUST carry the transient PLAINTEXT ``raw_token``: since M6
        # (hashed tokens at rest) ``token.token`` holds only the SHA-256 hash,
        # and POST /auth/magic-login hashes whatever it receives before the
        # lookup — a hash in the link could never match. Same rule as the
        # password-reset link (password_reset_routes.py).
        return f"{_public_url()}/auto-login/{token.raw_token}"
    except Exception:
        logging.getLogger('email').warning("Could not mint magic-login token for %s", username)
        return None


def send_ijcai_welcome(
    *,
    username: str,
    email: str,
    recipient_user_id: Optional[int] = None,
    referral_link_id: Optional[int] = None,
) -> None:
    """Send the English IJCAI demo welcome mail (logged as mail_type 'welcome').

    Includes a passwordless auto-login link so the recipient can sign back in
    straight from the mail (the email is the ownership proof). The link stays
    usable for its whole 7-day window, not just once — see
    ``_make_magic_login_url``.
    """
    auto_login_url = _make_magic_login_url(username)
    rendered = render_ijcai_welcome(username=username, auto_login_url=auto_login_url)
    record_and_send(
        mail_type='welcome',
        to_email=email,
        subject=rendered['subject'],
        body_text=rendered['body_text'],
        body_html=rendered['body_html'],
        from_addr=_from_notify(),
        reply_to=_reply_to_addr(),
        recipient_user_id=recipient_user_id,
        referral_link_id=referral_link_id,
        meta={'username': username, 'variant': 'ijcai'} if username else None,
    )


# ---------------------------------------------------------------------------
# General LLARS demo: bilingual invitation + welcome (de + en)
# ---------------------------------------------------------------------------
# A recipient gets a 1-week demo account that walks through one scenario PER
# evaluation type (rating, ranking, comparison, communication comparison,
# authenticity, labeling, mail rating). The invitation mail (sent from the
# Mail-Center) carries both the German and the English join link; the welcome
# mail (on /join/demo-* signup) explains the types and the 1-week window.

# (Deutsch, English) labels for the seven evaluation types shown in both mails.
_DEMO_TYPES = [
    ("Bewertung (Rating)", "Rating"),
    ("Ranking", "Ranking"),
    ("Paarvergleich (Comparison)", "Pairwise comparison"),
    ("Kommunikationsvergleich", "Communication comparison"),
    ("Authentizität", "Authenticity"),
    ("Labeling", "Labeling"),
    ("Mail-Bewertung", "Mail rating"),
]
DEMO_LINK_SLUG_DE = "demo-de"
DEMO_LINK_SLUG_EN = "demo-en"


def _demo_types_li(lang: str) -> str:
    idx = 0 if lang == 'de' else 1
    return "".join(
        f'<li style="margin:0 0 4px;">{_html_escape(t[idx])}</li>' for t in _DEMO_TYPES
    )


def _demo_shell(header_sub: str, inner_html: str) -> str:
    """Shared branded card shell (matches the IJCAI/welcome design)."""
    logo_url = f"{_public_url()}/android-chrome-192x192.png"
    return f"""\
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:28px 24px;">
            <img src="{logo_url}" width="64" height="64" alt="LLARS" style="display:block;border:0;margin-bottom:10px;border-radius:12px;">
            <div style="font-size:20px;font-weight:600;color:#ffffff;">LLARS — Demo</div>
            <div style="font-size:13px;color:#ffffff;opacity:0.9;margin-top:2px;">{_html_escape(header_sub)}</div>
          </td>
        </tr>
        <tr><td style="padding:26px 28px 10px;">{inner_html}</td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _demo_cta(href: str, label: str) -> str:
    return (f'<p style="margin:0 0 16px;text-align:center;">'
            f'<a href="{href}" style="display:inline-block;background:#5d7a4a;color:#ffffff;'
            f'text-decoration:none;font-size:15px;font-weight:600;padding:12px 26px;'
            f'border-radius:14px 4px 14px 4px;">{_html_escape(label)}</a></p>')


# Per-language copy for the two single-language demo mails (de | en).
_DEMO_COPY = {
    'de': {
        'inv_subject': "Schauen Sie sich LLARS an — kostenlose Demo",
        'wel_subject': "Willkommen bei der LLARS-Demo",
        'hello': "Hallo,",
        'inv_intro': ("wir laden Sie ein, <strong>LLARS</strong> (das LLM-Assisted Research "
                      "System) unverbindlich auszuprobieren. Über die Demo legen Sie in einem "
                      "Klick einen Zugang an und klicken sich durch je ein Szenario pro "
                      "Evaluationstyp:"),
        'inv_note': ("So sehen Sie, wie Rating, Ranking, Vergleiche &amp; Co. aussehen — und in "
                     "der Szenario-Analyse die live aggregierte Übereinstimmung aller "
                     "Teilnehmenden. Die Szenarien bleiben <strong>eine Woche</strong> verfügbar."),
        'inv_cta': "Demo starten →",
        'wel_lead': "Willkommen bei der LLARS-Demo!",
        'user_label': "Ihr Benutzername",
        'wel_enrolled': "Sie sind als Evaluator:in in je einem Demo-Szenario pro Typ eingetragen:",
        'wel_note': ("Probieren Sie ein paar aus und öffnen Sie dann die Analyse eines Szenarios, "
                     "um die live aggregierte Übereinstimmung aller Teilnehmenden zu sehen. "
                     "<strong>Die Szenarien sind eine Woche verfügbar.</strong>"),
        'wel_cta': "Zur Demo →",
    },
    'en': {
        'inv_subject': "Explore LLARS — free demo",
        'wel_subject': "Welcome to the LLARS demo",
        'hello': "Hello,",
        'inv_intro': ("we invite you to try <strong>LLARS</strong> (the LLM-Assisted Research "
                      "System). The demo sets up an account in one click and walks you through "
                      "one scenario per evaluation type:"),
        'inv_note': ("See how rating, ranking, comparison &amp; co. look — and watch the live "
                     "aggregated inter-rater agreement in the scenario analysis. The scenarios "
                     "stay available for <strong>one week</strong>."),
        'inv_cta': "Start the demo →",
        'wel_lead': "Welcome to the LLARS demo!",
        'user_label': "Your username",
        'wel_enrolled': "You're enrolled as an evaluator in one demo scenario per type:",
        'wel_note': ("Try a few, then open a scenario's analysis to watch the live aggregated "
                     "inter-rater results. <strong>The scenarios are available for one week.</strong>"),
        'wel_cta': "Open the demo →",
    },
}
_DEMO_FOOTER = ('<p style="margin:14px 0 0;font-size:13px;line-height:1.5;color:#6b7563;">'
                'Das LLARS-Team · KI-Zentrum Bayern · TH Nürnberg</p>')


def render_demo_invitation(*, lang: str = 'de', link: Optional[str] = None) -> Dict[str, str]:
    """LLARS demo INVITATION mail in a single language (``lang`` ∈ {de, en}).

    The CTA points at /join/demo-de or /join/demo-en (the account + UI is set to
    that language). Pure render, no send. ``link`` overrides the default.
    """
    lang = 'en' if lang == 'en' else 'de'
    c = _DEMO_COPY[lang]
    base = _public_url()
    slug = DEMO_LINK_SLUG_EN if lang == 'en' else DEMO_LINK_SLUG_DE
    link = link or f"{base}/join/{slug}"
    inner = (
        f'<p style="margin:0 0 12px;font-size:15px;line-height:1.55;">{c["hello"]}</p>'
        f'<p style="margin:0 0 12px;font-size:15px;line-height:1.55;">{c["inv_intro"]}</p>'
        f'<ul style="margin:0 0 14px;padding-left:20px;font-size:14px;line-height:1.5;color:#5a6650;">{_demo_types_li(lang)}</ul>'
        f'<p style="margin:0 0 14px;font-size:14px;line-height:1.55;color:#5a6650;">{c["inv_note"]}</p>'
        f'{_demo_cta(link, c["inv_cta"])}{_DEMO_FOOTER}'
    )
    body_html = _demo_shell("Kann KI Beratung? · KI-Zentrum Bayern", inner)
    types_text = ", ".join(t[0 if lang == 'de' else 1] for t in _DEMO_TYPES)
    body_text = f"{c['inv_subject']}\n\n{c['hello']}\n{types_text}\n{link}\n\nLLARS · KI-Zentrum Bayern\n"
    return {'subject': c['inv_subject'], 'body_text': body_text, 'body_html': body_html}


def render_demo_welcome(*, username: str, lang: str = 'de',
                        auto_login_url: Optional[str] = None) -> Dict[str, str]:
    """LLARS demo WELCOME mail in a single language, shown after /join/demo-* signup.

    Explains the scenario types + the one-week availability and offers a
    one-click sign-in when ``auto_login_url`` is given.
    """
    lang = 'en' if lang == 'en' else 'de'
    c = _DEMO_COPY[lang]
    base = _public_url()
    cta = auto_login_url or f"{base}/evaluation"
    safe_user = _html_escape(username)
    user_box = (
        '<div style="background:#f7f9f4;border-radius:10px 3px 10px 3px;padding:14px 18px;margin:0 0 18px;line-height:1.4;">'
        f'<div style="font-size:12px;color:#8a9580;margin:0 0 4px;">{c["user_label"]}</div>'
        f'<div style="font-size:19px;font-weight:600;color:#2c3320;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;word-break:break-all;">{safe_user}</div></div>'
    )
    inner = (
        f'<p style="margin:0 0 12px;font-size:15px;line-height:1.55;">{c["wel_lead"]}</p>'
        f'{user_box}'
        f'<p style="margin:0 0 12px;font-size:15px;line-height:1.55;">{c["wel_enrolled"]}</p>'
        f'<ul style="margin:0 0 14px;padding-left:20px;font-size:14px;line-height:1.5;color:#5a6650;">{_demo_types_li(lang)}</ul>'
        f'<p style="margin:0 0 14px;font-size:14px;line-height:1.55;color:#5a6650;">{c["wel_note"]}</p>'
        f'{_demo_cta(cta, c["wel_cta"])}{_DEMO_FOOTER}'
    )
    body_html = _demo_shell("Kann KI Beratung? · KI-Zentrum Bayern", inner)
    body_text = f"{c['wel_lead']}\n{c['user_label']}: {username}\n{cta}\n\nLLARS · KI-Zentrum Bayern\n"
    return {'subject': c['wel_subject'], 'body_text': body_text, 'body_html': body_html}


def send_demo_welcome(*, username: str, email: str, lang: str = 'de',
                      recipient_user_id: Optional[int] = None,
                      referral_link_id: Optional[int] = None) -> None:
    """Send the bilingual demo welcome mail with a re-usable auto-login link
    (valid 7 days — see ``_make_magic_login_url``)."""
    auto_login_url = _make_magic_login_url(username)
    rendered = render_demo_welcome(username=username, lang=lang, auto_login_url=auto_login_url)
    record_and_send(
        mail_type='welcome',
        to_email=email,
        subject=rendered['subject'],
        body_text=rendered['body_text'],
        body_html=rendered['body_html'],
        from_addr=_from_notify(),
        reply_to=_reply_to_addr(),
        recipient_user_id=recipient_user_id,
        referral_link_id=referral_link_id,
        meta={'username': username, 'variant': 'demo'} if username else None,
    )


def send_magic_login_email(
    *,
    username: str,
    email: str,
    locale: str = 'en',
    recipient_user_id: Optional[int] = None,
    referral_link_id: Optional[int] = None,
) -> bool:
    """Send a passwordless QUICK-LOGIN mail (used on re-entry via an email-mode
    referral link). The /auto-login/<token> link stays usable for its whole
    7-day window (not one-shot); the emailed address is the ownership proof. Language follows the link (en/de). Returns False if no token
    could be minted (caller may fall back). Logged as mail_type 'magic_login'.
    """
    auto_login_url = _make_magic_login_url(username)
    if not auto_login_url:
        return False
    base = _public_url()
    logo_url = f"{base}/android-chrome-192x192.png"
    de = (locale or 'en').lower().startswith('de')

    if de:
        subject = "Dein Anmelde-Link für LLARS"
        head_sub = "LLARS — Demo"
        greeting = "Hallo,"
        intro = "hier ist dein persönlicher Anmelde-Link für die LLARS-Demo. Ein Klick — kein Passwort nötig."
        cta = "Jetzt anmelden →"
        note = ("Der Link ist 7 Tage gültig und kann in dieser Zeit beliebig oft genutzt werden — "
                "bewahre die E-Mail einfach auf. Falls du das nicht angefordert hast, ignoriere diese E-Mail.")
        body_text = (
            f"Hallo,\n\nhier ist dein persönlicher Anmelde-Link für die LLARS-Demo "
            f"(kein Passwort nötig):\n\n{auto_login_url}\n\n"
            f"Benutzername: {username}\n\n"
            f"Der Link ist 7 Tage gültig und in dieser Zeit beliebig oft nutzbar.\n"
        )
    else:
        subject = "Your LLARS sign-in link"
        head_sub = "LLARS — Demo"
        greeting = "Hello,"
        intro = "here is your personal sign-in link for the LLARS demo. One click — no password needed."
        cta = "Sign in →"
        note = ("The link stays valid for 7 days and you can use it as often as you like in that "
                "window — just keep this email. If you didn't request this, just ignore it.")
        body_text = (
            f"Hello,\n\nhere is your personal sign-in link for the LLARS demo "
            f"(no password needed):\n\n{auto_login_url}\n\n"
            f"Username: {username}\n\n"
            f"The link is valid for 7 days and can be reused as often as you like.\n"
        )

    body_html = f"""\
<!DOCTYPE html>
<html lang="{'de' if de else 'en'}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr><td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:24px;">
          <img src="{logo_url}" width="56" height="56" alt="LLARS" style="display:block;border:0;margin-bottom:8px;border-radius:12px;">
          <div style="font-size:18px;font-weight:600;color:#ffffff;">{head_sub}</div>
        </td></tr>
        <tr><td style="padding:26px 28px;">
          <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">{greeting}</p>
          <p style="margin:0 0 20px;font-size:15px;line-height:1.55;">{intro}</p>
          <p style="margin:0 0 20px;text-align:center;">
            <a href="{auto_login_url}" style="display:inline-block;background:#5d7a4a;color:#ffffff;text-decoration:none;font-size:15px;font-weight:600;padding:12px 26px;border-radius:14px 4px 14px 4px;">{cta}</a>
          </p>
          <p style="margin:0;font-size:12px;line-height:1.5;color:#8a9580;">{note}</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    record_and_send(
        mail_type='magic_login',
        to_email=email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        from_addr=_from_notify(),
        reply_to=_reply_to_addr(),
        recipient_user_id=recipient_user_id,
        referral_link_id=referral_link_id,
        meta={'username': username, 'variant': 'magic_login'} if username else None,
    )
    return True


def render_password_reset(
    *,
    username: str,
    reset_link: str,
    ttl_hours: int = 2,
) -> Dict[str, str]:
    """Build the branded self-service password-reset mail (subject + text + html).

    Pure render — NO send. Shared by ``send_password_reset`` and the admin
    ``/templates`` preview endpoint so the preview is byte-identical to what
    gets sent. All body-building lives here.

    Same visual shell as the welcome mail ("Kann KI Beratung?" / KI-Zentrum
    Bayern), with a single reset call-to-action, the validity window and a
    clear "ignore if you did not request this" note. German only; the raw link
    is shown too so a client that strips the button still works.
    """
    base = _public_url()
    logo_url = f"{base}/android-chrome-192x192.png"
    safe_user = _html_escape(username)
    safe_link = _html_escape(reset_link)

    subject = "Passwort zurücksetzen — „Kann KI Beratung?\""

    body_text = (
        "Hallo,\n\n"
        "für Ihr Konto beim Forschungsprojekt „Kann KI Beratung?\" "
        "(KI-Zentrum Bayern, TH Nürnberg) wurde ein Zurücksetzen des Passworts "
        "angefordert.\n\n"
        f"Benutzername: {username}\n\n"
        f"Setzen Sie Ihr Passwort über folgenden Link zurück (gültig für {ttl_hours} Stunden):\n"
        f"{reset_link}\n\n"
        "Falls Sie diese Anfrage nicht gestellt haben, können Sie diese E-Mail "
        "ignorieren — Ihr Passwort bleibt unverändert.\n\n"
        "Fragen? Schreiben Sie uns an llars@e-beratungsinstitut.de.\n\n"
        "— Das Team des KI-Zentrums Bayern\n"
    )

    body_html = f"""\
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:28px 24px;">
            <img src="{logo_url}" width="64" height="64" alt="Kann KI Beratung?" style="display:block;border:0;margin-bottom:10px;border-radius:12px;">
            <div style="font-size:20px;font-weight:600;color:#ffffff;">Passwort zurücksetzen</div>
            <div style="font-size:13px;color:#ffffff;opacity:0.9;margin-top:2px;">KI-Zentrum Bayern · TH Nürnberg</div>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 28px 8px;">
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">Hallo,</p>
            <p style="margin:0 0 14px;font-size:15px;line-height:1.55;">für Ihr Konto beim Projekt <strong>„Kann KI Beratung?"</strong> wurde ein Zurücksetzen des Passworts angefordert.</p>
            <div style="background:#f4f6f2;border-radius:10px 3px 10px 3px;padding:14px 16px;margin:0 0 16px;font-size:14px;line-height:1.5;">
              <p style="margin:0;"><strong>Benutzername:</strong> {safe_user}</p>
            </div>
            <p style="margin:0 0 22px;text-align:center;">
              <a href="{safe_link}" style="display:inline-block;background:#b0ca97;color:#2c3320;text-decoration:none;font-weight:600;font-size:15px;padding:12px 28px;border-radius:10px 3px 10px 3px;">Passwort zurücksetzen</a>
            </p>
            <p style="margin:0 0 14px;font-size:13px;line-height:1.5;color:#5a6650;">Der Link ist <strong>{ttl_hours} Stunden</strong> gültig. Falls der Button nicht funktioniert, kopieren Sie diesen Link in den Browser:<br><a href="{safe_link}" style="color:#3f7d6b;word-break:break-all;">{safe_link}</a></p>
            <p style="margin:0 0 14px;font-size:13px;line-height:1.5;color:#5a6650;">Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail — Ihr Passwort bleibt unverändert.</p>
            <p style="margin:0 0 14px;font-size:13px;line-height:1.5;color:#5a6650;">Fragen? Schreiben Sie uns an <a href="mailto:llars@e-beratungsinstitut.de" style="color:#3f7d6b;">llars@e-beratungsinstitut.de</a>.</p>
            <p style="margin:18px 0 0;font-size:12px;color:#8a9580;">— Das Team des KI-Zentrums Bayern</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    return {'subject': subject, 'body_text': body_text, 'body_html': body_html}


def send_password_reset(
    *,
    username: str,
    email: str,
    reset_link: str,
    ttl_hours: int = 2,
) -> None:
    """Send the branded self-service password-reset email.

    Thin send wrapper over ``render_password_reset`` (which owns the
    body-building). No-ops for unreachable inboxes (defensive — the route
    already guards on a real recipient).
    """
    if not _is_real_inbox(email):
        logger.info("[email] skipping reset mail for %s — no real inbox", username)
        return

    rendered = render_password_reset(
        username=username,
        reset_link=reset_link,
        ttl_hours=ttl_hours,
    )

    # PRIVACY: password-reset bodies contain a single-use token. We log only
    # type / recipient / subject / status — NEVER the body or the reset link
    # (no ``meta`` preview here). See app/db/models/email_log.py.
    record_and_send(
        mail_type='password_reset',
        to_email=email,
        subject=rendered['subject'],
        body_text=rendered['body_text'],
        body_html=rendered['body_html'],
        from_addr=_from_noreply(),
        reply_to=_reply_to_addr(),
    )


# ---------------------------------------------------------------------------
# Branded wrapper + Mail-Center senders (invitation / announcement)
# ---------------------------------------------------------------------------


def _brand_wrap_html(*, heading: str, body_inner_html: str,
                     cta_label: Optional[str] = None,
                     cta_url: Optional[str] = None,
                     lang: str = 'de') -> str:
    """Wrap arbitrary inner HTML in the LLARS green-gradient brand shell.

    Reuses the exact header gradient (#b0ca97 → #88c4c8), rounded-asymmetric
    card and footer of the transactional welcome / reset mails so manual
    invitations and announcements look like first-class LLARS mail. The caller
    is responsible for producing *safe* ``body_inner_html`` (escaped plain text
    or sanitised Markdown→HTML) — this function does not escape it.
    """
    base = _public_url()
    logo_url = f"{base}/android-chrome-192x192.png"
    safe_heading = _html_escape(heading)
    subtitle = "KI-Zentrum Bayern · TH Nürnberg"

    cta_html = ""
    if cta_label and cta_url:
        cta_html = (
            '<p style="margin:0 0 8px;text-align:center;">'
            f'<a href="{_html_escape(cta_url)}" '
            'style="display:inline-block;background:#b0ca97;color:#2c3320;'
            'text-decoration:none;font-weight:600;font-size:15px;padding:12px 28px;'
            f'border-radius:10px 3px 10px 3px;">{_html_escape(cta_label)}</a></p>'
        )

    return f"""\
<!DOCTYPE html>
<html lang="{_html_escape(lang)}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:28px 24px;">
            <img src="{logo_url}" width="64" height="64" alt="LLARS" style="display:block;border:0;margin-bottom:10px;border-radius:12px;">
            <div style="font-size:20px;font-weight:600;color:#ffffff;">{safe_heading}</div>
            <div style="font-size:13px;color:#ffffff;opacity:0.9;margin-top:2px;">{subtitle}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 28px 8px;font-size:15px;line-height:1.55;">
            {body_inner_html}
            {cta_html}
            <p style="margin:18px 0 0;font-size:13px;line-height:1.5;color:#5a6650;">Fragen? Schreiben Sie uns an <a href="mailto:llars@e-beratungsinstitut.de" style="color:#3f7d6b;">llars@e-beratungsinstitut.de</a>.</p>
            <p style="margin:14px 0 0;font-size:12px;color:#8a9580;">KI-Zentrum Bayern · TH Nürnberg</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def _markdown_or_text_to_html(text: str) -> str:
    """Render an announcement body to safe HTML.

    Tries Markdown (if the ``markdown`` package is available) for nice
    formatting; otherwise falls back to escaped plain text with line breaks.
    Either way the output is safe: Markdown is rendered with no raw-HTML
    passthrough beyond the package default, and the fallback fully escapes.
    Kept dependency-soft so a missing ``markdown`` package never breaks sends.
    """
    raw = text or ""
    try:
        import markdown as _md  # type: ignore
        # No 'extra' raw-HTML; treat input as Markdown only.
        return _md.markdown(raw, extensions=[])
    except Exception:
        return _html_escape(raw).replace("\n", "<br>")


def render_invitation(*, link_url: str, label: Optional[str] = None,
                      intro: Optional[str] = None) -> Dict[str, str]:
    """Build the branded invitation mail (subject + text + html). No send.

    Always the LONG recruitment version — the same wording + branded shell as
    the per-org HTML templates (``data/human_study/v15/invitation_branded``).
    The short variant was dropped: we always send the full invitation.

    ``link_url`` is the org-specific join link (source tracking). ``label`` is
    the recruiting-source tag (e.g. "Friends & Family") and is deliberately NOT
    shown to recipients — the study is "Kann KI Beratung?". ``intro`` optionally
    prepends one custom line after the salutation.

    Used by ``send_invitation`` and the admin ``/preview`` so the live preview
    is byte-identical to what gets sent.
    """
    base = _public_url()
    logo_url = f"{base}/android-chrome-192x192.png"
    safe_link = _html_escape(link_url)
    subject = "Kann KI Beratung?"
    intro_clean = (intro or "").strip()

    # --- plain-text ---
    text_parts = ["Liebe Fachkräfte,", ""]
    if intro_clean:
        text_parts += [intro_clean, ""]
    text_parts += [
        "die Entwicklungen in den KI-Technologien schreiten rasant voran. "
        "Insbesondere KI-Chatbots erfreuen sich einer breiten Aufmerksamkeit "
        "und werden als persönliche Assistenten und Ratgeber in allen "
        "Lebenslagen genutzt. Wir am KI-Zentrum Bayern möchten verstehen, "
        "welche Rolle KI-Chatbots künftig in professionellen Beratungskontexten "
        "der Onlineberatung einnehmen können. Hierzu möchten wir in einem "
        "ersten Schritt prüfen:",
        "",
        "- Standard-KI vs. trainierte KI: wie sich die Qualität häufig "
        "genutzter KI-Modelle gegenüber speziell trainierten KI-Modellen "
        "unterscheidet, und",
        "- KI vs. Mensch: wie die Qualität von KI-Modellen im Vergleich zu "
        "Antworten professioneller Fachkräfte der Onlineberatung bewertet wird.",
        "",
        "Wir bitten Sie um Unterstützung und Ihre Expertise.",
        "",
        f"Jetzt mitmachen: {link_url}",
        "",
        "Über den Link gelangen Sie zu einer Testplattform. Darin finden Sie "
        "kleine Fallvignetten, in denen Beratungsinteraktionen dargestellt "
        "werden — überwiegend aus der Mailberatung, ergänzt um Chat- und "
        "Transkript-Formate. Stets werden zwei mögliche Antworten "
        "bereitgestellt; Sie wählen, welche Sie am ehesten verwenden würden.",
        "",
        "1. Öffnen Sie den Link und legen Sie ein Konto an — anonym oder mit "
        "E-Mail (Benutzername + Passwort; E-Mail optional).",
        "2. Starten Sie den Test durch Auswahl der ersten Fallvignette.",
        "",
        "Sie möchten wissen, was Sie persönlich bevorzugen? Bewerten Sie 5 "
        "Fälle (ca. 5–10 Minuten), dann erscheint ein Pop-up mit Ihrer "
        "bisherigen Auswertung. Anschließend werden weitere Fälle freigeschaltet.",
        "",
        "Jeder bewertete Fall ist für die Gesamttestung ein Gewinn! Fühlen Sie "
        "sich frei, so viele Fälle zu beantworten, wie Sie möchten. Sie können "
        "jederzeit pausieren und sich wieder einloggen.",
        "",
        "Leiten Sie diese Mail gerne an andere Beratungsfachkräfte in Ihrem "
        "Umfeld weiter.",
        "",
        "Bei Fragen erreichen Sie uns unter llars@e-beratungsinstitut.de.",
        "",
        "Vielen Dank!",
        "",
        "Mit kollegialen Grüßen",
        "Philipp Steigerwald",
        "KI-Zentrum Bayern",
    ]
    body_text = "\n".join(text_parts)

    # --- HTML: identical branded shell + wording as the recruitment templates ---
    intro_html = (
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.6;">{_html_escape(intro_clean)}</p>'
        if intro_clean else ""
    )
    body_html = f"""\
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f4f6f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#2c3320;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f2;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:14px 4px 14px 4px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
        <tr>
          <td align="center" style="background:linear-gradient(135deg,#b0ca97,#88c4c8);padding:30px 24px;">
            <img src="{logo_url}" width="64" height="64" alt="Kann KI Beratung?" style="display:block;border:0;margin-bottom:10px;border-radius:12px;">
            <div style="font-size:22px;font-weight:600;color:#ffffff;">Kann KI Beratung?</div>
            <div style="font-size:13px;color:#ffffff;opacity:0.9;margin-top:2px;">KI-Zentrum Bayern · TH Nürnberg</div>
          </td>
        </tr>
        <tr><td style="padding:28px 30px 26px;">
<p style="margin:0 0 14px;font-size:15px;line-height:1.6;">Liebe Fachkräfte,</p>
{intro_html}
<p style="margin:0 0 14px;font-size:15px;line-height:1.6;">die Entwicklungen in den KI-Technologien schreiten rasant voran. Insbesondere KI-Chatbots erfreuen sich einer breiten Aufmerksamkeit und werden als persönliche Assistenten und Ratgeber in allen Lebenslagen genutzt. Wir am KI-Zentrum Bayern möchten verstehen, welche Rolle KI-Chatbots künftig in professionellen Beratungskontexten der Onlineberatung einnehmen können. Hierzu möchten wir in einem ersten Schritt prüfen:</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px;">
  <tr><td style="padding:0 0 8px;font-size:15px;line-height:1.55;">• <strong>Standard-KI vs. trainierte KI:</strong> wie sich die Qualität häufig genutzter KI-Modelle gegenüber speziell trainierten KI-Modellen unterscheidet, und</td></tr>
  <tr><td style="font-size:15px;line-height:1.55;">• <strong>KI vs. Mensch:</strong> wie die Qualität von KI-Modellen im Vergleich zu Antworten professioneller Fachkräfte der Onlineberatung bewertet wird.</td></tr>
</table>
<p style="margin:24px 0;text-align:center;font-size:20px;font-weight:700;line-height:1.4;color:#2c3320;">Wir bitten Sie um Unterstützung und Ihre Expertise.</p>
<p style="margin:0 0 10px;text-align:center;">
  <a href="{safe_link}" style="display:inline-block;background:#b0ca97;color:#2c3320;text-decoration:none;font-weight:600;font-size:16px;padding:14px 34px;border-radius:10px 3px 10px 3px;">Jetzt mitmachen</a>
</p>
<p style="margin:0 0 20px;text-align:center;font-size:12px;color:#8a9580;word-break:break-all;"><a href="{safe_link}" style="color:#3f7d6b;">{safe_link}</a></p>
<p style="margin:0 0 14px;font-size:15px;line-height:1.6;">Über den Link gelangen Sie zu einer Testplattform. Darin finden Sie kleine Fallvignetten, in denen Beratungsinteraktionen dargestellt werden — überwiegend aus der Mailberatung, ergänzt um Chat- und Transkript-Formate. Stets werden zwei mögliche Antworten bereitgestellt; Sie wählen, welche Sie am ehesten verwenden würden.</p>
<div style="background:#f4f6f2;border-radius:10px 3px 10px 3px;padding:16px 18px;margin:0 0 16px;">
  <p style="margin:0 0 8px;font-size:14px;line-height:1.55;"><strong>1.</strong> Öffnen Sie den Link und legen Sie ein Konto an — <strong>anonym oder mit E-Mail</strong> (Benutzername + Passwort; E-Mail optional).</p>
  <p style="margin:0;font-size:14px;line-height:1.55;"><strong>2.</strong> Starten Sie den Test durch Auswahl der ersten Fallvignette.</p>
</div>
<p style="margin:0 0 14px;font-size:15px;line-height:1.6;"><strong>Sie möchten wissen, was Sie persönlich bevorzugen?</strong> Bewerten Sie 5 Fälle (ca. 5–10 Minuten), dann erscheint ein Pop-up-Fenster mit Ihrer bisherigen Auswertung. Anschließend werden weitere Fälle freigeschaltet. Nach jeder 5er-Etappe erhalten Sie eine neue Auswertung.</p>
<p style="margin:0 0 14px;font-size:14px;line-height:1.6;color:#5a6650;">Jeder bewertete Fall ist für die Gesamttestung ein Gewinn! Fühlen Sie sich frei, so viele Fälle zu beantworten, wie Sie möchten. Sie können jederzeit pausieren und sich wieder einloggen.</p>
<p style="margin:0 0 14px;font-size:14px;line-height:1.6;color:#5a6650;">Leiten Sie diese Mail gerne an andere Beratungsfachkräfte in Ihrem Umfeld weiter.</p>
<p style="margin:0 0 14px;font-size:14px;line-height:1.6;color:#5a6650;">Bei Fragen erreichen Sie uns unter <a href="mailto:llars@e-beratungsinstitut.de" style="color:#3f7d6b;">llars@e-beratungsinstitut.de</a>.</p>
<p style="margin:0 0 14px;font-size:15px;line-height:1.6;">Vielen Dank!</p>
<p style="margin:0;font-size:15px;line-height:1.6;">Mit kollegialen Grüßen<br>Philipp Steigerwald<br>KI-Zentrum Bayern</p>
        </td></tr>
      </table>
      <div style="max-width:600px;font-size:11px;color:#9aa48d;padding:14px 8px;">KI-Zentrum Bayern · TH Nürnberg · <a href="https://ki-zentrum.bayern" style="color:#9aa48d;">ki-zentrum.bayern</a></div>
    </td></tr>
  </table>
</body>
</html>
"""
    return {'subject': subject, 'body_text': body_text, 'body_html': body_html}


def render_announcement(*, subject: str, body: str) -> Dict[str, str]:
    """Build a branded announcement mail from a custom subject + Markdown body.

    No send — shared by ``send_announcement`` and the ``/preview`` endpoint.
    """
    inner = (
        '<div style="margin:0 0 8px;">'
        + _markdown_or_text_to_html(body)
        + '</div>'
    )
    body_html = _brand_wrap_html(heading=subject, body_inner_html=inner)
    return {'subject': subject, 'body_text': body or "", 'body_html': body_html}


# ---------------------------------------------------------------------------
# Standard-template previews (Mail-Center "Vorlagen" tab)
# ---------------------------------------------------------------------------
#
# The three automatic transactional mails (welcome / password_reset /
# invitation) are normally only ever SENT — there is no UI to look at them.
# These helpers render each with clearly-marked SAMPLE data so an admin can
# preview exactly what users receive, without triggering a real send. The
# render functions above are reused, so the preview is byte-identical to a
# real send modulo the obviously-fake sample values.

# Clearly-fake placeholders so a preview can never be mistaken for a real mail.
SAMPLE_USERNAME = "Max Mustermann"
SAMPLE_RESET_LINK = "https://llars.example.org/reset-password?token=BEISPIEL-TOKEN-1234"
SAMPLE_STUDY_LABEL = "Beispiel-Studie"


def render_standard_template(template_type: str) -> Dict[str, Any]:
    """Render one standard transactional template with sample data (no send).

    ``template_type`` ∈ {``welcome``, ``password_reset``, ``invitation``}.
    Returns ``{type, subject, html, text, description, variables}`` where
    ``description``/``variables`` document when the mail is sent and which
    placeholders it interpolates — surfaced in the Mail-Center "Vorlagen" tab.
    Raises ``ValueError`` for an unknown type so the route can map it to 400.
    """
    if template_type == 'welcome':
        rendered = render_welcome(
            username=SAMPLE_USERNAME,
            scenario_id=None,
            referral_label=SAMPLE_STUDY_LABEL,
        )
        meta = {
            'description': (
                "Wird automatisch versendet, sobald sich ein Nutzer registriert "
                "oder über einen Einladungslink ein Konto anlegt."
            ),
            'variables': ['username', 'studienlink', 'studienlabel'],
        }
    elif template_type == 'password_reset':
        rendered = render_password_reset(
            username=SAMPLE_USERNAME,
            reset_link=SAMPLE_RESET_LINK,
            ttl_hours=2,
        )
        meta = {
            'description': (
                "Wird versendet, wenn ein Nutzer über „Passwort vergessen?\" "
                "ein Zurücksetzen anfordert. Enthält einen zeitlich begrenzten "
                "Link (Standard: 2 Stunden)."
            ),
            'variables': ['username', 'reset_link', 'ttl_hours'],
        }
    elif template_type == 'invitation':
        rendered = render_invitation(
            link_url="https://llars.example.org/join/beispiel-studie",
            label=SAMPLE_STUDY_LABEL,
            intro=None,
        )
        meta = {
            'description': (
                "Wird über „Senden → Einladung\" an ausgewählte Empfänger "
                "verschickt und enthält den Anmeldelink der gewählten Kampagne."
            ),
            'variables': ['join_link', 'studienlabel', 'intro'],
        }
    elif template_type == 'ijcai':
        # Englische Demo-Willkommensmail für den IJCAI-2026-Link (/join/ijcai).
        # Single source: dieselbe Render-Funktion wie der programmatische Versand.
        rendered = render_ijcai_welcome(username=SAMPLE_USERNAME, auto_login_url=None)
        meta = {
            'description': (
                "Englische Demo-Willkommensmail für den IJCAI-2026-Link "
                "(/join/ijcai). Beim Onboarding mit persönlichem One-Click-Sign-in "
                "(7 Tage gültig) versendet; ohne Magic-Link verweist der CTA auf den Hub."
            ),
            'variables': ['username', 'auto_login_url'],
        }
    elif template_type in ('demo_invitation_de', 'demo_invitation_en'):
        # LLARS-Demo-Einladung — die versendbare Mail, je Sprache eine Variante.
        _lang = 'en' if template_type.endswith('_en') else 'de'
        rendered = render_demo_invitation(lang=_lang)
        _lname = 'Deutsch' if _lang == 'de' else 'Englisch'
        meta = {
            'description': (
                f"LLARS-Demo-Einladung ({_lname}). Über „Senden → Vorlage\" an "
                f"Empfänger verschickbar; der /join/demo-{_lang}-Link legt einen "
                f"1-Wochen-Demo-Zugang in {_lname} an."
            ),
            'variables': ['link'],
        }
    else:
        raise ValueError(f"Unbekannter Vorlagentyp: {template_type}")

    return {
        'type': template_type,
        'subject': rendered['subject'],
        'html': rendered['body_html'],
        'text': rendered['body_text'],
        'description': meta['description'],
        'variables': meta['variables'],
    }


def render_standard_templates() -> list:
    """Render all three standard templates with sample data, in display order."""
    return [render_standard_template(t)
            for t in ('welcome', 'password_reset', 'invitation', 'ijcai',
                      'demo_invitation_de', 'demo_invitation_en')]


def _preview(text: str) -> str:
    """Trim a body to the privacy-bounded preview length for the log."""
    from db.models.email_log import PREVIEW_MAX_CHARS
    t = (text or "").strip()
    return t[:PREVIEW_MAX_CHARS]


def send_invitation(*, to_email: str, link_url: str,
                    label: Optional[str] = None, intro: Optional[str] = None,
                    referral_link_id: Optional[int] = None,
                    triggered_by_user_id: Optional[int] = None,
                    body_html: Optional[str] = None,
                    subject: Optional[str] = None,
                    async_send: bool = True) -> Dict[str, Any]:
    """Send one branded invitation mail and log it (mail_type ``invitation``).

    Returns ``record_and_send``'s ``{'status', 'log_id'}`` so the caller can
    tie a ``referral_invitation`` row to the produced ``email_log`` row.

    ``body_html`` override: the Mail-Center admin compose lets the sender pick a
    per-org branded template (faf/kiz/…) and EDIT it before sending. When given,
    that HTML is sent verbatim instead of the generic ``render_invitation``
    output, with ``subject`` overriding the default. A plaintext fallback is
    derived by stripping tags so non-HTML clients still get readable content.
    """
    if body_html:
        subj = (subject or '').strip() or 'Kann KI Beratung?'
        body_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body_html)).strip()
        rendered_html = body_html
    else:
        rendered = render_invitation(link_url=link_url, label=label, intro=intro)
        subj = rendered['subject']
        body_text = rendered['body_text']
        rendered_html = rendered['body_html']
    return record_and_send(
        mail_type='invitation',
        to_email=to_email,
        subject=subj,
        body_text=body_text,
        body_html=rendered_html,
        from_addr=_from_notify(),
        reply_to=_reply_to_addr(),
        referral_link_id=referral_link_id,
        triggered_by_user_id=triggered_by_user_id,
        meta={'preview': _preview(intro or body_text)},
        async_send=async_send,
    )


def send_announcement(*, to_email: str, subject: str, body: str,
                      triggered_by_user_id: Optional[int] = None,
                      recipient_user_id: Optional[int] = None,
                      scenario_id: Optional[int] = None,
                      async_send: bool = True) -> Dict[str, Any]:
    """Send one branded announcement mail and log it (mail_type ``announcement``)."""
    rendered = render_announcement(subject=subject, body=body)
    return record_and_send(
        mail_type='announcement',
        to_email=to_email,
        subject=rendered['subject'],
        body_text=rendered['body_text'],
        body_html=rendered['body_html'],
        from_addr=_from_notify(),
        reply_to=_reply_to_addr(),
        recipient_user_id=recipient_user_id,
        triggered_by_user_id=triggered_by_user_id,
        scenario_id=scenario_id,
        meta={'preview': _preview(body)},
        async_send=async_send,
    )


def send_standard_template(*, template_type: str, to_email: str,
                           triggered_by_user_id: Optional[int] = None,
                           async_send: bool = False) -> Dict[str, Any]:
    """Quick-send a standard transactional template to a single address.

    Powers the Mail-Center "Vorlagen" → Schnellversand: the admin picks one of
    the standard templates (``welcome`` / ``password_reset`` / ``invitation``)
    and sends it to an entered address. Renders with the SAME sample data shown
    in the preview so the mail is byte-identical to what the tab displays, and
    logs it under its real ``mail_type`` with a ``quick_send`` variant so it's
    recognisable in the log. Raises ``ValueError`` for an unknown template type
    (the route maps it to 400). Blocks by default (``async_send=False``) so the
    admin gets a truthful sent/failed result for the one recipient.
    """
    rendered = render_standard_template(template_type)  # may raise ValueError
    # password_reset keeps the no-reply sender like the real reset mail; the
    # other transactional templates use the notify sender.
    from_addr = _from_noreply() if template_type == 'password_reset' else _from_notify()
    return record_and_send(
        mail_type=template_type,
        to_email=to_email,
        subject=rendered['subject'],
        body_text=rendered['text'],
        body_html=rendered['html'],
        from_addr=from_addr,
        reply_to=_reply_to_addr(),
        triggered_by_user_id=triggered_by_user_id,
        meta={'variant': 'quick_send'},
        async_send=async_send,
    )


def send_quick_html(*, to_email: str, subject: str, body_html: str,
                    triggered_by_user_id: Optional[int] = None,
                    async_send: bool = False) -> Dict[str, Any]:
    """Quick-send a chosen branded template's raw HTML verbatim to one address.

    Used by the Mail-Center "Vorlagen" Schnellversand for the bundled study
    invitations, whose cards carry full branded HTML (no template type). The HTML
    is sent as-is; a plain-text fallback is derived by stripping tags so non-HTML
    clients still get readable content. Logged as ``announcement`` with a
    ``quick_send`` variant. Blocks by default for a truthful per-send result.
    """
    body_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body_html or '')).strip()
    return record_and_send(
        mail_type='announcement',
        to_email=to_email,
        subject=(subject or '').strip() or 'LLARS',
        body_text=body_text,
        body_html=body_html,
        from_addr=_from_notify(),
        reply_to=_reply_to_addr(),
        triggered_by_user_id=triggered_by_user_id,
        meta={'variant': 'quick_send', 'preview': _preview(body_text)},
        async_send=async_send,
    )
