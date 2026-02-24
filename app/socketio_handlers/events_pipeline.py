"""
Pipeline Socket.IO Events.

Handles room join/leave for pipeline run sessions.
Broadcast functions are called from PipelineOrchestratorService.

Event Namespace: pipeline:*

Rooms:
    pipeline_run_{run_id} - Per-run room for live updates
"""

import logging

from flask_socketio import emit, join_room, leave_room
from flask import request

logger = logging.getLogger(__name__)

PIPELINE_OVERVIEW_ROOM = "pipeline_overview"


def pipeline_run_room(run_id: int) -> str:
    """Return the Socket.IO room name for a pipeline run."""
    return f"pipeline_run_{int(run_id)}"


def register_pipeline_events(socketio):
    """Register Socket.IO events for the pipeline feature."""

    @socketio.on('pipeline:join_run')
    def handle_join_run(data):
        """Join a pipeline run room for live updates."""
        run_id = data.get('run_id')
        if not run_id:
            emit('pipeline:error', {'message': 'run_id required'})
            return

        room = pipeline_run_room(run_id)
        join_room(room)

        logger.info(
            "[Pipeline Socket] Client %s joined room %s",
            request.sid, room
        )

        emit('pipeline:joined', {
            'run_id': run_id,
            'room': room,
        })

    @socketio.on('pipeline:leave_run')
    def handle_leave_run(data):
        """Leave a pipeline run room."""
        run_id = data.get('run_id')
        if not run_id:
            return

        room = pipeline_run_room(run_id)
        leave_room(room)

        logger.info(
            "[Pipeline Socket] Client %s left room %s",
            request.sid, room
        )

    @socketio.on('pipeline:join_overview')
    def handle_join_overview():
        """Join the pipeline overview room for run list updates."""
        join_room(PIPELINE_OVERVIEW_ROOM)
        emit('pipeline:overview_joined', {'room': PIPELINE_OVERVIEW_ROOM})

    @socketio.on('pipeline:leave_overview')
    def handle_leave_overview():
        """Leave the pipeline overview room."""
        leave_room(PIPELINE_OVERVIEW_ROOM)

    logger.info("[Pipeline Socket] Events registered")


# =============================================================================
# BROADCAST HELPERS (called from services)
# =============================================================================


def emit_pipeline_run_update(socketio, run_id: int, event: str, data: dict):
    """Broadcast an event to all clients in a pipeline run room."""
    room = pipeline_run_room(run_id)
    socketio.emit(event, data, room=room)


def emit_pipeline_overview_update(socketio, data: dict):
    """Broadcast update to the overview room."""
    socketio.emit('pipeline:overview_updated', data, room=PIPELINE_OVERVIEW_ROOM)
