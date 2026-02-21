-- Migration: EmailThread -> EvaluationItem Rename
-- Date: 2026-01-19
-- Description: Renames email_threads table and related columns to evaluation_items
--              for a more generic evaluation system (Rating, Comparison, Labeling, Authenticity)

-- ============================================================================
-- 1) Rename the main table: email_threads -> evaluation_items
-- ============================================================================
-- Drop foreign key constraints first (they reference the old table name)

ALTER TABLE messages DROP FOREIGN KEY messages_ibfk_1;
ALTER TABLE features DROP FOREIGN KEY features_ibfk_1;
ALTER TABLE scenario_threads DROP FOREIGN KEY scenario_threads_ibfk_2;
ALTER TABLE user_mailhistory_ratings DROP FOREIGN KEY user_mailhistory_ratings_ibfk_2;
ALTER TABLE user_message_ratings DROP FOREIGN KEY user_message_ratings_ibfk_2;
ALTER TABLE user_consulting_category_selection DROP FOREIGN KEY user_consulting_category_selection_ibfk_2;
ALTER TABLE pillar_threads DROP FOREIGN KEY pillar_threads_ibfk_2;
ALTER TABLE authenticity_conversations DROP FOREIGN KEY authenticity_conversations_ibfk_1;
ALTER TABLE user_authenticity_votes DROP FOREIGN KEY user_authenticity_votes_ibfk_2;
ALTER TABLE oncoco_sentence_labels DROP FOREIGN KEY oncoco_sentence_labels_ibfk_2;
ALTER TABLE judge_comparisons DROP FOREIGN KEY judge_comparisons_ibfk_2;
ALTER TABLE judge_comparisons DROP FOREIGN KEY judge_comparisons_ibfk_3;

-- Rename the table
RENAME TABLE email_threads TO evaluation_items;

-- Rename the primary key column: thread_id -> item_id
ALTER TABLE evaluation_items CHANGE thread_id item_id INT AUTO_INCREMENT;

-- Update the unique constraint name
ALTER TABLE evaluation_items DROP INDEX _chat_institut_function_uc;
ALTER TABLE evaluation_items ADD CONSTRAINT _chat_institut_function_uc
    UNIQUE (chat_id, institut_id, function_type_id);

-- ============================================================================
-- 2) Update foreign key columns in related tables
-- ============================================================================

-- messages table
ALTER TABLE messages CHANGE thread_id item_id INT;
ALTER TABLE messages ADD CONSTRAINT messages_ibfk_1
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- features table
ALTER TABLE features CHANGE thread_id item_id INT;
ALTER TABLE features ADD CONSTRAINT features_ibfk_1
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- scenario_threads table -> scenario_items
RENAME TABLE scenario_threads TO scenario_items;
ALTER TABLE scenario_items CHANGE thread_id item_id INT;
ALTER TABLE scenario_items ADD CONSTRAINT scenario_items_ibfk_2
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);
-- Update unique constraint
ALTER TABLE scenario_items DROP INDEX uix_thread_szenario;
ALTER TABLE scenario_items ADD CONSTRAINT uix_item_scenario
    UNIQUE (item_id, scenario_id);

-- user_mailhistory_ratings table
ALTER TABLE user_mailhistory_ratings CHANGE thread_id item_id INT;
ALTER TABLE user_mailhistory_ratings ADD CONSTRAINT user_mailhistory_ratings_ibfk_2
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- user_message_ratings table
ALTER TABLE user_message_ratings CHANGE thread_id item_id INT;
ALTER TABLE user_message_ratings ADD CONSTRAINT user_message_ratings_ibfk_2
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- user_consulting_category_selection table
ALTER TABLE user_consulting_category_selection CHANGE thread_id item_id INT;
ALTER TABLE user_consulting_category_selection ADD CONSTRAINT user_consulting_category_selection_ibfk_2
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- pillar_threads table
ALTER TABLE pillar_threads CHANGE thread_id item_id INT;
ALTER TABLE pillar_threads ADD CONSTRAINT pillar_threads_ibfk_2
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- authenticity_conversations table
ALTER TABLE authenticity_conversations CHANGE thread_id item_id INT;
ALTER TABLE authenticity_conversations ADD CONSTRAINT authenticity_conversations_ibfk_1
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- user_authenticity_votes table
ALTER TABLE user_authenticity_votes CHANGE thread_id item_id INT;
ALTER TABLE user_authenticity_votes ADD CONSTRAINT user_authenticity_votes_ibfk_2
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- oncoco_sentence_labels table
ALTER TABLE oncoco_sentence_labels CHANGE thread_id item_id INT;
ALTER TABLE oncoco_sentence_labels ADD CONSTRAINT oncoco_sentence_labels_ibfk_2
    FOREIGN KEY (item_id) REFERENCES evaluation_items(item_id);

-- judge_comparisons table (has two references: thread_a_id and thread_b_id)
ALTER TABLE judge_comparisons CHANGE thread_a_id item_a_id INT;
ALTER TABLE judge_comparisons CHANGE thread_b_id item_b_id INT;
ALTER TABLE judge_comparisons ADD CONSTRAINT judge_comparisons_ibfk_2
    FOREIGN KEY (item_a_id) REFERENCES evaluation_items(item_id);
ALTER TABLE judge_comparisons ADD CONSTRAINT judge_comparisons_ibfk_3
    FOREIGN KEY (item_b_id) REFERENCES evaluation_items(item_id);

-- ============================================================================
-- 3) Update scenario_thread_distribution table
-- ============================================================================
-- This table references scenario_threads (now scenario_items)
ALTER TABLE scenario_thread_distribution DROP FOREIGN KEY scenario_thread_distribution_ibfk_3;
ALTER TABLE scenario_thread_distribution CHANGE scenario_thread_id scenario_item_id INT;
ALTER TABLE scenario_thread_distribution ADD CONSTRAINT scenario_thread_distribution_ibfk_3
    FOREIGN KEY (scenario_item_id) REFERENCES scenario_items(id);

-- Optionally rename the table itself
RENAME TABLE scenario_thread_distribution TO scenario_item_distribution;

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- Note: Run this migration AFTER backing up your database!
-- Rollback script should reverse all these operations.
