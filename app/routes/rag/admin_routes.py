"""
RAG Admin and Maintenance Routes

Provides API endpoints for RAG admin operations and processing queue management.
All routes are protected with appropriate permissions.

Routes:
    Processing Queue:
        GET    /api/rag/processing-queue           - Get processing queue status
        POST   /api/rag/processing-queue/<id>/retry - Retry failed processing
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from decorators.permission_decorator import require_permission
from db.tables import RAGProcessingQueue
from db.db import db
from sqlalchemy import desc

rag_admin_bp = Blueprint('rag_admin', __name__)


# ============================================================================
# PROCESSING QUEUE
# ============================================================================

@rag_admin_bp.route('/processing-queue', methods=['GET'])
@require_permission('feature:rag:view')
def get_processing_queue():
    """Get current processing queue status"""
    try:
        status_filter = request.args.get('status')

        query = RAGProcessingQueue.query
        if status_filter:
            query = query.filter_by(status=status_filter)

        queue_items = query.order_by(
            desc(RAGProcessingQueue.priority),
            RAGProcessingQueue.created_at
        ).all()

        return jsonify({
            'success': True,
            'queue': [{
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
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_processing_queue: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_admin_bp.route('/processing-queue/<int:queue_id>/retry', methods=['POST'])
@require_permission('feature:rag:edit')
def retry_processing(queue_id):
    """Retry failed document processing"""
    try:
        queue_item = RAGProcessingQueue.query.get_or_404(queue_id)

        if queue_item.status != 'failed':
            return jsonify({
                'success': False,
                'error': 'Can only retry failed processing jobs'
            }), 400

        if queue_item.retry_count >= queue_item.max_retries:
            return jsonify({
                'success': False,
                'error': f'Maximum retries ({queue_item.max_retries}) exceeded'
            }), 400

        # Reset for retry
        queue_item.status = 'queued'
        queue_item.retry_count += 1
        queue_item.progress_percent = 0
        queue_item.current_step = None
        queue_item.started_at = None
        queue_item.completed_at = None
        queue_item.updated_at = datetime.now()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Processing retry queued (attempt {queue_item.retry_count}/{queue_item.max_retries})'
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in retry_processing: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
