"""
LLM Provider Secret Encryption

Uses Fernet symmetric encryption with a key derived from LLM_PROVIDER_ENCRYPTION_KEY
or JWT_SECRET_KEY fallback.
"""

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def _derive_key(secret: str) -> bytes:
    key_bytes = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


_DEFAULT_DEV_SECRET = "dev-secret-key-change-in-production"


def _get_encryption_key() -> bytes:
    env_key = os.environ.get("LLM_PROVIDER_ENCRYPTION_KEY", "").strip()
    if env_key:
        return _derive_key(env_key)

    # Fallback chain: JWT_SECRET_KEY → FLASK_SECRET_KEY → default dev key
    jwt_secret = (
        os.environ.get("JWT_SECRET_KEY")
        or os.environ.get("FLASK_SECRET_KEY")
        or _DEFAULT_DEV_SECRET
    )

    # Block default key in production
    if jwt_secret == _DEFAULT_DEV_SECRET and os.environ.get("PROJECT_STATE") == "production":
        raise RuntimeError(
            "CRITICAL: No encryption key found. Set LLM_PROVIDER_ENCRYPTION_KEY, "
            "JWT_SECRET_KEY, or FLASK_SECRET_KEY in production."
        )

    if jwt_secret == _DEFAULT_DEV_SECRET:
        logger.warning("[Encryption] Using default dev key for encryption — set LLM_PROVIDER_ENCRYPTION_KEY in production!")

    return _derive_key(jwt_secret)


def _get_fallback_keys() -> list:
    """
    Zusätzliche Schlüssel, mit denen NUR entschlüsselt wird (nie verschlüsselt).

    Ermöglicht eine zero-downtime Key-Rotation: Während der Umstellung wird der
    NEUE Key als primär gesetzt (ver- + entschlüsseln) und der ALTE als Fallback
    (nur entschlüsseln). So bleiben bereits gespeicherte Chiffrate lesbar, bis die
    Re-Encrypt-Migration durchgelaufen ist — danach kann der Fallback-Env wieder
    entfernt werden. Quelle: ENV LLM_PROVIDER_ENCRYPTION_KEY_FALLBACK
    (kommagetrennt für mehrere Alt-Keys erlaubt).
    """
    raw = os.environ.get("LLM_PROVIDER_ENCRYPTION_KEY_FALLBACK", "").strip()
    keys = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            keys.append(_derive_key(part))
    return keys


def encrypt_api_key(api_key: str) -> str:
    try:
        fernet = Fernet(_get_encryption_key())
        encrypted = fernet.encrypt(api_key.encode())
        return encrypted.decode("utf-8")
    except Exception as exc:
        logger.error(f"Failed to encrypt API key: {exc}")
        raise ValueError("Failed to encrypt API key") from exc


def decrypt_api_key(encrypted_key: str) -> str:
    # Versucht erst den primären Key, dann alle Fallback-Keys (Rotation).
    token = encrypted_key.encode()
    last_invalid = None
    for key in [_get_encryption_key()] + _get_fallback_keys():
        try:
            return Fernet(key).decrypt(token).decode("utf-8")
        except InvalidToken as exc:
            last_invalid = exc
            continue
        except Exception as exc:
            logger.error(f"Failed to decrypt API key: {exc}")
            raise ValueError("Failed to decrypt API key") from exc
    logger.error("Failed to decrypt API key: invalid token (no matching key)")
    raise ValueError(
        "Failed to decrypt API key: invalid encryption key or corrupted data"
    ) from last_invalid


# ---------------------------------------------------------------------------
# Mixed-content wrappers — used for fields that historically stored plain
# text (Tavily API key on chatbot prompt settings) and are being migrated
# to encryption-at-rest without a one-shot data migration.
#
# Format: ``enc:v1:<fernet-token>`` on encrypted rows; anything else is
# treated as a legacy plain value and returned untouched. This lets old
# unencrypted rows keep working while new writes are encrypted, with no
# downtime and no migration script.
# ---------------------------------------------------------------------------


_ENC_PREFIX = "enc:v1:"


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret for at-rest storage.

    Returned string is prefixed with ``enc:v1:`` so :func:`decrypt_secret`
    can tell encrypted rows from legacy plain ones at read time.
    """
    if not plaintext:
        return plaintext
    return _ENC_PREFIX + encrypt_api_key(plaintext)


def decrypt_secret(stored: str) -> str:
    """Decrypt a value previously written with :func:`encrypt_secret`.

    If the value lacks the ``enc:v1:`` prefix it is assumed to be a
    legacy plain value (pre-encryption rollout) and returned as-is.
    Decryption errors are logged and the raw stored string is returned
    so a corrupted Fernet token never silently kills feature access —
    operators see the failure in logs rather than as a 500.
    """
    if not stored:
        return stored
    if not stored.startswith(_ENC_PREFIX):
        return stored  # legacy plain value
    token = stored[len(_ENC_PREFIX):]
    try:
        return decrypt_api_key(token)
    except ValueError:
        logger.warning(
            "[Encryption] decrypt_secret: stored value is prefixed but "
            "could not be decrypted; returning raw stored string"
        )
        return stored


def is_encrypted_secret(stored: str) -> bool:
    """True iff ``stored`` was written by :func:`encrypt_secret`."""
    return bool(stored) and stored.startswith(_ENC_PREFIX)
