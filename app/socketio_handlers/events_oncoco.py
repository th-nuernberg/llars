"""
Socket.IO event handlers for OnCoCo Analysis.

Provides real-time updates during analysis:
- Progress updates
- Sentence classification stream
- Hardware/worker status
- Completion notifications
"""

import logging
import time
from flask_socketio import emit, join_room, leave_room
from flask import request

logger = logging.getLogger(__name__)

# Track active analysis state for detailed updates
_active_analyses = {}


def register_oncoco_events(socketio):
    """Register OnCoCo Socket.IO event handlers."""

    @socketio.on('oncoco:join_analysis')
    def handle_join_analysis(data):
        """Join a room for analysis updates."""
        analysis_id = data.get('analysis_id')
        if analysis_id:
            room = f'oncoco_analysis_{analysis_id}'
            join_room(room)
            logger.info(f"[OnCoCo Socket] Client {request.sid} joined room {room}")
            emit('oncoco:joined', {'analysis_id': analysis_id, 'room': room})

    @socketio.on('oncoco:leave_analysis')
    def handle_leave_analysis(data):
        """Leave an analysis room."""
        analysis_id = data.get('analysis_id')
        if analysis_id:
            room = f'oncoco_analysis_{analysis_id}'
            leave_room(room)
            logger.info(f"[OnCoCo Socket] Client {request.sid} left room {room}")

    @socketio.on('oncoco:get_status')
    def handle_get_status(data):
        """Get current analysis status."""
        from db.tables import OnCoCoAnalysis

        analysis_id = data.get('analysis_id')
        if not analysis_id:
            emit('oncoco:error', {'message': 'analysis_id required'})
            return

        analysis = OnCoCoAnalysis.query.get(analysis_id)
        if not analysis:
            emit('oncoco:error', {'message': 'Analysis not found'})
            return

        emit('oncoco:status', {
            'analysis_id': analysis.id,
            'status': analysis.status.value,
            'processed_threads': analysis.processed_threads,
            'total_threads': analysis.total_threads,
            'total_sentences': analysis.total_sentences,
            'progress': (analysis.processed_threads / analysis.total_threads * 100)
                       if analysis.total_threads > 0 else 0
        })

    logger.info("[OnCoCo Socket] Events registered")


def emit_oncoco_progress(socketio, analysis_id: int, processed: int, total: int, sentences: int,
                         current_thread: dict = None, current_message: dict = None,
                         hardware_info: dict = None, timing_info: dict = None):
    """Emit detailed progress update to analysis room."""
    room = f'oncoco_analysis_{analysis_id}'

    # Calculate timing estimates
    elapsed = timing_info.get('elapsed', 0) if timing_info else 0
    threads_per_second = processed / elapsed if elapsed > 0 and processed > 0 else 0
    remaining_threads = total - processed
    eta_seconds = remaining_threads / threads_per_second if threads_per_second > 0 else 0

    socketio.emit('oncoco:progress', {
        'analysis_id': analysis_id,
        'processed_threads': processed,
        'total_threads': total,
        'total_sentences': sentences,
        'progress': (processed / total * 100) if total > 0 else 0,
        'current_thread': current_thread,
        'current_message': current_message,
        'hardware': hardware_info,
        'timing': {
            'elapsed_seconds': round(elapsed, 1),
            'threads_per_second': round(threads_per_second, 3),
            'eta_seconds': round(eta_seconds, 0),
            'sentences_per_second': round(sentences / elapsed, 2) if elapsed > 0 else 0,
            **(timing_info or {})
        }
    }, room=room)


def emit_oncoco_sentence(socketio, analysis_id: int, sentence_data: dict):
    """Emit sentence classification to analysis room."""
    room = f'oncoco_analysis_{analysis_id}'
    socketio.emit('oncoco:sentence', {
        'analysis_id': analysis_id,
        **sentence_data
    }, room=room)


def emit_oncoco_complete(socketio, analysis_id: int, status: str, total_sentences: int,
                        duration_seconds: float = 0, hardware_info: dict = None):
    """Emit completion notification to analysis room."""
    room = f'oncoco_analysis_{analysis_id}'
    socketio.emit('oncoco:complete', {
        'analysis_id': analysis_id,
        'status': status,
        'total_sentences': total_sentences,
        'duration_seconds': round(duration_seconds, 1),
        'hardware': hardware_info
    }, room=room)


def get_analysis_state(analysis_id: int) -> dict:
    """Get current state for an analysis."""
    return _active_analyses.get(analysis_id, {})


def set_analysis_state(analysis_id: int, state: dict):
    """Update state for an analysis."""
    _active_analyses[analysis_id] = state


def clear_analysis_state(analysis_id: int):
    """Clear state for a completed analysis."""
    _active_analyses.pop(analysis_id, None)
