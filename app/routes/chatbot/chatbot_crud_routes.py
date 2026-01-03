# chatbot_crud_routes.py
"""
Chatbot CRUD routes - Create, Read, Update, Delete operations.
"""

import logging
from flask import Blueprint, request, jsonify
from db.tables import Chatbot
from decorators.permission_decorator import require_permission, require_any_permission
from decorators.error_handler import handle_errors
from services.chatbot.chatbot_service import ChatbotService
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.chatbot_activity_service import ChatbotActivityService
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

chatbot_crud_bp = Blueprint('chatbot_crud', __name__)


@chatbot_crud_bp.route('/access/overview', methods=['GET'])
@require_permission('admin:permissions:manage')
@handle_errors(logger_name='chatbot')
def get_chatbot_access_overview():
    """Get an overview of chatbot access assignments (admin only)."""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    query = Chatbot.query
    if not include_inactive:
        query = query.filter(Chatbot.is_active == True)

    bots = query.order_by(Chatbot.created_at.desc()).all()
    chatbots = []
    for bot in bots:
        chatbots.append({
            'id': bot.id,
            'name': bot.name,
            'display_name': bot.display_name,
            'description': bot.description,
            'is_active': bot.is_active,
            'is_public': bot.is_public,
            'created_by': bot.created_by,
            'allowed_usernames': ChatbotAccessService.get_allowed_usernames_for_chatbot(bot.id),
            'allowed_roles': ChatbotAccessService.get_allowed_roles_for_chatbot(bot.id),
        })

    return jsonify({'success': True, 'chatbots': chatbots, 'count': len(chatbots)})


@chatbot_crud_bp.route('/<int:chatbot_id>/access', methods=['GET'])
@require_any_permission('admin:permissions:manage', 'feature:chatbots:share')
@handle_errors(logger_name='chatbot')
def get_chatbot_access(chatbot_id: int):
    """Get allowed usernames for a chatbot (admin only)."""
    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    return jsonify({
        'success': True,
        'chatbot_id': chatbot_id,
        'allowed_usernames': ChatbotAccessService.get_allowed_usernames_for_chatbot(chatbot_id),
        'allowed_roles': ChatbotAccessService.get_allowed_roles_for_chatbot(chatbot_id),
    })


@chatbot_crud_bp.route('/<int:chatbot_id>/access', methods=['PUT'])
@require_any_permission('admin:permissions:manage', 'feature:chatbots:share')
@handle_errors(logger_name='chatbot')
def set_chatbot_access(chatbot_id: int):
    """Replace allowed usernames for a chatbot (admin only)."""
    data = request.get_json() or {}
    usernames = data.get('usernames', data.get('allowed_usernames', [])) or []
    role_names = (
        data.get('role_names')
        or data.get('roles')
        or data.get('allowed_roles')
        or []
    )
    admin_username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(admin_username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    access = ChatbotAccessService.set_chatbot_access(
        chatbot_id=chatbot_id,
        usernames=usernames,
        role_names=role_names,
        granted_by=admin_username,
    )
    return jsonify({
        'success': True,
        'chatbot_id': chatbot_id,
        'allowed_usernames': access.get('allowed_usernames', []),
        'allowed_roles': access.get('allowed_roles', []),
    })


@chatbot_crud_bp.route('', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_chatbots():
    """Get all chatbots"""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    username = AuthUtils.extract_username_without_validation()
    chatbots = ChatbotService.get_all_chatbots(include_inactive=include_inactive, username=username)
    return jsonify({
        'success': True,
        'chatbots': chatbots,
        'count': len(chatbots)
    })


@chatbot_crud_bp.route('/<int:chatbot_id>', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_chatbot(chatbot_id):
    """Get a single chatbot by ID"""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    chatbot = ChatbotService.get_chatbot(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    return jsonify({'success': True, 'chatbot': chatbot})


@chatbot_crud_bp.route('', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def create_chatbot():
    """Create a new chatbot"""
    data = request.get_json()
    if not data:
        raise ValueError('No data provided')

    username = AuthUtils.extract_username_without_validation() or 'unknown'
    chatbot = ChatbotService.create_chatbot(data, username)

    # Log activity
    ChatbotActivityService.log_chatbot_created(
        chatbot_id=chatbot['id'],
        chatbot_name=chatbot.get('name', ''),
        display_name=chatbot['display_name'],
        username=username,
        via_wizard=False
    )

    return jsonify({
        'success': True,
        'chatbot': chatbot,
        'message': f"Chatbot '{chatbot['display_name']}' created successfully"
    }), 201


@chatbot_crud_bp.route('/<int:chatbot_id>', methods=['PUT'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def update_chatbot(chatbot_id):
    """Update an existing chatbot"""
    data = request.get_json()
    if not data:
        raise ValueError('No data provided')

    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    # Track which fields are changing
    original_name = chatbot.display_name
    trackable_fields = ['name', 'display_name', 'description', 'icon', 'color',
                        'system_prompt', 'model_name', 'temperature', 'max_tokens',
                        'welcome_message', 'fallback_message', 'is_active', 'is_public']
    changed_fields = {}
    for field in trackable_fields:
        if field in data:
            old_val = getattr(chatbot, field, None)
            new_val = data[field]
            if old_val != new_val:
                changed_fields[field] = {'old': old_val, 'new': new_val}

    updated_chatbot = ChatbotService.update_chatbot(chatbot_id, data)
    if not updated_chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

    # Log activity if fields changed
    if changed_fields:
        ChatbotActivityService.log_chatbot_updated(
            chatbot_id=chatbot_id,
            chatbot_name=updated_chatbot.get('display_name', original_name),
            username=username,
            changed_fields=changed_fields
        )

    return jsonify({
        'success': True,
        'chatbot': updated_chatbot,
        'message': 'Chatbot updated successfully'
    })


@chatbot_crud_bp.route('/<int:chatbot_id>', methods=['DELETE'])
@require_permission('feature:chatbots:delete')
@handle_errors(logger_name='chatbot')
def delete_chatbot(chatbot_id):
    """Delete a chatbot"""
    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    # Store info before deletion
    chatbot_name = chatbot.display_name
    delete_collections = request.args.get('delete_collections', 'false').lower() == 'true'

    success = ChatbotService.delete_chatbot(chatbot_id, delete_collections=delete_collections)
    if not success:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

    # Log activity
    ChatbotActivityService.log_chatbot_deleted(
        chatbot_id=chatbot_id,
        chatbot_name=chatbot_name,
        username=username,
        with_collections=delete_collections
    )

    return jsonify({
        'success': True,
        'message': 'Chatbot deleted successfully',
        'delete_collections': delete_collections
    })


@chatbot_crud_bp.route('/<int:chatbot_id>/duplicate', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def duplicate_chatbot(chatbot_id):
    """Duplicate a chatbot"""
    username = AuthUtils.extract_username_without_validation() or 'unknown'
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    new_chatbot = ChatbotService.duplicate_chatbot(chatbot_id, username)
    if not new_chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

    # Log activity
    ChatbotActivityService.log_chatbot_duplicated(
        source_chatbot_id=chatbot_id,
        new_chatbot_id=new_chatbot['id'],
        new_name=new_chatbot['display_name'],
        username=username
    )

    return jsonify({
        'success': True,
        'chatbot': new_chatbot,
        'message': f"Chatbot duplicated as '{new_chatbot['display_name']}'"
    }), 201
