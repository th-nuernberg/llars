# app/workers/embedding_worker.py
"""
Background Worker for RAG Document Embedding Processing.

IMPORTANT: This file is a backwards-compatibility shim.
The worker implementation has been refactored into the `embedding/` package.

New code should import from:
    from workers.embedding import start_embedding_worker, stop_embedding_worker

This file re-exports all public APIs for backwards compatibility.

Architecture (see workers/embedding/):
    - constants.py: Configuration constants and ChromaDB metadata
    - embedding_resolver.py: Model resolution with LiteLLM/HuggingFace fallback
    - document_processor.py: Core document processing and chunking
    - image_processor.py: Image embedding for multimodal models
    - batch_processor.py: Batch processing and stale document recovery
    - progress_emitter.py: Socket.IO progress updates
    - worker.py: Main worker class coordinating all modules

Features:
    - Thread-based background processing
    - Live Socket.IO broadcasts for progress updates
    - Automatic startup on application init
    - Error handling and retry logic
    - Batch processing for efficiency
    - Multi-model embedding support (LiteLLM API + local HuggingFace)
    - Image embedding for multimodal models (VDR-2B)

Usage:
    from workers.embedding_worker import start_embedding_worker, stop_embedding_worker

    # Start during app initialization
    start_embedding_worker(app)

    # Stop during shutdown
    stop_embedding_worker()

Author: LLARS Team
Date: November 2025 (refactored January 2026)
"""

# Re-export everything from the new package for backwards compatibility
from workers.embedding import (
    # Worker class and management
    EmbeddingWorker,
    get_embedding_worker,
    start_embedding_worker,
    stop_embedding_worker,
    # Constants
    CHROMA_COLLECTION_METADATA,
    POLL_INTERVAL,
    BATCH_SIZE,
    MAX_RETRIES,
)

__all__ = [
    'EmbeddingWorker',
    'get_embedding_worker',
    'start_embedding_worker',
    'stop_embedding_worker',
    'CHROMA_COLLECTION_METADATA',
    'POLL_INTERVAL',
    'BATCH_SIZE',
    'MAX_RETRIES',
]
