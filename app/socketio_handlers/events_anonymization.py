"""
Socket.IO Event Handlers for Anonymization Pipeline rooms.

Provides room-based subscription so clients can join an in-progress
NER session and receive real-time progress updates.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import request
from flask_socketio import emit, join_room, leave_room

from services.anonymize.socket_rooms import (
    ANONYMIZATION_OVERVIEW_ROOM,
    anonymization_conversation_room,
)

logger = logging.getLogger(__name__)


def _parse_conversation_id(data: Any) -> int | None:
    if not isinstance(data, dict):
        return None
    value = data.get("conversation_id")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def register_anonymization_events(socketio):
    """Register Socket.IO events for anonymization pipeline room management."""

    @socketio.on("anonymization:join_overview")
    def handle_join_overview():
        join_room(ANONYMIZATION_OVERVIEW_ROOM)
        logger.info("[Anonymization Socket] Client %s joined overview room", request.sid)
        emit("anonymization:overview_joined", {"room": ANONYMIZATION_OVERVIEW_ROOM})

    @socketio.on("anonymization:leave_overview")
    def handle_leave_overview():
        leave_room(ANONYMIZATION_OVERVIEW_ROOM)
        logger.info("[Anonymization Socket] Client %s left overview room", request.sid)

    @socketio.on("anonymization:join_conversation")
    def handle_join_conversation(data):
        conversation_id = _parse_conversation_id(data)
        if not conversation_id:
            emit("anonymization:error", {"message": "conversation_id required"})
            return

        # TODO: Security - add ownership/membership check before joining anonymization room
        room = anonymization_conversation_room(conversation_id)
        join_room(room)
        logger.info("[Anonymization Socket] Client %s joined room %s", request.sid, room)
        emit("anonymization:joined", {"conversation_id": conversation_id, "room": room})

    @socketio.on("anonymization:leave_conversation")
    def handle_leave_conversation(data):
        conversation_id = _parse_conversation_id(data)
        if not conversation_id:
            return

        room = anonymization_conversation_room(conversation_id)
        leave_room(room)
        logger.info("[Anonymization Socket] Client %s left room %s", request.sid, room)

    logger.info("[Anonymization Socket] Events registered")
