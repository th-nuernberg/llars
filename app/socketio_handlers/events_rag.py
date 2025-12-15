"""
Socket.IO events for RAG Processing Queue real-time updates.

Events:
    Client → Server:
        - rag:subscribe_queue: Subscribe to processing queue updates
        - rag:unsubscribe_queue: Unsubscribe from queue updates
        - rag:subscribe_collection: Subscribe to a collection's embedding progress
        - rag:unsubscribe_collection: Unsubscribe from collection progress
        - rag:get_collection_documents: Request recent documents for a collection

    Server → Client:
        - rag:queue_list: Initial processing queue after subscribing
        - rag:queue_updated: Processing queue has been updated
        - rag:document_processed: A document has finished processing
        - rag:collection_progress: Embedding progress for a collection
        - rag:collection_completed: Collection embedding completed
        - rag:collection_error: Collection embedding failed
        - rag:collection_documents: Recent documents for a collection
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

    @socketio.on('rag:subscribe_collection')
    def handle_subscribe_collection(data):
        """Subscribe to a specific collection's embedding progress."""
        try:
            collection_id = data.get('collection_id')
            if not collection_id:
                emit('rag:error', {'error': 'collection_id required'})
                return

            room = f"rag_collection_{collection_id}"
            join_room(room)
            logger.info(f"[RAG Socket] Client {request.sid} subscribed to collection {collection_id}")

            # Send current collection status
            from db.tables import RAGCollection
            collection = RAGCollection.query.get(collection_id)

            if collection:
                emit('rag:collection_status', {
                    'collection_id': collection.id,
                    'name': collection.name,
                    'embedding_status': collection.embedding_status,
                    'embedding_progress': collection.embedding_progress or 0,
                    'embedding_error': collection.embedding_error,
                    'document_count': collection.document_count,
                    'total_chunks': collection.total_chunks
                })

            emit('rag:subscribed_collection', {'collection_id': collection_id, 'room': room})

        except Exception as e:
            logger.error(f"[RAG Socket] Error subscribing to collection: {e}")
            emit('rag:error', {'error': str(e)})

    @socketio.on('rag:unsubscribe_collection')
    def handle_unsubscribe_collection(data):
        """Unsubscribe from a collection's embedding progress."""
        try:
            collection_id = data.get('collection_id')
            if collection_id:
                room = f"rag_collection_{collection_id}"
                leave_room(room)
                logger.info(f"[RAG Socket] Client {request.sid} unsubscribed from collection {collection_id}")

        except Exception as e:
            logger.error(f"[RAG Socket] Error unsubscribing from collection: {e}")

    @socketio.on('rag:get_collection_documents')
    def handle_get_collection_documents(data):
        """Fetch recent documents for a collection (includes linked documents via CollectionDocumentLink)."""
        try:
            data = data or {}
            collection_id = data.get('collection_id')
            if not collection_id:
                emit('rag:error', {'error': 'collection_id required'})
                return

            limit = data.get('limit', data.get('per_page', 25))
            try:
                limit = int(limit)
            except Exception:
                limit = 25
            limit = max(1, min(limit, 200))

            from sqlalchemy import desc
            from db.tables import CollectionDocumentLink
            from services.rag.document_service import DocumentService

            links = (
                CollectionDocumentLink.query
                .filter_by(collection_id=collection_id)
                .order_by(desc(CollectionDocumentLink.linked_at))
                .limit(limit)
                .all()
            )
            docs = [l.document for l in links if l.document]

            emit('rag:collection_documents', {
                'collection_id': collection_id,
                'documents': [DocumentService.serialize_document(d) for d in docs],
                'count': len(docs)
            })

        except Exception as e:
            logger.error(f"[RAG Socket] Error fetching collection documents: {e}")
            emit('rag:error', {'error': str(e)})

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


def emit_document_processed(
    socketio,
    document_id: int,
    status: str,
    error_message: str = None,
    collection_id: int = None
):
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
        from services.rag.document_service import DocumentService

        document = RAGDocument.query.get(document_id)

        effective_collection_id = collection_id or (document.collection_id if document else None)
        payload = {
            'document_id': document_id,
            'filename': document.filename if document else None,
            'status': status,
            'error_message': error_message,
            'chunk_count': document.chunk_count if document else 0,
            'collection_id': effective_collection_id,
            'document': DocumentService.serialize_document(document) if document else None
        }

        # Emit to global room
        socketio.emit('rag:document_processed', payload, room=RAG_QUEUE_ROOM)

        # Also emit to the collection room (so UIs can subscribe without global queue)
        if effective_collection_id:
            socketio.emit('rag:document_processed', payload, room=f"rag_collection_{effective_collection_id}")

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


def emit_collection_progress(socketio, collection_id: int, progress: int, current_doc: str = None,
                             docs_processed: int = 0, docs_total: int = 0):
    """
    Emit embedding progress for a collection.

    Args:
        socketio: Flask-SocketIO instance
        collection_id: The collection ID
        progress: Overall progress percentage (0-100)
        current_doc: Currently processing document name
        docs_processed: Number of documents already processed
        docs_total: Total number of documents to process
    """
    try:
        room = f"rag_collection_{collection_id}"
        socketio.emit('rag:collection_progress', {
            'collection_id': collection_id,
            'progress': progress,
            'current_document': current_doc,
            'documents_processed': docs_processed,
            'documents_total': docs_total
        }, room=room)

        # Also emit to global room
        socketio.emit('rag:collection_progress', {
            'collection_id': collection_id,
            'progress': progress,
            'current_document': current_doc,
            'documents_processed': docs_processed,
            'documents_total': docs_total
        }, room=RAG_QUEUE_ROOM)

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting collection progress: {e}")


def emit_collection_completed(socketio, collection_id: int, total_chunks: int, total_docs: int):
    """
    Emit when collection embedding is completed.

    Args:
        socketio: Flask-SocketIO instance
        collection_id: The collection ID
        total_chunks: Total number of chunks embedded
        total_docs: Total number of documents processed
    """
    try:
        room = f"rag_collection_{collection_id}"
        data = {
            'collection_id': collection_id,
            'status': 'completed',
            'total_chunks': total_chunks,
            'total_documents': total_docs
        }
        socketio.emit('rag:collection_completed', data, room=room)
        socketio.emit('rag:collection_completed', data, room=RAG_QUEUE_ROOM)

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting collection completed: {e}")


def emit_collection_error(socketio, collection_id: int, error: str):
    """
    Emit when collection embedding fails.

    Args:
        socketio: Flask-SocketIO instance
        collection_id: The collection ID
        error: Error message
    """
    try:
        room = f"rag_collection_{collection_id}"
        data = {
            'collection_id': collection_id,
            'status': 'failed',
            'error': error
        }
        socketio.emit('rag:collection_error', data, room=room)
        socketio.emit('rag:collection_error', data, room=RAG_QUEUE_ROOM)

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting collection error: {e}")
