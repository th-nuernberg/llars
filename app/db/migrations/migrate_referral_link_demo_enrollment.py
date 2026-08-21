"""
Migration: referral_links demo-enrollment + configurable signup flow.

Adds three columns that power the IJCAI demo link (one QR -> evaluator in one
demo scenario per evaluation type, plus read-only viewer on their analyses, with
a configurable amount of signup friction):

- ``target_scenario_ids`` (JSON)  -> enroll registrant as ASSESSOR into every id
- ``viewer_scenario_ids``  (JSON)  -> grant read-only manager VIEWER on every id
- ``signup_mode`` (VARCHAR(20))    -> 'full' (legacy) | 'email' | 'instant'

Defaults keep existing links unchanged: both lists NULL, signup_mode 'full'.

Usage:
    python -m app.db.migrations.migrate_referral_link_demo_enrollment
"""

import logging

logger = logging.getLogger(__name__)


_COLUMNS = (
    ('target_scenario_ids', 'JSON NULL'),
    ('viewer_scenario_ids', 'JSON NULL'),
    ("signup_mode", "VARCHAR(20) NOT NULL DEFAULT 'full'"),
    ("default_locale", "VARCHAR(5) NOT NULL DEFAULT 'de'"),
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


def migrate_referral_link_demo_enrollment(dry_run: bool = False) -> dict:
    """Add the demo-enrollment + signup_mode columns. Idempotent."""
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
        result = migrate_referral_link_demo_enrollment(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
