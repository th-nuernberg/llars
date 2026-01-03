# embedding_events.py
"""
WebSocket event emitters for the Collection Embedding Service.

This module handles all real-time communication during embedding:
- Progress updates during document processing
- Completion notifications when embedding finishes
- Error notifications when embedding fails
- Wizard session updates for chatbot building

Events are emitted via Flask-SocketIO to connected clients, enabling
real-time progress tracking in the frontend without polling.

Event Types:
    - collection:progress: Emitted during document processing
    - collection:completed: Emitted when all documents are processed
    - collection:error: Emitted when an error occurs
    - wizard:progress: Emitted for chatbot wizard sessions

Used by: collection_embedding_service.py
Depends on: socketio_handlers/events_rag.py, socketio_handlers/events_wizard.py
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# PROGRESS EVENTS
# =============================================================================

def emit_embedding_progress(
    collection_id: int,
    progress: int,
    current_doc: str,
    docs_processed: int,
    docs_total: int
) -> None:
    """
    Emit embedding progress via WebSocket and update wizard session.

    Sends real-time progress updates to:
    1. All clients subscribed to the collection (via RAG events)
    2. The wizard session if this is a chatbot embedding

    Args:
        collection_id: ID of the collection being embedded
        progress: Current progress percentage (0-100)
        current_doc: Filename of the document currently being processed
        docs_processed: Number of documents already processed
        docs_total: Total number of documents to process

    Side Effects:
        - Emits 'collection:progress' WebSocket event
        - Updates RAGCollection.embedding_progress in database
        - If linked to a chatbot wizard, emits 'wizard:progress' event

    Example:
        >>> emit_embedding_progress(
        ...     collection_id=42,
        ...     progress=50,
        ...     current_doc='document.pdf',
        ...     docs_processed=5,
        ...     docs_total=10
        ... )
        # Emits: {"collection_id": 42, "progress": 50, "current_doc": "document.pdf", ...}
    """
    try:
        from main import socketio
        from socketio_handlers.events_rag import emit_collection_progress

        # Emit to all subscribed clients
        emit_collection_progress(
            socketio, collection_id, progress,
            current_doc, docs_processed, docs_total
        )

        # Update database with current progress
        _update_collection_progress_in_db(collection_id, progress)

        # Update wizard session if this is a chatbot embedding
        _update_wizard_session_if_applicable(
            collection_id, progress, docs_processed, docs_total, current_doc
        )

    except Exception as e:
        # Progress emission is non-critical, log and continue
        logger.debug(f"[CollectionEmbedding] Could not emit progress: {e}")


def _update_collection_progress_in_db(collection_id: int, progress: int) -> None:
    """
    Update collection embedding progress in database.

    Args:
        collection_id: Collection ID to update
        progress: Progress percentage (0-100)

    Note:
        This is a best-effort update. Failures are logged but don't
        interrupt the embedding process.
    """
    try:
        from db.db import db
        from db.tables import RAGCollection

        collection = RAGCollection.query.get(collection_id)
        if collection:
            collection.embedding_progress = progress
            db.session.commit()
    except Exception as e:
        logger.debug(f"[CollectionEmbedding] Could not update progress in DB: {e}")
        try:
            from db.db import db
            db.session.rollback()
        except Exception:
            pass


def _update_wizard_session_if_applicable(
    collection_id: int,
    progress: int,
    docs_processed: int,
    docs_total: int,
    current_doc: str
) -> None:
    """
    Update wizard session if this collection is linked to a chatbot being built.

    The chatbot wizard shows embedding progress during the "embedding" phase.
    This function detects if the collection is a primary collection for a
    chatbot in the embedding phase and updates the wizard progress.

    Args:
        collection_id: Collection being embedded
        progress: Progress percentage (0-100)
        docs_processed: Documents processed so far
        docs_total: Total documents
        current_doc: Current document filename

    Note:
        Silently ignores if no chatbot is linked or wizard service unavailable.
    """
    try:
        from db.tables import Chatbot

        # Check if this collection is linked to a chatbot in embedding phase
        chatbot = Chatbot.query.filter_by(primary_collection_id=collection_id).first()
        if not chatbot or chatbot.build_status != 'embedding':
            return

        # Update wizard session
        from main import socketio
        from services.wizard import get_wizard_session_service
        from socketio_handlers.events_wizard import emit_wizard_progress

        wizard_service = get_wizard_session_service()
        wizard_service.update_embedding_progress(chatbot.id, {
            'embedding_progress': progress,
            'documents_processed': docs_processed,
            'documents_total': docs_total,
            'current_document': current_doc,
        })

        emit_wizard_progress(
            socketio, chatbot.id,
            wizard_service.get_progress(chatbot.id)
        )

    except Exception as we:
        logger.debug(f"[CollectionEmbedding] Could not update wizard session: {we}")


# =============================================================================
# COMPLETION EVENTS
# =============================================================================

def emit_embedding_completed(
    collection_id: int,
    total_chunks: int,
    docs_processed: int
) -> None:
    """
    Mark collection as completed and emit completion event.

    Updates database status to 'completed' and notifies all connected
    clients that embedding has finished successfully.

    Args:
        collection_id: ID of the completed collection
        total_chunks: Total number of chunks created
        docs_processed: Number of documents that were processed

    Database Effects:
        - Sets RAGCollection.embedding_status = 'completed'
        - Sets RAGCollection.embedding_progress = 100
        - Updates RAGCollection.total_chunks and last_indexed_at
        - Updates all CollectionEmbedding records for this collection

    WebSocket Events:
        - Emits 'collection:completed' to all subscribed clients
    """
    try:
        from db.db import db
        from db.tables import RAGCollection
        from db.models.rag import CollectionEmbedding

        # Update RAGCollection record
        collection = RAGCollection.query.get(collection_id)
        if collection:
            collection.embedding_status = 'completed'
            collection.embedding_progress = 100
            collection.total_chunks = total_chunks
            collection.last_indexed_at = datetime.now()

            # Also update CollectionEmbedding records
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

        # Emit completion event to clients
        from main import socketio
        from socketio_handlers.events_rag import emit_collection_completed
        emit_collection_completed(socketio, collection_id, total_chunks, docs_processed)

        logger.info(
            f"[CollectionEmbedding] Collection {collection_id} completed: "
            f"{total_chunks} chunks, {docs_processed} docs"
        )

    except Exception as e:
        logger.error(f"[CollectionEmbedding] Error completing collection: {e}")


# =============================================================================
# ERROR EVENTS
# =============================================================================

def emit_embedding_error(
    collection_id: int,
    error: str,
    live_mode_registry: Optional[dict] = None
) -> None:
    """
    Set error status on collection and emit error event.

    Updates database to reflect the error state and notifies connected
    clients that embedding has failed.

    Args:
        collection_id: ID of the collection that failed
        error: Error message (truncated to 1000 chars for DB storage)
        live_mode_registry: Optional dict to clean up live mode tracking

    Database Effects:
        - Sets RAGCollection.embedding_status = 'failed'
        - Sets RAGCollection.embedding_error to the error message
        - Updates all CollectionEmbedding records to 'failed' status

    WebSocket Events:
        - Emits 'collection:error' to all subscribed clients

    Example:
        >>> emit_embedding_error(
        ...     collection_id=42,
        ...     error="Model not available",
        ...     live_mode_registry=service._live_mode
        ... )
    """
    try:
        from db.db import db
        from db.tables import RAGCollection
        from db.models.rag import CollectionEmbedding

        # Update RAGCollection record
        collection = RAGCollection.query.get(collection_id)
        if collection:
            collection.embedding_status = 'failed'
            collection.embedding_error = error[:1000]  # Truncate for DB

            # Also update CollectionEmbedding records
            coll_embeddings = CollectionEmbedding.query.filter_by(
                collection_id=collection_id,
                status='processing'
            ).all()
            for ce in coll_embeddings:
                ce.status = 'failed'
                ce.error_message = error[:1000]

            db.session.commit()

        # Emit error event to clients
        from main import socketio
        from socketio_handlers.events_rag import emit_collection_error
        emit_collection_error(socketio, collection_id, error)

        logger.warning(
            f"[CollectionEmbedding] Collection {collection_id} failed: {error[:200]}"
        )

    except Exception as e:
        logger.error(f"[CollectionEmbedding] Error setting collection error: {e}")

    finally:
        # Cleanup live mode tracking
        if live_mode_registry is not None:
            live_mode_registry.pop(collection_id, None)


# =============================================================================
# DOCUMENT EVENTS
# =============================================================================

def emit_document_processed(
    doc_id: int,
    status: str,
    error: Optional[str],
    collection_id: int
) -> None:
    """
    Emit document processing status update.

    Called after each document is processed to notify clients of
    individual document status changes.

    Args:
        doc_id: ID of the processed document
        status: New status ('indexed' or 'failed')
        error: Error message if status is 'failed'
        collection_id: Parent collection ID

    WebSocket Events:
        - Emits 'document:processed' to all subscribed clients

    Example:
        >>> emit_document_processed(
        ...     doc_id=123,
        ...     status='indexed',
        ...     error=None,
        ...     collection_id=42
        ... )
    """
    try:
        from main import socketio
        from socketio_handlers.events_rag import emit_document_processed as emit_doc

        emit_doc(socketio, doc_id, status, error, collection_id=collection_id)

    except Exception as e:
        # Non-critical, continue silently
        logger.debug(f"[CollectionEmbedding] Could not emit document status: {e}")
