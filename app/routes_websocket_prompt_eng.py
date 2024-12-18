import json
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
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
        user_id = data.get('user_id')  # Client übergibt user_id optional
        s_id = request.sid
        logging.info(f"Client connected with user ID {user_id}, socket ID {s_id}")
        emit('pe_connected', {
            'message': 'Connected successfully',
            'user_id': s_id,  # Wir nutzen hier einfach s_id als user_id
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
                'content': room_data['content'],
                'users': list(room_data['users'])
            }, room=room_id)

    @socketio.on('pe_text_update')
    def handle_text_update(data):
        user_id = request.sid
        room_id = data.get('room')
        block_id = data.get('blockId')
        new_content = data.get('content')

        # Raumdaten holen
        room_data = pe_rooms.get_room_data(room_id)
        if not room_data:
            return

        # Bisherige Inhalte holen
        content = room_data.get('content', {})
        if 'blocks' not in content:
            content['blocks'] = {}

        # Block aktualisieren oder anlegen
        # Wenn der Block bereits existiert, wird nur der Inhalt aktualisiert
        # Ist er neu, wird er hinzugefügt
        if block_id in content['blocks']:
            content['blocks'][block_id]['content'] = new_content
        else:
            # Falls der Block neu ist, fügen wir ihn mit default-Werten an.
            # Die Position könnte hier z. B. die nächste freie Position sein,
            # oder du bestimmst sie anderweitig.
            new_position = len(content['blocks'])
            content['blocks'][block_id] = {
                'content': new_content,
                'position': new_position
            }

        # Raumcontent aktualisieren
        pe_rooms.update_room_content(room_id, content)

        # Nach dem Update ist der Raumcontent in room_data['content'] bereits aktualisiert
        # Jetzt senden wir den kompletten Content an alle im Raum
        emit('pe_text_update', room_data['content'], room=room_id, include_self=False)

