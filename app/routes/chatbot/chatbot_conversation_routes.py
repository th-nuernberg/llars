# chatbot_conversation_routes.py
"""
Chatbot conversation routes - conversation management and message rating.
"""

import logging
from flask import Blueprint, request, jsonify
from db.tables import Chatbot, ChatbotConversation
from db.db import db
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_errors
from services.chatbot.chat_service import ChatService
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.chatbot_activity_service import ChatbotActivityService
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

chatbot_conversation_bp = Blueprint('chatbot_conversation', __name__)


@chatbot_conversation_bp.route('/<int:chatbot_id>/conversations', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_conversations(chatbot_id):
    """Get conversations for a chatbot (filtered by current user for data isolation)"""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    limit = request.args.get('limit', 50, type=int)
    # SECURITY: Filter by username to ensure users only see their own conversations
    conversations = ChatService.get_conversations(chatbot_id, username=username, limit=limit)
    return jsonify({
        'success': True,
        'conversations': conversations,
        'count': len(conversations)
    })


@chatbot_conversation_bp.route('/<int:chatbot_id>/conversations', methods=['POST'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def create_conversation(chatbot_id):
    """Create a new conversation for a chatbot (scoped to current user)."""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    title = data.get('title')
    session_id = data.get('session_id')

    convo = ChatService.create_conversation(
        chatbot_id=chatbot_id,
        username=username,
        title=title,
        session_id=session_id
    )

    # Log activity - get chatbot name for better logging
    chatbot = Chatbot.query.get(chatbot_id)
    chatbot_name = chatbot.display_name if chatbot else f"Chatbot #{chatbot_id}"
    ChatbotActivityService.log_chat_created(
        conversation_id=convo['id'],
        chatbot_id=chatbot_id,
        chatbot_name=chatbot_name,
        username=username
    )

    return jsonify({'success': True, 'conversation': convo}), 201


@chatbot_conversation_bp.route('/<int:chatbot_id>/conversations/<int:conversation_id>', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_conversation(chatbot_id, conversation_id):
    """Get a single conversation with all messages (ownership verified)"""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    # SECURITY: Verify user owns this conversation
    conversation = ChatService.get_conversation(conversation_id, username=username, chatbot_id=chatbot_id)
    if not conversation or conversation['chatbot_id'] != chatbot_id:
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404
    return jsonify({'success': True, 'conversation': conversation})


@chatbot_conversation_bp.route('/<int:chatbot_id>/conversations/<int:conversation_id>', methods=['PATCH'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def update_conversation(chatbot_id, conversation_id):
    """Update a conversation (title / active flag) scoped to current user."""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    convo = ChatbotConversation.query.filter_by(id=conversation_id, chatbot_id=chatbot_id).first()
    if not convo or (convo.username and convo.username != username):
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404

    updated = False
    if 'title' in data:
        convo.title = data.get('title')
        updated = True
    if 'is_active' in data:
        convo.is_active = bool(data.get('is_active'))
        updated = True

    if updated:
        db.session.commit()

    return jsonify({'success': True, 'conversation': {
        'id': convo.id,
        'session_id': convo.session_id,
        'chatbot_id': convo.chatbot_id,
        'username': convo.username,
        'title': convo.title,
        'message_count': convo.message_count,
        'is_active': convo.is_active,
        'started_at': convo.started_at.isoformat() if convo.started_at else None,
        'last_message_at': convo.last_message_at.isoformat() if convo.last_message_at else None,
    }})


@chatbot_conversation_bp.route('/<int:chatbot_id>/conversations/<int:conversation_id>', methods=['DELETE'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def delete_conversation(chatbot_id, conversation_id):
    """Delete a conversation (ownership verified)"""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    # SECURITY: Verify user owns this conversation before getting details
    conversation = ChatService.get_conversation(conversation_id, username=username, chatbot_id=chatbot_id)
    if not conversation or conversation['chatbot_id'] != chatbot_id:
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404

    # Store info before deletion
    message_count = conversation.get('message_count', 0)
    chatbot = Chatbot.query.get(chatbot_id)
    chatbot_name = chatbot.display_name if chatbot else f"Chatbot #{chatbot_id}"

    # SECURITY: Pass username to ensure ownership is verified
    success = ChatService.delete_conversation(conversation_id, username=username)
    if not success:
        return jsonify({'success': False, 'error': 'Failed to delete conversation'}), 500

    # Log activity
    ChatbotActivityService.log_chat_deleted(
        conversation_id=conversation_id,
        chatbot_id=chatbot_id,
        chatbot_name=chatbot_name,
        username=username,
        message_count=message_count
    )

    return jsonify({'success': True, 'message': 'Conversation deleted successfully'})


@chatbot_conversation_bp.route('/messages/<int:message_id>/rate', methods=['POST'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def rate_message(message_id):
    """Rate a message"""
    data = request.get_json()
    if not data or 'rating' not in data:
        raise ValueError('rating is required')

    rating = data['rating']
    if rating not in ['helpful', 'not_helpful', 'incorrect']:
        raise ValueError('Invalid rating')

    success = ChatService.rate_message(
        message_id=message_id,
        rating=rating,
        feedback=data.get('feedback')
    )

    if not success:
        return jsonify({'success': False, 'error': 'Message not found'}), 404
    return jsonify({'success': True, 'message': 'Rating saved'})
