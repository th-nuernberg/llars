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
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, ForbiddenError
)
from db.tables import RAGProcessingQueue
from db.database import db
from sqlalchemy import desc
from auth.auth_utils import AuthUtils
from services.rag.access_service import RAGAccessService

rag_admin_bp = Blueprint('rag_admin', __name__)


# ============================================================================
# PROCESSING QUEUE
# ============================================================================

@rag_admin_bp.route('/processing-queue', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_processing_queue():
    """Get current processing queue status"""
    status_filter = request.args.get('status')
    username = AuthUtils.extract_username_without_validation()
    query = RAGProcessingQueue.query
    if not RAGAccessService.is_admin_user(username):
        query = query.join(RAGProcessingQueue.document)
        query = RAGAccessService.apply_document_access_filter(query, username, access='view')
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


@rag_admin_bp.route('/processing-queue/<int:queue_id>/retry', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def retry_processing(queue_id):
    """Retry failed document processing"""
    queue_item = RAGProcessingQueue.query.get(queue_id)
    if not queue_item:
        raise NotFoundError(f'Processing queue item with ID {queue_id} not found')
    username = AuthUtils.extract_username_without_validation()
    if not RAGAccessService.can_edit_document(username, queue_item.document):
        raise ForbiddenError('Keine Berechtigung für dieses Dokument')

    if queue_item.status != 'failed':
        raise ValidationError('Can only retry failed processing jobs')

    if queue_item.retry_count >= queue_item.max_retries:
        raise ValidationError(f'Maximum retries ({queue_item.max_retries}) exceeded')

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
