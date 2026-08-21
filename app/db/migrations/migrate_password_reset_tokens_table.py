"""
Migration: create the ``password_reset_tokens`` table.

Backs the self-service "Passwort vergessen?" flow on the login page. Each row
is a single-use, time-limited token tying a reset link to a username. The
password write-through itself goes to Authentik (LLARS stores no usable
``password_hash`` for Authentik-backed users), so this table only tracks the
LLARS-side token lifecycle: issued → (optionally) used.

Keyed on ``username`` rather than a FK to ``users.id`` — this mirrors the
username-keyed ``referral_registrations`` pattern and avoids a hard FK on a
table whose rows may be soft-deleted.

Usage:
    python -m app.db.migrations.migrate_password_reset_tokens_table
"""

import logging

logger = logging.getLogger(__name__)


_TABLE = 'password_reset_tokens'

_CREATE_DDL = f"""
    CREATE TABLE IF NOT EXISTS {_TABLE} (
        id          INT          NOT NULL AUTO_INCREMENT,
        token       VARCHAR(64)  NOT NULL,
        username    VARCHAR(255) NOT NULL,
        created_at  DATETIME     NOT NULL,
        expires_at  DATETIME     NOT NULL,
        used_at     DATETIME     NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uq_prt_token (token),
        INDEX ix_prt_username (username),
        INDEX ix_prt_expires (expires_at)
    )
"""


def _table_exists() -> bool:
    from db.database import db
    res = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME  = :tbl
        AND   TABLE_SCHEMA = DATABASE()
    """), {'tbl': _TABLE})
    return (res.scalar() or 0) > 0


def migrate_password_reset_tokens_table(dry_run: bool = False) -> dict:
    """Create the ``password_reset_tokens`` table. Idempotent."""
    from db.database import db

    if _table_exists():
        return {'dry_run': dry_run, 'table_created': False, 'already_existed': True}

    if dry_run:
        return {'dry_run': True, 'table_created': False, 'already_existed': False}

    try:
        db.session.execute(db.text(_CREATE_DDL))
        db.session.commit()
        logger.info("[Migration] created table %s", _TABLE)
    except Exception as exc:
        db.session.rollback()
        logger.error("[Migration] Failed to create %s: %s", _TABLE, exc)
        raise

    return {'dry_run': False, 'table_created': True, 'already_existed': False}


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from main import create_app
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    with app.app_context():
        result = migrate_password_reset_tokens_table(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
