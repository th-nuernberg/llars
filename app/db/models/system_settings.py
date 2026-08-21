"""System-wide settings stored in the LLARS database."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column

from db import db


class SystemSettings(db.Model):
    """
    Global system configuration.

    This is a single-row table (id=1) used to configure system-wide settings
    that can be changed at runtime via the Admin Panel.
    """

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=False, default=1)

    # Crawler Timeouts (in seconds)
    crawl_timeout_seconds: Mapped[int] = mapped_column(
        db.Integer, default=3600, nullable=False,
        comment="Timeout for website crawling (default: 3600 = 1 hour)"
    )
    embedding_timeout_seconds: Mapped[int] = mapped_column(
        db.Integer, default=7200, nullable=False,
        comment="Timeout for embedding generation (default: 7200 = 2 hours)"
    )

    # Crawler Defaults
    crawler_default_max_pages: Mapped[int] = mapped_column(
        db.Integer, default=500, nullable=False,
        comment="Default max pages for chatbot wizard crawler"
    )
    crawler_default_max_depth: Mapped[int] = mapped_column(
        db.Integer, default=3, nullable=False,
        comment="Default crawl depth for chatbot wizard"
    )

    # RAG Settings
    rag_default_chunk_size: Mapped[int] = mapped_column(
        db.Integer, default=1000, nullable=False,
        comment="Default chunk size for document splitting"
    )
    rag_default_chunk_overlap: Mapped[int] = mapped_column(
        db.Integer, default=200, nullable=False,
        comment="Default overlap between chunks"
    )

    # LLM AI Task Logging
    llm_ai_log_responses: Mapped[bool] = mapped_column(
        db.Boolean, default=True, nullable=False,
        comment="Enable logging of LLM evaluator responses"
    )
    llm_ai_log_tasks: Mapped[str] = mapped_column(
        db.String(255), default="authenticity", nullable=False,
        comment="Comma-separated task types to log (empty = all)"
    )
    llm_ai_log_response_max: Mapped[int] = mapped_column(
        db.Integer, default=800, nullable=False,
        comment="Max characters for logged LLM responses"
    )
    llm_ai_log_prompts: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False,
        comment="Enable logging of LLM evaluator prompts"
    )
    llm_ai_log_prompt_max: Mapped[int] = mapped_column(
        db.Integer, default=800, nullable=False,
        comment="Max characters for logged LLM prompts"
    )

    # Batch Generation Settings
    batch_generation_max_parallel: Mapped[int] = mapped_column(
        db.Integer, default=4, nullable=False,
        comment="Maximum number of parallel outputs processed in batch generation"
    )

    # Referral/Invitation System Settings
    referral_system_enabled: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False,
        comment="Enable referral/invitation link system"
    )
    self_registration_enabled: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False,
        comment="Enable self-registration via referral links (shows Register button)"
    )
    default_referral_role: Mapped[str] = mapped_column(
        db.String(100), default='evaluator', nullable=False,
        comment="Default role for users registered via referral"
    )

    # Communication (Messaging) Master Toggle
    communication_enabled: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False,
        comment="Enable communication features (messaging, calls) globally"
    )

    # Self-Service Password Reset Toggle
    self_service_password_reset_enabled: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False,
        comment="Enable self-service 'forgot password' flow on the login page"
    )

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'crawl_timeout_seconds': self.crawl_timeout_seconds,
            'embedding_timeout_seconds': self.embedding_timeout_seconds,
            'crawler_default_max_pages': self.crawler_default_max_pages,
            'crawler_default_max_depth': self.crawler_default_max_depth,
            'rag_default_chunk_size': self.rag_default_chunk_size,
            'rag_default_chunk_overlap': self.rag_default_chunk_overlap,
            'llm_ai_log_responses': self.llm_ai_log_responses,
            'llm_ai_log_tasks': self.llm_ai_log_tasks,
            'llm_ai_log_response_max': self.llm_ai_log_response_max,
            'llm_ai_log_prompts': self.llm_ai_log_prompts,
            'llm_ai_log_prompt_max': self.llm_ai_log_prompt_max,
            'batch_generation_max_parallel': self.batch_generation_max_parallel,
            # Referral System
            'referral_system_enabled': self.referral_system_enabled,
            'self_registration_enabled': self.self_registration_enabled,
            'default_referral_role': self.default_referral_role,
            # Communication
            'communication_enabled': self.communication_enabled,
            # Self-Service Password Reset
            'self_service_password_reset_enabled': self.self_service_password_reset_enabled,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
