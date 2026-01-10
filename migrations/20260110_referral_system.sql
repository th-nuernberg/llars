-- Migration: Referral/Invitation System
-- Date: 2026-01-10
-- Description: Adds tables for referral campaigns, invite links, and registration tracking
--              Also adds referral settings to system_settings table

-- ============================================================================
-- 1) Referral Campaigns Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS referral_campaigns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    start_date DATETIME,
    end_date DATETIME,
    max_registrations INT,
    created_by VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    config_json JSON COMMENT 'Custom campaign settings',
    INDEX ix_referral_campaigns_name (name),
    INDEX ix_referral_campaigns_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 2) Referral Links Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS referral_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NOT NULL,
    code VARCHAR(64) NOT NULL UNIQUE,
    slug VARCHAR(100) UNIQUE,
    role_name VARCHAR(100) NOT NULL DEFAULT 'evaluator',
    label VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    max_uses INT,
    expires_at DATETIME,
    created_by VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_referral_links_campaign_id (campaign_id),
    INDEX ix_referral_links_code (code),
    INDEX ix_referral_links_slug (slug),
    INDEX ix_referral_links_code_active (code, is_active),
    FOREIGN KEY (campaign_id) REFERENCES referral_campaigns(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3) Referral Registrations Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS referral_registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    link_id INT,
    username VARCHAR(255) NOT NULL,
    registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) COMMENT 'IPv6 max length',
    user_agent VARCHAR(512),
    metadata_json JSON,
    UNIQUE KEY uq_referral_registration_username (username),
    INDEX ix_referral_registrations_link_id (link_id),
    INDEX ix_referral_registrations_username (username),
    INDEX ix_referral_registrations_registered_at (registered_at),
    FOREIGN KEY (link_id) REFERENCES referral_links(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4) Add Referral Settings to system_settings
-- ============================================================================
ALTER TABLE system_settings
ADD COLUMN IF NOT EXISTS referral_system_enabled BOOLEAN NOT NULL DEFAULT FALSE
    COMMENT 'Enable referral/invitation link system';

ALTER TABLE system_settings
ADD COLUMN IF NOT EXISTS self_registration_enabled BOOLEAN NOT NULL DEFAULT FALSE
    COMMENT 'Enable self-registration via referral links (shows Register button)';

ALTER TABLE system_settings
ADD COLUMN IF NOT EXISTS default_referral_role VARCHAR(100) NOT NULL DEFAULT 'evaluator'
    COMMENT 'Default role for users registered via referral';

-- ============================================================================
-- Migration Complete
-- ============================================================================
