"""
Chatbot Build Monitor Service.

Handles monitoring of chatbot build processes.
Responsible for:
- Monitoring crawl jobs
- Monitoring embedding processes
- Transitioning between build stages
- Status reporting and diagnostics
"""

import logging
import time
import threading
from typing import Dict, Any

from db.db import db
from db.tables import (
    Chatbot, RAGCollection, CollectionDocumentLink,
    ChatbotConversation, ChatbotMessage
)

logger = logging.getLogger(__name__)


class ChatbotBuildMonitor:
    """Handles monitoring of chatbot build processes."""

    # Timeout and polling settings
    CRAWL_TIMEOUT_SECONDS = 600  # 10 minutes
    EMBEDDING_TIMEOUT_SECONDS = 1800  # 30 minutes
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

                while elapsed < ChatbotBuildMonitor.CRAWL_TIMEOUT_SECONDS:
                    status = crawler_service.get_job_status(job_id)

                    if not status:
                        logger.warning(f"[ChatbotBuildMonitor] Job {job_id} not found")
                        break

                    if status.get('status') == 'completed':
                        logger.info(f"[ChatbotBuildMonitor] Crawl completed for chatbot {chatbot_id}")

                        # Transition to embedding
                        chatbot = Chatbot.query.get(chatbot_id)
                        if chatbot:
                            chatbot.build_status = 'embedding'
                            db.session.commit()

                            # Start embedding
                            ChatbotBuildMonitor.start_embedding(app, chatbot_id, collection_id)
                        return

                    elif status.get('status') == 'failed':
                        logger.error(f"[ChatbotBuildMonitor] Crawl failed for chatbot {chatbot_id}: {status.get('error')}")
                        ChatbotBuildMonitor._set_error_status(
                            chatbot_id,
                            status.get('error', 'Crawl failed')
                        )
                        return

                    elif status.get('status') == 'cancelled':
                        logger.info(f"[ChatbotBuildMonitor] Crawl cancelled for chatbot {chatbot_id}")
                        ChatbotBuildMonitor._set_paused_status(chatbot_id, 'Crawl was cancelled')
                        return

                    time.sleep(ChatbotBuildMonitor.POLL_INTERVAL_SECONDS)
                    elapsed += ChatbotBuildMonitor.POLL_INTERVAL_SECONDS

                # Timeout reached
                logger.error(f"[ChatbotBuildMonitor] Crawl timeout for chatbot {chatbot_id}")
                ChatbotBuildMonitor._set_error_status(chatbot_id, 'Crawl timeout')

            except Exception as e:
                logger.error(f"[ChatbotBuildMonitor] Monitor error for chatbot {chatbot_id}: {e}")
                ChatbotBuildMonitor._set_error_status(chatbot_id, str(e)[:500])

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

                logger.debug(f"[ChatbotBuildMonitor] Starting monitor loop for chatbot {chatbot_id}")

                while elapsed < ChatbotBuildMonitor.EMBEDDING_TIMEOUT_SECONDS:
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

                        # Copy brand color from collection to chatbot if available
                        if collection.color and not chatbot.color:
                            chatbot.color = collection.color
                            logger.info(f"[ChatbotBuildMonitor] Set chatbot color from collection: {collection.color}")

                        # Generate icon using LLM
                        try:
                            from .chatbot_field_generator import ChatbotFieldGenerator
                            icon_result = ChatbotFieldGenerator.generate_icon(chatbot_id)
                            if icon_result.get('success') and icon_result.get('value'):
                                chatbot.icon = icon_result['value']
                                logger.info(f"[ChatbotBuildMonitor] Generated icon for chatbot: {chatbot.icon}")
                        except Exception as e:
                            logger.warning(f"[ChatbotBuildMonitor] Icon generation failed, using default: {e}")
                            chatbot.icon = 'mdi-robot'

                        # Transition to configuring
                        chatbot.build_status = 'configuring'
                        chatbot.build_error = None
                        db.session.commit()

                        logger.info(f"[ChatbotBuildMonitor] Chatbot {chatbot_id} transitioned to 'configuring' (color={chatbot.color}, icon={chatbot.icon})")
                        return

                    elif collection.embedding_status == 'failed':
                        logger.error(f"[ChatbotBuildMonitor] Embedding failed for chatbot {chatbot_id}")
                        ChatbotBuildMonitor._set_error_status(
                            chatbot_id,
                            collection.embedding_error or 'Embedding failed'
                        )
                        return

                    time.sleep(ChatbotBuildMonitor.POLL_INTERVAL_SECONDS)
                    elapsed += ChatbotBuildMonitor.POLL_INTERVAL_SECONDS

                # Timeout reached
                logger.error(f"[ChatbotBuildMonitor] Embedding timeout for chatbot {chatbot_id}")
                ChatbotBuildMonitor._set_error_status(chatbot_id, 'Embedding timeout')

            except Exception as e:
                logger.error(f"[ChatbotBuildMonitor] Embedding monitor error for chatbot {chatbot_id}: {e}")
                ChatbotBuildMonitor._set_error_status(chatbot_id, str(e)[:500])

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
