"""
Migration script to add membership_status fields to scenario_users table.

This migration adds:
- membership_status ENUM('active', 'archived') DEFAULT 'active'
- archived_at DATETIME NULL
- archived_by VARCHAR(255) NULL

The membership_status enables soft-delete functionality:
- ACTIVE: User is visible and can participate
- ARCHIVED: User is hidden but evaluations are preserved for potential restoration

Run this migration BEFORE deploying the new code to production.

Usage:
    python -m app.db.migrations.migrate_membership_status

Or via Flask shell:
    from app.db.migrations.migrate_membership_status import migrate_membership_status
    migrate_membership_status()
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def get_migration_sql() -> Tuple[str, str, str]:
    """
    Get the SQL statements for the migration.

    Returns a tuple of SQL statements to:
    1. Add membership_status column with ENUM type
    2. Add archived_at column
    3. Add archived_by column
    """
    # Add membership_status enum column with default 'ACTIVE'
    # Note: SQLAlchemy uses enum member names (ACTIVE, ARCHIVED), not values
    add_status = """
    ALTER TABLE scenario_users
    ADD COLUMN IF NOT EXISTS membership_status ENUM('ACTIVE', 'ARCHIVED')
    NOT NULL DEFAULT 'ACTIVE';
    """

    # Add archived_at timestamp column
    add_archived_at = """
    ALTER TABLE scenario_users
    ADD COLUMN IF NOT EXISTS archived_at DATETIME NULL;
    """

    # Add archived_by column for tracking who archived
    add_archived_by = """
    ALTER TABLE scenario_users
    ADD COLUMN IF NOT EXISTS archived_by VARCHAR(255) NULL;
    """

    return add_status, add_archived_at, add_archived_by


def check_columns_exist() -> dict:
    """Check if the columns already exist in the table."""
    from db.database import db

    result = db.session.execute(db.text("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'scenario_users'
        AND COLUMN_NAME IN ('membership_status', 'archived_at', 'archived_by')
    """))

    existing = {row[0] for row in result.fetchall()}

    return {
        'membership_status': 'membership_status' in existing,
        'archived_at': 'archived_at' in existing,
        'archived_by': 'archived_by' in existing,
    }


def migrate_membership_status(dry_run: bool = False) -> dict:
    """
    Execute the membership status migration.

    Args:
        dry_run: If True, only shows what would be changed without committing.

    Returns:
        Dict with migration statistics.
    """
    from db.database import db

    # Check existing state
    existing = check_columns_exist()

    logger.info("Current column state:")
    for col, exists in existing.items():
        logger.info(f"  - {col}: {'exists' if exists else 'missing'}")

    columns_to_add = [col for col, exists in existing.items() if not exists]

    if not columns_to_add:
        logger.info("All columns already exist. Nothing to migrate.")
        return {
            'dry_run': dry_run,
            'columns_added': [],
            'already_existed': list(existing.keys()),
        }

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        return {
            'dry_run': True,
            'columns_to_add': columns_to_add,
            'already_existed': [col for col, exists in existing.items() if exists],
        }

    # Execute migration
    add_status, add_archived_at, add_archived_by = get_migration_sql()

    try:
        added = []

        if not existing['membership_status']:
            db.session.execute(db.text(add_status))
            logger.info("Added membership_status column")
            added.append('membership_status')

        if not existing['archived_at']:
            db.session.execute(db.text(add_archived_at))
            logger.info("Added archived_at column")
            added.append('archived_at')

        if not existing['archived_by']:
            db.session.execute(db.text(add_archived_by))
            logger.info("Added archived_by column")
            added.append('archived_by')

        db.session.commit()
        logger.info("Migration completed successfully!")

        # Verify final state
        final_state = check_columns_exist()

        return {
            'dry_run': False,
            'columns_added': added,
            'final_state': final_state,
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"Migration failed: {e}")
        raise


def rollback_membership_status() -> dict:
    """
    Rollback the membership status migration (for emergency use).

    WARNING: This will drop the columns and lose any archived state data!
    """
    from db.database import db

    logger.warning("Rolling back membership status migration...")
    logger.warning("WARNING: This will lose all archived state data!")

    try:
        # Drop columns in reverse order
        db.session.execute(db.text(
            "ALTER TABLE scenario_users DROP COLUMN IF EXISTS archived_by;"
        ))
        db.session.execute(db.text(
            "ALTER TABLE scenario_users DROP COLUMN IF EXISTS archived_at;"
        ))
        db.session.execute(db.text(
            "ALTER TABLE scenario_users DROP COLUMN IF EXISTS membership_status;"
        ))

        db.session.commit()
        logger.info("Rollback completed successfully!")

        return {
            'columns_dropped': ['membership_status', 'archived_at', 'archived_by'],
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"Rollback failed: {e}")
        raise


if __name__ == '__main__':
    import sys
    import os

    # Add app to path for standalone execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

    from main import create_app

    logging.basicConfig(level=logging.INFO)

    app = create_app()
    with app.app_context():
        # Check for flags
        dry_run = '--dry-run' in sys.argv
        rollback = '--rollback' in sys.argv

        if rollback:
            confirm = input("This will DROP columns and lose archived data. Type 'YES' to confirm: ")
            if confirm == 'YES':
                result = rollback_membership_status()
            else:
                print("Rollback cancelled.")
                sys.exit(0)
        else:
            result = migrate_membership_status(dry_run=dry_run)

        print(f"\nResult: {result}")
