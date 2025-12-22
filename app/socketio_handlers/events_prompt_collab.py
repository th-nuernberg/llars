"""
Socket.IO events for Prompt Engineering real-time collaboration updates.

Events:
    Client → Server:
        - prompt:subscribe: Subscribe to commit updates for a prompt
        - prompt:unsubscribe: Unsubscribe from commit updates

    Server → Client:
        - prompt:commit_created: A new commit was created for a prompt
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request

logger = logging.getLogger(__name__)

PROMPT_ROOM_PREFIX = "prompt_"


def get_prompt_room(prompt_id: int) -> str:
    return f"{PROMPT_ROOM_PREFIX}{prompt_id}"


def register_prompt_collab_events(socketio):
    """Register Socket.IO events for Prompt Engineering collaboration."""

    @socketio.on('prompt:subscribe')
    def handle_subscribe_prompt(data=None):
        if data is None:
            data = {}

        prompt_id = data.get('prompt_id')
        if not prompt_id:
            emit('prompt:error', {'error': 'prompt_id is required'})
            return

        room = get_prompt_room(prompt_id)
        join_room(room)
        logger.info(f"[Prompt Collab] Client {request.sid} subscribed to prompt {prompt_id}")
        emit('prompt:subscribed', {'prompt_id': prompt_id, 'room': room})

    @socketio.on('prompt:unsubscribe')
    def handle_unsubscribe_prompt(data=None):
        if data is None:
            data = {}

        prompt_id = data.get('prompt_id')
        if not prompt_id:
            return

        room = get_prompt_room(prompt_id)
        leave_room(room)
        logger.info(f"[Prompt Collab] Client {request.sid} unsubscribed from prompt {prompt_id}")

    logger.info("[Prompt Collab] Socket events registered")


def emit_prompt_commit_created(socketio, prompt_id: int, commit: dict):
    """Emit a commit-created event to all subscribers of a prompt."""
    try:
        room = get_prompt_room(prompt_id)
        socketio.emit('prompt:commit_created', {'prompt_id': prompt_id, 'commit': commit}, room=room)
    except Exception as exc:
        logger.error(f"[Prompt Collab] Failed to emit commit_created for prompt {prompt_id}: {exc}")
