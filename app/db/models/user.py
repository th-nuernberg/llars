"""User-related database models."""

import secrets
import hashlib
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from db import db


class UserGroup(db.Model):
    """Group model for organizing users."""
    __tablename__ = 'user_groups'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), unique=True)


def generate_avatar_seed():
    """Generate a random seed for avatar generation."""
    return secrets.token_hex(8)


DEFAULT_COLLAB_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB',
    '#E74C3C', '#2ECC71', '#F39C12', '#1ABC9C'
]


class User(db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255))
    password_hash: Mapped[str] = mapped_column(db.String(255))
    api_key: Mapped[str] = mapped_column(db.String(100), unique=True)
    group_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user_groups.id'), default=1)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    is_ai: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    llm_model_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    avatar_seed: Mapped[Optional[str]] = mapped_column(db.String(32), nullable=True, default=generate_avatar_seed)
    collab_color: Mapped[Optional[str]] = mapped_column(db.String(7), nullable=True)  # #RRGGBB format
    avatar_file: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    avatar_public_id: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True, unique=True)
    avatar_mime_type: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    avatar_updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    avatar_change_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    avatar_change_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    settings_json: Mapped[Optional[dict]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="User preferences (theme, language, etc.)"
    )

    group = db.relationship('UserGroup', backref='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_avatar_seed(self):
        """Get the avatar seed, generating one if not exists."""
        if not self.avatar_seed:
            self.avatar_seed = generate_avatar_seed()
        return self.avatar_seed

    # Relationship to API keys
    api_keys: Mapped[List["UserApiKey"]] = relationship(
        "UserApiKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )


class UserApiKey(db.Model):
    """
    API Key model for programmatic access.

    Each user can have multiple API keys with labels for different purposes.
    Admin users can have a fixed key from .env that's never deleted.
    """
    __tablename__ = 'user_api_keys'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Key details
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(db.String(12), nullable=False)  # First 8 chars for display

    # Metadata
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Flags
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    is_system_key: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    # Permissions/Scopes (for future use)
    scopes: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """
        Generate a new API key.

        Returns:
            Tuple of (full_key, key_hash, key_prefix)
        """
        key = f"llars_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:12]
        return key, key_hash, key_prefix

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash a key for comparison."""
        return hashlib.sha256(key.encode()).hexdigest()

    @classmethod
    def find_by_key(cls, key: str) -> Optional["UserApiKey"]:
        """Find an API key by its value."""
        key_hash = cls.hash_key(key)
        return cls.query.filter_by(key_hash=key_hash, is_active=True).first()

    def update_last_used(self):
        """Update the last used timestamp."""
        self.last_used_at = datetime.utcnow()

    def to_dict(self, include_key: bool = False, full_key: str = None) -> dict:
        """
        Convert to dictionary for API response.

        Args:
            include_key: If True and full_key provided, include the full key
            full_key: The full key (only available at creation time)
        """
        result = {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "is_system_key": self.is_system_key,
            "scopes": self.scopes.split(",") if self.scopes else [],
        }
        if include_key and full_key:
            result["key"] = full_key
        return result
