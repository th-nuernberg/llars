# chatbot_wizard_routes.py
"""
Chatbot builder wizard routes - wizard session management and build process.
"""

import json
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from db.tables import Chatbot
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_errors
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.chatbot_activity_service import ChatbotActivityService
from services.system_settings_service import get_default_max_pages, get_default_max_depth
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

chatbot_wizard_bp = Blueprint('chatbot_wizard', __name__)


@chatbot_wizard_bp.route('/wizard/sessions', methods=['GET'])
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


@chatbot_wizard_bp.route('/wizard/sessions/<int:chatbot_id>/join', methods=['POST'])
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


@chatbot_wizard_bp.route('/wizard/sessions/<int:chatbot_id>/data', methods=['PATCH'])
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


@chatbot_wizard_bp.route('/wizard', methods=['POST'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/wizard/crawl', methods=['POST'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/wizard/generate-field', methods=['POST'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/wizard/status', methods=['GET'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/wizard/finalize', methods=['POST'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/wizard/pause', methods=['POST'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/cancel-build', methods=['POST'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/resume-build', methods=['POST'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/admin-test', methods=['GET'])
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


@chatbot_wizard_bp.route('/<int:chatbot_id>/tweak', methods=['PATCH'])
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
