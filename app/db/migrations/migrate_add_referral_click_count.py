"""
Migration: add ``click_count`` to ``referral_links``.

Adds a visit/click counter so admins can compute a funnel
"X Aufrufe -> Y registriert" per referral link. The column is incremented
(best-effort, atomically) on every public
``GET /api/referral/validate/<code_or_slug>`` hit — i.e. whenever the /join
landing page loads.

The default ``0 NOT NULL`` backfills every existing row, so links created
before this migration simply start counting from their next page load.

Usage:
    python -m app.db.migrations.migrate_add_referral_click_count
"""

import logging

logger = logging.getLogger(__name__)


_COLUMNS = (
    ('click_count', 'INT NOT NULL DEFAULT 0'),
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


def migrate_add_referral_click_count(dry_run: bool = False) -> dict:
    """Add the ``click_count`` visit counter column. Idempotent."""
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
        result = migrate_add_referral_click_count(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
