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


def _table_exists(db, table_name: str) -> bool:
    _validate_identifier(table_name, "table_name")
    result = db.session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
            """
        ),
        {"table_name": table_name},
    ).scalar()
    return bool(result and int(result) > 0)


def _ensure_table(db, table_name: str, create_sql: str) -> bool:
    _validate_identifier(table_name, "table_name")
    if _table_exists(db, table_name):
        return False
    db.session.execute(text(create_sql))
    db.session.commit()
    return True


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


def _is_column_nullable(db, table_name: str, column_name: str) -> bool:
    """Check if a column allows NULL values."""
    result = db.session.execute(
        text(
            """
            SELECT IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).scalar()
    return result == 'YES'


def _ensure_column_nullable(db, table_name: str, column_name: str, column_type: str) -> bool:
    """
    Ensure a column allows NULL values.

    Args:
        db: SQLAlchemy instance
        table_name: DB table name (validated)
        column_name: Column to modify (validated)
        column_type: SQL type for the column (e.g., 'INT', 'VARCHAR(255)')

    Returns:
        True if the column was modified, False if already nullable or doesn't exist.
    """
    _validate_identifier(table_name, "table_name")
    _validate_identifier(column_name, "column_name")

    if not _column_exists(db, table_name, column_name):
        return False

    if _is_column_nullable(db, table_name, column_name):
        return False

    db.session.execute(
        text(f"ALTER TABLE `{table_name}` MODIFY COLUMN `{column_name}` {column_type} NULL")
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
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="is_ai",
            column_definition_sql="`is_ai` TINYINT(1) NOT NULL DEFAULT 0",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="llm_model_id",
            column_definition_sql="`llm_model_id` VARCHAR(255) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="last_seen_at",
            column_definition_sql="`last_seen_at` DATETIME NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="last_active_at",
            column_definition_sql="`last_active_at` DATETIME NULL",
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

        # LLM models: provider registry linkage
        changed |= _ensure_column(
            db,
            table_name="llm_models",
            column_name="provider_id",
            column_definition_sql="`provider_id` INT NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="llm_models",
            column_name="created_by",
            column_definition_sql="`created_by` VARCHAR(255) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="llm_models",
            column_name="updated_by",
            column_definition_sql="`updated_by` VARCHAR(255) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="llm_models",
            column_name="color",
            column_definition_sql="`color` VARCHAR(32) NULL",
        )

        # LLM providers registry table
        changed |= _ensure_table(
            db,
            table_name="llm_providers",
            create_sql=(
                """
                CREATE TABLE `llm_providers` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `provider_type` VARCHAR(50) NOT NULL,
                    `name` VARCHAR(255) NOT NULL,
                    `base_url` VARCHAR(512) NULL,
                    `api_key_encrypted` TEXT NULL,
                    `config_json` JSON NULL,
                    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
                    `is_default` TINYINT(1) NOT NULL DEFAULT 0,
                    `is_openai_compatible` TINYINT(1) NOT NULL DEFAULT 1,
                    `created_at` DATETIME NOT NULL,
                    `updated_at` DATETIME NOT NULL,
                    PRIMARY KEY (`id`)
                )
                """
            ),
        )

        # LLM model access table
        changed |= _ensure_table(
            db,
            table_name="llm_model_permissions",
            create_sql=(
                """
                CREATE TABLE `llm_model_permissions` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `llm_model_id` INT NOT NULL,
                    `permission_type` VARCHAR(20) NOT NULL,
                    `target_identifier` VARCHAR(255) NOT NULL,
                    `granted_by` VARCHAR(255) NULL,
                    `granted_at` DATETIME NOT NULL,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `unique_llm_model_permission` (`llm_model_id`, `permission_type`, `target_identifier`)
                )
                """
            ),
        )

        # LLM scenario task results (LLM evaluators without user accounts)
        changed |= _ensure_table(
            db,
            table_name="llm_task_results",
            create_sql=(
                """
                CREATE TABLE `llm_task_results` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `scenario_id` INT NOT NULL,
                    `thread_id` INT NOT NULL,
                    `model_id` VARCHAR(255) NOT NULL,
                    `task_type` VARCHAR(50) NOT NULL,
                    `payload_json` JSON NULL,
                    `raw_response` TEXT NULL,
                    `error` TEXT NULL,
                    `created_at` DATETIME NOT NULL,
                    `updated_at` DATETIME NOT NULL,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `uix_llm_task_result` (`scenario_id`, `thread_id`, `model_id`, `task_type`)
                )
                """
            ),
        )

        # System settings: LLM AI logging
        changed |= _ensure_column(
            db,
            table_name="system_settings",
            column_name="llm_ai_log_responses",
            column_definition_sql="`llm_ai_log_responses` TINYINT(1) NOT NULL DEFAULT 1",
        )
        changed |= _ensure_column(
            db,
            table_name="system_settings",
            column_name="llm_ai_log_tasks",
            column_definition_sql="`llm_ai_log_tasks` VARCHAR(255) NOT NULL DEFAULT 'authenticity'",
        )
        changed |= _ensure_column(
            db,
            table_name="system_settings",
            column_name="llm_ai_log_response_max",
            column_definition_sql="`llm_ai_log_response_max` INT NOT NULL DEFAULT 800",
        )
        changed |= _ensure_column(
            db,
            table_name="system_settings",
            column_name="llm_ai_log_prompts",
            column_definition_sql="`llm_ai_log_prompts` TINYINT(1) NOT NULL DEFAULT 0",
        )
        changed |= _ensure_column(
            db,
            table_name="system_settings",
            column_name="llm_ai_log_prompt_max",
            column_definition_sql="`llm_ai_log_prompt_max` INT NOT NULL DEFAULT 800",
        )

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

        # LaTeX Comments: threading support (parent_id for replies)
        changed |= _ensure_column(
            db,
            table_name="latex_comments",
            column_name="parent_id",
            column_definition_sql="`parent_id` INT NULL",
        )
        # LaTeX Comments: author color for collab identification
        changed |= _ensure_column(
            db,
            table_name="latex_comments",
            column_name="author_color",
            column_definition_sql="`author_color` VARCHAR(7) NULL",
        )
        # LaTeX Comments: make range columns nullable for replies (replies don't have ranges)
        changed |= _ensure_column_nullable(
            db,
            table_name="latex_comments",
            column_name="range_start",
            column_type="INT",
        )
        changed |= _ensure_column_nullable(
            db,
            table_name="latex_comments",
            column_name="range_end",
            column_type="INT",
        )

        # AI Assistant settings for LaTeX Collab
        changed |= _ensure_column(
            db,
            table_name="system_settings",
            column_name="ai_assistant_enabled",
            column_definition_sql="`ai_assistant_enabled` TINYINT(1) NOT NULL DEFAULT 1",
        )
        changed |= _ensure_column(
            db,
            table_name="system_settings",
            column_name="ai_assistant_color",
            column_definition_sql="`ai_assistant_color` VARCHAR(7) NOT NULL DEFAULT '#9B59B6'",
        )
        changed |= _ensure_column(
            db,
            table_name="system_settings",
            column_name="ai_assistant_username",
            column_definition_sql="`ai_assistant_username` VARCHAR(50) NOT NULL DEFAULT 'LLARS KI'",
        )

        # =========================================================================
        # Evaluation Assistant: Prompt Templates, LLM Usage Tracking, Budgets
        # =========================================================================

        # Prompt Templates table
        changed |= _ensure_table(
            db,
            table_name="prompt_templates",
            create_sql=(
                """
                CREATE TABLE `prompt_templates` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `name` VARCHAR(100) NOT NULL,
                    `task_type` VARCHAR(50) NOT NULL,
                    `version` VARCHAR(20) NOT NULL DEFAULT '1.0',
                    `system_prompt` TEXT NOT NULL,
                    `user_prompt_template` TEXT NOT NULL,
                    `variables` JSON NULL,
                    `output_schema_version` VARCHAR(20) NOT NULL DEFAULT '1.0',
                    `is_default` TINYINT(1) NOT NULL DEFAULT 0,
                    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
                    `created_by` VARCHAR(100) NULL,
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    INDEX `ix_prompt_templates_task_type` (`task_type`),
                    INDEX `ix_prompt_templates_active` (`is_active`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ),
        )

        # LLM Usage Tracking table
        changed |= _ensure_table(
            db,
            table_name="llm_usage_tracking",
            create_sql=(
                """
                CREATE TABLE `llm_usage_tracking` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `user_id` INT NOT NULL,
                    `scenario_id` INT NULL,
                    `thread_id` INT NULL,
                    `model_id` VARCHAR(100) NOT NULL,
                    `task_type` VARCHAR(50) NOT NULL,
                    `input_tokens` INT NOT NULL DEFAULT 0,
                    `output_tokens` INT NOT NULL DEFAULT 0,
                    `estimated_cost_usd` DECIMAL(10, 6) NULL,
                    `prompt_template_id` INT NULL,
                    `prompt_version` VARCHAR(20) NULL,
                    `processing_time_ms` INT NULL,
                    `success` TINYINT(1) NOT NULL DEFAULT 1,
                    `error_message` TEXT NULL,
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    INDEX `ix_llm_usage_user_id` (`user_id`),
                    INDEX `ix_llm_usage_scenario_id` (`scenario_id`),
                    INDEX `ix_llm_usage_model_id` (`model_id`),
                    INDEX `ix_llm_usage_user_month` (`user_id`, `created_at`),
                    INDEX `ix_llm_usage_model_task` (`model_id`, `task_type`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ),
        )

        # User Token Budgets table
        changed |= _ensure_table(
            db,
            table_name="user_token_budgets",
            create_sql=(
                """
                CREATE TABLE `user_token_budgets` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `user_id` INT NOT NULL,
                    `monthly_token_limit` INT NOT NULL DEFAULT 1000000,
                    `current_month_usage` INT NOT NULL DEFAULT 0,
                    `last_reset_date` DATE NULL,
                    `warning_threshold_percent` INT NOT NULL DEFAULT 80,
                    `is_hard_limit` TINYINT(1) NOT NULL DEFAULT 1,
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `uq_user_token_budget_user` (`user_id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ),
        )

        # LLM Task Results: Add new columns for extended tracking
        changed |= _ensure_column(
            db,
            table_name="llm_task_results",
            column_name="reasoning_json",
            column_definition_sql="`reasoning_json` JSON NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="llm_task_results",
            column_name="prompt_template_id",
            column_definition_sql="`prompt_template_id` INT NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="llm_task_results",
            column_name="prompt_version",
            column_definition_sql="`prompt_version` VARCHAR(20) NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="llm_task_results",
            column_name="input_tokens",
            column_definition_sql="`input_tokens` INT NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="llm_task_results",
            column_name="output_tokens",
            column_definition_sql="`output_tokens` INT NULL",
        )
        changed |= _ensure_column(
            db,
            table_name="llm_task_results",
            column_name="processing_time_ms",
            column_definition_sql="`processing_time_ms` INT NULL",
        )

        # =========================================================================
        # User LLM Providers: Personal API Key Management & Sharing
        # =========================================================================

        # User LLM Providers table
        changed |= _ensure_table(
            db,
            table_name="user_llm_providers",
            create_sql=(
                """
                CREATE TABLE `user_llm_providers` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `user_id` INT NOT NULL,
                    `provider_type` VARCHAR(50) NOT NULL COMMENT 'Provider type: openai, anthropic, gemini, ollama, litellm, custom',
                    `name` VARCHAR(100) NOT NULL COMMENT 'User-friendly name for this provider',
                    `api_key_encrypted` TEXT NULL COMMENT 'Fernet-encrypted API key - NEVER store plaintext',
                    `base_url` VARCHAR(500) NULL COMMENT 'Base URL for self-hosted or proxy providers',
                    `config_json` JSON NULL COMMENT 'Provider-specific configuration',
                    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
                    `is_default` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Default provider for this user',
                    `priority` INT NOT NULL DEFAULT 0 COMMENT 'Priority for fallback ordering (lower = higher priority)',
                    `is_shared` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Whether this provider is shared with others',
                    `share_with_all` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Share with all users (requires permission)',
                    `total_requests` INT NOT NULL DEFAULT 0,
                    `total_tokens` INT NOT NULL DEFAULT 0,
                    `last_used_at` DATETIME NULL,
                    `last_error` TEXT NULL COMMENT 'Last error message (for debugging)',
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    INDEX `ix_user_llm_providers_user_id` (`user_id`),
                    INDEX `ix_user_provider_type` (`user_id`, `provider_type`),
                    UNIQUE KEY `uq_user_provider_name` (`user_id`, `name`),
                    CONSTRAINT `fk_user_llm_provider_user` FOREIGN KEY (`user_id`)
                        REFERENCES `users` (`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ),
        )

        # User LLM Provider Shares table
        changed |= _ensure_table(
            db,
            table_name="user_llm_provider_shares",
            create_sql=(
                """
                CREATE TABLE `user_llm_provider_shares` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `provider_id` INT NOT NULL,
                    `share_type` VARCHAR(20) NOT NULL COMMENT 'Type of share: user, role',
                    `target_identifier` VARCHAR(255) NOT NULL COMMENT 'Username or role name',
                    `can_use` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Can use this provider for API calls',
                    `usage_limit_tokens` INT NULL COMMENT 'Optional token limit per month for this share',
                    `current_month_usage` INT NOT NULL DEFAULT 0,
                    `shared_by` INT NULL,
                    `shared_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `expires_at` DATETIME NULL COMMENT 'Optional expiration date',
                    PRIMARY KEY (`id`),
                    INDEX `ix_user_llm_provider_shares_provider` (`provider_id`),
                    UNIQUE KEY `uq_provider_share_target` (`provider_id`, `share_type`, `target_identifier`),
                    CONSTRAINT `fk_provider_share_provider` FOREIGN KEY (`provider_id`)
                        REFERENCES `user_llm_providers` (`id`) ON DELETE CASCADE,
                    CONSTRAINT `fk_provider_share_user` FOREIGN KEY (`shared_by`)
                        REFERENCES `users` (`id`) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ),
        )

        # =========================================================================
        # Referral System: User-level link creation support
        # =========================================================================

        # Add created_by_user_id column to referral_links for user-owned links
        changed |= _ensure_column(
            db,
            table_name="referral_links",
            column_name="owner_user_id",
            column_definition_sql="`owner_user_id` INT NULL COMMENT 'User who owns this link (NULL = admin-created)'",
        )

        # Add description column to referral_links
        changed |= _ensure_column(
            db,
            table_name="referral_links",
            column_name="description",
            column_definition_sql="`description` TEXT NULL COMMENT 'Additional description for the link'",
        )

        # User Settings/Preferences column on users table
        changed |= _ensure_column(
            db,
            table_name="users",
            column_name="settings_json",
            column_definition_sql="`settings_json` JSON NULL COMMENT 'User preferences (theme, language, etc.)'",
        )

        # =========================================================================
        # Scenario Invitations: Status tracking for user invitations
        # =========================================================================

        # Invitation status for scenario users (ACCEPTED, REJECTED, PENDING)
        # NOTE: SQLAlchemy Enum uses member NAMES, not values - must be uppercase
        changed |= _ensure_column(
            db,
            table_name="scenario_users",
            column_name="invitation_status",
            column_definition_sql="`invitation_status` ENUM('ACCEPTED', 'REJECTED', 'PENDING') NOT NULL DEFAULT 'ACCEPTED'",
        )
        # When the user was invited
        changed |= _ensure_column(
            db,
            table_name="scenario_users",
            column_name="invited_at",
            column_definition_sql="`invited_at` DATETIME NULL",
        )
        # When the user responded to the invitation
        changed |= _ensure_column(
            db,
            table_name="scenario_users",
            column_name="responded_at",
            column_definition_sql="`responded_at` DATETIME NULL",
        )
        # Who invited the user (username)
        changed |= _ensure_column(
            db,
            table_name="scenario_users",
            column_name="invited_by",
            column_definition_sql="`invited_by` VARCHAR(255) NULL",
        )

        # =========================================================================
        # AI Field Assist: Prompt Templates for AI-Assisted Form Fields
        # =========================================================================

        # Field Prompt Templates table
        changed |= _ensure_table(
            db,
            table_name="field_prompt_templates",
            create_sql=(
                """
                CREATE TABLE `field_prompt_templates` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `field_key` VARCHAR(100) NOT NULL COMMENT 'Unique key: {module}.{entity}.{field}',
                    `display_name` VARCHAR(200) NOT NULL COMMENT 'Human-readable name',
                    `description` TEXT NULL COMMENT 'Help text for admins',
                    `system_prompt` TEXT NOT NULL COMMENT 'System prompt for LLM',
                    `user_prompt_template` TEXT NOT NULL COMMENT 'User prompt with {variables}',
                    `context_variables` JSON NULL COMMENT 'Expected context variables',
                    `max_tokens` INT NOT NULL DEFAULT 200,
                    `temperature` FLOAT NOT NULL DEFAULT 0.7,
                    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `uq_field_prompt_key` (`field_key`),
                    INDEX `ix_field_prompt_active` (`is_active`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ),
        )

        # =========================================================================
        # Multi-Dimensional Rating: New generalized rating system
        # =========================================================================

        # Item Dimension Ratings table (for generalized multi-dimensional ratings)
        changed |= _ensure_table(
            db,
            table_name="item_dimension_ratings",
            create_sql=(
                """
                CREATE TABLE `item_dimension_ratings` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `user_id` INT NOT NULL,
                    `item_id` INT NOT NULL,
                    `scenario_id` INT NOT NULL,
                    `dimension_ratings` JSON NOT NULL COMMENT 'Dict of dimension_id: score, e.g. {"coherence": 4, "fluency": 5}',
                    `overall_score` FLOAT NULL COMMENT 'Calculated weighted average',
                    `feedback` TEXT NULL COMMENT 'Optional user feedback',
                    `status` ENUM('NOT_STARTED', 'PROGRESSING', 'DONE') NOT NULL DEFAULT 'NOT_STARTED',
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    INDEX `ix_item_dim_ratings_user` (`user_id`),
                    INDEX `ix_item_dim_ratings_item` (`item_id`),
                    INDEX `ix_item_dim_ratings_scenario` (`scenario_id`),
                    UNIQUE KEY `uix_user_item_scenario_dim_rating` (`user_id`, `item_id`, `scenario_id`),
                    CONSTRAINT `fk_item_dim_rating_user` FOREIGN KEY (`user_id`)
                        REFERENCES `users` (`id`) ON DELETE CASCADE,
                    CONSTRAINT `fk_item_dim_rating_item` FOREIGN KEY (`item_id`)
                        REFERENCES `evaluation_items` (`item_id`) ON DELETE CASCADE,
                    CONSTRAINT `fk_item_dim_rating_scenario` FOREIGN KEY (`scenario_id`)
                        REFERENCES `rating_scenarios` (`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ),
        )

        # Table: item_labeling_evaluations (Labeling evaluations for text classification)
        changed |= _ensure_table(
            db,
            table_name="item_labeling_evaluations",
            create_sql=(
                """
                CREATE TABLE `item_labeling_evaluations` (
                    `id` INT NOT NULL AUTO_INCREMENT,
                    `user_id` INT NOT NULL,
                    `item_id` INT NOT NULL,
                    `scenario_id` INT NOT NULL,
                    `category_id` VARCHAR(255) NULL COMMENT 'Selected category ID from scenario config',
                    `is_unsure` TINYINT(1) NOT NULL DEFAULT 0,
                    `feedback` TEXT NULL,
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    INDEX `ix_labeling_eval_user` (`user_id`),
                    INDEX `ix_labeling_eval_item` (`item_id`),
                    INDEX `ix_labeling_eval_scenario` (`scenario_id`),
                    UNIQUE KEY `uix_user_item_scenario_labeling` (`user_id`, `item_id`, `scenario_id`),
                    CONSTRAINT `fk_labeling_eval_user` FOREIGN KEY (`user_id`)
                        REFERENCES `users` (`id`) ON DELETE CASCADE,
                    CONSTRAINT `fk_labeling_eval_item` FOREIGN KEY (`item_id`)
                        REFERENCES `evaluation_items` (`item_id`) ON DELETE CASCADE,
                    CONSTRAINT `fk_labeling_eval_scenario` FOREIGN KEY (`scenario_id`)
                        REFERENCES `rating_scenarios` (`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ),
        )

        # =========================================================================
        # Provider-Prefix Routing: Migrate model IDs to prefixed format
        # =========================================================================
        changed |= _migrate_model_id_prefixes(db)

        if changed:
            print("✅ Applied schema patches")
    except Exception as exc:
        db.session.rollback()
        print(f"⚠️  Schema patch failed: {exc}")
        raise


def _migrate_model_id_prefixes(db) -> bool:
    """
    Idempotent migration: add provider prefixes to LLM model IDs.

    Maps:
      gpt-5-nano → OpenAI/gpt-5-nano
      gpt-5      → OpenAI/gpt-5
      gpt-5.2    → OpenAI/gpt-5.2
      mistralai/Mistral-Small-3.2-24B-Instruct-2506 → LiteLLM/mistralai/...
      mistralai/Magistral-Small-2509                 → LiteLLM/mistralai/...

    Skips rows that already have the prefix (idempotent).
    Does NOT touch embedding/reranker model IDs.
    """
    PREFIX_MAP = {
        'gpt-5-nano': 'OpenAI/gpt-5-nano',
        'gpt-5': 'OpenAI/gpt-5',
        'gpt-5.2': 'OpenAI/gpt-5.2',
        'mistralai/Mistral-Small-3.2-24B-Instruct-2506': 'LiteLLM/mistralai/Mistral-Small-3.2-24B-Instruct-2506',
        'mistralai/Magistral-Small-2509': 'LiteLLM/mistralai/Magistral-Small-2509',
    }

    changed = False
    try:
        for old_id, new_id in PREFIX_MAP.items():
            # 1. llm_models.model_id
            result = db.session.execute(
                text("UPDATE llm_models SET model_id = :new WHERE model_id = :old"),
                {"old": old_id, "new": new_id},
            )
            if result.rowcount > 0:
                changed = True
                print(f"  [Prefix Migration] llm_models: {old_id} → {new_id}")

            # 2. generated_outputs.llm_model_name
            if _column_exists(db, 'generated_outputs', 'llm_model_name'):
                result = db.session.execute(
                    text("UPDATE generated_outputs SET llm_model_name = :new WHERE llm_model_name = :old"),
                    {"old": old_id, "new": new_id},
                )
                if result.rowcount > 0:
                    changed = True

            # 3. llm_usage_tracking.model_id
            if _table_exists(db, 'llm_usage_tracking'):
                result = db.session.execute(
                    text("UPDATE llm_usage_tracking SET model_id = :new WHERE model_id = :old"),
                    {"old": old_id, "new": new_id},
                )
                if result.rowcount > 0:
                    changed = True

            # 4. users.llm_model_id
            if _column_exists(db, 'users', 'llm_model_id'):
                result = db.session.execute(
                    text("UPDATE users SET llm_model_id = :new WHERE llm_model_id = :old"),
                    {"old": old_id, "new": new_id},
                )
                if result.rowcount > 0:
                    changed = True

            # 5. chatbots.model_name
            if _column_exists(db, 'chatbots', 'model_name'):
                result = db.session.execute(
                    text("UPDATE chatbots SET model_name = :new WHERE model_name = :old"),
                    {"old": old_id, "new": new_id},
                )
                if result.rowcount > 0:
                    changed = True

            # 6. llm_task_results.model_id
            if _table_exists(db, 'llm_task_results'):
                result = db.session.execute(
                    text("UPDATE llm_task_results SET model_id = :new WHERE model_id = :old"),
                    {"old": old_id, "new": new_id},
                )
                if result.rowcount > 0:
                    changed = True

        # 7. generation_jobs.config_json["llm_models"] (JSON array)
        if _table_exists(db, 'generation_jobs') and _column_exists(db, 'generation_jobs', 'config_json'):
            for old_id, new_id in PREFIX_MAP.items():
                # Use JSON_SEARCH to find and replace within llm_models arrays
                result = db.session.execute(
                    text(
                        """
                        UPDATE generation_jobs
                        SET config_json = JSON_REPLACE(
                            config_json,
                            REPLACE(
                                JSON_UNQUOTE(JSON_SEARCH(config_json, 'one', :old, NULL, '$.llm_models')),
                                '"', ''
                            ),
                            :new
                        )
                        WHERE JSON_SEARCH(config_json, 'one', :old2, NULL, '$.llm_models') IS NOT NULL
                        """
                    ),
                    {"old": old_id, "new": new_id, "old2": old_id},
                )
                if result.rowcount > 0:
                    changed = True
                    print(f"  [Prefix Migration] generation_jobs config_json: {old_id} → {new_id}")

        if changed:
            db.session.commit()
            print("  [Prefix Migration] Model ID prefix migration completed")
        else:
            print("  [Prefix Migration] No model IDs to migrate (already prefixed or empty)")

    except Exception as exc:
        db.session.rollback()
        print(f"  ⚠️ Prefix migration failed (non-fatal): {exc}")

    return changed
