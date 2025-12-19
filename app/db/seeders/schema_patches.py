"""
Schema Patches (Idempotent)

LLARS uses `db.create_all()` on startup without Alembic migrations.
To keep existing databases compatible, we apply small, idempotent schema patches
for newly introduced columns.
"""

from sqlalchemy import text


def _column_exists(db, table_name: str, column_name: str) -> bool:
    result = db.session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).scalar()
    return bool(result and int(result) > 0)


def _ensure_column(db, table_name: str, column_name: str, column_definition_sql: str) -> bool:
    """
    Ensure a column exists on a table.

    Args:
        db: SQLAlchemy instance
        table_name: DB table name
        column_name: Column to check
        column_definition_sql: Full SQL definition for ADD COLUMN (including the column name)

    Returns:
        True if the column was added, False if it already existed.
    """
    if _column_exists(db, table_name, column_name):
        return False

    db.session.execute(text(f"ALTER TABLE `{table_name}` ADD COLUMN {column_definition_sql}"))
    db.session.commit()
    return True


def apply_schema_patches(db) -> None:
    """Apply required schema patches (safe to run multiple times)."""
    try:
        changed = False

        # Users: account lifecycle & lock state
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="is_active",
            column_definition_sql="`is_active` TINYINT(1) NOT NULL DEFAULT 1",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="deleted_at",
            column_definition_sql="`deleted_at` DATETIME NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="avatar_seed",
            column_definition_sql="`avatar_seed` VARCHAR(32) NULL",
        )

        # Scenarios: per-scenario config + comparison model config
        changed |= _ensure_column(
            db,
            table_name="rating_scenarios",
            column_name="llm1_model",
            column_definition_sql="`llm1_model` VARCHAR(255) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="rating_scenarios",
            column_name="llm2_model",
            column_definition_sql="`llm2_model` VARCHAR(255) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="rating_scenarios",
            column_name="config_json",
            column_definition_sql="`config_json` JSON NULL",
        )

        if changed:
            print("✅ Applied schema patches")
    except Exception as exc:
        db.session.rollback()
        print(f"⚠️  Schema patch failed: {exc}")
        raise
