from flask_socketio import emit, join_room, leave_room
from flask import request
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', "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"))
import os
import asyncio



def configure_socket_routes(socketio):
    @socketio.on('connect')
    def handle_connect():
        emit('welcome', {
            'message': 'Welcome to LLARS Chat!',
            'client_id': request.sid
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client {request.sid} disconnected')

    @socketio.on('chat_message')
    def handle_chat_message(data):
        user_message = data.get('message', '')
        client_id = request.sid

        # Start streaming response
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}],
        stream=True)

        # Stream the response
        collected_chunks = []
        collected_messages = []

        for chunk in response:
            chunk_message = chunk.choices[0].delta
            collected_chunks.append(chunk_message)

            # Extract the content from the chunk if it exists
            if 'content' in chunk_message:
                content = chunk_message['content']
                collected_messages.append(content)
                emit('chat_response', {
                    'content': content,
                    'complete': False
                }, room=client_id)

        # Send complete message flag
        emit('chat_response', {
            'content': ''.join(collected_messages),
            'complete': True
        }, room=client_id)

    @socketio.on('mock_chat')
    def handle_mock_chat(data):
        user_message = data.get('message', '')
        client_id = request.sid

        # Mock response broken into chunks
        response = "Let me simulate a streaming response... \n\nThis is a mock LLM response being streamed word by word. \nI'll add some artificial delays to make it look more realistic. \n\nThe message you sent was: " + user_message

        words = response.split()

        for word in words:
            emit('chat_response', {
                'content': word + ' ',
                'complete': False
            }, room=client_id)
            socketio.sleep(0.1)  # Add delay between words

        emit('chat_response', {
            'content': response,
            'complete': True
        }, room=client_id)