"""
Self-service password-reset routes.

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

LLARS stores no usable ``password_hash`` for Authentik-backed users, so the
recipient email is resolved from the Authentik user record, and the password
is only ever written through to Authentik — never to ``User.password_hash``.
"""

import logging
from datetime import datetime, timedelta

from flask import jsonify, request

from auth.decorators import public_endpoint
from decorators.error_handler import handle_api_errors, ValidationError
from routes.auth import auth_bp
from db.database import db
from db.models.password_reset import PasswordResetToken, hash_reset_token
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
    recent = (
        PasswordResetToken.query
        .filter(PasswordResetToken.username == username)
        .filter(PasswordResetToken.created_at >= now - _RESEND_COOLDOWN)
        .first()
    )
    if recent is not None:
        db.session.commit()  # persist the expired-row cleanup above
        return _neutral_ok()

    # Invalidate any still-valid older tokens for this account so only the newest
    # reset link works (one outstanding link at a time — limits the blast radius
    # if an earlier link leaked).
    PasswordResetToken.query.filter(
        PasswordResetToken.username == username,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)

    # Issue a fresh short-lived single-use token and email the reset link.
    token = PasswordResetToken.create_for(username)
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
    """Exchange a valid token + new password for an Authentik write-through."""
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
    token = PasswordResetToken.query.filter_by(token=token_hash).first() if token_value else None
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
    """Exchange a one-time magic-login token for an auto-login token bundle.

    Powers the passwordless sign-in link in the IJCAI welcome mail: the link
    carries a single-use PasswordResetToken; we reserve it atomically, set a
    fresh random password on the account and mint an Authentik token so the
    frontend logs the user straight in. The emailed link IS the ownership proof.
    Single-use + time-limited (token TTL). Bounded to the demo/study accounts the
    welcome mail is sent to.
    """
    import secrets
    data = request.get_json(silent=True) or {}
    token_value = (data.get('token') or '').strip()
    # M6: DB hält nur den Hash — Klartext-Token hashen.
    token_hash = hash_reset_token(token_value) if token_value else ''
    token = PasswordResetToken.query.filter_by(token=token_hash).first() if token_value else None
    if token is None or not token.is_valid():
        return _invalid_token()

    now = datetime.utcnow()
    # Atomic single-use reservation (same TOCTOU guard as the reset flow).
    reserved = (
        PasswordResetToken.query
        .filter(
            PasswordResetToken.token == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .update({PasswordResetToken.used_at: now}, synchronize_session=False)
    )
    db.session.commit()
    if reserved != 1:
        return _invalid_token()

    username = token.username
    password = secrets.token_urlsafe(24)
    ok, err = AuthentikAdminService.set_password(username, password)
    if not ok:
        # Re-open the link so the user can retry while it is still valid.
        PasswordResetToken.query.filter(PasswordResetToken.token == token_hash)\
            .update({PasswordResetToken.used_at: None}, synchronize_session=False)
        db.session.commit()
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
