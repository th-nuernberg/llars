"""
WSGI entry point for Gunicorn with eventlet.

IMPORTANT: eventlet.monkey_patch() MUST be called before any other imports!
This is critical for proper DNS resolution and socket handling in Docker.
"""

# Monkey-patch MUST be first!
import eventlet
eventlet.monkey_patch()

# Now we can safely import the app
from main import app, socketio

# For gunicorn: gunicorn --worker-class eventlet -w 1 wsgi:app
