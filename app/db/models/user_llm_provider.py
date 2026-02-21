"""
User LLM Provider Models.

Allows users to connect their own LLM API keys and share them with others.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from db import db


class UserLLMProvider(db.Model):
    """
    User-owned LLM provider configuration.

    Enables users to connect their own API keys (OpenAI, Anthropic, etc.)
    without requiring admin intervention. Keys are stored encrypted.
    """

    __tablename__ = "user_llm_providers"

    # Primary key
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Owner
    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Provider configuration
    provider_type: Mapped[str] = mapped_column(
        db.String(50),
        nullable=False,
        comment="Provider type: openai, anthropic, gemini, ollama, litellm, custom"
    )
    name: Mapped[str] = mapped_column(
        db.String(100),
        nullable=False,
        comment="User-friendly name for this provider"
    )

    # Connection details (API key encrypted!)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Fernet-encrypted API key - NEVER store plaintext"
    )
    base_url: Mapped[Optional[str]] = mapped_column(
        db.String(500),
        nullable=True,
        comment="Base URL for self-hosted or proxy providers"
    )

    # Additional configuration
    config_json: Mapped[Optional[dict]] = mapped_column(
        db.JSON,
        nullable=True,
        default=dict,
        comment="Provider-specific configuration"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=True
    )
    is_default: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=False,
        comment="Default provider for this user"
    )
    priority: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=0,
        comment="Priority for fallback ordering (lower = higher priority)"
    )

    # Sharing settings
    is_shared: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=False,
        comment="Whether this provider is shared with others"
    )
    share_with_all: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=False,
        comment="Share with all users (requires permission)"
    )

    # Usage tracking
    total_requests: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=0
    )
    total_tokens: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=0
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime,
        nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True,
        comment="Last error message (for debugging)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", backref="llm_providers", lazy="selectin")
    shares = relationship(
        "UserLLMProviderShare",
        backref="provider",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        db.Index("ix_user_provider_type", "user_id", "provider_type"),
        db.UniqueConstraint("user_id", "name", name="uq_user_provider_name"),
    )

    def to_dict(self, include_shares: bool = False) -> dict:
        """Convert to dictionary for API responses."""
        owner = self.user
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "owner_username": owner.username if owner else None,
            "owner_avatar_seed": getattr(owner, 'avatar_seed', None) if owner else None,
            "owner_avatar_url": (
                f"/api/users/avatar/{owner.avatar_public_id}"
                if owner and getattr(owner, 'avatar_public_id', None) and getattr(owner, 'avatar_file', None)
                else None
            ),
            "provider_type": self.provider_type,
            "name": self.name,
            "base_url": self.base_url,
            "api_key_set": bool(self.api_key_encrypted),
            "config": self.config_json or {},
            "is_active": self.is_active,
            "is_default": self.is_default,
            "priority": self.priority,
            "is_shared": self.is_shared,
            "share_with_all": self.share_with_all,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_shares and self.shares:
            result["shares"] = [s.to_dict() for s in self.shares]
            result["share_count"] = len(self.shares)

        return result

    def record_usage(self, tokens: int = 0, error: str = None) -> None:
        """Record usage statistics."""
        self.total_requests += 1
        self.total_tokens += tokens
        self.last_used_at = datetime.utcnow()
        if error:
            self.last_error = error
        db.session.add(self)

    @classmethod
    def get_for_user(cls, user_id: int, provider_type: str = None) -> List["UserLLMProvider"]:
        """Get all providers for a user, optionally filtered by type."""
        query = cls.query.filter_by(user_id=user_id, is_active=True)
        if provider_type:
            query = query.filter_by(provider_type=provider_type)
        return query.order_by(cls.priority, cls.created_at).all()

    @classmethod
    def get_default_for_user(cls, user_id: int) -> Optional["UserLLMProvider"]:
        """Get the default provider for a user."""
        return cls.query.filter_by(
            user_id=user_id,
            is_active=True,
            is_default=True
        ).first()

    def __repr__(self) -> str:
        return f"<UserLLMProvider {self.id}: {self.name} ({self.provider_type})>"


class UserLLMProviderShare(db.Model):
    """
    Tracks sharing of user LLM providers with other users.

    Allows provider owners to share their API access with specific users
    or roles without exposing the actual API key.
    """

    __tablename__ = "user_llm_provider_shares"

    # Primary key
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Provider being shared
    provider_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("user_llm_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Share target
    share_type: Mapped[str] = mapped_column(
        db.String(20),
        nullable=False,
        comment="Type of share: user, role"
    )
    target_identifier: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        comment="Username or role name"
    )

    # Permissions
    can_use: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=True,
        comment="Can use this provider for API calls"
    )
    usage_limit_tokens: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        nullable=True,
        comment="Optional token limit per month for this share"
    )
    current_month_usage: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=0
    )

    # Audit
    shared_by: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    shared_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime,
        nullable=True,
        comment="Optional expiration date"
    )

    # Indexes
    __table_args__ = (
        db.UniqueConstraint(
            "provider_id", "share_type", "target_identifier",
            name="uq_provider_share_target"
        ),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "share_type": self.share_type,
            "target_identifier": self.target_identifier,
            "can_use": self.can_use,
            "usage_limit_tokens": self.usage_limit_tokens,
            "current_month_usage": self.current_month_usage,
            "shared_by": self.shared_by,
            "shared_at": self.shared_at.isoformat() if self.shared_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def is_valid(self) -> bool:
        """Check if share is still valid."""
        if not self.can_use:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        if self.usage_limit_tokens and self.current_month_usage >= self.usage_limit_tokens:
            return False
        return True

    def __repr__(self) -> str:
        return f"<UserLLMProviderShare {self.id}: {self.share_type}:{self.target_identifier}>"
