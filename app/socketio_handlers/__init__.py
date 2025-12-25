"""
SocketIO Handlers Module
========================

Centralized Socket.IO event handlers for real-time features.

Architecture:
    - Flask Socket.IO handles: Chat, Judge, OnCoCo, Crawler, RAG, Prompts, Ranker
    - YJS Server (yjs-server/) handles: Collaborative Prompt Editing (CRDT-based)

Event Namespaces:
    - judge:*     - LLM-as-Judge evaluation sessions
    - rag:*       - RAG document processing queue
    - ranker:*    - Ranking statistics updates
    - prompts:*   - User prompt list updates
    - crawler:*   - Web crawler job progress
    - oncoco:*    - OnCoCo analysis progress
    - (default)   - Chat streaming, connection events
"""

import logging
from .chat_manager import ChatManager
from .events_connection import register_connection_events
from .events_chat import register_chat_events
from .events_chatbot import register_chatbot_events
from .events_judge import register_judge_events
from .events_oncoco import register_oncoco_events
from .events_crawler import register_crawler_events
from .events_prompts import register_prompts_events
from .events_rag import register_rag_events
from .events_ranker import register_ranker_events
from .events_docker_monitor import register_docker_monitor_events
from .events_comparison import register_comparison_events
from .events_markdown_collab import register_markdown_collab_events
from .events_latex_collab import register_latex_collab_events
from .events_prompt_collab import register_prompt_collab_events

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

    Registered Event Handlers:
        Connection (events_connection.py):
            - connect: Client connection with welcome message
            - disconnect: Client disconnection and cleanup

        Chat (events_chat.py):
            - chat_stream: Streaming chat with RAG integration
            - test_prompt_stream: Test prompt execution

        Chatbot (events_chatbot.py):
            - chatbot:stream: Streaming chat with specific chatbot (Multi-Collection RAG)
            - chatbot:join: Join chatbot session room
            - chatbot:leave: Leave chatbot session room

        Judge (events_judge.py):
            - judge:join_session: Join evaluation session room
            - judge:leave_session: Leave evaluation session room
            - judge:get_status: Request current session status

        RAG (events_rag.py):
            - rag:subscribe_queue: Subscribe to processing queue updates
            - rag:unsubscribe_queue: Unsubscribe from queue updates

        Ranker (events_ranker.py):
            - ranker:subscribe: Subscribe to ranking stat updates
            - ranker:unsubscribe: Unsubscribe from stat updates

        Prompts (events_prompts.py):
            - prompts:subscribe: Subscribe to user's prompt updates
            - prompts:unsubscribe: Unsubscribe from prompt updates

        Crawler (events_crawler.py):
            - crawler:join_session: Join crawler job session
            - crawler:leave_session: Leave crawler job session
            - crawler:subscribe_jobs: Subscribe to all jobs updates
            - crawler:unsubscribe_jobs: Unsubscribe from jobs updates
            - crawler:get_status: Request job status

        OnCoCo (events_oncoco.py):
            - oncoco:join_analysis: Join analysis session
            - oncoco:leave_analysis: Leave analysis session
            - oncoco:get_status: Request analysis status
    """
    # Initialize managers
    chat_manager = ChatManager(verbose=verbose)

    # Register event handlers
    register_connection_events(socketio, chat_manager)
    register_chat_events(socketio, chat_manager)
    register_chatbot_events(socketio)
    register_judge_events(socketio)
    register_oncoco_events(socketio)
    register_crawler_events(socketio)
    register_prompts_events(socketio)
    register_rag_events(socketio)
    register_ranker_events(socketio)
    register_docker_monitor_events(socketio)
    register_comparison_events(socketio)
    register_markdown_collab_events(socketio)
    register_latex_collab_events(socketio)
    register_prompt_collab_events(socketio)

    logging.info("SocketIO routes configured successfully")


__all__ = [
    'configure_socket_routes',
    'ChatManager'
]
