"""
Round-trip + legacy-compat tests for the mixed-content secret wrappers
used to migrate ``tavily_api_key`` (and any future at-rest secret) from
plain to encrypted storage without a one-shot migration.

Test IDs: SEC-ENC-001..006.
"""

from __future__ import annotations

import pytest

from services.llm.secret_encryption import (
    decrypt_secret,
    encrypt_secret,
    is_encrypted_secret,
)


class TestRoundTrip:
    def test_SEC_ENC_001_round_trip_recovers_plaintext(self):
        plain = "tvly-abcdefghijklmnopqrstuvwxyz0123456789"
        wrapped = encrypt_secret(plain)
        assert wrapped != plain
        assert wrapped.startswith("enc:v1:")
        assert decrypt_secret(wrapped) == plain

    def test_SEC_ENC_002_each_encrypt_call_yields_fresh_ciphertext(self):
        # Fernet uses a random IV per encrypt. Two encryptions of the
        # same plaintext must differ — anything else would mean the
        # backing implementation lost its IV randomness.
        plain = "tvly-1234"
        a = encrypt_secret(plain)
        b = encrypt_secret(plain)
        assert a != b
        assert decrypt_secret(a) == plain
        assert decrypt_secret(b) == plain


class TestLegacyCompat:
    """Legacy plain values (rows written before encryption rollout) must
    keep working — no migration is required."""

    def test_SEC_ENC_003_plain_value_passes_through(self):
        plain = "tvly-LEGACY"
        # Not prefixed → returned untouched.
        assert decrypt_secret(plain) == plain
        assert is_encrypted_secret(plain) is False

    def test_SEC_ENC_004_empty_string_is_safe(self):
        assert decrypt_secret("") == ""
        assert encrypt_secret("") == ""
        assert is_encrypted_secret("") is False


class TestPrefix:
    def test_SEC_ENC_005_is_encrypted_secret_marker_only(self):
        assert is_encrypted_secret("enc:v1:foo") is True
        assert is_encrypted_secret("enc:v0:foo") is False
        assert is_encrypted_secret("plain-tvly") is False

    def test_SEC_ENC_006_corrupted_token_returns_raw_not_500(self):
        # A prefixed-but-malformed value must NOT raise — it's logged
        # and returned untouched so the caller sees "wrong key" rather
        # than a server crash. Otherwise an operator key rotation
        # would brick every chatbot with web-search enabled.
        bogus = "enc:v1:not-actually-a-valid-fernet-token"
        assert decrypt_secret(bogus) == bogus
