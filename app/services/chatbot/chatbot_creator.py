"""
Chatbot Creator Service.

Handles chatbot creation, configuration, and finalization.
Responsible for:
- Creating draft chatbots from URLs
- Starting crawl processes
- Finalizing chatbot configuration
- Managing chatbot lifecycle (cancel, resume, status updates)
"""

import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from db.db import db
from db.tables import Chatbot, ChatbotCollection, RAGCollection
from db.models.llm_model import LLMModel

logger = logging.getLogger(__name__)


class ChatbotCreator:
    """Handles chatbot creation and lifecycle management."""

    @staticmethod
    def create_wizard_chatbot(url: str, username: str) -> Dict[str, Any]:
        """
        Start the chatbot creation wizard with a URL.

        Creates a draft chatbot and prepares for crawl process.

        Args:
            url: The source URL to crawl
            username: Username creating the chatbot

        Returns:
            Dict with chatbot info and status

        Raises:
            ValueError: If URL format is invalid
        """
        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception:
            raise ValueError("Invalid URL format")

        # Generate a unique name from the URL
        domain = parsed.netloc.replace('www.', '').replace('.', '_')
        base_name = f"bot_{domain}"
        name = base_name

        # Ensure unique name
        counter = 1
        while Chatbot.query.filter_by(name=name).first():
            name = f"{base_name}_{counter}"
            counter += 1

        # Create draft chatbot
        default_model = LLMModel.get_default_model(model_type=LLMModel.MODEL_TYPE_LLM)
        if not default_model:
            raise ValueError("No default LLM model configured in llm_models")
        chatbot = Chatbot(
            name=name,
            display_name=f"Chatbot for {parsed.netloc}",
            description=f"Auto-generated chatbot from {url}",
            system_prompt="Du bist ein hilfreicher Assistent.",
            model_name=default_model.model_id,
            build_status='draft',
            source_url=url,
            is_active=False,  # Not active until ready
            created_by=username
        )
        db.session.add(chatbot)
        db.session.commit()

        logger.info(f"[ChatbotCreator] Created draft chatbot {chatbot.id} for URL: {url}")

        return {
            'success': True,
            'chatbot_id': chatbot.id,
            'name': chatbot.name,
            'display_name': chatbot.display_name,
            'build_status': chatbot.build_status,
            'source_url': url
        }

    @staticmethod
    def start_crawl(
        chatbot_id: int,
        max_pages: int = 50,
        max_depth: int = 3,
        use_playwright: bool = True,
        use_vision_llm: bool = False,
        take_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Start crawling the source URL for a chatbot.

        Args:
            chatbot_id: The chatbot ID
            max_pages: Maximum pages to crawl
            max_depth: Maximum crawl depth
            use_playwright: Whether to use Playwright for JavaScript rendering
            use_vision_llm: Whether to use Vision LLM for screenshot extraction
            take_screenshots: Whether to capture screenshots with Playwright

        Returns:
            Dict with status and job_id for tracking

        Raises:
            ValueError: If chatbot not found or invalid status
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        if chatbot.build_status not in ('draft', 'error', 'paused'):
            raise ValueError(f'Cannot start crawl in status: {chatbot.build_status}')

        if not chatbot.source_url:
            raise ValueError('No source URL configured')

        # Create a collection for this chatbot first (synchronously)
        collection_name = f"chatbot_{chatbot.name}"
        collection = RAGCollection.query.filter_by(name=collection_name).first()

        if not collection:
            embedding_model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_EMBEDDING)
            if not embedding_model:
                raise ValueError("No default embedding model configured in llm_models")
            collection = RAGCollection(
                name=collection_name,
                display_name=f"Collection für {chatbot.display_name}",
                description=f"Automatisch erstellt für Chatbot aus {chatbot.source_url}",
                source_type='crawler',
                source_url=chatbot.source_url,
                embedding_model=embedding_model,
                created_by=chatbot.created_by
            )
            db.session.add(collection)
            db.session.commit()

        # Link collection to chatbot
        chatbot.primary_collection_id = collection.id

        # Assign collection to chatbot
        existing = ChatbotCollection.query.filter_by(
            chatbot_id=chatbot_id,
            collection_id=collection.id
        ).first()

        if not existing:
            assignment = ChatbotCollection(
                chatbot_id=chatbot_id,
                collection_id=collection.id,
                is_primary=True,
                assigned_by=chatbot.created_by
            )
            db.session.add(assignment)

        # Update status to crawling
        chatbot.build_status = 'crawling'
        chatbot.build_error = None
        db.session.commit()

        # Start background crawl using the crawler service (returns job_id immediately)
        from services.crawler.web_crawler import crawler_service
        from flask import current_app
        app = current_app._get_current_object()

        job_id = crawler_service.start_crawl_background(
            urls=[chatbot.source_url],
            collection_name=collection.display_name,
            collection_description=collection.description,
            max_pages_per_site=max_pages,
            max_depth=max_depth,
            existing_collection_id=collection.id,
            use_playwright=use_playwright,
            use_vision_llm=use_vision_llm,
            take_screenshots=take_screenshots,
            app=app,
            chatbot_id=chatbot_id  # For wizard session progress updates
        )

        # Store job_id in collection
        collection.crawl_job_id = job_id
        db.session.commit()

        # Start a thread to monitor the crawl and transition to embedding when done
        # Import monitoring service here to avoid circular imports
        from .chatbot_build_monitor import ChatbotBuildMonitor
        thread = threading.Thread(
            target=ChatbotBuildMonitor.monitor_crawl,
            args=(app, chatbot_id, collection.id, job_id),
            daemon=True
        )
        thread.start()

        logger.info(f"[ChatbotCreator] Started crawl for chatbot {chatbot_id}, job_id: {job_id}")

        return {
            'success': True,
            'message': 'Crawl started',
            'job_id': job_id,
            'collection_id': collection.id
        }

    @staticmethod
    def finalize_chatbot(chatbot_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize the chatbot configuration and mark as ready.

        The chatbot can be finalized even if embedding is still in progress.
        The embedding will continue in the background, and the chatbot will
        work with the chunks that are already available.

        Args:
            chatbot_id: The chatbot ID
            data: Configuration data (name, display_name, system_prompt, etc.)

        Returns:
            Dict with result including embedding_in_progress flag

        Raises:
            ValueError: If chatbot not found or name already exists
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        # Check if embedding is still in progress
        embedding_in_progress = False
        embedding_progress = 0
        if chatbot.primary_collection_id:
            collection = RAGCollection.query.get(chatbot.primary_collection_id)
            if collection and collection.embedding_status == 'processing':
                embedding_in_progress = True
                embedding_progress = collection.embedding_progress or 0

        # Update fields if provided
        if 'name' in data:
            # Check if name is unique
            existing = Chatbot.query.filter(
                Chatbot.name == data['name'],
                Chatbot.id != chatbot_id
            ).first()
            if existing:
                raise ValueError('Name already exists')
            chatbot.name = data['name']

        if 'display_name' in data:
            chatbot.display_name = data['display_name']
        if 'description' in data:
            chatbot.description = data['description']
        if 'system_prompt' in data:
            chatbot.system_prompt = data['system_prompt']
        if 'model_name' in data and data['model_name']:
            chatbot.model_name = data['model_name']
        if 'welcome_message' in data:
            chatbot.welcome_message = data['welcome_message']
        if 'icon' in data:
            chatbot.icon = data['icon']
        if 'color' in data:
            chatbot.color = data['color']

        # Mark as ready - chatbot is usable even if embedding is still running
        chatbot.build_status = 'ready'
        chatbot.build_error = None
        chatbot.is_active = True
        chatbot.updated_at = datetime.now()

        db.session.commit()

        if embedding_in_progress:
            logger.info(f"[ChatbotCreator] Finalized chatbot {chatbot_id} (embedding still in progress: {embedding_progress}%)")
        else:
            logger.info(f"[ChatbotCreator] Finalized chatbot {chatbot_id}")

        return {
            'success': True,
            'chatbot_id': chatbot_id,
            'name': chatbot.name,
            'display_name': chatbot.display_name,
            'build_status': chatbot.build_status,
            'embedding_in_progress': embedding_in_progress,
            'embedding_progress': embedding_progress
        }

    @staticmethod
    def update_build_status(chatbot_id: int, status: str, error: Optional[str] = None) -> Dict[str, Any]:
        """
        Update the build status of a chatbot.

        Args:
            chatbot_id: The chatbot ID
            status: New status
            error: Optional error message

        Returns:
            Dict with result

        Raises:
            ValueError: If chatbot not found or invalid status
        """
        valid_statuses = ['draft', 'crawling', 'embedding', 'configuring', 'ready', 'error', 'paused']
        if status not in valid_statuses:
            raise ValueError(f'Invalid status: {status}')

        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        chatbot.build_status = status
        if error:
            chatbot.build_error = error
        elif status == 'ready':
            chatbot.build_error = None
            chatbot.is_active = True  # Activate when ready

        db.session.commit()

        return {
            'success': True,
            'chatbot_id': chatbot_id,
            'build_status': status
        }

    @staticmethod
    def cancel_build(chatbot_id: int) -> Dict[str, Any]:
        """
        Cancel the chatbot build process.

        Aborts any running crawl/embedding and keeps already processed data.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with cancellation result and cleanup info

        Raises:
            ValueError: If chatbot not found or cannot cancel in current status
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        if chatbot.build_status not in ('crawling', 'embedding', 'paused'):
            raise ValueError(f'Cannot cancel build in status: {chatbot.build_status}')

        # Get cleanup info
        cleanup_info = {
            'documents_kept': 0,
            'embeddings_kept': 0,
            'collection_status': 'empty'
        }

        if chatbot.primary_collection_id:
            collection = RAGCollection.query.get(chatbot.primary_collection_id)
            if collection:
                cleanup_info['documents_kept'] = collection.document_count or 0
                cleanup_info['embeddings_kept'] = collection.total_chunks or 0
                cleanup_info['collection_status'] = 'partial' if cleanup_info['documents_kept'] > 0 else 'empty'

                # Cancel embedding if running
                if collection.embedding_status == 'processing':
                    from services.rag.collection_embedding_service import get_collection_embedding_service
                    service = get_collection_embedding_service()
                    service.pause_embedding(collection.id)

        chatbot.build_status = 'paused'
        chatbot.build_error = 'Build cancelled by user'
        db.session.commit()

        logger.info(f"[ChatbotCreator] Cancelled build for chatbot {chatbot_id}")

        return {
            'success': True,
            'chatbot_id': chatbot_id,
            'build_status': 'paused',
            'message': 'Build wurde abgebrochen',
            'cleanup': cleanup_info
        }

    @staticmethod
    def resume_build(chatbot_id: int) -> Dict[str, Any]:
        """
        Resume a paused chatbot build process.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with resume result

        Raises:
            ValueError: If chatbot not found or cannot resume in current status
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        if chatbot.build_status != 'paused':
            raise ValueError(f'Cannot resume build in status: {chatbot.build_status}')

        # Determine where to resume
        if chatbot.primary_collection_id:
            collection = RAGCollection.query.get(chatbot.primary_collection_id)
            if collection:
                # Check if embedding needs to continue
                if collection.embedding_status in ('idle', 'failed'):
                    # Resume embedding
                    chatbot.build_status = 'embedding'
                    db.session.commit()

                    from flask import current_app
                    from .chatbot_build_monitor import ChatbotBuildMonitor
                    app = current_app._get_current_object()
                    ChatbotBuildMonitor.start_embedding(app, chatbot_id, collection.id)

                    return {
                        'success': True,
                        'chatbot_id': chatbot_id,
                        'build_status': 'embedding',
                        'resumed_at': datetime.now().isoformat()
                    }
                elif collection.embedding_status == 'completed':
                    # Move to configuring
                    chatbot.build_status = 'configuring'
                    db.session.commit()

                    return {
                        'success': True,
                        'chatbot_id': chatbot_id,
                        'build_status': 'configuring',
                        'resumed_at': datetime.now().isoformat()
                    }

        # No collection - restart crawl
        chatbot.build_status = 'draft'
        db.session.commit()

        return ChatbotCreator.start_crawl(chatbot_id)

    @staticmethod
    def tweak_chatbot(chatbot_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quick-tweak chatbot parameters (partial update).

        Args:
            chatbot_id: The chatbot ID
            data: Parameters to update

        Returns:
            Dict with updated fields

        Raises:
            ValueError: If chatbot not found or no valid fields to update
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        updated_fields = []
        allowed_fields = [
            'temperature', 'max_tokens', 'system_prompt',
            'rag_retrieval_k', 'rag_min_relevance', 'rag_enabled'
        ]

        for field in allowed_fields:
            if field in data:
                setattr(chatbot, field, data[field])
                updated_fields.append(field)

        if not updated_fields:
            raise ValueError('No valid fields to update')

        chatbot.updated_at = datetime.now()
        db.session.commit()

        logger.info(f"[ChatbotCreator] Tweaked chatbot {chatbot_id}: {updated_fields}")

        return {
            'success': True,
            'id': chatbot_id,
            'updated_fields': updated_fields,
            'updated_at': chatbot.updated_at.isoformat()
        }
