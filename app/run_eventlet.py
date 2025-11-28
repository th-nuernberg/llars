"""
Eventlet runner for Flask-SocketIO.

IMPORTANT: eventlet.monkey_patch() MUST be called before any other imports!
This is critical for proper DNS resolution and socket handling.
"""

# Monkey-patch MUST be first!
# Use select_only=True to avoid patching DNS which can cause issues in Docker
import eventlet
eventlet.monkey_patch(os=True, select=True, socket=True, thread=True, time=True)

# Now we can safely import the app
from main import app, socketio

if __name__ == '__main__':
    print("Starting Flask with eventlet WebSocket support...")
    # Run with SocketIO (uses eventlet internally when async_mode='eventlet')
    socketio.run(
        app,
        host='0.0.0.0',
        port=8081,
        debug=True,
        use_reloader=False,  # eventlet doesn't support reloader
        log_output=True
    )
