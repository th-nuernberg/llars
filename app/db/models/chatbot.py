"""Chatbot database models."""

from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class ChatbotMessageRole(Enum):
    """Role of a chat message"""
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


class Chatbot(db.Model):
    """Configurable chatbots with RAG integration"""
    __tablename__ = 'chatbots'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Identification
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Visual Configuration
    icon: Mapped[str] = mapped_column(db.String(50), default='mdi-robot')
    avatar_url: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    color: Mapped[str] = mapped_column(db.String(7), default='#5d7a4a')

    # LLM Configuration
    system_prompt: Mapped[str] = mapped_column(db.Text, nullable=False)
    model_name: Mapped[str] = mapped_column(db.String(100), default='mistralai/Mistral-Small-3.2-24B-Instruct-2506')
    temperature: Mapped[float] = mapped_column(db.Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(db.Integer, default=2048)
    top_p: Mapped[float] = mapped_column(db.Float, default=0.9)

    # RAG Configuration
    rag_enabled: Mapped[bool] = mapped_column(db.Boolean, default=True)
    rag_retrieval_k: Mapped[int] = mapped_column(db.Integer, default=4)
    rag_min_relevance: Mapped[float] = mapped_column(db.Float, default=0.3)
    rag_include_sources: Mapped[bool] = mapped_column(db.Boolean, default=True)

    # Behavior
    welcome_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    fallback_message: Mapped[str] = mapped_column(db.Text, default='Ich konnte leider keine passende Antwort finden.')
    max_context_messages: Mapped[int] = mapped_column(db.Integer, default=10)

    # Access Control
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, index=True)
    is_public: Mapped[bool] = mapped_column(db.Boolean, default=False)
    allowed_roles: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Build Status (for Chatbot Builder Wizard)
    build_status: Mapped[str] = mapped_column(
        db.Enum('draft', 'crawling', 'embedding', 'configuring', 'ready', 'error', 'paused', name='chatbot_build_status_enum'),
        default='ready',
        nullable=False,
        index=True
    )
    build_error: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Source Information (for Chatbot Builder)
    source_url: Mapped[Optional[str]] = mapped_column(db.String(2048), nullable=True)
    primary_collection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_collections.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Audit
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    collections = db.relationship('ChatbotCollection', backref='chatbot', cascade='all, delete-orphan')
    conversations = db.relationship('ChatbotConversation', backref='chatbot', cascade='all, delete-orphan')
    primary_collection = db.relationship('RAGCollection', foreign_keys=[primary_collection_id], backref='primary_chatbots')
    user_access = db.relationship('ChatbotUserAccess', backref='chatbot', cascade='all, delete-orphan')


class ChatbotUserAccess(db.Model):
    """Per-user allowlist for private chatbots."""
    __tablename__ = 'chatbot_user_access'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    chatbot_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbots.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)

    granted_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('chatbot_id', 'username', name='unique_chatbot_user_access'),
    )


class ChatbotCollection(db.Model):
    """M:N relationship between chatbots and RAG collections"""
    __tablename__ = 'chatbot_collections'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    chatbot_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbots.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    collection_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_collections.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Configuration
    priority: Mapped[int] = mapped_column(db.Integer, default=0)
    weight: Mapped[float] = mapped_column(db.Float, default=1.0)
    is_primary: Mapped[bool] = mapped_column(db.Boolean, default=False)

    # Audit
    assigned_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    # Relationship to collection
    collection = db.relationship('RAGCollection', backref='chatbot_assignments')

    __table_args__ = (
        db.UniqueConstraint('chatbot_id', 'collection_id', name='unique_chatbot_collection'),
    )


class ChatbotConversation(db.Model):
    """Chat sessions/conversations with a chatbot"""
    __tablename__ = 'chatbot_conversations'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    chatbot_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbots.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Session
    session_id: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True)
    message_count: Mapped[int] = mapped_column(db.Integer, default=0)

    # Timing
    started_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    messages = db.relationship('ChatbotMessage', backref='conversation', cascade='all, delete-orphan')


class ChatbotMessage(db.Model):
    """Individual messages in a chatbot conversation"""
    __tablename__ = 'chatbot_messages'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbot_conversations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Message
    role: Mapped[str] = mapped_column(db.Enum(ChatbotMessageRole), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)

    # RAG Context (only for assistant messages)
    rag_context: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    rag_sources: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Metrics
    tokens_input: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    tokens_output: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Feedback
    user_rating: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)  # helpful, not_helpful, incorrect
    user_feedback: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, index=True)
