# embedding_database.py
"""
Database operations for the Collection Embedding Service.

This module handles all database updates during embedding:
- Document status updates (processing → indexed/failed)
- Collection statistics updates
- Stuck document recovery
- Model-specific embedding tracking via CollectionEmbedding table

All operations use the @retry_on_deadlock decorator to handle
concurrent database access from multiple embedding threads.

Database Tables Affected:
    - RAGDocument: Document status and processing timestamps
    - RAGCollection: Collection statistics and embedding status
    - RAGDocumentChunk: Chunk counts for statistics
    - CollectionDocumentLink: Collection-document relationships
    - CollectionEmbedding: Model-specific embedding tracking

Used by: collection_embedding_service.py
Depends on: embedding_constants.py
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List, Any

from .embedding_constants import retry_on_deadlock

logger = logging.getLogger(__name__)


# =============================================================================
# DOCUMENT STATUS UPDATES
# =============================================================================

@retry_on_deadlock(max_retries=3, delay=0.5)
def update_document_status(
    doc_id: int,
    status: str,
    error: Optional[str] = None,
    **kwargs
) -> None:
    """
    Update document status with deadlock retry.

    Safely updates a document's processing status, handling concurrent
    access via automatic deadlock retry with exponential backoff.

    Args:
        doc_id: Document ID to update
        status: New status ('processing', 'indexed', 'failed')
        error: Error message (only used when status='failed')
        **kwargs: Additional fields to update:
            - chunk_count (int): Number of chunks created
            - vector_ids (list): List of ChromaDB vector IDs
            - embedding_model (str): Name of embedding model used

    Database Effects:
        - Updates RAGDocument.status
        - Updates RAGDocument.updated_at to current time
        - If status='indexed': sets processed_at and indexed_at
        - If status='failed': sets processing_error

    Example:
        >>> update_document_status(
        ...     doc_id=123,
        ...     status='indexed',
        ...     chunk_count=15,
        ...     embedding_model='llamaindex/vdr-2b-multi-v1'
        ... )

    Raises:
        OperationalError: If max retries exceeded (deadlock not resolved)

    Note:
        Uses @retry_on_deadlock decorator - see embedding_constants.py
    """
    from db.database import db
    from db.tables import RAGDocument

    doc = RAGDocument.query.get(doc_id)
    if not doc:
        logger.warning(f"[CollectionEmbedding] Document {doc_id} not found for status update")
        return

    # Update core fields
    doc.status = status
    doc.updated_at = datetime.now()

    # Status-specific updates
    if status == 'indexed':
        doc.processed_at = datetime.now()
        doc.indexed_at = datetime.now()
    elif status == 'failed' and error:
        doc.processing_error = error

    # Apply additional fields from kwargs
    for key, value in kwargs.items():
        if hasattr(doc, key):
            setattr(doc, key, value)

    db.session.commit()
    logger.debug(f"[CollectionEmbedding] Document {doc_id} status updated to '{status}'")


# =============================================================================
# COLLECTION STATISTICS
# =============================================================================

@retry_on_deadlock(max_retries=3, delay=0.5)
def update_collection_stats(
    collection_id: int,
    progress: int,
    doc_count: int
) -> None:
    """
    Update collection statistics with deadlock retry.

    Recalculates and updates collection statistics including total chunks,
    document count, and embedding progress.

    Args:
        collection_id: Collection ID to update
        progress: Current embedding progress (0-100)
        doc_count: Number of documents in collection

    Database Effects:
        - Recalculates RAGCollection.total_chunks from actual chunk count
        - Updates RAGCollection.document_count
        - Updates RAGCollection.embedding_progress
        - Updates RAGCollection.last_indexed_at

    Note:
        Chunk count is recalculated from database to avoid drift from
        incremental counting which can miss reused chunks.

    Example:
        >>> update_collection_stats(
        ...     collection_id=42,
        ...     progress=75,
        ...     doc_count=10
        ... )
    """
    from db.database import db
    from db.tables import RAGCollection, RAGDocumentChunk, CollectionDocumentLink

    collection = RAGCollection.query.get(collection_id)
    if not collection:
        logger.warning(f"[CollectionEmbedding] Collection {collection_id} not found for stats update")
        return

    # Recalculate total chunks to avoid drift from incremental counting
    linked_doc_ids = db.session.query(CollectionDocumentLink.document_id).filter(
        CollectionDocumentLink.collection_id == collection_id
    ).subquery()

    actual_chunk_count = RAGDocumentChunk.query.filter(
        RAGDocumentChunk.document_id.in_(linked_doc_ids)
    ).count()

    # Update collection fields
    collection.total_chunks = actual_chunk_count
    collection.document_count = doc_count
    collection.embedding_progress = progress
    collection.last_indexed_at = datetime.now()

    db.session.commit()
    logger.debug(
        f"[CollectionEmbedding] Collection {collection_id} stats updated: "
        f"{actual_chunk_count} chunks, {doc_count} docs, {progress}% progress"
    )


def finalize_collection_stats(collection_id: int) -> int:
    """
    Finalize collection statistics after all documents are processed.

    Performs a final recalculation of collection statistics from the
    database to ensure accuracy.

    Args:
        collection_id: Collection ID to finalize

    Returns:
        Total number of chunks in the collection

    Database Effects:
        - Updates RAGCollection.document_count
        - Updates RAGCollection.total_chunks

    Note:
        This is called at the end of embedding to ensure stats are
        accurate before marking the collection as completed.
    """
    from db.database import db
    from db.tables import RAGCollection, RAGDocumentChunk, CollectionDocumentLink

    collection = RAGCollection.query.get(collection_id)
    if not collection:
        return 0

    # Get all document links
    doc_links = CollectionDocumentLink.query.filter_by(
        collection_id=collection_id
    ).all()
    all_docs = [link.document for link in doc_links if link.document]

    # Count total chunks via subquery
    linked_doc_ids = db.session.query(CollectionDocumentLink.document_id).filter(
        CollectionDocumentLink.collection_id == collection_id
    ).subquery()

    total_chunks = RAGDocumentChunk.query.filter(
        RAGDocumentChunk.document_id.in_(linked_doc_ids)
    ).count()

    # Update collection
    collection.document_count = len(all_docs)
    collection.total_chunks = total_chunks
    db.session.commit()

    logger.info(
        f"[CollectionEmbedding] Collection {collection_id} finalized: "
        f"{total_chunks} chunks, {len(all_docs)} documents"
    )

    return total_chunks


# =============================================================================
# STUCK DOCUMENT RECOVERY
# =============================================================================

def recover_stuck_documents(collection_id: int) -> int:
    """
    Recover documents stuck in 'processing' state from interrupted runs.

    When the embedding service crashes or is restarted, documents may
    be left in 'processing' state. This function resets them to 'pending'
    so they can be reprocessed.

    Args:
        collection_id: Collection ID to check for stuck documents

    Returns:
        Number of documents recovered

    Database Effects:
        - Sets status='pending' for documents with status='processing'
          that are linked to the specified collection

    Example:
        >>> recovered = recover_stuck_documents(collection_id=42)
        >>> print(f"Recovered {recovered} stuck documents")
    """
    from db.database import db
    from db.tables import RAGDocument, CollectionDocumentLink

    try:
        stuck_docs = (
            db.session.query(RAGDocument)
            .join(CollectionDocumentLink, RAGDocument.id == CollectionDocumentLink.document_id)
            .filter(
                CollectionDocumentLink.collection_id == collection_id,
                RAGDocument.status == 'processing'
            )
            .all()
        )

        if stuck_docs:
            for doc in stuck_docs:
                doc.status = 'pending'
            db.session.commit()

            logger.info(
                f"[CollectionEmbedding] Reset {len(stuck_docs)} documents from "
                f"'processing' to 'pending' for collection {collection_id}"
            )
            return len(stuck_docs)

        return 0

    except Exception as e:
        db.session.rollback()
        logger.warning(
            f"[CollectionEmbedding] Failed to reset stuck documents for "
            f"collection {collection_id}: {e}"
        )
        return 0


def reset_collection_for_restart(collection_id: int) -> bool:
    """
    Reset a collection's status for restart after crash.

    When a collection shows 'processing' status but no active job is
    running, it means the embedding process crashed. This function
    resets the status to 'idle' so embedding can be restarted.

    Args:
        collection_id: Collection ID to reset

    Returns:
        True if collection was reset, False otherwise

    Database Effects:
        - Sets RAGCollection.embedding_status = 'idle'
    """
    from db.database import db
    from db.tables import RAGCollection

    try:
        collection = RAGCollection.query.get(collection_id)
        if collection and collection.embedding_status == 'processing':
            collection.embedding_status = 'idle'
            db.session.commit()
            logger.warning(
                f"[CollectionEmbedding] Collection {collection_id} was marked "
                f"'processing' with no active job; reset to 'idle'"
            )
            return True
        return False

    except Exception as e:
        db.session.rollback()
        logger.error(f"[CollectionEmbedding] Failed to reset collection {collection_id}: {e}")
        return False


# =============================================================================
# COLLECTION EMBEDDING TRACKING
# =============================================================================

def create_or_update_collection_embedding(
    collection_id: int,
    model_name: str,
    model_source: str,
    embedding_dimensions: int,
    chroma_collection_name: str
) -> Any:
    """
    Create or update a CollectionEmbedding record for model tracking.

    The CollectionEmbedding table tracks which embedding models have been
    used for each collection, enabling multi-model support.

    Args:
        collection_id: Collection ID
        model_name: Embedding model identifier (e.g., 'llamaindex/vdr-2b-multi-v1')
        model_source: Where the model runs ('litellm' or 'local')
        embedding_dimensions: Vector dimensions (e.g., 1024)
        chroma_collection_name: Sanitized ChromaDB collection name

    Returns:
        The CollectionEmbedding record (created or updated)

    Database Effects:
        - Creates new CollectionEmbedding if not exists
        - Updates existing record if found
        - Sets status='processing' and progress=0
    """
    from db.database import db
    from db.models.rag import CollectionEmbedding

    # Check for existing record
    coll_embedding = CollectionEmbedding.query.filter_by(
        collection_id=collection_id,
        model_id=model_name
    ).first()

    if not coll_embedding:
        # Create new record
        coll_embedding = CollectionEmbedding(
            collection_id=collection_id,
            model_id=model_name,
            model_source=model_source,
            embedding_dimensions=embedding_dimensions,
            chroma_collection_name=chroma_collection_name,
            status='processing',
            progress=0,
            # Higher priority for VDR-2B model (multimodal)
            priority=100 if 'vdr-2b' in model_name.lower() else 50
        )
        db.session.add(coll_embedding)
        logger.info(
            f"[CollectionEmbedding] Created CollectionEmbedding record: "
            f"collection={collection_id}, model={model_name}"
        )
    else:
        # Update existing record
        coll_embedding.status = 'processing'
        coll_embedding.progress = 0
        coll_embedding.error_message = None
        coll_embedding.model_source = model_source
        coll_embedding.embedding_dimensions = embedding_dimensions
        logger.debug(
            f"[CollectionEmbedding] Updated CollectionEmbedding record: "
            f"collection={collection_id}, model={model_name}"
        )

    db.session.commit()
    return coll_embedding


def set_collection_chroma_name(collection_id: int, chroma_collection_name: str) -> None:
    """
    Store the ChromaDB collection name in the RAGCollection record.

    This enables the chat service to find the correct ChromaDB collection
    when performing semantic search.

    Args:
        collection_id: Collection ID
        chroma_collection_name: Sanitized ChromaDB collection name

    Database Effects:
        - Sets RAGCollection.chroma_collection_name if not already set
    """
    from db.database import db
    from db.tables import RAGCollection

    collection = RAGCollection.query.get(collection_id)
    if collection and not collection.chroma_collection_name:
        collection.chroma_collection_name = chroma_collection_name
        db.session.commit()
        logger.info(
            f"[CollectionEmbedding] Set chroma_collection_name: {chroma_collection_name}"
        )


# =============================================================================
# QUERY HELPERS
# =============================================================================

def get_pending_documents(collection_id: int) -> List:
    """
    Get documents pending embedding for a collection.

    Args:
        collection_id: Collection ID

    Returns:
        List of RAGDocument objects with status 'pending' or 'failed'
    """
    from db.tables import CollectionDocumentLink

    doc_links = CollectionDocumentLink.query.filter_by(
        collection_id=collection_id
    ).all()

    return [
        link.document
        for link in doc_links
        if link.document and link.document.status in ('pending', 'failed')
    ]


def count_indexed_documents(collection_id: int) -> int:
    """
    Count documents with 'indexed' status in a collection.

    Args:
        collection_id: Collection ID

    Returns:
        Number of indexed documents
    """
    from db.database import db
    from db.tables import RAGDocument, CollectionDocumentLink

    return (
        db.session.query(RAGDocument)
        .join(CollectionDocumentLink, RAGDocument.id == CollectionDocumentLink.document_id)
        .filter(
            CollectionDocumentLink.collection_id == collection_id,
            RAGDocument.status == 'indexed'
        )
        .count()
    )
