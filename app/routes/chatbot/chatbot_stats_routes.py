# chatbot_stats_routes.py
"""
Chatbot statistics routes.
"""

import logging
from flask import Blueprint, jsonify
from db.tables import Chatbot, ChatbotConversation, ChatbotMessage
from db.database import db
from sqlalchemy import func
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_errors
from services.chatbot.chatbot_service import ChatbotService
from services.chatbot.chatbot_access_service import ChatbotAccessService
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

chatbot_stats_bp = Blueprint('chatbot_stats', __name__)


@chatbot_stats_bp.route('/stats/overview', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_overview_stats():
    """Get global chatbot statistics"""
    username = AuthUtils.extract_username_without_validation()
    if ChatbotAccessService.is_admin_user(username):
        stats = ChatbotService.get_overview_stats()
    else:
        owned = ChatbotAccessService.get_owned_chatbots(username)
        owned_ids = [bot.id for bot in owned]
        if not owned_ids:
            stats = {
                'total_chatbots': 0,
                'active_chatbots': 0,
                'total_conversations': 0,
                'total_messages': 0,
                'top_chatbots': []
            }
        else:
            active_chatbots = Chatbot.query.filter(
                Chatbot.id.in_(owned_ids),
                Chatbot.is_active == True
            ).count()
            total_conversations = ChatbotConversation.query.filter(
                ChatbotConversation.chatbot_id.in_(owned_ids)
            ).count()
            total_messages = db.session.query(func.count(ChatbotMessage.id)).join(
                ChatbotConversation
            ).filter(ChatbotConversation.chatbot_id.in_(owned_ids)).scalar() or 0
            top_chatbots = db.session.query(
                Chatbot.id,
                Chatbot.display_name,
                func.count(ChatbotConversation.id).label('conv_count')
            ).outerjoin(ChatbotConversation).filter(
                Chatbot.id.in_(owned_ids)
            ).group_by(Chatbot.id).order_by(
                func.count(ChatbotConversation.id).desc()
            ).limit(5).all()
            stats = {
                'total_chatbots': len(owned_ids),
                'active_chatbots': active_chatbots,
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'top_chatbots': [
                    {'id': t[0], 'name': t[1], 'conversations': t[2]}
                    for t in top_chatbots
                ]
            }
    return jsonify({'success': True, 'stats': stats})


@chatbot_stats_bp.route('/<int:chatbot_id>/stats', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_chatbot_stats(chatbot_id):
    """Get statistics for a specific chatbot"""
    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    stats = ChatbotService.get_stats(chatbot_id)
    if not stats:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    return jsonify({'success': True, 'stats': stats})
