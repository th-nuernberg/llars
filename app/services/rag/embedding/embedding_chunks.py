# embedding_chunks.py
"""
Chunk processing for the Collection Embedding Service.

This module handles:
- Creating and updating document chunks in the database
- Processing existing chunks vs creating new ones
- Image chunk embedding for multimodal models
- Chunk metadata preparation for ChromaDB

Document chunking workflow:
1. Document content is split into text chunks
2. Each chunk is stored in RAGDocumentChunk table
3. Chunks are embedded and stored in ChromaDB
4. Image chunks (screenshots, inline images) are processed separately

Used by: collection_embedding_service.py
Depends on: embedding_constants.py, embedding_chroma.py
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Dict, Any, Tuple, Optional

from .embedding_constants import sanitize_chroma_metadata, hash_content

logger = logging.getLogger(__name__)


# =============================================================================
# TEXT CHUNK PROCESSING
# =============================================================================

def process_document_chunks(
    doc,
    chunks: List,
    collection_id: int,
    pipeline
) -> Tuple[List[str], List[str], List[Dict[str, Any]], List[str]]:
    """
    Process document chunks and prepare them for ChromaDB.

    Handles both new chunks and existing chunks (for retries/deduplication).
    Existing chunks are updated in place, new chunks are created.

    Args:
        doc: RAGDocument object being processed
        chunks: List of chunk objects from lumber_chunker
        collection_id: ID of the collection
        pipeline: RAGPipeline instance with model info

    Returns:
        Tuple of:
            - texts: List of chunk text contents
            - ids: List of vector IDs
            - metadatas: List of metadata dicts
            - all_vector_ids: All vector IDs (for document update)

    Database Effects:
        - Creates new RAGDocumentChunk records for new chunks
        - Updates existing chunks if found
        - Does NOT commit - caller must commit
    """
    from db.database import db
    from db.tables import RAGDocumentChunk

    # Get existing chunks for this document (text chunks only)
    existing_chunks = (
        RAGDocumentChunk.query
        .filter_by(document_id=doc.id)
        .filter(RAGDocumentChunk.has_image.is_(False))
        .all()
    )
    existing_by_index = {c.chunk_index: c for c in existing_chunks}

    chroma_texts = []
    chroma_ids = []
    chroma_metadatas = []
    all_vector_ids = []

    for i, chunk in enumerate(chunks):
        chunk_text = chunk.text
        content_hash = hash_content(chunk_text)
        existing_chunk = existing_by_index.get(i)

        if existing_chunk:
            # Reuse existing DB chunk, update content
            texts, ids, metadatas, vector_id = _update_existing_chunk(
                existing_chunk, chunk, chunk_text, content_hash,
                doc, collection_id, pipeline
            )
        else:
            # Create new chunk
            texts, ids, metadatas, vector_id = _create_new_chunk(
                i, chunk, chunk_text, content_hash,
                doc, collection_id, pipeline, db
            )

        chroma_texts.extend(texts)
        chroma_ids.extend(ids)
        chroma_metadatas.extend(metadatas)
        all_vector_ids.append(vector_id)

    return chroma_texts, chroma_ids, chroma_metadatas, all_vector_ids


def _update_existing_chunk(
    existing_chunk,
    chunk,
    chunk_text: str,
    content_hash: str,
    doc,
    collection_id: int,
    pipeline
) -> Tuple[List[str], List[str], List[Dict], str]:
    """
    Update an existing chunk with new content.

    Args:
        existing_chunk: Existing RAGDocumentChunk object
        chunk: New chunk data from chunker
        chunk_text: Text content of the chunk
        content_hash: SHA-256 hash of content
        doc: Parent RAGDocument
        collection_id: Collection ID for metadata
        pipeline: RAGPipeline with model info

    Returns:
        Tuple of (texts, ids, metadatas, vector_id) for ChromaDB
    """
    # Update existing chunk fields
    existing_chunk.content = chunk_text
    existing_chunk.content_hash = content_hash

    # Ensure vector_id exists
    if not existing_chunk.vector_id:
        existing_chunk.vector_id = f"doc_{doc.id}_chunk_{existing_chunk.chunk_index}_{uuid.uuid4().hex[:8]}"

    # Update position and model info
    existing_chunk.page_number = chunk.page_number
    existing_chunk.start_char = chunk.start_char
    existing_chunk.end_char = chunk.end_char
    existing_chunk.embedding_model = pipeline.model_name
    existing_chunk.embedding_dimensions = getattr(pipeline, "embedding_dimensions", None)
    existing_chunk.embedding_status = 'completed'
    existing_chunk.embedding_error = None

    chunk_id = existing_chunk.vector_id

    # Prepare ChromaDB data
    metadata = sanitize_chroma_metadata({
        'document_id': doc.id,
        'chunk_index': existing_chunk.chunk_index,
        'filename': doc.filename,
        'collection_id': collection_id,
        'page_number': chunk.page_number,
        'start_char': chunk.start_char,
        'end_char': chunk.end_char,
        'vector_id': chunk_id
    })

    return [chunk_text], [chunk_id], [metadata], chunk_id


def _create_new_chunk(
    index: int,
    chunk,
    chunk_text: str,
    content_hash: str,
    doc,
    collection_id: int,
    pipeline,
    db
) -> Tuple[List[str], List[str], List[Dict], str]:
    """
    Create a new chunk in the database.

    Args:
        index: Chunk index within document
        chunk: Chunk data from chunker
        chunk_text: Text content of the chunk
        content_hash: SHA-256 hash of content
        doc: Parent RAGDocument
        collection_id: Collection ID for metadata
        pipeline: RAGPipeline with model info
        db: SQLAlchemy database instance

    Returns:
        Tuple of (texts, ids, metadatas, vector_id) for ChromaDB
    """
    from db.tables import RAGDocumentChunk

    # Generate unique vector ID
    chunk_id = f"doc_{doc.id}_chunk_{index}_{uuid.uuid4().hex[:8]}"

    # Create database record
    db_chunk = RAGDocumentChunk(
        document_id=doc.id,
        chunk_index=index,
        content=chunk_text,
        content_hash=content_hash,
        vector_id=chunk_id,
        page_number=chunk.page_number,
        start_char=chunk.start_char,
        end_char=chunk.end_char,
        embedding_model=pipeline.model_name,
        embedding_dimensions=getattr(pipeline, "embedding_dimensions", None),
        embedding_status='completed'
    )
    db.session.add(db_chunk)

    # Prepare ChromaDB data
    metadata = sanitize_chroma_metadata({
        'document_id': doc.id,
        'chunk_index': index,
        'filename': doc.filename,
        'collection_id': collection_id,
        'page_number': chunk.page_number,
        'start_char': chunk.start_char,
        'end_char': chunk.end_char,
        'vector_id': chunk_id
    })

    return [chunk_text], [chunk_id], [metadata], chunk_id


# =============================================================================
# IMAGE CHUNK EMBEDDING
# =============================================================================

def embed_image_chunks_for_document(
    doc,
    collection_id: int,
    collection_name: str,
    vectorstore_dir: str,
    model_id: str
) -> int:
    """
    Embed image chunks for a document using multimodal embedding model.

    Processes image chunks (screenshots, inline images) that have image_path
    set but haven't been embedded yet with the current model.

    Args:
        doc: RAGDocument object
        collection_id: Collection ID
        collection_name: ChromaDB collection name
        vectorstore_dir: ChromaDB storage directory
        model_id: Embedding model ID

    Returns:
        Number of image chunks successfully embedded

    Database Effects:
        - Updates RAGDocumentChunk records with embedding info
        - Commits changes
    """
    from db.database import db
    from db.tables import RAGDocumentChunk
    from services.rag.image_embedding_service import ImageEmbeddingService
    from .embedding_chroma import get_vectorstore_without_embeddings

    # Check if model supports image embedding
    if not ImageEmbeddingService.supports_model(model_id):
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
    to_embed = _filter_chunks_needing_embedding(image_chunks, model_id)

    if not to_embed:
        return 0

    # Generate embeddings for images
    embeddings = ImageEmbeddingService.embed_image_paths(
        model_id,
        [c.image_path for c in to_embed]
    )

    # Get vectorstore for upsertion
    vectorstore = get_vectorstore_without_embeddings(
        collection_name, vectorstore_dir
    )

    # Prepare data for ChromaDB
    ids, documents, metadatas, vectors = _prepare_image_chunk_data(
        to_embed, embeddings, doc, collection_id, model_id
    )

    # Upsert to ChromaDB
    embedded_count = 0
    if ids:
        try:
            vectorstore._collection.upsert(
                ids=ids,
                embeddings=vectors,
                metadatas=metadatas,
                documents=documents
            )
            embedded_count = len(ids)
            logger.info(
                f"[CollectionEmbedding] Embedded {embedded_count} image chunks "
                f"for doc {doc.id}"
            )
        except Exception as exc:
            logger.warning(
                f"[CollectionEmbedding] Image upsert failed for doc {doc.id}: {exc}"
            )

    # Commit database changes
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return embedded_count


def _filter_chunks_needing_embedding(
    chunks: List,
    model_id: str
) -> List:
    """
    Filter image chunks that need embedding.

    A chunk needs embedding if:
    - It has an image_path
    - It doesn't have a vector_id, OR
    - It's not yet completed with this model

    Args:
        chunks: List of RAGDocumentChunk objects
        model_id: Current embedding model ID

    Returns:
        List of chunks that need embedding
    """
    to_embed = []
    for chunk in chunks:
        if not chunk.image_path:
            continue
        if (chunk.vector_id and
            chunk.embedding_status == 'completed' and
            chunk.embedding_model == model_id):
            continue
        to_embed.append(chunk)
    return to_embed


def _prepare_image_chunk_data(
    chunks: List,
    embeddings: List[Optional[List[float]]],
    doc,
    collection_id: int,
    model_id: str
) -> Tuple[List[str], List[str], List[Dict], List[List[float]]]:
    """
    Prepare image chunk data for ChromaDB upsertion.

    Updates chunk database records and prepares ChromaDB data.

    Args:
        chunks: List of RAGDocumentChunk objects
        embeddings: List of embedding vectors (None for failed)
        doc: Parent RAGDocument
        collection_id: Collection ID
        model_id: Embedding model ID

    Returns:
        Tuple of (ids, documents, metadatas, vectors) for ChromaDB
    """
    ids = []
    documents = []
    metadatas = []
    vectors = []

    for chunk, embedding in zip(chunks, embeddings):
        if not embedding:
            # Mark as failed
            chunk.embedding_status = 'failed'
            chunk.embedding_error = 'Image embedding failed or unavailable'
            continue

        # Ensure vector_id exists
        if not chunk.vector_id:
            chunk.vector_id = f"doc_{doc.id}_img_{chunk.chunk_index}_{uuid.uuid4().hex[:8]}"

        # Update chunk with embedding info
        chunk.embedding_model = model_id
        chunk.embedding_dimensions = len(embedding)
        chunk.embedding_status = 'completed'
        chunk.embedding_error = None

        # Prepare ChromaDB data
        content = chunk.content or chunk.image_alt_text or "[Bild]"

        ids.append(chunk.vector_id)
        documents.append(content)
        vectors.append(embedding)
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

    return ids, documents, metadatas, vectors
