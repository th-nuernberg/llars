"""
Background Worker for RAG Document Embedding Processing.

This worker processes the embedding queue in the background,
creating vector embeddings for documents and storing them in ChromaDB.

Features:
- Thread-based background processing
- Live Socket.IO broadcasts for progress updates
- Automatic startup on application init
- Error handling and retry logic
- Batch processing for efficiency
"""

import logging
import threading
import time
import uuid
from datetime import datetime
from datetime import timedelta
import os
from typing import Optional

from flask import current_app

# Configure logger to output to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global worker instance
_worker: Optional['EmbeddingWorker'] = None
_worker_lock = threading.Lock()


class EmbeddingWorker:
    """
    Background worker for processing document embeddings.

    Runs in a separate thread and continuously processes documents
    with status='pending' from the RAGDocument table.
    """

    # Configuration
    POLL_INTERVAL = 5  # Seconds between queue checks when idle
    BATCH_SIZE = 5     # Number of documents to process in one batch
    MAX_RETRIES = 3    # Maximum retry attempts per document

    def __init__(self, app):
        """
        Initialize the worker.

        Args:
            app: Flask application instance (for context)
        """
        self.app = app
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._processing_count = 0
        self._pipeline = None

    def start(self):
        """Start the worker in a background thread."""
        if self.running:
            logger.warning("[EmbeddingWorker] Already running")
            return

        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(
            target=self._run,
            name="EmbeddingWorker",
            daemon=True
        )
        self.thread.start()
        logger.info("[EmbeddingWorker] Started")

    def stop(self):
        """Stop the worker gracefully."""
        logger.info("[EmbeddingWorker] Stopping...")
        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10.0)

        logger.info("[EmbeddingWorker] Stopped")

    def _run(self):
        """Main worker loop."""
        with self.app.app_context():
            try:
                # Initialize pipeline once
                self._init_pipeline()

                # Main processing loop
                while self.running and not self._stop_event.is_set():
                    try:
                        processed = self._process_batch()

                        if processed == 0:
                            # No documents to process, wait before checking again
                            self._stop_event.wait(timeout=self.POLL_INTERVAL)
                        else:
                            # Processed some documents, immediately check for more
                            time.sleep(0.1)

                    except Exception as e:
                        logger.error(f"[EmbeddingWorker] Error in processing loop: {e}")
                        try:
                            from db.db import db
                            db.session.rollback()
                        except Exception:
                            pass
                        # Wait a bit before retrying
                        self._stop_event.wait(timeout=5)

            except Exception as e:
                logger.error(f"[EmbeddingWorker] Fatal error: {e}")
            finally:
                self.running = False
                logger.info("[EmbeddingWorker] Exited")

    def _init_pipeline(self):
        """Initialize the RAG pipeline for embedding generation."""
        try:
            from rag_pipeline import RAGPipeline

            # Initialize with default collection - we'll use custom collection per document
            self._pipeline = RAGPipeline()
            logger.info(f"[EmbeddingWorker] Pipeline initialized with model: {self._pipeline.model_name}")
        except Exception as e:
            logger.error(f"[EmbeddingWorker] Failed to initialize pipeline: {e}")
            raise

    def _process_batch(self) -> int:
        """
        Process a batch of pending documents.

        Returns:
            Number of documents processed
        """
        from db.db import db
        from db.tables import RAGDocument, RAGDocumentChunk, RAGCollection, RAGProcessingQueue

        # Ensure a clean session at the beginning of each batch.
        try:
            db.session.rollback()
        except Exception:
            pass

        # Requeue stale "processing" documents after restarts/crashes
        try:
            stale_seconds = int(os.environ.get("EMBEDDING_STALE_SECONDS", "900"))  # 15 min default
        except Exception:
            stale_seconds = 900

        cutoff = datetime.now() - timedelta(seconds=stale_seconds)

        stale_queue_entries = RAGProcessingQueue.query.filter(
            RAGProcessingQueue.status == 'processing',
            RAGProcessingQueue.started_at.isnot(None),
            RAGProcessingQueue.started_at < cutoff
        ).all()

        if stale_queue_entries:
            logger.warning(f"[EmbeddingWorker] Requeuing {len(stale_queue_entries)} stale processing documents")

            for entry in stale_queue_entries:
                doc = entry.document
                if not doc:
                    continue
                if entry.retry_count >= entry.max_retries:
                    entry.status = 'failed'
                    entry.error_message = 'Stuck in processing; max retries reached'
                    doc.status = 'failed'
                    doc.processing_error = entry.error_message[:500]
                else:
                    entry.retry_count += 1
                    entry.status = 'queued'
                    entry.progress_percent = 0
                    entry.current_step = 'Requeued after stale processing'
                    entry.error_message = None
                    entry.started_at = None
                    doc.status = 'pending'

            db.session.commit()

        # Also reset documents stuck in processing without queue info
        stale_docs = RAGDocument.query.filter(
            RAGDocument.status == 'processing',
            RAGDocument.updated_at.isnot(None),
            RAGDocument.updated_at < cutoff
        ).all()

        if stale_docs:
            logger.warning(f"[EmbeddingWorker] Resetting {len(stale_docs)} stale docs without active queue")
            for doc in stale_docs:
                doc.status = 'pending'
            db.session.commit()

        # Get pending documents
        pending_docs = RAGDocument.query.filter_by(
            status='pending'
        ).limit(self.BATCH_SIZE).all()

        if not pending_docs:
            return 0

        logger.info(f"[EmbeddingWorker] Processing {len(pending_docs)} documents...")
        processed_count = 0

        for doc in pending_docs:
            if self._stop_event.is_set():
                break

            try:
                self._process_document(doc, db)
                processed_count += 1
            except Exception as e:
                logger.error(f"[EmbeddingWorker] Error processing document {doc.id}: {e}")
                try:
                    db.session.rollback()
                except Exception:
                    pass
                doc.status = 'failed'
                doc.processing_error = str(e)[:500]
                db.session.commit()

                # Update queue entry if exists
                queue_entry = RAGProcessingQueue.query.filter_by(document_id=doc.id).first()
                if queue_entry:
                    queue_entry.status = 'failed'
                    queue_entry.error_message = str(e)[:500]
                    db.session.commit()

                # Emit error event
                self._emit_progress(doc, 'failed', error=str(e))

        return processed_count

    def _process_document(self, doc, db):
        """
        Process a single document: create chunks and embeddings.

        With the n:m Collection-Document linking system, a document can be in
        multiple collections. We store embeddings once and update all linked
        collections' stats.

        Args:
            doc: RAGDocument instance
            db: Database session
        """
        from db.tables import RAGDocumentChunk, RAGCollection, RAGProcessingQueue, CollectionDocumentLink
        from langchain_chroma import Chroma
        import os

        logger.info(f"[EmbeddingWorker] Processing document {doc.id}: {doc.filename}")

        # Update status to processing
        doc.status = 'processing'
        db.session.commit()

        # Update queue entry
        queue_entry = RAGProcessingQueue.query.filter_by(document_id=doc.id).first()
        if queue_entry:
            queue_entry.status = 'processing'
            queue_entry.started_at = datetime.now()
            queue_entry.current_step = 'Loading document'
            queue_entry.progress_percent = 10
            db.session.commit()

        # Emit progress
        self._emit_progress(doc, 'processing', progress=10, step='Loading document')

        # Update progress
        if queue_entry:
            queue_entry.current_step = 'Splitting into chunks'
            queue_entry.progress_percent = 30
            db.session.commit()
        self._emit_progress(doc, 'processing', progress=30, step='Splitting into chunks')

        # Split into chunks (PDF-aware, with offsets)
        from services.rag.lumber_chunker import chunk_file

        chunks = chunk_file(
            doc.file_path,
            doc.mime_type,
            chunk_size=1000,
            chunk_overlap=200,
        )
        if not chunks:
            raise ValueError(f"Could not extract any text from {doc.file_path}")

        logger.info(f"[EmbeddingWorker] Document {doc.id} split into {len(chunks)} chunks")

        # Update progress
        if queue_entry:
            queue_entry.current_step = 'Creating embeddings'
            queue_entry.progress_percent = 50
            db.session.commit()
        self._emit_progress(doc, 'processing', progress=50, step='Creating embeddings')

        # Get collections for this document via links
        # A document can be in multiple collections, use the first one for ChromaDB naming
        # (embeddings are stored once, metadata references all collections)
        linked_collections = [link.collection for link in doc.collection_links if link.collection]

        if not linked_collections:
            # Fallback to legacy collection_id field for backwards compatibility
            if doc.collection_id:
                collection = RAGCollection.query.get(doc.collection_id)
                if collection:
                    linked_collections = [collection]

        if not linked_collections:
            raise ValueError(f"Document {doc.id} has no collection assigned")

        # Use first collection for ChromaDB naming (embeddings are shared)
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name, sanitize_chroma_metadata
        primary_collection = linked_collections[0]
        collection_name = sanitize_chroma_collection_name(primary_collection.name, self._pipeline.model_name)

        # Ensure stored chroma_collection_name matches actual Chroma collection
        for coll in linked_collections:
            if coll and coll.chroma_collection_name != collection_name:
                coll.chroma_collection_name = collection_name

        # Get or create Chroma collection
        vectorstore_dir = os.path.join(self._pipeline.storage_dir, "vectorstore", self._pipeline.model_name.replace('/', '_'))
        os.makedirs(vectorstore_dir, exist_ok=True)

        # Clean up existing chunks/vectors for retries (prevents unique constraint errors and stale vectors).
        try:
            existing_chunks = RAGDocumentChunk.query.filter_by(document_id=doc.id).all()
            existing_vector_ids = [c.vector_id for c in existing_chunks if c and c.vector_id]

            if existing_chunks:
                try:
                    vectorstore = Chroma(
                        collection_name=collection_name,
                        persist_directory=vectorstore_dir,
                        embedding_function=self._pipeline.embeddings,
                    )
                    if existing_vector_ids:
                        try:
                            vectorstore._collection.delete(ids=existing_vector_ids)
                        except Exception:
                            # Fallback for different langchain-chroma versions
                            try:
                                vectorstore.delete(ids=existing_vector_ids)
                            except Exception:
                                pass
                except Exception as e:
                    logger.warning(f"[EmbeddingWorker] Could not delete old vectors for doc {doc.id}: {e}")

                RAGDocumentChunk.query.filter_by(document_id=doc.id).delete()
                doc.vector_ids = None
                doc.chunk_count = 0
                db.session.commit()
        except Exception as e:
            logger.warning(f"[EmbeddingWorker] Cleanup skipped for doc {doc.id}: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass

        # Create chunks and store in DB + ChromaDB
        vector_ids = []
        for i, chunk in enumerate(chunks):
            try:
                chunk_text = chunk.text
                # Generate unique ID for this chunk
                chunk_id = f"doc_{doc.id}_chunk_{i}_{uuid.uuid4().hex[:8]}"

                # Store in database chunk table
                db_chunk = RAGDocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk_text,
                    content_hash=self._hash_content(chunk_text),
                    page_number=chunk.page_number,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    embedding_model=self._pipeline.model_name,
                    embedding_status='completed',
                    vector_id=chunk_id
                )
                db.session.add(db_chunk)
                vector_ids.append(chunk_id)

                # Update progress
                progress = 50 + int((i + 1) / len(chunks) * 40)
                if queue_entry and i % 5 == 0:  # Update every 5 chunks
                    queue_entry.progress_percent = progress
                    queue_entry.current_step = f'Embedding chunk {i+1}/{len(chunks)}'
                    db.session.commit()

                if i % 10 == 0:  # Emit every 10 chunks
                    self._emit_progress(doc, 'processing', progress=progress,
                                       step=f'Embedding chunk {i+1}/{len(chunks)}')

            except Exception as e:
                logger.error(f"[EmbeddingWorker] Error embedding chunk {i} of doc {doc.id}: {e}")
                raise

        # Add to ChromaDB vectorstore
        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=vectorstore_dir,
                embedding_function=self._pipeline.embeddings
            )

            # Add texts with IDs - store all linked collection IDs in metadata
            collection_ids = [c.id for c in linked_collections]
            vectorstore.add_texts(
                texts=[c.text for c in chunks],
                ids=vector_ids,
                metadatas=[
                    sanitize_chroma_metadata({
                        'document_id': doc.id,
                        'chunk_index': i,
                        'filename': doc.filename,
                        'collection_id': primary_collection.id,  # Primary collection
                        'collection_ids': ','.join(map(str, collection_ids)),  # All linked collections
                        'page_number': chunks[i].page_number,
                        'start_char': chunks[i].start_char,
                        'end_char': chunks[i].end_char,
                        'vector_id': vector_ids[i]
                    })
                    for i in range(len(chunks))
                ]
            )
            logger.info(f"[EmbeddingWorker] Added {len(chunks)} chunks to ChromaDB collection {collection_name}")

        except Exception as e:
            logger.error(f"[EmbeddingWorker] Error adding to ChromaDB: {e}")
            raise

        # Update document status
        doc.status = 'indexed'
        doc.processed_at = datetime.now()
        doc.indexed_at = datetime.now()
        doc.chunk_count = len(chunks)
        doc.vector_ids = vector_ids
        doc.embedding_model = self._pipeline.model_name

        # Update stats for ALL linked collections
        for coll in linked_collections:
            # Count chunks for documents linked to this collection
            linked_doc_ids = db.session.query(CollectionDocumentLink.document_id).filter(
                CollectionDocumentLink.collection_id == coll.id
            ).subquery()
            coll.total_chunks = RAGDocumentChunk.query.filter(
                RAGDocumentChunk.document_id.in_(linked_doc_ids)
            ).count()
            logger.debug(f"[EmbeddingWorker] Updated collection {coll.id} total_chunks: {coll.total_chunks}")

        # Update queue entry
        if queue_entry:
            queue_entry.status = 'completed'
            queue_entry.progress_percent = 100
            queue_entry.current_step = 'Completed'
            queue_entry.completed_at = datetime.now()

        db.session.commit()

        # Emit completion
        self._emit_progress(doc, 'indexed', progress=100, step='Completed')
        logger.info(f"[EmbeddingWorker] Document {doc.id} indexed successfully with {len(chunks)} chunks")

    def _load_document_content(self, doc) -> str:
        """Load content from document file."""
        import os

        if not os.path.exists(doc.file_path):
            logger.warning(f"[EmbeddingWorker] File not found: {doc.file_path}")
            return ""

        try:
            with open(doc.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"[EmbeddingWorker] Error reading file {doc.file_path}: {e}")
            return ""

    def _hash_content(self, content: str) -> str:
        """Generate hash for chunk content."""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _emit_progress(self, doc, status: str, progress: int = 0, step: str = '', error: str = None):
        """Emit progress update via Socket.IO."""
        try:
            from app import socketio
            from socketio_handlers.events_rag import emit_document_progress

            emit_document_progress(
                socketio,
                document_id=doc.id,
                status=status,
                progress=progress,
                step=step,
                error=error
            )

        except Exception as e:
            logger.debug(f"[EmbeddingWorker] Could not emit progress: {e}")


# Global functions for worker management

def get_embedding_worker() -> Optional[EmbeddingWorker]:
    """Get the global embedding worker instance."""
    return _worker


def start_embedding_worker(app):
    """
    Start the global embedding worker.

    Should be called once during application startup.

    Args:
        app: Flask application instance
    """
    global _worker

    with _worker_lock:
        if _worker is not None:
            logger.warning("[EmbeddingWorker] Worker already exists")
            return

        _worker = EmbeddingWorker(app)
        _worker.start()
        logger.info("[EmbeddingWorker] Global worker started")


def stop_embedding_worker():
    """Stop the global embedding worker."""
    global _worker

    with _worker_lock:
        if _worker is None:
            return

        _worker.stop()
        _worker = None
        logger.info("[EmbeddingWorker] Global worker stopped")
