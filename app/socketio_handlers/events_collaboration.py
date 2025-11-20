"""
SocketIO Collaboration Events
Handles collaborative editing features (join, leave, cursor, content updates).
"""

import logging
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room


def register_collaboration_events(socketio, collab_manager):
    """Register collaboration-related SocketIO events"""

    @socketio.on('join_prompt')
    def handle_join_prompt(data):
        """Handle user joining a collaborative prompt session"""
        prompt_id = data['promptId']
        username = data.get('username', 'Anonymous')
        user_id = request.sid
        room = f"prompt_{prompt_id}"

        join_room(room)
        collaborators = collab_manager.join_prompt(prompt_id, user_id, username)

        # Informiere alle im Raum über den neuen Collaborator
        emit('collaborator_joined', {
            'collaborators': collaborators,
            'joinedUser': username
        }, room=room)

        logging.info(f"User {username} joined prompt {prompt_id}")

    @socketio.on('leave_prompt')
    def handle_leave_prompt(data):
        """Handle user leaving a collaborative prompt session"""
        prompt_id = data['promptId']
        user_id = request.sid
        room = f"prompt_{prompt_id}"

        collaborators = collab_manager.leave_prompt(prompt_id, user_id)
        leave_room(room)

        # Informiere andere über das Verlassen
        emit('collaborator_left', {
            'collaborators': collaborators,
            'leftuser_id': user_id
        }, room=room)

    @socketio.on('cursor_move')
    def handle_cursor_move(data):
        """Handle cursor movement in collaborative editing"""
        prompt_id = data['promptId']
        block_id = data['block_id']
        position = data['position']
        user_id = request.sid
        room = f"prompt_{prompt_id}"

        cursor_data = collab_manager.update_cursor(prompt_id, user_id, block_id, position)

        # Sende Cursor-Position an alle anderen im Raum
        emit('cursor_update', {
            **cursor_data
        }, room=room, include_self=False)

    @socketio.on('blocks_update')
    def handle_blocks_update(data):
        """Handle block structure updates in collaborative editing"""
        prompt_id = data['promptId']
        blocks = data['blocks']
        user_id = request.sid
        room = f"prompt_{prompt_id}"

        # Broadcast the blocks update to all other users in the room
        emit('blocks_update', {
            'blocks': blocks,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }, room=room, include_self=False)

    @socketio.on('content_change')
    def handle_content_change(data):
        """Handle content changes in collaborative editing"""
        prompt_id = data['promptId']
        block_id = data['block_id']
        content = data['content']
        user_id = request.sid
        room = f"prompt_{prompt_id}"

        # Speichere die Änderung in der Datenbank
        try:
            # Hier müsstest du deine Datenbanklogik implementieren
            # update_prompt_content(prompt_id, block_id, content)

            # Broadcaste die Änderung an alle anderen im Raum
            emit('content_update', {
                'block_id': block_id,
                'content': content,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }, room=room, include_self=False)

        except Exception as e:
            logging.error(f"Error updating content: {str(e)}")
            emit('error', {
                'message': 'Failed to save changes'
            }, room=request.sid)
