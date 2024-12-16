import json
from flask import request
from flask_socketio import SocketIO, emit, send, join_room, leave_room
import logging


class RoomManager:
    def __init__(self):
        # Dictionary to store room-specific data
        self.rooms = {}

    def create_room(self, room_name):
        """Create a new room if it doesn't exist"""
        if room_name not in self.rooms:
            self.rooms[room_name] = {
                'prompt': "",  # Stored prompt for the room
                'users': set(),  # Users in the room
                'messages': [],  # Message history
                'last_updated': None  # Timestamp of last update
            }

    def add_user_to_room(self, room_name, user_id):
        """Add a user to a specific room"""
        if room_name not in self.rooms:
            self.create_room(room_name)
        self.rooms[room_name]['users'].add(user_id)

    def remove_user_from_room(self, room_name, user_id):
        """Remove a user from a specific room"""
        if room_name in self.rooms and user_id in self.rooms[room_name]['users']:
            self.rooms[room_name]['users'].remove(user_id)

    def update_room_prompt(self, room_name, prompt):
        """Update the prompt for a specific room"""
        if room_name in self.rooms:
            self.rooms[room_name]['prompt'] = prompt

    def get_room_prompt(self, room_name):
        """Get the prompt for a specific room"""
        return self.rooms.get(room_name, {}).get('prompt', '')

    def get_room_users(self, room_name):
        """Get users in a specific room"""
        return list(self.rooms.get(room_name, {}).get('users', set()))


def configure_websocket_prompt_eng(socketio):
    """
    Configure WebSocket routes for collaborative prompt editing.
    """
    # Create a global room manager
    room_manager = RoomManager()

    @socketio.on('connect_prompt_eng')
    def handle_connect():
        """Handle client connection to WebSocket."""
        user_id = request.sid
        logging.info(f"Client connected with user ID {user_id}")
        emit('connection_response', {'message': 'Connected successfully', 'user_id': user_id})

    @socketio.on('join_eng')
    def handle_join(data):
        """User joins a room."""
        room = data.get('room', 'default_room')
        user_id = request.sid

        # Add user to the room
        room_manager.add_user_to_room(room, user_id)
        join_room(room)

        # Get current prompt for the room (if any)
        current_prompt = room_manager.get_room_prompt(room)

        logging.info(f"User {user_id} joined room: {room}")

        # Emit current room state to the joined user
        emit('room_state', {
            'room': room,
            'users': room_manager.get_room_users(room),
            'prompt': current_prompt
        })

    @socketio.on('update_text')
    def handle_update_text(data):
        """Update text in a specific room."""
        room = data.get('room', 'default_room')
        text = data.get('newText', '')
        user_id = request.sid

        # Update room's prompt
        room_manager.update_room_prompt(room, text)

        # Broadcast update to all users in the room
        logging.info(f"Text update in room {room}: {text}")
        emit('text_update', {'newText': text}, to=room)

    @socketio.on('leave_eng')
    def handle_disconnect():
        """Handle user disconnection."""
        user_id = request.sid
        # Remove user from all rooms
        for room_name in list(room_manager.rooms.keys()):
            room_manager.remove_user_from_room(room_name, user_id)
        logging.info(f"User {user_id} disconnected")

    return room_manager  # Optionally return room manager for external access

