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

    # Zotero OAuth Settings
    # Admin registers ONE app at zotero.org/oauth/apps and enters credentials here.
    # All users then use "Connect with Zotero" button to authorize their accounts.
    zotero_oauth_enabled: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False,
        comment="Enable Zotero OAuth login for users"
    )
    zotero_client_key: Mapped[Optional[str]] = mapped_column(
        db.String(255), nullable=True,
        comment="Zotero OAuth Client Key from zotero.org/oauth/apps"
    )
    zotero_client_secret_encrypted: Mapped[Optional[str]] = mapped_column(
        db.Text, nullable=True,
        comment="Zotero OAuth Client Secret (encrypted)"
    )

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def to_dict(self, include_zotero_secret: bool = False):
        """Convert to dictionary for API responses."""
        result = {
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
            'zotero_oauth_enabled': self.zotero_oauth_enabled,
            'zotero_client_key': self.zotero_client_key,
            'zotero_oauth_configured': bool(self.zotero_client_key and self.zotero_client_secret_encrypted),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        # Never expose the actual secret, only indicate if it's set
        if include_zotero_secret:
            result['zotero_client_secret_set'] = bool(self.zotero_client_secret_encrypted)
        return result
