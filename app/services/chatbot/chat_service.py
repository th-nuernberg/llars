# chat_service.py
"""
Service for handling chat interactions with chatbots including RAG retrieval.
Supports file uploads (images for Vision, documents via OCR).

This is the main orchestration service that coordinates:
- ChatTitleService: Title generation
- ChatPromptBuilder: Prompt and context formatting
- ChatRAGRetrieval: RAG search and retrieval
- ChatConversationService: Conversation CRUD
"""

import os
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from openai import OpenAI

from db.db import db
from db.tables import (
    Chatbot,
    ChatbotConversation,
    ChatbotMessage,
    ChatbotMessageRole,
)
from rag_pipeline import RAGPipeline
from services.chatbot.file_processor import FileProcessor, file_processor
from services.chatbot.chat_title_service import ChatTitleService
from services.chatbot.chat_prompt_builder import ChatPromptBuilder
from services.chatbot.chat_rag_retrieval import ChatRAGRetrieval
from services.chatbot.chat_conversation_service import ChatConversationService
from llm.openai_utils import extract_delta_text, extract_message_text

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chatbot chat interactions with Multi-Collection RAG"""

    def __init__(self, chatbot_id: int):
        self.chatbot = Chatbot.query.get(chatbot_id)
        if not self.chatbot:
            raise ValueError(f"Chatbot with ID {chatbot_id} not found")

        self.rag_pipeline = RAGPipeline() if self.chatbot.rag_enabled else None

        # Initialize LLM client
        self.llm_client = OpenAI(
            api_key=os.environ.get('LITELLM_API_KEY'),
            base_url=os.environ.get('LITELLM_BASE_URL')
        )

        # Initialize helper services
        self.prompt_builder = ChatPromptBuilder(self.chatbot)
        self.rag_retrieval = ChatRAGRetrieval(self.chatbot, self.rag_pipeline)

    # ========== Delegate methods for backward compatibility ==========

    def get_unknown_answer(self) -> str:
        """Get the configured 'unknown answer' response for RAG."""
        return self.prompt_builder.get_unknown_answer()

    def _requires_sources(self) -> bool:
        """Check if the chatbot requires RAG sources for responses."""
        return self.prompt_builder.requires_sources()

    def _build_citation_instructions(self) -> str:
        """Build citation instructions to append to system prompt."""
        return self.prompt_builder.build_citation_instructions()

    def _build_numbered_context(self, sources: List[Dict[str, Any]]) -> str:
        """Build numbered context string from sources."""
        return self.prompt_builder.build_numbered_context(sources)

    def _get_prompt_settings(self):
        """Get prompt settings from chatbot."""
        return self.prompt_builder._get_prompt_settings()

    def _generate_smart_title(self, message: Optional[str], stream_callback=None) -> Optional[str]:
        """Generate an intelligent short title using LLM."""
        return ChatTitleService.generate_smart_title(message, stream_callback)

    def _maybe_set_conversation_title(self, conversation: ChatbotConversation, message: Optional[str]) -> bool:
        """Update conversation title if it's a placeholder."""
        return ChatTitleService.maybe_update_conversation_title(conversation, message)

    def _is_placeholder_title(self, title: Optional[str]) -> bool:
        """Check if the title is a placeholder (delegate to ChatTitleService)."""
        return ChatTitleService.is_placeholder_title(title)

    def _get_multi_collection_context(self, query: str) -> Tuple[str, List[Dict]]:
        """Retrieve context from multiple collections using semantic search."""
        return self.rag_retrieval.get_multi_collection_context(query)

    def _search_collection(self, collection, query: str, k: int = 4) -> List[Dict]:
        """Search a specific collection using ChromaDB."""
        return self.rag_retrieval.search_collection(collection, query, k)

    def _extract_lexical_tokens(self, query: str) -> List[str]:
        """Extract and expand lexical tokens from query."""
        return self.rag_retrieval.extract_lexical_tokens(query)

    def _lexical_search_collection(self, collection, query: str, tokens: List[str], limit: int) -> List[Dict[str, Any]]:
        """Perform lexical search on a collection."""
        return self.rag_retrieval.lexical_search_collection(collection, query, tokens, limit)

    def _get_or_create_conversation(self, session_id: str, username: str = None, conversation_id: Optional[int] = None) -> ChatbotConversation:
        """Get existing conversation or create a new one (delegate to ChatConversationService)."""
        return ChatConversationService.get_or_create_conversation(
            self.chatbot.id, session_id, username, conversation_id
        )

    def _save_message(
        self,
        conversation_id: int,
        role: ChatbotMessageRole,
        content: str,
        rag_context: str = None,
        rag_sources: List[Dict] = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        response_time_ms: int = None,
        stream_metadata: Dict = None,
        agent_trace: List[Dict] = None
    ) -> ChatbotMessage:
        """Save a message to the conversation (delegate to ChatConversationService)."""
        return ChatConversationService.save_message(
            conversation_id, role, content,
            rag_context=rag_context,
            rag_sources=rag_sources,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms,
            stream_metadata=stream_metadata,
            agent_trace=agent_trace
        )

    # ========== Main Chat Methods ==========

    def chat(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main method for chat interaction with RAG support and file handling.

        Args:
            message: User's message
            session_id: Session ID for conversation tracking
            username: Optional username
            include_sources: Whether to include source references
            files: List of processed file dicts from file_processor
            conversation_id: Optional specific conversation ID

        Returns:
            Dict with response, sources, and metadata
        """
        start_time = time.time()

        # 1. Get or create conversation
        conversation = ChatConversationService.get_or_create_conversation(
            self.chatbot.id, session_id, username, conversation_id
        )

        # 2. Save user message
        user_msg = ChatConversationService.save_message(
            conversation.id, ChatbotMessageRole.USER, message
        )

        # 3. Get RAG context if enabled
        rag_context = ""
        sources = []
        retrieval_time_ms = None
        if self.chatbot.rag_enabled and self.chatbot.collections:
            retrieval_start = time.time()
            rag_context, sources = self._get_multi_collection_context(message)
            retrieval_time_ms = int((time.time() - retrieval_start) * 1000)

        # If RAG is enabled but no context, avoid hallucinations
        if self._requires_sources() and not sources and not files:
            response_text = self.get_unknown_answer()
            response_time_ms = int((time.time() - start_time) * 1000)

            assistant_msg = ChatConversationService.save_message(
                conversation.id,
                ChatbotMessageRole.ASSISTANT,
                response_text,
                rag_context=None,
                rag_sources=[],
                tokens_input=0,
                tokens_output=0,
                response_time_ms=response_time_ms,
                stream_metadata={
                    "retrieval_time_ms": retrieval_time_ms,
                    "sources_count": len(sources),
                    "mode": "standard"
                }
            )

            conversation.message_count += 2
            conversation.last_message_at = datetime.now()
            self._maybe_set_conversation_title(conversation, message)
            db.session.commit()

            return {
                'response': response_text,
                'sources': [],
                'conversation_id': conversation.id,
                'session_id': session_id,
                'title': conversation.title,
                'message_id': assistant_msg.id,
                'tokens': {'input': 0, 'output': 0},
                'response_time_ms': response_time_ms,
                'files_processed': len(files) if files else 0
            }

        # 4. Build prompt with context, history, and files
        messages = self._build_messages(conversation, message, rag_context, files, sources=sources)

        # 5. Call LLM (with vision support if needed)
        has_images = files and any(
            f.get('type') == 'image' and f.get('image_data')
            for f in files
        )
        response_text, tokens_input, tokens_output = self._call_llm(messages, use_vision=has_images)

        # 6. Handle fallback on empty response
        if response_text is None or not str(response_text).strip():
            fallback = (self.chatbot.fallback_message or "").strip()
            response_text = fallback or (self.get_unknown_answer() if self.chatbot.rag_enabled else "")

        response_time_ms = int((time.time() - start_time) * 1000)

        # 7. Save assistant message
        sources_to_save = sources if self.chatbot.rag_include_sources else []
        assistant_msg = ChatConversationService.save_message(
            conversation.id,
            ChatbotMessageRole.ASSISTANT,
            response_text,
            rag_context=rag_context if rag_context else None,
            rag_sources=sources_to_save,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms,
            stream_metadata={
                "retrieval_time_ms": retrieval_time_ms,
                "sources_count": len(sources),
                "mode": "standard"
            }
        )

        # 8. Update conversation
        conversation.message_count += 2
        conversation.last_message_at = datetime.now()
        self._maybe_set_conversation_title(conversation, message)
        db.session.commit()

        return {
            'response': response_text,
            'sources': sources_to_save if include_sources else [],
            'conversation_id': conversation.id,
            'session_id': session_id,
            'title': conversation.title,
            'message_id': assistant_msg.id,
            'tokens': {
                'input': tokens_input,
                'output': tokens_output
            },
            'response_time_ms': response_time_ms,
            'files_processed': len(files) if files else 0
        }

    def test_chat(self, message: str) -> Dict[str, Any]:
        """
        Test chat without saving to database.
        Useful for previewing chatbot responses.
        """
        start_time = time.time()

        # Get RAG context if enabled
        rag_context = ""
        sources = []
        if self.chatbot.rag_enabled and self.chatbot.collections:
            rag_context, sources = self._get_multi_collection_context(message)

        if self._requires_sources() and not sources:
            response_time_ms = int((time.time() - start_time) * 1000)
            return {
                'response': self.get_unknown_answer(),
                'sources': [],
                'tokens': {'input': 0, 'output': 0},
                'response_time_ms': response_time_ms,
                'test_mode': True
            }

        # Build messages (no history in test mode)
        system_prompt = self.chatbot.system_prompt
        require_citations = self.prompt_builder.get_require_citations()
        if sources and require_citations:
            system_prompt += self._build_citation_instructions()

        messages = [{"role": "system", "content": system_prompt}]

        if sources:
            messages.append({"role": "system", "content": self._build_numbered_context(sources)})
        elif rag_context:
            messages.append({"role": "system", "content": f"Kontext:\n\n{rag_context}"})

        messages.append({"role": "user", "content": message})

        # Call LLM
        response_text, tokens_input, tokens_output = self._call_llm(messages)

        response_time_ms = int((time.time() - start_time) * 1000)

        return {
            'response': response_text,
            'sources': sources if self.chatbot.rag_include_sources else [],
            'tokens': {
                'input': tokens_input,
                'output': tokens_output
            },
            'response_time_ms': response_time_ms,
            'test_mode': True
        }

    def test_chat_stream(self, message: str):
        """
        Stream test chat response tokens (Server-Sent Events friendly).
        Yields dicts with delta chunks and a final done payload.
        """
        start_time = time.time()

        # Get RAG context if enabled
        rag_context = ""
        sources = []
        if self.chatbot.rag_enabled and self.chatbot.collections:
            rag_context, sources = self._get_multi_collection_context(message)

        if self._requires_sources() and not sources:
            response_time_ms = int((time.time() - start_time) * 1000)
            unknown = self.get_unknown_answer()
            yield {"delta": unknown}
            yield {
                "done": True,
                "full_response": unknown,
                "sources": [],
                "tokens": None,
                "response_time_ms": response_time_ms,
                "test_mode": True
            }
            return

        # Build messages (no history in test mode)
        system_prompt = self.chatbot.system_prompt
        require_citations = self.prompt_builder.get_require_citations()
        if sources and require_citations:
            system_prompt += self._build_citation_instructions()

        messages = [{"role": "system", "content": system_prompt}]

        if sources:
            messages.append({"role": "system", "content": self._build_numbered_context(sources)})
        elif rag_context:
            messages.append({"role": "system", "content": f"Kontext:\n\n{rag_context}"})

        messages.append({"role": "user", "content": message})

        try:
            completion_kwargs = {
                "model": self.chatbot.model_name,
                "messages": messages,
                "temperature": self.chatbot.temperature,
                "top_p": self.chatbot.top_p,
                "stream": True
            }
            if self.chatbot.max_tokens:
                completion_kwargs["max_tokens"] = self.chatbot.max_tokens

            stream = self.llm_client.chat.completions.create(**completion_kwargs)

            accumulated = ""
            for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                delta_obj = getattr(choice, "delta", None) if choice else None
                delta_text = extract_delta_text(delta_obj)
                if not delta_text:
                    continue

                accumulated += delta_text
                yield {"delta": delta_text}

            response_time_ms = int((time.time() - start_time) * 1000)

            yield {
                "done": True,
                "full_response": accumulated,
                "sources": sources if self.chatbot.rag_include_sources else [],
                "tokens": None,
                "response_time_ms": response_time_ms,
                "test_mode": True
            }

        except Exception as e:
            logger.error(f"[ChatService] Streaming test_chat failed: {e}")
            yield {"error": str(e)}

    # ========== Message Building ==========

    def _build_messages(
        self,
        conversation: ChatbotConversation,
        current_message: str,
        rag_context: str,
        files: List[Dict[str, Any]] = None,
        *,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build the message list for LLM including history, context, and files.
        Supports Vision API format for images.
        """
        messages = []

        # System prompt
        system_prompt = self.chatbot.system_prompt
        require_citations = self.prompt_builder.get_require_citations()
        if sources and require_citations:
            system_prompt += self._build_citation_instructions()

        messages.append({"role": "system", "content": system_prompt})

        # RAG context as system message
        if sources:
            numbered_context = self._build_numbered_context(sources)
            if numbered_context:
                messages.append({"role": "system", "content": numbered_context})
        elif rag_context:
            messages.append({"role": "system", "content": f"Kontext:\n\n{rag_context}"})

        # Add document content from files (non-image)
        if files:
            doc_text = file_processor.format_for_prompt([
                f for f in files if f.get('type') == 'document' or f.get('text_content')
            ])
            if doc_text:
                messages.append({"role": "system", "content": doc_text})

        # Chat history (limited)
        history = ChatbotMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(ChatbotMessage.created_at.desc()).limit(
            self.chatbot.max_context_messages * 2
        ).all()

        history.reverse()

        for msg in history:
            role = "user" if msg.role == ChatbotMessageRole.USER else "assistant"
            messages.append({"role": role, "content": msg.content})

        # Current user message (with images if vision model)
        use_vision = FileProcessor.is_vision_model(self.chatbot.model_name)
        rag_images = self._get_rag_images(sources) if use_vision and sources else []

        user_images = []
        if files:
            user_images = [
                f for f in files
                if f.get('type') == 'image' and f.get('image_data')
            ]

        if use_vision and (rag_images or user_images):
            user_content = self._build_vision_content(current_message, rag_images, user_images)
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": current_message})

        return messages

    def _get_rag_images(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and process images from RAG sources."""
        rag_images = []
        seen_paths = set()

        for source in sources:
            if not source.get('has_image'):
                continue
            image_path = source.get('image_path')
            if not image_path or image_path in seen_paths:
                continue
            seen_paths.add(image_path)
            try:
                with open(image_path, 'rb') as f:
                    processed = file_processor.process_file(
                        f.read(),
                        os.path.basename(image_path),
                        model_name=self.chatbot.model_name
                    )
                if processed.get('type') == 'image' and processed.get('image_data'):
                    rag_images.append(processed)
            except Exception as e:
                logger.debug(f"[ChatService] Failed to load RAG image {image_path}: {e}")

        return rag_images

    def _build_vision_content(
        self,
        message: str,
        rag_images: List[Dict[str, Any]],
        user_images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build vision-enabled user content with images."""
        user_content = []

        if rag_images:
            user_content.append({"type": "text", "text": "Kontextbilder aus der Wissensbasis:"})
            for img in rag_images:
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img.get('mime_type', 'image/jpeg')};base64,{img['image_data']}"
                    }
                })

        if user_images:
            if rag_images:
                user_content.append({"type": "text", "text": "Vom Nutzer hochgeladene Bilder:"})
            for img in user_images:
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img.get('mime_type', 'image/jpeg')};base64,{img['image_data']}"
                    }
                })

        user_content.append({"type": "text", "text": message})
        return user_content

    # ========== LLM Interaction ==========

    def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        use_vision: bool = False
    ) -> Tuple[str, int, int]:
        """
        Call the LLM API and return response with token counts.
        """
        try:
            completion_kwargs = {
                "model": self.chatbot.model_name,
                "messages": messages,
                "temperature": self.chatbot.temperature,
                "top_p": self.chatbot.top_p
            }

            max_tokens = self.chatbot.max_tokens
            if max_tokens:
                model_info = FileProcessor.get_model_info(self.chatbot.model_name)
                if model_info and model_info.get("supports_reasoning"):
                    max_tokens = None
            if max_tokens:
                completion_kwargs["max_tokens"] = max_tokens

            response = self.llm_client.chat.completions.create(**completion_kwargs)

            response_text = ""
            if getattr(response, 'choices', None):
                response_text = extract_message_text(response.choices[0].message)

            tokens_input = response.usage.prompt_tokens if response.usage else 0
            tokens_output = response.usage.completion_tokens if response.usage else 0

            return response_text, tokens_input, tokens_output

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def supports_vision(self) -> bool:
        """Check if this chatbot's model supports vision."""
        return FileProcessor.is_vision_model(self.chatbot.model_name)

    # ========== Static Conversation Methods (backward compatibility) ==========

    @staticmethod
    def get_conversations(chatbot_id: int, username: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversations for a chatbot."""
        return ChatConversationService.get_conversations(chatbot_id, username, limit)

    @staticmethod
    def get_conversation(
        conversation_id: int,
        username: str = None,
        chatbot_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a single conversation with all messages."""
        return ChatConversationService.get_conversation(conversation_id, username, chatbot_id)

    @staticmethod
    def create_conversation(
        chatbot_id: int,
        username: str = None,
        title: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new conversation for a chatbot."""
        return ChatConversationService.create_conversation(chatbot_id, username, title, session_id)

    @staticmethod
    def delete_conversation(conversation_id: int, username: str = None) -> bool:
        """Delete a conversation and all its messages."""
        return ChatConversationService.delete_conversation(conversation_id, username)

    @staticmethod
    def rate_message(message_id: int, rating: str, feedback: str = None) -> bool:
        """Rate a message (helpful, not_helpful, incorrect)."""
        return ChatConversationService.rate_message(message_id, rating, feedback)
