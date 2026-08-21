-- Add metadata storage for anonymization conversation imports
ALTER TABLE anonymization_conversations
ADD COLUMN metadata_json JSON NULL COMMENT 'Original import metadata + derived model/course summaries';
