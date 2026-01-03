# chatbot_chat_routes.py
"""
Chatbot chat routes - message handling and test functionality.
"""

import uuid
import json
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from db.tables import Chatbot
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_errors
from services.chatbot.chat_service import ChatService
from services.chatbot.agent_chat_service import AgentChatService
from services.chatbot.file_processor import file_processor, FileProcessor
from services.chatbot.chatbot_access_service import ChatbotAccessService
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

# Max file upload size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

chatbot_chat_bp = Blueprint('chatbot_chat', __name__)


@chatbot_chat_bp.route('/<int:chatbot_id>/chat', methods=['POST'])
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


@chatbot_chat_bp.route('/<int:chatbot_id>/capabilities', methods=['GET'])
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


@chatbot_chat_bp.route('/<int:chatbot_id>/test', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_errors(logger_name='chatbot')
def test_chat(chatbot_id):
    """Test a chatbot without saving the conversation"""
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
