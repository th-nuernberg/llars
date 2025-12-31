"""
Encryption utilities for Zotero API keys.

Uses Fernet symmetric encryption with a key derived from ZOTERO_ENCRYPTION_KEY
environment variable (or falls back to JWT_SECRET_KEY).
"""

import os
import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """
    Get or derive the Fernet encryption key.
    Uses ZOTERO_ENCRYPTION_KEY if set, otherwise derives from JWT_SECRET_KEY.
    """
    # Check for dedicated Zotero encryption key
    zotero_key = os.environ.get('ZOTERO_ENCRYPTION_KEY')
    if zotero_key:
        # Ensure it's a valid Fernet key (32 bytes, base64-encoded = 44 chars)
        if len(zotero_key) == 44:
            return zotero_key.encode()
        # Otherwise derive from provided key
        return _derive_key(zotero_key)

    # Fall back to JWT_SECRET_KEY
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    return _derive_key(jwt_secret)


def _derive_key(secret: str) -> bytes:
    """Derive a Fernet-compatible key from an arbitrary secret string."""
    # Use SHA256 to get 32 bytes, then base64 encode for Fernet
    key_bytes = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt a Zotero API key for storage in the database.

    Args:
        api_key: The plaintext API key

    Returns:
        Encrypted key as a base64-encoded string
    """
    try:
        fernet = Fernet(_get_encryption_key())
        encrypted = fernet.encrypt(api_key.encode())
        return encrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {e}")
        raise ValueError("Failed to encrypt API key") from e


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt a Zotero API key from the database.

    Args:
        encrypted_key: The encrypted key string from the database

    Returns:
        Decrypted plaintext API key

    Raises:
        ValueError: If decryption fails (invalid key or corrupted data)
    """
    try:
        fernet = Fernet(_get_encryption_key())
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode('utf-8')
    except InvalidToken:
        logger.error("Failed to decrypt API key: Invalid token (wrong key or corrupted data)")
        raise ValueError("Failed to decrypt API key: invalid encryption key or corrupted data")
    except Exception as e:
        logger.error(f"Failed to decrypt API key: {e}")
        raise ValueError("Failed to decrypt API key") from e
