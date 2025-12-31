"""
AI Writing Models

Database models for the AI Writing Assistant feature.
Includes chat sessions, messages, usage tracking, and citation ignores.
"""

from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.db import db


class AIFeatureType(PyEnum):
    """Types of AI writing features for usage tracking."""
    COMPLETION = 'completion'
    REWRITE = 'rewrite'
    CITATION = 'citation'
    CHAT = 'chat'
    REVIEW = 'review'


class AIChatSession(db.Model):
    """Chat session for AI writing assistant."""
    __tablename__ = 'ai_chat_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('latex_documents.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    messages = relationship('AIChatMessage', back_populates='session', cascade='all, delete-orphan')
    user = relationship('User', backref='ai_chat_sessions')

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': len(self.messages) if self.messages else 0
        }


class AIChatMessage(db.Model):
    """Chat message in an AI writing session."""
    __tablename__ = 'ai_chat_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('ai_chat_sessions.id', ondelete='CASCADE'), nullable=False)
    role = Column(Enum('user', 'assistant', 'system', name='ai_chat_role'), nullable=False)
    content = Column(Text, nullable=False)
    artifacts = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    session = relationship('AIChatSession', back_populates='messages')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'artifacts': self.artifacts,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AIUsageTracking(db.Model):
    """Track AI feature usage for analytics and rate limiting."""
    __tablename__ = 'ai_usage_tracking'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    feature = Column(
        Enum('completion', 'rewrite', 'citation', 'chat', 'review', name='ai_feature_type'),
        nullable=False
    )
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    model_id = Column(String(100), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship('User', backref='ai_usage_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'feature': self.feature,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'model_id': self.model_id,
            'latency_ms': self.latency_ms,
            'success': self.success,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AICitationIgnore(db.Model):
    """Track ignored citation warnings per document."""
    __tablename__ = 'ai_citation_ignores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('latex_documents.id', ondelete='CASCADE'), nullable=False)
    text_hash = Column(String(64), nullable=False)
    ignored_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('document_id', 'text_hash', name='uq_doc_text_hash'),
    )

    # Relationships
    user = relationship('User', backref='citation_ignores')

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'text_hash': self.text_hash,
            'ignored_by': self.ignored_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
