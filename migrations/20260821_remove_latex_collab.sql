-- Migration: Remove LaTeX Collab feature (incl. Zotero + AI Writing Assistant)
-- Date: 2026-08-21
-- Description: Drops the eight latex_* tables plus the two subsystems that only
--              existed to serve them: the Zotero integration (wrote .bib files
--              into LaTeX workspaces) and the AI Writing Assistant (its tables
--              FK latex_documents). Also removes the paper -> latex_workspace
--              link, the LaTeX-comment-AI settings columns and the four
--              feature:latex_collab:* permissions.
--
--              Markdown Collab is NOT affected (separate markdown_* tables).
--              papers.overleaf_url is KEPT — it is a plain external link field
--              and has nothing to do with the internal LaTeX workspaces.

-- ---------------------------------------------------------------------------
-- 1. AI Writing Assistant tables
--    ai_chat_messages.session_id -> ai_chat_sessions.id, so messages go first.
--    ai_chat_sessions / ai_citation_ignores both FK latex_documents.id, which
--    is why they must be gone before section 4 touches the latex tables.
--    ai_usage_tracking only references users.id and has no dependants.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS ai_chat_messages;
DROP TABLE IF EXISTS ai_chat_sessions;
DROP TABLE IF EXISTS ai_citation_ignores;
DROP TABLE IF EXISTS ai_usage_tracking;

-- ---------------------------------------------------------------------------
-- 2. Zotero integration tables
--    zotero_sync_logs.library_id -> workspace_zotero_libraries.id -> both
--    zotero_connections.id and latex_workspaces/latex_documents. Dropped
--    leaf-first so the order holds even with FK checks enabled.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS zotero_sync_logs;
DROP TABLE IF EXISTS workspace_zotero_libraries;
DROP TABLE IF EXISTS zotero_connections;

-- ---------------------------------------------------------------------------
-- 3. papers.latex_workspace_id
--    The column exists in two flavours depending on how the DB was built:
--      * created by SQLAlchemy create_all() -> has a real FK constraint with an
--        auto-generated name (papers_ibfk_N), which differs per database;
--      * added later by schema_patches._ensure_column() -> plain INT, no FK.
--    DROP FOREIGN KEY IF EXISTS still needs a literal name, so the constraint
--    name is looked up in information_schema and dropped via dynamic SQL; if no
--    constraint exists the statement degrades to a harmless SELECT. Only then
--    is the column itself dropped (DROP COLUMN also removes the FK index).
--    papers.overleaf_url is deliberately untouched.
-- ---------------------------------------------------------------------------
SET @papers_fk = (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'papers'
      AND COLUMN_NAME = 'latex_workspace_id'
      AND REFERENCED_TABLE_NAME IS NOT NULL
    LIMIT 1
);
SET @papers_fk_sql = IF(
    @papers_fk IS NULL,
    'SELECT ''papers.latex_workspace_id has no FK constraint'' AS info',
    CONCAT('ALTER TABLE `papers` DROP FOREIGN KEY `', @papers_fk, '`')
);
PREPARE drop_papers_fk FROM @papers_fk_sql;
EXECUTE drop_papers_fk;
DEALLOCATE PREPARE drop_papers_fk;

ALTER TABLE papers DROP COLUMN IF EXISTS latex_workspace_id;

-- ---------------------------------------------------------------------------
-- 4. LaTeX Collab tables
--    These cannot be ordered FK-safely: latex_workspaces.main_document_id ->
--    latex_documents.id and latex_workspaces.latest_compile_job_id ->
--    latex_compile_jobs.id, while both children FK latex_workspaces.id back
--    (SQLAlchemy declares them use_alter/post_update precisely because of that
--    cycle). FK enforcement is therefore disabled for the duration of the
--    drops. This is safe here because every table in the cycle is being
--    removed — nothing is left holding a dangling reference afterwards.
--    Sections 1-3 already removed the only outside referrers (ai_*, zotero_*,
--    papers), so the cycle is fully self-contained at this point.
-- ---------------------------------------------------------------------------
SET @old_fk_checks = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS latex_comments;
DROP TABLE IF EXISTS latex_compile_jobs;
DROP TABLE IF EXISTS latex_commits;
DROP TABLE IF EXISTS latex_workspace_access_requests;
DROP TABLE IF EXISTS latex_workspace_members;
DROP TABLE IF EXISTS latex_documents;
DROP TABLE IF EXISTS latex_assets;
DROP TABLE IF EXISTS latex_workspaces;

SET FOREIGN_KEY_CHECKS = @old_fk_checks;

-- ---------------------------------------------------------------------------
-- 5. system_settings columns
--    ai_assistant_* configured the "LLARS KI" persona that answered LaTeX
--    comment threads; zotero_* held the single admin-registered Zotero OAuth
--    app. Both features are gone. Other toggles in this table
--    (communication_enabled, referral_*, self_service_password_reset_enabled)
--    are unrelated and stay.
-- ---------------------------------------------------------------------------
ALTER TABLE system_settings DROP COLUMN IF EXISTS ai_assistant_enabled;
ALTER TABLE system_settings DROP COLUMN IF EXISTS ai_assistant_username;
ALTER TABLE system_settings DROP COLUMN IF EXISTS ai_assistant_color;
ALTER TABLE system_settings DROP COLUMN IF EXISTS zotero_oauth_enabled;
ALTER TABLE system_settings DROP COLUMN IF EXISTS zotero_client_key;
ALTER TABLE system_settings DROP COLUMN IF EXISTS zotero_client_secret_encrypted;

-- ---------------------------------------------------------------------------
-- 6. LaTeX-only permissions
--    role_permissions / user_permissions reference permissions.id with
--    ON DELETE CASCADE, but the joins are spelled out explicitly so the cleanup
--    also works on databases where the FKs were never created.
--    permission_audit_log keeps its rows: it stores permission_key as plain
--    text and is a historical record.
-- ---------------------------------------------------------------------------
DELETE rp FROM role_permissions rp
    JOIN permissions p ON p.id = rp.permission_id
    WHERE p.permission_key IN (
        'feature:latex_collab:view',
        'feature:latex_collab:edit',
        'feature:latex_collab:share',
        'feature:latex_collab:ai'
    );

DELETE up FROM user_permissions up
    JOIN permissions p ON p.id = up.permission_id
    WHERE p.permission_key IN (
        'feature:latex_collab:view',
        'feature:latex_collab:edit',
        'feature:latex_collab:share',
        'feature:latex_collab:ai'
    );

DELETE FROM permissions WHERE permission_key IN (
    'feature:latex_collab:view',
    'feature:latex_collab:edit',
    'feature:latex_collab:share',
    'feature:latex_collab:ai'
);
