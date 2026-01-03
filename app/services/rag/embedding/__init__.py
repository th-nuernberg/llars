# embedding/__init__.py
"""
Collection Embedding Module.

This package handles the embedding process for RAG collections:
- Document chunking and vectorization
- ChromaDB storage and retrieval
- Real-time progress updates via WebSocket
- Wizard integration for chatbot building

Module Structure:
    - embedding_constants: Configuration, decorators, utilities
        - CHROMA_COLLECTION_METADATA
        - retry_on_deadlock decorator
        - sanitize_chroma_metadata, sanitize_chroma_collection_name
        - hash_content

    - embedding_chroma: ChromaDB operations
        - get_or_create_vectorstore
        - upsert_chunks_to_chroma, upsert_embeddings_to_chroma
        - backfill_empty_collection, get_collection_count

    - embedding_chunks: Chunk creation and image embedding
        - process_document_chunks
        - embed_image_chunks_for_document

    - embedding_events: WebSocket progress and completion events
        - emit_embedding_progress
        - emit_embedding_completed
        - emit_embedding_error
        - emit_document_processed

    - embedding_database: Database status updates with deadlock retry
        - update_document_status
        - update_collection_stats, finalize_collection_stats
        - recover_stuck_documents, reset_collection_for_restart
        - create_or_update_collection_embedding

    - collection_embedding_service: Main service class
        - CollectionEmbeddingService
        - get_collection_embedding_service

Usage:
    from services.rag.embedding import get_collection_embedding_service

    service = get_collection_embedding_service()
    service.start_embedding(collection_id=123)

Backward Compatibility:
    This module replaces the original collection_embedding_service.py file.
    The old file location is kept as a compatibility shim that re-exports
    from this package.
"""

# Main service class (most common import)
from .collection_embedding_service import (
    CollectionEmbeddingService,
    get_collection_embedding_service,
)

# Constants and utilities
from .embedding_constants import (
    CHROMA_COLLECTION_METADATA,
    retry_on_deadlock,
    sanitize_chroma_metadata,
    sanitize_chroma_collection_name,
    hash_content,
)

# ChromaDB operations
from .embedding_chroma import (
    get_or_create_vectorstore,
    get_vectorstore_without_embeddings,
    upsert_chunks_to_chroma,
    upsert_embeddings_to_chroma,
    backfill_empty_collection,
    get_collection_count,
)

# Chunk processing
from .embedding_chunks import (
    process_document_chunks,
    embed_image_chunks_for_document,
)

# Event emitters
from .embedding_events import (
    emit_embedding_progress,
    emit_embedding_completed,
    emit_embedding_error,
    emit_document_processed,
)

# Database operations
from .embedding_database import (
    update_document_status,
    update_collection_stats,
    finalize_collection_stats,
    recover_stuck_documents,
    reset_collection_for_restart,
    create_or_update_collection_embedding,
    set_collection_chroma_name,
    get_pending_documents,
    count_indexed_documents,
)

__all__ = [
    # Main service
    'CollectionEmbeddingService',
    'get_collection_embedding_service',

    # Constants
    'CHROMA_COLLECTION_METADATA',
    'retry_on_deadlock',
    'sanitize_chroma_metadata',
    'sanitize_chroma_collection_name',
    'hash_content',

    # ChromaDB
    'get_or_create_vectorstore',
    'get_vectorstore_without_embeddings',
    'upsert_chunks_to_chroma',
    'upsert_embeddings_to_chroma',
    'backfill_empty_collection',
    'get_collection_count',

    # Chunks
    'process_document_chunks',
    'embed_image_chunks_for_document',

    # Events
    'emit_embedding_progress',
    'emit_embedding_completed',
    'emit_embedding_error',
    'emit_document_processed',

    # Database
    'update_document_status',
    'update_collection_stats',
    'finalize_collection_stats',
    'recover_stuck_documents',
    'reset_collection_for_restart',
    'create_or_update_collection_embedding',
    'set_collection_chroma_name',
    'get_pending_documents',
    'count_indexed_documents',
]
