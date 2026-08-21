"""
Migration: add ``color`` to ``referral_links``.

Adds a per-link badge/pill color so a referral source has one consistent color
everywhere it is surfaced in LLARS (scenario-team origin pills, origin legends,
admin link list). The column is NULL by default; links without an explicit color
fall back to a deterministic auto-color (see ``ReferralLink.resolved_color``),
so no backfill is required — existing links get a stable color immediately.

Usage:
    python -m app.db.migrations.migrate_add_referral_link_color
"""

import logging

logger = logging.getLogger(__name__)


_COLUMNS = (
    ('color', 'VARCHAR(7) NULL DEFAULT NULL'),
)


def _column_exists(column: str) -> bool:
    from db.database import db
    res = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME  = 'referral_links'
        AND   COLUMN_NAME = :col
        AND   TABLE_SCHEMA = DATABASE()
    """), {'col': column})
    return (res.scalar() or 0) > 0


def migrate_add_referral_link_color(dry_run: bool = False) -> dict:
    """Add the ``color`` badge-color column. Idempotent."""
    from db.database import db

    added = []
    already = []

    for column, ddl in _COLUMNS:
        if _column_exists(column):
            already.append(column)
            continue
        if dry_run:
            continue
        try:
            db.session.execute(db.text(
                f"ALTER TABLE referral_links ADD COLUMN {column} {ddl}"
            ))
            added.append(column)
        except Exception as exc:
            db.session.rollback()
            logger.error("[Migration] Failed to add %s on referral_links: %s", column, exc)
            raise

    if added and not dry_run:
        db.session.commit()
        logger.info("[Migration] referral_links — added columns: %s", added)

    return {
        'dry_run': dry_run,
        'columns_added': added,
        'already_existed': already,
    }


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from main import create_app
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    with app.app_context():
        result = migrate_add_referral_link_color(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
