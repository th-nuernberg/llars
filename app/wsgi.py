"""
WSGI entry point for Gunicorn with eventlet.

IMPORTANT: eventlet.monkey_patch() MUST be called before any other imports!
This is critical for proper socket handling.

NOTE: We do NOT patch DNS (no dns=True) because it causes issues in Docker
with container name resolution. The limited patching below works correctly.
"""

# Monkey-patch MUST be first!
# Use limited patching to avoid DNS issues in Docker
import eventlet
eventlet.monkey_patch(os=True, select=True, socket=True, thread=True, time=True)

# Now we can safely import the app
from main import app, socketio

# For gunicorn: gunicorn --worker-class eventlet -w 1 wsgi:app
