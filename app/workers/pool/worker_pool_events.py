# worker_pool_events.py
"""
Socket.IO event broadcasting for the Judge Worker Pool.

This module handles all real-time WebSocket communication from workers:
- Comparison start/complete notifications
- LLM streaming token broadcasts
- Progress updates (atomic and legacy)
- Session completion notifications

All events are broadcast to two rooms:
1. `judge_session_{session_id}` - Session-specific room for detail view
2. `judge_overview` - Overview room for dashboard updates

Used by: judge_worker_pool.py (PooledJudgeWorker class)
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


# =============================================================================
# SOCKETIO INSTANCE RETRIEVAL
# =============================================================================

def get_socketio(session_id: int, worker_id: int):
    """
    Get the Flask-SocketIO instance.

    Tries multiple import paths to handle different execution contexts:
    1. Direct import from main module
    2. Import from app.main module
    3. Flask current_app extensions

    Args:
        session_id: Session ID for logging context
        worker_id: Worker ID for logging context

    Returns:
        SocketIO instance if found, None otherwise

    Note:
        This function is designed to work in both main thread and
        background worker thread contexts.
    """
    try:
        # Try direct import from main
        try:
            from main import socketio
            logger.debug(
                f"[JudgeWorker:{session_id}:{worker_id}] Got socketio from main"
            )
            return socketio
        except ImportError as e:
            logger.debug(
                f"[JudgeWorker:{session_id}:{worker_id}] main import failed: {e}"
            )

        # Try import from app.main
        try:
            from app.main import socketio
            logger.debug(
                f"[JudgeWorker:{session_id}:{worker_id}] Got socketio from app.main"
            )
            return socketio
        except ImportError as e:
            logger.debug(
                f"[JudgeWorker:{session_id}:{worker_id}] app.main import failed: {e}"
            )

        # Try Flask extensions
        from flask import current_app
        if hasattr(current_app, 'extensions') and 'socketio' in current_app.extensions:
            logger.debug(
                f"[JudgeWorker:{session_id}:{worker_id}] Got socketio from extensions"
            )
            return current_app.extensions['socketio']

        logger.warning(
            f"[JudgeWorker:{session_id}:{worker_id}] No socketio instance found!"
        )
        return None

    except Exception as e:
        logger.warning(
            f"[JudgeWorker:{session_id}:{worker_id}] Failed to get socketio: {e}"
        )
        return None


# =============================================================================
# COMPARISON LIFECYCLE EVENTS
# =============================================================================

def broadcast_comparison_start(
    session_id: int,
    worker_id: int,
    comparison_data: Dict[str, Any]
) -> None:
    """
    Broadcast when a comparison starts processing.

    Notifies connected clients that a worker has begun evaluating a comparison.
    The comparison_data is stored by the worker for reconnect support.

    Args:
        session_id: ID of the judge session
        worker_id: ID of the worker processing the comparison
        comparison_data: Dict containing:
            - comparison_id: ID of the comparison
            - thread_a_id: First thread being compared
            - thread_b_id: Second thread being compared
            - pillar_a: First pillar ID
            - pillar_b: Second pillar ID
            - position_order: Order variant (AB or BA)

    Event: judge:comparison_start
    Rooms: judge_session_{session_id}
    """
    socketio = get_socketio(session_id, worker_id)
    if not socketio:
        logger.warning(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Cannot broadcast comparison_start - no socketio"
        )
        return

    room = f"judge_session_{session_id}"
    logger.info(
        f"[JudgeWorker:{session_id}:{worker_id}] "
        f"Broadcasting comparison_start to room {room}"
    )

    socketio.emit('judge:comparison_start', {
        'session_id': session_id,
        'worker_id': worker_id,
        **comparison_data
    }, room=room)


def broadcast_stream_chunk(
    session_id: int,
    worker_id: int,
    chunk: str,
    accumulated_length: int
) -> None:
    """
    Broadcast an LLM streaming token chunk.

    Called for each token received during LLM evaluation streaming.
    The accumulated_length helps clients verify they haven't missed chunks.

    Args:
        session_id: ID of the judge session
        worker_id: ID of the worker streaming
        chunk: The token/chunk content
        accumulated_length: Total length of accumulated stream content

    Event: judge:llm_stream
    Rooms: judge_session_{session_id}
    """
    socketio = get_socketio(session_id, worker_id)
    if not socketio:
        return

    room = f"judge_session_{session_id}"
    socketio.emit('judge:llm_stream', {
        'session_id': session_id,
        'worker_id': worker_id,
        'token': chunk,
        'content': chunk,
        'accumulated_length': accumulated_length
    }, room=room)


def broadcast_comparison_complete(
    session_id: int,
    worker_id: int,
    comparison_id: int,
    result: Any,
    stream_content: str,
    completed: int,
    total: int
) -> None:
    """
    Broadcast when a comparison completes successfully.

    Sends the evaluation result to all connected clients.
    Includes the final stream content for verification.

    Args:
        session_id: ID of the judge session
        worker_id: ID of the worker that processed the comparison
        comparison_id: ID of the completed comparison
        result: JudgeEvaluationResult with winner, confidence, reasoning
        stream_content: Final accumulated LLM stream content
        completed: Number of completed comparisons (atomic value)
        total: Total number of comparisons in session

    Event: judge:comparison_complete
    Rooms: judge_session_{session_id}, judge_overview
    """
    socketio = get_socketio(session_id, worker_id)
    if not socketio:
        return

    room = f"judge_session_{session_id}"

    event_data = {
        'session_id': session_id,
        'worker_id': worker_id,
        'comparison_id': comparison_id,
        'winner': result.winner,
        'confidence': result.confidence,
        'reasoning': result.final_justification,
        'final_stream_content': stream_content,
        'completed': completed,
        'total': total
    }

    # Broadcast to session room
    socketio.emit('judge:comparison_complete', event_data, room=room)

    # Also broadcast to overview room for dashboard updates
    socketio.emit('judge:comparison_complete', event_data, room='judge_overview')


# =============================================================================
# PROGRESS EVENTS
# =============================================================================

def broadcast_progress_atomic(
    session_id: int,
    worker_id: int,
    completed: int,
    total: int
) -> None:
    """
    Broadcast session progress with atomic values.

    Uses values from atomic database increment to prevent race conditions
    where multiple workers might report incorrect progress.

    Args:
        session_id: ID of the judge session
        worker_id: ID of the reporting worker
        completed: Atomically incremented completion count
        total: Total comparisons in session

    Event: judge:progress
    Rooms: judge_session_{session_id}, judge_overview
    """
    socketio = get_socketio(session_id, worker_id)
    if not socketio:
        return

    room = f"judge_session_{session_id}"
    progress = (completed / total * 100) if total > 0 else 0

    event_data = {
        'session_id': session_id,
        'status': 'running',
        'completed': completed,
        'total': total,
        'percent': progress
    }

    socketio.emit('judge:progress', event_data, room=room)
    socketio.emit('judge:progress', event_data, room='judge_overview')


def broadcast_progress_legacy(
    session_id: int,
    worker_id: int,
    session: Any
) -> None:
    """
    Broadcast session progress using session object values.

    Legacy method that reads values from the session object.
    Prefer broadcast_progress_atomic() when possible for accuracy.

    Args:
        session_id: ID of the judge session
        worker_id: ID of the reporting worker
        session: JudgeSession database object

    Event: judge:progress
    Rooms: judge_session_{session_id}, judge_overview
    """
    socketio = get_socketio(session_id, worker_id)
    if not socketio:
        return

    room = f"judge_session_{session_id}"
    progress = (session.completed_comparisons / session.total_comparisons * 100) \
        if session.total_comparisons > 0 else 0

    event_data = {
        'session_id': session_id,
        'status': session.status.value if hasattr(session.status, 'value') else str(session.status),
        'completed': session.completed_comparisons,
        'total': session.total_comparisons,
        'percent': progress
    }

    socketio.emit('judge:progress', event_data, room=room)
    socketio.emit('judge:progress', event_data, room='judge_overview')


# =============================================================================
# SESSION LIFECYCLE EVENTS
# =============================================================================

def broadcast_session_complete(
    session_id: int,
    worker_id: int,
    total: int
) -> None:
    """
    Broadcast when an entire session completes.

    Notifies all clients that the session has finished processing
    all comparisons. Both completed and total are set to the same
    value to indicate 100% completion.

    Args:
        session_id: ID of the completed session
        worker_id: ID of the worker that detected completion
        total: Total number of comparisons in the session

    Event: judge:session_complete
    Rooms: judge_session_{session_id}, judge_overview
    """
    socketio = get_socketio(session_id, worker_id)
    if not socketio:
        return

    room = f"judge_session_{session_id}"

    event_data = {
        'session_id': session_id,
        'total': total,
        'completed': total  # Both equal when complete
    }

    socketio.emit('judge:session_complete', event_data, room=room)
    socketio.emit('judge:session_complete', event_data, room='judge_overview')
