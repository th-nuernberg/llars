"""
Migration: add ``collect_email_optional`` to ``referral_links``.

This flag refines the existing ``collect_email`` toggle. When
``collect_email`` is TRUE the email field is shown; ``collect_email_optional``
then decides whether it is *required* (FALSE, the legacy behaviour) or merely
*offered* (TRUE — the field is visible but a registrant may leave it blank,
in which case the server synthesizes a ``@noemail.invalid`` placeholder).

The default is picked so existing referral links keep behaving exactly as
before this migration:

- ``collect_email_optional = FALSE`` → when the email field is shown it stays
  required, identical to the pre-migration form.

Usage:
    python -m app.db.migrations.migrate_add_collect_email_optional
"""

import logging

logger = logging.getLogger(__name__)


_COLUMNS = (
    ('collect_email_optional', 'TINYINT(1) NOT NULL DEFAULT 0'),
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


def migrate_add_collect_email_optional(dry_run: bool = False) -> dict:
    """Add the ``collect_email_optional`` boolean toggle. Idempotent."""
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
        result = migrate_add_collect_email_optional(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
