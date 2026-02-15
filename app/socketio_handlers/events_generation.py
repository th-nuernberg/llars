"""
Socket.IO Event Handlers for Batch Generation rooms.

Provides room-based subscription so clients can join an in-progress job stream
and immediately receive current state + subsequent live events.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import request
from flask_socketio import emit, join_room, leave_room

from services.generation import BatchGenerationService
from services.generation.socket_rooms import (
    GENERATION_OVERVIEW_ROOM,
    generation_job_room,
)

logger = logging.getLogger(__name__)


def _parse_job_id(data: Any) -> int | None:
    if not isinstance(data, dict):
        return None
    value = data.get("job_id")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def register_generation_events(socketio):
    """Register Socket.IO events for generation room management."""

    @socketio.on("generation:join_job")
    def handle_join_job(data):
        job_id = _parse_job_id(data)
        if not job_id:
            emit("generation:error", {"message": "job_id erforderlich"})
            return

        room = generation_job_room(job_id)
        join_room(room)
        logger.info("[Generation Socket] Client %s joined room %s", request.sid, room)

        emit("generation:joined", {"job_id": job_id, "room": room})

        # Send current state snapshot immediately so join-in-progress can resume stream.
        try:
            job_data = BatchGenerationService.get_job_status(job_id)
            emit(
                "generation:state",
                {
                    "job_id": job_id,
                    "status": job_data.get("status"),
                    "progress": job_data.get("progress"),
                    "currently_processing": job_data.get("currently_processing"),
                },
            )
        except Exception as e:
            logger.warning("[Generation Socket] Could not load state for job %s: %s", job_id, e)
            emit("generation:error", {"message": f"Job {job_id} nicht gefunden"})

    @socketio.on("generation:leave_job")
    def handle_leave_job(data):
        job_id = _parse_job_id(data)
        if not job_id:
            return

        room = generation_job_room(job_id)
        leave_room(room)
        logger.info("[Generation Socket] Client %s left room %s", request.sid, room)
        emit("generation:left", {"job_id": job_id, "room": room})

    @socketio.on("generation:join_overview")
    def handle_join_overview():
        join_room(GENERATION_OVERVIEW_ROOM)
        logger.info("[Generation Socket] Client %s joined overview room", request.sid)
        emit("generation:overview_joined", {"room": GENERATION_OVERVIEW_ROOM})

    @socketio.on("generation:leave_overview")
    def handle_leave_overview():
        leave_room(GENERATION_OVERVIEW_ROOM)
        logger.info("[Generation Socket] Client %s left overview room", request.sid)

    logger.info("[Generation Socket] Events registered")

