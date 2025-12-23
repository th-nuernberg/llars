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
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from db.tables import RAGCollection, RAGDocument, RAGDocumentChunk, CollectionDocumentLink, ChatbotCollection
from db.models.llm_model import LLMModel
from db.db import db
from sqlalchemy import desc
from auth.auth_utils import AuthUtils

rag_collection_bp = Blueprint('rag_collection', __name__)


@rag_collection_bp.route('/collections', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_collections():
    """Get all RAG collections with statistics"""
    collections = RAGCollection.query.filter_by(is_active=True).all()

    result = []
    for c in collections:
        # Count linked documents via CollectionDocumentLink (n:m relationship)
        link_count = CollectionDocumentLink.query.filter_by(collection_id=c.id).count()

        # Count by link type
        new_docs = CollectionDocumentLink.query.filter_by(collection_id=c.id, link_type='new').count()
        linked_docs = CollectionDocumentLink.query.filter_by(collection_id=c.id, link_type='linked').count()

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
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'last_indexed_at': c.last_indexed_at.isoformat() if c.last_indexed_at else None,
            # Embedding status fields (for Chatbot Builder)
            'source_type': c.source_type,
            'source_url': c.source_url,
            'embedding_status': c.embedding_status,
            'embedding_progress': c.embedding_progress or 0,
            'embedding_error': c.embedding_error
        })

    return jsonify({
        'success': True,
        'collections': result
    }), 200


@rag_collection_bp.route('/collections/<int:collection_id>', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_collection(collection_id):
    """Get detailed collection information with linked documents"""
    collection = RAGCollection.query.get(collection_id)
    if not collection:
        raise NotFoundError(f'Collection with ID {collection_id} not found')

    # Get documents via CollectionDocumentLink (n:m relationship)
    links = CollectionDocumentLink.query.filter_by(
        collection_id=collection_id
    ).order_by(desc(CollectionDocumentLink.linked_at)).all()

    # Build document list with link info
    documents_list = []
    for link in links:
        doc = link.document
        if doc:
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
            'created_at': collection.created_at.isoformat() if collection.created_at else None,
            'last_indexed_at': collection.last_indexed_at.isoformat() if collection.last_indexed_at else None,
            'documents': documents_list
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
        chunk_size=data.get('chunk_size', 1000),
        chunk_overlap=data.get('chunk_overlap', 200),
        retrieval_k=data.get('retrieval_k', 4),
        is_public=data.get('is_public', True),
        created_by=username
    )

    db.session.add(collection)
    db.session.commit()

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

    data = request.get_json()

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
    if doc_count > 0 and force:
        # Delete all chunks for documents in this collection
        documents = RAGDocument.query.filter_by(collection_id=collection_id).all()
        for doc in documents:
            RAGDocumentChunk.query.filter_by(document_id=doc.id).delete()

        # Delete all documents
        RAGDocument.query.filter_by(collection_id=collection_id).delete()
        current_app.logger.info(f"Cascade deleted {doc_count} documents from collection {collection_id}")

    # Delete chatbot-collection associations
    ChatbotCollection.query.filter_by(collection_id=collection_id).delete()

    # Delete document-collection links
    CollectionDocumentLink.query.filter_by(collection_id=collection_id).delete()

    db.session.delete(collection)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f"Collection '{collection.display_name}' erfolgreich gelöscht" + (f" (inkl. {doc_count} Dokumente)" if doc_count > 0 else "")
    }), 200


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

    service = get_collection_embedding_service()
    result = service.get_status(collection_id)

    if result['success']:
        return jsonify(result), 200
    else:
        raise NotFoundError(result.get('error', 'Embedding status not found'))
