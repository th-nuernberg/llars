"""Fake-vs-Real (Authenticity) evaluation models.

These models enable importing augmented conversations and collecting
human votes whether a conversation is "real" or "fake".
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class AuthenticityConversation(db.Model):
    """Metadata for an imported authenticity sample (linked to an EmailThread)."""

    __tablename__ = "authenticity_conversations"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    thread_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("email_threads.thread_id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Stable unique key derived from the provided metadata (format_version + identifying fields)
    sample_key: Mapped[str] = mapped_column(db.String(255), unique=True, index=True, nullable=False)

    conversation_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)
    augmentation_type: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    replaced_positions: Mapped[Optional[list]] = mapped_column(db.JSON, nullable=True)
    num_replacements: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    total_messages: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    saeule: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True, index=True)
    split: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True, index=True)
    model: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    model_short: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    format_version: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)

    # Ground truth: fake if at least one message was replaced by a model.
    is_fake: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)

    # Store raw metadata for forward compatibility.
    metadata_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, index=True)

    thread = db.relationship("EmailThread", backref=db.backref("authenticity_conversation", uselist=False))


class UserAuthenticityVote(db.Model):
    """Human vote whether a conversation is real or fake."""

    __tablename__ = "user_authenticity_votes"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    thread_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("email_threads.thread_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "real" | "fake" | None (until user decides)
    vote: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    confidence: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref="authenticity_votes")
    thread = db.relationship("EmailThread", backref="authenticity_votes")

    __table_args__ = (
        db.UniqueConstraint("user_id", "thread_id", name="uix_user_authenticity_vote"),
    )

