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
from datetime import datetime
from typing import Optional, Dict, Any, List

from flask import current_app

logger = logging.getLogger(__name__)


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

    def start_embedding(self, collection_id: int) -> Dict[str, Any]:
        """
        Start embedding process for a collection.

        Args:
            collection_id: ID of the collection to embed

        Returns:
            Dict with status and message
        """
        from db.db import db
        from db.tables import RAGCollection

        collection = RAGCollection.query.get(collection_id)
        if not collection:
            return {'success': False, 'error': 'Collection not found'}

        if collection.embedding_status == 'processing':
            return {'success': False, 'error': 'Collection is already being processed'}

        # Update collection status
        collection.embedding_status = 'processing'
        collection.embedding_progress = 0
        collection.embedding_error = None
        db.session.commit()

        # Create stop event for this collection
        self._stop_events[collection_id] = threading.Event()

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
        from rag_pipeline import RAGPipeline
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        import os

        stop_event = self._stop_events.get(collection_id)
        collection = RAGCollection.query.get(collection_id)

        if not collection:
            raise ValueError(f"Collection {collection_id} not found")

        logger.info(f"[CollectionEmbedding] Processing collection {collection.id}: {collection.name}")

        # Initialize RAG pipeline early to set chroma_collection_name
        pipeline = RAGPipeline()
        collection_name = sanitize_chroma_collection_name(collection.name, pipeline.model_name)

        # Store chroma_collection_name in database so chat service can find it
        if not collection.chroma_collection_name:
            collection.chroma_collection_name = collection_name
            db.session.commit()
            logger.info(f"[CollectionEmbedding] Set chroma_collection_name: {collection_name}")

        # Get all documents linked to this collection
        doc_links = CollectionDocumentLink.query.filter_by(
            collection_id=collection_id
        ).all()

        documents = [link.document for link in doc_links if link.document and link.document.status in ('pending', 'failed')]
        total_docs = len(documents)

        if total_docs == 0:
            # Check if all docs are already indexed
            all_docs = [link.document for link in doc_links if link.document]
            indexed = sum(1 for d in all_docs if d.status == 'indexed')
            if indexed == len(all_docs):
                self._complete_collection(collection_id, collection.total_chunks, len(all_docs))
                return

            logger.info(f"[CollectionEmbedding] No pending documents for collection {collection_id}")
            self._complete_collection(collection_id, collection.total_chunks, 0)
            return

        # Initialize vectorstore directory
        vectorstore_dir = os.path.join(pipeline.storage_dir, "vectorstore", pipeline.model_name.replace('/', '_'))
        os.makedirs(vectorstore_dir, exist_ok=True)

        # Text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=collection.chunk_size or 1000,
            chunk_overlap=collection.chunk_overlap or 200,
            separators=["# ", "## ", "\n\n", "\n", ". ", "! ", "? "]
        )

        processed_count = 0
        total_chunks = 0

        for doc in documents:
            if stop_event and stop_event.is_set():
                logger.info(f"[CollectionEmbedding] Embedding paused for collection {collection_id}")
                return

            try:
                # Update document status
                doc.status = 'processing'
                db.session.commit()

                # Emit progress
                progress = int((processed_count / total_docs) * 100)
                self._emit_progress(collection_id, progress, doc.filename, processed_count, total_docs)

                # Load document content
                content = self._load_document_content(doc)
                if not content:
                    doc.status = 'failed'
                    doc.processing_error = 'Could not load document content'
                    db.session.commit()
                    processed_count += 1
                    continue

                # Split into chunks
                chunks = text_splitter.split_text(content)
                logger.info(f"[CollectionEmbedding] Document {doc.id} split into {len(chunks)} chunks")

                # Create chunks and embeddings - track new chunks separately
                new_chunks = []
                new_vector_ids = []
                all_vector_ids = []

                for i, chunk_text in enumerate(chunks):
                    # Check for existing chunk with same hash
                    content_hash = self._hash_content(chunk_text)
                    existing_chunk = RAGDocumentChunk.query.filter_by(
                        document_id=doc.id,
                        content_hash=content_hash
                    ).first()

                    if existing_chunk:
                        # Reuse existing chunk - don't add to ChromaDB again
                        all_vector_ids.append(existing_chunk.vector_id)
                        continue

                    # Create new chunk with unique ID
                    chunk_id = f"doc_{doc.id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                    db_chunk = RAGDocumentChunk(
                        document_id=doc.id,
                        chunk_index=i,
                        content=chunk_text,
                        content_hash=content_hash,
                        vector_id=chunk_id,
                        embedding_model=pipeline.model_name,
                        embedding_status='completed'
                    )
                    db.session.add(db_chunk)
                    new_chunks.append(chunk_text)
                    new_vector_ids.append(chunk_id)
                    all_vector_ids.append(chunk_id)

                db.session.commit()

                # Only add NEW chunks to ChromaDB (skip already embedded ones)
                if new_chunks:
                    try:
                        vectorstore = Chroma(
                            collection_name=collection_name,
                            persist_directory=vectorstore_dir,
                            embedding_function=pipeline.embeddings
                        )

                        vectorstore.add_texts(
                            texts=new_chunks,
                            ids=new_vector_ids,
                            metadatas=[{
                                'document_id': doc.id,
                                'chunk_index': i,
                                'filename': doc.filename,
                                'collection_id': collection_id
                            } for i in range(len(new_chunks))]
                        )
                        logger.info(f"[CollectionEmbedding] Added {len(new_chunks)} new chunks to ChromaDB (skipped {len(chunks) - len(new_chunks)} existing)")

                    except Exception as e:
                        logger.error(f"[CollectionEmbedding] ChromaDB error: {e}")
                        raise
                else:
                    logger.info(f"[CollectionEmbedding] All {len(chunks)} chunks already exist, skipping ChromaDB insert")

                # Update document status
                doc.status = 'indexed'
                doc.processed_at = datetime.now()
                doc.indexed_at = datetime.now()
                doc.chunk_count = len(chunks)
                doc.vector_ids = all_vector_ids
                doc.embedding_model = pipeline.model_name
                db.session.commit()

                total_chunks += len(new_chunks)
                processed_count += 1

                # Emit progress after each document
                progress = int((processed_count / total_docs) * 100)
                self._emit_progress(collection_id, progress, doc.filename, processed_count, total_docs)

            except Exception as e:
                logger.error(f"[CollectionEmbedding] Error processing document {doc.id}: {e}")
                doc.status = 'failed'
                doc.processing_error = str(e)[:500]
                db.session.commit()
                processed_count += 1

        # Update collection stats
        self._complete_collection(collection_id, total_chunks, processed_count)

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
        """Emit progress via WebSocket."""
        try:
            from main import socketio
            from socketio_handlers.events_rag import emit_collection_progress

            emit_collection_progress(
                socketio, collection_id, progress,
                current_doc, docs_processed, docs_total
            )

            # Also update DB
            from db.db import db
            from db.tables import RAGCollection
            collection = RAGCollection.query.get(collection_id)
            if collection:
                collection.embedding_progress = progress
                db.session.commit()

        except Exception as e:
            logger.debug(f"[CollectionEmbedding] Could not emit progress: {e}")

    def _complete_collection(self, collection_id: int, total_chunks: int, docs_processed: int):
        """Mark collection as completed."""
        try:
            from db.db import db
            from db.tables import RAGCollection

            collection = RAGCollection.query.get(collection_id)
            if collection:
                collection.embedding_status = 'completed'
                collection.embedding_progress = 100
                collection.total_chunks = total_chunks
                collection.last_indexed_at = datetime.now()
                db.session.commit()

            # Emit completion event
            from main import socketio
            from socketio_handlers.events_rag import emit_collection_completed
            emit_collection_completed(socketio, collection_id, total_chunks, docs_processed)

            logger.info(f"[CollectionEmbedding] Collection {collection_id} completed: {total_chunks} chunks, {docs_processed} docs")

        except Exception as e:
            logger.error(f"[CollectionEmbedding] Error completing collection: {e}")

    def _set_collection_error(self, collection_id: int, error: str):
        """Set error status on collection."""
        try:
            from db.db import db
            from db.tables import RAGCollection

            collection = RAGCollection.query.get(collection_id)
            if collection:
                collection.embedding_status = 'failed'
                collection.embedding_error = error[:1000]
                db.session.commit()

            # Emit error event
            from main import socketio
            from socketio_handlers.events_rag import emit_collection_error
            emit_collection_error(socketio, collection_id, error)

        except Exception as e:
            logger.error(f"[CollectionEmbedding] Error setting collection error: {e}")


# Global service instance
_embedding_service: Optional[CollectionEmbeddingService] = None


def get_collection_embedding_service() -> CollectionEmbeddingService:
    """Get the global collection embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        from flask import current_app
        _embedding_service = CollectionEmbeddingService(current_app._get_current_object())
    return _embedding_service
