# embedding_constants.py
"""
Constants and utilities for the Collection Embedding Service.

This module provides:
- ChromaDB configuration constants
- Deadlock retry decorator for database operations
- ChromaDB metadata and collection name sanitization

ChromaDB Requirements:
    Collection names must be:
    - 3-63 characters long
    - Start and end with alphanumeric characters
    - Contain only alphanumeric, underscores, or hyphens
    - Not be a valid IPv4 address

Used by: collection_embedding_service.py, embedding_chroma.py
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from functools import wraps
from typing import Dict, Any, TypeVar, Callable

from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# Type variable for generic return types in decorators
T = TypeVar('T')


# =============================================================================
# CHROMADB CONFIGURATION
# =============================================================================

# ChromaDB collection metadata for cosine distance similarity
# IMPORTANT: This ensures proper similarity scoring for both
# normalized and unnormalized embeddings
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}


# =============================================================================
# DEADLOCK RETRY DECORATOR
# =============================================================================

def retry_on_deadlock(max_retries: int = 3, delay: float = 0.5):
    """
    Decorator to retry database operations on deadlock.

    MariaDB/MySQL can encounter deadlocks when multiple threads
    compete for the same rows. This decorator automatically retries
    the operation with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 0.5)
               Doubles with each retry attempt (exponential backoff)

    Returns:
        Decorated function that retries on deadlock

    Example:
        @retry_on_deadlock(max_retries=3, delay=0.5)
        def update_document_status(doc_id: int, status: str):
            doc = RAGDocument.query.get(doc_id)
            doc.status = status
            db.session.commit()

    Detects deadlocks by:
        - 'deadlock' in error message (case-insensitive)
        - MySQL error code 1213 (ER_LOCK_DEADLOCK)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            from db.db import db

            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if _is_deadlock_error(e):
                        last_exception = e
                        logger.warning(
                            f"[DB] Deadlock detected in {func.__name__}, "
                            f"attempt {attempt + 1}/{max_retries + 1}, "
                            f"retrying in {current_delay}s"
                        )
                        _safe_rollback(db)

                        if attempt < max_retries:
                            time.sleep(current_delay)
                            current_delay *= 2  # Exponential backoff
                            continue
                    raise
                except Exception as e:
                    # Check for nested deadlock errors (wrapped exceptions)
                    if _is_deadlock_error(e):
                        last_exception = e
                        logger.warning(
                            f"[DB] Deadlock detected (nested) in {func.__name__}, "
                            f"attempt {attempt + 1}/{max_retries + 1}"
                        )
                        _safe_rollback(db)

                        if attempt < max_retries:
                            time.sleep(current_delay)
                            current_delay *= 2
                            continue
                    raise

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def _is_deadlock_error(exception: Exception) -> bool:
    """
    Check if an exception is a database deadlock error.

    Args:
        exception: The exception to check

    Returns:
        True if the exception indicates a deadlock
    """
    error_msg = str(exception).lower()
    return 'deadlock' in error_msg or '1213' in error_msg


def _safe_rollback(db) -> None:
    """
    Safely rollback a database session.

    Args:
        db: SQLAlchemy database instance
    """
    try:
        db.session.rollback()
    except Exception:
        pass


# =============================================================================
# METADATA SANITIZATION
# =============================================================================

def sanitize_chroma_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata for ChromaDB storage.

    ChromaDB metadata must only contain primitive values (str/int/float/bool)
    and must not contain None values. This function filters and converts
    metadata to comply with these requirements.

    Args:
        metadata: Dictionary of metadata to sanitize

    Returns:
        Sanitized dictionary with only valid ChromaDB metadata values

    Example:
        >>> sanitize_chroma_metadata({
        ...     'document_id': 123,
        ...     'title': 'Test',
        ...     'tags': ['a', 'b'],  # List - will be stringified
        ...     'deleted': None      # None - will be removed
        ... })
        {'document_id': 123, 'title': 'Test', 'tags': "['a', 'b']"}
    """
    if not metadata:
        return {}

    cleaned: Dict[str, Any] = {}
    for key, value in metadata.items():
        # Skip None values
        if value is None:
            continue

        # Keep primitive types as-is
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            # Convert complex types to string
            cleaned[key] = str(value)

    return cleaned


# =============================================================================
# COLLECTION NAME SANITIZATION
# =============================================================================

def sanitize_chroma_collection_name(name: str, model_name: str) -> str:
    """
    Create a valid ChromaDB collection name.

    ChromaDB has strict requirements for collection names:
    - 3-63 characters length
    - Start and end with alphanumeric character
    - Only alphanumeric, underscores, or hyphens allowed
    - No consecutive periods
    - Not a valid IPv4 address

    This function transforms collection and model names into a valid
    ChromaDB collection name by:
    1. Replacing invalid characters with underscores
    2. Removing consecutive underscores
    3. Trimming leading/trailing special characters
    4. Truncating with hash suffix if too long
    5. Padding if too short

    Args:
        name: The collection name from database
        model_name: The embedding model name (e.g., 'llamaindex/vdr-2b-multi-v1')

    Returns:
        A valid ChromaDB collection name

    Example:
        >>> sanitize_chroma_collection_name('My Collection', 'llamaindex/vdr-2b-multi-v1')
        'llars_My_Collection_llamaindex_vdr-2b-multi-v1'
    """
    # Replace invalid characters with underscores
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    clean_model = re.sub(r'[^a-zA-Z0-9_-]', '_', model_name.replace('/', '_'))

    # Build the full name with prefix
    full_name = f"llars_{clean_name}_{clean_model}"

    # Remove consecutive underscores
    full_name = re.sub(r'_+', '_', full_name)

    # Ensure it starts and ends with alphanumeric
    full_name = full_name.strip('_-')

    # Truncate to 63 characters max while keeping meaningful parts
    if len(full_name) > 63:
        # Keep prefix and hash the rest for uniqueness
        prefix = full_name[:50]
        suffix_hash = hashlib.md5(full_name.encode()).hexdigest()[:12]
        full_name = f"{prefix}_{suffix_hash}"

    # Final validation - ensure 3+ chars minimum
    if len(full_name) < 3:
        full_name = f"col_{full_name}"

    return full_name


# =============================================================================
# CONTENT HASHING
# =============================================================================

def hash_content(content: str) -> str:
    """
    Generate SHA-256 hash for content.

    Used for deduplication and change detection of document chunks.

    Args:
        content: Text content to hash

    Returns:
        Hexadecimal SHA-256 hash string (64 characters)

    Example:
        >>> hash_content("Hello, World!")
        'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
