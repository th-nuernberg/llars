"""
Migration: add ``collect_email`` + ``collect_display_name`` to ``referral_links``.

These two flags let a referral-link owner trim the registration form down
to just username + password — useful for closed-network rollouts where the
counsellors don't want to type their real email into a research platform
they're seeing for the first time.

Defaults are picked so existing referral links keep behaving exactly as
before this migration:

- ``collect_email = TRUE``  → email field is shown + required
- ``collect_display_name = TRUE`` → display-name field is shown (still
  optional content-wise; the toggle only controls whether the field
  exists in the form)

Usage:
    python -m app.db.migrations.migrate_referral_link_collect_flags
"""

import logging

logger = logging.getLogger(__name__)


_COLUMNS = (
    ('collect_email', 'TINYINT(1) NOT NULL DEFAULT 1'),
    ('collect_display_name', 'TINYINT(1) NOT NULL DEFAULT 1'),
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


def migrate_referral_link_collect_flags(dry_run: bool = False) -> dict:
    """Add the two boolean toggles. Idempotent."""
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
        result = migrate_referral_link_collect_flags(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
