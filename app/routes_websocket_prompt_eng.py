import json
from flask import request
from flask_socketio import emit, join_room, leave_room
import y_py as Y
from typing import Dict, Set

# Store active rooms and their documents
rooms: Dict[str, Y.YDoc] = {}
# Store active users in rooms
room_users: Dict[str, Set[Dict]] = {}


def configure_websocket_prompt_eng(socketio):
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
        # Find and remove user from all rooms
        for room_id, users in room_users.items():
            users_to_remove = [u for u in users if u['socketId'] == request.sid]
            for user in users_to_remove:
                users.remove(user)
                emit('user-left', user['id'], room=room_id)

    @socketio.on('join-room')
    def handle_join_room(data):
        room_id = data['roomId']
        user = data['user']
        user['socketId'] = request.sid

        # Join Socket.IO room
        join_room(room_id)

        # Initialize room if it doesn't exist
        if room_id not in rooms:
            rooms[room_id] = Y.YDoc()
            room_users[room_id] = set()

        # Add user to room
        room_users[room_id].add(user)

        # Notify others in the room
        emit('user-joined', user, room=room_id)

        # Send current document state to the new user
        state = Y.encode_state_as_update(rooms[room_id])
        emit('doc-update', list(state))

        # Send list of current users to the new user
        emit('current-users', list(room_users[room_id]))

    @socketio.on('leave-room')
    def handle_leave_room(data):
        room_id = data['roomId']
        user_id = data['userId']

        if room_id in room_users:
            # Remove user from room
            room_users[room_id] = {u for u in room_users[room_id] if u['id'] != user_id}
            # Notify others
            emit('user-left', user_id, room=room_id)

        leave_room(room_id)

    @socketio.on('doc-update')
    def handle_doc_update(data):
        room_id = data['roomId']
        update = bytes(data['update'])

        if room_id in rooms:
            # Apply update to the server's document
            Y.apply_update(rooms[room_id], update)
            # Broadcast to all clients in the room except sender
            emit('doc-update', data['update'], room=room_id, skip_sid=request.sid)

    @socketio.on('cursor-update')
    def handle_cursor_update(data):
        room_id = data['roomId']
        # Broadcast cursor position to all clients in the room except sender
        emit('cursor-update', data, room=room_id, skip_sid=request.sid)

    @socketio.on('error')
    def handle_error(error):
        print(f"WebSocket error occurred: {error}")