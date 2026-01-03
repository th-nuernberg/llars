"""
Schema Patches (Idempotent)

LLARS uses `db.create_all()` on startup without Alembic migrations.
To keep existing databases compatible, we apply small, idempotent schema patches
for newly introduced columns.

Security Note:
    This module uses dynamic SQL for ALTER TABLE statements. All inputs are
    validated against strict patterns to prevent SQL injection. Only alphanumeric
    identifiers with underscores are allowed. This code only runs at application
    startup with hardcoded values from this file - there is no user input path.
"""

import re
from sqlalchemy import text


# Strict pattern for SQL identifiers: alphanumeric + underscore, must start with letter/underscore
_SQL_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

# Pattern for column definitions: allows common SQL types and constraints
# Matches: `column_name` TYPE[(size)] [NOT NULL] [DEFAULT ...] [UNIQUE] etc.
_COLUMN_DEF_PATTERN = re.compile(
    r'^`[a-zA-Z_][a-zA-Z0-9_]*`\s+'  # Column name in backticks
    r'[A-Z]+',                        # Type name (VARCHAR, INT, etc.)
    re.IGNORECASE
)


def _validate_identifier(name: str, context: str) -> None:
    """Validate that a name is a safe SQL identifier."""
    if not name or not _SQL_IDENTIFIER_PATTERN.match(name):
        raise ValueError(
            f"Invalid SQL identifier for {context}: '{name}'. "
            "Only alphanumeric characters and underscores are allowed."
        )


def _validate_column_definition(definition: str) -> None:
    """Validate that a column definition follows expected SQL patterns."""
    if not definition or not _COLUMN_DEF_PATTERN.match(definition.strip()):
        raise ValueError(
            f"Invalid column definition format: '{definition[:50]}...'. "
            "Must start with backtick-quoted column name followed by SQL type."
        )


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
        table_name: DB table name (validated against SQL identifier pattern)
        column_name: Column to check (validated against SQL identifier pattern)
        column_definition_sql: Full SQL definition for ADD COLUMN (validated format)

    Returns:
        True if the column was added, False if it already existed.

    Raises:
        ValueError: If any parameter fails validation
    """
    # Validate all inputs to prevent SQL injection
    _validate_identifier(table_name, "table_name")
    _validate_identifier(column_name, "column_name")
    _validate_column_definition(column_definition_sql)

    if _column_exists(db, table_name, column_name):
        return False

    db.session.execute(text(f"ALTER TABLE `{table_name}` ADD COLUMN {column_definition_sql}"))
    db.session.commit()
    return True


def _unique_constraint_exists(db, table_name: str, constraint_name: str) -> bool:
    result = db.session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND CONSTRAINT_NAME = :constraint_name
              AND CONSTRAINT_TYPE = 'UNIQUE'
            """
        ),
        {"table_name": table_name, "constraint_name": constraint_name},
    ).scalar()
    return bool(result and int(result) > 0)


def _unique_index_exists(db, table_name: str, column_names: list[str]) -> bool:
    rows = db.session.execute(
        text(
            """
            SELECT INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND NON_UNIQUE = 0
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """
        ),
        {"table_name": table_name},
    ).fetchall()
    if not rows:
        return False

    index_columns: dict[str, list[str]] = {}
    for row in rows:
        index_columns.setdefault(row[0], []).append(row[1])

    for columns in index_columns.values():
        if columns == column_names:
            return True

    return False


def _ensure_unique_constraint(
    db, table_name: str, constraint_name: str, column_names: list[str]
) -> bool:
    """
    Ensure a unique constraint exists on specified columns.

    Args:
        db: SQLAlchemy instance
        table_name: DB table name (validated)
        constraint_name: Name for the constraint (validated)
        column_names: List of column names to include (all validated)

    Returns:
        True if the constraint was added, False if it already existed.

    Raises:
        ValueError: If any parameter fails validation
    """
    # Validate all inputs to prevent SQL injection
    _validate_identifier(table_name, "table_name")
    _validate_identifier(constraint_name, "constraint_name")
    for col in column_names:
        _validate_identifier(col, f"column_name '{col}'")

    if _unique_constraint_exists(db, table_name, constraint_name):
        return False
    if _unique_index_exists(db, table_name, column_names):
        return False

    columns_sql = ", ".join(f"`{column}`" for column in column_names)
    db.session.execute(
        text(
            f"ALTER TABLE `{table_name}` "
            f"ADD CONSTRAINT `{constraint_name}` UNIQUE ({columns_sql})"
        )
    )
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
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="collab_color",
            column_definition_sql="`collab_color` VARCHAR(7) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="avatar_file",
            column_definition_sql="`avatar_file` VARCHAR(255) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="avatar_public_id",
            column_definition_sql="`avatar_public_id` VARCHAR(64) NULL UNIQUE",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="avatar_mime_type",
            column_definition_sql="`avatar_mime_type` VARCHAR(100) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="avatar_updated_at",
            column_definition_sql="`avatar_updated_at` DATETIME NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="avatar_change_count",
            column_definition_sql="`avatar_change_count` INT NOT NULL DEFAULT 0",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="avatar_change_date",
            column_definition_sql="`avatar_change_date` DATE NULL",
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

        # Chatbot conversations/messages: session scoping + agent traces
        changed |= _ensure_unique_constraint(
            db,
            table_name="chatbot_conversations",
            constraint_name="uq_chatbot_session_per_bot",
            column_names=["chatbot_id", "session_id"],
        )
        changed |= _ensure_column(
            db,
            table_name="chatbot_messages",
            column_name="agent_trace",
            column_definition_sql="`agent_trace` JSON NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="chatbot_messages",
            column_name="stream_metadata",
            column_definition_sql="`stream_metadata` JSON NULL",
        )

        # Chatbot prompt settings: agent prompts
        changed |= _ensure_column(
            db,
            table_name="chatbot_prompt_settings",
            column_name="reflection_prompt",
            column_definition_sql="`reflection_prompt` TEXT NOT NULL DEFAULT ''",
        )
        changed |= _ensure_column(
            db,
            table_name="chatbot_prompt_settings",
            column_name="act_system_prompt",
            column_definition_sql="`act_system_prompt` TEXT NOT NULL DEFAULT ''",
        )
        changed |= _ensure_column(
            db,
            table_name="chatbot_prompt_settings",
            column_name="react_system_prompt",
            column_definition_sql="`react_system_prompt` TEXT NOT NULL DEFAULT ''",
        )
        changed |= _ensure_column(
            db,
            table_name="chatbot_prompt_settings",
            column_name="reflact_system_prompt",
            column_definition_sql="`reflact_system_prompt` TEXT NOT NULL DEFAULT ''",
        )

        # LLM models: model type (llm/embedding/reranker)
        added_model_type = _ensure_column(
            db,
            table_name="llm_models",
            column_name="model_type",
            column_definition_sql="`model_type` VARCHAR(50) NOT NULL DEFAULT 'llm'",
        )
        changed |= added_model_type

        # Best-effort backfill for model_type if column exists
        try:
            db.session.execute(
                text(
                    """
                    UPDATE llm_models
                    SET model_type = 'embedding'
                    WHERE model_type = 'llm'
                      AND (
                        model_id LIKE '%embedding%'
                        OR model_id LIKE '%embed%'
                        OR model_id LIKE '%vdr%'
                        OR model_id LIKE '%bge%'
                        OR model_id LIKE '%e5%'
                        OR model_id LIKE '%minilm%'
                      )
                    """
                )
            )
            db.session.execute(
                text(
                    """
                    UPDATE llm_models
                    SET model_type = 'reranker'
                    WHERE model_type = 'llm'
                      AND (
                        model_id LIKE '%rerank%'
                        OR model_id LIKE '%cross-encoder%'
                      )
                    """
                )
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Analytics settings: custom dimensions
        changed |= _ensure_column(
            db,
            table_name="analytics_settings",
            column_name="dimension_route_id",
            column_definition_sql="`dimension_route_id` INT NOT NULL DEFAULT 0",
        )
        changed |= _ensure_column(
            db,
            table_name="analytics_settings",
            column_name="dimension_module_id",
            column_definition_sql="`dimension_module_id` INT NOT NULL DEFAULT 0",
        )
        changed |= _ensure_column(
            db,
            table_name="analytics_settings",
            column_name="dimension_entity_id",
            column_definition_sql="`dimension_entity_id` INT NOT NULL DEFAULT 0",
        )
        changed |= _ensure_column(
            db,
            table_name="analytics_settings",
            column_name="dimension_view_id",
            column_definition_sql="`dimension_view_id` INT NOT NULL DEFAULT 0",
        )
        changed |= _ensure_column(
            db,
            table_name="analytics_settings",
            column_name="dimension_role_id",
            column_definition_sql="`dimension_role_id` INT NOT NULL DEFAULT 0",
        )

        # RAG: embedding provenance
        changed |= _ensure_column(
            db,
            table_name="rag_document_chunks",
            column_name="embedding_dimensions",
            column_definition_sql="`embedding_dimensions` INT NULL",
        )

        # LaTeX Collab: ensure newer columns exist
        changed |= _ensure_column(
            db,
            table_name="latex_documents",
            column_name="content_text",
            column_definition_sql="`content_text` LONGTEXT NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="latex_commits",
            column_name="document_id",
            column_definition_sql="`document_id` INT NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="latex_compile_jobs",
            column_name="created_at",
            column_definition_sql="`created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        )

        # Soft-delete support for git panel (deleted file restore)
        changed |= _ensure_column(
            db,
            table_name="latex_documents",
            column_name="deleted_at",
            column_definition_sql="`deleted_at` DATETIME NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="markdown_documents",
            column_name="deleted_at",
            column_definition_sql="`deleted_at` DATETIME NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="markdown_documents",
            column_name="content_text",
            column_definition_sql="`content_text` TEXT NULL",
        )

        if changed:
            print("✅ Applied schema patches")
    except Exception as exc:
        db.session.rollback()
        print(f"⚠️  Schema patch failed: {exc}")
        raise
