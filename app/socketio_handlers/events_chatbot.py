"""
SocketIO Chatbot Events
Handles chatbot-specific streaming with Multi-Collection RAG support.

Events:
    Client → Server:
        - chatbot:stream: Send a chat message to a specific chatbot for streaming response
        - chatbot:join: Join chatbot room for updates
        - chatbot:leave: Leave chatbot room

    Server → Client:
        - chatbot:response: Streaming chat response chunks
        - chatbot:sources: RAG sources after streaming completes
        - chatbot:error: Error message
        - chatbot:complete: Signal stream completion with metadata

Integration:
    - Uses ChatService for Multi-Collection RAG
    - Supports chatbot-specific model configuration
    - Supports Vision models with RAG images
    - Saves conversation to database
"""

import logging
import os
import time
import base64
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room
from openai import OpenAI

from db.db import db
from db.tables import (
    Chatbot, ChatbotConversation, ChatbotMessage, ChatbotMessageRole
)
from services.chatbot.chat_service import ChatService
from services.chatbot.file_processor import FileProcessor
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.permission_service import PermissionService
from auth.oidc_validator import validate_token

logger = logging.getLogger(__name__)


def _build_messages_with_footnotes(chat_service, conversation, user_message, rag_context, sources, rag_images=None):
    """
    Build LLM messages with instructions to use footnote references.
    Supports Vision models with RAG images.

    Args:
        chat_service: ChatService instance
        conversation: Current conversation
        user_message: User's message
        rag_context: RAG context string
        sources: List of sources with footnote_id
        rag_images: List of image dicts with base64_data for vision models

    Returns:
        List of messages for LLM
    """
    from db.tables import ChatbotMessage, ChatbotMessageRole

    chatbot = chat_service.chatbot
    is_vision = FileProcessor.is_vision_model(chatbot.model_name)
    messages = []

    # System prompt with footnote instructions
    footnote_instruction = ""
    if sources:
        footnote_instruction = """

WICHTIG - Quellenangaben:
Du hast Zugriff auf die folgenden nummerierten Dokumente. Wenn du Informationen aus diesen Dokumenten verwendest, MUSST du Fußnoten im Format [1], [2], etc. direkt im Text setzen.
- Setze die Fußnote DIREKT nach dem Satz oder der Information, die aus der Quelle stammt.
- Verwende NUR die Nummern der Dokumente, die du tatsächlich verwendest.
- Beispiel: "Die Hauptstadt von Frankreich ist Paris [1]."
"""

    # Add vision instruction if applicable
    if is_vision and rag_images:
        footnote_instruction += """
Du hast auch Bilder aus den Dokumenten erhalten. Analysiere diese Bilder sorgfältig, wenn sie für die Beantwortung der Frage relevant sind.
"""

    system_prompt = chatbot.system_prompt + footnote_instruction
    messages.append({"role": "system", "content": system_prompt})

    # RAG context with numbered documents
    if rag_context and sources:
        numbered_context = "Verfügbare Dokumente:\n\n"
        for source in sources:
            footnote_id = source.get('footnote_id', 0)
            title = source.get('title', 'Unbekannt')
            excerpt = source.get('excerpt', '')
            numbered_context += f"[{footnote_id}] {title}:\n{excerpt}\n\n"

        messages.append({
            "role": "system",
            "content": numbered_context
        })

    # Chat history (limited)
    history = ChatbotMessage.query.filter_by(
        conversation_id=conversation.id
    ).order_by(ChatbotMessage.created_at.desc()).limit(
        chatbot.max_context_messages * 2
    ).all()

    history.reverse()

    for msg in history:
        role = "user" if msg.role == ChatbotMessageRole.USER else "assistant"
        messages.append({"role": role, "content": msg.content})

    # Current user message - with images for vision models
    if is_vision and rag_images:
        # Build multimodal content
        user_content = []

        # Add text first
        user_content.append({
            "type": "text",
            "text": user_message
        })

        # Add images from RAG
        for img in rag_images[:5]:  # Limit to 5 images
            if img.get('base64_data'):
                mime_type = img.get('mime_type', 'image/jpeg')
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{img['base64_data']}"
                    }
                })

        messages.append({
            "role": "user",
            "content": user_content
        })
    else:
        messages.append({"role": "user", "content": user_message})

    return messages


def _get_rag_images_for_sources(sources):
    """
    Load images associated with RAG sources.

    Args:
        sources: List of source dicts

    Returns:
        List of image dicts with base64_data
    """
    from db.tables import RAGDocumentChunk

    images = []

    for source in sources:
        doc_id = source.get('document_id')
        if not doc_id:
            continue

        # Find chunks with images for this document
        chunks_with_images = RAGDocumentChunk.query.filter(
            RAGDocumentChunk.document_id == doc_id,
            RAGDocumentChunk.has_image == True
        ).limit(3).all()

        for chunk in chunks_with_images:
            if chunk.image_path and os.path.exists(chunk.image_path):
                try:
                    with open(chunk.image_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                    images.append({
                        'base64_data': image_data,
                        'mime_type': chunk.image_mime_type or 'image/jpeg',
                        'alt_text': chunk.image_alt_text,
                        'source_url': chunk.image_url,
                        'document_id': doc_id
                    })
                except Exception as e:
                    logger.warning(f"Failed to load RAG image {chunk.image_path}: {e}")

    return images


def register_chatbot_events(socketio):
    """
    Register chatbot-related SocketIO events.

    Events:
        chatbot:stream: Handle user chat message with streaming response
        chatbot:join: Join chatbot session room
        chatbot:leave: Leave chatbot session room
    """

    @socketio.on("chatbot:join")
    def handle_join(data):
        """Join a chatbot session room"""
        session_id = data.get("session_id")
        if session_id:
            join_room(f"chatbot_{session_id}")
            logger.info(f"Client {request.sid} joined chatbot room {session_id}")

    @socketio.on("chatbot:leave")
    def handle_leave(data):
        """Leave a chatbot session room"""
        session_id = data.get("session_id")
        if session_id:
            leave_room(f"chatbot_{session_id}")
            logger.info(f"Client {request.sid} left chatbot room {session_id}")

    @socketio.on("chatbot:stream")
    def handle_chatbot_stream(data):
        """
        Handle streaming chat with a specific chatbot.

        Expected data:
            chatbot_id: int - ID of the chatbot
            message: str - User message
            session_id: str - Session ID for conversation tracking
            username: str (optional) - Username for tracking

        Emits:
            chatbot:response - Streaming chunks {content, complete}
            chatbot:sources - RAG sources after completion
            chatbot:complete - Final metadata {conversation_id, tokens, response_time_ms}
            chatbot:error - Error message if something fails
        """
        client_id = request.sid
        start_time = time.time()

        try:
            data = data or {}

            token = data.get("token")
            if not token:
                emit("chatbot:error", {"error": "Authentication required"}, room=client_id)
                return

            payload = validate_token(token)
            if not payload:
                emit("chatbot:error", {"error": "Authentication failed"}, room=client_id)
                return

            username_from_token = (
                payload.get('preferred_username') or
                payload.get('username') or
                payload.get('name') or
                payload.get('uid') or
                payload.get('sub')
            )
            if not username_from_token:
                emit("chatbot:error", {"error": "Authentication failed"}, room=client_id)
                return

            if not PermissionService.check_permission(username_from_token, 'feature:chatbots:view'):
                emit("chatbot:error", {"error": "Forbidden"}, room=client_id)
                return

            chatbot_id = data.get("chatbot_id")
            user_message = data.get("message", "").strip()
            session_id = data.get("session_id")
            username = username_from_token

            if not chatbot_id:
                emit("chatbot:error", {"error": "chatbot_id is required"}, room=client_id)
                return

            if not user_message:
                emit("chatbot:error", {"error": "message is required"}, room=client_id)
                return

            if not session_id:
                emit("chatbot:error", {"error": "session_id is required"}, room=client_id)
                return

            # Get chatbot
            chatbot = Chatbot.query.get(chatbot_id)
            if not chatbot:
                emit("chatbot:error", {"error": f"Chatbot {chatbot_id} not found"}, room=client_id)
                return

            if not ChatbotAccessService.user_can_access_chatbot(username, chatbot):
                emit("chatbot:error", {"error": "Forbidden"}, room=client_id)
                return

            if not chatbot.is_active:
                emit("chatbot:error", {"error": "Chatbot is not active"}, room=client_id)
                return

            # Initialize service (for RAG and conversation management)
            chat_service = ChatService(chatbot_id)

            # Get or create conversation
            conversation = chat_service._get_or_create_conversation(session_id, username)

            # Save user message
            chat_service._save_message(conversation.id, ChatbotMessageRole.USER, user_message)

            # Get RAG context if enabled
            rag_context = ""
            sources = []
            sources_with_ids = []
            if chatbot.rag_enabled and chatbot.collections:
                rag_context, sources = chat_service._get_multi_collection_context(user_message)
                # Add numeric IDs to sources for footnote references
                for idx, source in enumerate(sources):
                    source['footnote_id'] = idx + 1
                    sources_with_ids.append(source)

            # Send sources BEFORE streaming so frontend can render footnotes
            if sources_with_ids:
                emit("chatbot:sources", {
                    "sources": sources_with_ids
                }, room=client_id)

            # Check if model supports vision and load RAG images if so
            is_vision_model = FileProcessor.is_vision_model(chatbot.model_name)
            rag_images = []
            if is_vision_model and sources_with_ids:
                rag_images = _get_rag_images_for_sources(sources_with_ids)
                if rag_images:
                    logger.info(f"Loaded {len(rag_images)} images for vision model {chatbot.model_name}")

            # Build messages for LLM with footnote instructions (and images for vision models)
            messages = _build_messages_with_footnotes(
                chat_service, conversation, user_message, rag_context, sources_with_ids, rag_images
            )

            # Initialize LLM client
            llm_client = OpenAI(
                api_key=os.environ.get('LITELLM_API_KEY'),
                base_url=os.environ.get('LITELLM_BASE_URL')
            )

            # Stream response
            assistant_message = ""
            tokens_input = 0
            tokens_output = 0

            stream = llm_client.chat.completions.create(
                model=chatbot.model_name,
                messages=messages,
                temperature=chatbot.temperature,
                max_tokens=chatbot.max_tokens,
                top_p=chatbot.top_p,
                stream=True
            )

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = getattr(delta, "content", "")

                if content:
                    assistant_message += content
                    emit("chatbot:response", {
                        "content": content,
                        "complete": False
                    }, room=client_id)

                # Check for completion
                if getattr(choice, "finish_reason", None) is not None:
                    break

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Estimate tokens (streaming doesn't always provide usage)
            tokens_input = len(str(messages)) // 4  # Rough estimate
            tokens_output = len(assistant_message) // 4

            # Save assistant message
            sources_to_save = sources_with_ids if chatbot.rag_include_sources else []
            assistant_msg = chat_service._save_message(
                conversation.id,
                ChatbotMessageRole.ASSISTANT,
                assistant_message,
                rag_context=rag_context if rag_context else None,
                rag_sources=sources_to_save,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                response_time_ms=response_time_ms
            )

            # Update conversation
            conversation.message_count += 2
            conversation.last_message_at = datetime.now()
            if not conversation.title and len(user_message) > 0:
                conversation.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            db.session.commit()

            # Emit completion with metadata
            emit("chatbot:complete", {
                "conversation_id": conversation.id,
                "message_id": assistant_msg.id,
                "tokens": {
                    "input": tokens_input,
                    "output": tokens_output
                },
                "response_time_ms": response_time_ms
            }, room=client_id)

            # Also emit final response chunk to signal completion
            emit("chatbot:response", {
                "content": "",
                "complete": True
            }, room=client_id)

            logger.info(f"Chatbot {chatbot.name} responded in {response_time_ms}ms")

        except Exception as e:
            logger.error(f"Chatbot stream error: {e}", exc_info=True)
            emit("chatbot:error", {
                "error": "Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut."
            }, room=client_id)
            emit("chatbot:response", {
                "content": "",
                "complete": True
            }, room=client_id)
