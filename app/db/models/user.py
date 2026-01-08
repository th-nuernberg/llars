"""User-related database models."""

import secrets
from typing import Optional
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column
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
