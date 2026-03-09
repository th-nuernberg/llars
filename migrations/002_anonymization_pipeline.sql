-- Anonymization Pipeline - Database Migration
-- Created: 2025-02-01
-- Description: Creates tables for conversation anonymization workflow

-- Table 1: Conversation metadata and status tracking
CREATE TABLE IF NOT EXISTS anonymization_conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,

    -- Source tracking
    source_file_path VARCHAR(512) NOT NULL,
    original_chat_id VARCHAR(255),
    title VARCHAR(512),

    -- Status tracking
    status ENUM('pending', 'in_progress', 'completed', 'error') DEFAULT 'pending' NOT NULL,
    error_message TEXT,

    -- Metadata
    message_count INT DEFAULT 0,
    entity_count INT DEFAULT 0,
    original_created_at DATETIME,
    persona_json JSON,

    -- Audit
    imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    imported_by INT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by INT,
    completed_at DATETIME,

    FOREIGN KEY (imported_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,

    INDEX idx_status (status),
    INDEX idx_source_file (source_file_path(255)),
    INDEX idx_original_chat_id (original_chat_id),
    INDEX idx_title (title(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 2: Messages with original and anonymized content
CREATE TABLE IF NOT EXISTS anonymization_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,

    -- Message data
    message_number INT NOT NULL,
    author VARCHAR(255) NOT NULL,
    original_content TEXT NOT NULL,
    anonymized_content TEXT NOT NULL,

    -- Version tracking
    current_version INT DEFAULT 1,
    is_manually_edited BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (conversation_id) REFERENCES anonymization_conversations(id) ON DELETE CASCADE,

    INDEX idx_conversation (conversation_id),
    INDEX idx_message_number (conversation_id, message_number),
    UNIQUE KEY unique_conversation_message (conversation_id, message_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 3: Detected entities per message
CREATE TABLE IF NOT EXISTS anonymization_entities (
    id INT PRIMARY KEY AUTO_INCREMENT,
    message_id INT NOT NULL,

    -- Entity data (from anonymization service)
    label ENUM('PER', 'LOC', 'ORG', 'DATE', 'AGE', 'PHONE', 'MAIL', 'AHV', 'PLZ', 'MISC') NOT NULL,
    original_text VARCHAR(512) NOT NULL,
    replacement_text VARCHAR(512) NOT NULL,
    start_pos INT NOT NULL,
    end_pos INT NOT NULL,

    -- Group tracking (for entity consistency)
    group_key VARCHAR(255),
    group_mode VARCHAR(50),
    db_hit BOOLEAN DEFAULT FALSE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES anonymization_messages(id) ON DELETE CASCADE,

    INDEX idx_message (message_id),
    INDEX idx_label (label),
    INDEX idx_group_key (group_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 4: Message edit history (version tracking)
CREATE TABLE IF NOT EXISTS anonymization_message_versions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    message_id INT NOT NULL,

    -- Version data
    version_number INT NOT NULL,
    content TEXT NOT NULL,
    change_description TEXT,

    -- Audit
    changed_by INT NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES anonymization_messages(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE CASCADE,

    INDEX idx_message (message_id),
    UNIQUE KEY unique_message_version (message_id, version_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
