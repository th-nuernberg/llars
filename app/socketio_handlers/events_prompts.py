"""
Socket.IO events for Prompt Engineering real-time updates.

Events:
    Client → Server:
        - prompts:subscribe: Subscribe to prompt updates for a user
        - prompts:unsubscribe: Unsubscribe from prompt updates

    Server → Client:
        - prompts:list: Initial list of prompts after subscribing
        - prompts:updated: Prompt list has been updated
        - prompts:prompt_updated: Single prompt content changed
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request

logger = logging.getLogger(__name__)

# Room name pattern for prompt subscriptions
PROMPTS_ROOM_PREFIX = "prompts_user_"


def get_prompts_room(user_id: int) -> str:
    """Get room name for a user's prompt updates."""
    return f"{PROMPTS_ROOM_PREFIX}{user_id}"


def register_prompts_events(socketio):
    """Register Socket.IO events for prompt real-time updates."""

    @socketio.on('prompts:subscribe')
    def handle_subscribe_prompts(data=None):
        """
        Subscribe to prompt updates for the current user.

        Expected data:
            - user_id: int (required) - The user's ID to subscribe to their prompts
        """
        try:
            if data is None:
                data = {}

            user_id = data.get('user_id')
            if not user_id:
                emit('prompts:error', {'error': 'user_id is required'})
                return

            room = get_prompts_room(user_id)
            join_room(room)

            logger.info(f"[Prompts Socket] Client {request.sid} subscribed to prompts for user {user_id}")

            # Fetch and send current prompts
            from db.db import db
            from db.tables import UserPrompt, UserPromptShare, User

            user_prompts = UserPrompt.query.filter_by(user_id=user_id).all()

            prompts_data = []
            for prompt in user_prompts:
                shared_users = db.session.query(User.username) \
                    .join(UserPromptShare, User.id == UserPromptShare.shared_with_user_id) \
                    .filter(UserPromptShare.prompt_id == prompt.prompt_id) \
                    .all()
                shared_with = [u[0] for u in shared_users]

                prompts_data.append({
                    'id': prompt.prompt_id,
                    'name': prompt.name,
                    'content': prompt.content,
                    'created_at': prompt.created_at.isoformat() if prompt.created_at else None,
                    'updated_at': prompt.updated_at.isoformat() if prompt.updated_at else None,
                    'shared_with': shared_with
                })

            emit('prompts:list', {'prompts': prompts_data})
            emit('prompts:subscribed', {'user_id': user_id, 'room': room})

        except Exception as e:
            logger.error(f"[Prompts Socket] Error subscribing to prompts: {e}")
            emit('prompts:error', {'error': str(e)})

    @socketio.on('prompts:unsubscribe')
    def handle_unsubscribe_prompts(data=None):
        """Unsubscribe from prompt updates."""
        try:
            if data is None:
                data = {}

            user_id = data.get('user_id')
            if user_id:
                room = get_prompts_room(user_id)
                leave_room(room)
                logger.info(f"[Prompts Socket] Client {request.sid} unsubscribed from prompts for user {user_id}")

        except Exception as e:
            logger.error(f"[Prompts Socket] Error unsubscribing from prompts: {e}")

    logger.info("[Prompts Socket] Events registered")


def emit_prompts_updated(socketio, user_id: int, prompts: list = None):
    """
    Emit prompt list update to all subscribed clients for a user.

    Args:
        socketio: Flask-SocketIO instance
        user_id: The user whose prompts have been updated
        prompts: Optional list of prompts to send (will fetch if None)
    """
    try:
        if prompts is None:
            from db.db import db
            from db.tables import UserPrompt, UserPromptShare, User

            user_prompts = UserPrompt.query.filter_by(user_id=user_id).all()

            prompts = []
            for prompt in user_prompts:
                shared_users = db.session.query(User.username) \
                    .join(UserPromptShare, User.id == UserPromptShare.shared_with_user_id) \
                    .filter(UserPromptShare.prompt_id == prompt.prompt_id) \
                    .all()
                shared_with = [u[0] for u in shared_users]

                prompts.append({
                    'id': prompt.prompt_id,
                    'name': prompt.name,
                    'content': prompt.content,
                    'created_at': prompt.created_at.isoformat() if prompt.created_at else None,
                    'updated_at': prompt.updated_at.isoformat() if prompt.updated_at else None,
                    'shared_with': shared_with
                })

        room = get_prompts_room(user_id)
        socketio.emit('prompts:updated', {'prompts': prompts}, room=room)
        logger.info(f"[Prompts Socket] Emitted prompts update to room {room}")

    except Exception as e:
        logger.error(f"[Prompts Socket] Error emitting prompts update: {e}")


def emit_prompt_content_updated(socketio, user_id: int, prompt_id: int, content: dict):
    """
    Emit a single prompt content update.

    Args:
        socketio: Flask-SocketIO instance
        user_id: The user whose prompt was updated
        prompt_id: The ID of the updated prompt
        content: The new content of the prompt
    """
    try:
        room = get_prompts_room(user_id)
        socketio.emit('prompts:prompt_updated', {
            'prompt_id': prompt_id,
            'content': content
        }, room=room)
        logger.info(f"[Prompts Socket] Emitted prompt {prompt_id} content update to room {room}")

    except Exception as e:
        logger.error(f"[Prompts Socket] Error emitting prompt content update: {e}")
