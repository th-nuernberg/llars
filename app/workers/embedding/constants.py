# app/workers/embedding/constants.py
"""
Configuration Constants for Embedding Worker.

This module contains all configuration constants used by the embedding
worker, including ChromaDB settings, polling intervals, and retry limits.

Constants:
    CHROMA_COLLECTION_METADATA: ChromaDB collection config for cosine distance
    POLL_INTERVAL: Seconds between queue checks when idle
    BATCH_SIZE: Number of documents to process in one batch
    MAX_RETRIES: Maximum retry attempts per document
    STALE_PROCESSING_SECONDS: Time after which processing docs are considered stale

Environment Variables:
    EMBEDDING_STALE_SECONDS: Override for stale processing timeout (default: 900)

Author: LLARS Team
Date: January 2026
"""

import os

# ChromaDB collection metadata for cosine distance
# IMPORTANT: This ensures proper similarity scoring for both normalized and unnormalized embeddings
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}

# Worker configuration
POLL_INTERVAL = 5  # Seconds between queue checks when idle
BATCH_SIZE = 5     # Number of documents to process in one batch
MAX_RETRIES = 3    # Maximum retry attempts per document


def get_stale_processing_seconds() -> int:
    """
    Get the timeout in seconds after which processing documents are considered stale.

    Stale documents are those that have been in 'processing' status for too long,
    typically due to worker crashes or restarts. These are automatically requeued.

    Returns:
        int: Number of seconds (default 900 = 15 minutes)

    Environment:
        EMBEDDING_STALE_SECONDS: Override the default timeout
    """
    try:
        return int(os.environ.get("EMBEDDING_STALE_SECONDS", "900"))
    except (ValueError, TypeError):
        return 900


# Models available via LiteLLM/KIZ API
LITELLM_EMBEDDING_MODELS = [
    "llamaindex/vdr-2b-multi-v1",
]

# Default chunk sizes for document processing
DEFAULT_CHUNK_SIZE = 1500
DEFAULT_CHUNK_OVERLAP = 300
