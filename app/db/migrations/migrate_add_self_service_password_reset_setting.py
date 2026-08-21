"""
Migration: add ``self_service_password_reset_enabled`` to ``system_settings``.

``system_settings`` is a single-row table; ``create_all`` never alters an
existing table, so a new boolean column needs an explicit migration (same
reason as the referral collect-flags). Default FALSE so the self-service
"Passwort vergessen?" link on the login page stays hidden until an admin
turns it on in the admin panel.

Usage:
    python -m app.db.migrations.migrate_add_self_service_password_reset_setting
"""

import logging

logger = logging.getLogger(__name__)


_COLUMNS = (
    ('self_service_password_reset_enabled', 'TINYINT(1) NOT NULL DEFAULT 0'),
)


def _column_exists(column: str) -> bool:
    from db.database import db
    res = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME  = 'system_settings'
        AND   COLUMN_NAME = :col
        AND   TABLE_SCHEMA = DATABASE()
    """), {'col': column})
    return (res.scalar() or 0) > 0


def migrate_add_self_service_password_reset_setting(dry_run: bool = False) -> dict:
    """Add the ``self_service_password_reset_enabled`` toggle. Idempotent."""
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
                f"ALTER TABLE system_settings ADD COLUMN {column} {ddl}"
            ))
            added.append(column)
        except Exception as exc:
            db.session.rollback()
            logger.error("[Migration] Failed to add %s on system_settings: %s", column, exc)
            raise

    if added and not dry_run:
        db.session.commit()
        logger.info("[Migration] system_settings — added columns: %s", added)

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
        result = migrate_add_self_service_password_reset_setting(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
