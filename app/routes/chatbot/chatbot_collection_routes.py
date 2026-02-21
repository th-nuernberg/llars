# chatbot_collection_routes.py
"""
Chatbot collection assignment routes.
"""

import logging
from flask import Blueprint, request, jsonify
from db.tables import Chatbot, RAGCollection
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_errors
from services.chatbot.chatbot_service import ChatbotService
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.rag.document_service import DocumentService
from services.rag.access_service import RAGAccessService
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

chatbot_collection_bp = Blueprint('chatbot_collection', __name__)


@chatbot_collection_bp.route('/<int:chatbot_id>/collections', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_chatbot_collections(chatbot_id):
    """Get all collections assigned to a chatbot"""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    collections = ChatbotService.get_collections(chatbot_id)
    return jsonify({
        'success': True,
        'collections': collections,
        'count': len(collections)
    })


@chatbot_collection_bp.route('/<int:chatbot_id>/wizard/collection-documents', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_wizard_collection_documents(chatbot_id):
    """List documents for the wizard's primary collection (for live preview during crawling/embedding)."""
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    if not chatbot.primary_collection_id:
        return jsonify({'success': True, 'documents': [], 'collection_id': None})

    per_page = request.args.get('per_page', 25, type=int)
    documents, _ = DocumentService.get_documents(
        collection_id=chatbot.primary_collection_id,
        page=1,
        per_page=per_page,
        username=username
    )

    return jsonify({
        'success': True,
        'collection_id': chatbot.primary_collection_id,
        'documents': [DocumentService.serialize_document(d) for d in documents]
    })


@chatbot_collection_bp.route('/<int:chatbot_id>/collections', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def assign_collection(chatbot_id):
    """Assign a collection to a chatbot"""
    data = request.get_json()
    if not data or 'collection_id' not in data:
        raise ValueError('collection_id is required')

    username = AuthUtils.extract_username_without_validation() or 'unknown'
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    collection = RAGCollection.query.get(data['collection_id'])
    if not collection:
        return jsonify({'success': False, 'error': 'Collection not found'}), 404
    if not RAGAccessService.can_edit_collection(username, collection):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    assignment = ChatbotService.assign_collection(
        chatbot_id=chatbot_id,
        collection_id=data['collection_id'],
        username=username,
        priority=data.get('priority', 0),
        weight=data.get('weight', 1.0),
        is_primary=data.get('is_primary', False)
    )

    if not assignment:
        return jsonify({'success': False, 'error': 'Chatbot or collection not found'}), 404

    return jsonify({
        'success': True,
        'assignment': assignment,
        'message': 'Collection assigned successfully'
    }), 201


@chatbot_collection_bp.route('/<int:chatbot_id>/collections/<int:collection_id>', methods=['PUT'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def update_collection_assignment(chatbot_id, collection_id):
    """Update a collection assignment (priority, weight)"""
    data = request.get_json()
    if not data:
        raise ValueError('No data provided')

    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    assignment = ChatbotService.update_collection_assignment(
        chatbot_id=chatbot_id,
        collection_id=collection_id,
        priority=data.get('priority'),
        weight=data.get('weight'),
        is_primary=data.get('is_primary')
    )

    if not assignment:
        return jsonify({'success': False, 'error': 'Assignment not found'}), 404

    return jsonify({
        'success': True,
        'assignment': assignment,
        'message': 'Assignment updated successfully'
    })


@chatbot_collection_bp.route('/<int:chatbot_id>/collections/<int:collection_id>', methods=['DELETE'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def remove_collection(chatbot_id, collection_id):
    """Remove a collection from a chatbot"""
    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    success = ChatbotService.remove_collection(chatbot_id, collection_id)
    if not success:
        return jsonify({'success': False, 'error': 'Assignment not found'}), 404
    return jsonify({'success': True, 'message': 'Collection removed from chatbot'})
