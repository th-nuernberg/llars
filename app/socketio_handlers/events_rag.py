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
from sqlalchemy import desc, select

from auth.oidc_validator import validate_token, get_username
from services.permission_service import PermissionService
from services.rag.access_service import RAGAccessService

logger = logging.getLogger(__name__)

# Room prefix for RAG queue subscriptions (per user)
RAG_QUEUE_ROOM_PREFIX = "rag_queue_user_"
RAG_QUEUE_SUBSCRIBERS = {}


def _queue_room(username: str) -> str:
    return f"{RAG_QUEUE_ROOM_PREFIX}{username}"


def _register_queue_subscriber(sid: str, username: str) -> None:
    RAG_QUEUE_SUBSCRIBERS[sid] = username


def unregister_queue_subscriber(sid: str) -> None:
    RAG_QUEUE_SUBSCRIBERS.pop(sid, None)


def _get_queue_subscriber_usernames() -> list:
    return sorted(set(RAG_QUEUE_SUBSCRIBERS.values()))


def _require_user(permission_key: str = None):
    token = str(request.args.get("token") or "").strip()
    payload = validate_token(token) if token else None
    if not payload:
        emit('rag:error', {'error': 'Unauthorized'})
        return None

    username = get_username(payload)
    if not username:
        emit('rag:error', {'error': 'Unauthorized'})
        return None

    if permission_key and not PermissionService.check_permission(username, permission_key):
        emit('rag:error', {'error': 'Forbidden'})
        return None

    return username


def _serialize_queue_items(queue_items) -> list:
    return [{
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


def _get_queue_for_user(username: str):
    from db.tables import RAGProcessingQueue, RAGDocument

    doc_ids = (
        RAGAccessService.apply_document_access_filter(
            RAGDocument.query, username, access='view'
        )
        .with_entities(RAGDocument.id)
        .subquery()
    )

    queue_items = (
        RAGProcessingQueue.query
        .filter(RAGProcessingQueue.document_id.in_(select(doc_ids.c.id)))
        .order_by(desc(RAGProcessingQueue.priority), RAGProcessingQueue.created_at)
        .all()
    )

    return _serialize_queue_items(queue_items)


def _get_image_chunk_stats(collection_id: int) -> tuple[int, int]:
    """Return (total_image_chunks, completed_image_chunks) for a collection."""
    try:
        from db.database import db
        from db.tables import RAGDocumentChunk, CollectionDocumentLink

        linked_doc_ids = db.session.query(CollectionDocumentLink.document_id).filter(
            CollectionDocumentLink.collection_id == collection_id
        ).subquery()

        image_chunks = RAGDocumentChunk.query.filter(
            RAGDocumentChunk.document_id.in_(linked_doc_ids),
            RAGDocumentChunk.has_image.is_(True)
        )

        total = image_chunks.count()
        completed = image_chunks.filter(RAGDocumentChunk.embedding_status == 'completed').count()
        return total, completed
    except Exception:
        return 0, 0


def register_rag_events(socketio):
    """Register Socket.IO events for RAG real-time updates."""

    @socketio.on('rag:subscribe_queue')
    def handle_subscribe_queue():
        """Subscribe to RAG processing queue updates."""
        try:
            username = _require_user('feature:rag:view')
            if not username:
                return

            room = _queue_room(username)
            join_room(room)
            _register_queue_subscriber(request.sid, username)

            logger.info(f"[RAG Socket] Client {request.sid} subscribed to processing queue ({username})")

            # Fetch and send current queue
            queue_data = _get_queue_for_user(username)

            emit('rag:queue_list', {'queue': queue_data}, room=room)
            emit('rag:subscribed', {'room': room})

        except Exception as e:
            logger.error(f"[RAG Socket] Error subscribing to queue: {e}")
            emit('rag:error', {'error': str(e)})

    @socketio.on('rag:unsubscribe_queue')
    def handle_unsubscribe_queue():
        """Unsubscribe from RAG processing queue updates."""
        try:
            username = RAG_QUEUE_SUBSCRIBERS.get(request.sid)
            if username:
                leave_room(_queue_room(username))
                unregister_queue_subscriber(request.sid)
                logger.info(f"[RAG Socket] Client {request.sid} unsubscribed from processing queue ({username})")

        except Exception as e:
            logger.error(f"[RAG Socket] Error unsubscribing from queue: {e}")

    @socketio.on('rag:subscribe_collection')
    def handle_subscribe_collection(data):
        """Subscribe to a specific collection's embedding progress."""
        try:
            username = _require_user('feature:rag:view')
            if not username:
                return

            collection_id = data.get('collection_id')
            if not collection_id:
                emit('rag:error', {'error': 'collection_id required'})
                return

            # Send current collection status
            from db.tables import RAGCollection
            collection = RAGCollection.query.get(collection_id)

            if not collection:
                emit('rag:error', {'error': 'collection not found'})
                return
            if not RAGAccessService.can_view_collection(username, collection):
                emit('rag:error', {'error': 'Forbidden'})
                return

            room = f"rag_collection_{collection_id}"
            join_room(room)
            logger.info(f"[RAG Socket] Client {request.sid} subscribed to collection {collection_id} ({username})")

            image_total, image_completed = _get_image_chunk_stats(collection.id)
            emit('rag:collection_status', {
                'collection_id': collection.id,
                'name': collection.name,
                'embedding_status': collection.embedding_status,
                'embedding_progress': collection.embedding_progress or 0,
                'embedding_error': collection.embedding_error,
                'document_count': collection.document_count,
                'total_chunks': collection.total_chunks,
                'image_chunks_total': image_total,
                'image_chunks_completed': image_completed
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
            username = _require_user('feature:rag:view')
            if not username:
                return

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
            from db.tables import CollectionDocumentLink, RAGCollection
            from services.rag.document_service import DocumentService

            collection = RAGCollection.query.get(collection_id)
            if not collection:
                emit('rag:error', {'error': 'collection not found'})
                return
            if not RAGAccessService.can_view_collection(username, collection):
                emit('rag:error', {'error': 'Forbidden'})
                return

            links = (
                CollectionDocumentLink.query
                .filter_by(collection_id=collection_id)
                .order_by(desc(CollectionDocumentLink.linked_at))
                .limit(limit)
                .all()
            )
            docs = [
                l.document for l in links
                if l.document and RAGAccessService.can_view_document(username, l.document)
            ]

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
        usernames = _get_queue_subscriber_usernames()
        if not usernames:
            return

        for username in usernames:
            queue_data = _get_queue_for_user(username)
            socketio.emit('rag:queue_updated', {'queue': queue_data}, room=_queue_room(username))
        logger.info("[RAG Socket] Emitted queue update to subscribed users")

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

        # Emit to subscribed users who can view the document
        if document:
            for username in _get_queue_subscriber_usernames():
                if RAGAccessService.can_view_document(username, document):
                    socketio.emit('rag:document_processed', payload, room=_queue_room(username))

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
        from db.tables import RAGProcessingQueue

        queue_item = RAGProcessingQueue.query.get(queue_id)
        document = queue_item.document if queue_item else None

        if not document:
            return

        payload = {
            'queue_id': queue_id,
            'progress_percent': progress_percent,
            'current_step': current_step
        }

        for username in _get_queue_subscriber_usernames():
            if RAGAccessService.can_view_document(username, document):
                socketio.emit('rag:progress', payload, room=_queue_room(username))

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting progress: {e}")


def emit_document_progress(socketio, document_id: int, status: str, progress: int = 0, step: str = '',
                           error: str = None):
    """
    Emit document-level progress updates to authorized subscribers.

    Args:
        socketio: Flask-SocketIO instance
        document_id: The document ID
        status: Current status string
        progress: Progress percentage
        step: Current processing step
        error: Optional error message
    """
    try:
        from db.tables import RAGDocument

        document = RAGDocument.query.get(document_id)
        if not document:
            return

        payload = {
            'document_id': document_id,
            'filename': document.filename,
            'status': status,
            'progress': progress,
            'step': step
        }
        if error:
            payload['error'] = error

        for username in _get_queue_subscriber_usernames():
            if RAGAccessService.can_view_document(username, document):
                socketio.emit('rag:document_progress', payload, room=_queue_room(username))

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting document progress: {e}")


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
        image_total, image_completed = _get_image_chunk_stats(collection_id)
        payload = {
            'collection_id': collection_id,
            'progress': progress,
            'current_document': current_doc,
            'documents_processed': docs_processed,
            'documents_total': docs_total,
            'image_chunks_total': image_total,
            'image_chunks_completed': image_completed
        }
        socketio.emit('rag:collection_progress', payload, room=room)

        from db.tables import RAGCollection
        collection = RAGCollection.query.get(collection_id)
        if collection:
            for username in _get_queue_subscriber_usernames():
                if RAGAccessService.can_view_collection(username, collection):
                    socketio.emit('rag:collection_progress', payload, room=_queue_room(username))

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
        image_total, image_completed = _get_image_chunk_stats(collection_id)
        data = {
            'collection_id': collection_id,
            'status': 'completed',
            'total_chunks': total_chunks,
            'total_documents': total_docs,
            'image_chunks_total': image_total,
            'image_chunks_completed': image_completed
        }
        socketio.emit('rag:collection_completed', data, room=room)

        from db.tables import RAGCollection
        collection = RAGCollection.query.get(collection_id)
        if collection:
            for username in _get_queue_subscriber_usernames():
                if RAGAccessService.can_view_collection(username, collection):
                    socketio.emit('rag:collection_completed', data, room=_queue_room(username))

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

        from db.tables import RAGCollection
        collection = RAGCollection.query.get(collection_id)
        if collection:
            for username in _get_queue_subscriber_usernames():
                if RAGAccessService.can_view_collection(username, collection):
                    socketio.emit('rag:collection_error', data, room=_queue_room(username))

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting collection error: {e}")


def emit_document_uploaded(socketio, document_id: int, collection_id: int, uploaded_by: str):
    """
    Emit when a new document is uploaded to a collection.
    This notifies all users subscribed to the collection for real-time updates.

    Args:
        socketio: Flask-SocketIO instance
        document_id: The ID of the uploaded document
        collection_id: The collection ID the document was uploaded to
        uploaded_by: Username who uploaded the document
    """
    try:
        from db.tables import RAGDocument, RAGCollection
        from services.rag.document_service import DocumentService

        document = RAGDocument.query.get(document_id)
        collection = RAGCollection.query.get(collection_id) if collection_id else None

        if not document:
            return

        payload = {
            'event': 'document_uploaded',
            'document_id': document_id,
            'collection_id': collection_id,
            'uploaded_by': uploaded_by,
            'document': DocumentService.serialize_document(document),
            'collection': {
                'id': collection.id,
                'name': collection.name,
                'display_name': collection.display_name,
                'document_count': collection.document_count
            } if collection else None
        }

        # Emit to collection room (for users viewing this collection)
        if collection_id:
            room = f"rag_collection_{collection_id}"
            socketio.emit('rag:document_uploaded', payload, room=room)
            logger.info(f"[RAG Socket] Emitted document_uploaded to room {room}")

        # Also emit to queue subscribers who have access
        if document:
            for username in _get_queue_subscriber_usernames():
                if RAGAccessService.can_view_document(username, document):
                    socketio.emit('rag:document_uploaded', payload, room=_queue_room(username))

    except Exception as e:
        logger.error(f"[RAG Socket] Error emitting document uploaded: {e}")
