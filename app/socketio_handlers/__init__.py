"""
SocketIO Handlers Module
Refactored from routes_socketio.py into focused modules.
"""

import logging
from .chat_manager import ChatManager
from .collaborative_manager import CollaborativeManager
from .events_connection import register_connection_events
from .events_collaboration import register_collaboration_events
from .events_chat import register_chat_events

# Enhanced logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def configure_socket_routes(socketio, verbose=True):
    """
    Configure all SocketIO routes and event handlers.

    Args:
        socketio: Flask-SocketIO instance
        verbose: Enable verbose logging for prompts and debugging

    Event Handlers Registered:
        Connection Events:
            - connect: Client connection
            - disconnect: Client disconnection

        Collaboration Events:
            - join_prompt: Join collaborative session
            - leave_prompt: Leave collaborative session
            - cursor_move: Cursor position updates
            - blocks_update: Block structure updates
            - content_change: Content modifications

        Chat Events:
            - chat_stream: Streaming chat with RAG
            - test_prompt_stream: Test prompt execution
    """
    # Initialize managers
    chat_manager = ChatManager(verbose=verbose)
    collab_manager = CollaborativeManager()

    # Register event handlers
    register_connection_events(socketio, chat_manager, collab_manager)
    register_collaboration_events(socketio, collab_manager)
    register_chat_events(socketio, chat_manager)

    logging.info("SocketIO routes configured successfully")


__all__ = [
    'configure_socket_routes',
    'ChatManager',
    'CollaborativeManager'
]
