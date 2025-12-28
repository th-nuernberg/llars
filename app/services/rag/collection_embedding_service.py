"""
Collection Embedding Service.

Manages the embedding process for entire collections, with real-time
WebSocket progress updates. Used by the Chatbot Builder wizard.
"""

import logging
import threading
import hashlib
import uuid
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, TypeVar
from functools import wraps

from flask import current_app
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

T = TypeVar('T')

# ChromaDB collection metadata for cosine distance
# IMPORTANT: This ensures proper similarity scoring for both normalized and unnormalized embeddings
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}


def retry_on_deadlock(max_retries: int = 3, delay: float = 0.5):
    """
    Decorator to retry database operations on deadlock.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (doubles each retry)
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
                    error_msg = str(e).lower()
                    if 'deadlock' in error_msg or '1213' in str(e):
                        last_exception = e
                        logger.warning(
                            f"[DB] Deadlock detected in {func.__name__}, "
                            f"attempt {attempt + 1}/{max_retries + 1}, retrying in {current_delay}s"
                        )
                        try:
                            db.session.rollback()
                        except Exception:
                            pass

                        if attempt < max_retries:
                            time.sleep(current_delay)
                            current_delay *= 2  # Exponential backoff
                            continue
                    raise
                except Exception as e:
                    # Check if it's a nested deadlock error
                    error_msg = str(e).lower()
                    if 'deadlock' in error_msg or '1213' in error_msg:
                        last_exception = e
                        logger.warning(
                            f"[DB] Deadlock detected (nested) in {func.__name__}, "
                            f"attempt {attempt + 1}/{max_retries + 1}"
                        )
                        try:
                            db.session.rollback()
                        except Exception:
                            pass

                        if attempt < max_retries:
                            time.sleep(current_delay)
                            current_delay *= 2
                            continue
                    raise

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def sanitize_chroma_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    ChromaDB metadata must only contain primitive values (str/int/float/bool) and must not contain None.
    """
    if not metadata:
        return {}

    cleaned: Dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = str(value)
    return cleaned


def sanitize_chroma_collection_name(name: str, model_name: str) -> str:
    """
    Create a valid ChromaDB collection name.

    ChromaDB requires:
    - 3-63 characters
    - Start and end with alphanumeric
    - Only alphanumeric, underscores, or hyphens
    - No consecutive periods
    - Not a valid IPv4 address

    Args:
        name: The collection name from database
        model_name: The embedding model name

    Returns:
        A valid ChromaDB collection name
    """
    # Replace invalid characters with underscores
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    clean_model = re.sub(r'[^a-zA-Z0-9_-]', '_', model_name.replace('/', '_'))

    # Build the full name
    full_name = f"llars_{clean_name}_{clean_model}"

    # Remove consecutive underscores
    full_name = re.sub(r'_+', '_', full_name)

    # Ensure it starts and ends with alphanumeric
    full_name = full_name.strip('_-')

    # Truncate to 63 characters max while keeping meaningful parts
    if len(full_name) > 63:
        # Keep prefix and hash the rest
        prefix = full_name[:50]
        suffix_hash = hashlib.md5(full_name.encode()).hexdigest()[:12]
        full_name = f"{prefix}_{suffix_hash}"

    # Final validation - ensure 3+ chars
    if len(full_name) < 3:
        full_name = f"col_{full_name}"

    return full_name


class CollectionEmbeddingService:
    """
    Service for embedding all documents in a collection with progress tracking.

    Supports:
    - Starting embedding for a collection
    - Real-time progress via WebSocket
    - Pause/Resume functionality
    - Error handling with detailed messages
    """

    def __init__(self, app=None):
        """Initialize the service with Flask app context."""
        self.app = app
        self._active_jobs: Dict[int, threading.Thread] = {}
        self._stop_events: Dict[int, threading.Event] = {}

    def start_embedding(self, collection_id: int, wait_for_more: bool = False, source_job_id: str = None) -> Dict[str, Any]:
        """
        Start embedding process for a collection.

        Args:
            collection_id: ID of the collection to embed
            wait_for_more: If True, keep waiting for new documents (live crawl)
            source_job_id: Optional crawler job id to detect when crawling is finished

        Returns:
            Dict with status and message
        """
        from db.db import db
        from db.tables import RAGCollection

        collection = RAGCollection.query.get(collection_id)
        if not collection:
            return {'success': False, 'error': 'Collection not found'}

        if collection.embedding_status == 'processing':
            # If the status says "processing" but no thread is running anymore (e.g. crash),
            # allow restarting the job instead of getting stuck forever.
            if collection_id in self._active_jobs:
                return {'success': True, 'message': 'Collection already processing'}
            logger.warning(
                f"[CollectionEmbedding] Collection {collection_id} marked 'processing' but no active job found; restarting"
            )
            collection.embedding_status = 'idle'
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        # Update collection status
        collection.embedding_status = 'processing'
        collection.embedding_progress = 0
        collection.embedding_error = None
        db.session.commit()

        # Recover documents stuck in 'processing' from interrupted runs.
        try:
            from db.tables import RAGDocument, CollectionDocumentLink

            stuck_docs = (
                db.session.query(RAGDocument)
                .join(CollectionDocumentLink, RAGDocument.id == CollectionDocumentLink.document_id)
                .filter(CollectionDocumentLink.collection_id == collection_id, RAGDocument.status == 'processing')
                .all()
            )
            if stuck_docs:
                for doc in stuck_docs:
                    doc.status = 'pending'
                db.session.commit()
                logger.info(
                    f"[CollectionEmbedding] Reset {len(stuck_docs)} documents from 'processing' to 'pending' for collection {collection_id}"
                )
        except Exception as e:
            db.session.rollback()
            logger.warning(f"[CollectionEmbedding] Failed to reset stuck documents for collection {collection_id}: {e}")

        # Create stop event for this collection
        self._stop_events[collection_id] = threading.Event()
        # Track live mode metadata
        if wait_for_more or source_job_id:
            if not hasattr(self, '_live_mode'):
                self._live_mode = {}
            self._live_mode[collection_id] = {
                'wait_for_more': wait_for_more,
                'source_job_id': source_job_id
            }

        # Start background thread
        app = current_app._get_current_object()
        thread = threading.Thread(
            target=self._process_collection,
            args=(app, collection_id),
            name=f"EmbedCollection_{collection_id}",
            daemon=True
        )
        self._active_jobs[collection_id] = thread
        thread.start()

        logger.info(f"[CollectionEmbedding] Started embedding for collection {collection_id}")
        return {'success': True, 'message': 'Embedding started'}

    def pause_embedding(self, collection_id: int) -> Dict[str, Any]:
        """Pause embedding process for a collection."""
        from db.db import db
        from db.tables import RAGCollection

        if collection_id in self._stop_events:
            self._stop_events[collection_id].set()

        collection = RAGCollection.query.get(collection_id)
        if collection and collection.embedding_status == 'processing':
            collection.embedding_status = 'idle'
            db.session.commit()
            logger.info(f"[CollectionEmbedding] Paused embedding for collection {collection_id}")
            return {'success': True, 'message': 'Embedding paused'}

        return {'success': False, 'error': 'Collection not processing'}

    def get_status(self, collection_id: int) -> Dict[str, Any]:
        """Get embedding status for a collection."""
        from db.tables import RAGCollection, RAGDocument, CollectionDocumentLink

        collection = RAGCollection.query.get(collection_id)
        if not collection:
            return {'success': False, 'error': 'Collection not found'}

        # Count documents via links
        total_docs = CollectionDocumentLink.query.filter_by(collection_id=collection_id).count()

        # Count indexed documents
        indexed_docs = db.session.query(RAGDocument).join(
            CollectionDocumentLink,
            RAGDocument.id == CollectionDocumentLink.document_id
        ).filter(
            CollectionDocumentLink.collection_id == collection_id,
            RAGDocument.status == 'indexed'
        ).count()

        return {
            'success': True,
            'collection_id': collection_id,
            'name': collection.name,
            'status': collection.embedding_status,
            'progress': collection.embedding_progress or 0,
            'error': collection.embedding_error,
            'documents_total': total_docs,
            'documents_indexed': indexed_docs,
            'total_chunks': collection.total_chunks,
            'is_active': collection_id in self._active_jobs
        }

    def _process_collection(self, app, collection_id: int):
        """
        Background process for embedding a collection.

        Args:
            app: Flask app for context
            collection_id: Collection ID to process
        """
        with app.app_context():
            try:
                self._do_embedding(collection_id)
            except Exception as e:
                logger.error(f"[CollectionEmbedding] Error processing collection {collection_id}: {e}")
                try:
                    from db.db import db
                    db.session.rollback()
                except Exception:
                    pass
                self._set_collection_error(collection_id, str(e))
            finally:
                # Cleanup
                if collection_id in self._active_jobs:
                    del self._active_jobs[collection_id]
                if collection_id in self._stop_events:
                    del self._stop_events[collection_id]

    def _do_embedding(self, collection_id: int):
        """
        Execute the actual embedding process.

        Args:
            collection_id: Collection ID to process
        """
        from db.db import db
        from db.tables import RAGCollection, RAGDocument, RAGDocumentChunk, CollectionDocumentLink
        from db.models.rag import CollectionEmbedding
        from rag_pipeline import RAGPipeline
        from langchain_chroma import Chroma
        from services.rag.embedding_model_service import get_embedding_model_service, ModelSource
        import os

        stop_event = self._stop_events.get(collection_id)
        collection = RAGCollection.query.get(collection_id)

        if not collection:
            raise ValueError(f"Collection {collection_id} not found")

        logger.info(f"[CollectionEmbedding] Processing collection {collection.id}: {collection.name}")

        # Initialize RAG pipeline early to set chroma_collection_name
        pipeline = RAGPipeline()
        collection_name = sanitize_chroma_collection_name(collection.name, pipeline.model_name)

        # Determine model source (litellm or local)
        model_service = get_embedding_model_service()
        model_info = model_service.check_model_availability(pipeline.model_name)
        model_source = model_info.source.value if model_info.source else 'local'
        embedding_dimensions = model_info.dimensions or pipeline.embedding_dimensions

        # Create or update CollectionEmbedding record
        coll_embedding = CollectionEmbedding.query.filter_by(
            collection_id=collection_id,
            model_id=pipeline.model_name
        ).first()

        if not coll_embedding:
            coll_embedding = CollectionEmbedding(
                collection_id=collection_id,
                model_id=pipeline.model_name,
                model_source=model_source,
                embedding_dimensions=embedding_dimensions,
                chroma_collection_name=collection_name,
                status='processing',
                progress=0,
                priority=100 if 'vdr-2b' in pipeline.model_name.lower() else 50
            )
            db.session.add(coll_embedding)
        else:
            coll_embedding.status = 'processing'
            coll_embedding.progress = 0
            coll_embedding.error_message = None
            coll_embedding.model_source = model_source
            coll_embedding.embedding_dimensions = embedding_dimensions

        db.session.commit()
        logger.info(f"[CollectionEmbedding] Using model {pipeline.model_name} ({model_source}, {embedding_dimensions} dims)")

        # Store chroma_collection_name in database so chat service can find it
        if not collection.chroma_collection_name:
            collection.chroma_collection_name = collection_name
            db.session.commit()
            logger.info(f"[CollectionEmbedding] Set chroma_collection_name: {collection_name}")

        live_meta = getattr(self, '_live_mode', {}).get(collection_id, {'wait_for_more': False, 'source_job_id': None})
        wait_for_more = live_meta.get('wait_for_more', False)
        source_job_id = live_meta.get('source_job_id')

        # Initialize vectorstore directory
        vectorstore_dir = os.path.join(pipeline.storage_dir, "vectorstore", pipeline.model_name.replace('/', '_'))
        os.makedirs(vectorstore_dir, exist_ok=True)

        processed_count = 0
        total_chunks_total = 0

        def crawl_still_running() -> bool:
            if not source_job_id:
                return False
            try:
                from services.crawler.web_crawler import crawler_service
                job = crawler_service.get_job_status(source_job_id)
                return job and job.get('status') in ('queued', 'running')
            except Exception as e:
                logger.debug(f"[CollectionEmbedding] Could not read crawler job {source_job_id}: {e}")
                return False

        while True:
            if stop_event and stop_event.is_set():
                logger.info(f"[CollectionEmbedding] Embedding paused for collection {collection_id}")
                return

            # Get all documents linked to this collection
            doc_links = CollectionDocumentLink.query.filter_by(
                collection_id=collection_id
            ).all()

            documents = [link.document for link in doc_links if link.document and link.document.status in ('pending', 'failed')]
            total_docs = processed_count + len(documents)

            if not documents:
                if wait_for_more and crawl_still_running():
                    time.sleep(1)
                    continue

                # No documents and crawl finished -> finalize
                all_docs = [link.document for link in doc_links if link.document]
                indexed = sum(1 for d in all_docs if d and d.status == 'indexed')

                # Recompute stats from DB (don't rely on incremental counters which can miss reused chunks)
                linked_doc_ids = db.session.query(CollectionDocumentLink.document_id).filter(
                    CollectionDocumentLink.collection_id == collection_id
                ).subquery()
                total_chunks_db = RAGDocumentChunk.query.filter(
                    RAGDocumentChunk.document_id.in_(linked_doc_ids)
                ).count()
                collection.document_count = len(all_docs)
                collection.total_chunks = total_chunks_db
                db.session.commit()

                # Self-heal: if Chroma collection is empty but DB has chunks, backfill all chunks into Chroma.
                # This can happen when a document was deduplicated and linked from another collection.
                if total_chunks_db > 0:
                    try:
                        vectorstore = Chroma(
                            collection_name=collection_name,
                            persist_directory=vectorstore_dir,
                            embedding_function=pipeline.embeddings,
                            collection_metadata=CHROMA_COLLECTION_METADATA,
                        )
                        if vectorstore._collection.count() == 0:
                            logger.warning(
                                f"[CollectionEmbedding] Chroma collection '{collection_name}' is empty but DB has {total_chunks_db} chunks; backfilling"
                            )

                            # Load chunks via joins to avoid reading files again
                            chunks_to_backfill = (
                                db.session.query(RAGDocumentChunk)
                                .join(RAGDocument, RAGDocument.id == RAGDocumentChunk.document_id)
                                .join(CollectionDocumentLink, CollectionDocumentLink.document_id == RAGDocument.id)
                                .filter(CollectionDocumentLink.collection_id == collection_id)
                                .order_by(RAGDocumentChunk.document_id.asc(), RAGDocumentChunk.chunk_index.asc())
                                .all()
                            )

                            # Filter out chunks without vector_id (e.g., image chunks that weren't embedded)
                            chunks_with_ids = [c for c in chunks_to_backfill if c.vector_id]
                            skipped = len(chunks_to_backfill) - len(chunks_with_ids)
                            if skipped > 0:
                                logger.warning(
                                    f"[CollectionEmbedding] Skipping {skipped} chunks without vector_id during backfill"
                                )

                            # Batch upserts to keep memory bounded
                            batch_size = 256
                            for start in range(0, len(chunks_with_ids), batch_size):
                                batch = chunks_with_ids[start : start + batch_size]
                                texts = [c.content for c in batch]
                                ids = [c.vector_id for c in batch]
                                metadatas = []
                                for c in batch:
                                    # Fetch filename from document relationship via join (safe in same session)
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

                                # Chroma.add_texts uses upsert, so repeated IDs are safe
                                vectorstore.add_texts(texts=texts, ids=ids, metadatas=metadatas)

                            logger.info(f"[CollectionEmbedding] Backfilled {len(chunks_with_ids)} chunks into ChromaDB collection {collection_name}")

                    except Exception as e:
                        logger.error(f"[CollectionEmbedding] Failed to backfill Chroma collection {collection_name}: {e}")

                self._complete_collection(collection_id, total_chunks_db, indexed)
                return

            batch_chunks = 0

            for doc in documents:
                if stop_event and stop_event.is_set():
                    logger.info(f"[CollectionEmbedding] Embedding paused for collection {collection_id}")
                    return

                try:
                    # Update document status with deadlock retry
                    self._update_document_status(doc.id, 'processing')

                    # Emit progress
                    progress = int((processed_count / max(total_docs, 1)) * 100)
                    self._emit_progress(collection_id, progress, doc.filename, processed_count, total_docs)

                    # Load document content
                    from services.rag.lumber_chunker import chunk_file

                    chunks = chunk_file(
                        doc.file_path,
                        doc.mime_type,
                        chunk_size=collection.chunk_size or 1000,
                        chunk_overlap=collection.chunk_overlap or 200,
                    )
                    if not chunks:
                        self._update_document_status(doc.id, 'failed', 'Could not extract any document content')
                        processed_count += 1
                        continue

                    logger.info(f"[CollectionEmbedding] Document {doc.id} split into {len(chunks)} chunks")

                    # Create chunks + upsert into Chroma (reuse existing chunks by index for retries/dedup)
                    chroma_texts = []
                    chroma_ids = []
                    chroma_metadatas = []
                    all_vector_ids = []

                    existing_chunks = (
                        RAGDocumentChunk.query
                        .filter_by(document_id=doc.id)
                        .filter(RAGDocumentChunk.has_image.is_(False))
                        .all()
                    )
                    existing_by_index = {c.chunk_index: c for c in existing_chunks}

                    for i, chunk in enumerate(chunks):
                        chunk_text = chunk.text
                        content_hash = self._hash_content(chunk_text)
                        existing_chunk = existing_by_index.get(i)

                        if existing_chunk:
                            # Reuse existing DB chunk, but still upsert into THIS collection's Chroma index.
                            existing_chunk.content = chunk_text
                            existing_chunk.content_hash = content_hash
                            if not existing_chunk.vector_id:
                                existing_chunk.vector_id = f"doc_{doc.id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                            existing_chunk.page_number = chunk.page_number
                            existing_chunk.start_char = chunk.start_char
                            existing_chunk.end_char = chunk.end_char
                            existing_chunk.embedding_model = pipeline.model_name
                            existing_chunk.embedding_dimensions = getattr(pipeline, "embedding_dimensions", None)
                            existing_chunk.embedding_status = 'completed'
                            existing_chunk.embedding_error = None

                            chunk_id = existing_chunk.vector_id
                            all_vector_ids.append(chunk_id)
                            chroma_texts.append(chunk_text)
                            chroma_ids.append(chunk_id)
                            chroma_metadatas.append(sanitize_chroma_metadata({
                                'document_id': doc.id,
                                'chunk_index': i,
                                'filename': doc.filename,
                                'collection_id': collection_id,
                                'page_number': chunk.page_number,
                                'start_char': chunk.start_char,
                                'end_char': chunk.end_char,
                                'vector_id': chunk_id
                            }))
                            continue

                        # Create new chunk with unique ID
                        chunk_id = f"doc_{doc.id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                        db_chunk = RAGDocumentChunk(
                            document_id=doc.id,
                            chunk_index=i,
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
                        chroma_texts.append(chunk_text)
                        chroma_ids.append(chunk_id)
                        chroma_metadatas.append(sanitize_chroma_metadata({
                            'document_id': doc.id,
                            'chunk_index': i,
                            'filename': doc.filename,
                            'collection_id': collection_id,
                            'page_number': chunk.page_number,
                            'start_char': chunk.start_char,
                            'end_char': chunk.end_char,
                            'vector_id': chunk_id
                        }))
                        all_vector_ids.append(chunk_id)

                    db.session.commit()

                    # Upsert all chunks into ChromaDB for this collection (idempotent)
                    try:
                        vectorstore = Chroma(
                            collection_name=collection_name,
                            persist_directory=vectorstore_dir,
                            embedding_function=pipeline.embeddings,
                            collection_metadata=CHROMA_COLLECTION_METADATA,
                        )

                        if chroma_texts:
                            # Avoid duplicates within the same batch (shouldn't happen, but protects against malformed data)
                            seen = set()
                            texts_unique = []
                            ids_unique = []
                            metadatas_unique = []
                            for text, vid, meta in zip(chroma_texts, chroma_ids, chroma_metadatas):
                                if not vid or vid in seen:
                                    continue
                                seen.add(vid)
                                texts_unique.append(text)
                                ids_unique.append(vid)
                                metadatas_unique.append(meta)

                            vectorstore.add_texts(
                                texts=texts_unique,
                                ids=ids_unique,
                                metadatas=metadatas_unique
                            )
                            logger.info(f"[CollectionEmbedding] Upserted {len(ids_unique)} chunks into ChromaDB collection {collection_name}")

                    except Exception as e:
                        logger.error(f"[CollectionEmbedding] ChromaDB error: {e}")
                        raise

                    # Embed image chunks (screenshots / inline images) if supported by the embedding model
                    self._embed_image_chunks_for_document(
                        doc=doc,
                        collection_id=collection_id,
                        collection_name=collection_name,
                        vectorstore_dir=vectorstore_dir,
                        model_id=pipeline.model_name
                    )

                    # Update document status with deadlock retry
                    self._update_document_status(
                        doc.id, 'indexed',
                        chunk_count=len(chunks),
                        vector_ids=all_vector_ids,
                        embedding_model=pipeline.model_name
                    )

                    # Emit per-document status update (no polling needed in UIs)
                    try:
                        from main import socketio
                        from socketio_handlers.events_rag import emit_document_processed
                        emit_document_processed(socketio, doc.id, 'indexed', None, collection_id=collection_id)
                    except Exception:
                        pass

                    batch_chunks += len(chunks)
                    total_chunks_total += len(chunks)
                    processed_count += 1

                    # Emit progress after each document
                    progress = int((processed_count / max(total_docs, 1)) * 100)
                    self._emit_progress(collection_id, progress, doc.filename, processed_count, total_docs)

                except Exception as e:
                    logger.error(f"[CollectionEmbedding] Error processing document {doc.id}: {e}")
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    # Update document status with deadlock retry
                    try:
                        self._update_document_status(doc.id, 'failed', str(e)[:500])
                    except Exception as update_err:
                        logger.warning(f"[CollectionEmbedding] Failed to update document {doc.id} status: {update_err}")
                    try:
                        from main import socketio
                        from socketio_handlers.events_rag import emit_document_processed
                        emit_document_processed(socketio, doc.id, 'failed', str(e), collection_id=collection_id)
                    except Exception:
                        pass
                    processed_count += 1

            # Update collection stats after each batch with deadlock retry
            try:
                self._update_collection_stats(
                    collection_id,
                    int((processed_count / max(total_docs, 1)) * 100),
                    len([link for link in doc_links if link.document])
                )
            except Exception as stats_err:
                logger.warning(f"[CollectionEmbedding] Failed to update collection stats: {stats_err}")

    def _embed_image_chunks_for_document(
        self,
        doc,
        collection_id: int,
        collection_name: str,
        vectorstore_dir: str,
        model_id: str
    ) -> int:
        """Embed image chunks for a document when using a multimodal embedding model."""
        from db.db import db
        from db.tables import RAGDocumentChunk
        from langchain_chroma import Chroma
        from services.rag.image_embedding_service import ImageEmbeddingService

        if not ImageEmbeddingService.supports_model(model_id):
            return 0

        image_chunks = (
            RAGDocumentChunk.query
            .filter_by(document_id=doc.id, has_image=True)
            .all()
        )
        if not image_chunks:
            return 0

        to_embed = []
        for chunk in image_chunks:
            if not chunk.image_path:
                continue
            if chunk.vector_id and chunk.embedding_status == 'completed' and chunk.embedding_model == model_id:
                continue
            to_embed.append(chunk)

        if not to_embed:
            return 0

        embeddings = ImageEmbeddingService.embed_image_paths(
            model_id,
            [c.image_path for c in to_embed]
        )

        vectorstore = Chroma(
            collection_name=collection_name,
            persist_directory=vectorstore_dir,
            collection_metadata=CHROMA_COLLECTION_METADATA,
        )

        ids = []
        documents = []
        metadatas = []
        vectors = []

        for chunk, embedding in zip(to_embed, embeddings):
            if not embedding:
                chunk.embedding_status = 'failed'
                chunk.embedding_error = 'Image embedding failed or unavailable'
                continue

            if not chunk.vector_id:
                chunk.vector_id = f"doc_{doc.id}_img_{chunk.chunk_index}_{uuid.uuid4().hex[:8]}"

            chunk.embedding_model = model_id
            chunk.embedding_dimensions = len(embedding)
            chunk.embedding_status = 'completed'
            chunk.embedding_error = None

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

        if ids:
            try:
                vectorstore._collection.upsert(
                    ids=ids,
                    embeddings=vectors,
                    metadatas=metadatas,
                    documents=documents
                )
                logger.info(f"[CollectionEmbedding] Embedded {len(ids)} image chunks for doc {doc.id}")
            except Exception as exc:
                logger.warning(f"[CollectionEmbedding] Image upsert failed for doc {doc.id}: {exc}")

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        return len(ids)

    @retry_on_deadlock(max_retries=3, delay=0.5)
    def _update_document_status(self, doc_id: int, status: str, error: str = None, **kwargs):
        """
        Update document status with deadlock retry.

        Args:
            doc_id: Document ID
            status: New status ('processing', 'indexed', 'failed')
            error: Error message for failed status
            **kwargs: Additional fields to update (chunk_count, vector_ids, embedding_model)
        """
        from db.db import db
        from db.tables import RAGDocument

        doc = RAGDocument.query.get(doc_id)
        if not doc:
            logger.warning(f"[CollectionEmbedding] Document {doc_id} not found for status update")
            return

        doc.status = status
        doc.updated_at = datetime.now()

        if status == 'indexed':
            doc.processed_at = datetime.now()
            doc.indexed_at = datetime.now()
        elif status == 'failed' and error:
            doc.processing_error = error

        # Apply additional fields
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)

        db.session.commit()

    @retry_on_deadlock(max_retries=3, delay=0.5)
    def _update_collection_stats(self, collection_id: int, progress: int, doc_count: int):
        """
        Update collection stats with deadlock retry.

        Args:
            collection_id: Collection ID
            progress: Current embedding progress (0-100)
            doc_count: Number of documents in collection
        """
        from db.db import db
        from db.tables import RAGCollection, RAGDocumentChunk, CollectionDocumentLink

        collection = RAGCollection.query.get(collection_id)
        if not collection:
            return

        # Recompute total chunks for the collection to avoid drift
        linked_doc_ids = db.session.query(CollectionDocumentLink.document_id).filter(
            CollectionDocumentLink.collection_id == collection_id
        ).subquery()
        collection.total_chunks = RAGDocumentChunk.query.filter(
            RAGDocumentChunk.document_id.in_(linked_doc_ids)
        ).count()
        collection.document_count = doc_count
        collection.embedding_progress = progress
        collection.last_indexed_at = datetime.now()
        db.session.commit()

    def _load_document_content(self, doc) -> str:
        """Load content from document file."""
        import os

        if not os.path.exists(doc.file_path):
            logger.warning(f"[CollectionEmbedding] File not found: {doc.file_path}")
            return ""

        try:
            with open(doc.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"[CollectionEmbedding] Error reading file {doc.file_path}: {e}")
            return ""

    def _hash_content(self, content: str) -> str:
        """Generate SHA-256 hash for content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _emit_progress(self, collection_id: int, progress: int, current_doc: str,
                       docs_processed: int, docs_total: int):
        """Emit progress via WebSocket and update wizard session if applicable."""
        try:
            from main import socketio
            from socketio_handlers.events_rag import emit_collection_progress

            emit_collection_progress(
                socketio, collection_id, progress,
                current_doc, docs_processed, docs_total
            )

            # Also update DB
            from db.db import db
            from db.tables import RAGCollection, Chatbot
            collection = RAGCollection.query.get(collection_id)
            if collection:
                collection.embedding_progress = progress
                db.session.commit()

            # Update wizard session if this is a chatbot embedding
            chatbot = Chatbot.query.filter_by(primary_collection_id=collection_id).first()
            if chatbot and chatbot.build_status == 'embedding':
                try:
                    from services.wizard import get_wizard_session_service
                    from socketio_handlers.events_wizard import emit_wizard_progress
                    wizard_service = get_wizard_session_service()
                    wizard_service.update_embedding_progress(chatbot.id, {
                        'embedding_progress': progress,
                        'documents_processed': docs_processed,
                        'documents_total': docs_total,
                        'current_document': current_doc,
                    })
                    emit_wizard_progress(socketio, chatbot.id,
                        wizard_service.get_progress(chatbot.id))
                except Exception as we:
                    logger.debug(f"[CollectionEmbedding] Could not update wizard session: {we}")

        except Exception as e:
            logger.debug(f"[CollectionEmbedding] Could not emit progress: {e}")

    def _complete_collection(self, collection_id: int, total_chunks: int, docs_processed: int):
        """Mark collection as completed."""
        try:
            from db.db import db
            from db.tables import RAGCollection
            from db.models.rag import CollectionEmbedding

            collection = RAGCollection.query.get(collection_id)
            if collection:
                collection.embedding_status = 'completed'
                collection.embedding_progress = 100
                collection.total_chunks = total_chunks
                collection.last_indexed_at = datetime.now()

                # Also update CollectionEmbedding record
                coll_embeddings = CollectionEmbedding.query.filter_by(
                    collection_id=collection_id,
                    status='processing'
                ).all()
                for ce in coll_embeddings:
                    ce.status = 'completed'
                    ce.progress = 100
                    ce.chunk_count = total_chunks
                    ce.completed_at = datetime.now()

                db.session.commit()

            # Emit completion event
            from main import socketio
            from socketio_handlers.events_rag import emit_collection_completed
            emit_collection_completed(socketio, collection_id, total_chunks, docs_processed)

            logger.info(f"[CollectionEmbedding] Collection {collection_id} completed: {total_chunks} chunks, {docs_processed} docs")

            # Cleanup live mode tracking
            if hasattr(self, '_live_mode'):
                self._live_mode.pop(collection_id, None)

        except Exception as e:
            logger.error(f"[CollectionEmbedding] Error completing collection: {e}")

    def _set_collection_error(self, collection_id: int, error: str):
        """Set error status on collection."""
        try:
            from db.db import db
            from db.tables import RAGCollection
            from db.models.rag import CollectionEmbedding

            collection = RAGCollection.query.get(collection_id)
            if collection:
                collection.embedding_status = 'failed'
                collection.embedding_error = error[:1000]

                # Also update CollectionEmbedding record
                coll_embeddings = CollectionEmbedding.query.filter_by(
                    collection_id=collection_id,
                    status='processing'
                ).all()
                for ce in coll_embeddings:
                    ce.status = 'failed'
                    ce.error_message = error[:1000]

                db.session.commit()

            # Emit error event
            from main import socketio
            from socketio_handlers.events_rag import emit_collection_error
            emit_collection_error(socketio, collection_id, error)

        except Exception as e:
            logger.error(f"[CollectionEmbedding] Error setting collection error: {e}")
        finally:
            if hasattr(self, '_live_mode'):
                self._live_mode.pop(collection_id, None)


# Global service instance
_embedding_service: Optional[CollectionEmbeddingService] = None


def get_collection_embedding_service() -> CollectionEmbeddingService:
    """Get the global collection embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        from flask import current_app
        _embedding_service = CollectionEmbeddingService(current_app._get_current_object())
    return _embedding_service
