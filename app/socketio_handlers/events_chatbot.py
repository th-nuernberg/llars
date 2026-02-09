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

from db.database import db
from db.tables import (
    Chatbot, ChatbotConversation, ChatbotMessage, ChatbotMessageRole
)
from services.chatbot.chat_service import ChatService
from services.chatbot.agent_chat_service import AgentChatService
from services.chatbot.file_processor import FileProcessor
from services.chatbot.chatbot_access_service import ChatbotAccessService
from services.llm.llm_client_factory import LLMClientFactory
from services.permission_service import PermissionService
from auth.oidc_validator import validate_token
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


def _replace_url_placeholders(text: str) -> str:
    """
    Replace PROJECT_URL placeholders in LLM response.

    The LLM might output {PROJECT_URL} or ${PROJECT_URL} if it sees
    these patterns in RAG context (e.g., from documentation about
    environment variables). This ensures all such placeholders are
    replaced with the actual URL.
    """
    if not text:
        return text
    project_url = os.environ.get('PROJECT_URL', 'http://localhost:55080')
    # Replace various placeholder formats (order matters - longer patterns first)
    text = text.replace('${PROJECT_URL}', project_url)  # Shell-style
    text = text.replace('{PROJECT_URL}', project_url)   # Simple placeholder
    text = text.replace('%24%7BPROJECT_URL%7D', project_url)  # URL-encoded ${...}
    text = text.replace('%7BPROJECT_URL%7D', project_url)  # URL-encoded {...}
    return text


def _commit_with_retry(max_retries: int = 3, delay: float = 0.1):
    """
    Commit database session with retry logic for deadlocks.

    MariaDB deadlocks can occur when concurrent transactions lock rows
    in different orders. This helper retries the commit on deadlock.
    """
    import time as time_module
    for attempt in range(max_retries):
        try:
            db.session.commit()
            return True
        except OperationalError as e:
            # Check if it's a deadlock error (MySQL error 1213)
            if "1213" in str(e) or "Deadlock" in str(e):
                db.session.rollback()
                if attempt < max_retries - 1:
                    logger.warning(f"[Chatbot] Deadlock detected, retrying ({attempt + 1}/{max_retries})...")
                    time_module.sleep(delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"[Chatbot] Deadlock persisted after {max_retries} retries")
                    raise
            else:
                raise
    return False


def _classify_token_error(token: str) -> str:
    """Best-effort classification of auth failures for frontend handling."""
    if not token:
        return 'missing token'
    try:
        import jwt as pyjwt

        decoded = pyjwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
            }
        )
        exp = decoded.get('exp')
        if exp is None:
            return 'invalid token'

        exp_int = int(exp)
        if exp_int < int(time.time()):
            return 'jwt expired'
        return 'invalid token'
    except Exception:
        return 'invalid token'


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
    require_citations = bool(getattr(chatbot.prompt_settings, 'rag_require_citations', True)) if chatbot else True
    if sources and require_citations:
        footnote_instruction = chat_service._build_citation_instructions()

    # Add vision instruction if applicable
    if is_vision and rag_images:
        footnote_instruction += """
Du hast auch Bilder aus den Dokumenten erhalten. Analysiere diese Bilder sorgfältig, wenn sie für die Beantwortung der Frage relevant sind.
"""

    # Replace {PROJECT_URL} placeholders in system prompt before sending to LLM
    system_prompt = _replace_url_placeholders(chatbot.system_prompt) + footnote_instruction
    messages.append({"role": "system", "content": system_prompt})

    # RAG context with numbered documents
    if sources:
        numbered_context = chat_service._build_numbered_context(sources)
        if numbered_context:
            messages.append({"role": "system", "content": numbered_context})
    elif rag_context:
        messages.append({"role": "system", "content": f"Kontext:\n\n{rag_context}"})

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


def _get_rag_images_for_sources(sources, max_images=4):
    """
    Load images associated with RAG sources.

    Args:
        sources: List of source dicts
        max_images: Maximum number of images to return (default: 4, LiteLLM limit)

    Returns:
        List of image dicts with base64_data (limited to max_images)
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
                    # Early exit if we have enough images
                    if len(images) >= max_images:
                        logger.info(f"Reached max vision images limit ({max_images})")
                        return images
                except Exception as e:
                    logger.warning(f"Failed to load RAG image {chunk.image_path}: {e}")

        # Check after each source document
        if len(images) >= max_images:
            break

    return images


def _stream_title_generation(socketio, chat_service, conversation, user_message, client_id):
    """
    Stream title generation to the client.

    Emits:
        chatbot:title_generating - Title generation starting (with conversation_id)
        chatbot:title_delta - Streaming title characters
        chatbot:title_complete - Final title (with conversation_id)
    """
    if not chat_service._is_placeholder_title(conversation.title):
        return conversation.title

    conv_id = conversation.id

    def title_stream_callback(delta: str):
        emit("chatbot:title_delta", {"delta": delta, "conversation_id": conv_id}, room=client_id)
        socketio.sleep(0)

    # Emit that title generation is starting
    emit("chatbot:title_generating", {"generating": True, "conversation_id": conv_id}, room=client_id)
    socketio.sleep(0)

    # Generate title with streaming
    title = chat_service._generate_smart_title(user_message, stream_callback=title_stream_callback)

    if title:
        conversation.title = title
        emit("chatbot:title_complete", {"title": title, "conversation_id": conv_id}, room=client_id)
        socketio.sleep(0)

    return title


def _handle_agent_stream(socketio, agent_service, chatbot, user_message, session_id, username, client_id, start_time, conversation_id=None):
    """
    Handle streaming chat with agent modes (ACT, ReAct, ReflAct).

    Emits:
        chatbot:agent_status - Agent reasoning steps
        chatbot:response - Streaming content
        chatbot:sources - RAG sources
        chatbot:complete - Final metadata
        chatbot:title_delta - Streaming title characters
        chatbot:title_complete - Final title
    """
    try:
        # Emit initial agent mode info
        agent_mode = agent_service.get_agent_mode()
        task_type = agent_service.get_task_type()

        def emit_agent_status(payload: dict) -> None:
            emit("chatbot:agent_status", payload, room=client_id)
            socketio.sleep(0)

        emit_agent_status({
            "type": "init",
            "mode": agent_mode,
            "task_type": task_type,
            "max_iterations": agent_service.get_max_iterations()
        })

        final_response = ""
        all_sources = []
        reasoning_steps = []
        conversation_id_result = None
        conversation_title = None
        message_id = None

        # Stream agent responses
        for event in agent_service.chat_agent(user_message, session_id, username, conversation_id=conversation_id):
            event_status = event.get("status")

            if event_status == "starting":
                emit_agent_status({
                    "type": "starting",
                    "mode": event.get("mode")
                })

            elif event_status == "iteration":
                emit_agent_status({
                    "type": "iteration",
                    "iteration": event.get("iteration"),
                    "max": event.get("max")
                })

            elif event_status == "context_retrieved":
                emit_agent_status({
                    "type": "context",
                    "sources_count": event.get("sources_count", 0)
                })

            elif event_status == "defining_goal":
                emit_agent_status({
                    "type": "defining_goal"
                })

            elif event_status == "goal_defined":
                reasoning_steps.append({"type": "goal", "content": event.get("goal")})
                emit_agent_status({
                    "type": "goal",
                    "goal": event.get("goal")
                })
            elif event_status == "goal_delta":
                emit_agent_status({
                    "type": "goal_delta",
                    "delta": event.get("delta"),
                    "iteration": event.get("iteration")
                })

            elif event_status == "reflecting":
                emit_agent_status({
                    "type": "reflecting",
                    "iteration": event.get("iteration")
                })

            elif event_status == "reflection":
                reasoning_steps.append({"type": "reflection", "content": event.get("reflection")})
                emit_agent_status({
                    "type": "reflection",
                    "content": event.get("reflection"),
                    "iteration": event.get("iteration")
                })
            elif event_status == "reflection_delta":
                emit_agent_status({
                    "type": "reflection_delta",
                    "delta": event.get("delta"),
                    "iteration": event.get("iteration")
                })

            elif event_status == "thinking":
                emit_agent_status({
                    "type": "thinking",
                    "iteration": event.get("iteration")
                })

            elif event_status == "thought":
                reasoning_steps.append({"type": "thought", "content": event.get("thought")})
                emit_agent_status({
                    "type": "thought",
                    "content": event.get("thought"),
                    "iteration": event.get("iteration")
                })
            elif event_status == "thought_delta":
                emit_agent_status({
                    "type": "thought_delta",
                    "delta": event.get("delta"),
                    "iteration": event.get("iteration")
                })

            elif event_status == "getting_action":
                emit_agent_status({
                    "type": "getting_action",
                    "iteration": event.get("iteration")
                })

            elif event_status == "action_delta":
                # Stream action text as it's being generated
                emit_agent_status({
                    "type": "action_delta",
                    "delta": event.get("delta"),
                    "iteration": event.get("iteration")
                })

            elif event_status == "action":
                reasoning_steps.append({
                    "type": "action",
                    "action": event.get("action"),
                    "param": event.get("param")
                })
                emit_agent_status({
                    "type": "action",
                    "action": event.get("action"),
                    "param": event.get("param"),
                    "iteration": event.get("iteration")
                })

            elif event_status == "observation":
                reasoning_steps.append({
                    "type": "observation",
                    "content": event.get("result_preview")
                })
                emit_agent_status({
                    "type": "observation",
                    "content": event.get("result_preview"),
                    "iteration": event.get("iteration")
                })
            elif event_status == "observation_delta":
                emit_agent_status({
                    "type": "observation_delta",
                    "delta": event.get("delta"),
                    "iteration": event.get("iteration")
                })

            elif event_status == "generating":
                emit_agent_status({
                    "type": "generating"
                })

            elif event_status == "final_answer":
                emit_agent_status({
                    "type": "final_answer"
                })

            elif event_status == "max_iterations_reached":
                emit_agent_status({
                    "type": "max_iterations"
                })

            elif event_status == "adaptive_iteration":
                emit_agent_status({
                    "type": "adaptive_iteration",
                    "iteration": event.get("iteration"),
                    "reason": event.get("reason")
                })

            elif event_status == "adaptive_response":
                emit_agent_status({
                    "type": "adaptive_response",
                    "reason": event.get("reason")
                })

            elif "delta" in event:
                # Streaming response chunk - replace URL placeholders
                delta_content = _replace_url_placeholders(event["delta"])
                emit("chatbot:response", {
                    "content": delta_content,
                    "complete": False
                }, room=client_id)
                socketio.sleep(0)
                final_response += delta_content

            elif "error" in event:
                emit("chatbot:error", {
                    "error": event["error"]
                }, room=client_id)

            elif event.get("done"):
                # Final response - apply URL placeholder replacement
                raw_response = event.get("full_response", final_response)
                final_response = _replace_url_placeholders(raw_response)
                all_sources = event.get("sources", [])
                reasoning_steps = event.get("reasoning_steps", reasoning_steps)
                conversation_id_result = event.get("conversation_id") or conversation_id
                message_id = event.get("message_id") or message_id

                # Stream title generation if needed
                conv = agent_service._get_or_create_conversation(session_id, username, conversation_id_result)
                if agent_service._is_placeholder_title(conv.title):
                    conversation_title = _stream_title_generation(
                        socketio, agent_service, conv, user_message, client_id
                    )
                    _commit_with_retry()  # Use retry logic to handle deadlocks
                else:
                    conversation_title = conv.title

        # Note: final_response is now streamed via delta events above,
        # so we don't need to send it all at once here

        # Send sources
        if all_sources:
            # Add footnote IDs
            for idx, source in enumerate(all_sources):
                source['footnote_id'] = idx + 1
            emit("chatbot:sources", {"sources": all_sources}, room=client_id)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Emit completion
        emit("chatbot:complete", {
            "mode": agent_mode,
            "task_type": task_type,
            "tokens": {
                "input": len(user_message) // 4,  # Rough estimate
                "output": len(final_response) // 4
            },
            "response_time_ms": response_time_ms,
            "reasoning_steps": reasoning_steps,
            "conversation_id": conversation_id_result,
            "session_id": session_id,
            "title": conversation_title,
            "message_id": message_id
        }, room=client_id)

        # Signal completion
        emit("chatbot:response", {
            "content": "",
            "complete": True
        }, room=client_id)
        socketio.sleep(0)

        logger.info(f"Agent {agent_mode} responded to chatbot {chatbot.name} in {response_time_ms}ms")

    except Exception as e:
        logger.error(f"Agent stream error: {e}", exc_info=True)
        emit("chatbot:error", {
            "error": "Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut."
        }, room=client_id)
        emit("chatbot:response", {
            "content": "",
            "complete": True
        }, room=client_id)


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
                emit("chatbot:error", {"error": "Authentication required", "code": "AUTH_REQUIRED"}, room=client_id)
                return

            payload = validate_token(token)
            if not payload:
                reason = _classify_token_error(token)
                emit(
                    "chatbot:error",
                    {
                        "error": f"Authentication failed: {reason}",
                        "code": "AUTH_EXPIRED" if reason == "jwt expired" else "AUTH_FAILED",
                    },
                    room=client_id
                )
                return

            username_from_token = (
                payload.get('preferred_username') or
                payload.get('username') or
                payload.get('name') or
                payload.get('uid') or
                payload.get('sub')
            )
            if not username_from_token:
                emit("chatbot:error", {"error": "Authentication failed", "code": "AUTH_FAILED"}, room=client_id)
                return

            # Ensure user exists in DB and enforce account state (locked/deleted)
            from auth.decorators import get_or_create_user
            user_obj = get_or_create_user(username_from_token)
            if getattr(user_obj, 'deleted_at', None) is not None:
                emit("chatbot:error", {"error": "Account has been deleted", "code": "ACCOUNT_DELETED"}, room=client_id)
                return
            if not bool(getattr(user_obj, 'is_active', True)):
                emit("chatbot:error", {"error": "Account is locked", "code": "ACCOUNT_LOCKED"}, room=client_id)
                return

            if not PermissionService.check_permission(username_from_token, 'feature:chatbots:view'):
                emit("chatbot:error", {"error": "Forbidden", "code": "FORBIDDEN"}, room=client_id)
                return

            chatbot_id = data.get("chatbot_id")
            user_message = data.get("message", "").strip()
            session_id = data.get("session_id")
            conversation_id = data.get("conversation_id")
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
                emit("chatbot:error", {"error": "Forbidden", "code": "FORBIDDEN"}, room=client_id)
                return

            if not chatbot.is_active:
                emit("chatbot:error", {"error": "Chatbot is not active", "code": "BOT_INACTIVE"}, room=client_id)
                return

            # Initialize service - use AgentChatService for agent modes
            agent_service = AgentChatService(chatbot_id)
            agent_mode = agent_service.get_agent_mode()

            # Route to agent handler for non-standard modes
            if agent_mode != 'standard':
                _handle_agent_stream(socketio, agent_service, chatbot, user_message, session_id, username, client_id, start_time, conversation_id=conversation_id)
                return

            # Standard mode - use regular ChatService
            chat_service = agent_service  # AgentChatService extends ChatService

            # Get or create conversation
            conversation = chat_service._get_or_create_conversation(session_id, username, conversation_id)

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
            elif chat_service._requires_sources():
                # RAG is enabled but produced no sources. Avoid hallucinations by returning fallback directly.
                fallback = chat_service.get_unknown_answer()

                response_time_ms = int((time.time() - start_time) * 1000)
                tokens_input = 0
                tokens_output = 0

                assistant_msg = chat_service._save_message(
                    conversation.id,
                    ChatbotMessageRole.ASSISTANT,
                    fallback,
                    rag_context=None,
                    rag_sources=[],
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    response_time_ms=response_time_ms
                )

                conversation.message_count += 2
                conversation.last_message_at = datetime.now()
                chat_service._maybe_set_conversation_title(conversation, user_message)
                _commit_with_retry()  # Use retry logic to handle deadlocks

                emit("chatbot:response", {"content": fallback, "complete": False}, room=client_id)
                emit("chatbot:complete", {
                    "conversation_id": conversation.id,
                    "message_id": assistant_msg.id,
                    "tokens": {"input": tokens_input, "output": tokens_output},
                    "response_time_ms": response_time_ms,
                    "title": conversation.title
                }, room=client_id)
                emit("chatbot:response", {"content": "", "complete": True}, room=client_id)
                logger.info(f"Chatbot {chatbot.name} returned fallback (no sources) in {response_time_ms}ms")
                return

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

            # Initialize LLM client (provider-aware, including user-provider models)
            llm_client, api_model_id = LLMClientFactory.resolve_client_and_model_id(chatbot.model_name)
            api_model_id = api_model_id or chatbot.model_name

            # Stream response
            assistant_message = ""
            tokens_input = 0
            tokens_output = 0

            stream = llm_client.chat.completions.create(
                model=api_model_id,
                messages=messages,
                temperature=chatbot.temperature,
                max_tokens=chatbot.max_tokens,
                top_p=chatbot.top_p,
                stream=True
            )

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = (
                    getattr(delta, "content", None)
                    or getattr(delta, "reasoning_content", None)
                    or ""
                )

                if isinstance(content, list):
                    content = "".join(
                        [
                            getattr(part, 'text', '') if hasattr(part, 'text') else str(part)
                            for part in content
                            if part is not None
                        ]
                    )

                if content:
                    # Replace URL placeholders before sending
                    content = _replace_url_placeholders(content)
                    assistant_message += content
                    emit("chatbot:response", {
                        "content": content,
                        "complete": False
                    }, room=client_id)
                    socketio.sleep(0)

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

            # Stream title generation if needed
            if chat_service._is_placeholder_title(conversation.title):
                _stream_title_generation(socketio, chat_service, conversation, user_message, client_id)

            _commit_with_retry()  # Use retry logic to handle deadlocks

            # Emit completion with metadata
            emit("chatbot:complete", {
                "conversation_id": conversation.id,
                "message_id": assistant_msg.id,
                "tokens": {
                    "input": tokens_input,
                    "output": tokens_output
                },
                "response_time_ms": response_time_ms,
                "title": conversation.title
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
