"""
Self-service password-reset routes + the passwordless magic-login exchange.

All three endpoints below read the SAME ``password_reset_tokens`` table, so
each one gates on ``PasswordResetToken.purpose`` (``'reset'`` vs ``'magic'``,
NULL = legacy = ``'reset'``). Without that gate a re-usable sign-in link could
be posted to /password-reset/reset to CHANGE the account's password — a
privilege the sign-in link is explicitly not meant to carry.

Backs the "Passwort vergessen?" link on the login page. Two endpoints:

- ``POST /auth/password-reset/request`` — accepts an email-or-username, and,
  if the feature is enabled and the account resolves to a real email in
  Authentik, mails a short-lived reset link. Returns an identical neutral
  200 for every outcome (found / not-found / no-email / feature-off) so the
  endpoint cannot be used to enumerate accounts.

- ``POST /auth/password-reset/reset`` — exchanges a valid token + new password
  for an Authentik write-through via ``AuthentikAdminService.set_password``.
  The token is only marked used on a successful write, so a failed write
  leaves the old password working and allows a retry.

- ``POST /auth/magic-login`` — exchanges a ``'magic'`` token for an Authentik
  token bundle (passwordless sign-in). Deliberately MULTI-USE inside its TTL;
  see the endpoint docstring.

LLARS stores no usable ``password_hash`` for Authentik-backed users, so the
recipient email is resolved from the Authentik user record, and the password
is only ever written through to Authentik — never to ``User.password_hash``.
"""

import logging
from datetime import datetime, timedelta

from flask import jsonify, request
from sqlalchemy import or_

from auth.decorators import public_endpoint
from decorators.error_handler import handle_api_errors, ValidationError
from routes.auth import auth_bp
from db.database import db
from db.models.password_reset import (
    PasswordResetToken, hash_reset_token, PURPOSE_RESET, PURPOSE_MAGIC,
)
from services.system_settings_service import is_self_service_password_reset_enabled
from services.authentik_admin_service import AuthentikAdminService
from services import email_service

logger = logging.getLogger(__name__)

# Per-account cooldown between reset emails. Caps inbox flooding / SMTP-reputation
# abuse independently of the client IP, so it holds even if the per-IP rate limit
# is evaded (e.g. via X-Forwarded-For rotation). Short enough not to frustrate a
# legitimate user who needs to retry.
_RESEND_COOLDOWN = timedelta(minutes=2)

# Minimum password length for a self-service reset. The write-through targets
# Authentik's admin set_password endpoint, which does NOT run the org password
# policy — so this is the only server-side strength gate on this path.
_MIN_PASSWORD_LENGTH = 8

# Identical neutral response for every /request outcome (anti-enumeration).
_NEUTRAL_MESSAGE = (
    "Falls ein Konto mit diesen Angaben existiert, wurde eine E-Mail mit "
    "Anweisungen zum Zurücksetzen des Passworts gesendet. / If an account "
    "matching these details exists, an email with password-reset "
    "instructions has been sent."
)


def _neutral_ok():
    return jsonify({'success': True, 'message': _NEUTRAL_MESSAGE}), 200


def _invalid_token():
    """Uniform 'invalid/expired link' response (also used as the feature kill-switch)."""
    return jsonify({
        'success': False,
        'code': 'INVALID_TOKEN',
        'error': 'Der Link ist ungültig oder abgelaufen. / The link is invalid or has expired.',
    }), 400


def _looks_like_email(value: str) -> bool:
    return '@' in value and '.' in value


# Reusable purpose gate for the two RESET endpoints. Rows written before the
# ``purpose`` column existed carry NULL; they predate the magic-login split and
# are therefore treated as the stricter, single-use 'reset' kind. Magic tokens
# (purpose='magic') never match this and can never be spent on a password
# change. See db/models/password_reset.py (PURPOSE_* block).
_IS_RESET_TOKEN = or_(
    PasswordResetToken.purpose == PURPOSE_RESET,
    PasswordResetToken.purpose.is_(None),
)


@auth_bp.route('/password-reset/request', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='password_reset')
def request_password_reset():
    """Request a password-reset email. Always returns a neutral 200."""
    # Feature gate: when disabled, behave exactly like a non-matching account.
    if not is_self_service_password_reset_enabled():
        return _neutral_ok()

    data = request.get_json(silent=True) or {}
    identifier = (data.get('email_or_username') or '').strip()
    if not identifier:
        return _neutral_ok()

    # Resolve the Authentik user — by username first, then by email shape.
    user = AuthentikAdminService.find_user(identifier)
    if user is None and _looks_like_email(identifier):
        user = AuthentikAdminService.find_user_by_email(identifier)

    if user is None:
        return _neutral_ok()

    username = user.get('username')
    recipient = (user.get('email') or '').strip()

    # Guard: no real inbox to send to. Synthetic ``@noemail.invalid`` accounts
    # (created for email-less referral signups) and empty addresses get the
    # same neutral response and no email — never write to the .invalid domain.
    if not recipient or recipient.lower().endswith('@noemail.invalid'):
        return _neutral_ok()

    now = datetime.utcnow()

    # Opportunistic cleanup: drop fully-expired rows so the table cannot grow
    # unbounded under repeated requests. Cheap — backed by ix_prt_expires, and
    # this endpoint is low-frequency.
    PasswordResetToken.query.filter(
        PasswordResetToken.expires_at < now
    ).delete(synchronize_session=False)

    # Per-account resend cooldown (anti-abuse / anti-email-bombing). Keyed on the
    # resolved account, NOT the request IP, so it holds even if the per-IP rate
    # limit is evaded via X-Forwarded-For rotation. If we issued a token for this
    # account within the cooldown window, send nothing more but still return the
    # neutral 200 so the response stays indistinguishable from the success path.
    #
    # Scoped to RESET tokens: a magic sign-in link minted seconds earlier (QR
    # join → welcome mail) must not silently swallow the reset mail of a user
    # who immediately clicks "Passwort vergessen".
    recent = (
        PasswordResetToken.query
        .filter(PasswordResetToken.username == username)
        .filter(_IS_RESET_TOKEN)
        .filter(PasswordResetToken.created_at >= now - _RESEND_COOLDOWN)
        .first()
    )
    if recent is not None:
        db.session.commit()  # persist the expired-row cleanup above
        return _neutral_ok()

    # Invalidate any still-valid older RESET tokens for this account so only the
    # newest reset link works (one outstanding link at a time — limits the blast
    # radius if an earlier link leaked). Scoped to purpose='reset' so requesting
    # a password reset does not also kill the user's live magic sign-in link
    # (email_service._make_magic_login_url scopes its mirror UPDATE to 'magic').
    PasswordResetToken.query.filter(
        PasswordResetToken.username == username,
        _IS_RESET_TOKEN,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)

    # Issue a fresh short-lived single-use token and email the reset link.
    token = PasswordResetToken.create_for(username, purpose=PURPOSE_RESET)
    db.session.add(token)
    db.session.commit()

    base = email_service._public_url()
    # Klartext-Token (transient aus create_for) in den Link; DB hält nur den Hash (M6).
    reset_link = f"{base}/reset/{token.raw_token}"

    # Branded HTML reset mail (same "Kann KI Beratung?" look as the welcome
    # mail). Fire-and-forget; never blocks or raises on SMTP issues.
    email_service.send_password_reset(
        username=username,
        email=recipient,
        reset_link=reset_link,
        ttl_hours=2,
    )

    return _neutral_ok()


@auth_bp.route('/password-reset/reset', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='password_reset')
def perform_password_reset():
    """Exchange a valid RESET token + new password for an Authentik write-through.

    Accepts ``purpose='reset'`` tokens only (NULL/legacy counts as 'reset').
    A magic sign-in token is rejected here even though it lives in the same
    table: sign-in links are re-usable and long-lived by design, so letting one
    change the account password would hand anyone who ever saw the mailed link
    a permanent takeover. Single-use semantics are unchanged.
    """
    # Feature kill-switch: when the admin toggle is off the flow is fully closed,
    # including any in-flight links. Return the uniform invalid-token response so
    # we never reveal whether the feature (or the token) exists.
    if not is_self_service_password_reset_enabled():
        return _invalid_token()

    data = request.get_json(silent=True) or {}
    token_value = (data.get('token') or '').strip()
    new_password = data.get('new_password') or ''

    # M6: in der DB liegt nur der Hash — eingehenden Klartext-Token hashen.
    token_hash = hash_reset_token(token_value) if token_value else ''
    token = (
        PasswordResetToken.query
        .filter(PasswordResetToken.token == token_hash, _IS_RESET_TOKEN)
        .first()
    ) if token_value else None
    if token is None or not token.is_valid():
        return _invalid_token()

    if not new_password or len(new_password) < _MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Passwort muss mindestens {_MIN_PASSWORD_LENGTH} Zeichen haben")

    username = token.username
    now = datetime.utcnow()

    # Atomic single-use reservation. Across multiple gevent workers two concurrent
    # POSTs could both pass the is_valid() read above and each trigger an Authentik
    # write (TOCTOU). Reserving the token with a conditional UPDATE (used_at
    # NULL -> now()) means only the request that gets rowcount == 1 proceeds.
    reserved = (
        PasswordResetToken.query
        .filter(
            PasswordResetToken.token == token_hash,
            _IS_RESET_TOKEN,  # defence in depth — the read above already gated
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .update({PasswordResetToken.used_at: now}, synchronize_session=False)
    )
    db.session.commit()
    if reserved != 1:
        # Lost the race (or token vanished/expired between the read and here).
        return _invalid_token()

    # Write the new password through to Authentik.
    ok, err = AuthentikAdminService.set_password(username, new_password)
    if not ok:
        # Re-open the link for retry: the old password still works, so clear the
        # reservation we just made and let the user try the same link again while
        # it is still valid.
        PasswordResetToken.query.filter(
            PasswordResetToken.token == token_hash
        ).update({PasswordResetToken.used_at: None}, synchronize_session=False)
        db.session.commit()
        logger.warning("Password reset write-through failed for '%s': %s", username, err)
        return jsonify({
            'success': False,
            'code': 'RESET_FAILED',
            'error': 'Das Passwort konnte nicht gesetzt werden. Bitte versuche es erneut. / '
                     'The password could not be set. Please try again.',
        }), 502

    return jsonify({
        'success': True,
        'message': 'Passwort erfolgreich zurückgesetzt. / Password reset successfully.',
    }), 200


@auth_bp.route('/magic-login', methods=['POST'])
@public_endpoint
@handle_api_errors(logger_name='magic_login')
def magic_login():
    """Exchange a magic-login token for an auto-login token bundle.

    Powers the passwordless sign-in link in the QR-join welcome mail and the
    returning-user sign-in mail: the link carries a ``purpose='magic'``
    PasswordResetToken; we set a fresh random password on the account and mint
    an Authentik token so the frontend logs the user straight in. The emailed
    link IS the ownership proof.

    MULTI-USE BY DESIGN (product decision, replaces the earlier single-use
    behaviour): a study participant scans the QR once, receives this mail and
    must be able to click the SAME link again on later visits. The token is
    therefore NOT consumed here — no ``used_at`` stamp — and keeps working
    until it expires. What still bounds it:

    - **TTL** — 168h / 7 days, set at mint time and never extended.
    - **Hashed at rest** — the DB holds only the SHA-256 (M6), so a DB read
      does not yield a working link.
    - **Superseded on re-mint** — a newer magic link for the same account
      retires this one (``email_service._make_magic_login_url``).
    - **Purpose gate** — accepted here only with ``purpose='magic'``. Reset
      tokens (and legacy rows with NULL purpose, which are all dead magic
      links from the pre-M6 hash bug anyway) are rejected, and this token in
      turn cannot be spent on /password-reset/reset to CHANGE a password.

    Note the side effect of the passwordless design: every redemption rotates
    the account password to a fresh random value. A user who has set their own
    password should sign in normally rather than re-click the mailed link.
    """
    import secrets
    data = request.get_json(silent=True) or {}
    token_value = (data.get('token') or '').strip()
    # M6: DB hält nur den Hash — Klartext-Token hashen.
    token_hash = hash_reset_token(token_value) if token_value else ''
    token = (
        PasswordResetToken.query
        .filter(
            PasswordResetToken.token == token_hash,
            PasswordResetToken.purpose == PURPOSE_MAGIC,
        )
        .first()
    ) if token_value else None
    # is_valid() = not superseded and not expired. No reservation UPDATE and no
    # used_at stamp: consuming the token here is exactly what we do NOT want.
    if token is None or not token.is_valid():
        return _invalid_token()

    username = token.username
    password = secrets.token_urlsafe(24)
    ok, err = AuthentikAdminService.set_password(username, password)
    if not ok:
        # Nothing to roll back — the link was never consumed, so it stays
        # usable for a retry on its own.
        logger.warning("Magic-login set_password failed for '%s': %s", username, err)
        return _invalid_token()

    try:
        from routes.authentik_routes import issue_authentik_token
        bundle = issue_authentik_token(username, password)
    except Exception:
        bundle = None
    if not bundle:
        return jsonify({
            'success': False, 'code': 'LOGIN_FAILED',
            'error': 'Anmeldung fehlgeschlagen. Bitte erneut versuchen. / Sign-in failed. Please try again.',
        }), 502

    return jsonify({
        'success': True,
        'username': username,
        'token': bundle,
        'redirect_path': '/evaluation',
    }), 200
