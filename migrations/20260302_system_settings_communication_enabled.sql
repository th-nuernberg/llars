-- Migration: Add communication_enabled to system_settings
-- Date: 2026-03-02
-- Description: Adds global communication feature toggle used by messaging/call endpoints.

ALTER TABLE system_settings
ADD COLUMN IF NOT EXISTS communication_enabled BOOLEAN NOT NULL DEFAULT FALSE
    COMMENT 'Enable communication features (messaging, calls) globally';
