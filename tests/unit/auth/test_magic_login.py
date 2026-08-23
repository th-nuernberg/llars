"""
Regression tests for the passwordless "magic login" (one-click sign-in) flow.

The flow has two halves that must agree on ONE thing — which value goes in the
emailed link:

1. ``email_service._make_magic_login_url()`` mints a ``PasswordResetToken`` and
   builds ``<public>/auto-login/<token>``.
2. ``POST /auth/magic-login`` receives that token, hashes it and looks the row
   up, then sets a fresh random password and mints an Authentik bundle.

Since the M6 hardening (commit e71648dd) ``PasswordResetToken.token`` stores the
SHA-256 **hash**; the plaintext exists only transiently as ``raw_token``. The
URL builder was missed in that change and shipped the hash, so every emailed
link was dead on arrival (the verifier re-hashes → never matches). These tests
pin the contract from both ends so the two halves cannot drift apart again.

They also pin the deliberate MULTI-USE semantics of magic links: a participant
scans the QR once and re-clicks the SAME mailed link for up to 7 days, so
/auth/magic-login must NOT consume the token. The ``purpose`` column keeps the
two link kinds in this shared table apart — a magic token may not be spent on
/auth/password-reset/reset (that would be a password change), and a reset token
may not sign anyone in.

Test setup mirrors ``test_password_reset.py``: a self-contained Flask app that
mounts the *real* ``auth_bp`` over an in-memory SQLite DB built from the real
model metadata. External effects are mocked — ``AuthentikAdminService`` (no
live Authentik) and ``issue_authentik_token`` (no token exchange).
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

# Ensure the app package is importable exactly as the production code expects
# (imports like ``from routes.auth import auth_bp`` are rooted at ``app/``).
_APP_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app')
sys.path.insert(0, os.path.abspath(_APP_DIR))
os.environ.setdefault('TESTING', 'true')

from flask import Flask  # noqa: E402
from db.database import db  # noqa: E402
from db.models.password_reset import (  # noqa: E402
    PasswordResetToken, hash_reset_token, PURPOSE_RESET, PURPOSE_MAGIC,
)
from services import email_service  # noqa: E402


_PUBLIC_URL = 'https://llars.example.org'


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

    from routes.auth import auth_bp
    import routes.auth.password_reset_routes  # noqa: F401  (attaches routes)

    if 'auth' not in flask_app.blueprints:
        flask_app.register_blueprint(auth_bp, url_prefix='/auth')

    with flask_app.app_context():
        PasswordResetToken.__table__.create(db.engine, checkfirst=True)
        yield flask_app
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def public_url():
    """Pin the public base URL so link assertions are deterministic."""
    with patch.object(email_service, '_public_url', return_value=_PUBLIC_URL):
        yield _PUBLIC_URL


@pytest.fixture()
def authentik_ok():
    """Happy-path Authentik: password write-through + token bundle both succeed."""
    import routes.authentik_routes as ak_routes
    with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak, \
         patch.object(ak_routes, 'issue_authentik_token',
                      return_value={'access_token': 'jwt-abc', 'token_type': 'Bearer'}) as issue:
        ak.set_password.return_value = (True, None)
        yield ak, issue


@pytest.fixture()
def feature_on():
    """Enable the self-service reset feature flag (needed by /password-reset/*)."""
    with patch(
        'routes.auth.password_reset_routes.is_self_service_password_reset_enabled',
        return_value=True,
    ):
        yield


def _token_from_url(url: str) -> str:
    """Extract the token path segment from an /auto-login/<token> URL."""
    return url.rsplit('/auto-login/', 1)[1]


def _mint_capturing_secrets(username='alice'):
    """Mint a magic-login URL, capturing what ``create_for`` actually produced.

    ``raw_token`` is a transient, UNMAPPED instance attribute, so it cannot be
    read back off a re-loaded row (SQLAlchemy's identity map is weak: once
    ``_make_magic_login_url`` returns, the original instance is collected and a
    later query yields a fresh object built from columns only). Spying on
    ``create_for`` is therefore the only way to compare the link against both
    the plaintext and the hash of the very same token.
    """
    minted = {}
    real_create_for = PasswordResetToken.create_for

    def _spy(user, ttl_hours=2, purpose=PURPOSE_RESET):
        row = real_create_for(user, ttl_hours=ttl_hours, purpose=purpose)
        minted['raw'] = row.raw_token
        minted['hash'] = row.token
        return row

    with patch.object(PasswordResetToken, 'create_for', side_effect=_spy):
        url = email_service._make_magic_login_url(username)
    return url, minted


# ---------------------------------------------------------------------------
# 1. URL minting — the value in the link must be the PLAINTEXT token
# ---------------------------------------------------------------------------

class TestMakeMagicLoginUrl:

    def test_MAGIC_URL_001_url_carries_raw_token_not_stored_hash(self, app, public_url):
        """The regression that broke every emailed sign-in link.

        The URL segment must be the transient plaintext; the DB row must hold
        its SHA-256 hash (and therefore must NOT equal the URL segment).
        """
        url, minted = _mint_capturing_secrets('alice')
        assert url is not None
        assert url.startswith(f'{_PUBLIC_URL}/auto-login/')

        url_token = _token_from_url(url)

        # The link carries the plaintext, never the persisted hash.
        assert url_token == minted['raw']
        assert url_token != minted['hash']

        row = PasswordResetToken.query.filter_by(username='alice').one()
        # ...and the stored value is exactly the hash of what is in the link,
        # which is what the verifier recomputes on the way back in.
        assert row.token == hash_reset_token(url_token)
        assert row.token == minted['hash']
        assert len(row.token) == 64  # sha256 hexdigest
        assert PasswordResetToken.find_by_raw(url_token) is row

    def test_MAGIC_URL_002_default_ttl_is_seven_days(self, app, public_url):
        email_service._make_magic_login_url('alice')
        row = PasswordResetToken.query.filter_by(username='alice').one()
        window = row.expires_at - row.created_at
        assert timedelta(days=6, hours=23) < window <= timedelta(days=7, minutes=1)
        assert row.is_valid() is True

    def test_MAGIC_URL_003_minting_invalidates_previous_unused_token(self, app, public_url):
        """Hardening: only the newest emailed link stays live (mirrors the reset flow)."""
        first_url = email_service._make_magic_login_url('alice')
        second_url = email_service._make_magic_login_url('alice')
        assert first_url != second_url

        first_row = PasswordResetToken.find_by_raw(_token_from_url(first_url))
        second_row = PasswordResetToken.find_by_raw(_token_from_url(second_url))

        assert first_row.used_at is not None      # superseded
        assert first_row.is_valid() is False
        assert second_row.used_at is None
        assert second_row.is_valid() is True
        # Both rows are magic links, never reset credentials.
        assert first_row.purpose == PURPOSE_MAGIC
        assert second_row.purpose == PURPOSE_MAGIC

        # Exactly one outstanding link for the account.
        valid = [t for t in PasswordResetToken.query.filter_by(username='alice').all()
                 if t.is_valid()]
        assert len(valid) == 1

    def test_MAGIC_URL_004_invalidation_is_scoped_to_the_account(self, app, public_url):
        """Minting for one user must not kill another user's live link."""
        bob_url = email_service._make_magic_login_url('bob')
        email_service._make_magic_login_url('alice')
        assert PasswordResetToken.find_by_raw(_token_from_url(bob_url)).is_valid() is True

    def test_MAGIC_URL_005_returns_none_on_failure(self, app, public_url):
        """A minting failure must degrade to None (mail still sends, without CTA)."""
        with patch.object(PasswordResetToken, 'create_for', side_effect=RuntimeError('db down')):
            assert email_service._make_magic_login_url('alice') is None


# ---------------------------------------------------------------------------
# 2. Round trip — minted URL must actually be redeemable at /auth/magic-login
# ---------------------------------------------------------------------------

class TestMagicLoginRoundTrip:

    def test_MAGIC_RT_001_minted_url_signs_the_user_in(self, app, client, public_url, authentik_ok):
        ak, issue = authentik_ok
        url = email_service._make_magic_login_url('alice')

        resp = client.post('/auth/magic-login', json={'token': _token_from_url(url)})

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert body['username'] == 'alice'
        assert body['token'] == {'access_token': 'jwt-abc', 'token_type': 'Bearer'}
        assert body['redirect_path'] == '/evaluation'

        # A fresh random password was written through to Authentik for 'alice'.
        ak.set_password.assert_called_once()
        assert ak.set_password.call_args[0][0] == 'alice'
        issue.assert_called_once()
        # The token SURVIVES the sign-in: magic links are multi-use inside their
        # TTL, so nothing may stamp used_at here.
        row = PasswordResetToken.find_by_raw(_token_from_url(url))
        assert row.used_at is None
        assert row.is_valid() is True

    def test_MAGIC_RT_002_stored_hash_is_rejected(self, app, client, public_url, authentik_ok):
        """Direct guard against the original bug: the pre-fix links shipped the
        stored hash, which the verifier re-hashes and can never match."""
        ak, _ = authentik_ok
        email_service._make_magic_login_url('alice')
        stored_hash = PasswordResetToken.query.filter_by(username='alice').one().token

        resp = client.post('/auth/magic-login', json={'token': stored_hash})

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'
        ak.set_password.assert_not_called()

    def test_MAGIC_RT_003_token_is_multi_use_within_its_ttl(self, app, client, public_url, authentik_ok):
        """The product decision: the SAME mailed link signs the user in again.

        A participant scans the QR once and comes back to the same email over
        the following days — every click must work while the token is live.
        """
        ak, issue = authentik_ok
        token = _token_from_url(email_service._make_magic_login_url('alice'))

        first = client.post('/auth/magic-login', json={'token': token})
        second = client.post('/auth/magic-login', json={'token': token})
        third = client.post('/auth/magic-login', json={'token': token})

        for resp in (first, second, third):
            assert resp.status_code == 200
            assert resp.get_json()['success'] is True
            assert resp.get_json()['username'] == 'alice'

        # Each redemption rotates the account password (passwordless design).
        assert ak.set_password.call_count == 3
        assert issue.call_count == 3
        # ...and the link is still live afterwards.
        row = PasswordResetToken.find_by_raw(token)
        assert row.used_at is None
        assert row.is_valid() is True

    def test_MAGIC_RT_004_expired_token_is_rejected(self, app, client, public_url, authentik_ok):
        ak, _ = authentik_ok
        token = _token_from_url(email_service._make_magic_login_url('alice'))
        row = PasswordResetToken.find_by_raw(token)
        row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()

        resp = client.post('/auth/magic-login', json={'token': token})

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'
        ak.set_password.assert_not_called()

    def test_MAGIC_RT_005_superseded_token_is_rejected(self, app, client, public_url, authentik_ok):
        """End-to-end proof of the task-2 hardening: a re-sent welcome mail
        retires the link from the earlier mail."""
        ak, _ = authentik_ok
        old = _token_from_url(email_service._make_magic_login_url('alice'))
        new = _token_from_url(email_service._make_magic_login_url('alice'))

        stale = client.post('/auth/magic-login', json={'token': old})
        assert stale.status_code == 400
        assert stale.get_json()['code'] == 'INVALID_TOKEN'
        ak.set_password.assert_not_called()

        assert client.post('/auth/magic-login', json={'token': new}).status_code == 200

    def test_MAGIC_RT_006_unknown_and_empty_tokens_are_rejected(self, app, client, authentik_ok):
        ak, _ = authentik_ok
        for payload in ({'token': 'does-not-exist'}, {'token': ''}, {}):
            resp = client.post('/auth/magic-login', json=payload)
            assert resp.status_code == 400
            assert resp.get_json()['code'] == 'INVALID_TOKEN'
        ak.set_password.assert_not_called()

    def test_MAGIC_RT_007_failed_writethrough_leaves_link_usable(self, app, client, public_url,
                                                                 authentik_ok):
        """A transient Authentik failure must leave the link usable for a retry.

        Nothing is rolled back any more (the token is never reserved), so this
        now also proves the retry actually succeeds on the same link.
        """
        token = _token_from_url(email_service._make_magic_login_url('alice'))
        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            ak.set_password.return_value = (False, 'Authentik down')
            resp = client.post('/auth/magic-login', json={'token': token})

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'
        row = PasswordResetToken.find_by_raw(token)
        assert row.used_at is None
        assert row.is_valid() is True

        # Authentik recovers → the very same link works.
        assert client.post('/auth/magic-login', json={'token': token}).status_code == 200


# ---------------------------------------------------------------------------
# 3. Purpose gate — the two link kinds share one table and must not mix
# ---------------------------------------------------------------------------

def _legacy_null_purpose(username='alice', ttl_hours=2):
    """Seed a row exactly as it looked BEFORE the ``purpose`` column existed.

    Assigning ``purpose=None`` on the instance is not enough: the column's
    Python-side default would fill in 'reset' at flush time. A raw UPDATE after
    the INSERT is the only way to reproduce a genuine NULL.
    """
    tok = PasswordResetToken.create_for(username, ttl_hours=ttl_hours)
    raw = tok.raw_token
    db.session.add(tok)
    db.session.commit()
    db.session.execute(
        db.text("UPDATE password_reset_tokens SET purpose = NULL WHERE id = :id"),
        {'id': tok.id},
    )
    db.session.commit()
    db.session.expire_all()
    return raw


class TestPurposeGate:

    def test_MAGIC_PURPOSE_001_minted_link_is_stamped_magic(self, app, public_url):
        """The mint side must label the row, or every gate below is a no-op."""
        email_service._make_magic_login_url('alice')
        row = PasswordResetToken.query.filter_by(username='alice').one()
        assert row.purpose == PURPOSE_MAGIC
        assert row.effective_purpose == PURPOSE_MAGIC
        assert row.is_for(PURPOSE_MAGIC) is True
        assert row.is_for(PURPOSE_RESET) is False

    def test_MAGIC_PURPOSE_002_magic_token_cannot_change_the_password(
            self, app, client, public_url, feature_on):
        """Closes the cross-use hole: a re-usable, 7-day sign-in link must not
        double as a credential for CHANGING the account password."""
        token = _token_from_url(email_service._make_magic_login_url('alice'))

        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            ak.set_password.return_value = (True, None)
            resp = client.post('/auth/password-reset/reset',
                               json={'token': token, 'new_password': 'a-new-password'})

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'
        ak.set_password.assert_not_called()
        # ...and the rejection did not quietly retire the sign-in link.
        row = PasswordResetToken.find_by_raw(token)
        assert row.used_at is None
        assert row.is_valid() is True

    def test_MAGIC_PURPOSE_003_reset_token_cannot_sign_anyone_in(
            self, app, client, authentik_ok):
        """The mirror image: a password-reset link must not be a login link."""
        ak, issue = authentik_ok
        tok = PasswordResetToken.create_for('alice')
        raw = tok.raw_token
        db.session.add(tok)
        db.session.commit()
        assert tok.purpose == PURPOSE_RESET

        resp = client.post('/auth/magic-login', json={'token': raw})

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'
        ak.set_password.assert_not_called()
        issue.assert_not_called()

    def test_MAGIC_PURPOSE_004_legacy_null_purpose_counts_as_reset(
            self, app, client, authentik_ok, feature_on):
        """Rows predating the column are treated as the stricter kind.

        Rejecting them at /magic-login costs nothing: every legacy magic link
        was already dead (the URL shipped the stored hash, see MAGIC_RT_002).
        """
        ak, issue = authentik_ok
        raw = _legacy_null_purpose('alice')

        row = PasswordResetToken.find_by_raw(raw)
        assert row.purpose is None
        assert row.effective_purpose == PURPOSE_RESET
        assert row.is_for(PURPOSE_RESET) is True

        # Not a sign-in link...
        magic = client.post('/auth/magic-login', json={'token': raw})
        assert magic.status_code == 400
        assert magic.get_json()['code'] == 'INVALID_TOKEN'
        issue.assert_not_called()

        # ...but still a working RESET link.
        reset = client.post('/auth/password-reset/reset',
                            json={'token': raw, 'new_password': 'a-new-password'})
        assert reset.status_code == 200
        ak.set_password.assert_called_once()

    def test_MAGIC_PURPOSE_005_new_magic_link_spares_a_pending_reset(
            self, app, public_url):
        """Re-sending a welcome mail must not silently kill a reset link the
        user requested moments earlier (the invalidate-UPDATE is purpose-scoped)."""
        pending_reset = PasswordResetToken.create_for('alice')
        reset_raw = pending_reset.raw_token
        db.session.add(pending_reset)
        db.session.commit()

        email_service._make_magic_login_url('alice')

        reset_row = PasswordResetToken.find_by_raw(reset_raw)
        assert reset_row.used_at is None
        assert reset_row.is_valid() is True

    def test_MAGIC_PURPOSE_006_reset_request_spares_a_live_magic_link(
            self, app, client, feature_on):
        """...and the reverse: asking for a password reset must not log the
        participant out of their still-valid 7-day sign-in link."""
        with patch.object(email_service, '_public_url', return_value=_PUBLIC_URL):
            magic_raw = _token_from_url(email_service._make_magic_login_url('alice'))

        # Age the magic row past the resend cooldown window so it cannot be the
        # reason the request short-circuits — we want the real issue path.
        magic_row = PasswordResetToken.find_by_raw(magic_raw)
        magic_row.created_at = datetime.utcnow() - timedelta(minutes=10)
        db.session.commit()

        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak, \
             patch('routes.auth.password_reset_routes.email_service') as mail:
            ak.find_user.return_value = {
                'pk': 1, 'username': 'alice', 'email': 'alice@example.org', 'is_active': True,
            }
            mail._public_url.return_value = _PUBLIC_URL
            resp = client.post('/auth/password-reset/request',
                               json={'email_or_username': 'alice'})

        assert resp.status_code == 200
        # A reset token was issued...
        reset_rows = PasswordResetToken.query.filter_by(
            username='alice', purpose=PURPOSE_RESET).all()
        assert len(reset_rows) == 1
        # ...and the magic link is untouched.
        assert PasswordResetToken.find_by_raw(magic_raw).is_valid() is True

    def test_MAGIC_PURPOSE_007_reset_tokens_stay_single_use(
            self, app, client, feature_on):
        """Contrast to MAGIC_RT_003: only MAGIC links became multi-use."""
        tok = PasswordResetToken.create_for('alice')
        raw = tok.raw_token
        db.session.add(tok)
        db.session.commit()

        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            ak.set_password.return_value = (True, None)
            first = client.post('/auth/password-reset/reset',
                                json={'token': raw, 'new_password': 'a-new-password'})
            second = client.post('/auth/password-reset/reset',
                                 json={'token': raw, 'new_password': 'another-password'})

        assert first.status_code == 200
        assert second.status_code == 400
        assert second.get_json()['code'] == 'INVALID_TOKEN'
        assert ak.set_password.call_count == 1
        assert PasswordResetToken.find_by_raw(raw).used_at is not None
