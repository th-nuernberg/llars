import json
from flask import request
from flask_socketio import emit, join_room, leave_room
from typing import Dict, Set, List

document_updates: Dict[str, List[bytes]] = {}
room_participants: Dict[str, Set[str]] = {}
user_cursors: Dict[str, Dict] = {}  # Speichert Cursor-Positionen pro Raum


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
                # Entferne Cursor-Information
                if room in user_cursors and request.sid in user_cursors[room]:
                    del user_cursors[room][request.sid]

    @socketio.on('join_room')
    def handle_join_room(room):
        join_room(room)
        if room not in room_participants:
            room_participants[room] = set()
        room_participants[room].add(request.sid)

        if room not in document_updates:
            document_updates[room] = []

        for update in document_updates[room]:
            emit('update_document', list(update), to=request.sid)

        # Sende existierende Cursor-Positionen
        if room in user_cursors:
            for userId, cursorInfo in user_cursors[room].items():
                if userId != request.sid:
                    emit('cursor_update', cursorInfo, to=request.sid)

        print(f"Client {request.sid} joined room: {room}")

    @socketio.on('set_user_info')
    def handle_user_info(data):
        room = data['room']
        if room not in user_cursors:
            user_cursors[room] = {}
        user_cursors[room][request.sid] = {
            'userId': request.sid,
            'name': data['user']['name'],
            'color': data['user']['color']
        }

    @socketio.on('cursor_update')
    def handle_cursor_update(data):
        room = data['room']
        if room not in user_cursors:
            user_cursors[room] = {}

        # Aktualisiere Cursor-Information
        user_cursors[room][request.sid] = data

        # Sende an alle anderen im Raum
        emit('cursor_update', data, to=room, skip_sid=request.sid)

    @socketio.on('document_update')
    def handle_document_update(data):
        room = data['room']
        update = bytes(data['update'])

        if room in document_updates:
            document_updates[room].append(update)

        emit('update_document', list(update), to=room, skip_sid=request.sid)