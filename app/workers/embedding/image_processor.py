# app/workers/embedding/image_processor.py
"""
Image Embedding Processor for the Embedding Worker.

This module handles embedding of image chunks for documents that contain
images. It uses multimodal embedding models (like VDR-2B) to create
vector representations of images.

Features:
    - Automatic detection of image-capable models
    - Batch processing of image chunks
    - Vector storage in ChromaDB with image metadata
    - Skip already-embedded images for efficiency

Supported Models:
    - llamaindex/vdr-2b-multi-v1 (via ImageEmbeddingService)

Author: LLARS Team
Date: January 2026
"""

import logging
import uuid
from typing import List, Optional

from workers.embedding.constants import CHROMA_COLLECTION_METADATA

logger = logging.getLogger(__name__)


def embed_image_chunks(
    doc,
    collection_id: int,
    collection_name: str,
    vectorstore_dir: str,
    model_id: str,
    db
) -> int:
    """
    Embed image chunks for a document using multimodal embeddings.

    Processes all image chunks associated with a document, creating
    vector embeddings and storing them in ChromaDB.

    Args:
        doc: RAGDocument instance containing image chunks
        collection_id: ID of the RAG collection
        collection_name: Sanitized ChromaDB collection name
        vectorstore_dir: Directory path for ChromaDB storage
        model_id: Embedding model identifier
        db: Database session for updates

    Returns:
        int: Number of image chunks successfully embedded

    Note:
        - Only processes chunks where has_image=True
        - Skips chunks that are already embedded with the same model
        - Updates chunk metadata in database after embedding
    """
    from db.tables import RAGDocumentChunk
    from services.rag.image_embedding_service import ImageEmbeddingService

    # Check if model supports image embeddings
    if not ImageEmbeddingService.supports_model(model_id):
        logger.debug(f"[ImageProcessor] Model {model_id} doesn't support images")
        return 0

    # Get image chunks for this document
    image_chunks = (
        RAGDocumentChunk.query
        .filter_by(document_id=doc.id, has_image=True)
        .all()
    )

    if not image_chunks:
        return 0

    # Filter to chunks that need embedding
    to_embed = _filter_chunks_to_embed(image_chunks, model_id)

    if not to_embed:
        logger.debug(f"[ImageProcessor] All image chunks already embedded for doc {doc.id}")
        return 0

    # Get embeddings for all images
    image_paths = [c.image_path for c in to_embed]
    embeddings = ImageEmbeddingService.embed_image_paths(model_id, image_paths)

    # Store embeddings in ChromaDB
    embedded_count = _store_image_embeddings(
        doc=doc,
        chunks=to_embed,
        embeddings=embeddings,
        collection_id=collection_id,
        collection_name=collection_name,
        vectorstore_dir=vectorstore_dir,
        model_id=model_id,
        db=db
    )

    return embedded_count


def _filter_chunks_to_embed(
    chunks: List,
    model_id: str
) -> List:
    """
    Filter image chunks to those that need embedding.

    Args:
        chunks: List of RAGDocumentChunk instances
        model_id: Target embedding model

    Returns:
        List of chunks that need to be embedded
    """
    to_embed = []

    for chunk in chunks:
        # Skip if no image path
        if not chunk.image_path:
            continue

        # Skip if already embedded with this model
        if (chunk.vector_id and
            chunk.embedding_status == 'completed' and
            chunk.embedding_model == model_id):
            continue

        to_embed.append(chunk)

    return to_embed


def _store_image_embeddings(
    doc,
    chunks: List,
    embeddings: List[Optional[List[float]]],
    collection_id: int,
    collection_name: str,
    vectorstore_dir: str,
    model_id: str,
    db
) -> int:
    """
    Store image embeddings in ChromaDB and update chunk metadata.

    Args:
        doc: RAGDocument instance
        chunks: List of image chunks to embed
        embeddings: List of embedding vectors (or None for failed)
        collection_id: RAG collection ID
        collection_name: ChromaDB collection name
        vectorstore_dir: ChromaDB storage directory
        model_id: Embedding model ID
        db: Database session

    Returns:
        int: Number of successfully embedded chunks
    """
    from langchain_chroma import Chroma
    from services.rag.collection_embedding_service import sanitize_chroma_metadata

    # Prepare batch data
    ids = []
    documents = []
    metadatas = []
    vectors = []

    for chunk, embedding in zip(chunks, embeddings):
        if not embedding:
            chunk.embedding_status = 'failed'
            chunk.embedding_error = 'Image embedding failed or unavailable'
            continue

        # Generate vector ID if needed
        if not chunk.vector_id:
            chunk.vector_id = f"doc_{doc.id}_img_{chunk.chunk_index}_{uuid.uuid4().hex[:8]}"

        # Update chunk metadata
        chunk.embedding_model = model_id
        chunk.embedding_dimensions = len(embedding)
        chunk.embedding_status = 'completed'
        chunk.embedding_error = None

        # Prepare ChromaDB data
        content = chunk.content or chunk.image_alt_text or "[Bild]"
        ids.append(chunk.vector_id)
        documents.append(content)
        metadatas.append(sanitize_chroma_metadata({
            'document_id': doc.id,
            'chunk_index': chunk.chunk_index,
            'filename': doc.filename,
            'collection_id': collection_id,
            'page_number': chunk.page_number,
            'start_char': chunk.start_char,
            'end_char': chunk.end_char,
            'vector_id': chunk.vector_id,
            'has_image': True,
            'image_path': chunk.image_path,
            'image_url': chunk.image_url,
            'image_alt_text': chunk.image_alt_text,
            'image_mime_type': chunk.image_mime_type
        }))
        vectors.append(embedding)

    # Store in ChromaDB
    if ids:
        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=vectorstore_dir,
                collection_metadata=CHROMA_COLLECTION_METADATA,
            )

            vectorstore._collection.upsert(
                ids=ids,
                embeddings=vectors,
                metadatas=metadatas,
                documents=documents
            )

            logger.info(
                f"[ImageProcessor] Embedded {len(ids)} image chunks for doc {doc.id}"
            )

        except Exception as exc:
            logger.warning(f"[ImageProcessor] Image upsert failed for doc {doc.id}: {exc}")
            # Mark chunks as failed
            for chunk in chunks:
                if chunk.vector_id in ids:
                    chunk.embedding_status = 'failed'
                    chunk.embedding_error = str(exc)[:500]

    # Commit database changes
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return len(ids)


def get_pending_image_chunks(document_id: int) -> List:
    """
    Get all image chunks that still need embedding.

    Args:
        document_id: ID of the document

    Returns:
        List of RAGDocumentChunk instances with has_image=True
        that haven't been successfully embedded yet
    """
    from db.tables import RAGDocumentChunk

    return (
        RAGDocumentChunk.query
        .filter_by(document_id=document_id, has_image=True)
        .filter(RAGDocumentChunk.embedding_status != 'completed')
        .all()
    )
