"""
Migration script to add metadata_json column to evaluation_items table.

Introduced in commit 6f2acd61 alongside frontend variable substitution for
per-item-header templates (e.g. {{target_style}}). The column was added to
the SQLAlchemy model but never backed by an ALTER TABLE statement, so any
pre-existing DB instance is missing the column. db.create_all() only creates
absent *tables* — it never ALTERs existing ones.

Without this migration: thread.metadata_json returns None →
currentItemMeta.value = {} → _resolveVariables() can't find target_style →
the literal string {{target_style}} is rendered instead of the actual value.

Usage:
    python -m app.db.migrations.migrate_evaluation_items_metadata

Or via Flask shell:
    from app.db.migrations.migrate_evaluation_items_metadata import migrate_evaluation_item_metadata
    migrate_evaluation_item_metadata()
"""

import logging

logger = logging.getLogger(__name__)


def get_migration_sql() -> str:
    """Return the ALTER TABLE statement that adds the missing column."""
    return """
    ALTER TABLE evaluation_items
    ADD COLUMN IF NOT EXISTS metadata_json JSON NULL;
    """


def check_column_exists() -> bool:
    """Return True if metadata_json already exists on evaluation_items."""
    from db.database import db

    result = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME   = 'evaluation_items'
        AND   COLUMN_NAME  = 'metadata_json'
    """))
    return result.scalar() > 0


def migrate_evaluation_item_metadata(dry_run: bool = False) -> dict:
    """
    Add metadata_json (JSON, nullable) to evaluation_items.

    Idempotent — safe to call on a DB that already has the column.

    Args:
        dry_run: If True, checks what would change without modifying the DB.

    Returns:
        Dict describing what was (or would be) done.
    """
    from db.database import db

    already_exists = check_column_exists()

    if already_exists:
        logger.info("[Migration] metadata_json already exists on evaluation_items — nothing to do.")
        return {'dry_run': dry_run, 'column_added': False, 'already_existed': True}

    if dry_run:
        logger.info("[Migration] DRY RUN — metadata_json column is missing but no changes made.")
        return {'dry_run': True, 'column_added': False, 'already_existed': False}

    try:
        db.session.execute(db.text(get_migration_sql()))
        db.session.commit()
        logger.info("[Migration] Added metadata_json column to evaluation_items.")
        return {'dry_run': False, 'column_added': True, 'already_existed': False}
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Migration] Failed to add metadata_json: {e}")
        raise


if __name__ == '__main__':
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

    from main import create_app

    logging.basicConfig(level=logging.INFO)

    app = create_app()
    with app.app_context():
        dry_run = '--dry-run' in sys.argv
        result = migrate_evaluation_item_metadata(dry_run=dry_run)
        print(f"\nResult: {result}")
