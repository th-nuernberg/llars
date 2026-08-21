"""
End-to-end-ish unit tests for the self-service / admin password-reset flow.

Covers the three pillars of the feature:

1. ``PasswordResetToken`` model lifecycle — TTL window, expiry, single-use.
2. Self-service routes (``/auth/password-reset/{request,reset}``) — anti-
   enumeration neutrality, feature kill-switch, no-email guard, resend
   cooldown, old-token invalidation, token issuance + mail send, and the
   reset exchange (invalid/expired/used token, weak password, successful
   Authentik write-through, failed write-through re-opening the link).
3. Admin-triggered reset (``/api/admin/users/<u>/send-password-reset`` and
   ``/generate-reset-link``) — token issuance, no-email guard, link shape.

The tests build a self-contained Flask app that mounts the *real* ``auth_bp``
(so the real route handlers run) plus a thin wrapper around the real admin
handlers, and use an in-memory SQLite DB created from the real model metadata.
External effects are mocked: ``AuthentikAdminService`` (no live Authentik),
``email_service.send_password_reset`` (no SMTP), and the feature-flag getter.

NOTE: This module is deliberately independent of ``tests/conftest.py`` — the
password-reset feature is newer than that fixture's model registry, so we wire
up a minimal app here rather than relying on it.
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

# Ensure the app package is importable exactly as the production code expects
# (imports like ``from routes.auth import auth_bp`` are rooted at ``app/``).
_APP_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app')
sys.path.insert(0, os.path.abspath(_APP_DIR))
os.environ.setdefault('TESTING', 'true')

from flask import Flask  # noqa: E402
from db.database import db  # noqa: E402
from db.models.password_reset import (  # noqa: E402
    PasswordResetToken, generate_reset_token, hash_reset_token,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """Minimal Flask app with the real auth_bp + password-reset table."""
    flask_app = Flask(__name__)
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY='test-secret',
    )
    db.init_app(flask_app)

    # Import the real route module so it attaches the handlers to auth_bp,
    # then register the blueprint under /auth (matching production mounting).
    from routes.auth import auth_bp
    import routes.auth.password_reset_routes  # noqa: F401  (attaches routes)

    # Register only once even if the module/blueprint is reused across tests.
    if 'auth' not in flask_app.blueprints:
        flask_app.register_blueprint(auth_bp, url_prefix='/auth')

    with flask_app.app_context():
        # Create just the table under test (avoids importing the full model
        # graph, which is heavier than this feature needs).
        PasswordResetToken.__table__.create(db.engine, checkfirst=True)
        yield flask_app
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def feature_on():
    """Enable the self-service feature flag for the duration of a test."""
    with patch(
        'routes.auth.password_reset_routes.is_self_service_password_reset_enabled',
        return_value=True,
    ):
        yield


def _make_authentik_user(username='alice', email='alice@example.org'):
    return {'pk': 1, 'username': username, 'email': email, 'is_active': True}


# ---------------------------------------------------------------------------
# 1. Model lifecycle
# ---------------------------------------------------------------------------

class TestPasswordResetTokenModel:

    def test_PWRESET_MODEL_001_token_is_url_safe_and_unique(self):
        a, b = generate_reset_token(), generate_reset_token()
        assert a != b
        assert len(a) >= 32

    def test_PWRESET_MODEL_002_create_for_sets_default_ttl(self):
        tok = PasswordResetToken.create_for('alice')
        window = tok.expires_at - tok.created_at
        # Default TTL is 2h (deliberately short for higher-risk reset links).
        assert timedelta(hours=1, minutes=59) < window <= timedelta(hours=2, minutes=1)
        assert tok.used_at is None

    def test_PWRESET_MODEL_003_create_for_honours_custom_ttl(self):
        tok = PasswordResetToken.create_for('alice', ttl_hours=5)
        window = tok.expires_at - tok.created_at
        assert timedelta(hours=4, minutes=59) < window <= timedelta(hours=5, minutes=1)

    def test_PWRESET_MODEL_004_fresh_token_is_valid(self):
        assert PasswordResetToken.create_for('alice').is_valid() is True

    def test_PWRESET_MODEL_005_expired_token_is_invalid(self):
        tok = PasswordResetToken.create_for('alice')
        tok.expires_at = datetime.utcnow() - timedelta(seconds=1)
        assert tok.is_valid() is False

    def test_PWRESET_MODEL_006_used_token_is_invalid(self):
        tok = PasswordResetToken.create_for('alice')
        tok.mark_used()
        assert tok.used_at is not None
        assert tok.is_valid() is False


# ---------------------------------------------------------------------------
# 2a. Self-service: /password-reset/request (anti-enumeration neutrality)
# ---------------------------------------------------------------------------

class TestRequestEndpoint:

    def test_PWRESET_REQ_001_feature_off_returns_neutral_and_sends_nothing(self, app, client):
        with patch(
            'routes.auth.password_reset_routes.is_self_service_password_reset_enabled',
            return_value=False,
        ), patch('routes.auth.password_reset_routes.email_service') as mail:
            resp = client.post('/auth/password-reset/request',
                               json={'email_or_username': 'alice'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        mail.send_password_reset.assert_not_called()
        with app.app_context():
            assert PasswordResetToken.query.count() == 0

    def test_PWRESET_REQ_002_empty_identifier_is_neutral(self, client, feature_on):
        resp = client.post('/auth/password-reset/request', json={'email_or_username': ''})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_PWRESET_REQ_003_unknown_account_is_neutral_no_token(self, app, client, feature_on):
        with patch(
            'routes.auth.password_reset_routes.AuthentikAdminService'
        ) as ak, patch('routes.auth.password_reset_routes.email_service') as mail:
            ak.find_user.return_value = None
            ak.find_user_by_email.return_value = None
            resp = client.post('/auth/password-reset/request',
                               json={'email_or_username': 'ghost@example.org'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        mail.send_password_reset.assert_not_called()
        with app.app_context():
            assert PasswordResetToken.query.count() == 0

    def test_PWRESET_REQ_004_noemail_invalid_account_sends_nothing(self, app, client, feature_on):
        with patch(
            'routes.auth.password_reset_routes.AuthentikAdminService'
        ) as ak, patch('routes.auth.password_reset_routes.email_service') as mail:
            ak.find_user.return_value = _make_authentik_user(email='bob@noemail.invalid')
            resp = client.post('/auth/password-reset/request',
                               json={'email_or_username': 'bob'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        mail.send_password_reset.assert_not_called()
        with app.app_context():
            assert PasswordResetToken.query.count() == 0

    def test_PWRESET_REQ_005_happy_path_issues_token_and_sends_mail(self, app, client, feature_on):
        with patch(
            'routes.auth.password_reset_routes.AuthentikAdminService'
        ) as ak, patch('routes.auth.password_reset_routes.email_service') as mail:
            ak.find_user.return_value = _make_authentik_user()
            mail._public_url.return_value = 'https://llars.example.org'
            resp = client.post('/auth/password-reset/request',
                               json={'email_or_username': 'alice'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        mail.send_password_reset.assert_called_once()
        kwargs = mail.send_password_reset.call_args.kwargs
        assert kwargs['username'] == 'alice'
        assert kwargs['email'] == 'alice@example.org'
        assert '/reset/' in kwargs['reset_link']
        with app.app_context():
            toks = PasswordResetToken.query.all()
            assert len(toks) == 1
            assert toks[0].username == 'alice'
            assert toks[0].is_valid()

    def test_PWRESET_REQ_006_resolves_by_email_when_not_a_username(self, app, client, feature_on):
        with patch(
            'routes.auth.password_reset_routes.AuthentikAdminService'
        ) as ak, patch('routes.auth.password_reset_routes.email_service') as mail:
            ak.find_user.return_value = None  # username lookup misses
            ak.find_user_by_email.return_value = _make_authentik_user()
            mail._public_url.return_value = 'https://llars.example.org'
            resp = client.post('/auth/password-reset/request',
                               json={'email_or_username': 'alice@example.org'})
        assert resp.status_code == 200
        ak.find_user_by_email.assert_called_once()
        mail.send_password_reset.assert_called_once()

    def test_PWRESET_REQ_007_resend_cooldown_suppresses_second_mail(self, app, client, feature_on):
        with app.app_context():
            # Pre-seed a recent token (inside the 2-minute cooldown window).
            db.session.add(PasswordResetToken.create_for('alice'))
            db.session.commit()
        with patch(
            'routes.auth.password_reset_routes.AuthentikAdminService'
        ) as ak, patch('routes.auth.password_reset_routes.email_service') as mail:
            ak.find_user.return_value = _make_authentik_user()
            resp = client.post('/auth/password-reset/request',
                               json={'email_or_username': 'alice'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        # Cooldown active -> no new mail, no second token.
        mail.send_password_reset.assert_not_called()
        with app.app_context():
            assert PasswordResetToken.query.count() == 1

    def test_PWRESET_REQ_008_new_request_invalidates_older_valid_tokens(self, app, client, feature_on):
        with app.app_context():
            # An older valid token, created OUTSIDE the cooldown window so a new
            # request is allowed to proceed and supersede it.
            old = PasswordResetToken.create_for('alice')
            old.created_at = datetime.utcnow() - timedelta(minutes=10)
            db.session.add(old)
            db.session.commit()
            old_token_value = old.token
        with patch(
            'routes.auth.password_reset_routes.AuthentikAdminService'
        ) as ak, patch('routes.auth.password_reset_routes.email_service') as mail:
            ak.find_user.return_value = _make_authentik_user()
            mail._public_url.return_value = 'https://llars.example.org'
            resp = client.post('/auth/password-reset/request',
                               json={'email_or_username': 'alice'})
        assert resp.status_code == 200
        with app.app_context():
            old_row = PasswordResetToken.query.filter_by(token=old_token_value).first()
            assert old_row.used_at is not None  # superseded
            # Exactly one outstanding (valid) token remains.
            valid = [t for t in PasswordResetToken.query.all() if t.is_valid()]
            assert len(valid) == 1
            assert valid[0].token != old_token_value

    def test_PWRESET_REQ_009_expired_rows_are_cleaned_up(self, app, client, feature_on):
        with app.app_context():
            # A fully-expired token for an unrelated account.
            expired = PasswordResetToken.create_for('someone')
            expired.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.add(expired)
            db.session.commit()
        # The opportunistic cleanup runs on the resolved-account path, so drive
        # a real resolution for a *different* account.
        with patch(
            'routes.auth.password_reset_routes.AuthentikAdminService'
        ) as ak, patch('routes.auth.password_reset_routes.email_service') as mail:
            ak.find_user.return_value = _make_authentik_user()
            mail._public_url.return_value = 'https://llars.example.org'
            client.post('/auth/password-reset/request',
                        json={'email_or_username': 'alice'})
        with app.app_context():
            # The expired 'someone' row was dropped; only the fresh 'alice'
            # token remains.
            rows = PasswordResetToken.query.all()
            assert all(r.username == 'alice' for r in rows)
            assert PasswordResetToken.query.filter_by(username='someone').count() == 0


# ---------------------------------------------------------------------------
# 2b. Self-service: /password-reset/reset (token exchange + write-through)
# ---------------------------------------------------------------------------

class TestResetEndpoint:

    def _seed_token(self, app, username='alice', ttl_hours=2, used=False):
        with app.app_context():
            tok = PasswordResetToken.create_for(username, ttl_hours=ttl_hours)
            if used:
                tok.mark_used()
            db.session.add(tok)
            db.session.commit()
            # M6: DB speichert den Hash; der PLAINTEXT-Token geht in Link/POST.
            return tok.raw_token

    def test_PWRESET_RST_001_feature_off_returns_invalid_token(self, app, client):
        token = self._seed_token(app)
        with patch(
            'routes.auth.password_reset_routes.is_self_service_password_reset_enabled',
            return_value=False,
        ):
            resp = client.post('/auth/password-reset/reset',
                               json={'token': token, 'new_password': 'longenough1'})
        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'

    def test_PWRESET_RST_002_unknown_token_is_invalid(self, client, feature_on):
        resp = client.post('/auth/password-reset/reset',
                           json={'token': 'does-not-exist', 'new_password': 'longenough1'})
        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'

    def test_PWRESET_RST_003_expired_token_is_invalid(self, app, client, feature_on):
        token = self._seed_token(app, ttl_hours=2)
        with app.app_context():
            row = PasswordResetToken.query.filter_by(token=hash_reset_token(token)).first()
            row.expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.session.commit()
        resp = client.post('/auth/password-reset/reset',
                           json={'token': token, 'new_password': 'longenough1'})
        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'

    def test_PWRESET_RST_004_used_token_is_invalid(self, app, client, feature_on):
        token = self._seed_token(app, used=True)
        resp = client.post('/auth/password-reset/reset',
                           json={'token': token, 'new_password': 'longenough1'})
        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'

    def test_PWRESET_RST_005_weak_password_rejected_without_consuming_token(self, app, client, feature_on):
        token = self._seed_token(app)
        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            resp = client.post('/auth/password-reset/reset',
                               json={'token': token, 'new_password': 'short'})
        assert resp.status_code == 400  # ValidationError -> 400
        # Token must NOT be consumed by a rejected weak password.
        with app.app_context():
            assert PasswordResetToken.query.filter_by(token=hash_reset_token(token)).first().used_at is None
        ak.set_password.assert_not_called()

    def test_PWRESET_RST_006_happy_path_writes_through_and_consumes_token(self, app, client, feature_on):
        token = self._seed_token(app)
        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            ak.set_password.return_value = (True, None)
            resp = client.post('/auth/password-reset/reset',
                               json={'token': token, 'new_password': 'brandnewpass1'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        ak.set_password.assert_called_once_with('alice', 'brandnewpass1')
        with app.app_context():
            row = PasswordResetToken.query.filter_by(token=hash_reset_token(token)).first()
            assert row.used_at is not None  # single-use: consumed
            assert row.is_valid() is False

    def test_PWRESET_RST_007_token_is_single_use(self, app, client, feature_on):
        token = self._seed_token(app)
        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            ak.set_password.return_value = (True, None)
            first = client.post('/auth/password-reset/reset',
                                json={'token': token, 'new_password': 'brandnewpass1'})
            second = client.post('/auth/password-reset/reset',
                                 json={'token': token, 'new_password': 'anotherpass2'})
        assert first.status_code == 200
        assert second.status_code == 400
        assert second.get_json()['code'] == 'INVALID_TOKEN'
        # The second attempt must not reach Authentik.
        assert ak.set_password.call_count == 1

    def test_PWRESET_RST_008_failed_writethrough_reopens_link(self, app, client, feature_on):
        token = self._seed_token(app)
        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            ak.set_password.return_value = (False, 'Authentik down')
            resp = client.post('/auth/password-reset/reset',
                               json={'token': token, 'new_password': 'brandnewpass1'})
        assert resp.status_code == 502
        assert resp.get_json()['code'] == 'RESET_FAILED'
        # The reservation was rolled back so the same link can be retried.
        with app.app_context():
            row = PasswordResetToken.query.filter_by(token=hash_reset_token(token)).first()
            assert row.used_at is None
            assert row.is_valid() is True

    def test_PWRESET_RST_009_retry_after_transient_failure_succeeds(self, app, client, feature_on):
        token = self._seed_token(app)
        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            ak.set_password.side_effect = [(False, 'transient'), (True, None)]
            fail = client.post('/auth/password-reset/reset',
                               json={'token': token, 'new_password': 'brandnewpass1'})
            ok = client.post('/auth/password-reset/reset',
                             json={'token': token, 'new_password': 'brandnewpass1'})
        assert fail.status_code == 502
        assert ok.status_code == 200
        with app.app_context():
            assert PasswordResetToken.query.filter_by(token=hash_reset_token(token)).first().used_at is not None


# ---------------------------------------------------------------------------
# 3. Admin-triggered reset
# ---------------------------------------------------------------------------

class TestAdminReset:
    """Exercise the admin handlers' core logic directly.

    The HTTP-level permission gate (``@require_permission('admin:users:manage')``)
    is enforced by the decorator stack; here we drive the underlying handler
    logic with the auth/permission layer mocked out, focusing on the
    reset-specific behaviour (no-email guard, token issuance, link shape).
    """

    @pytest.fixture()
    def admin_module(self):
        import routes.users.user_admin_routes as mod
        return mod

    def test_PWRESET_ADMIN_001_send_resets_for_user_with_email(self, app, admin_module):
        with app.app_context():
            with patch.object(admin_module, 'User') as User, \
                 patch('services.authentik_admin_service.AuthentikAdminService') as ak, \
                 patch('services.email_service.send_password_reset') as send, \
                 patch('services.email_service._public_url', return_value='https://llars.example.org'):
                User.query.filter_by.return_value.first.return_value = MagicMock(deleted_at=None)
                ak.find_user.return_value = _make_authentik_user()
                # Call the undecorated function body via the view function.
                resp, status = admin_module.send_password_reset.__wrapped__('alice') \
                    if hasattr(admin_module.send_password_reset, '__wrapped__') \
                    else admin_module.send_password_reset('alice')
            assert status == 200
            send.assert_called_once()
            assert PasswordResetToken.query.filter_by(username='alice').count() == 1
            # Der gemailte Link muss den KLARTEXT tragen, nicht den Hash (M6):
            # find_by_raw hasht selbst — nur mit dem Klartext gibt es einen Treffer.
            mailed_link = send.call_args.kwargs['reset_link']
            raw = mailed_link.rsplit('/', 1)[-1]
            row = PasswordResetToken.find_by_raw(raw)
            assert row is not None and row.username == 'alice'
            assert raw != row.token  # nie den persistierten Hash verschicken

    def test_PWRESET_ADMIN_002_no_email_guard_returns_400(self, app, admin_module):
        with app.app_context():
            with patch.object(admin_module, 'User') as User, \
                 patch('services.authentik_admin_service.AuthentikAdminService') as ak, \
                 patch('services.email_service.send_password_reset') as send:
                User.query.filter_by.return_value.first.return_value = MagicMock(deleted_at=None)
                ak.find_user.return_value = _make_authentik_user(email='x@noemail.invalid')
                fn = getattr(admin_module.send_password_reset, '__wrapped__',
                             admin_module.send_password_reset)
                resp, status = fn('bob')
            assert status == 400
            assert resp.get_json()['code'] == 'NO_EMAIL'
            send.assert_not_called()

    def test_PWRESET_ADMIN_003_generate_reset_link_returns_branded_link(self, app, admin_module):
        with app.app_context():
            with patch.object(admin_module, 'User') as User, \
                 patch('services.email_service._public_url', return_value='https://llars.example.org'):
                User.query.filter_by.return_value.first.return_value = MagicMock(deleted_at=None)
                fn = getattr(admin_module.generate_reset_link, '__wrapped__',
                             admin_module.generate_reset_link)
                resp, status = fn('alice')
            assert status == 200
            link = resp.get_json()['link']
            assert link.startswith('https://llars.example.org/reset/')
            assert PasswordResetToken.query.filter_by(username='alice').count() == 1
            # Link muss den Klartext-Token tragen (nicht den gespeicherten Hash, M6).
            raw = link.rsplit('/', 1)[-1]
            row = PasswordResetToken.find_by_raw(raw)
            assert row is not None and row.username == 'alice'
            assert raw != row.token
