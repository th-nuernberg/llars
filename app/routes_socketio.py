# routes_socketio.py
from flask_socketio import emit, join_room, leave_room
from flask import request

def configure_socket_routes(socketio):
    @socketio.on('connect')
    def handle_connect():
        emit('welcome', {
            'message': 'Welcome to LLARS!',
            'client_id': request.sid
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client {request.sid} disconnected')

    @socketio.on('join_room')
    def on_join(data):
        room = data.get('room')
        join_room(room)
        emit('room_joined', {'room': room}, room=room)

    @socketio.on('message')
    def handle_message(data):
        print(f'Received message: {data}')
        emit('message', {
            'sender': request.sid,
            'content': data
        }, broadcast=True)