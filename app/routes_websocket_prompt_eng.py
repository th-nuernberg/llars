import json
from flask import request
from flask_socketio import emit, join_room, leave_room
from typing import Dict, Set, List

# Statt YDoc-Objekte speichern wir die Updates als Liste
document_updates: Dict[str, List[bytes]] = {}
room_participants: Dict[str, Set[str]] = {}

def configure_websocket_prompt_eng(socketio):
    @socketio.on('connect')
    def handle_connect():
        print(f"Client connected: {request.sid}")

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f"Client disconnected: {request.sid}")
        for room in room_participants:
            if request.sid in room_participants[room]:
                room_participants[room].remove(request.sid)

    @socketio.on('join_room')
    def handle_join_room(room):
        join_room(room)
        if room not in room_participants:
            room_participants[room] = set()
        room_participants[room].add(request.sid)

        # Initialisiere Updates-Liste falls noch nicht vorhanden
        if room not in document_updates:
            document_updates[room] = []

        # Sende alle bisherigen Updates an den neuen Client
        for update in document_updates[room]:
            emit('update_document', list(update), to=request.sid)

        print(f"Client {request.sid} joined room: {room}")

    @socketio.on('leave_room')
    def handle_leave_room(room):
        leave_room(room)
        if room in room_participants and request.sid in room_participants[room]:
            room_participants[room].remove(request.sid)
        print(f"Client {request.sid} left room: {room}")

    @socketio.on('document_update')
    def handle_document_update(data):
        room = data['room']
        update = bytes(data['update'])

        # Speichere das Update
        if room in document_updates:
            document_updates[room].append(update)

        # Sende das Update an alle anderen Clients im Raum
        emit('update_document', list(update), to=room, skip_sid=request.sid)