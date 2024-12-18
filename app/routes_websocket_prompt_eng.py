import json
from flask import request
from flask_socketio import SocketIO, emit, send, join_room, leave_room
import logging
from db.db import db
from pe_rooms import PeRooms


def configure_websocket_prompt_eng(socketio):
    """
    Configure WebSocket routes for collaborative prompt editing.
    """

    pe_rooms = PeRooms(db)

    @socketio.on('pe_connect')
    def handle_connect(data):
        """Handle client connection to WebSocket."""
        user_id = data.get('user_id')  # entspricht dem Client-seitigen { user_id: user }
        s_id = request.sid
        logging.info(f"Client connected with user ID {user_id}, socket ID {s_id}")
        emit('pe_connected', {
            'message': 'Connected successfully',
            'user_id': user_id,
            'sid': s_id
        })

    @socketio.on('pe_join_room')
    def handle_join_room(data):
        prompt_id = data.get('prompt_id')
        user_id = request.sid
        logging.info(f"User {user_id} joined room for prompt {prompt_id}")
        room_data, room_id = pe_rooms.join_room(prompt_id, user_id)
        if room_data:
            join_room(room_id)
            emit('pe_joined_room', {
                'room': room_id,
                'content': room_data['content']
            }, room=room_id)

