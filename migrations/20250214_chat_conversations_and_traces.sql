-- Migration: Chat conversations scoping + agent trace storage + embedding provenance
-- Date: 2025-02-14
-- Notes: Applies to MariaDB/MySQL. Run this after backup.

-- 1) Ensure session IDs are scoped per chatbot (avoid collisions)
ALTER TABLE chatbot_conversations
ADD CONSTRAINT uq_chatbot_session_per_bot UNIQUE (chatbot_id, session_id);

-- 2) Store agent traces and streaming metadata on messages
ALTER TABLE chatbot_messages
ADD COLUMN IF NOT EXISTS agent_trace JSON NULL,
ADD COLUMN IF NOT EXISTS stream_metadata JSON NULL;

-- 3) Persist embedding dimensions alongside embedding model (provenance)
ALTER TABLE rag_document_chunks
ADD COLUMN IF NOT EXISTS embedding_dimensions INT NULL;
