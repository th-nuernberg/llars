# app/workers/embedding/worker.py
"""
Main Embedding Worker Class.

This module contains the EmbeddingWorker class that coordinates document
embedding processing in a background thread. It delegates to specialized
modules for specific tasks.

Architecture:
    The worker is a thin coordinator that:
    1. Manages the background thread lifecycle
    2. Initializes the RAG pipeline
    3. Delegates to batch_processor for document processing
    4. Uses embedding_resolver for model management

Usage:
    from workers.embedding import start_embedding_worker, stop_embedding_worker

    # Start during app initialization
    start_embedding_worker(app)

    # Stop during shutdown
    stop_embedding_worker()

Author: LLARS Team
Date: January 2026
"""

import logging
import threading
import time
from typing import Optional

from workers.embedding.constants import POLL_INTERVAL
from workers.embedding.embedding_resolver import EmbeddingResolver
from workers.embedding.batch_processor import process_batch

logger = logging.getLogger(__name__)

# Global worker instance
_worker: Optional['EmbeddingWorker'] = None
_worker_lock = threading.Lock()


class EmbeddingWorker:
    """
    Background worker for processing document embeddings.

    Runs in a separate thread and continuously processes documents
    with status='pending' from the RAGDocument table.

    Attributes:
        app: Flask application instance
        running: Boolean indicating if worker is active
        thread: Background processing thread
        _stop_event: Threading event for graceful shutdown
        _pipeline: RAGPipeline for embedding generation
        _embedding_resolver: Resolver for embedding models

    Example:
        >>> worker = EmbeddingWorker(app)
        >>> worker.start()
        >>> # ... application runs ...
        >>> worker.stop()
    """

    def __init__(self, app):
        """
        Initialize the embedding worker.

        Args:
            app: Flask application instance (required for app context)
        """
        self.app = app
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pipeline = None
        self._embedding_resolver = None

    def start(self) -> None:
        """
        Start the worker in a background thread.

        Creates a daemon thread that will process documents continuously
        until stop() is called.
        """
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

    def stop(self) -> None:
        """
        Stop the worker gracefully.

        Signals the worker to stop and waits for the thread to finish
        (up to 10 seconds timeout).
        """
        logger.info("[EmbeddingWorker] Stopping...")

        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10.0)

        logger.info("[EmbeddingWorker] Stopped")

    def _run(self) -> None:
        """
        Main worker loop.

        Runs within a Flask app context and continuously processes
        document batches until stopped.
        """
        with self.app.app_context():
            try:
                # Initialize pipeline and resolver
                self._init_components()

                # Main processing loop
                while self.running and not self._stop_event.is_set():
                    try:
                        processed = process_batch(
                            self._embedding_resolver,
                            self._pipeline,
                            self._stop_event
                        )

                        if processed == 0:
                            # No documents to process, wait before checking again
                            self._stop_event.wait(timeout=POLL_INTERVAL)
                        else:
                            # Processed some documents, immediately check for more
                            time.sleep(0.1)

                    except Exception as e:
                        self._handle_loop_error(e)

            except Exception as e:
                logger.error(f"[EmbeddingWorker] Fatal error: {e}")

            finally:
                self.running = False
                logger.info("[EmbeddingWorker] Exited")

    def _init_components(self) -> None:
        """
        Initialize the RAG pipeline and embedding resolver.

        Raises:
            Exception: If pipeline initialization fails
        """
        try:
            from rag_pipeline import RAGPipeline

            self._pipeline = RAGPipeline()
            self._embedding_resolver = EmbeddingResolver(self._pipeline)

            logger.info(
                f"[EmbeddingWorker] Initialized with model: {self._pipeline.model_name}"
            )

        except Exception as e:
            logger.error(f"[EmbeddingWorker] Failed to initialize: {e}")
            raise

    def _handle_loop_error(self, error: Exception) -> None:
        """
        Handle an error in the processing loop.

        Rolls back the database session and waits before retrying.

        Args:
            error: The exception that occurred
        """
        logger.error(f"[EmbeddingWorker] Error in processing loop: {error}")

        try:
            from db.db import db
            db.session.rollback()
        except Exception:
            pass

        # Wait before retrying
        self._stop_event.wait(timeout=5)

    @property
    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        return self.running and self.thread is not None and self.thread.is_alive()

    @property
    def pipeline(self):
        """Get the RAG pipeline instance."""
        return self._pipeline

    @property
    def embedding_resolver(self) -> Optional[EmbeddingResolver]:
        """Get the embedding resolver instance."""
        return self._embedding_resolver


# =============================================================================
# Global Worker Management Functions
# =============================================================================

def get_embedding_worker() -> Optional[EmbeddingWorker]:
    """
    Get the global embedding worker instance.

    Returns:
        EmbeddingWorker instance or None if not started
    """
    return _worker


def start_embedding_worker(app) -> None:
    """
    Start the global embedding worker.

    Should be called once during application startup. If a worker
    already exists, this function logs a warning and returns.

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


def stop_embedding_worker() -> None:
    """
    Stop the global embedding worker.

    Should be called during application shutdown.
    """
    global _worker

    with _worker_lock:
        if _worker is None:
            return

        _worker.stop()
        _worker = None

        logger.info("[EmbeddingWorker] Global worker stopped")
