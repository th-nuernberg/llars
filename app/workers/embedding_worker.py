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
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_community.document_loaders import TextLoader
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

        # Load document content
        content = self._load_document_content(doc)
        if not content:
            raise ValueError(f"Could not load content from {doc.file_path}")

        # Update progress
        if queue_entry:
            queue_entry.current_step = 'Splitting into chunks'
            queue_entry.progress_percent = 30
            db.session.commit()
        self._emit_progress(doc, 'processing', progress=30, step='Splitting into chunks')

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["# ", "## ", "\n\n", "\n", ". ", "! ", "? "]
        )
        chunks = text_splitter.split_text(content)
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
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name
        primary_collection = linked_collections[0]
        collection_name = sanitize_chroma_collection_name(primary_collection.name, self._pipeline.model_name)

        # Get or create Chroma collection
        vectorstore_dir = os.path.join(self._pipeline.storage_dir, "vectorstore", self._pipeline.model_name.replace('/', '_'))
        os.makedirs(vectorstore_dir, exist_ok=True)

        # Create embeddings and store in ChromaDB
        vector_ids = []
        for i, chunk_text in enumerate(chunks):
            try:
                # Generate unique ID for this chunk
                chunk_id = f"doc_{doc.id}_chunk_{i}_{uuid.uuid4().hex[:8]}"

                # Create embedding
                embedding = self._pipeline.embeddings.embed_query(chunk_text)

                # Store in database chunk table
                db_chunk = RAGDocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk_text,
                    content_hash=self._hash_content(chunk_text),
                    start_char=0,  # Would need proper tracking for accurate values
                    end_char=len(chunk_text),
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
                texts=chunks,
                ids=vector_ids,
                metadatas=[{
                    'document_id': doc.id,
                    'chunk_index': i,
                    'filename': doc.filename,
                    'collection_id': primary_collection.id,  # Primary collection
                    'collection_ids': ','.join(map(str, collection_ids))  # All linked collections
                } for i in range(len(chunks))]
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

            data = {
                'document_id': doc.id,
                'filename': doc.filename,
                'status': status,
                'progress': progress,
                'step': step
            }
            if error:
                data['error'] = error

            socketio.emit('rag:document_progress', data, namespace='/')

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
