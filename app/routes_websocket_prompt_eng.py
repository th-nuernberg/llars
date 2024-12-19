# websocket.py
import json
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
from db.db import db
from pe_rooms import PeRooms

def configure_websocket_prompt_eng(socketio):
    """
    Configure WebSocket routes for collaborative prompt editing.
    Uses the namespace '/prompt-engineering' for all routes.
    """
    namespace = '/pe'
    pe_rooms = PeRooms(db)

    @socketio.on('disconnect', namespace=namespace)
    def handle_disconnect():
        user_id = request.sid
        success, room_id, remaining_users = pe_rooms.leave_room(user_id)
        if success:
            # Physisch den Socket-Room verlassen
            leave_room(room_id)
            logging.info(f"User {user_id} disconnected and was removed from room {room_id}.")
            # Anderen Benutzern im Raum Bescheid geben
            emit('pe_user_left', {
                'room': room_id,
                'users': [{'id': uid, 'username': uname} for uid, uname in remaining_users.items()]
            }, room=room_id, namespace=namespace)

    @socketio.on('pe_connect', namespace=namespace)
    def handle_connect(data):
        username = data.get('username', 'Unknown')
        s_id = request.sid
        # Username zuordnen
        pe_rooms.usernames[s_id] = username
        logging.info(f"Client connected with username {username}, socket ID {s_id}")
        emit('pe_connected', {
            'message': 'Connected successfully',
            'user_id': s_id,
            'sid': s_id
        }, namespace=namespace)

    @socketio.on('pe_join_room', namespace=namespace)
    def handle_join_room(data):
        prompt_id = data.get('prompt_id')
        user_id = request.sid
        logging.info(f"User {user_id} attempts to join room for prompt {prompt_id}")
        room_data, room_id = pe_rooms.join_room(prompt_id, user_id)
        if room_data:
            join_room(room_id)
            # Nutzerliste extrahieren
            users_list = [{'id': u_id, 'username': uname} for u_id, uname in room_data['users'].items()]
            # Cursorinformationen hinzufügen
            cursors = room_data.get('cursors', {})
            emit('pe_joined_room', {
                'room': room_id,
                'content': room_data['content'],
                'users': users_list,
                'cursors': cursors
            }, room=room_id, namespace=namespace)

    @socketio.on('pe_leave_room', namespace=namespace)
    def handle_leave_room():
        user_id = request.sid
        success, room_id, remaining_users = pe_rooms.leave_room(user_id)
        if success:
            # Physisch den Socket-Room verlassen
            leave_room(room_id)
            logging.info(f"User {user_id} left room {room_id}")
            # Anderen Benutzern im Raum Bescheid geben
            emit('pe_user_left', {
                'room': room_id,
                'users': [{'id': uid, 'username': uname} for uid, uname in remaining_users.items()]
            }, room=room_id, namespace=namespace)

    @socketio.on('pe_text_update', namespace=namespace)
    def handle_text_update(data):
        user_id = request.sid
        room_id = data.get('room')
        block_id = data.get('blockId')
        new_content = data.get('content')

        room_data = pe_rooms.get_room_data(room_id)
        if not room_data:
            return
        logging.info(f"Room Data: {room_data}")

        # Aktuelle Inhalte holen
        content = room_data.get('content', {})
        if 'blocks' not in content:
            content['blocks'] = {}

        # Block aktualisieren (falls bereits existiert) oder neu anlegen
        if block_id in content['blocks']:
            content['blocks'][block_id]['content'] = new_content
        else:
            new_position = len(content['blocks'])
            content['blocks'][block_id] = {
                'content': new_content,
                'position': new_position
            }

        pe_rooms.update_room_content(room_id, content)
        # An alle im Raum senden (außer dem Absender)
        emit('pe_text_update', room_data['content'], room=room_id, include_self=False, namespace=namespace)

    @socketio.on('pe_update_blocks', namespace=namespace)
    def handle_update_blocks(data):
        """
        Erwartetes Datenformat:
        {
          "room": "room_1",
          "updates": {
            "AvoidFormalities": { "new_position": 1, "content": "Neuer Inhalt" },
            "Context": { "new_position": 2 },
            "NewBlock": { "new_position": 3, "content": "Dies ist ein neuer Block" }
          }
        }
        """
        user_id = request.sid
        room_id = data.get('room')
        updates = data.get('updates', {})

        room_data = pe_rooms.get_room_data(room_id)
        logging.info(f"Room Data: {room_data}")
        if not room_data:
            return

        # Bestehende Inhalte laden
        content = room_data.get('content', {})
        old_blocks = content.get('blocks', {})

        new_blocks = {}
        # Durch die Updates iterieren
        for block_name, block_update in updates.items():
            new_pos = block_update.get('new_position')
            # Wenn kein Inhalt mitgeschickt, alten Inhalt beibehalten oder leer
            new_content = block_update.get('content', old_blocks.get(block_name, {}).get('content', ''))

            new_blocks[block_name] = {
                'content': new_content,
                'position': new_pos
            }

        # Alte Blöcke, die nicht mehr in updates sind, entfallen automatisch
        content['blocks'] = new_blocks

        # Raum aktualisieren
        pe_rooms.update_room_content(room_id, content)

        # Aktualisierte Inhalte an alle im Raum senden
        emit('pe_blocks_updated', room_data['content'], room=room_id, include_self=False, namespace=namespace)

    # NEUER EVENT: Cursor Update
    @socketio.on('pe_cursor_update', namespace=namespace)
    def handle_cursor_update(data):
        """
        Erwartetes Datenformat:
        {
          "room": "room_1",
          "block_id": "Block123",
          "position": 15
        }
        """
        user_id = request.sid
        room_id = data.get('room')
        block_id = data.get('block_id')
        position = data.get('position', 0)

        if not room_id or not block_id:
            return

        success = pe_rooms.update_cursor_position(room_id, user_id, block_id, position)
        if not success:
            return

        # Aktualisierte Cursor-Infos an alle anderen User im Raum senden
        room_data = pe_rooms.get_room_data(room_id)
        emit('pe_cursor_updated', {
            'cursors': room_data['cursors']
        }, room=room_id, include_self=False, namespace=namespace)
