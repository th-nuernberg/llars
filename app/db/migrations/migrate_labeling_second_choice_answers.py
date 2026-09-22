"""
Idempotent startup migration: second_choice_id + answers_json on
item_labeling_evaluations (question-first labeling + second choice).

Purely additive, both columns nullable — classic labeling rows keep their
shape (NULL in both). Run automatically from app/main.py, or by hand:

    python -m app.db.migrations.migrate_labeling_second_choice_answers [--dry-run]
"""

import logging

logger = logging.getLogger(__name__)

TABLE = "item_labeling_evaluations"
COLUMNS = [
    ("second_choice_id", "VARCHAR(255) NULL"),
    ("answers_json", "JSON NULL"),
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


def migrate_labeling_second_choice_answers(dry_run: bool = False) -> dict:
    from db.database import db

    result = {"table": TABLE, "added": [], "changed": False}
    if not _table_exists(TABLE):
        logger.info("[migrate] %s missing — nothing to do", TABLE)
        return result
    for column, ddl in COLUMNS:
        if _column_exists(TABLE, column):
            continue
        if dry_run:
            logger.info("[migrate] would add %s.%s", TABLE, column)
        else:
            db.session.execute(db.text(f"ALTER TABLE {TABLE} ADD COLUMN {column} {ddl}"))
            db.session.commit()
        result["added"].append(column)
        result["changed"] = True
    return result


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.path.insert(0, "app")
    from main import app  # noqa: E402

    with app.app_context():
        print(migrate_labeling_second_choice_answers(dry_run="--dry-run" in sys.argv))
