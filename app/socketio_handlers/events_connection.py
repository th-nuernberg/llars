"""
SocketIO Connection Events
Handles client connection and disconnection.

Note: Collaborative editing for Prompt Engineering is handled by the dedicated
YJS WebSocket server (yjs-server/) which provides CRDT-based real-time sync.
"""

import logging
from flask import request
from flask_socketio import emit

from socketio_handlers.events_rag import unregister_queue_subscriber
from services.presence_service import get_presence_service


def register_connection_events(socketio, chat_manager):
    """
    Register connection-related SocketIO events.

    Events:
        connect: Client connects to Socket.IO server
        disconnect: Client disconnects from Socket.IO server
    """

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
        chat_manager.clear_history(request.sid)
        unregister_queue_subscriber(request.sid)
        try:
            service = get_presence_service()
            payload = service.remove_socket(request.sid)
            if payload:
                socketio.emit("presence:update", payload, room="presence_admin")
        except Exception:
            pass
        logging.info(f'Client {request.sid} disconnected')
