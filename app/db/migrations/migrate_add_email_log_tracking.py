"""
Migration: add engagement-tracking columns to ``email_log``.

Backs the Brevo transactional-event webhook (see
``app/routes/webhooks_routes.py`` and ``app/db/models/email_log.py``):

- ``provider_message_id`` — the ``Message-ID`` header Brevo SMTP returns per
  send. Indexed so the webhook can match an ``opened`` / ``click`` event back
  to its exact send row. When unavailable we fall back to matching by
  (recipient_email + subject, most-recent).
- ``opened_at`` / ``clicked_at`` — first-occurrence-wins timestamps set by the
  webhook. NULL = not (yet) opened / clicked.

Idempotent — each column is added only when missing (the project does not rely
on the MariaDB 10.6+ ``ADD COLUMN IF NOT EXISTS`` syntax; we probe
INFORMATION_SCHEMA first, matching the existing migration convention).

Usage:
    python -m app.db.migrations.migrate_add_email_log_tracking
"""

import logging

logger = logging.getLogger(__name__)

_TABLE = 'email_log'

# Order matters only cosmetically; each is added independently when missing.
_COLUMNS = (
    ('provider_message_id', 'VARCHAR(255) NULL'),
    ('opened_at', 'DATETIME NULL'),
    ('clicked_at', 'DATETIME NULL'),
)

# Index on provider_message_id so the webhook lookup stays cheap.
_INDEX = ('ix_email_log_provider_message_id', 'provider_message_id')


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


def migrate_add_email_log_tracking(dry_run: bool = False) -> dict:
    """Add the open/click tracking columns + index. Idempotent."""
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
                f"ALTER TABLE {_TABLE} ADD COLUMN {column} {ddl}"
            ))
            added.append(column)
        except Exception as exc:
            db.session.rollback()
            logger.error("[Migration] Failed to add %s on %s: %s", column, _TABLE, exc)
            raise

    # Index the message-id only after the column exists.
    index_name, index_col = _INDEX
    index_added = False
    if not dry_run and _column_exists(index_col) and not _index_exists(index_name):
        try:
            db.session.execute(db.text(
                f"ALTER TABLE {_TABLE} ADD INDEX {index_name} ({index_col})"
            ))
            index_added = True
        except Exception as exc:
            db.session.rollback()
            logger.error("[Migration] Failed to add index %s on %s: %s", index_name, _TABLE, exc)
            raise

    if (added or index_added) and not dry_run:
        db.session.commit()
        logger.info("[Migration] %s — added columns %s (index_added=%s)",
                    _TABLE, added, index_added)

    return {
        'dry_run': dry_run,
        'columns_added': added,
        'already_existed': already,
        'index_added': index_added,
    }


if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from main import create_app
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    with app.app_context():
        result = migrate_add_email_log_tracking(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
