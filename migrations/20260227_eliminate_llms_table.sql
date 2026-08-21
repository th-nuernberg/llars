-- Migration: Eliminate legacy `llms` table — LLM Single Source of Truth
-- Date: 2026-02-27
-- Description: Replaces llm_id (FK → llms) with model_id (VARCHAR string) on
--              features and user_feature_rankings. The llm_models table serves
--              as the optional metadata registry. The llms table is dropped.
--
-- IMPORTANT: Create a DB backup before running this migration!
--   docker exec llars_db_service mysqldump -u dev_user -pdev_password_change_me database_llars > backup_before_llm_migration.sql

-- ============================================================================
-- Phase 1: Add model_id columns (non-destructive)
-- ============================================================================

ALTER TABLE features ADD COLUMN model_id VARCHAR(255) AFTER llm_id;
ALTER TABLE features ADD INDEX ix_features_model_id (model_id);

ALTER TABLE user_feature_rankings ADD COLUMN model_id VARCHAR(255) AFTER llm_id;
ALTER TABLE user_feature_rankings ADD INDEX ix_ufr_model_id (model_id);

-- ============================================================================
-- Phase 2: Migrate data — llms.name → model_id string
-- ============================================================================

-- Features: Map llm_id → model_id via llms table
UPDATE features f
JOIN llms l ON f.llm_id = l.llm_id
SET f.model_id = CASE
    -- Legacy short names → normalized Global/ format
    WHEN l.name = 'GPT-4'           THEN 'Global/OpenAI/gpt-4'
    WHEN l.name = 'GPT-5 Nano'      THEN 'Global/OpenAI/gpt-5-nano'
    WHEN l.name = 'GPT-5 Mini'      THEN 'Global/OpenAI/gpt-5-mini'
    WHEN l.name = 'Claude-3'        THEN 'Global/Anthropic/claude-3'
    WHEN l.name = 'Mistral-7B'      THEN 'Global/Mistral/Mistral-7B'
    WHEN l.name = 'Mistral Small'   THEN 'Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506'
    WHEN l.name = 'Magistral Small' THEN 'Global/Mistral/Magistral-Small-2509'
    WHEN l.name = 'SummEval'        THEN 'SummEval'
    -- Models with prompt suffix in name: strip the " (prompt-name)" part
    WHEN l.name LIKE '% (%)'        THEN TRIM(SUBSTRING_INDEX(l.name, ' (', 1))
    -- Everything else (user-provider:..., Global/...) → keep as-is
    ELSE l.name
END;

-- User Feature Rankings: same mapping logic
UPDATE user_feature_rankings ufr
JOIN llms l ON ufr.llm_id = l.llm_id
SET ufr.model_id = CASE
    WHEN l.name = 'GPT-4'           THEN 'Global/OpenAI/gpt-4'
    WHEN l.name = 'GPT-5 Nano'      THEN 'Global/OpenAI/gpt-5-nano'
    WHEN l.name = 'GPT-5 Mini'      THEN 'Global/OpenAI/gpt-5-mini'
    WHEN l.name = 'Claude-3'        THEN 'Global/Anthropic/claude-3'
    WHEN l.name = 'Mistral-7B'      THEN 'Global/Mistral/Mistral-7B'
    WHEN l.name = 'Mistral Small'   THEN 'Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506'
    WHEN l.name = 'Magistral Small' THEN 'Global/Mistral/Magistral-Small-2509'
    WHEN l.name = 'SummEval'        THEN 'SummEval'
    WHEN l.name LIKE '% (%)'        THEN TRIM(SUBSTRING_INDEX(l.name, ' (', 1))
    ELSE l.name
END;

-- ============================================================================
-- Phase 2b: Validation queries (run these manually to verify)
-- ============================================================================

-- Check: No NULL model_ids where llm_id was set
-- SELECT COUNT(*) FROM features WHERE llm_id IS NOT NULL AND model_id IS NULL;
-- Expected: 0

-- Check: Distinct model_ids are clean
-- SELECT DISTINCT model_id FROM features ORDER BY model_id;

-- Check: No legacy short names remain
-- SELECT DISTINCT model_id FROM features
-- WHERE model_id NOT LIKE 'Global/%'
--   AND model_id NOT LIKE 'user-provider:%'
--   AND model_id NOT IN ('SummEval')
--   AND model_id IS NOT NULL;

-- Check: user_feature_rankings
-- SELECT COUNT(*) FROM user_feature_rankings WHERE llm_id IS NOT NULL AND model_id IS NULL;
-- Expected: 0

-- ============================================================================
-- Phase 3: Drop FK constraints, llm_id columns, and llms table
-- ============================================================================
-- IMPORTANT: Only run this AFTER verifying Phase 2 data migration is correct!

-- Drop FK from features → llms
-- Note: FK name may vary. Use SHOW CREATE TABLE features; to find exact name.
-- Common names: features_ibfk_3 or fk_features_llm_id
ALTER TABLE features DROP FOREIGN KEY features_ibfk_3;
ALTER TABLE features DROP COLUMN llm_id;

-- Drop FK from user_feature_rankings → llms
ALTER TABLE user_feature_rankings DROP FOREIGN KEY user_feature_rankings_ibfk_3;
ALTER TABLE user_feature_rankings DROP COLUMN llm_id;

-- Drop the legacy llms table
DROP TABLE llms;
