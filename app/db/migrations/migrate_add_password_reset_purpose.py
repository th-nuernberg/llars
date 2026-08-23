"""
Migration: add ``purpose`` to ``password_reset_tokens``.

``password_reset_tokens`` backs two different kinds of emailed link, and until
this column existed they were indistinguishable — a passwordless sign-in token
could be posted to the password-RESET endpoint (and vice versa). The column
splits them and lets each endpoint gate on its own kind:

- ``'reset'`` — self-service "Passwort vergessen?" link. A single-use
  credential for CHANGING a password; consumed on redemption, 2h TTL.
- ``'magic'`` — passwordless sign-in link from the QR-join welcome mail / the
  returning-user mail. Deliberately RE-USABLE inside its 7-day TTL, never
  consumed on use, only retired when a newer magic link supersedes it.

The default is picked so every pre-existing row keeps its old, stricter
behaviour:

- ``purpose = 'reset'`` → legacy rows stay single-use reset tokens and are
  rejected by the magic-login endpoint. This is safe in practice because all
  legacy magic links were already dead (they shipped the stored hash, not the
  plaintext — fixed separately).

Usage:
    python -m app.db.migrations.migrate_add_password_reset_purpose
"""

import logging

logger = logging.getLogger(__name__)


_TABLE = 'password_reset_tokens'

_COLUMNS = (
    ('purpose', "VARCHAR(16) NOT NULL DEFAULT 'reset'"),
)

# Non-unique index: both endpoints filter on (token_hash, purpose) and the
# invalidate-previous-links UPDATEs filter on (username, purpose).
_INDEXES = (
    ('ix_prt_purpose', 'purpose'),
)


def _column_exists(column: str) -> bool:
    from db.database import db
    res = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME  = :tbl
        AND   COLUMN_NAME = :col
        AND   TABLE_SCHEMA = DATABASE()
    """), {'tbl': _TABLE, 'col': column})
    return (res.scalar() or 0) > 0


def _index_exists(index: str) -> bool:
    from db.database import db
    res = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_NAME  = :tbl
        AND   INDEX_NAME  = :idx
        AND   TABLE_SCHEMA = DATABASE()
    """), {'tbl': _TABLE, 'idx': index})
    return (res.scalar() or 0) > 0


def _table_exists() -> bool:
    from db.database import db
    res = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME  = :tbl
        AND   TABLE_SCHEMA = DATABASE()
    """), {'tbl': _TABLE})
    return (res.scalar() or 0) > 0


def migrate_add_password_reset_purpose(dry_run: bool = False) -> dict:
    """Add the ``purpose`` discriminator column + its index. Idempotent."""
    from db.database import db

    # The table itself is created by migrate_password_reset_tokens_table, which
    # runs earlier at startup. If it is somehow missing there is nothing to
    # alter — report a no-op instead of raising and aborting boot.
    if not _table_exists():
        logger.info("[Migration] %s does not exist yet — skipping purpose column", _TABLE)
        return {
            'dry_run': dry_run,
            'columns_added': [],
            'indexes_added': [],
            'already_existed': [],
            'table_missing': True,
        }

    added = []
    already = []
    indexes_added = []

    for column, ddl in _COLUMNS:
        if _column_exists(column):
            already.append(column)
            continue
        if dry_run:
            continue
        try:
            # NOT NULL DEFAULT 'reset' backfills every existing row in one
            # statement — no separate UPDATE pass needed.
            db.session.execute(db.text(
                f"ALTER TABLE {_TABLE} ADD COLUMN {column} {ddl}"
            ))
            added.append(column)
        except Exception as exc:
            db.session.rollback()
            logger.error("[Migration] Failed to add %s on %s: %s", column, _TABLE, exc)
            raise

    if added and not dry_run:
        db.session.commit()

    # Index comes after the column exists (fresh add or a previous run).
    if _column_exists('purpose') and not dry_run:
        for index, column in _INDEXES:
            if _index_exists(index):
                continue
            try:
                db.session.execute(db.text(
                    f"CREATE INDEX {index} ON {_TABLE} ({column})"
                ))
                db.session.commit()
                indexes_added.append(index)
            except Exception as exc:
                # A missing secondary index only costs a scan on a tiny table —
                # never fail startup over it.
                db.session.rollback()
                logger.warning("[Migration] Could not create %s on %s: %s", index, _TABLE, exc)

    if added or indexes_added:
        logger.info("[Migration] %s — added columns: %s, indexes: %s",
                    _TABLE, added, indexes_added)

    return {
        'dry_run': dry_run,
        'columns_added': added,
        'indexes_added': indexes_added,
        'already_existed': already,
        'table_missing': False,
    }


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from main import create_app
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    with app.app_context():
        result = migrate_add_password_reset_purpose(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
