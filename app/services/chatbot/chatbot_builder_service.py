"""
Chatbot Builder Service.

Provides functionality for the Chatbot Builder wizard:
- Creating chatbots from URLs via Web Crawler
- Auto-generating fields (name, system_prompt, welcome_message) using LLM
- Managing build pipeline (draft → crawling → embedding → configuring → ready)
"""

import logging
import re
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from db.db import db
from db.tables import Chatbot, ChatbotCollection, RAGCollection, RAGDocument, CollectionDocumentLink

logger = logging.getLogger(__name__)


class ChatbotBuilderService:
    """Service for building chatbots via the wizard workflow."""

    # LLM settings for field generation
    DEFAULT_MODEL = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"

    @staticmethod
    def create_wizard_chatbot(url: str, username: str) -> Dict[str, Any]:
        """
        Start the chatbot creation wizard with a URL.

        Creates a draft chatbot and starts the crawl process.

        Args:
            url: The source URL to crawl
            username: Username creating the chatbot

        Returns:
            Dict with chatbot info and status
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
        chatbot = Chatbot(
            name=name,
            display_name=f"Chatbot for {parsed.netloc}",
            description=f"Auto-generated chatbot from {url}",
            system_prompt="Du bist ein hilfreicher Assistent.",
            build_status='draft',
            source_url=url,
            is_active=False,  # Not active until ready
            created_by=username
        )
        db.session.add(chatbot)
        db.session.commit()

        logger.info(f"[ChatbotBuilder] Created draft chatbot {chatbot.id} for URL: {url}")

        return {
            'success': True,
            'chatbot_id': chatbot.id,
            'name': chatbot.name,
            'display_name': chatbot.display_name,
            'build_status': chatbot.build_status,
            'source_url': url
        }

    @staticmethod
    def start_crawl(chatbot_id: int, max_pages: int = 50, max_depth: int = 3) -> Dict[str, Any]:
        """
        Start crawling the source URL for a chatbot.

        Args:
            chatbot_id: The chatbot ID
            max_pages: Maximum pages to crawl
            max_depth: Maximum crawl depth

        Returns:
            Dict with status and job_id for tracking
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

        if chatbot.build_status not in ('draft', 'error', 'paused'):
            return {'success': False, 'error': f'Cannot start crawl in status: {chatbot.build_status}'}

        if not chatbot.source_url:
            return {'success': False, 'error': 'No source URL configured'}

        # Create a collection for this chatbot first (synchronously)
        collection_name = f"chatbot_{chatbot.name}"
        collection = RAGCollection.query.filter_by(name=collection_name).first()

        if not collection:
            collection = RAGCollection(
                name=collection_name,
                display_name=f"Collection für {chatbot.display_name}",
                description=f"Automatisch erstellt für Chatbot aus {chatbot.source_url}",
                source_type='crawler',
                source_url=chatbot.source_url,
                embedding_model='llamaindex/vdr-2b-multi-v1',
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
            app=app
        )

        # Store job_id in collection
        collection.crawl_job_id = job_id
        db.session.commit()

        # Start a thread to monitor the crawl and transition to embedding when done
        thread = threading.Thread(
            target=ChatbotBuilderService._monitor_crawl,
            args=(app, chatbot_id, collection.id, job_id),
            daemon=True
        )
        thread.start()

        logger.info(f"[ChatbotBuilder] Started crawl for chatbot {chatbot_id}, job_id: {job_id}")

        return {
            'success': True,
            'message': 'Crawl started',
            'job_id': job_id,
            'collection_id': collection.id
        }

    @staticmethod
    def _monitor_crawl(app, chatbot_id: int, collection_id: int, job_id: str):
        """
        Monitor the crawl job and transition to embedding when done.

        This runs in a background thread and polls the crawler service
        for completion status.
        """
        import time
        from services.crawler.web_crawler import crawler_service

        with app.app_context():
            try:
                max_wait_seconds = 600  # 10 minutes timeout
                poll_interval = 2  # Check every 2 seconds
                elapsed = 0

                while elapsed < max_wait_seconds:
                    status = crawler_service.get_job_status(job_id)

                    if not status:
                        logger.warning(f"[ChatbotBuilder] Job {job_id} not found")
                        break

                    if status.get('status') == 'completed':
                        logger.info(f"[ChatbotBuilder] Crawl completed for chatbot {chatbot_id}")

                        # Transition to embedding
                        chatbot = Chatbot.query.get(chatbot_id)
                        if chatbot:
                            chatbot.build_status = 'embedding'
                            db.session.commit()

                            # Start embedding
                            ChatbotBuilderService._start_embedding(app, chatbot_id, collection_id)
                        return

                    elif status.get('status') == 'failed':
                        logger.error(f"[ChatbotBuilder] Crawl failed for chatbot {chatbot_id}: {status.get('error')}")
                        chatbot = Chatbot.query.get(chatbot_id)
                        if chatbot:
                            chatbot.build_status = 'error'
                            chatbot.build_error = status.get('error', 'Crawl failed')
                            db.session.commit()
                        return

                    elif status.get('status') == 'cancelled':
                        logger.info(f"[ChatbotBuilder] Crawl cancelled for chatbot {chatbot_id}")
                        chatbot = Chatbot.query.get(chatbot_id)
                        if chatbot:
                            chatbot.build_status = 'paused'
                            chatbot.build_error = 'Crawl was cancelled'
                            db.session.commit()
                        return

                    time.sleep(poll_interval)
                    elapsed += poll_interval

                # Timeout reached
                logger.error(f"[ChatbotBuilder] Crawl timeout for chatbot {chatbot_id}")
                chatbot = Chatbot.query.get(chatbot_id)
                if chatbot:
                    chatbot.build_status = 'error'
                    chatbot.build_error = 'Crawl timeout'
                    db.session.commit()

            except Exception as e:
                logger.error(f"[ChatbotBuilder] Monitor error for chatbot {chatbot_id}: {e}")
                chatbot = Chatbot.query.get(chatbot_id)
                if chatbot:
                    chatbot.build_status = 'error'
                    chatbot.build_error = str(e)[:500]
                    db.session.commit()

    @staticmethod
    def _start_embedding(app, chatbot_id: int, collection_id: int):
        """Start embedding process after crawl."""
        try:
            from services.rag.collection_embedding_service import get_collection_embedding_service

            logger.info(f"[ChatbotBuilder] Starting embedding for chatbot {chatbot_id}, collection {collection_id}")

            service = get_collection_embedding_service()
            service.start_embedding(collection_id)

            # Start a thread to monitor embedding completion
            logger.info(f"[ChatbotBuilder] Starting embedding monitor thread for chatbot {chatbot_id}")
            thread = threading.Thread(
                target=ChatbotBuilderService._monitor_embedding,
                args=(app, chatbot_id, collection_id),
                daemon=True
            )
            thread.start()
            logger.info(f"[ChatbotBuilder] Embedding monitor thread started for chatbot {chatbot_id}")

        except Exception as e:
            logger.error(f"[ChatbotBuilder] Embedding error: {e}")
            chatbot = Chatbot.query.get(chatbot_id)
            if chatbot:
                chatbot.build_status = 'error'
                chatbot.build_error = f"Embedding failed: {str(e)}"
                db.session.commit()

    @staticmethod
    def _monitor_embedding(app, chatbot_id: int, collection_id: int):
        """
        Monitor the embedding process and transition to configuring when done.
        """
        import time

        logger.info(f"[ChatbotBuilder] Embedding monitor running for chatbot {chatbot_id}")

        with app.app_context():
            try:
                max_wait_seconds = 1800  # 30 minutes timeout for embedding
                poll_interval = 2  # Check every 2 seconds
                elapsed = 0

                logger.debug(f"[ChatbotBuilder] Starting monitor loop for chatbot {chatbot_id}")

                while elapsed < max_wait_seconds:
                    # Force fresh read from database by closing and re-opening session
                    db.session.rollback()  # Rollback any uncommitted changes
                    db.session.close()     # Close the session to release connections

                    collection = RAGCollection.query.get(collection_id)
                    chatbot = Chatbot.query.get(chatbot_id)

                    status = collection.embedding_status if collection else 'N/A'
                    # Only log every 5th poll to reduce noise
                    if elapsed % (poll_interval * 5) == 0:
                        logger.info(f"[ChatbotBuilder] Monitor poll: collection {collection_id} status={status}")

                    if not collection or not chatbot:
                        logger.warning(f"[ChatbotBuilder] Collection or Chatbot not found")
                        return

                    # Check if chatbot was paused or errored
                    if chatbot.build_status in ('paused', 'error', 'ready'):
                        logger.info(f"[ChatbotBuilder] Chatbot {chatbot_id} status changed to {chatbot.build_status}, stopping monitor")
                        return

                    if collection.embedding_status == 'completed':
                        logger.info(f"[ChatbotBuilder] Embedding completed for chatbot {chatbot_id}, transitioning to configuring")

                        # Transition to configuring
                        chatbot.build_status = 'configuring'
                        chatbot.build_error = None
                        db.session.commit()

                        logger.info(f"[ChatbotBuilder] Chatbot {chatbot_id} transitioned to 'configuring'")
                        return

                    elif collection.embedding_status == 'failed':
                        logger.error(f"[ChatbotBuilder] Embedding failed for chatbot {chatbot_id}")
                        chatbot.build_status = 'error'
                        chatbot.build_error = collection.embedding_error or 'Embedding failed'
                        db.session.commit()
                        return

                    time.sleep(poll_interval)
                    elapsed += poll_interval

                # Timeout reached
                logger.error(f"[ChatbotBuilder] Embedding timeout for chatbot {chatbot_id}")
                chatbot = Chatbot.query.get(chatbot_id)
                if chatbot:
                    chatbot.build_status = 'error'
                    chatbot.build_error = 'Embedding timeout'
                    db.session.commit()

            except Exception as e:
                logger.error(f"[ChatbotBuilder] Embedding monitor error for chatbot {chatbot_id}: {e}")
                chatbot = Chatbot.query.get(chatbot_id)
                if chatbot:
                    chatbot.build_status = 'error'
                    chatbot.build_error = str(e)[:500]
                    db.session.commit()

    @staticmethod
    def generate_field(chatbot_id: int, field: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a field value using LLM based on the chatbot's context.

        Args:
            chatbot_id: The chatbot ID
            field: The field to generate (name, system_prompt, welcome_message)
            context: Optional additional context

        Returns:
            Dict with generated value
        """
        from openai import OpenAI
        import os

        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

        # Get collection info for context
        collection_info = ""
        if chatbot.primary_collection_id:
            collection = RAGCollection.query.get(chatbot.primary_collection_id)
            if collection:
                # Get sample documents
                links = CollectionDocumentLink.query.filter_by(
                    collection_id=collection.id
                ).limit(5).all()

                doc_titles = [link.document.title or link.document.filename
                              for link in links if link.document]
                collection_info = f"Die Wissensbasis enthält Dokumente wie: {', '.join(doc_titles)}"

        # Build prompts based on field
        prompts = {
            'name': {
                'system': "Du bist ein Experte für das Benennen von Chatbots. Generiere einen kurzen, prägnanten internen Namen (nur Kleinbuchstaben, Unterstriche erlaubt, keine Leerzeichen).",
                'user': f"Generiere einen internen Namen für einen Chatbot basierend auf:\n- URL: {chatbot.source_url}\n- {collection_info}\n\nAntworte NUR mit dem Namen, ohne Erklärung."
            },
            'display_name': {
                'system': "Du bist ein Experte für Chatbot-Branding. Generiere einen ansprechenden Anzeigenamen für einen Chatbot.",
                'user': f"Generiere einen freundlichen Anzeigenamen für einen Chatbot basierend auf:\n- URL: {chatbot.source_url}\n- {collection_info}\n\nAntworte NUR mit dem Namen, ohne Erklärung."
            },
            'system_prompt': {
                'system': "Du bist ein Experte für das Erstellen von System-Prompts für Chatbots. Erstelle einen professionellen System-Prompt.",
                'user': f"""Erstelle einen System-Prompt für einen Chatbot mit folgenden Eigenschaften:
- Basiert auf Inhalten von: {chatbot.source_url}
- {collection_info}
- Soll hilfreich und präzise antworten
- Soll bei Unsicherheit ehrlich sagen, wenn er keine Antwort weiß

Der Prompt sollte 2-3 Absätze lang sein und die Persönlichkeit des Bots definieren."""
            },
            'welcome_message': {
                'system': "Du bist ein Experte für Chatbot-Kommunikation. Erstelle eine einladende Willkommensnachricht.",
                'user': f"""Erstelle eine Willkommensnachricht für einen Chatbot mit:
- Basiert auf: {chatbot.source_url}
- {collection_info}

Die Nachricht sollte freundlich sein und den Nutzer einladen, Fragen zu stellen. Max 2-3 Sätze."""
            },
            'description': {
                'system': "Du bist ein Experte für Produktbeschreibungen. Erstelle eine kurze Beschreibung für einen Chatbot.",
                'user': f"Erstelle eine kurze Beschreibung (1-2 Sätze) für einen Chatbot basierend auf:\n- URL: {chatbot.source_url}\n- {collection_info}"
            }
        }

        if field not in prompts:
            return {'success': False, 'error': f'Unknown field: {field}'}

        try:
            # Use LiteLLM endpoint
            client = OpenAI(
                base_url=os.environ.get('LITELLM_BASE_URL', 'https://kiz1.in.ohmportal.de/llmproxy/v1'),
                api_key=os.environ.get('LITELLM_API_KEY', 'dummy')
            )

            response = client.chat.completions.create(
                model=ChatbotBuilderService.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": prompts[field]['system']},
                    {"role": "user", "content": prompts[field]['user']}
                ],
                temperature=0.7,
                max_tokens=500
            )

            generated_value = response.choices[0].message.content.strip()

            # Clean up the value based on field type
            if field == 'name':
                # Ensure valid name format
                generated_value = re.sub(r'[^a-z0-9_]', '_', generated_value.lower())
                generated_value = generated_value[:50]  # Limit length

            return {
                'success': True,
                'field': field,
                'value': generated_value
            }

        except Exception as e:
            logger.error(f"[ChatbotBuilder] Field generation error: {e}")
            return {'success': False, 'error': str(e)}

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
        """
        valid_statuses = ['draft', 'crawling', 'embedding', 'configuring', 'ready', 'error', 'paused']
        if status not in valid_statuses:
            return {'success': False, 'error': f'Invalid status: {status}'}

        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

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
    def get_build_status(chatbot_id: int) -> Dict[str, Any]:
        """
        Get the current build status of a chatbot.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with build status and progress info
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

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
                    'embedding_status': collection.embedding_status,
                    'embedding_progress': collection.embedding_progress or 0,
                    'document_count': collection.document_count,
                    'total_chunks': collection.total_chunks
                }

        return result

    @staticmethod
    def finalize_chatbot(chatbot_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize the chatbot configuration and mark as ready.

        Args:
            chatbot_id: The chatbot ID
            data: Configuration data (name, display_name, system_prompt, etc.)

        Returns:
            Dict with result
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

        # Update fields if provided
        if 'name' in data:
            # Check if name is unique
            existing = Chatbot.query.filter(
                Chatbot.name == data['name'],
                Chatbot.id != chatbot_id
            ).first()
            if existing:
                return {'success': False, 'error': 'Name already exists'}
            chatbot.name = data['name']

        if 'display_name' in data:
            chatbot.display_name = data['display_name']
        if 'description' in data:
            chatbot.description = data['description']
        if 'system_prompt' in data:
            chatbot.system_prompt = data['system_prompt']
        if 'welcome_message' in data:
            chatbot.welcome_message = data['welcome_message']
        if 'icon' in data:
            chatbot.icon = data['icon']
        if 'color' in data:
            chatbot.color = data['color']

        # Mark as ready
        chatbot.build_status = 'ready'
        chatbot.build_error = None
        chatbot.is_active = True
        chatbot.updated_at = datetime.now()

        db.session.commit()

        logger.info(f"[ChatbotBuilder] Finalized chatbot {chatbot_id}")

        return {
            'success': True,
            'chatbot_id': chatbot_id,
            'name': chatbot.name,
            'display_name': chatbot.display_name,
            'build_status': chatbot.build_status
        }

    @staticmethod
    def cancel_build(chatbot_id: int) -> Dict[str, Any]:
        """
        Cancel the chatbot build process.

        Aborts any running crawl/embedding and keeps already processed data.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with cancellation result
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

        if chatbot.build_status not in ('crawling', 'embedding', 'paused'):
            return {'success': False, 'error': f'Cannot cancel build in status: {chatbot.build_status}'}

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

        logger.info(f"[ChatbotBuilder] Cancelled build for chatbot {chatbot_id}")

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
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

        if chatbot.build_status != 'paused':
            return {'success': False, 'error': f'Cannot resume build in status: {chatbot.build_status}'}

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
                    app = current_app._get_current_object()
                    ChatbotBuilderService._start_embedding(app, chatbot_id, collection.id)

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

        return ChatbotBuilderService.start_crawl(chatbot_id)

    @staticmethod
    def get_admin_test_data(chatbot_id: int) -> Dict[str, Any]:
        """
        Get data for the admin test page.

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with chatbot config, collection info, stats, and sample documents
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

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
        from db.tables import ChatbotConversation, ChatbotMessage
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
    def tweak_chatbot(chatbot_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quick-tweak chatbot parameters (partial update).

        Args:
            chatbot_id: The chatbot ID
            data: Parameters to update

        Returns:
            Dict with updated fields
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return {'success': False, 'error': 'Chatbot not found'}

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
            return {'success': False, 'error': 'No valid fields to update'}

        chatbot.updated_at = datetime.now()
        db.session.commit()

        logger.info(f"[ChatbotBuilder] Tweaked chatbot {chatbot_id}: {updated_fields}")

        return {
            'success': True,
            'id': chatbot_id,
            'updated_fields': updated_fields,
            'updated_at': chatbot.updated_at.isoformat()
        }
