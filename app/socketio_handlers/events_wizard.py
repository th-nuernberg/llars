"""
Socket.IO events for Wizard Session real-time updates.

This module provides server-authoritative session management via WebSocket.
Clients join a session room to receive live updates; all state is stored in Redis.

Events (Client -> Server):
    wizard:join_session   - Join a wizard session room for live updates
    wizard:leave_session  - Leave a wizard session room (session continues)
    wizard:get_state      - Request current session state (for reconnection)
    wizard:heartbeat      - Keep session active, update last_activity_at

Events (Server -> Client):
    wizard:state          - Full session state snapshot
    wizard:progress       - Progress update (crawl/embed stats)
    wizard:status_changed - Status transition notification
    wizard:elapsed_time   - Server-computed elapsed time
    wizard:error          - Error notification
"""

import logging
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)


def register_wizard_events(socketio):
    """Register Socket.IO events for wizard sessions."""

    @socketio.on('wizard:join_session')
    def handle_join_session(data):
        """
        Join wizard session room and receive full state.

        Args:
            data: {chatbot_id: int}

        Emits:
            wizard:state - Full session state to requesting client
        """
        chatbot_id = data.get('chatbot_id')
        if not chatbot_id:
            emit('wizard:error', {'message': 'chatbot_id required'})
            return

        from services.wizard import get_wizard_session_service
        service = get_wizard_session_service()

        session = service.get_session(chatbot_id)
        if not session:
            emit('wizard:error', {'message': f'Session {chatbot_id} not found'})
            return

        # Join the wizard session room
        room = f"wizard_{chatbot_id}"
        join_room(room)

        # Also join related rooms for live updates
        if session.get('crawler_job_id'):
            join_room(f"crawler_{session['crawler_job_id']}")

        if session.get('collection_id'):
            join_room(f"rag_collection_{session['collection_id']}")

        # Get current progress and elapsed time
        progress = service.get_progress(chatbot_id)
        elapsed = service.get_elapsed_time(chatbot_id)

        # Send full state to the joining client
        emit('wizard:state', {
            'session': session,
            'progress': progress,
            'elapsed_time': elapsed,
            'server_time': datetime.utcnow().isoformat()
        })

        logger.info(f"[Wizard] Client {request.sid} joined session {chatbot_id}")

    @socketio.on('wizard:leave_session')
    def handle_leave_session(data):
        """
        Leave wizard session room (session continues on server).

        Args:
            data: {chatbot_id: int}
        """
        chatbot_id = data.get('chatbot_id')
        if not chatbot_id:
            return

        room = f"wizard_{chatbot_id}"
        leave_room(room)

        logger.info(f"[Wizard] Client {request.sid} left session {chatbot_id}")

    @socketio.on('wizard:get_state')
    def handle_get_state(data):
        """
        Request current session state (for reconnection).

        Args:
            data: {chatbot_id: int}

        Emits:
            wizard:state - Full session state to requesting client
        """
        chatbot_id = data.get('chatbot_id')
        if not chatbot_id:
            emit('wizard:error', {'message': 'chatbot_id required'})
            return

        from services.wizard import get_wizard_session_service
        service = get_wizard_session_service()

        session = service.get_session(chatbot_id)
        if not session:
            emit('wizard:error', {'message': f'Session {chatbot_id} not found'})
            return

        progress = service.get_progress(chatbot_id)
        elapsed = service.get_elapsed_time(chatbot_id)

        emit('wizard:state', {
            'session': session,
            'progress': progress,
            'elapsed_time': elapsed,
            'server_time': datetime.utcnow().isoformat()
        })

    @socketio.on('wizard:heartbeat')
    def handle_heartbeat(data):
        """
        Keep session active and update last_activity_at.

        Args:
            data: {chatbot_id: int}

        Emits:
            wizard:elapsed_time - Server-computed elapsed time
        """
        chatbot_id = data.get('chatbot_id')
        if not chatbot_id:
            return

        from services.wizard import get_wizard_session_service
        service = get_wizard_session_service()

        # Update activity timestamp
        service.update_session(chatbot_id, {
            'last_activity_at': datetime.utcnow().isoformat()
        })

        # Send back elapsed time
        elapsed = service.get_elapsed_time(chatbot_id)
        emit('wizard:elapsed_time', elapsed)


# ========== Emit Functions for Workers ==========
# These functions are called by background workers to broadcast updates

def emit_wizard_state(socketio, chatbot_id: int, session: dict = None, progress: dict = None):
    """
    Emit full session state to all clients in room.

    Args:
        socketio: SocketIO instance
        chatbot_id: The chatbot ID
        session: Optional session dict (fetched if not provided)
        progress: Optional progress dict (fetched if not provided)
    """
    from services.wizard import get_wizard_session_service
    service = get_wizard_session_service()

    if session is None:
        session = service.get_session(chatbot_id)
    if progress is None:
        progress = service.get_progress(chatbot_id)

    elapsed = service.get_elapsed_time(chatbot_id)

    room = f"wizard_{chatbot_id}"
    socketio.emit('wizard:state', {
        'chatbot_id': chatbot_id,  # Include for client-side filtering
        'session': session,
        'progress': progress,
        'elapsed_time': elapsed,
        'server_time': datetime.utcnow().isoformat()
    }, room=room)


def emit_wizard_progress(socketio, chatbot_id: int, progress: dict):
    """
    Emit progress update to all clients in room.

    Args:
        socketio: SocketIO instance
        chatbot_id: The chatbot ID
        progress: Progress dict with stats
    """
    from services.wizard import get_wizard_session_service
    service = get_wizard_session_service()

    elapsed = service.get_elapsed_time(chatbot_id)

    room = f"wizard_{chatbot_id}"
    socketio.emit('wizard:progress', {
        'chatbot_id': chatbot_id,  # Include for client-side filtering
        'progress': progress,
        'elapsed_time': elapsed,
        'server_time': datetime.utcnow().isoformat()
    }, room=room)


def emit_wizard_status_changed(socketio, chatbot_id: int, status: str, step: int = None, data: dict = None):
    """
    Emit status transition event to all clients in room.

    Args:
        socketio: SocketIO instance
        chatbot_id: The chatbot ID
        status: The new status
        step: The new step number
        data: Additional data to include
    """
    from services.wizard import get_wizard_session_service
    service = get_wizard_session_service()

    elapsed = service.get_elapsed_time(chatbot_id)

    room = f"wizard_{chatbot_id}"
    payload = {
        'chatbot_id': chatbot_id,  # Include for client-side filtering
        'status': status,
        'step': step,
        'elapsed_time': elapsed,
        'server_time': datetime.utcnow().isoformat()
    }

    if data:
        payload.update(data)

    socketio.emit('wizard:status_changed', payload, room=room)


def emit_wizard_error(socketio, chatbot_id: int, message: str, source: str = None):
    """
    Emit error notification to all clients in room.

    Args:
        socketio: SocketIO instance
        chatbot_id: The chatbot ID
        message: Error message
        source: Error source (crawl, embed, config)
    """
    room = f"wizard_{chatbot_id}"
    socketio.emit('wizard:error', {
        'chatbot_id': chatbot_id,  # Include for client-side filtering
        'message': message,
        'source': source,
        'server_time': datetime.utcnow().isoformat()
    }, room=room)


def emit_wizard_elapsed_time(socketio, chatbot_id: int):
    """
    Emit server-computed elapsed time to all clients in room.

    Args:
        socketio: SocketIO instance
        chatbot_id: The chatbot ID
    """
    from services.wizard import get_wizard_session_service
    service = get_wizard_session_service()

    elapsed = service.get_elapsed_time(chatbot_id)

    room = f"wizard_{chatbot_id}"
    socketio.emit('wizard:elapsed_time', {
        'chatbot_id': chatbot_id,  # Include for client-side filtering
        'elapsed_time': elapsed,
        'server_time': datetime.utcnow().isoformat()
    }, room=room)
