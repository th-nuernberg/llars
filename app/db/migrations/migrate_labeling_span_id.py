"""
Migration: add `span_id` to the three labeling-related tables.

Why
---
The conversation-labeling type (function_type 9) stores one vote PER SPAN of a
conversation, where the classic labeling type (7) stores one vote per item. All
three tables that key on "one row per case" therefore need a span dimension:

    item_labeling_evaluations   uix_user_item_scenario_labeling
    labeling_copilot_logs       uix_user_item_scenario_copilot_log
    evaluation_item_timings     uix_user_item_scenario_timing

The third one is easy to miss and would fail silently: the first span of a
conversation writes the timing row and every following span collides with the
unique key, so "time per span" — the measurement the whole efficiency argument
rests on — would never be recorded.

Design
------
`span_id VARCHAR(64) NOT NULL DEFAULT ''`, empty string = "the whole item".

NOT NULL is load-bearing, not cosmetic: MariaDB/MySQL treat NULL values in a
unique key as distinct from one another, so a nullable column would quietly
DISABLE the duplicate protection for every existing (classic) row. With the
empty-string default those rows keep exactly the guarantee they had before, and
the migration stays purely additive — no backfill, no rewriting of study data.

The index swap happens inside a SINGLE `ALTER TABLE` per table. Dropping and
re-adding in two statements would open a window in which duplicates could be
inserted.

Idempotent: safe to run repeatedly. Both the column and the index are checked
against INFORMATION_SCHEMA first.

Usage:
    python -m app.db.migrations.migrate_labeling_span_id [--dry-run]
"""

import logging

logger = logging.getLogger(__name__)

# (table, old unique index name, new unique index name)
_TARGETS = [
    (
        "item_labeling_evaluations",
        "uix_user_item_scenario_labeling",
        "uix_user_item_scenario_span_labeling",
    ),
    (
        "labeling_copilot_logs",
        "uix_user_item_scenario_copilot_log",
        "uix_user_item_scenario_span_copilot_log",
    ),
    (
        "evaluation_item_timings",
        "uix_user_item_scenario_timing",
        "uix_user_item_scenario_span_timing",
    ),
]


def _table_exists(table: str) -> bool:
    from db.database import db

    result = db.session.execute(
        db.text(
            """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table
            """
        ),
        {"table": table},
    )
    return (result.scalar() or 0) > 0


def _column_exists(table: str, column: str) -> bool:
    from db.database import db

    result = db.session.execute(
        db.text(
            """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = :table
              AND COLUMN_NAME  = :column
            """
        ),
        {"table": table, "column": column},
    )
    return (result.scalar() or 0) > 0


def _index_exists(table: str, index: str) -> bool:
    from db.database import db

    result = db.session.execute(
        db.text(
            """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = :table
              AND INDEX_NAME   = :index
            """
        ),
        {"table": table, "index": index},
    )
    return (result.scalar() or 0) > 0


def _migrate_table(table: str, old_index: str, new_index: str, dry_run: bool) -> dict:
    """Add span_id + swap the unique key for one table. Returns what it did."""
    from db.database import db

    state = {
        "table": table,
        "column_added": False,
        "index_swapped": False,
        "skipped": None,
    }

    if not _table_exists(table):
        # Fresh install: db.create_all() / schema_patches build the table with
        # the final shape already, so there is nothing to migrate.
        state["skipped"] = "table_missing"
        return state

    needs_column = not _column_exists(table, "span_id")
    needs_index = _index_exists(table, old_index) and not _index_exists(table, new_index)

    if not needs_column and not needs_index:
        state["skipped"] = "already_current"
        return state

    if dry_run:
        state["skipped"] = "dry_run"
        state["column_added"] = needs_column
        state["index_swapped"] = needs_index
        return state

    # Build ONE statement so the unique key is never absent in between.
    clauses = []
    if needs_column:
        clauses.append("ADD COLUMN span_id VARCHAR(64) NOT NULL DEFAULT ''")
    if needs_index:
        clauses.append(f"DROP INDEX {old_index}")
        clauses.append(
            f"ADD UNIQUE KEY {new_index} (user_id, item_id, scenario_id, span_id)"
        )

    sql = f"ALTER TABLE {table} " + ", ".join(clauses)

    try:
        db.session.execute(db.text(sql))
        db.session.commit()
        state["column_added"] = needs_column
        state["index_swapped"] = needs_index
        logger.info("[Migration] %s: %s", table, ", ".join(clauses))
    except Exception as exc:
        db.session.rollback()
        logger.error("[Migration] Failed on %s: %s", table, exc)
        raise

    return state


def migrate_labeling_span_id(dry_run: bool = False) -> dict:
    """
    Add span_id + extend the unique key on all three labeling tables.

    Idempotent — safe on a DB that is already migrated.

    Returns:
        {'dry_run': bool, 'tables': [per-table state, ...], 'changed': bool}
    """
    results = [
        _migrate_table(table, old_index, new_index, dry_run)
        for table, old_index, new_index in _TARGETS
    ]
    changed = any(r["column_added"] or r["index_swapped"] for r in results)
    return {"dry_run": dry_run, "tables": results, "changed": changed}


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    )

    from main import create_app

    logging.basicConfig(level=logging.INFO)

    app = create_app()
    with app.app_context():
        result = migrate_labeling_span_id(dry_run="--dry-run" in sys.argv)
        print(f"\nResult: {result}")
