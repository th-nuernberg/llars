"""
RAG Collection Management Routes

Provides API endpoints for managing RAG collections.
All routes are protected with appropriate permissions.

Routes:
    GET    /api/rag/collections                - List all collections
    GET    /api/rag/collections/<id>           - Get collection details
    POST   /api/rag/collections                - Create new collection
    PUT    /api/rag/collections/<id>           - Update collection
    DELETE /api/rag/collections/<id>           - Delete collection
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, ForbiddenError
)
from db.tables import (
    RAGCollection,
    RAGDocument,
    RAGDocumentChunk,
    RAGProcessingQueue,
    CollectionDocumentLink,
    ChatbotCollection,
)
from db.models.rag import CollectionEmbedding
from db.models.llm_model import LLMModel
from db.database import db
from sqlalchemy import desc
from auth.auth_utils import AuthUtils
from services.rag.access_service import RAGAccessService
from services.chatbot_activity_service import ChatbotActivityService

rag_collection_bp = Blueprint('rag_collection', __name__)


@rag_collection_bp.route('/collections', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_collections():
    """Get all RAG collections with statistics"""
    username = AuthUtils.extract_username_without_validation()
    collections_query = RAGCollection.query.filter_by(is_active=True)
    collections_query = RAGAccessService.apply_collection_view_filter(collections_query, username)
    collections = collections_query.all()

    result = []
    for c in collections:
        # Count linked documents via CollectionDocumentLink (n:m relationship)
        link_count = CollectionDocumentLink.query.filter_by(collection_id=c.id).count()

        # Count by link type
        new_docs = CollectionDocumentLink.query.filter_by(collection_id=c.id, link_type='new').count()
        linked_docs = CollectionDocumentLink.query.filter_by(collection_id=c.id, link_type='linked').count()

        can_edit = RAGAccessService.can_edit_collection(username, c)
        can_delete = RAGAccessService.can_delete_collection(username, c)
        can_share = RAGAccessService.can_share_collection(username, c)

        result.append({
            'id': c.id,
            'name': c.name,
            'display_name': c.display_name,
            'description': c.description,
            'icon': c.icon,
            'color': c.color,
            'document_count': link_count,  # Use link count instead of legacy field
            'documents_new': new_docs,
            'documents_linked': linked_docs,
            'total_chunks': c.total_chunks,
            'total_size_bytes': c.total_size_bytes,
            'total_size_mb': round(c.total_size_bytes / (1024*1024), 2),
            'embedding_model': c.embedding_model,
            'chunk_size': c.chunk_size,
            'chunk_overlap': c.chunk_overlap,
            'retrieval_k': c.retrieval_k,
            'is_public': c.is_public,
            'created_by': c.created_by,
            'can_edit': can_edit,
            'can_delete': can_delete,
            'can_share': can_share,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'last_indexed_at': c.last_indexed_at.isoformat() if c.last_indexed_at else None,
            # Embedding status fields (for Chatbot Builder)
            'source_type': c.source_type,
            'source_url': c.source_url,
            'embedding_status': c.embedding_status,
            'embedding_progress': c.embedding_progress or 0,
            'embedding_error': c.embedding_error,
            # Multi-embedding info
            'embeddings': _get_collection_embeddings_summary(c.id)
        })

    return jsonify({
        'success': True,
        'collections': result
    }), 200


def _get_collection_embeddings_summary(collection_id: int) -> list:
    """Get summary of all embeddings for a collection."""
    embeddings = CollectionEmbedding.query.filter_by(
        collection_id=collection_id
    ).order_by(desc(CollectionEmbedding.priority)).all()

    return [{
        'model_id': e.model_id,
        'model_source': e.model_source,
        'dimensions': e.embedding_dimensions,
        'status': e.status,
        'progress': e.progress,
        'chunk_count': e.chunk_count,
        'priority': e.priority,
        'chroma_collection': e.chroma_collection_name,
        'completed_at': e.completed_at.isoformat() if e.completed_at else None
    } for e in embeddings]


@rag_collection_bp.route('/collections/<int:collection_id>', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_collection(collection_id):
    """Get detailed collection information with linked documents"""
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    username = AuthUtils.extract_username_without_validation()
    if not RAGAccessService.can_view_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    # Get documents via CollectionDocumentLink (n:m relationship)
    links = CollectionDocumentLink.query.filter_by(
        collection_id=collection_id
    ).order_by(desc(CollectionDocumentLink.linked_at)).all()

    # Build document list with link info
    documents_list = []
    for link in links:
        doc = link.document
        if doc and RAGAccessService.can_view_document(username, doc):
            documents_list.append({
                'id': doc.id,
                'filename': doc.filename,
                'title': doc.title,
                'file_size_bytes': doc.file_size_bytes,
                'mime_type': doc.mime_type,
                'status': doc.status,
                'chunk_count': doc.chunk_count,
                'retrieval_count': doc.retrieval_count,
                'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                # Link-specific info
                'link_type': link.link_type,
                'source_url': link.source_url,
                'linked_at': link.linked_at.isoformat() if link.linked_at else None
            })

    # Count by link type
    new_docs = sum(1 for link in links if link.link_type == 'new')
    linked_docs = sum(1 for link in links if link.link_type == 'linked')

    return jsonify({
        'success': True,
        'collection': {
            'id': collection.id,
            'name': collection.name,
            'display_name': collection.display_name,
            'description': collection.description,
            'icon': collection.icon,
            'color': collection.color,
            'document_count': len(links),
            'documents_new': new_docs,
            'documents_linked': linked_docs,
            'total_chunks': collection.total_chunks,
            'total_size_bytes': collection.total_size_bytes,
            'total_size_mb': round(collection.total_size_bytes / (1024*1024), 2),
            'embedding_model': collection.embedding_model,
            'chunk_size': collection.chunk_size,
            'chunk_overlap': collection.chunk_overlap,
            'retrieval_k': collection.retrieval_k,
            'is_public': collection.is_public,
            'created_by': collection.created_by,
            'can_edit': RAGAccessService.can_edit_collection(username, collection),
            'can_delete': RAGAccessService.can_delete_collection(username, collection),
            'can_share': RAGAccessService.can_share_collection(username, collection),
            'created_at': collection.created_at.isoformat() if collection.created_at else None,
            'last_indexed_at': collection.last_indexed_at.isoformat() if collection.last_indexed_at else None,
            'documents': documents_list,
            # Multi-embedding info
            'embeddings': _get_collection_embeddings_summary(collection.id)
        }
    }), 200


@rag_collection_bp.route('/collections', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def create_collection():
    """Create new RAG collection"""
    data = request.get_json()

    # Get username from token
    username = AuthUtils.extract_username_without_validation()

    # Validate required fields
    if not data.get('name') or not data.get('display_name'):
        raise ValidationError('name and display_name are required')

    # Check if collection name already exists
    existing = RAGCollection.query.filter_by(name=data['name']).first()
    if existing:
        raise ConflictError(f"Collection with name '{data['name']}' already exists")

    # Embedding model (actual Chroma collection name is set by embedding services/worker)
    embedding_model = data.get('embedding_model')
    if embedding_model:
        db_model = LLMModel.get_by_model_id(embedding_model)
        if not db_model or not db_model.is_active or db_model.model_type != LLMModel.MODEL_TYPE_EMBEDDING:
            raise ValidationError("embedding_model must reference an active embedding model")
        embedding_model = db_model.model_id
    else:
        default_model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_EMBEDDING)
        if not default_model_id:
            raise ValidationError("No default embedding model configured in llm_models")
        embedding_model = default_model_id

    # Create new collection
    collection = RAGCollection(
        name=data['name'],
        display_name=data['display_name'],
        description=data.get('description'),
        icon=data.get('icon', '📚'),
        color=data.get('color', '#4CAF50'),
        embedding_model=embedding_model,
        chunk_size=data.get('chunk_size', 1500),
        chunk_overlap=data.get('chunk_overlap', 300),
        retrieval_k=data.get('retrieval_k', 4),
        is_public=data.get('is_public', False),
        created_by=username
    )

    db.session.add(collection)
    db.session.commit()

    # Log activity
    ChatbotActivityService.log_collection_created(
        collection_id=collection.id,
        collection_name=collection.name,
        display_name=collection.display_name,
        username=username,
        is_public=collection.is_public
    )

    return jsonify({
        'success': True,
        'message': f"Collection '{data['display_name']}' created successfully",
        'collection': {
            'id': collection.id,
            'name': collection.name,
            'display_name': collection.display_name
        }
    }), 201


@rag_collection_bp.route('/collections/<int:collection_id>', methods=['PUT'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def update_collection(collection_id):
    """Update collection metadata"""
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    username = AuthUtils.extract_username_without_validation()
    if not RAGAccessService.can_edit_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    data = request.get_json()

    # Track changes for activity log
    trackable_fields = ['display_name', 'description', 'icon', 'color', 'is_public', 'retrieval_k']
    changed_fields = {}
    for field in trackable_fields:
        if field in data:
            old_val = getattr(collection, field, None)
            new_val = data[field]
            if old_val != new_val:
                changed_fields[field] = {'old': old_val, 'new': new_val}

    # Update allowed fields
    if 'display_name' in data:
        collection.display_name = data['display_name']
    if 'description' in data:
        collection.description = data['description']
    if 'icon' in data:
        collection.icon = data['icon']
    if 'color' in data:
        collection.color = data['color']
    if 'is_public' in data:
        collection.is_public = data['is_public']
    if 'retrieval_k' in data:
        collection.retrieval_k = data['retrieval_k']

    collection.updated_at = datetime.now()
    db.session.commit()

    # Log activity if fields changed
    if changed_fields:
        ChatbotActivityService.log_collection_updated(
            collection_id=collection_id,
            collection_name=collection.display_name,
            username=username,
            changed_fields=changed_fields
        )

    return jsonify({
        'success': True,
        'message': f"Collection '{collection.display_name}' updated successfully"
    }), 200


@rag_collection_bp.route('/collections/<int:collection_id>', methods=['DELETE'])
@require_permission('feature:rag:delete')
@handle_api_errors(logger_name='rag')
def delete_collection(collection_id):
    """Delete collection with optional cascade delete of documents"""
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    username = AuthUtils.extract_username_without_validation()
    if not RAGAccessService.can_delete_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    # Store info before deletion
    collection_name = collection.display_name

    # Check for force parameter (cascade delete)
    force = request.args.get('force', 'false').lower() == 'true'

    # Check if collection has documents
    doc_count = RAGDocument.query.filter_by(collection_id=collection_id).count()

    if doc_count > 0 and not force:
        raise ValidationError(
            f"Collection enthält {doc_count} Dokument(e). Verwenden Sie 'Inkl. Dokumente löschen' um die Collection mit allen Dokumenten zu löschen.",
            details={'document_count': doc_count}
        )

    # If force delete, remove all documents first
    deleted_doc_ids = []
    if doc_count > 0 and force:
        # Delete all chunks for documents in this collection
        documents = RAGDocument.query.filter_by(collection_id=collection_id).all()
        for doc in documents:
            RAGDocumentChunk.query.filter_by(document_id=doc.id).delete()
            deleted_doc_ids.append(doc.id)

        # Delete all documents
        RAGDocument.query.filter_by(collection_id=collection_id).delete()
        current_app.logger.info(f"Cascade deleted {doc_count} documents from collection {collection_id}")

    # Delete chatbot-collection associations
    ChatbotCollection.query.filter_by(collection_id=collection_id).delete()

    # Delete document-collection links
    CollectionDocumentLink.query.filter_by(collection_id=collection_id).delete()

    # Delete collection embeddings (multi-model records)
    CollectionEmbedding.query.filter_by(collection_id=collection_id).delete()

    db.session.delete(collection)
    db.session.commit()

    try:
        from services.chatbot.lexical_index import LexicalSearchIndex
        for doc_id in deleted_doc_ids:
            LexicalSearchIndex.remove_document(doc_id)
        LexicalSearchIndex.remove_collection(collection_id)
    except Exception as exc:
        current_app.logger.warning(f"[RAG] Lexical index cleanup failed for collection {collection_id}: {exc}")

    # Log activity
    ChatbotActivityService.log_collection_deleted(
        collection_id=collection_id,
        collection_name=collection_name,
        username=username,
        document_count=doc_count,
        force=force
    )

    return jsonify({
        'success': True,
        'message': f"Collection '{collection_name}' erfolgreich gelöscht" + (f" (inkl. {doc_count} Dokumente)" if doc_count > 0 else "")
    }), 200


@rag_collection_bp.route('/collections/<int:collection_id>/access', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_collection_access(collection_id):
    """Get collection access assignments (owner/admin)."""
    username = AuthUtils.extract_username_without_validation()
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    if not RAGAccessService.can_share_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    access = RAGAccessService.get_collection_permissions(collection_id)
    return jsonify({'success': True, 'collection_id': collection_id, **access}), 200


@rag_collection_bp.route('/collections/<int:collection_id>/access', methods=['PUT'])
@require_permission('feature:rag:share')
@handle_api_errors(logger_name='rag')
def set_collection_access(collection_id):
    """Replace collection access assignments (owner/admin)."""
    from socketio_handlers.events_rag import emit_collection_shared

    username = AuthUtils.extract_username_without_validation()
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    if not RAGAccessService.can_share_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    # Get previous users before changing permissions (for WebSocket notification)
    previous_permissions = RAGAccessService.get_collection_permissions(collection_id)
    previous_users = [u['target'] for u in previous_permissions.get('users', [])]

    data = request.get_json() or {}

    # Check if using batch mode (user_permissions with individual access levels)
    user_permissions = data.get('user_permissions')
    if user_permissions is not None:
        # Batch mode - individual permissions per user
        role_names = data.get('role_names') or data.get('roles') or []
        result = RAGAccessService.set_collection_permissions_batch(
            collection_id=collection_id,
            user_permissions=user_permissions,
            role_names=role_names,
            granted_by=username
        )
    else:
        # Legacy mode - same access for all users
        usernames = data.get('usernames') or data.get('users') or []
        role_names = data.get('role_names') or data.get('roles') or []
        access = data.get('access') or {}
        result = RAGAccessService.set_collection_permissions(
            collection_id=collection_id,
            usernames=usernames,
            role_names=role_names,
            granted_by=username,
            access=access
        )

    # Emit WebSocket event for real-time updates (includes removed users)
    emit_collection_shared(collection, result, username, previous_users)

    return jsonify({'success': True, 'collection_id': collection_id, **result}), 200


@rag_collection_bp.route('/collections/<int:collection_id>/access/required', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_collection_required_access(collection_id):
    """Get users/roles who need collection access because of chatbot sharing."""
    username = AuthUtils.extract_username_without_validation()
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    if not RAGAccessService.can_view_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    required = RAGAccessService.get_chatbot_required_access(collection_id)
    return jsonify({'success': True, 'collection_id': collection_id, **required}), 200


# ============================================================================
# Embedding API Endpoints
# ============================================================================

@rag_collection_bp.route('/collections/<int:collection_id>/embed', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def start_collection_embedding(collection_id):
    """
    Start embedding process for a collection.

    All linked documents will be processed and embedded.
    Progress is streamed via WebSocket.
    """
    from services.rag.collection_embedding_service import get_collection_embedding_service

    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    username = AuthUtils.extract_username_without_validation()
    if not RAGAccessService.can_edit_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    service = get_collection_embedding_service()
    result = service.start_embedding(collection_id)

    if result['success']:
        return jsonify(result), 202
    else:
        raise ValidationError(result.get('error', 'Failed to start embedding'))


@rag_collection_bp.route('/collections/<int:collection_id>/embed', methods=['DELETE'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def pause_collection_embedding(collection_id):
    """Pause/Stop embedding process for a collection."""
    from services.rag.collection_embedding_service import get_collection_embedding_service
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    username = AuthUtils.extract_username_without_validation()
    if not RAGAccessService.can_edit_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    service = get_collection_embedding_service()
    result = service.pause_embedding(collection_id)

    if result['success']:
        return jsonify(result), 200
    else:
        raise ValidationError(result.get('error', 'Failed to pause embedding'))


@rag_collection_bp.route('/collections/<int:collection_id>/embed/status', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_collection_embedding_status(collection_id):
    """Get embedding status for a collection."""
    from services.rag.collection_embedding_service import get_collection_embedding_service
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    username = AuthUtils.extract_username_without_validation()
    if not RAGAccessService.can_view_collection(username, collection):
        raise ForbiddenError('Keine Berechtigung für diese Collection')

    service = get_collection_embedding_service()
    result = service.get_status(collection_id)

    if result['success']:
        return jsonify(result), 200
    else:
        raise NotFoundError(result.get('error', 'Embedding status not found'))


@rag_collection_bp.route('/collections/<int:collection_id>/reindex', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def reindex_collection(collection_id):
    """
    Requeue all documents in a collection for reindexing.

    Optional JSON body:
      - pdf_only: bool (default False)
    """
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')
    username = AuthUtils.extract_username_without_validation()

    # Reindex requires explicit access: owner OR explicit share (not just public visibility)
    is_owner = collection.created_by == username
    is_admin = RAGAccessService.is_admin_user(username)
    has_explicit_edit = RAGAccessService._has_collection_permission(username, collection_id, 'edit')

    # Allow if: admin, owner, or (not public AND has explicit edit permission)
    if not (is_admin or is_owner or (not collection.is_public and has_explicit_edit)):
        raise ForbiddenError('Reindexierung nur für eigene oder explizit geteilte Collections erlaubt')

    payload = request.get_json(silent=True) or {}
    pdf_only = bool(payload.get('pdf_only'))

    docs_query = (
        db.session.query(RAGDocument)
        .join(CollectionDocumentLink, CollectionDocumentLink.document_id == RAGDocument.id)
        .filter(CollectionDocumentLink.collection_id == collection_id)
    )
    if pdf_only:
        docs_query = docs_query.filter(RAGDocument.mime_type == 'application/pdf')

    documents = docs_query.all()
    queued = 0
    skipped_processing = 0

    for doc in documents:
        if doc.status == 'processing':
            skipped_processing += 1
            continue

        doc.status = 'pending'
        doc.processing_error = None
        doc.indexed_at = None
        doc.processed_at = None
        doc.chunk_count = 0
        doc.embedding_model = None
        doc.updated_at = datetime.now()

        queue_entry = RAGProcessingQueue.query.filter_by(document_id=doc.id).first()
        if queue_entry:
            queue_entry.status = 'queued'
            queue_entry.progress_percent = 0
            queue_entry.current_step = 'Reindex queued'
            queue_entry.error_message = None
            queue_entry.retry_count = 0
            queue_entry.started_at = None
            queue_entry.completed_at = None
            queue_entry.priority = max(queue_entry.priority or 0, 10)
            queue_entry.updated_at = datetime.now()
        else:
            queue_entry = RAGProcessingQueue(
                document_id=doc.id,
                priority=10,
                status='queued',
                created_at=datetime.now(),
            )
            db.session.add(queue_entry)

        queued += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'queued': queued,
        'skipped_processing': skipped_processing,
        'pdf_only': pdf_only
    }), 202
