"""
WSGI entry point for Gunicorn with gevent.

IMPORTANT: gevent.monkey.patch_all() MUST be called before any other imports!
This patches standard library modules to be cooperative (non-blocking).

Gevent is preferred over eventlet for Docker deployments because:
- Better DNS resolution compatibility with Docker networking
- More stable WebSocket support via gevent-websocket
- Active maintenance and Python 3.10+ support
"""

# Monkey-patch MUST be first!
from gevent import monkey
monkey.patch_all()

# Now we can safely import the app
from main import app, socketio

# For gunicorn with gevent-websocket worker:
# gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker wsgi_gevent:app
