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


def _get_encryption_key() -> bytes:
    env_key = os.environ.get("LLM_PROVIDER_ENCRYPTION_KEY", "").strip()
    if env_key:
        return _derive_key(env_key)

    jwt_secret = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    return _derive_key(jwt_secret)


def encrypt_api_key(api_key: str) -> str:
    try:
        fernet = Fernet(_get_encryption_key())
        encrypted = fernet.encrypt(api_key.encode())
        return encrypted.decode("utf-8")
    except Exception as exc:
        logger.error(f"Failed to encrypt API key: {exc}")
        raise ValueError("Failed to encrypt API key") from exc


def decrypt_api_key(encrypted_key: str) -> str:
    try:
        fernet = Fernet(_get_encryption_key())
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode("utf-8")
    except InvalidToken as exc:
        logger.error("Failed to decrypt API key: invalid token")
        raise ValueError("Failed to decrypt API key: invalid encryption key or corrupted data") from exc
    except Exception as exc:
        logger.error(f"Failed to decrypt API key: {exc}")
        raise ValueError("Failed to decrypt API key") from exc
