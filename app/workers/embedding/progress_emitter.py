# app/workers/embedding/progress_emitter.py
"""
Socket.IO Progress Emitter for Embedding Worker.

This module handles real-time progress updates via Socket.IO,
allowing the frontend to display live embedding progress.

Events Emitted:
    document:progress - Emitted on namespace '/rag' with document status updates

Event Payload:
    {
        "document_id": int,
        "status": "processing" | "indexed" | "failed",
        "progress": int (0-100),
        "step": str (current processing step),
        "error": str | None
    }

Author: LLARS Team
Date: January 2026
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def emit_document_progress(
    doc,
    status: str,
    progress: int = 0,
    step: str = '',
    error: Optional[str] = None
) -> bool:
    """
    Emit document processing progress via Socket.IO.

    Sends real-time updates to connected clients showing the current
    status of document embedding processing.

    Args:
        doc: RAGDocument instance being processed
        status: Current status ('processing', 'indexed', 'failed')
        progress: Progress percentage (0-100)
        step: Human-readable description of current step
        error: Error message if status is 'failed'

    Returns:
        bool: True if emission succeeded, False otherwise

    Example:
        >>> emit_document_progress(doc, 'processing', 50, 'Creating embeddings')
        True
    """
    try:
        from main import socketio
        from socketio_handlers.events_rag import emit_document_progress as _emit

        _emit(
            socketio,
            document_id=doc.id,
            status=status,
            progress=progress,
            step=step,
            error=error
        )
        return True

    except ImportError:
        logger.debug("[ProgressEmitter] Socket.IO not available")
        return False

    except Exception as e:
        logger.debug(f"[ProgressEmitter] Could not emit progress: {e}")
        return False


def emit_batch_progress(
    processed: int,
    total: int,
    current_doc_id: Optional[int] = None
) -> bool:
    """
    Emit batch processing progress via Socket.IO.

    Useful for showing overall progress when processing multiple documents.

    Args:
        processed: Number of documents processed so far
        total: Total number of documents in batch
        current_doc_id: ID of document currently being processed

    Returns:
        bool: True if emission succeeded, False otherwise
    """
    try:
        from main import socketio

        socketio.emit(
            'batch:progress',
            {
                'processed': processed,
                'total': total,
                'current_document_id': current_doc_id,
                'percent': int((processed / total) * 100) if total > 0 else 0
            },
            namespace='/rag'
        )
        return True

    except Exception as e:
        logger.debug(f"[ProgressEmitter] Could not emit batch progress: {e}")
        return False


class ProgressTracker:
    """
    Tracks and emits progress for document processing.

    Provides a convenient interface for updating progress at various
    stages of document processing.

    Attributes:
        doc: The RAGDocument being processed
        total_chunks: Total number of chunks to process
        processed_chunks: Number of chunks processed so far

    Example:
        >>> tracker = ProgressTracker(doc)
        >>> tracker.start()
        >>> tracker.update_chunking(30)
        >>> tracker.update_embedding(50, 10, 100)
        >>> tracker.complete()
    """

    def __init__(self, doc):
        """
        Initialize progress tracker for a document.

        Args:
            doc: RAGDocument instance to track
        """
        self.doc = doc
        self.total_chunks = 0
        self.processed_chunks = 0

    def start(self) -> None:
        """Emit processing started event."""
        emit_document_progress(
            self.doc,
            status='processing',
            progress=10,
            step='Loading document'
        )

    def update_chunking(self, progress: int = 30) -> None:
        """
        Emit chunking progress.

        Args:
            progress: Progress percentage (default 30)
        """
        emit_document_progress(
            self.doc,
            status='processing',
            progress=progress,
            step='Splitting into chunks'
        )

    def update_embedding(
        self,
        base_progress: int,
        current_chunk: int,
        total_chunks: int
    ) -> None:
        """
        Emit embedding progress for a specific chunk.

        Args:
            base_progress: Base progress percentage before embedding started
            current_chunk: Current chunk index (0-based)
            total_chunks: Total number of chunks
        """
        self.total_chunks = total_chunks
        self.processed_chunks = current_chunk + 1

        # Calculate progress: base_progress to 90% during embedding
        embedding_progress = int(
            base_progress + ((current_chunk + 1) / total_chunks) * (90 - base_progress)
        )

        emit_document_progress(
            self.doc,
            status='processing',
            progress=embedding_progress,
            step=f'Embedding chunk {current_chunk + 1}/{total_chunks}'
        )

    def complete(self) -> None:
        """Emit processing completed event."""
        emit_document_progress(
            self.doc,
            status='indexed',
            progress=100,
            step='Completed'
        )

    def fail(self, error: str) -> None:
        """
        Emit processing failed event.

        Args:
            error: Error message describing the failure
        """
        emit_document_progress(
            self.doc,
            status='failed',
            progress=0,
            step='Failed',
            error=error
        )
