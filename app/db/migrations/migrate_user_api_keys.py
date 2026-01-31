"""
Migration script to create user_api_keys table.

This table allows users to have multiple API keys with labels,
replacing the single api_key field on the User model.

Usage:
    python -m app.db.migrations.migrate_user_api_keys

Or via Flask shell:
    from app.db.migrations.migrate_user_api_keys import migrate
    migrate()
"""

import logging

logger = logging.getLogger(__name__)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME NULL,
    expires_at DATETIME NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system_key BOOLEAN NOT NULL DEFAULT FALSE,
    scopes VARCHAR(500) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_api_keys_user_id (user_id),
    INDEX idx_user_api_keys_key_hash (key_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


def check_table_exists() -> bool:
    """Check if user_api_keys table already exists."""
    from db.database import db

    result = db.session.execute(db.text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = 'user_api_keys'"
    ))
    return result.scalar() > 0


def migrate(dry_run: bool = False) -> dict:
    """
    Create the user_api_keys table.

    Args:
        dry_run: If True, only shows what would be changed without committing.

    Returns:
        Dict with migration statistics.
    """
    from db.database import db

    if check_table_exists():
        logger.info("Table user_api_keys already exists, skipping creation")
        return {
            'created': False,
            'message': 'Table already exists'
        }

    if dry_run:
        logger.info("DRY RUN - Would create user_api_keys table")
        return {
            'dry_run': True,
            'would_create': True
        }

    try:
        logger.info("Creating user_api_keys table...")
        db.session.execute(db.text(CREATE_TABLE_SQL))
        db.session.commit()
        logger.info("Table user_api_keys created successfully!")

        return {
            'created': True,
            'message': 'Table created successfully'
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"Migration failed: {e}")
        raise


def rollback() -> dict:
    """
    Drop the user_api_keys table (for emergency use).
    """
    from db.database import db

    if not check_table_exists():
        logger.info("Table user_api_keys does not exist, nothing to rollback")
        return {'dropped': False}

    try:
        logger.warning("Dropping user_api_keys table...")
        db.session.execute(db.text("DROP TABLE user_api_keys;"))
        db.session.commit()
        logger.info("Table user_api_keys dropped successfully!")

        return {'dropped': True}

    except Exception as e:
        db.session.rollback()
        logger.error(f"Rollback failed: {e}")
        raise


if __name__ == '__main__':
    import sys
    import os

    # Add app to path for standalone execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

    from main import app

    logging.basicConfig(level=logging.INFO)

    with app.app_context():
        # Check for flags
        dry_run = '--dry-run' in sys.argv
        do_rollback = '--rollback' in sys.argv

        if do_rollback:
            result = rollback()
        else:
            result = migrate(dry_run=dry_run)

        print(f"\nResult: {result}")
