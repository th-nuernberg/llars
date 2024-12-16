import json
from flask import request
from flask_socketio import SocketIO, emit, send, join_room, leave_room
import logging


class CollaborativePromptEditor:
    def __init__(self, room):
        self.json_prompt = ""
        self.room = ""

    def set_prompt(self, prompt):
        self.json_prompt = prompt

    def get_prompt(self):
        return self.json_prompt

def configure_websocket_prompt_eng(socketio):
    """
    Configure WebSocket routes for collaborative prompt editing using Yjs.
    """
    prompt_editor = CollaborativePromptEditor(room="room-1")
    @socketio.on('connect_prompt_eng')
    def handle_connect():
        """
        Handle client connection to WebSocket.
        """
        # Optionally, retrieve user information or other connection-related data
        user_id = request.sid  # This gives the session ID of the client
        logging.info(f"Client connected to Yjs prompt collaboration with user ID {user_id}")

        # Send a response back to the client confirming the connection
        emit('connection_response', {'message': 'Connected successfully', 'user_id': user_id})
        join_room(user_id)

    @socketio.on('disconnect_eng')
    def handle_disconnect():
        print("User disconnected")

    @socketio.on('join_eng')
    def handle_join(room):
        """Der Benutzer tritt einem Raum bei."""
        room = room.get("room")
        join_room(room)
        logging.info(f"User joined room: {room}")

    @socketio.on('leave_eng')
    def handle_leave(room):
        """Der Benutzer verlässt einen Raum."""
        leave_room(room)
        logging.info(f"User left room: {room}")
        send(f"User has left the room {room}", room=room)

    @socketio.on('message')
    def handle_message(message):
        """Nachricht an alle in einem bestimmten Raum senden."""
        logging.info(f"Received message: {message}")
        send(message, broadcast=True)

    @socketio.on("update_text")
    def handle_update_text(data):
        """Aktualisiert den Text im Editor."""
        logging.info(f"Received text update: {data}")
        room = data.get("room")
        text = data.get("newText")
        payload = {"newText": text}
        emit("text_update", payload, to=room)


