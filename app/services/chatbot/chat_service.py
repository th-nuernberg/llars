# chat_service.py
"""
Service for handling chat interactions with chatbots including RAG retrieval.
Supports file uploads (images for Vision, documents via OCR).
"""

import os
import logging
import uuid
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from openai import OpenAI
from db.db import db
from db.tables import (
    Chatbot, ChatbotCollection, ChatbotConversation, ChatbotMessage,
    ChatbotMessageRole, RAGCollection, RAGDocument, RAGDocumentChunk
)
from rag_pipeline import RAGPipeline
from services.chatbot.file_processor import FileProcessor, file_processor

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

    def chat(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method for chat interaction with RAG support and file handling.

        Args:
            message: User's message
            session_id: Session ID for conversation tracking
            username: Optional username
            include_sources: Whether to include source references
            files: List of processed file dicts from file_processor

        Returns:
            Dict with response, sources, and metadata
        """
        start_time = time.time()

        # 1. Get or create conversation
        conversation = self._get_or_create_conversation(session_id, username)

        # 2. Save user message
        user_msg = self._save_message(conversation.id, ChatbotMessageRole.USER, message)

        # 3. Get RAG context if enabled
        rag_context = ""
        sources = []
        if self.chatbot.rag_enabled and self.chatbot.collections:
            rag_context, sources = self._get_multi_collection_context(message)

        # 4. Build prompt with context, history, and files
        messages = self._build_messages(conversation, message, rag_context, files)

        # 5. Call LLM (with vision support if needed)
        has_images = files and any(
            f.get('type') == 'image' and f.get('image_data')
            for f in files
        )
        response_text, tokens_input, tokens_output = self._call_llm(
            messages,
            use_vision=has_images
        )

        # 6. Handle fallback if no RAG results and empty response
        if not sources and self.chatbot.fallback_message and not response_text.strip():
            response_text = self.chatbot.fallback_message

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # 7. Save assistant message
        sources_to_save = sources if self.chatbot.rag_include_sources else []
        assistant_msg = self._save_message(
            conversation.id,
            ChatbotMessageRole.ASSISTANT,
            response_text,
            rag_context=rag_context if rag_context else None,
            rag_sources=sources_to_save,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms
        )

        # 8. Update conversation
        conversation.message_count += 2
        conversation.last_message_at = datetime.now()
        if not conversation.title and len(message) > 0:
            conversation.title = message[:50] + ('...' if len(message) > 50 else '')
        db.session.commit()

        return {
            'response': response_text,
            'sources': sources_to_save if include_sources else [],
            'conversation_id': conversation.id,
            'session_id': session_id,
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

        # Build messages (no history in test mode)
        messages = [
            {"role": "system", "content": self.chatbot.system_prompt}
        ]

        if rag_context:
            messages.append({
                "role": "system",
                "content": f"Kontext aus Dokumenten:\n\n{rag_context}"
            })

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

        # Build messages (no history in test mode)
        messages = [
            {"role": "system", "content": self.chatbot.system_prompt}
        ]

        if rag_context:
            messages.append({
                "role": "system",
                "content": f"Kontext aus Dokumenten:\n\n{rag_context}"
            })

        messages.append({"role": "user", "content": message})

        try:
            stream = self.llm_client.chat.completions.create(
                model=self.chatbot.model_name,
                messages=messages,
                temperature=self.chatbot.temperature,
                max_tokens=self.chatbot.max_tokens,
                top_p=self.chatbot.top_p,
                stream=True
            )

            accumulated = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if not delta:
                    continue
                # Handle list-of-parts vs string
                if isinstance(delta, list):
                    delta_text = "".join([getattr(part, 'text', '') if hasattr(part, 'text') else str(part) for part in delta])
                else:
                    delta_text = delta

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

    def _get_or_create_conversation(self, session_id: str, username: str = None) -> ChatbotConversation:
        """
        Get existing conversation or create a new one.
        """
        conversation = ChatbotConversation.query.filter_by(session_id=session_id).first()

        if not conversation:
            conversation = ChatbotConversation(
                chatbot_id=self.chatbot.id,
                session_id=session_id,
                username=username,
                is_active=True
            )
            db.session.add(conversation)
            db.session.flush()
            logger.info(f"Created new conversation {session_id} for chatbot {self.chatbot.name}")

        return conversation

    def _save_message(
        self,
        conversation_id: int,
        role: ChatbotMessageRole,
        content: str,
        rag_context: str = None,
        rag_sources: List[Dict] = None,
        tokens_input: int = None,
        tokens_output: int = None,
        response_time_ms: int = None
    ) -> ChatbotMessage:
        """
        Save a message to the database.
        """
        message = ChatbotMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            rag_context=rag_context,
            rag_sources=rag_sources,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms
        )
        db.session.add(message)
        db.session.flush()
        return message

    def _get_multi_collection_context(self, query: str) -> Tuple[str, List[Dict]]:
        """
        Retrieve context from multiple collections with weighting.

        Returns:
            Tuple of (context_string, sources_list)
        """
        if not self.rag_pipeline:
            return "", []

        all_results = []

        # Query each assigned collection
        for cc in sorted(self.chatbot.collections, key=lambda x: -x.priority):
            collection = cc.collection
            if not collection.chroma_collection_name:
                continue

            try:
                # Use RAG pipeline to search
                results = self._search_collection(
                    collection,
                    query,
                    k=self.chatbot.rag_retrieval_k
                )

                # Apply weight and add collection info
                for result in results:
                    result['score'] *= cc.weight
                    result['collection_id'] = collection.id
                    result['collection_name'] = collection.display_name

                all_results.extend(results)

            except Exception as e:
                logger.error(f"Error searching collection {collection.name}: {e}")
                continue

        if not all_results:
            return "", []

        # Sort by score and take top K
        all_results.sort(key=lambda x: x['score'], reverse=True)
        top_results = all_results[:self.chatbot.rag_retrieval_k]

        # Filter by minimum relevance
        filtered_results = [
            r for r in top_results
            if r['score'] >= self.chatbot.rag_min_relevance
        ]

        if not filtered_results:
            return "", []

        # Build context string
        context_parts = []
        sources = []

        for i, result in enumerate(filtered_results):
            context_parts.append(f"[Dokument {i+1}]\n{result['content']}")
            sources.append({
                'document_id': result.get('document_id'),
                'title': result.get('title', 'Unbekannt'),
                'collection_name': result.get('collection_name'),
                'relevance': round(result['score'], 3),
                'excerpt': result['content'][:200] + '...' if len(result['content']) > 200 else result['content']
            })

        context = "\n\n---\n\n".join(context_parts)

        return context, sources

    def _search_collection(
        self,
        collection: RAGCollection,
        query: str,
        k: int = 4
    ) -> List[Dict]:
        """
        Search a specific collection using ChromaDB.
        """
        from langchain_chroma import Chroma

        vectorstore_dir = os.path.join(
            "/app/storage/vectorstore",
            self.rag_pipeline.model_name.replace('/', '_')
        )

        try:
            vectorstore = Chroma(
                collection_name=collection.chroma_collection_name,
                persist_directory=vectorstore_dir,
                embedding_function=self.rag_pipeline.embeddings
            )

            # Perform similarity search with scores
            docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)

            results = []
            for doc, score in docs_with_scores:
                # Get document info from metadata
                doc_id = doc.metadata.get('document_id')
                title = doc.metadata.get('title', doc.metadata.get('source', 'Unbekannt'))

                # Convert L2 distance to cosine similarity for normalized vectors
                # For normalized vectors: L2_distance^2 = 2 * (1 - cosine_similarity)
                # Therefore: cosine_similarity = 1 - (L2_distance^2 / 2)
                # Clamp to [0, 1] to handle any numerical edge cases
                similarity = max(0.0, min(1.0, 1 - (score ** 2) / 2))

                results.append({
                    'content': doc.page_content,
                    'score': similarity,
                    'document_id': doc_id,
                    'title': title,
                    'metadata': doc.metadata
                })

            return results

        except Exception as e:
            logger.error(f"Error searching collection {collection.name}: {e}")
            return []

    def _build_messages(
        self,
        conversation: ChatbotConversation,
        current_message: str,
        rag_context: str,
        files: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build the message list for LLM including history, context, and files.
        Supports Vision API format for images.
        """
        messages = []

        # System prompt
        messages.append({
            "role": "system",
            "content": self.chatbot.system_prompt
        })

        # RAG context as system message
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"Nutze den folgenden Kontext aus der Wissensdatenbank, um die Frage zu beantworten:\n\n{rag_context}"
            })

        # Add document content from files (non-image)
        if files:
            doc_text = file_processor.format_for_prompt([
                f for f in files if f.get('type') == 'document' or f.get('text_content')
            ])
            if doc_text:
                messages.append({
                    "role": "system",
                    "content": doc_text
                })

        # Chat history (limited)
        history = ChatbotMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(ChatbotMessage.created_at.desc()).limit(
            self.chatbot.max_context_messages * 2  # *2 for user+assistant pairs
        ).all()

        history.reverse()  # Oldest first

        for msg in history:
            role = "user" if msg.role == ChatbotMessageRole.USER else "assistant"
            messages.append({
                "role": role,
                "content": msg.content
            })

        # Current user message (with images if vision model)
        if files and FileProcessor.is_vision_model(self.chatbot.model_name):
            # Build multimodal content
            user_content = []

            # Add images
            for f in files:
                if f.get('type') == 'image' and f.get('image_data'):
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{f.get('mime_type', 'image/jpeg')};base64,{f['image_data']}"
                        }
                    })

            # Add text message
            user_content.append({
                "type": "text",
                "text": current_message
            })

            messages.append({
                "role": "user",
                "content": user_content
            })
        else:
            messages.append({
                "role": "user",
                "content": current_message
            })

        return messages

    def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        use_vision: bool = False
    ) -> Tuple[str, int, int]:
        """
        Call the LLM API and return response with token counts.
        Supports vision models for image analysis.
        """
        try:
            # For vision models with images, we might need to adjust max_tokens
            max_tokens = self.chatbot.max_tokens
            if use_vision and max_tokens < 1000:
                max_tokens = 1000  # Ensure enough tokens for image analysis

            response = self.llm_client.chat.completions.create(
                model=self.chatbot.model_name,
                messages=messages,
                temperature=self.chatbot.temperature,
                max_tokens=max_tokens,
                top_p=self.chatbot.top_p
            )

            response_text = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens if response.usage else 0
            tokens_output = response.usage.completion_tokens if response.usage else 0

            return response_text, tokens_input, tokens_output

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def supports_vision(self) -> bool:
        """Check if this chatbot's model supports vision."""
        return FileProcessor.is_vision_model(self.chatbot.model_name)

    # ========== Conversation Management Methods ==========

    @staticmethod
    def get_conversations(chatbot_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all conversations for a chatbot.
        """
        conversations = ChatbotConversation.query.filter_by(
            chatbot_id=chatbot_id
        ).order_by(ChatbotConversation.last_message_at.desc()).limit(limit).all()

        return [
            {
                'id': c.id,
                'session_id': c.session_id,
                'username': c.username,
                'title': c.title,
                'message_count': c.message_count,
                'is_active': c.is_active,
                'started_at': c.started_at.isoformat() if c.started_at else None,
                'last_message_at': c.last_message_at.isoformat() if c.last_message_at else None
            }
            for c in conversations
        ]

    @staticmethod
    def get_conversation(conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single conversation with all messages.
        """
        conversation = ChatbotConversation.query.get(conversation_id)
        if not conversation:
            return None

        messages = ChatbotMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatbotMessage.created_at.asc()).all()

        return {
            'id': conversation.id,
            'session_id': conversation.session_id,
            'chatbot_id': conversation.chatbot_id,
            'username': conversation.username,
            'title': conversation.title,
            'message_count': conversation.message_count,
            'is_active': conversation.is_active,
            'started_at': conversation.started_at.isoformat() if conversation.started_at else None,
            'last_message_at': conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            'messages': [
                {
                    'id': m.id,
                    'role': m.role.value if hasattr(m.role, 'value') else m.role,
                    'content': m.content,
                    'rag_sources': m.rag_sources,
                    'tokens_input': m.tokens_input,
                    'tokens_output': m.tokens_output,
                    'response_time_ms': m.response_time_ms,
                    'user_rating': m.user_rating,
                    'created_at': m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ]
        }

    @staticmethod
    def delete_conversation(conversation_id: int) -> bool:
        """
        Delete a conversation and all its messages.
        """
        conversation = ChatbotConversation.query.get(conversation_id)
        if not conversation:
            return False

        db.session.delete(conversation)
        db.session.commit()

        logger.info(f"Deleted conversation {conversation_id}")
        return True

    @staticmethod
    def rate_message(message_id: int, rating: str, feedback: str = None) -> bool:
        """
        Rate a message (helpful, not_helpful, incorrect).
        """
        message = ChatbotMessage.query.get(message_id)
        if not message:
            return False

        message.user_rating = rating
        message.user_feedback = feedback
        db.session.commit()

        return True
