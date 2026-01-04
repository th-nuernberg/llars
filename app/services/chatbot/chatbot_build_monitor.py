"""
Chatbot Build Monitor Service.

Handles monitoring of chatbot build processes.
Responsible for:
- Monitoring crawl jobs
- Monitoring embedding processes
- Transitioning between build stages
- Status reporting and diagnostics
- Updating Redis wizard sessions for real-time sync
"""

import logging
import time
import threading
from typing import Dict, Any

from db.database import db
from db.tables import (
    Chatbot, RAGCollection, CollectionDocumentLink,
    ChatbotConversation, ChatbotMessage
)
from services.system_settings_service import get_crawl_timeout, get_embedding_timeout

logger = logging.getLogger(__name__)


def _update_wizard_session(chatbot_id: int, status: str, error_message: str = None, emit_event: bool = True):
    """
    Update the Redis wizard session and optionally emit Socket.IO event.

    This is a helper function to avoid circular imports.
    """
    try:
        from services.wizard import get_wizard_session_service
        from socketio_handlers.events_wizard import emit_wizard_status_changed
        from main import socketio

        wizard_service = get_wizard_session_service()
        session = wizard_service.get_session(chatbot_id)

        if session:
            wizard_service.transition_status(chatbot_id, status, error_message)

            if emit_event:
                step = wizard_service.STATUS_TO_STEP.get(status)
                emit_wizard_status_changed(socketio, chatbot_id, status, step)

    except Exception as e:
        logger.warning(f"[ChatbotBuildMonitor] Failed to update wizard session: {e}")


class ChatbotBuildMonitor:
    """Handles monitoring of chatbot build processes."""

    # Polling interval (timeouts are loaded from system_settings DB table)
    POLL_INTERVAL_SECONDS = 2  # Check every 2 seconds

    @staticmethod
    def monitor_crawl(app, chatbot_id: int, collection_id: int, job_id: str):
        """
        Monitor the crawl job and transition to embedding when done.

        This runs in a background thread and polls the crawler service
        for completion status.

        Args:
            app: Flask application context
            chatbot_id: The chatbot ID
            collection_id: The collection ID
            job_id: The crawler job ID
        """
        from services.crawler.web_crawler import crawler_service

        with app.app_context():
            try:
                elapsed = 0
                crawl_timeout = get_crawl_timeout()
                logger.info(f"[ChatbotBuildMonitor] Crawl timeout set to {crawl_timeout}s ({crawl_timeout // 60} min)")

                while elapsed < crawl_timeout:
                    status = crawler_service.get_job_status(job_id)

                    if not status:
                        # Job not found yet - this can happen during startup or long exploration phase
                        # Keep waiting, don't treat as error
                        logger.debug(f"[ChatbotBuildMonitor] Job {job_id} not found yet, waiting...")
                        time.sleep(ChatbotBuildMonitor.POLL_INTERVAL_SECONDS)
                        elapsed += ChatbotBuildMonitor.POLL_INTERVAL_SECONDS
                        continue

                    job_status = status.get('status')

                    # Valid in-progress states: queued, planning, running
                    if job_status in ('queued', 'planning', 'running'):
                        # Still in progress, keep monitoring
                        time.sleep(ChatbotBuildMonitor.POLL_INTERVAL_SECONDS)
                        elapsed += ChatbotBuildMonitor.POLL_INTERVAL_SECONDS
                        continue

                    if job_status == 'completed':
                        logger.info(f"[ChatbotBuildMonitor] Crawl completed for chatbot {chatbot_id}")

                        # Transition to embedding
                        chatbot = Chatbot.query.get(chatbot_id)
                        if chatbot:
                            collection = RAGCollection.query.get(collection_id)
                            if collection and collection.color and (not chatbot.color or chatbot.color == '#5d7a4a'):
                                chatbot.color = collection.color
                                logger.info(
                                    f"[ChatbotBuildMonitor] Set chatbot color from crawled brand color: {collection.color}"
                                )
                            chatbot.build_status = 'embedding'
                            db.session.commit()

                            # Update Redis session and emit event
                            _update_wizard_session(chatbot_id, 'embedding')

                            # Start embedding
                            ChatbotBuildMonitor.start_embedding(app, chatbot_id, collection_id)
                        return

                    elif job_status == 'failed':
                        logger.error(f"[ChatbotBuildMonitor] Crawl failed for chatbot {chatbot_id}: {status.get('error')}")
                        error_msg = status.get('error', 'Crawl failed')
                        ChatbotBuildMonitor._set_error_status(chatbot_id, error_msg)

                        # Update Redis session and emit error event
                        _update_wizard_session(chatbot_id, 'error', error_msg)
                        return

                    elif job_status == 'cancelled':
                        logger.info(f"[ChatbotBuildMonitor] Crawl cancelled for chatbot {chatbot_id}")
                        ChatbotBuildMonitor._set_paused_status(chatbot_id, 'Crawl was cancelled')

                        # Update Redis session and emit paused event
                        _update_wizard_session(chatbot_id, 'paused', 'Crawl was cancelled')
                        return

                    else:
                        # Unknown status, log and continue monitoring
                        logger.warning(f"[ChatbotBuildMonitor] Unknown job status '{job_status}' for chatbot {chatbot_id}")
                        time.sleep(ChatbotBuildMonitor.POLL_INTERVAL_SECONDS)
                        elapsed += ChatbotBuildMonitor.POLL_INTERVAL_SECONDS

                # Timeout reached
                logger.error(f"[ChatbotBuildMonitor] Crawl timeout for chatbot {chatbot_id}")
                ChatbotBuildMonitor._set_error_status(chatbot_id, 'Crawl timeout')

                # Update Redis session and emit error event
                _update_wizard_session(chatbot_id, 'error', 'Crawl timeout')

            except Exception as e:
                logger.error(f"[ChatbotBuildMonitor] Monitor error for chatbot {chatbot_id}: {e}")
                error_msg = str(e)[:500]
                ChatbotBuildMonitor._set_error_status(chatbot_id, error_msg)

                # Update Redis session and emit error event
                _update_wizard_session(chatbot_id, 'error', error_msg)

    @staticmethod
    def start_embedding(app, chatbot_id: int, collection_id: int):
        """
        Start embedding process after crawl.

        Args:
            app: Flask application context
            chatbot_id: The chatbot ID
            collection_id: The collection ID
        """
        try:
            from services.rag.collection_embedding_service import get_collection_embedding_service

            logger.info(f"[ChatbotBuildMonitor] Starting embedding for chatbot {chatbot_id}, collection {collection_id}")

            service = get_collection_embedding_service()
            result = service.start_embedding(collection_id)
            if not result.get('success'):
                raise ValueError(result.get('error', 'Embedding start failed'))
            if result.get('message'):
                logger.info(f"[ChatbotBuildMonitor] {result.get('message')}")

            # Start a thread to monitor embedding completion
            logger.info(f"[ChatbotBuildMonitor] Starting embedding monitor thread for chatbot {chatbot_id}")
            thread = threading.Thread(
                target=ChatbotBuildMonitor.monitor_embedding,
                args=(app, chatbot_id, collection_id),
                daemon=True
            )
            thread.start()
            logger.info(f"[ChatbotBuildMonitor] Embedding monitor thread started for chatbot {chatbot_id}")

        except Exception as e:
            logger.error(f"[ChatbotBuildMonitor] Embedding error: {e}")
            ChatbotBuildMonitor._set_error_status(chatbot_id, f"Embedding failed: {str(e)}")

    @staticmethod
    def monitor_embedding(app, chatbot_id: int, collection_id: int):
        """
        Monitor the embedding process and transition to configuring when done.

        Args:
            app: Flask application context
            chatbot_id: The chatbot ID
            collection_id: The collection ID
        """
        logger.info(f"[ChatbotBuildMonitor] Embedding monitor running for chatbot {chatbot_id}")

        with app.app_context():
            try:
                elapsed = 0
                embedding_timeout = get_embedding_timeout()
                logger.info(f"[ChatbotBuildMonitor] Embedding timeout set to {embedding_timeout}s ({embedding_timeout // 60} min)")

                while elapsed < embedding_timeout:
                    # Force fresh read from database by closing and re-opening session
                    db.session.rollback()  # Rollback any uncommitted changes
                    db.session.close()     # Close the session to release connections

                    collection = RAGCollection.query.get(collection_id)
                    chatbot = Chatbot.query.get(chatbot_id)

                    status = collection.embedding_status if collection else 'N/A'
                    # Only log every 5th poll to reduce noise
                    if elapsed % (ChatbotBuildMonitor.POLL_INTERVAL_SECONDS * 5) == 0:
                        logger.info(f"[ChatbotBuildMonitor] Monitor poll: collection {collection_id} status={status}")

                    if not collection or not chatbot:
                        logger.warning(f"[ChatbotBuildMonitor] Collection or Chatbot not found")
                        return

                    # Check if chatbot was paused or errored
                    if chatbot.build_status in ('paused', 'error', 'ready'):
                        logger.info(f"[ChatbotBuildMonitor] Chatbot {chatbot_id} status changed to {chatbot.build_status}, stopping monitor")
                        return

                    if collection.embedding_status == 'completed':
                        logger.info(f"[ChatbotBuildMonitor] Embedding completed for chatbot {chatbot_id}, transitioning to configuring")

                        # Generate color and icon using the field generator
                        try:
                            from .chatbot_field_generator import ChatbotFieldGenerator

                            # Generate color (uses crawled brand color if available, else LLM)
                            color_result = ChatbotFieldGenerator.generate_color(chatbot_id)
                            if color_result.get('success') and color_result.get('value'):
                                chatbot.color = color_result['value']
                                logger.info(f"[ChatbotBuildMonitor] Set chatbot color: {chatbot.color} (source: {color_result.get('source', 'unknown')})")

                            # Generate icon using LLM
                            icon_result = ChatbotFieldGenerator.generate_icon(chatbot_id)
                            if icon_result.get('success') and icon_result.get('value'):
                                chatbot.icon = icon_result['value']
                                logger.info(f"[ChatbotBuildMonitor] Generated icon for chatbot: {chatbot.icon}")

                        except Exception as e:
                            logger.warning(f"[ChatbotBuildMonitor] Color/Icon generation failed, using defaults: {e}")
                            # Keep defaults if generation fails

                        # Transition to configuring
                        chatbot.build_status = 'configuring'
                        chatbot.build_error = None
                        db.session.commit()

                        # Update Redis session and emit status change
                        _update_wizard_session(chatbot_id, 'configuring')

                        logger.info(f"[ChatbotBuildMonitor] Chatbot {chatbot_id} transitioned to 'configuring' (color={chatbot.color}, icon={chatbot.icon})")
                        return

                    elif collection.embedding_status == 'failed':
                        logger.error(f"[ChatbotBuildMonitor] Embedding failed for chatbot {chatbot_id}")
                        error_msg = collection.embedding_error or 'Embedding failed'
                        ChatbotBuildMonitor._set_error_status(chatbot_id, error_msg)

                        # Update Redis session and emit error event
                        _update_wizard_session(chatbot_id, 'error', error_msg)
                        return

                    time.sleep(ChatbotBuildMonitor.POLL_INTERVAL_SECONDS)
                    elapsed += ChatbotBuildMonitor.POLL_INTERVAL_SECONDS

                # Timeout reached
                logger.error(f"[ChatbotBuildMonitor] Embedding timeout for chatbot {chatbot_id}")
                ChatbotBuildMonitor._set_error_status(chatbot_id, 'Embedding timeout')

                # Update Redis session and emit error event
                _update_wizard_session(chatbot_id, 'error', 'Embedding timeout')

            except Exception as e:
                logger.error(f"[ChatbotBuildMonitor] Embedding monitor error for chatbot {chatbot_id}: {e}")
                error_msg = str(e)[:500]
                ChatbotBuildMonitor._set_error_status(chatbot_id, error_msg)

                # Update Redis session and emit error event
                _update_wizard_session(chatbot_id, 'error', error_msg)

    @staticmethod
    def get_build_status(chatbot_id: int) -> Dict[str, Any]:
        """
        Get the current build status of a chatbot.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with build status and progress info

        Raises:
            ValueError: If chatbot not found
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        result = {
            'success': True,
            'chatbot_id': chatbot_id,
            'build_status': chatbot.build_status,
            'build_error': chatbot.build_error,
            'source_url': chatbot.source_url,
            'is_active': chatbot.is_active
        }

        # Add collection info if available
        if chatbot.primary_collection_id:
            collection = RAGCollection.query.get(chatbot.primary_collection_id)
            if collection:
                result['collection'] = {
                    'id': collection.id,
                    'name': collection.name,
                    'crawl_job_id': collection.crawl_job_id,
                    'embedding_status': collection.embedding_status,
                    'embedding_progress': collection.embedding_progress or 0,
                    'document_count': collection.document_count,
                    'total_chunks': collection.total_chunks
                }

        return result

    @staticmethod
    def get_admin_test_data(chatbot_id: int) -> Dict[str, Any]:
        """
        Get data for the admin test page.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with chatbot config, collection info, stats, and sample documents

        Raises:
            ValueError: If chatbot not found
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        result = {
            'success': True,
            'chatbot': {
                'id': chatbot.id,
                'name': chatbot.name,
                'display_name': chatbot.display_name,
                'system_prompt': chatbot.system_prompt,
                'welcome_message': chatbot.welcome_message,
                'fallback_message': chatbot.fallback_message,
                'build_status': chatbot.build_status,
                'source_url': chatbot.source_url,
                'temperature': chatbot.temperature,
                'max_tokens': chatbot.max_tokens,
                'rag_enabled': chatbot.rag_enabled,
                'rag_retrieval_k': chatbot.rag_retrieval_k,
                'rag_min_relevance': chatbot.rag_min_relevance
            },
            'collections': [],
            'stats': {
                'total_documents': 0,
                'total_chunks': 0,
                'total_embeddings': 0,
                'avg_response_time_ms': 0,
                'conversations_count': 0,
                'messages_count': 0
            },
            'sample_documents': [],
            'test_queries': []
        }

        # Get collections
        for assignment in chatbot.collections:
            collection = assignment.collection
            if collection:
                result['collections'].append({
                    'id': collection.id,
                    'name': collection.name,
                    'display_name': collection.display_name,
                    'document_count': collection.document_count or 0,
                    'embedding_status': collection.embedding_status,
                    'is_primary': assignment.is_primary
                })
                result['stats']['total_documents'] += collection.document_count or 0
                result['stats']['total_chunks'] += collection.total_chunks or 0

        result['stats']['total_embeddings'] = result['stats']['total_chunks']

        # Get conversation stats
        result['stats']['conversations_count'] = ChatbotConversation.query.filter_by(
            chatbot_id=chatbot_id
        ).count()
        result['stats']['messages_count'] = ChatbotMessage.query.join(ChatbotConversation).filter(
            ChatbotConversation.chatbot_id == chatbot_id
        ).count()

        # Get sample documents
        if chatbot.primary_collection_id:
            links = CollectionDocumentLink.query.filter_by(
                collection_id=chatbot.primary_collection_id
            ).limit(5).all()

            for link in links:
                doc = link.document
                if doc:
                    result['sample_documents'].append({
                        'id': doc.id,
                        'title': doc.title or doc.filename,
                        'excerpt': (doc.content[:200] + '...') if doc.content and len(doc.content) > 200 else doc.content,
                        'chunks_count': doc.chunk_count or 0
                    })

        # Generate test queries based on content
        if chatbot.source_url:
            result['test_queries'] = [
                f"Was ist {chatbot.display_name}?",
                "Welche Informationen findest du hier?",
                "Wie kann ich mehr erfahren?"
            ]

        return result

    @staticmethod
    def _set_error_status(chatbot_id: int, error_message: str):
        """
        Set chatbot to error status.

        Args:
            chatbot_id: The chatbot ID
            error_message: Error message
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if chatbot:
            chatbot.build_status = 'error'
            chatbot.build_error = error_message
            db.session.commit()

    @staticmethod
    def _set_paused_status(chatbot_id: int, message: str):
        """
        Set chatbot to paused status.

        Args:
            chatbot_id: The chatbot ID
            message: Pause message
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if chatbot:
            chatbot.build_status = 'paused'
            chatbot.build_error = message
            db.session.commit()
