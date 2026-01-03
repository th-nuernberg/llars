# app/workers/embedding/__init__.py
"""
Background Worker for RAG Document Embedding Processing.

This package provides the embedding worker which processes documents in the
background, creating vector embeddings and storing them in ChromaDB.

Architecture:
    The worker is split into focused modules:
    - constants.py: Configuration constants and ChromaDB metadata
    - embedding_resolver.py: Model resolution with LiteLLM/HuggingFace fallback
    - document_processor.py: Core document processing and chunking
    - image_processor.py: Image embedding for multimodal models
    - batch_processor.py: Batch processing and stale document recovery
    - progress_emitter.py: Socket.IO progress updates
    - worker.py: Main worker class coordinating all modules

Usage:
    from workers.embedding import start_embedding_worker, stop_embedding_worker

    # Start during app initialization
    start_embedding_worker(app)

    # Stop during shutdown
    stop_embedding_worker()

Features:
    - Thread-based background processing
    - Live Socket.IO broadcasts for progress updates
    - Automatic startup on application init
    - Error handling and retry logic
    - Batch processing for efficiency
    - Multi-model embedding support (LiteLLM API + local HuggingFace)
    - Image embedding for multimodal models (VDR-2B)

Author: LLARS Team
Date: January 2026 (refactored from monolithic embedding_worker.py)
"""

from workers.embedding.worker import (
    EmbeddingWorker,
    get_embedding_worker,
    start_embedding_worker,
    stop_embedding_worker,
)

from workers.embedding.constants import (
    CHROMA_COLLECTION_METADATA,
    POLL_INTERVAL,
    BATCH_SIZE,
    MAX_RETRIES,
)

__all__ = [
    # Worker class and management
    'EmbeddingWorker',
    'get_embedding_worker',
    'start_embedding_worker',
    'stop_embedding_worker',
    # Constants
    'CHROMA_COLLECTION_METADATA',
    'POLL_INTERVAL',
    'BATCH_SIZE',
    'MAX_RETRIES',
]
