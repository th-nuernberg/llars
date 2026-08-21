"""
Migration: Hash plaintext API keys with argon2id.

Converts all users with a plaintext api_key to use the api_key_hash column.
After hashing, the plaintext api_key is cleared.

This migration is idempotent: it only processes users that have api_key set
but api_key_hash not set. Safe to run multiple times.

Called during startup from main.py.
"""

import logging

from argon2 import PasswordHasher

logger = logging.getLogger(__name__)

_ph = PasswordHasher()


def migrate_api_keys_to_hash(db) -> int:
    """
    Hash all plaintext API keys and clear the plaintext column.

    Args:
        db: SQLAlchemy database instance

    Returns:
        Number of keys migrated
    """
    from db.models import User

    # Find users with plaintext key but no hash yet
    users_to_migrate = User.query.filter(
        User.api_key.isnot(None),
        User.api_key != '',
        User.api_key_hash.is_(None),
    ).all()

    if not users_to_migrate:
        return 0

    migrated = 0
    for user in users_to_migrate:
        try:
            user.api_key_hash = _ph.hash(user.api_key)
            user.api_key = None
            migrated += 1
        except Exception as e:
            logger.error(f"[Migration] Failed to hash API key for user {user.username}: {e}")
            continue

    if migrated > 0:
        db.session.commit()
        logger.info(f"[Migration] Migrated {migrated} API keys from plaintext to argon2 hash")

    return migrated
