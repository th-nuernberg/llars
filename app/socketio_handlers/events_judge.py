"""
Socket.IO Event Handlers for LLM-as-Judge.

Handles real-time communication for:
- Session room management (join/leave)
- Live evaluation streaming
- Progress updates
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request

logger = logging.getLogger(__name__)


def register_judge_events(socketio):
    """
    Register Socket.IO events for Judge functionality.

    Events:
        judge:join_session - Join a session room for live updates
        judge:leave_session - Leave a session room
    """

    @socketio.on('judge:join_session')
    def handle_join_session(data):
        """
        Handle client joining a Judge session room.

        Args:
            data: dict with 'session_id'

        Emits:
            judge:joined - Confirmation of join
        """
        session_id = data.get('session_id')
        if not session_id:
            emit('judge:error', {'message': 'session_id erforderlich'})
            return

        room = f"judge_session_{session_id}"
        join_room(room)

        logger.info(f"[Judge Socket] Client {request.sid} joined room {room}")

        emit('judge:joined', {
            'session_id': session_id,
            'room': room,
            'message': 'Erfolgreich verbunden'
        })

    @socketio.on('judge:leave_session')
    def handle_leave_session(data):
        """
        Handle client leaving a Judge session room.

        Args:
            data: dict with 'session_id'
        """
        session_id = data.get('session_id')
        if not session_id:
            return

        room = f"judge_session_{session_id}"
        leave_room(room)

        logger.info(f"[Judge Socket] Client {request.sid} left room {room}")

        emit('judge:left', {
            'session_id': session_id,
            'room': room
        })

    @socketio.on('judge:get_status')
    def handle_get_status(data):
        """
        Get current status of a Judge session.

        Args:
            data: dict with 'session_id'

        Emits:
            judge:status - Current session status
        """
        from db.tables import JudgeSession

        session_id = data.get('session_id')
        if not session_id:
            emit('judge:error', {'message': 'session_id erforderlich'})
            return

        session = JudgeSession.query.get(session_id)
        if not session:
            emit('judge:error', {'message': 'Session nicht gefunden'})
            return

        progress = (session.completed_comparisons / session.total_comparisons * 100) \
            if session.total_comparisons > 0 else 0

        emit('judge:status', {
            'session_id': session_id,
            'status': session.status.value,
            'completed': session.completed_comparisons,
            'total': session.total_comparisons,
            'progress': progress,
            'current_comparison_id': session.current_comparison_id
        })

    logger.info("[Judge Socket] Events registered")


# Broadcast functions (called from worker)
def broadcast_to_session(socketio, session_id: int, event: str, data: dict):
    """
    Broadcast an event to all clients in a session room.

    Args:
        socketio: SocketIO instance
        session_id: Session ID
        event: Event name
        data: Event data
    """
    room = f"judge_session_{session_id}"
    socketio.emit(event, data, room=room)
