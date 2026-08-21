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
from db.models.password_reset import PasswordResetToken, hash_reset_token  # noqa: E402
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

    def _spy(user, ttl_hours=2):
        row = real_create_for(user, ttl_hours=ttl_hours)
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
        # The token is consumed by the successful sign-in.
        assert PasswordResetToken.find_by_raw(_token_from_url(url)).used_at is not None

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

    def test_MAGIC_RT_003_token_is_single_use(self, app, client, public_url, authentik_ok):
        ak, _ = authentik_ok
        token = _token_from_url(email_service._make_magic_login_url('alice'))

        first = client.post('/auth/magic-login', json={'token': token})
        second = client.post('/auth/magic-login', json={'token': token})

        assert first.status_code == 200
        assert second.status_code == 400
        assert second.get_json()['code'] == 'INVALID_TOKEN'
        # The replay must not reach Authentik.
        assert ak.set_password.call_count == 1

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

    def test_MAGIC_RT_007_failed_writethrough_reopens_link(self, app, client, public_url):
        """A transient Authentik failure must leave the link usable for a retry."""
        token = _token_from_url(email_service._make_magic_login_url('alice'))
        with patch('routes.auth.password_reset_routes.AuthentikAdminService') as ak:
            ak.set_password.return_value = (False, 'Authentik down')
            resp = client.post('/auth/magic-login', json={'token': token})

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_TOKEN'
        row = PasswordResetToken.find_by_raw(token)
        assert row.used_at is None
        assert row.is_valid() is True
