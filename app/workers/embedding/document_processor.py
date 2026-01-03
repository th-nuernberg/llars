# app/workers/embedding/document_processor.py
"""
Document Processor for the Embedding Worker.

This module handles the core document processing logic: loading documents,
splitting them into chunks, creating embeddings, and storing them in ChromaDB.

Processing Pipeline:
    1. Load document content from file
    2. Split into chunks using lumber_chunker
    3. Create embeddings for each chunk
    4. Store chunks in database and ChromaDB
    5. Update collection statistics
    6. Process image chunks if model supports multimodal

Author: LLARS Team
Date: January 2026
"""

import logging
import hashlib
import os
import uuid
from datetime import datetime
from typing import List, Tuple, Optional, Any

from workers.embedding.constants import (
    CHROMA_COLLECTION_METADATA,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
)
from workers.embedding.progress_emitter import ProgressTracker
from workers.embedding.image_processor import embed_image_chunks

logger = logging.getLogger(__name__)


def process_document(
    doc,
    db,
    embedding_resolver,
    pipeline
) -> None:
    """
    Process a single document: create chunks and embeddings.

    With the n:m Collection-Document linking system, a document can be in
    multiple collections. Embeddings are stored once and all linked
    collections' stats are updated.

    Args:
        doc: RAGDocument instance to process
        db: Database session
        embedding_resolver: EmbeddingResolver instance for getting embeddings
        pipeline: RAGPipeline instance for default configuration

    Raises:
        ValueError: If document has no collection or no text could be extracted
        Exception: On embedding or storage failures

    Note:
        Updates document status to 'processing' at start and 'indexed' on completion.
        On failure, status is set to 'failed' with error message.
    """
    from db.tables import RAGDocumentChunk, RAGCollection, RAGProcessingQueue, CollectionDocumentLink
    from langchain_chroma import Chroma
    from services.rag.collection_embedding_service import (
        sanitize_chroma_collection_name,
        sanitize_chroma_metadata
    )

    logger.info(f"[DocumentProcessor] Processing document {doc.id}: {doc.filename}")

    # Initialize progress tracker
    tracker = ProgressTracker(doc)

    # Update status to processing
    doc.status = 'processing'
    db.session.commit()

    # Update queue entry
    queue_entry = _update_queue_status(doc.id, 'processing', 10, 'Loading document', db)
    tracker.start()

    # Update progress for chunking
    _update_queue_status(doc.id, None, 30, 'Splitting into chunks', db)
    tracker.update_chunking(30)

    # Split document into chunks
    chunks = _split_document(doc)

    logger.info(f"[DocumentProcessor] Document {doc.id} split into {len(chunks)} chunks")

    # Update progress for embedding
    _update_queue_status(doc.id, None, 50, 'Creating embeddings', db)

    # Get collections for this document
    linked_collections = _get_linked_collections(doc, db)

    if not linked_collections:
        raise ValueError(f"Document {doc.id} has no collection assigned")

    # Get primary collection and embedding model
    primary_collection = linked_collections[0]
    target_model = primary_collection.embedding_model or pipeline.model_name
    embeddings = embedding_resolver.get_embeddings(target_model)

    # Setup ChromaDB collection
    collection_name = sanitize_chroma_collection_name(
        primary_collection.name,
        target_model
    )
    vectorstore_dir = _get_vectorstore_dir(pipeline.storage_dir, target_model)

    # Update collection metadata
    _update_collection_metadata(primary_collection, collection_name, target_model)

    # Clean up existing text chunks for retries
    _cleanup_existing_chunks(doc, collection_name, vectorstore_dir, embeddings, db)

    # Create chunks and store in DB + ChromaDB
    vector_ids = _create_and_store_chunks(
        doc=doc,
        chunks=chunks,
        target_model=target_model,
        collection_name=collection_name,
        vectorstore_dir=vectorstore_dir,
        embeddings=embeddings,
        linked_collections=linked_collections,
        tracker=tracker,
        db=db
    )

    # Embed image chunks if supported
    embed_image_chunks(
        doc=doc,
        collection_id=primary_collection.id,
        collection_name=collection_name,
        vectorstore_dir=vectorstore_dir,
        model_id=target_model,
        db=db
    )

    # Finalize document
    _finalize_document(
        doc=doc,
        chunks=chunks,
        vector_ids=vector_ids,
        linked_collections=linked_collections,
        pipeline=pipeline,
        db=db
    )

    # Update lexical search index
    _update_lexical_index(doc.id)

    # Emit completion
    tracker.complete()
    logger.info(
        f"[DocumentProcessor] Document {doc.id} indexed successfully "
        f"with {len(chunks)} chunks"
    )


def _split_document(doc) -> List:
    """
    Split document into chunks using lumber_chunker.

    Args:
        doc: RAGDocument instance

    Returns:
        List of Chunk objects with text, page_number, start_char, end_char

    Raises:
        ValueError: If no text could be extracted
    """
    from services.rag.lumber_chunker import chunk_file

    chunks = chunk_file(
        doc.file_path,
        doc.mime_type,
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    )

    if not chunks:
        raise ValueError(f"Could not extract any text from {doc.file_path}")

    return chunks


def _get_linked_collections(doc, db) -> List:
    """
    Get all collections linked to a document.

    Args:
        doc: RAGDocument instance
        db: Database session

    Returns:
        List of RAGCollection instances
    """
    from db.tables import RAGCollection

    # Get collections via links (n:m relationship)
    linked_collections = [
        link.collection for link in doc.collection_links if link.collection
    ]

    # Fallback to legacy collection_id field
    if not linked_collections and doc.collection_id:
        collection = RAGCollection.query.get(doc.collection_id)
        if collection:
            linked_collections = [collection]

    return linked_collections


def _get_vectorstore_dir(storage_dir: str, model_id: str) -> str:
    """
    Get or create vectorstore directory for a model.

    Args:
        storage_dir: Base storage directory
        model_id: Embedding model identifier

    Returns:
        Path to vectorstore directory
    """
    vectorstore_dir = os.path.join(
        storage_dir,
        "vectorstore",
        model_id.replace('/', '_')
    )
    os.makedirs(vectorstore_dir, exist_ok=True)
    return vectorstore_dir


def _update_collection_metadata(
    collection,
    collection_name: str,
    target_model: str
) -> None:
    """
    Update collection's ChromaDB name and embedding model.

    Args:
        collection: RAGCollection instance
        collection_name: Sanitized ChromaDB collection name
        target_model: Embedding model ID
    """
    if collection.chroma_collection_name != collection_name:
        collection.chroma_collection_name = collection_name
    if collection.embedding_model != target_model:
        collection.embedding_model = target_model


def _cleanup_existing_chunks(
    doc,
    collection_name: str,
    vectorstore_dir: str,
    embeddings,
    db
) -> None:
    """
    Clean up existing text chunks/vectors for document retries.

    Keeps image chunks intact, only removes text chunks.

    Args:
        doc: RAGDocument instance
        collection_name: ChromaDB collection name
        vectorstore_dir: ChromaDB storage directory
        embeddings: Embedding function for Chroma
        db: Database session
    """
    from db.tables import RAGDocumentChunk
    from langchain_chroma import Chroma

    try:
        existing_chunks = RAGDocumentChunk.query.filter_by(document_id=doc.id).all()
        text_vector_ids = [
            c.vector_id for c in existing_chunks
            if c and c.vector_id and not c.has_image
        ]

        if existing_chunks:
            try:
                vectorstore = Chroma(
                    collection_name=collection_name,
                    persist_directory=vectorstore_dir,
                    embedding_function=embeddings,
                    collection_metadata=CHROMA_COLLECTION_METADATA,
                )

                if text_vector_ids:
                    try:
                        vectorstore._collection.delete(ids=text_vector_ids)
                    except Exception:
                        try:
                            vectorstore.delete(ids=text_vector_ids)
                        except Exception:
                            pass

            except Exception as e:
                logger.warning(
                    f"[DocumentProcessor] Could not delete old vectors for doc {doc.id}: {e}"
                )

            # Delete text chunks from database
            RAGDocumentChunk.query.filter_by(
                document_id=doc.id,
                has_image=False
            ).delete()

            doc.vector_ids = None
            doc.chunk_count = 0
            db.session.commit()

    except Exception as e:
        logger.warning(f"[DocumentProcessor] Cleanup skipped for doc {doc.id}: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass


def _create_and_store_chunks(
    doc,
    chunks: List,
    target_model: str,
    collection_name: str,
    vectorstore_dir: str,
    embeddings,
    linked_collections: List,
    tracker: ProgressTracker,
    db
) -> List[str]:
    """
    Create chunks in database and store embeddings in ChromaDB.

    Args:
        doc: RAGDocument instance
        chunks: List of Chunk objects from splitting
        target_model: Embedding model ID
        collection_name: ChromaDB collection name
        vectorstore_dir: ChromaDB storage directory
        embeddings: Embedding function
        linked_collections: List of linked RAGCollection instances
        tracker: ProgressTracker for emitting progress
        db: Database session

    Returns:
        List of vector IDs for all chunks
    """
    from db.tables import RAGDocumentChunk
    from langchain_chroma import Chroma
    from services.rag.collection_embedding_service import sanitize_chroma_metadata

    vector_ids = []

    for i, chunk in enumerate(chunks):
        try:
            chunk_text = chunk.text
            chunk_id = f"doc_{doc.id}_chunk_{i}_{uuid.uuid4().hex[:8]}"

            # Store in database
            db_chunk = RAGDocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk_text,
                content_hash=_hash_content(chunk_text),
                page_number=chunk.page_number,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                embedding_model=target_model,
                embedding_status='completed',
                vector_id=chunk_id
            )
            db.session.add(db_chunk)
            vector_ids.append(chunk_id)

            # Update progress every 5 chunks
            if i % 5 == 0:
                _update_queue_status(
                    doc.id, None,
                    50 + int((i + 1) / len(chunks) * 40),
                    f'Embedding chunk {i+1}/{len(chunks)}',
                    db
                )

            # Emit progress every 10 chunks
            if i % 10 == 0:
                tracker.update_embedding(50, i, len(chunks))

        except Exception as e:
            logger.error(
                f"[DocumentProcessor] Error creating chunk {i} of doc {doc.id}: {e}"
            )
            raise

    # Add all chunks to ChromaDB in one batch
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            persist_directory=vectorstore_dir,
            embedding_function=embeddings,
            collection_metadata=CHROMA_COLLECTION_METADATA,
        )

        collection_ids = [c.id for c in linked_collections]
        primary_collection = linked_collections[0]

        vectorstore.add_texts(
            texts=[c.text for c in chunks],
            ids=vector_ids,
            metadatas=[
                sanitize_chroma_metadata({
                    'document_id': doc.id,
                    'chunk_index': i,
                    'filename': doc.filename,
                    'collection_id': primary_collection.id,
                    'collection_ids': ','.join(map(str, collection_ids)),
                    'page_number': chunks[i].page_number,
                    'start_char': chunks[i].start_char,
                    'end_char': chunks[i].end_char,
                    'vector_id': vector_ids[i]
                })
                for i in range(len(chunks))
            ]
        )

        logger.info(
            f"[DocumentProcessor] Added {len(chunks)} chunks to ChromaDB "
            f"collection {collection_name}"
        )

    except Exception as e:
        logger.error(f"[DocumentProcessor] Error adding to ChromaDB: {e}")
        raise

    return vector_ids


def _finalize_document(
    doc,
    chunks: List,
    vector_ids: List[str],
    linked_collections: List,
    pipeline,
    db
) -> None:
    """
    Finalize document processing and update statistics.

    Args:
        doc: RAGDocument instance
        chunks: List of processed chunks
        vector_ids: List of vector IDs
        linked_collections: List of linked collections
        pipeline: RAGPipeline for model name
        db: Database session
    """
    from db.tables import RAGDocumentChunk, RAGProcessingQueue, CollectionDocumentLink

    # Update document status
    doc.status = 'indexed'
    doc.processed_at = datetime.now()
    doc.indexed_at = datetime.now()
    doc.chunk_count = len(chunks)
    doc.vector_ids = vector_ids
    doc.embedding_model = pipeline.model_name

    # Update stats for ALL linked collections
    for coll in linked_collections:
        linked_doc_ids = db.session.query(CollectionDocumentLink.document_id).filter(
            CollectionDocumentLink.collection_id == coll.id
        ).subquery()

        coll.total_chunks = RAGDocumentChunk.query.filter(
            RAGDocumentChunk.document_id.in_(linked_doc_ids)
        ).count()

        logger.debug(
            f"[DocumentProcessor] Updated collection {coll.id} "
            f"total_chunks: {coll.total_chunks}"
        )

    # Update queue entry
    queue_entry = RAGProcessingQueue.query.filter_by(document_id=doc.id).first()
    if queue_entry:
        queue_entry.status = 'completed'
        queue_entry.progress_percent = 100
        queue_entry.current_step = 'Completed'
        queue_entry.completed_at = datetime.now()

    db.session.commit()


def _update_queue_status(
    document_id: int,
    status: Optional[str],
    progress: int,
    step: str,
    db
) -> Optional[Any]:
    """
    Update the processing queue entry for a document.

    Args:
        document_id: Document ID
        status: New status (or None to keep current)
        progress: Progress percentage
        step: Current step description
        db: Database session

    Returns:
        RAGProcessingQueue entry or None
    """
    from db.tables import RAGProcessingQueue

    queue_entry = RAGProcessingQueue.query.filter_by(document_id=document_id).first()

    if queue_entry:
        if status:
            queue_entry.status = status
            if status == 'processing':
                queue_entry.started_at = datetime.now()
        queue_entry.progress_percent = progress
        queue_entry.current_step = step
        db.session.commit()

    return queue_entry


def _update_lexical_index(document_id: int) -> None:
    """
    Update the lexical search index for a document.

    Args:
        document_id: Document ID to reindex
    """
    try:
        from services.chatbot.lexical_index import LexicalSearchIndex
        LexicalSearchIndex.reindex_document(document_id)
    except Exception as e:
        logger.warning(
            f"[DocumentProcessor] Lexical index update failed for doc {document_id}: {e}"
        )


def _hash_content(content: str) -> str:
    """
    Generate SHA-256 hash for chunk content.

    Args:
        content: Text content to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def load_document_content(doc) -> str:
    """
    Load content from document file.

    Args:
        doc: RAGDocument instance

    Returns:
        File content as string (empty if file not found or read error)
    """
    if not os.path.exists(doc.file_path):
        logger.warning(f"[DocumentProcessor] File not found: {doc.file_path}")
        return ""

    try:
        with open(doc.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"[DocumentProcessor] Error reading file {doc.file_path}: {e}")
        return ""
