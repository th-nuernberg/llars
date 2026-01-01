# chatbot_routes.py
"""
API routes for chatbot management and chat functionality.
"""

import uuid
import logging
import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from db.tables import Chatbot, ChatbotConversation, ChatbotMessage, RAGCollection
from db.db import db
from sqlalchemy import func
from services.rag.document_service import DocumentService
from decorators.permission_decorator import require_permission, require_any_permission
from decorators.error_handler import handle_errors
from services.chatbot.chatbot_service import ChatbotService
from services.chatbot.chat_service import ChatService
from services.chatbot.agent_chat_service import AgentChatService
from services.chatbot.file_processor import file_processor, FileProcessor
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.rag.access_service import RAGAccessService
from services.chatbot_activity_service import ChatbotActivityService
from services.system_settings_service import get_default_max_pages, get_default_max_depth
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

# Max file upload size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

chatbot_blueprint = Blueprint('chatbot', __name__, url_prefix='/api/chatbots')


# ============================================================================
# CHATBOT CRUD ROUTES
# ============================================================================

@chatbot_blueprint.route('/access/overview', methods=['GET'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/access', methods=['GET'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/access', methods=['PUT'])
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


@chatbot_blueprint.route('', methods=['GET'])
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


@chatbot_blueprint.route('/<int:chatbot_id>', methods=['GET'])
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


@chatbot_blueprint.route('', methods=['POST'])
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


@chatbot_blueprint.route('/<int:chatbot_id>', methods=['PUT'])
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


@chatbot_blueprint.route('/<int:chatbot_id>', methods=['DELETE'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/duplicate', methods=['POST'])
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


# ============================================================================
# COLLECTION ASSIGNMENT ROUTES
# ============================================================================

@chatbot_blueprint.route('/<int:chatbot_id>/collections', methods=['GET'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/wizard/collection-documents', methods=['GET'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/collections', methods=['POST'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/collections/<int:collection_id>', methods=['PUT'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/collections/<int:collection_id>', methods=['DELETE'])
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


# ============================================================================
# CHAT ROUTES
# ============================================================================

@chatbot_blueprint.route('/<int:chatbot_id>/chat', methods=['POST'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def chat(chatbot_id):
    """Send a message to a chatbot and get a response (supports file uploads)"""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    # Handle both JSON and multipart form data
    if request.content_type and 'multipart/form-data' in request.content_type:
        # File upload via form data
        message = request.form.get('message', '')
        session_id = request.form.get('session_id', str(uuid.uuid4()))
        include_sources = request.form.get('include_sources', 'true').lower() == 'true'
        conversation_id = request.form.get('conversation_id', type=int)

        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

        # Process uploaded files
        processed_files = []
        files = request.files.getlist('files')

        for file in files:
            if file and file.filename:
                # Check file size
                file.seek(0, 2)  # Seek to end
                size = file.tell()
                file.seek(0)  # Reset

                if size > MAX_FILE_SIZE:
                    raise ValueError(f'File {file.filename} exceeds max size of 10MB')

                if not file_processor.is_supported(file.filename):
                    raise ValueError(f'Unsupported file type: {file.filename}')

                # Read and process file
                file_data = file.read()
                processed = file_processor.process_file(file_data, file.filename, model_name=chatbot.model_name)
                processed_files.append(processed)
    else:
        # Regular JSON request
        data = request.get_json()
        if not data:
            raise ValueError('No data provided')

        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        include_sources = data.get('include_sources', True)
        conversation_id = data.get('conversation_id')
        processed_files = None

    if not message.strip() and not processed_files:
        raise ValueError('message or files required')

    # Prefer agent mode for text-only REST fallback; files stay on standard chat
    if not processed_files:
        agent_service = AgentChatService(chatbot_id)
        if agent_service.get_agent_mode() != 'standard':
            result = agent_service.chat_agent_sync(
                message=message,
                session_id=session_id,
                username=username,
                include_sources=include_sources,
                files=processed_files,
                conversation_id=conversation_id
            )
            return jsonify({'success': True, **result})

    chat_service = ChatService(chatbot_id)
    result = chat_service.chat(
        message=message,
        session_id=session_id,
        username=username,
        include_sources=include_sources,
        files=processed_files,
        conversation_id=conversation_id
    )
    return jsonify({'success': True, **result})


@chatbot_blueprint.route('/<int:chatbot_id>/capabilities', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_capabilities(chatbot_id):
    """Get chatbot capabilities including vision support"""
    username = AuthUtils.extract_username_without_validation()
    if not ChatbotAccessService.user_can_access_chatbot_id(username, chatbot_id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    chat_service = ChatService(chatbot_id)
    return jsonify({
        'success': True,
        'capabilities': {
            'vision': chat_service.supports_vision(),
            'rag': chat_service.chatbot.rag_enabled,
            'supported_file_types': {
                'images': list(FileProcessor.SUPPORTED_IMAGES) if chat_service.supports_vision() else [],
                'documents': list(FileProcessor.SUPPORTED_DOCUMENTS)
            }
        }
    })


@chatbot_blueprint.route('/<int:chatbot_id>/test', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def test_chat(chatbot_id):
    """Test a chatbot without saving the conversation"""
    from flask import Response, stream_with_context
    data = request.get_json()
    if not data or 'message' not in data:
        raise ValueError('message is required')

    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    stream = bool(data.get('stream'))
    chat_service = ChatService(chatbot_id)
    if not stream:
        result = chat_service.test_chat(data['message'])
        return jsonify({'success': True, **result})

    def event_stream():
        try:
            for chunk in chat_service.test_chat_stream(data['message']):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"[ChatbotTest] Streaming failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    response = Response(stream_with_context(event_stream()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


# ============================================================================
# CONVERSATION ROUTES
# ============================================================================

@chatbot_blueprint.route('/<int:chatbot_id>/conversations', methods=['GET'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/conversations', methods=['POST'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/conversations/<int:conversation_id>', methods=['GET'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/conversations/<int:conversation_id>', methods=['PATCH'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/conversations/<int:conversation_id>', methods=['DELETE'])
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


@chatbot_blueprint.route('/messages/<int:message_id>/rate', methods=['POST'])
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


# ============================================================================
# STATISTICS ROUTES
# ============================================================================

@chatbot_blueprint.route('/stats/overview', methods=['GET'])
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


@chatbot_blueprint.route('/<int:chatbot_id>/stats', methods=['GET'])
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


# ============================================================================
# CHATBOT BUILDER WIZARD ROUTES
# ============================================================================

@chatbot_blueprint.route('/wizard/sessions', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_wizard_sessions():
    """Get all active wizard sessions for the current user."""
    from services.wizard import get_wizard_session_service
    from auth.decorators import get_or_create_user

    username = AuthUtils.extract_username_without_validation()
    user = get_or_create_user(username)

    service = get_wizard_session_service()
    sessions = service.get_user_sessions(user.id)

    return jsonify({
        'success': True,
        'sessions': sessions,
        'count': len(sessions)
    })


@chatbot_blueprint.route('/wizard/sessions/<int:chatbot_id>/join', methods=['POST'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def join_wizard_session(chatbot_id):
    """Join/resume a wizard session. Returns full state."""
    from services.wizard import get_wizard_session_service
    from auth.decorators import get_or_create_user
    from datetime import datetime

    username = AuthUtils.extract_username_without_validation()
    user = get_or_create_user(username)

    service = get_wizard_session_service()
    session = service.get_session(chatbot_id)

    if not session:
        return jsonify({'success': False, 'error': 'Wizard session not found'}), 404

    # Access check
    if session.get('user_id') != user.id:
        return jsonify({'success': False, 'error': 'Not your session'}), 403

    # Update activity
    service.update_session(chatbot_id, {
        'last_activity_at': datetime.utcnow().isoformat()
    })

    # Get progress and elapsed time
    progress = service.get_progress(chatbot_id)
    elapsed = service.get_elapsed_time(chatbot_id)

    return jsonify({
        'success': True,
        'session': session,
        'progress': progress,
        'elapsed_time': elapsed,
        'server_time': datetime.utcnow().isoformat()
    })


@chatbot_blueprint.route('/wizard/sessions/<int:chatbot_id>/data', methods=['PATCH'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def update_wizard_session_data(chatbot_id):
    """Update wizard configuration data (name, systemPrompt, etc.)."""
    from services.wizard import get_wizard_session_service
    from auth.decorators import get_or_create_user

    username = AuthUtils.extract_username_without_validation()
    user = get_or_create_user(username)

    service = get_wizard_session_service()
    session = service.get_session(chatbot_id)

    if not session:
        return jsonify({'success': False, 'error': 'Wizard session not found'}), 404

    if session.get('user_id') != user.id:
        return jsonify({'success': False, 'error': 'Not your session'}), 403

    data = request.get_json() or {}
    success = service.update_wizard_data(chatbot_id, data)

    return jsonify({'success': success})


@chatbot_blueprint.route('/wizard', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def create_wizard_chatbot():
    """Start the chatbot creation wizard with a URL."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    from services.wizard import get_wizard_session_service
    from auth.decorators import get_or_create_user

    data = request.get_json()
    if not data or 'url' not in data:
        raise ValueError('url is required')

    username = AuthUtils.extract_username_without_validation() or 'unknown'
    user = get_or_create_user(username)

    result = ChatbotBuilderService.create_wizard_chatbot(data['url'], username)

    # Log wizard started
    if result['success'] and 'chatbot' in result:
        chatbot_id = result['chatbot']['id']

        # Create Redis session for server-authoritative state
        wizard_service = get_wizard_session_service()
        wizard_service.create_session(
            chatbot_id=chatbot_id,
            user_id=user.id,
            username=username,
            source_url=data['url'],
            crawler_config=data.get('crawler_config'),
            wizard_data={
                'name': result['chatbot'].get('name', ''),
                'displayName': result['chatbot'].get('display_name', ''),
            }
        )

        ChatbotActivityService.log_wizard_started(
            chatbot_id=chatbot_id,
            source_url=data['url'],
            username=username
        )
        # Also log chatbot creation (via wizard)
        ChatbotActivityService.log_chatbot_created(
            chatbot_id=chatbot_id,
            chatbot_name=result['chatbot'].get('name', ''),
            display_name=result['chatbot'].get('display_name', ''),
            username=username,
            source_url=data['url'],
            via_wizard=True
        )

        # Add session_id to response (equals chatbot_id, for API consumers)
        result['session_id'] = chatbot_id

    return jsonify(result), 201 if result['success'] else 400


@chatbot_blueprint.route('/<int:chatbot_id>/wizard/crawl', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def start_wizard_crawl(chatbot_id):
    """Start the crawl process for a wizard chatbot."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    from services.wizard import get_wizard_session_service
    from socketio_handlers.events_wizard import emit_wizard_status_changed
    from main import socketio

    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    # Defaults loaded from system_settings DB table
    max_pages = data.get('max_pages', get_default_max_pages())
    max_depth = data.get('max_depth', get_default_max_depth())
    use_playwright = data.get('use_playwright', True)
    use_vision_llm = data.get('use_vision_llm', False)
    take_screenshots = data.get('take_screenshots', True)

    # Store crawler config in session
    crawler_config = {
        'max_pages': max_pages,
        'max_depth': max_depth,
        'use_playwright': use_playwright,
        'use_vision_llm': use_vision_llm,
        'take_screenshots': take_screenshots
    }

    result = ChatbotBuilderService.start_crawl(
        chatbot_id,
        max_pages=max_pages,
        max_depth=max_depth,
        use_playwright=use_playwright,
        use_vision_llm=use_vision_llm,
        take_screenshots=take_screenshots
    )

    # Update Redis session with job info
    if result['success']:
        wizard_service = get_wizard_session_service()
        wizard_service.transition_status(chatbot_id, 'crawling')
        wizard_service.update_session(chatbot_id, {
            'crawler_job_id': result.get('job_id', ''),
            'collection_id': result.get('collection_id', ''),
            'crawler_config': crawler_config
        })

        # Emit status change to connected clients
        emit_wizard_status_changed(socketio, chatbot_id, 'crawling', step=2)

    return jsonify(result), 200 if result['success'] else 400


@chatbot_blueprint.route('/<int:chatbot_id>/wizard/generate-field', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def generate_chatbot_field(chatbot_id):
    """Generate a field value using LLM."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    data = request.get_json()
    if not data or 'field' not in data:
        raise ValueError('field is required')

    stream = bool(data.get('stream'))
    force_llm = bool(data.get('force_llm', False))

    # Fast path: classic non-streaming behaviour
    if not stream:
        result = ChatbotBuilderService.generate_field(
            chatbot_id=chatbot_id,
            field=data['field'],
            context=data.get('context'),
            force_llm=force_llm
        )
        return jsonify(result), 200 if result['success'] else 400

    # Streaming mode (Server-Sent Events)
    def event_stream():
        try:
            for chunk in ChatbotBuilderService.stream_field(
                chatbot_id=chatbot_id,
                field=data['field'],
                context=data.get('context')
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"[ChatbotWizard] Streaming generation failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    response = Response(stream_with_context(event_stream()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


@chatbot_blueprint.route('/<int:chatbot_id>/wizard/status', methods=['GET'])
@require_permission('feature:chatbots:view')
@handle_errors(logger_name='chatbot')
def get_wizard_status(chatbot_id):
    """Get the current build status of a wizard chatbot (from Redis session if available)."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    from services.wizard import get_wizard_session_service
    from datetime import datetime

    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    # Try Redis session first (more up-to-date)
    wizard_service = get_wizard_session_service()
    session = wizard_service.get_session(chatbot_id)

    if session:
        progress = wizard_service.get_progress(chatbot_id)
        elapsed = wizard_service.get_elapsed_time(chatbot_id)
        return jsonify({
            'success': True,
            'session': session,
            'progress': progress,
            'elapsed_time': elapsed,
            'server_time': datetime.utcnow().isoformat()
        })

    # Fall back to database/service
    result = ChatbotBuilderService.get_build_status(chatbot_id)
    return jsonify(result), 200 if result['success'] else 404


@chatbot_blueprint.route('/<int:chatbot_id>/wizard/finalize', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def finalize_wizard_chatbot(chatbot_id):
    """Finalize the chatbot configuration and mark as ready."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    from services.wizard import get_wizard_session_service
    from socketio_handlers.events_wizard import emit_wizard_status_changed
    from main import socketio
    from db.tables import RAGDocument, CollectionDocumentLink

    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    result = ChatbotBuilderService.finalize_chatbot(chatbot_id, data)

    # Log wizard completed
    if result['success']:
        # Count documents in primary collection
        doc_count = 0
        if chatbot.primary_collection_id:
            doc_count = CollectionDocumentLink.query.filter_by(
                collection_id=chatbot.primary_collection_id
            ).count()

        ChatbotActivityService.log_wizard_completed(
            chatbot_id=chatbot_id,
            chatbot_name=chatbot.display_name,
            username=username,
            document_count=doc_count
        )

        # Emit final status change and clean up Redis session
        emit_wizard_status_changed(socketio, chatbot_id, 'ready', step=5)

        wizard_service = get_wizard_session_service()
        wizard_service.delete_session(chatbot_id)

    return jsonify(result), 200 if result['success'] else 400


@chatbot_blueprint.route('/<int:chatbot_id>/wizard/pause', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def pause_wizard_build(chatbot_id):
    """Pause the chatbot build process."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    from services.wizard import get_wizard_session_service
    from socketio_handlers.events_wizard import emit_wizard_status_changed
    from main import socketio

    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    result = ChatbotBuilderService.update_build_status(chatbot_id, 'paused')

    if result['success']:
        # Update Redis session (pauses timers)
        wizard_service = get_wizard_session_service()
        wizard_service.transition_status(chatbot_id, 'paused')
        emit_wizard_status_changed(socketio, chatbot_id, 'paused', step=None)

    return jsonify(result), 200 if result['success'] else 400


@chatbot_blueprint.route('/<int:chatbot_id>/cancel-build', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def cancel_chatbot_build(chatbot_id):
    """Cancel the chatbot build process."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    from services.wizard import get_wizard_session_service
    from socketio_handlers.events_wizard import emit_wizard_status_changed
    from main import socketio

    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    result = ChatbotBuilderService.cancel_build(chatbot_id)

    # Log wizard cancelled
    if result['success']:
        ChatbotActivityService.log_wizard_cancelled(
            chatbot_id=chatbot_id,
            username=username
        )

        # Emit status change and delete Redis session
        emit_wizard_status_changed(socketio, chatbot_id, 'error', step=None, data={'cancelled': True})

        wizard_service = get_wizard_session_service()
        wizard_service.delete_session(chatbot_id)

    return jsonify(result), 200 if result['success'] else 400


@chatbot_blueprint.route('/<int:chatbot_id>/resume-build', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def resume_chatbot_build(chatbot_id):
    """Resume a paused chatbot build process."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    result = ChatbotBuilderService.resume_build(chatbot_id)
    return jsonify(result), 200 if result['success'] else 400


@chatbot_blueprint.route('/<int:chatbot_id>/admin-test', methods=['GET'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def get_admin_test_data(chatbot_id):
    """Get data for the admin test page."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    result = ChatbotBuilderService.get_admin_test_data(chatbot_id)
    return jsonify(result), 200 if result['success'] else 404


@chatbot_blueprint.route('/<int:chatbot_id>/tweak', methods=['PATCH'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def tweak_chatbot(chatbot_id):
    """Quick-tweak chatbot parameters (partial update)."""
    from services.chatbot.chatbot_builder_service import ChatbotBuilderService
    username = AuthUtils.extract_username_without_validation()
    chatbot = Chatbot.query.get(chatbot_id)
    if not chatbot:
        return jsonify({'success': False, 'error': 'Chatbot not found'}), 404
    if not ChatbotAccessService.user_can_manage_chatbot(username, chatbot):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    data = request.get_json()
    if not data:
        raise ValueError('No data provided')
    result = ChatbotBuilderService.tweak_chatbot(chatbot_id, data)
    return jsonify(result), 200 if result['success'] else 400
