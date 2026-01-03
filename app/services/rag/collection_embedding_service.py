# collection_embedding_service.py
"""
Collection Embedding Service.

DEPRECATED: This file is kept for backward compatibility.
The implementation has been moved to services/rag/embedding/ module.

Import from services.rag.embedding instead:
    from services.rag.embedding import (
        CollectionEmbeddingService,
        get_collection_embedding_service,
        sanitize_chroma_metadata,
        sanitize_chroma_collection_name,
    )

Or use the legacy imports (still supported):
    from services.rag.collection_embedding_service import get_collection_embedding_service

Module Structure (services/rag/embedding/):
    - embedding_constants.py: Configuration, decorators, utilities
    - embedding_chroma.py: ChromaDB operations (upsert, backfill)
    - embedding_chunks.py: Chunk creation and image embedding
    - embedding_events.py: WebSocket progress and completion events
    - embedding_database.py: Database status updates with deadlock retry
    - collection_embedding_service.py: Main service class

Author: LLARS Team
Date: November 2025 (refactored January 2026)
"""

# Re-export everything from the new module location for backward compatibility
from .embedding.collection_embedding_service import (
    CollectionEmbeddingService,
    get_collection_embedding_service,
)

# Re-export constants and utilities for any code that might reference them
from .embedding.embedding_constants import (
    CHROMA_COLLECTION_METADATA,
    retry_on_deadlock,
    sanitize_chroma_metadata,
    sanitize_chroma_collection_name,
    hash_content,
)

__all__ = [
    # Main classes
    'CollectionEmbeddingService',
    'get_collection_embedding_service',

    # Constants (for backward compatibility)
    'CHROMA_COLLECTION_METADATA',
    'retry_on_deadlock',
    'sanitize_chroma_metadata',
    'sanitize_chroma_collection_name',
    'hash_content',
]
