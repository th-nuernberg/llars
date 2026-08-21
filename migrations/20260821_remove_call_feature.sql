-- Migration: Remove LiveKit voice/video call feature
-- Date: 2026-08-21
-- Description: Drops the call tables, shrinks the messaging_messages.message_type
--              ENUM back to the message kinds that still exist, and removes the
--              three call-only permissions. The messaging feature itself
--              (system_settings.communication_enabled, feature:communication:
--              access/chat/ai) is NOT affected.

-- ---------------------------------------------------------------------------
-- 1. Call tables
--    Participants first: messaging_call_participants.call_id has an FK on
--    messaging_calls.id, so dropping the parent first would fail on engines
--    that enforce the constraint.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS messaging_call_participants;
DROP TABLE IF EXISTS messaging_calls;

-- ---------------------------------------------------------------------------
-- 2. message_type ENUM
--    'call_event' rows were auto-generated call log entries in the chat
--    timeline. They are converted to 'system' BEFORE the ALTER, otherwise MySQL
--    would silently coerce them to the empty string when the member disappears.
-- ---------------------------------------------------------------------------
UPDATE messaging_messages SET message_type = 'system' WHERE message_type = 'call_event';

ALTER TABLE messaging_messages
    MODIFY COLUMN message_type ENUM('text', 'system', 'file') NOT NULL;

-- ---------------------------------------------------------------------------
-- 3. Call-only permissions
--    role_permissions / user_permissions reference permissions.id with
--    ON DELETE CASCADE, but the joins are spelled out explicitly so the cleanup
--    also works on databases where the FKs were never created.
--    permission_audit_log keeps its rows: it stores permission_key as plain
--    text and is a historical record.
-- ---------------------------------------------------------------------------
DELETE rp FROM role_permissions rp
    JOIN permissions p ON p.id = rp.permission_id
    WHERE p.permission_key IN (
        'feature:communication:voice',
        'feature:communication:video',
        'feature:communication:transcription'
    );

DELETE up FROM user_permissions up
    JOIN permissions p ON p.id = up.permission_id
    WHERE p.permission_key IN (
        'feature:communication:voice',
        'feature:communication:video',
        'feature:communication:transcription'
    );

DELETE FROM permissions WHERE permission_key IN (
    'feature:communication:voice',
    'feature:communication:video',
    'feature:communication:transcription'
);
