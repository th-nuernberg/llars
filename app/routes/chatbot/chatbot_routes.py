# chatbot_routes.py
"""
API routes for chatbot management and chat functionality.
"""

import uuid
import logging
from flask import Blueprint, request, jsonify, g
from decorators.permission_decorator import require_permission, require_any_permission
from services.chatbot.chatbot_service import ChatbotService
from services.chatbot.chat_service import ChatService
from services.chatbot.file_processor import file_processor, FileProcessor

logger = logging.getLogger(__name__)

# Max file upload size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

chatbot_blueprint = Blueprint('chatbot', __name__, url_prefix='/api/chatbots')


# ============================================================================
# CHATBOT CRUD ROUTES
# ============================================================================

@chatbot_blueprint.route('', methods=['GET'])
@require_permission('feature:chatbots:view')
def get_chatbots():
    """Get all chatbots"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        chatbots = ChatbotService.get_all_chatbots(include_inactive=include_inactive)
        return jsonify({
            'success': True,
            'chatbots': chatbots,
            'count': len(chatbots)
        })
    except Exception as e:
        logger.error(f"Error fetching chatbots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>', methods=['GET'])
@require_permission('feature:chatbots:view')
def get_chatbot(chatbot_id):
    """Get a single chatbot by ID"""
    try:
        chatbot = ChatbotService.get_chatbot(chatbot_id)
        if not chatbot:
            return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

        return jsonify({
            'success': True,
            'chatbot': chatbot
        })
    except Exception as e:
        logger.error(f"Error fetching chatbot {chatbot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('', methods=['POST'])
@require_permission('feature:chatbots:edit')
def create_chatbot():
    """Create a new chatbot"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        username = g.get('username', 'unknown')
        chatbot = ChatbotService.create_chatbot(data, username)

        return jsonify({
            'success': True,
            'chatbot': chatbot,
            'message': f"Chatbot '{chatbot['display_name']}' created successfully"
        }), 201

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating chatbot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>', methods=['PUT'])
@require_permission('feature:chatbots:edit')
def update_chatbot(chatbot_id):
    """Update an existing chatbot"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        chatbot = ChatbotService.update_chatbot(chatbot_id, data)
        if not chatbot:
            return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

        return jsonify({
            'success': True,
            'chatbot': chatbot,
            'message': 'Chatbot updated successfully'
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating chatbot {chatbot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>', methods=['DELETE'])
@require_permission('feature:chatbots:delete')
def delete_chatbot(chatbot_id):
    """Delete a chatbot"""
    try:
        success = ChatbotService.delete_chatbot(chatbot_id)
        if not success:
            return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Chatbot deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting chatbot {chatbot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/duplicate', methods=['POST'])
@require_permission('feature:chatbots:edit')
def duplicate_chatbot(chatbot_id):
    """Duplicate a chatbot"""
    try:
        username = g.get('username', 'unknown')
        chatbot = ChatbotService.duplicate_chatbot(chatbot_id, username)
        if not chatbot:
            return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

        return jsonify({
            'success': True,
            'chatbot': chatbot,
            'message': f"Chatbot duplicated as '{chatbot['display_name']}'"
        }), 201

    except Exception as e:
        logger.error(f"Error duplicating chatbot {chatbot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# COLLECTION ASSIGNMENT ROUTES
# ============================================================================

@chatbot_blueprint.route('/<int:chatbot_id>/collections', methods=['GET'])
@require_permission('feature:chatbots:view')
def get_chatbot_collections(chatbot_id):
    """Get all collections assigned to a chatbot"""
    try:
        collections = ChatbotService.get_collections(chatbot_id)
        return jsonify({
            'success': True,
            'collections': collections,
            'count': len(collections)
        })
    except Exception as e:
        logger.error(f"Error fetching collections for chatbot {chatbot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/collections', methods=['POST'])
@require_permission('feature:chatbots:edit')
def assign_collection(chatbot_id):
    """Assign a collection to a chatbot"""
    try:
        data = request.get_json()
        if not data or 'collection_id' not in data:
            return jsonify({'success': False, 'error': 'collection_id is required'}), 400

        username = g.get('username', 'unknown')
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

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error assigning collection to chatbot {chatbot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/collections/<int:collection_id>', methods=['PUT'])
@require_permission('feature:chatbots:edit')
def update_collection_assignment(chatbot_id, collection_id):
    """Update a collection assignment (priority, weight)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

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

    except Exception as e:
        logger.error(f"Error updating collection assignment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/collections/<int:collection_id>', methods=['DELETE'])
@require_permission('feature:chatbots:edit')
def remove_collection(chatbot_id, collection_id):
    """Remove a collection from a chatbot"""
    try:
        success = ChatbotService.remove_collection(chatbot_id, collection_id)
        if not success:
            return jsonify({'success': False, 'error': 'Assignment not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Collection removed from chatbot'
        })

    except Exception as e:
        logger.error(f"Error removing collection from chatbot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CHAT ROUTES
# ============================================================================

@chatbot_blueprint.route('/<int:chatbot_id>/chat', methods=['POST'])
@require_permission('feature:chatbots:view')
def chat(chatbot_id):
    """Send a message to a chatbot and get a response (supports file uploads)"""
    try:
        # Handle both JSON and multipart form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            # File upload via form data
            message = request.form.get('message', '')
            session_id = request.form.get('session_id', str(uuid.uuid4()))
            include_sources = request.form.get('include_sources', 'true').lower() == 'true'

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
                        return jsonify({
                            'success': False,
                            'error': f'File {file.filename} exceeds max size of 10MB'
                        }), 400

                    if not file_processor.is_supported(file.filename):
                        return jsonify({
                            'success': False,
                            'error': f'Unsupported file type: {file.filename}'
                        }), 400

                    # Read and process file
                    file_data = file.read()
                    processed = file_processor.process_file(
                        file_data,
                        file.filename
                    )
                    processed_files.append(processed)

        else:
            # Regular JSON request
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400

            message = data.get('message', '')
            session_id = data.get('session_id', str(uuid.uuid4()))
            include_sources = data.get('include_sources', True)
            processed_files = None

        if not message.strip() and not processed_files:
            return jsonify({'success': False, 'error': 'message or files required'}), 400

        username = g.get('username')

        # Initialize chat service
        chat_service = ChatService(chatbot_id)

        # Process chat with files
        result = chat_service.chat(
            message=message,
            session_id=session_id,
            username=username,
            include_sources=include_sources,
            files=processed_files
        )

        return jsonify({
            'success': True,
            **result
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error in chat with chatbot {chatbot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/capabilities', methods=['GET'])
@require_permission('feature:chatbots:view')
def get_capabilities(chatbot_id):
    """Get chatbot capabilities including vision support"""
    try:
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
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/test', methods=['POST'])
@require_permission('feature:chatbots:edit')
def test_chat(chatbot_id):
    """Test a chatbot without saving the conversation"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'message is required'}), 400

        chat_service = ChatService(chatbot_id)
        result = chat_service.test_chat(data['message'])

        return jsonify({
            'success': True,
            **result
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error in test chat with chatbot {chatbot_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CONVERSATION ROUTES
# ============================================================================

@chatbot_blueprint.route('/<int:chatbot_id>/conversations', methods=['GET'])
@require_permission('feature:chatbots:view')
def get_conversations(chatbot_id):
    """Get all conversations for a chatbot"""
    try:
        limit = request.args.get('limit', 50, type=int)
        conversations = ChatService.get_conversations(chatbot_id, limit=limit)

        return jsonify({
            'success': True,
            'conversations': conversations,
            'count': len(conversations)
        })

    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/conversations/<int:conversation_id>', methods=['GET'])
@require_permission('feature:chatbots:view')
def get_conversation(chatbot_id, conversation_id):
    """Get a single conversation with all messages"""
    try:
        conversation = ChatService.get_conversation(conversation_id)
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404

        # Verify conversation belongs to chatbot
        if conversation['chatbot_id'] != chatbot_id:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404

        return jsonify({
            'success': True,
            'conversation': conversation
        })

    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/conversations/<int:conversation_id>', methods=['DELETE'])
@require_permission('feature:chatbots:edit')
def delete_conversation(chatbot_id, conversation_id):
    """Delete a conversation"""
    try:
        # First verify the conversation belongs to this chatbot
        conversation = ChatService.get_conversation(conversation_id)
        if not conversation or conversation['chatbot_id'] != chatbot_id:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404

        success = ChatService.delete_conversation(conversation_id)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete conversation'}), 500

        return jsonify({
            'success': True,
            'message': 'Conversation deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/messages/<int:message_id>/rate', methods=['POST'])
@require_permission('feature:chatbots:view')
def rate_message(message_id):
    """Rate a message"""
    try:
        data = request.get_json()
        if not data or 'rating' not in data:
            return jsonify({'success': False, 'error': 'rating is required'}), 400

        rating = data['rating']
        if rating not in ['helpful', 'not_helpful', 'incorrect']:
            return jsonify({'success': False, 'error': 'Invalid rating'}), 400

        success = ChatService.rate_message(
            message_id=message_id,
            rating=rating,
            feedback=data.get('feedback')
        )

        if not success:
            return jsonify({'success': False, 'error': 'Message not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Rating saved'
        })

    except Exception as e:
        logger.error(f"Error rating message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# STATISTICS ROUTES
# ============================================================================

@chatbot_blueprint.route('/stats/overview', methods=['GET'])
@require_permission('feature:chatbots:view')
def get_overview_stats():
    """Get global chatbot statistics"""
    try:
        stats = ChatbotService.get_overview_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error fetching overview stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chatbot_blueprint.route('/<int:chatbot_id>/stats', methods=['GET'])
@require_permission('feature:chatbots:view')
def get_chatbot_stats(chatbot_id):
    """Get statistics for a specific chatbot"""
    try:
        stats = ChatbotService.get_stats(chatbot_id)
        if not stats:
            return jsonify({'success': False, 'error': 'Chatbot not found'}), 404

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error fetching chatbot stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
