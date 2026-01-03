# app/workers/embedding/batch_processor.py
"""
Batch Processor for the Embedding Worker.

This module handles batch processing of documents, including:
- Fetching pending documents from the queue
- Handling stale processing documents (crash recovery)
- Processing documents in configurable batch sizes

Features:
    - Automatic recovery of documents stuck in 'processing' status
    - Configurable batch sizes and stale timeouts
    - Error handling with retry logic
    - Transaction management with rollback support

Author: LLARS Team
Date: January 2026
"""

import logging
from datetime import datetime, timedelta
from typing import List, Tuple

from workers.embedding.constants import BATCH_SIZE, get_stale_processing_seconds
from workers.embedding.document_processor import process_document
from workers.embedding.progress_emitter import emit_document_progress

logger = logging.getLogger(__name__)


def process_batch(
    embedding_resolver,
    pipeline,
    stop_event
) -> int:
    """
    Process a batch of pending documents.

    Handles the full batch processing cycle:
    1. Requeue stale documents from previous crashes
    2. Fetch pending documents
    3. Process each document
    4. Handle errors and update statuses

    Args:
        embedding_resolver: EmbeddingResolver for getting embedding models
        pipeline: RAGPipeline for default configuration
        stop_event: Threading event to check for stop signal

    Returns:
        int: Number of documents successfully processed
    """
    from db.db import db

    # Ensure clean session at batch start
    _safe_rollback(db)

    # Requeue stale documents
    _requeue_stale_documents(db)

    # Get pending documents
    pending_docs = _get_pending_documents(BATCH_SIZE)

    if not pending_docs:
        return 0

    logger.info(f"[BatchProcessor] Processing {len(pending_docs)} documents...")
    processed_count = 0

    for doc in pending_docs:
        if stop_event.is_set():
            break

        try:
            process_document(doc, db, embedding_resolver, pipeline)
            processed_count += 1

        except Exception as e:
            _handle_document_error(doc, e, db)

    return processed_count


def _requeue_stale_documents(db) -> int:
    """
    Requeue documents stuck in 'processing' status.

    Documents can get stuck if the worker crashes or restarts during
    processing. This function detects such documents and requeues them
    for retry (up to max_retries).

    Args:
        db: Database session

    Returns:
        int: Number of documents requeued
    """
    from db.tables import RAGDocument, RAGProcessingQueue

    stale_seconds = get_stale_processing_seconds()
    cutoff = datetime.now() - timedelta(seconds=stale_seconds)

    # Find stale queue entries
    stale_queue = RAGProcessingQueue.query.filter(
        RAGProcessingQueue.status == 'processing',
        RAGProcessingQueue.started_at.isnot(None),
        RAGProcessingQueue.started_at < cutoff
    ).all()

    if stale_queue:
        logger.warning(
            f"[BatchProcessor] Requeuing {len(stale_queue)} stale processing documents"
        )

    requeued = 0
    for entry in stale_queue:
        doc = entry.document
        if not doc:
            continue

        if entry.retry_count >= entry.max_retries:
            # Max retries exceeded - mark as failed
            entry.status = 'failed'
            entry.error_message = 'Stuck in processing; max retries reached'
            doc.status = 'failed'
            doc.processing_error = entry.error_message[:500]
        else:
            # Requeue for retry
            entry.retry_count += 1
            entry.status = 'queued'
            entry.progress_percent = 0
            entry.current_step = 'Requeued after stale processing'
            entry.error_message = None
            entry.started_at = None
            doc.status = 'pending'
            requeued += 1

    db.session.commit()

    # Also reset documents stuck without queue info
    stale_docs = RAGDocument.query.filter(
        RAGDocument.status == 'processing',
        RAGDocument.updated_at.isnot(None),
        RAGDocument.updated_at < cutoff
    ).all()

    if stale_docs:
        logger.warning(
            f"[BatchProcessor] Resetting {len(stale_docs)} stale docs without queue"
        )
        for doc in stale_docs:
            doc.status = 'pending'
            requeued += 1

        db.session.commit()

    return requeued


def _get_pending_documents(limit: int) -> List:
    """
    Get pending documents from the database.

    Args:
        limit: Maximum number of documents to fetch

    Returns:
        List of RAGDocument instances with status='pending'
    """
    from db.tables import RAGDocument

    return RAGDocument.query.filter_by(
        status='pending'
    ).limit(limit).all()


def _handle_document_error(doc, error: Exception, db) -> None:
    """
    Handle an error during document processing.

    Updates the document and queue entry status to 'failed' and
    emits an error event via Socket.IO.

    Args:
        doc: RAGDocument that failed
        error: The exception that occurred
        db: Database session
    """
    from db.tables import RAGProcessingQueue

    logger.error(f"[BatchProcessor] Error processing document {doc.id}: {error}")

    _safe_rollback(db)

    # Update document status
    doc.status = 'failed'
    doc.processing_error = str(error)[:500]
    db.session.commit()

    # Update queue entry
    queue_entry = RAGProcessingQueue.query.filter_by(document_id=doc.id).first()
    if queue_entry:
        queue_entry.status = 'failed'
        queue_entry.error_message = str(error)[:500]
        db.session.commit()

    # Emit error event
    emit_document_progress(doc, 'failed', error=str(error))


def _safe_rollback(db) -> None:
    """
    Safely rollback the database session.

    Args:
        db: Database session
    """
    try:
        db.session.rollback()
    except Exception:
        pass


def get_queue_stats() -> dict:
    """
    Get statistics about the document processing queue.

    Returns:
        Dict with queue statistics:
        - pending: Number of pending documents
        - processing: Number of documents currently processing
        - completed: Number of completed documents
        - failed: Number of failed documents
        - total: Total documents in queue
    """
    from db.tables import RAGProcessingQueue

    stats = {
        'pending': RAGProcessingQueue.query.filter_by(status='queued').count(),
        'processing': RAGProcessingQueue.query.filter_by(status='processing').count(),
        'completed': RAGProcessingQueue.query.filter_by(status='completed').count(),
        'failed': RAGProcessingQueue.query.filter_by(status='failed').count(),
    }
    stats['total'] = sum(stats.values())

    return stats


def get_pending_count() -> int:
    """
    Get the count of pending documents.

    Returns:
        Number of documents with status='pending'
    """
    from db.tables import RAGDocument

    return RAGDocument.query.filter_by(status='pending').count()


def get_processing_count() -> int:
    """
    Get the count of documents currently processing.

    Returns:
        Number of documents with status='processing'
    """
    from db.tables import RAGDocument

    return RAGDocument.query.filter_by(status='processing').count()
