# chat_conversation_service.py
"""
Service for managing chat conversations - CRUD operations, message saving, and ratings.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional

from db.database import db
from db.tables import (
    ChatbotConversation,
    ChatbotMessage,
    ChatbotMessageRole
)

logger = logging.getLogger(__name__)


class ChatConversationService:
    """Service for chat conversation CRUD operations."""

    @staticmethod
    def get_or_create_conversation(
        chatbot_id: int,
        session_id: str,
        username: str = None,
        conversation_id: Optional[int] = None
    ) -> ChatbotConversation:
        """
        Get existing conversation or create a new one.

        Args:
            chatbot_id: ID of the chatbot
            session_id: Session identifier
            username: Optional username for ownership
            conversation_id: Optional specific conversation ID

        Returns:
            ChatbotConversation instance
        """
        # Prefer explicit conversation_id
        if conversation_id:
            conversation = ChatbotConversation.query.filter_by(
                id=conversation_id,
                chatbot_id=chatbot_id
            ).first()
            if conversation and conversation.username and username and conversation.username != username:
                logger.warning(
                    f"[ChatConversationService] User {username} attempted to access "
                    f"conversation {conversation_id} owned by {conversation.username}"
                )
                conversation = None
            if conversation:
                return conversation

        # Look up by session_id
        conversation = ChatbotConversation.query.filter_by(
            chatbot_id=chatbot_id,
            session_id=session_id
        ).first()

        # If conversation exists but belongs to different user, create new one
        if conversation and conversation.username and username and conversation.username != username:
            conversation = None

        if not conversation:
            conversation = ChatbotConversation(
                chatbot_id=chatbot_id,
                session_id=session_id,
                username=username,
                is_active=True
            )
            db.session.add(conversation)
            db.session.flush()
            logger.info(f"Created new conversation {session_id} for chatbot {chatbot_id}")

        return conversation

    @staticmethod
    def save_message(
        conversation_id: int,
        role: ChatbotMessageRole,
        content: str,
        rag_context: str = None,
        rag_sources: List[Dict] = None,
        tokens_input: int = None,
        tokens_output: int = None,
        response_time_ms: int = None,
        agent_trace: Optional[List[Dict[str, Any]]] = None,
        stream_metadata: Optional[Dict[str, Any]] = None
    ) -> ChatbotMessage:
        """
        Save a message to the database.

        Args:
            conversation_id: ID of the conversation
            role: Message role (USER or ASSISTANT)
            content: Message content
            rag_context: Optional RAG context used
            rag_sources: Optional list of source dicts
            tokens_input: Input token count
            tokens_output: Output token count
            response_time_ms: Response time in milliseconds
            agent_trace: Optional agent trace for ACT/ReAct modes
            stream_metadata: Optional streaming metadata

        Returns:
            Created ChatbotMessage instance
        """
        message = ChatbotMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            rag_context=rag_context,
            rag_sources=rag_sources,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms,
            agent_trace=agent_trace,
            stream_metadata=stream_metadata
        )
        db.session.add(message)
        db.session.flush()
        return message

    @staticmethod
    def get_conversations(
        chatbot_id: int,
        username: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversations for a chatbot, filtered by username for data isolation.

        Args:
            chatbot_id: The chatbot ID
            username: Filter by this user (required for non-admin access)
            limit: Maximum number of conversations to return

        Returns:
            List of conversation dicts
        """
        query = ChatbotConversation.query.filter_by(chatbot_id=chatbot_id)

        # SECURITY: Always filter by username to ensure data isolation
        if username:
            query = query.filter_by(username=username)

        conversations = query.order_by(
            ChatbotConversation.last_message_at.desc()
        ).limit(limit).all()

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
    def get_conversation(
        conversation_id: int,
        username: str = None,
        chatbot_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single conversation with all messages.

        Args:
            conversation_id: The conversation ID
            username: If provided, verify the conversation belongs to this user
            chatbot_id: Optional chatbot ID filter

        Returns:
            Conversation dict or None if not found/not authorized
        """
        query = ChatbotConversation.query.filter_by(id=conversation_id)
        if chatbot_id:
            query = query.filter_by(chatbot_id=chatbot_id)
        conversation = query.first()
        if not conversation:
            return None

        # SECURITY: Verify ownership if username is provided
        if username and conversation.username != username:
            logger.warning(
                f"User {username} attempted to access conversation "
                f"{conversation_id} owned by {conversation.username}"
            )
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
                    'created_at': m.created_at.isoformat() if m.created_at else None,
                    'agent_trace': m.agent_trace,
                    'stream_metadata': m.stream_metadata
                }
                for m in messages
            ]
        }

    @staticmethod
    def create_conversation(
        chatbot_id: int,
        username: str = None,
        title: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation for a chatbot.

        Args:
            chatbot_id: ID of the chatbot
            username: Owner username
            title: Optional initial title
            session_id: Optional session ID (generated if not provided)

        Returns:
            Created conversation dict
        """
        session = session_id or str(uuid.uuid4())
        conversation = ChatbotConversation(
            chatbot_id=chatbot_id,
            session_id=session,
            username=username,
            title=title,
            is_active=True
        )
        db.session.add(conversation)
        db.session.commit()

        return {
            'id': conversation.id,
            'session_id': conversation.session_id,
            'chatbot_id': conversation.chatbot_id,
            'username': conversation.username,
            'title': conversation.title,
            'message_count': conversation.message_count,
            'is_active': conversation.is_active,
            'started_at': conversation.started_at.isoformat() if conversation.started_at else None,
            'last_message_at': conversation.last_message_at.isoformat() if conversation.last_message_at else None
        }

    @staticmethod
    def delete_conversation(conversation_id: int, username: str = None) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: The conversation ID
            username: If provided, verify the conversation belongs to this user

        Returns:
            True if deleted, False if not found/not authorized
        """
        conversation = ChatbotConversation.query.get(conversation_id)
        if not conversation:
            return False

        # SECURITY: Verify ownership if username is provided
        if username and conversation.username != username:
            logger.warning(
                f"User {username} attempted to delete conversation "
                f"{conversation_id} owned by {conversation.username}"
            )
            return False

        db.session.delete(conversation)
        db.session.commit()

        logger.info(f"User {username or 'admin'} deleted conversation {conversation_id}")
        return True

    @staticmethod
    def rate_message(message_id: int, rating: str, feedback: str = None) -> bool:
        """
        Rate a message (helpful, not_helpful, incorrect).

        Args:
            message_id: ID of the message to rate
            rating: Rating value
            feedback: Optional feedback text

        Returns:
            True if rated successfully, False if message not found
        """
        message = ChatbotMessage.query.get(message_id)
        if not message:
            return False

        message.user_rating = rating
        message.user_feedback = feedback
        db.session.commit()

        return True
