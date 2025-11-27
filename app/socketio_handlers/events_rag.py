"""
Socket.IO events for RAG Processing Queue real-time updates.

Events:
    Client → Server:
        - rag:subscribe_queue: Subscribe to processing queue updates
        - rag:unsubscribe_queue: Unsubscribe from queue updates

    Server → Client:
        - rag:queue_list: Initial processing queue after subscribing
        - rag:queue_updated: Processing queue has been updated
        - rag:document_processed: A document has finished processing
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request
from sqlalchemy import desc

logger = logging.getLogger(__name__)

# Room name for RAG queue subscriptions
RAG_QUEUE_ROOM = "rag_queue_global"


def register_rag_events(socketio):
    """Register Socket.IO events for RAG real-time updates."""

    @socketio.on('rag:subscribe_queue')
    def handle_subscribe_queue():
        """Subscribe to RAG processing queue updates."""
        try:
            join_room(RAG_QUEUE_ROOM)

            logger.info(f"[RAG Socket] Client {request.sid} subscribed to processing queue")

            # Fetch and send current queue
            from db.db import db
            from db.tables import RAGProcessingQueue

            queue_items = RAGProcessingQueue.query.order_by(
                desc(RAGProcessingQueue.priority),
                RAGProcessingQueue.created_at
            ).all()

            queue_data = [{
                'id': q.id,
                'document_id': q.document_id,
                'document_filename': q.document.filename if q.document else None,
                'priority': q.priority,
                'status': q.status,
                'progress_percent': q.progress_percent,
                'current_step': q.current_step,
                'error_message': q.error_message,
                'retry_count': q.retry_count,
                'max_retries': q.max_retries,
                'created_at': q.created_at.isoformat() if q.created_at else None,
                'started_at': q.started_at.isoformat() if q.started_at else None,
                'completed_at': q.completed_at.isoformat() if q.completed_at else None
            } for q in queue_items]

            emit('rag:queue_list', {'queue': queue_data})
            emit('rag:subscribed', {'room': RAG_QUEUE_ROOM})

        except Exception as e:
            logger.error(f"[RAG Socket] Error subscribing to queue: {e}")
            emit('rag:error', {'error': str(e)})

    @socketio.on('rag:unsubscribe_queue')
    def handle_unsubscribe_queue():
        """Unsubscribe from RAG processing queue updates."""
        try:
            leave_room(RAG_QUEUE_ROOM)
            logger.info(f"[RAG Socket] Client {request.sid} unsubscribed from processing queue")

        except Exception as e:
            logger.error(f"[RAG Socket] Error unsubscribing from queue: {e}")

    logger.info("[RAG Socket] Events registered")


def emit_rag_queue_updated(socketio, queue: list = None):
    """
    Emit processing queue update to all subscribed clients.

    Args:
        socketio: Flask-SocketIO instance
        queue: Optional list of queue items (will fetch if None)
    """
    try:
        if queue is None:
            from db.tables import RAGProcessingQueue
            from sqlalchemy import desc

            queue_items = RAGProcessingQueue.query.order_by(
                desc(RAGProcessingQueue.priority),
                RAGProcessingQueue.created_at
            ).all()

            queue = [{
                'id': q.id,
                'document_id': q.document_id,
                'document_filename': q.document.filename if q.document else None,
                'priority': q.priority,
                'status': q.status,
                'progress_percent': q.progress_percent,
                'current_step': q.current_step,
                'error_message': q.error_message,
                'retry_count': q.retry_count,
                'max_retries': q.max_retries,
                'created_at': q.created_at.isoformat() if q.created_at else None,
                'started_at': q.started_at.isoformat() if q.started_at else None,
                'completed_at': q.completed_at.isoformat() if q.completed_at else None
            } for q in queue_items]

        socketio.emit('rag:queue_updated', {'queue': queue}, room=RAG_QUEUE_ROOM)
        logger.info(f"[RAG Socket] Emitted queue update to {RAG_QUEUE_ROOM}")

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting queue update: {e}")


def emit_document_processed(socketio, document_id: int, status: str, error_message: str = None):
    """
    Emit notification when a document has finished processing.

    Args:
        socketio: Flask-SocketIO instance
        document_id: The ID of the processed document
        status: The final status ('indexed', 'failed')
        error_message: Optional error message if failed
    """
    try:
        from db.tables import RAGDocument

        document = RAGDocument.query.get(document_id)

        socketio.emit('rag:document_processed', {
            'document_id': document_id,
            'filename': document.filename if document else None,
            'status': status,
            'error_message': error_message,
            'chunk_count': document.chunk_count if document else 0
        }, room=RAG_QUEUE_ROOM)

        logger.info(f"[RAG Socket] Emitted document processed event for {document_id}")

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting document processed: {e}")


def emit_rag_progress(socketio, queue_id: int, progress_percent: int, current_step: str):
    """
    Emit processing progress update for a specific queue item.

    Args:
        socketio: Flask-SocketIO instance
        queue_id: The ID of the queue item
        progress_percent: Current progress percentage (0-100)
        current_step: Description of the current processing step
    """
    try:
        socketio.emit('rag:progress', {
            'queue_id': queue_id,
            'progress_percent': progress_percent,
            'current_step': current_step
        }, room=RAG_QUEUE_ROOM)

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting progress: {e}")
