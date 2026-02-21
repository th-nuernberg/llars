"""
LLM Provider Configuration

Stores credentials and endpoints for external LLM providers.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class LLMProvider(db.Model):
    """Configuration for an LLM provider (OpenAI, Ollama, vLLM, Anthropic, Gemini, ...)."""

    __tablename__ = "llm_providers"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    provider_type: Mapped[str] = mapped_column(db.String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)

    base_url: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    config_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    is_openai_compatible: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider_type": self.provider_type,
            "name": self.name,
            "base_url": self.base_url,
            "config": self.config_json,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "is_openai_compatible": self.is_openai_compatible,
            "api_key_set": bool(self.api_key_encrypted),
        }
