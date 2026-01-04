# collection_embedding_service.py
"""
Collection Embedding Service.

Main service class for managing the embedding process for RAG collections.
Provides real-time WebSocket progress updates and integrates with the
Chatbot Builder wizard.

Features:
    - Start/Pause embedding for collections
    - Real-time progress via WebSocket
    - Live mode for concurrent crawling + embedding
    - Automatic recovery of stuck documents
    - Multi-model embedding support

Architecture:
    This service orchestrates the embedding process by coordinating:
    - embedding_constants: Configuration and utilities
    - embedding_chroma: ChromaDB vectorstore operations
    - embedding_chunks: Document chunk processing
    - embedding_events: WebSocket progress notifications
    - embedding_database: Database status updates

Usage:
    from services.rag.embedding import get_collection_embedding_service

    service = get_collection_embedding_service()
    result = service.start_embedding(collection_id=123)

Author: LLARS Team
Date: November 2025 (refactored January 2026)
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Dict, Any, Optional

from flask import current_app

logger = logging.getLogger(__name__)


class CollectionEmbeddingService:
    """
    Service for embedding all documents in a collection with progress tracking.

    Manages background embedding threads, stop events for pause functionality,
    and live mode for concurrent crawling operations.

    Attributes:
        app: Flask application instance
        _active_jobs: Dict mapping collection_id to active Thread
        _stop_events: Dict mapping collection_id to threading.Event for pausing
        _live_mode: Dict tracking live crawl mode metadata

    Thread Safety:
        Uses threading.Event for safe pause/resume signaling between threads.
    """

    def __init__(self, app=None):
        """
        Initialize the service with Flask app context.

        Args:
            app: Flask application instance (optional, can be set later)
        """
        self.app = app
        self._active_jobs: Dict[int, threading.Thread] = {}
        self._stop_events: Dict[int, threading.Event] = {}
        self._live_mode: Dict[int, Dict[str, Any]] = {}

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def start_embedding(
        self,
        collection_id: int,
        wait_for_more: bool = False,
        source_job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start embedding process for a collection.

        Initializes the embedding process in a background thread, handling
        concurrent access and recovering from interrupted runs.

        Args:
            collection_id: ID of the collection to embed
            wait_for_more: If True, keep waiting for new documents (live crawl)
            source_job_id: Optional crawler job ID to detect when crawling finishes

        Returns:
            Dict with:
                - success (bool): Whether embedding started successfully
                - message/error (str): Status message or error description

        Example:
            >>> service = get_collection_embedding_service()
            >>> result = service.start_embedding(collection_id=42)
            >>> print(result)
            {'success': True, 'message': 'Embedding started'}
        """
        from db.database import db
        from db.tables import RAGCollection
        from .embedding_database import (
            recover_stuck_documents,
            reset_collection_for_restart,
        )

        collection = RAGCollection.query.get(collection_id)
        if not collection:
            return {'success': False, 'error': 'Collection not found'}

        # Handle "processing" status without active job (crash recovery)
        if collection.embedding_status == 'processing':
            if collection_id in self._active_jobs:
                return {'success': True, 'message': 'Collection already processing'}
            reset_collection_for_restart(collection_id)

        # Update collection status to processing
        collection.embedding_status = 'processing'
        collection.embedding_progress = 0
        collection.embedding_error = None
        db.session.commit()

        # Recover documents stuck in 'processing' from interrupted runs
        recover_stuck_documents(collection_id)

        # Create stop event and track live mode
        self._stop_events[collection_id] = threading.Event()
        if wait_for_more or source_job_id:
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
        """
        Pause embedding process for a collection.

        Sets the stop event to signal the background thread to pause.
        The thread will finish the current document before stopping.

        Args:
            collection_id: Collection ID to pause

        Returns:
            Dict with success status and message

        Example:
            >>> service.pause_embedding(collection_id=42)
            {'success': True, 'message': 'Embedding paused'}
        """
        from db.database import db
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
        """
        Get embedding status for a collection.

        Args:
            collection_id: Collection ID to query

        Returns:
            Dict containing:
                - success (bool): Whether query succeeded
                - collection_id (int): Collection ID
                - name (str): Collection name
                - status (str): Current embedding status
                - progress (int): Progress percentage (0-100)
                - error (str): Error message if failed
                - documents_total (int): Total documents in collection
                - documents_indexed (int): Number of indexed documents
                - total_chunks (int): Total chunks created
                - is_active (bool): Whether a job is currently running

        Example:
            >>> status = service.get_status(collection_id=42)
            >>> print(f"Progress: {status['progress']}%")
        """
        from db.database import db
        from db.tables import RAGCollection, RAGDocument, CollectionDocumentLink

        collection = RAGCollection.query.get(collection_id)
        if not collection:
            return {'success': False, 'error': 'Collection not found'}

        # Count documents via links
        total_docs = CollectionDocumentLink.query.filter_by(
            collection_id=collection_id
        ).count()

        # Count indexed documents
        indexed_docs = (
            db.session.query(RAGDocument)
            .join(CollectionDocumentLink, RAGDocument.id == CollectionDocumentLink.document_id)
            .filter(
                CollectionDocumentLink.collection_id == collection_id,
                RAGDocument.status == 'indexed'
            )
            .count()
        )

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

    # =========================================================================
    # BACKGROUND PROCESSING
    # =========================================================================

    def _process_collection(self, app, collection_id: int) -> None:
        """
        Background process for embedding a collection.

        Entry point for the background thread. Handles app context,
        error handling, and cleanup.

        Args:
            app: Flask app for context
            collection_id: Collection ID to process
        """
        with app.app_context():
            try:
                self._do_embedding(collection_id)
            except Exception as e:
                logger.error(f"[CollectionEmbedding] Error processing collection {collection_id}: {e}")
                self._handle_error(collection_id, str(e))
            finally:
                self._cleanup(collection_id)

    def _do_embedding(self, collection_id: int) -> None:
        """
        Execute the actual embedding process.

        Main embedding loop that processes all pending documents,
        handles live mode, and coordinates all submodules.

        Args:
            collection_id: Collection ID to process

        Raises:
            ValueError: If collection not found
        """
        from db.database import db
        from db.tables import RAGCollection, RAGDocumentChunk, CollectionDocumentLink
        from rag_pipeline import RAGPipeline
        from services.rag.embedding_model_service import get_embedding_model_service

        from .embedding_constants import sanitize_chroma_collection_name
        from .embedding_chroma import (
            get_or_create_vectorstore,
            upsert_chunks_to_chroma,
            backfill_empty_collection,
        )
        from .embedding_chunks import (
            process_document_chunks,
            embed_image_chunks_for_document,
        )
        from .embedding_events import (
            emit_embedding_progress,
            emit_embedding_completed,
            emit_document_processed,
        )
        from .embedding_database import (
            update_document_status,
            update_collection_stats,
            finalize_collection_stats,
            create_or_update_collection_embedding,
            set_collection_chroma_name,
            get_pending_documents,
        )

        stop_event = self._stop_events.get(collection_id)
        collection = RAGCollection.query.get(collection_id)

        if not collection:
            raise ValueError(f"Collection {collection_id} not found")

        logger.info(f"[CollectionEmbedding] Processing collection {collection.id}: {collection.name}")

        # Initialize RAG pipeline and model info
        pipeline = RAGPipeline()
        collection_name = sanitize_chroma_collection_name(collection.name, pipeline.model_name)

        model_service = get_embedding_model_service()
        model_info = model_service.check_model_availability(pipeline.model_name)
        model_source = model_info.source.value if model_info.source else 'local'
        embedding_dimensions = model_info.dimensions or pipeline.embedding_dimensions

        # Create or update CollectionEmbedding tracking record
        create_or_update_collection_embedding(
            collection_id=collection_id,
            model_name=pipeline.model_name,
            model_source=model_source,
            embedding_dimensions=embedding_dimensions,
            chroma_collection_name=collection_name
        )

        logger.info(
            f"[CollectionEmbedding] Using model {pipeline.model_name} "
            f"({model_source}, {embedding_dimensions} dims)"
        )

        # Store chroma_collection_name in database
        set_collection_chroma_name(collection_id, collection_name)

        # Get live mode settings
        live_meta = self._live_mode.get(collection_id, {
            'wait_for_more': False,
            'source_job_id': None
        })
        wait_for_more = live_meta.get('wait_for_more', False)
        source_job_id = live_meta.get('source_job_id')

        # Initialize vectorstore directory
        vectorstore_dir = os.path.join(
            pipeline.storage_dir, "vectorstore",
            pipeline.model_name.replace('/', '_')
        )
        os.makedirs(vectorstore_dir, exist_ok=True)

        processed_count = 0

        # Main processing loop
        while True:
            if stop_event and stop_event.is_set():
                logger.info(f"[CollectionEmbedding] Embedding paused for collection {collection_id}")
                return

            # Get pending documents
            doc_links = CollectionDocumentLink.query.filter_by(
                collection_id=collection_id
            ).all()
            documents = [
                link.document for link in doc_links
                if link.document and link.document.status in ('pending', 'failed')
            ]
            total_docs = processed_count + len(documents)

            if not documents:
                # Check if we should wait for more documents (live crawl)
                if wait_for_more and self._is_crawl_running(source_job_id):
                    time.sleep(1)
                    continue

                # All documents processed - finalize
                total_chunks = finalize_collection_stats(collection_id)
                indexed_count = sum(
                    1 for link in doc_links
                    if link.document and link.document.status == 'indexed'
                )

                # Backfill ChromaDB if needed (handles deduplicated documents)
                backfill_empty_collection(
                    collection_id, collection_name,
                    vectorstore_dir, pipeline.embeddings
                )

                emit_embedding_completed(collection_id, total_chunks, indexed_count)
                self._live_mode.pop(collection_id, None)
                return

            # Process each document
            for doc in documents:
                if stop_event and stop_event.is_set():
                    logger.info(f"[CollectionEmbedding] Embedding paused for collection {collection_id}")
                    return

                try:
                    # Mark document as processing
                    update_document_status(doc.id, 'processing')

                    # Emit progress
                    progress = int((processed_count / max(total_docs, 1)) * 100)
                    emit_embedding_progress(
                        collection_id, progress, doc.filename,
                        processed_count, total_docs
                    )

                    # Chunk the document
                    from services.rag.lumber_chunker import chunk_file
                    chunks = chunk_file(
                        doc.file_path,
                        doc.mime_type,
                        chunk_size=collection.chunk_size or 1000,
                        chunk_overlap=collection.chunk_overlap or 200,
                    )

                    if not chunks:
                        update_document_status(
                            doc.id, 'failed',
                            'Could not extract any document content'
                        )
                        processed_count += 1
                        continue

                    logger.info(
                        f"[CollectionEmbedding] Document {doc.id} split into {len(chunks)} chunks"
                    )

                    # Process chunks and prepare for ChromaDB
                    chroma_texts, chroma_ids, chroma_metadatas, all_vector_ids = \
                        process_document_chunks(doc, chunks, collection_id, pipeline)

                    db.session.commit()

                    # Upsert to ChromaDB
                    vectorstore = get_or_create_vectorstore(
                        collection_name, vectorstore_dir, pipeline.embeddings
                    )
                    upsert_chunks_to_chroma(
                        vectorstore, chroma_texts, chroma_ids,
                        chroma_metadatas, collection_name
                    )

                    # Embed image chunks if supported
                    embed_image_chunks_for_document(
                        doc, collection_id, collection_name,
                        vectorstore_dir, pipeline.model_name
                    )

                    # Mark document as indexed
                    update_document_status(
                        doc.id, 'indexed',
                        chunk_count=len(chunks),
                        vector_ids=all_vector_ids,
                        embedding_model=pipeline.model_name
                    )

                    emit_document_processed(doc.id, 'indexed', None, collection_id)
                    processed_count += 1

                    # Emit progress after each document
                    progress = int((processed_count / max(total_docs, 1)) * 100)
                    emit_embedding_progress(
                        collection_id, progress, doc.filename,
                        processed_count, total_docs
                    )

                except Exception as e:
                    logger.error(f"[CollectionEmbedding] Error processing document {doc.id}: {e}")
                    self._handle_document_error(doc.id, str(e), collection_id)
                    processed_count += 1

            # Update collection stats after each batch
            try:
                update_collection_stats(
                    collection_id,
                    int((processed_count / max(total_docs, 1)) * 100),
                    len([link for link in doc_links if link.document])
                )
            except Exception as stats_err:
                logger.warning(f"[CollectionEmbedding] Failed to update collection stats: {stats_err}")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _is_crawl_running(self, source_job_id: Optional[str]) -> bool:
        """
        Check if the source crawler job is still running.

        Args:
            source_job_id: Crawler job ID to check

        Returns:
            True if crawl is still running, False otherwise
        """
        if not source_job_id:
            return False

        try:
            from services.crawler.web_crawler import crawler_service
            job = crawler_service.get_job_status(source_job_id)
            return job and job.get('status') in ('queued', 'running')
        except Exception as e:
            logger.debug(f"[CollectionEmbedding] Could not read crawler job {source_job_id}: {e}")
            return False

    def _handle_document_error(
        self,
        doc_id: int,
        error: str,
        collection_id: int
    ) -> None:
        """
        Handle document processing error.

        Args:
            doc_id: Document ID that failed
            error: Error message
            collection_id: Parent collection ID
        """
        from db.database import db
        from .embedding_database import update_document_status
        from .embedding_events import emit_document_processed

        try:
            db.session.rollback()
        except Exception:
            pass

        try:
            update_document_status(doc_id, 'failed', error[:500])
        except Exception as update_err:
            logger.warning(f"[CollectionEmbedding] Failed to update document {doc_id} status: {update_err}")

        emit_document_processed(doc_id, 'failed', error, collection_id)

    def _handle_error(self, collection_id: int, error: str) -> None:
        """
        Handle collection-level error.

        Args:
            collection_id: Collection that failed
            error: Error message
        """
        from db.database import db
        from .embedding_events import emit_embedding_error

        try:
            db.session.rollback()
        except Exception:
            pass

        emit_embedding_error(collection_id, error, self._live_mode)

    def _cleanup(self, collection_id: int) -> None:
        """
        Cleanup resources after embedding completes or fails.

        Args:
            collection_id: Collection to cleanup
        """
        if collection_id in self._active_jobs:
            del self._active_jobs[collection_id]
        if collection_id in self._stop_events:
            del self._stop_events[collection_id]


# =============================================================================
# GLOBAL SERVICE INSTANCE
# =============================================================================

_embedding_service: Optional[CollectionEmbeddingService] = None


def get_collection_embedding_service() -> CollectionEmbeddingService:
    """
    Get the global collection embedding service instance.

    Creates the service on first call, reusing Flask app context.

    Returns:
        The singleton CollectionEmbeddingService instance

    Example:
        >>> service = get_collection_embedding_service()
        >>> service.start_embedding(collection_id=42)
    """
    global _embedding_service
    if _embedding_service is None:
        from flask import current_app
        _embedding_service = CollectionEmbeddingService(current_app._get_current_object())
    return _embedding_service
