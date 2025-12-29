"""System-wide settings stored in the LLARS database."""

from datetime import datetime
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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
