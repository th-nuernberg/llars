# embedding_chroma.py
"""
ChromaDB operations for the Collection Embedding Service.

This module handles all ChromaDB interactions:
- Creating and accessing vectorstore collections
- Upserting document chunks with embeddings
- Backfilling chunks when collections become empty
- Batch operations for memory efficiency

ChromaDB is used as the vector store for semantic search in the RAG pipeline.
Each collection in the LLARS database maps to a ChromaDB collection with
a sanitized name.

Used by: collection_embedding_service.py, embedding_chunks.py
Depends on: embedding_constants.py
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from .embedding_constants import (
    CHROMA_COLLECTION_METADATA,
    sanitize_chroma_metadata,
)

logger = logging.getLogger(__name__)


# =============================================================================
# VECTORSTORE INITIALIZATION
# =============================================================================

def get_or_create_vectorstore(
    collection_name: str,
    vectorstore_dir: str,
    embeddings
):
    """
    Get or create a ChromaDB vectorstore collection.

    Creates a Chroma collection with cosine distance similarity metric.
    If the collection already exists, returns a handle to it.

    Args:
        collection_name: Sanitized ChromaDB collection name
        vectorstore_dir: Directory for persistent storage
        embeddings: LangChain embedding function

    Returns:
        Chroma vectorstore instance

    Raises:
        Exception: If ChromaDB initialization fails
    """
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=collection_name,
        persist_directory=vectorstore_dir,
        embedding_function=embeddings,
        collection_metadata=CHROMA_COLLECTION_METADATA,
    )


def get_vectorstore_without_embeddings(
    collection_name: str,
    vectorstore_dir: str
):
    """
    Get a ChromaDB vectorstore without embedding function.

    Used when adding pre-computed embeddings directly (e.g., image embeddings).

    Args:
        collection_name: Sanitized ChromaDB collection name
        vectorstore_dir: Directory for persistent storage

    Returns:
        Chroma vectorstore instance without embedding function
    """
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=collection_name,
        persist_directory=vectorstore_dir,
        collection_metadata=CHROMA_COLLECTION_METADATA,
    )


# =============================================================================
# CHUNK UPSERTION
# =============================================================================

def upsert_chunks_to_chroma(
    vectorstore,
    texts: List[str],
    ids: List[str],
    metadatas: List[Dict[str, Any]],
    collection_name: str
) -> int:
    """
    Upsert text chunks into ChromaDB collection.

    Performs deduplication within the batch and uses ChromaDB's upsert
    semantics to handle existing chunks gracefully.

    Args:
        vectorstore: Chroma vectorstore instance
        texts: List of text contents to embed
        ids: List of unique vector IDs
        metadatas: List of metadata dictionaries
        collection_name: Collection name for logging

    Returns:
        Number of chunks successfully upserted

    Raises:
        Exception: If ChromaDB upsert fails

    Note:
        ChromaDB's add_texts uses upsert semantics, so repeated IDs
        will update rather than duplicate.
    """
    if not texts:
        return 0

    # Deduplicate within batch (protects against malformed data)
    seen = set()
    texts_unique = []
    ids_unique = []
    metadatas_unique = []

    for text, vid, meta in zip(texts, ids, metadatas):
        if not vid or vid in seen:
            continue
        seen.add(vid)
        texts_unique.append(text)
        ids_unique.append(vid)
        metadatas_unique.append(meta)

    if not texts_unique:
        return 0

    vectorstore.add_texts(
        texts=texts_unique,
        ids=ids_unique,
        metadatas=metadatas_unique
    )

    logger.info(
        f"[CollectionEmbedding] Upserted {len(ids_unique)} chunks "
        f"into ChromaDB collection {collection_name}"
    )

    return len(ids_unique)


def upsert_embeddings_to_chroma(
    vectorstore,
    ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    collection_name: str
) -> int:
    """
    Upsert pre-computed embeddings into ChromaDB collection.

    Used for image embeddings where we have pre-computed vectors
    rather than text to embed.

    Args:
        vectorstore: Chroma vectorstore instance
        ids: List of unique vector IDs
        embeddings: List of embedding vectors
        documents: List of document texts (for storage, not embedding)
        metadatas: List of metadata dictionaries
        collection_name: Collection name for logging

    Returns:
        Number of embeddings successfully upserted
    """
    if not ids:
        return 0

    try:
        vectorstore._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

        logger.info(
            f"[CollectionEmbedding] Upserted {len(ids)} embeddings "
            f"into ChromaDB collection {collection_name}"
        )

        return len(ids)

    except Exception as exc:
        logger.warning(
            f"[CollectionEmbedding] Embedding upsert failed "
            f"for collection {collection_name}: {exc}"
        )
        return 0


# =============================================================================
# BACKFILL OPERATIONS
# =============================================================================

def backfill_empty_collection(
    collection_id: int,
    collection_name: str,
    vectorstore_dir: str,
    embeddings
) -> int:
    """
    Backfill chunks into an empty ChromaDB collection.

    This handles cases where:
    - A document was deduplicated and linked from another collection
    - The ChromaDB collection was cleared but DB chunks remain
    - Service restart caused state inconsistency

    Args:
        collection_id: Database collection ID
        collection_name: Sanitized ChromaDB collection name
        vectorstore_dir: Directory for persistent storage
        embeddings: LangChain embedding function

    Returns:
        Number of chunks backfilled

    Database Effects:
        Reads chunks via joins, does not modify database
    """
    from db.database import db
    from db.tables import RAGDocument, RAGDocumentChunk, CollectionDocumentLink

    try:
        vectorstore = get_or_create_vectorstore(
            collection_name, vectorstore_dir, embeddings
        )

        # Check if collection is actually empty
        if vectorstore._collection.count() > 0:
            return 0

        logger.warning(
            f"[CollectionEmbedding] ChromaDB collection '{collection_name}' "
            f"is empty but DB has chunks; backfilling"
        )

        # Load all chunks for this collection via joins
        chunks_to_backfill = (
            db.session.query(RAGDocumentChunk)
            .join(RAGDocument, RAGDocument.id == RAGDocumentChunk.document_id)
            .join(CollectionDocumentLink, CollectionDocumentLink.document_id == RAGDocument.id)
            .filter(CollectionDocumentLink.collection_id == collection_id)
            .order_by(
                RAGDocumentChunk.document_id.asc(),
                RAGDocumentChunk.chunk_index.asc()
            )
            .all()
        )

        # Filter chunks that have vector_ids (skip unembedded image chunks)
        chunks_with_ids = [c for c in chunks_to_backfill if c.vector_id]
        skipped = len(chunks_to_backfill) - len(chunks_with_ids)

        if skipped > 0:
            logger.warning(
                f"[CollectionEmbedding] Skipping {skipped} chunks "
                f"without vector_id during backfill"
            )

        if not chunks_with_ids:
            return 0

        # Batch upserts to keep memory bounded
        backfilled = _batch_backfill_chunks(
            vectorstore, chunks_with_ids, collection_id
        )

        logger.info(
            f"[CollectionEmbedding] Backfilled {backfilled} chunks "
            f"into ChromaDB collection {collection_name}"
        )

        return backfilled

    except Exception as e:
        logger.error(
            f"[CollectionEmbedding] Failed to backfill "
            f"Chroma collection {collection_name}: {e}"
        )
        return 0


def _batch_backfill_chunks(
    vectorstore,
    chunks: List,
    collection_id: int,
    batch_size: int = 256
) -> int:
    """
    Backfill chunks in batches to manage memory.

    Args:
        vectorstore: Chroma vectorstore instance
        chunks: List of RAGDocumentChunk objects
        collection_id: Collection ID for metadata
        batch_size: Number of chunks per batch (default: 256)

    Returns:
        Total number of chunks backfilled
    """
    total_backfilled = 0

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]

        texts = [c.content for c in batch]
        ids = [c.vector_id for c in batch]
        metadatas = []

        for c in batch:
            # Get filename from document relationship
            filename = getattr(c.document, "filename", None)
            metadatas.append(sanitize_chroma_metadata({
                'document_id': c.document_id,
                'chunk_index': c.chunk_index,
                'filename': filename,
                'collection_id': collection_id,
                'page_number': c.page_number,
                'start_char': c.start_char,
                'end_char': c.end_char,
                'vector_id': c.vector_id,
            }))

        # ChromaDB add_texts uses upsert, so repeated IDs are safe
        vectorstore.add_texts(texts=texts, ids=ids, metadatas=metadatas)
        total_backfilled += len(batch)

    return total_backfilled


# =============================================================================
# COLLECTION UTILITIES
# =============================================================================

def get_collection_count(
    collection_name: str,
    vectorstore_dir: str
) -> int:
    """
    Get the number of vectors in a ChromaDB collection.

    Args:
        collection_name: Sanitized ChromaDB collection name
        vectorstore_dir: Directory for persistent storage

    Returns:
        Number of vectors in the collection, or 0 if collection doesn't exist
    """
    try:
        from langchain_chroma import Chroma

        vectorstore = Chroma(
            collection_name=collection_name,
            persist_directory=vectorstore_dir,
            collection_metadata=CHROMA_COLLECTION_METADATA,
        )
        return vectorstore._collection.count()

    except Exception as e:
        logger.warning(
            f"[CollectionEmbedding] Could not get count for "
            f"collection {collection_name}: {e}"
        )
        return 0
