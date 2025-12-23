"""
RAG Search and Statistics Routes

Provides API endpoints for RAG search, retrieval, and statistics.
All routes are protected with appropriate permissions.

Routes:
    Statistics:
        GET    /api/rag/stats                      - System overview stats
        GET    /api/rag/stats/overview             - System overview stats (alias)
        GET    /api/rag/stats/popular-documents    - Most retrieved documents
        GET    /api/rag/stats/popular-queries      - Most common queries

    Embedding Info:
        GET    /api/rag/embedding-info             - Get embedding model info
"""

from flask import Blueprint, request, jsonify, current_app
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from auth.auth_utils import AuthUtils
from services.rag.access_service import RAGAccessService
from db.tables import RAGCollection, RAGDocument, RAGRetrievalLog
from db.db import db
from sqlalchemy import func, desc, select

rag_search_bp = Blueprint('rag_search', __name__)


# ============================================================================
# STATISTICS & ANALYTICS
# ============================================================================

@rag_search_bp.route('/stats', methods=['GET'])
@rag_search_bp.route('/stats/overview', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_stats_overview():
    """Get system-wide RAG statistics"""
    username = AuthUtils.extract_username_without_validation()
    collections_query = RAGCollection.query.filter_by(is_active=True)
    collections_query = RAGAccessService.apply_collection_view_filter(collections_query, username)
    total_collections = collections_query.count()

    # Document stats
    documents_query = RAGAccessService.apply_document_access_filter(RAGDocument.query, username, access='view')
    total_documents = documents_query.count()
    documents_by_status = (
        documents_query
        .with_entities(RAGDocument.status, func.count(RAGDocument.id))
        .group_by(RAGDocument.status)
        .all()
    )

    total_size_bytes = (
        documents_query
        .with_entities(func.sum(RAGDocument.file_size_bytes))
        .scalar() or 0
    )

    total_chunks = (
        documents_query
        .with_entities(func.sum(RAGDocument.chunk_count))
        .scalar() or 0
    )

    # Retrieval stats
    total_retrievals = (
        documents_query
        .with_entities(func.sum(RAGDocument.retrieval_count))
        .scalar() or 0
    )

    accessible_collection_ids = collections_query.with_entities(RAGCollection.id).subquery()
    total_queries = (
        db.session.query(func.count(RAGRetrievalLog.id))
        .filter(RAGRetrievalLog.collection_id.in_(select(accessible_collection_ids.c.id)))
        .scalar() or 0
    )

    # Recent activity
    recent_uploads = documents_query.order_by(
        desc(RAGDocument.uploaded_at)
    ).limit(5).all()

    return jsonify({
        'success': True,
        'stats': {
            'collections': {
                'total': total_collections
            },
            'documents': {
                'total': total_documents,
                'by_status': {status: count for status, count in documents_by_status},
                'total_size_bytes': total_size_bytes,
                'total_size_mb': round(total_size_bytes / (1024*1024), 2),
                'total_chunks': total_chunks
            },
            'retrieval': {
                'total_retrievals': total_retrievals,
                'total_queries': total_queries,
                'avg_retrievals_per_document': round(total_retrievals / total_documents, 2) if total_documents > 0 else 0
            },
            'recent_uploads': [{
                'id': d.id,
                'filename': d.filename,
                'title': d.title,
                'uploaded_at': d.uploaded_at.isoformat() if d.uploaded_at else None,
                'file_size_mb': round(d.file_size_bytes / (1024*1024), 2)
            } for d in recent_uploads]
        }
    }), 200


@rag_search_bp.route('/stats/popular-documents', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_popular_documents():
    """Get most frequently retrieved documents"""
    limit = request.args.get('limit', 10, type=int)
    username = AuthUtils.extract_username_without_validation()
    documents_query = RAGAccessService.apply_document_access_filter(
        RAGDocument.query, username, access='view'
    )
    documents = documents_query.filter(
        RAGDocument.retrieval_count > 0
    ).order_by(
        desc(RAGDocument.retrieval_count)
    ).limit(limit).all()

    return jsonify({
        'success': True,
        'documents': [{
            'id': d.id,
            'filename': d.filename,
            'title': d.title,
            'collection_name': d.collection.display_name if d.collection else None,
            'retrieval_count': d.retrieval_count,
            'avg_relevance_score': d.avg_relevance_score,
            'last_retrieved_at': d.last_retrieved_at.isoformat() if d.last_retrieved_at else None
        } for d in documents]
    }), 200


@rag_search_bp.route('/stats/popular-queries', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_popular_queries():
    """Get most common search queries"""
    limit = request.args.get('limit', 10, type=int)
    username = AuthUtils.extract_username_without_validation()
    collections_query = RAGCollection.query.filter_by(is_active=True)
    collections_query = RAGAccessService.apply_collection_view_filter(collections_query, username)
    accessible_collection_ids = collections_query.with_entities(RAGCollection.id).subquery()

    queries = db.session.query(
        RAGRetrievalLog.query_hash,
        func.max(RAGRetrievalLog.query_text).label('query_text'),
        func.count(RAGRetrievalLog.id).label('count'),
        func.avg(RAGRetrievalLog.retrieval_time_ms).label('avg_time_ms')
    ).filter(
        RAGRetrievalLog.collection_id.in_(select(accessible_collection_ids.c.id))
    ).group_by(
        RAGRetrievalLog.query_hash
    ).order_by(
        desc('count')
    ).limit(limit).all()

    return jsonify({
        'success': True,
        'queries': [{
            'query_text': q.query_text,
            'count': q.count,
            'avg_time_ms': round(q.avg_time_ms, 2) if q.avg_time_ms else None
        } for q in queries]
    }), 200


# ============================================================================
# EMBEDDING MODEL INFO
# ============================================================================

@rag_search_bp.route('/embedding-info', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_embedding_info():
    """
    Get information about the current embedding model configuration.

    Returns details about:
    - Active embedding model (LiteLLM or HuggingFace fallback)
    - Model dimensions
    - Configuration status
    - Vectorstore paths
    """
    from rag_pipeline import RAGPipeline

    # Create a temporary pipeline instance to get embedding info
    # Note: This doesn't re-initialize embeddings if already cached
    pipeline = RAGPipeline()
    embedding_info = pipeline.get_embedding_info()

    return jsonify({
        'success': True,
        'embedding': embedding_info
    }), 200
