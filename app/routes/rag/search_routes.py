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
from db.tables import RAGCollection, RAGDocument, RAGRetrievalLog
from db.db import db
from sqlalchemy import func, desc

rag_search_bp = Blueprint('rag_search', __name__)


# ============================================================================
# STATISTICS & ANALYTICS
# ============================================================================

@rag_search_bp.route('/stats', methods=['GET'])
@rag_search_bp.route('/stats/overview', methods=['GET'])
@require_permission('feature:rag:view')
def get_stats_overview():
    """Get system-wide RAG statistics"""
    try:
        # Collection stats
        total_collections = RAGCollection.query.filter_by(is_active=True).count()

        # Document stats
        total_documents = RAGDocument.query.count()
        documents_by_status = db.session.query(
            RAGDocument.status,
            func.count(RAGDocument.id)
        ).group_by(RAGDocument.status).all()

        total_size_bytes = db.session.query(
            func.sum(RAGDocument.file_size_bytes)
        ).scalar() or 0

        total_chunks = db.session.query(
            func.sum(RAGDocument.chunk_count)
        ).scalar() or 0

        # Retrieval stats
        total_retrievals = db.session.query(
            func.sum(RAGDocument.retrieval_count)
        ).scalar() or 0

        total_queries = RAGRetrievalLog.query.count()

        # Recent activity
        recent_uploads = RAGDocument.query.order_by(
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

    except Exception as e:
        current_app.logger.error(f"Error in get_stats_overview: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_search_bp.route('/stats/popular-documents', methods=['GET'])
@require_permission('feature:rag:view')
def get_popular_documents():
    """Get most frequently retrieved documents"""
    try:
        limit = request.args.get('limit', 10, type=int)

        documents = RAGDocument.query.filter(
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

    except Exception as e:
        current_app.logger.error(f"Error in get_popular_documents: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_search_bp.route('/stats/popular-queries', methods=['GET'])
@require_permission('feature:rag:view')
def get_popular_queries():
    """Get most common search queries"""
    try:
        limit = request.args.get('limit', 10, type=int)

        queries = db.session.query(
            RAGRetrievalLog.query_hash,
            func.max(RAGRetrievalLog.query_text).label('query_text'),
            func.count(RAGRetrievalLog.id).label('count'),
            func.avg(RAGRetrievalLog.retrieval_time_ms).label('avg_time_ms')
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

    except Exception as e:
        current_app.logger.error(f"Error in get_popular_queries: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# EMBEDDING MODEL INFO
# ============================================================================

@rag_search_bp.route('/embedding-info', methods=['GET'])
@require_permission('feature:rag:view')
def get_embedding_info():
    """
    Get information about the current embedding model configuration.

    Returns details about:
    - Active embedding model (LiteLLM or HuggingFace fallback)
    - Model dimensions
    - Configuration status
    - Vectorstore paths
    """
    try:
        from rag_pipeline import RAGPipeline

        # Create a temporary pipeline instance to get embedding info
        # Note: This doesn't re-initialize embeddings if already cached
        pipeline = RAGPipeline()
        embedding_info = pipeline.get_embedding_info()

        return jsonify({
            'success': True,
            'embedding': embedding_info
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_embedding_info: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'embedding': {
                'model_name': 'Unknown',
                'model_type': 'error',
                'dimensions': 0,
                'is_primary': False,
                'error_message': str(e)
            }
        }), 500
