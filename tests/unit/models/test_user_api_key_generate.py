"""
Unit tests for ``UserApiKey.generate_key`` collision retry.

Test IDs: USR-APIKEY-001..003.

The key_prefix column has no UNIQUE constraint (would require a data
migration to add safely on a populated prod table), so the model
defends against an audit-time collision in code: it queries for the
freshly-rolled prefix and re-rolls if it already exists. These tests
exercise that retry loop without touching a live database — they
monkeypatch the ``db.session.query`` fluent chain.
"""

from __future__ import annotations

import pytest

from db.models.user import UserApiKey


class _FakeQuery:
    """Mimics ``db.session.query(...).filter_by(...).first()`` without
    needing a live SQLAlchemy session. ``.first()`` returns whatever
    sits at the head of ``responses``, popping as it goes."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def filter_by(self, **kwargs):
        return self

    def first(self):
        self.calls += 1
        return self.responses.pop(0) if self.responses else None


@pytest.fixture
def patch_session(monkeypatch):
    """Replace ``db.session.query(UserApiKey.id)`` with a fake."""

    holder = {}

    def install(responses):
        fake = _FakeQuery(responses)

        from db.database import db

        def fake_query(_arg):
            return fake

        monkeypatch.setattr(db.session, "query", fake_query)
        holder["fake"] = fake
        return fake

    return install


class TestGenerateKey:
    def test_USR_APIKEY_001_first_attempt_returns(self, patch_session):
        # No collision → return on the first roll, exactly one prefix
        # query was made.
        fake = patch_session([None])
        key, key_hash, key_prefix = UserApiKey.generate_key()

        assert key.startswith("llars_")
        assert len(key_prefix) == 12
        # SHA-256 hex digest is 64 chars; key_hash matches it.
        assert len(key_hash) == 64
        assert fake.calls == 1

    def test_USR_APIKEY_002_collision_retries_then_returns(self, patch_session):
        # Three consecutive "exists" rows, then a clean slot. The fourth
        # attempt should succeed and the loop should have queried 4×.
        fake = patch_session(["row", "row", "row", None])
        key, key_hash, key_prefix = UserApiKey.generate_key()

        assert key_prefix.startswith("llars_")
        assert fake.calls == 4

    def test_USR_APIKEY_003_exhausted_retries_raise(self, patch_session):
        # Five consecutive collisions → the loop gives up rather than
        # silently writing a duplicate prefix.
        patch_session(["row"] * 5)
        with pytest.raises(RuntimeError) as exc:
            UserApiKey.generate_key()
        assert "unique API-key prefix" in str(exc.value)
