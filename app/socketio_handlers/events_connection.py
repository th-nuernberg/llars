"""
SocketIO Connection Events
Handles client connection and disconnection.
"""

import logging
from flask import request
from flask_socketio import emit


def register_connection_events(socketio, chat_manager, collab_manager):
    """Register connection-related SocketIO events"""

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        client_id = request.sid
        username = request.args.get('username', 'Gast')
        logging.info(f'Client {client_id} connected')

        # Get existing chat history for the client
        existing_history = chat_manager.get_chat_history(client_id)

        # Only send welcome message if there's no existing history
        if not existing_history:
            initial_message = f"Hallo {username}! Wie kann ich dir helfen?"
            chat_manager.add_to_history(client_id, 'bot', initial_message)
            emit('chat_response', {
                'content': initial_message,
                'complete': True,
                'sender': 'bot'
            }, room=client_id)

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        user_id = request.sid

        # Verlasse alle aktiven Prompt-Räume
        if user_id in collab_manager.user_rooms:
            for room in collab_manager.user_rooms[user_id].copy():
                prompt_id = room.split('_')[1]  # Extract prompt_id from room name
                collaborators = collab_manager.leave_prompt(prompt_id, user_id)

                emit('collaborator_left', {
                    'collaborators': collaborators,
                    'leftuser_id': user_id
                }, room=room)

        # Bestehende Chat-Cleanup-Logik
        chat_manager.clear_history(request.sid)
        logging.info(f'Client {request.sid} disconnected')
