-- Add quality filtering fields to anonymization_conversations
ALTER TABLE anonymization_conversations
ADD COLUMN quality_rating TINYINT NULL COMMENT '1-5 star quality rating',
ADD COLUMN exclude_from_export BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Exclude from final dataset export',
ADD COLUMN quality_notes TEXT NULL COMMENT 'Reviewer notes about quality issues',
ADD COLUMN quality_reviewed_at DATETIME NULL COMMENT 'When quality was last reviewed',
ADD COLUMN quality_reviewed_by INT NULL COMMENT 'User who reviewed quality',
ADD INDEX idx_exclude_from_export (exclude_from_export),
ADD INDEX idx_quality_rating (quality_rating),
ADD CONSTRAINT fk_quality_reviewed_by FOREIGN KEY (quality_reviewed_by) REFERENCES users(id) ON DELETE SET NULL;
