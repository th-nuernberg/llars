"""Conversation Anonymization Pipeline models.

These models support batch processing of chat conversations through the
anonymization tool, with manual review/editing and export functionality.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, List, Any

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class AnonymizationConversation(db.Model):
    """Conversation from chat JSON with anonymization processing."""

    __tablename__ = "anonymization_conversations"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Source tracking
    source_file_path: Mapped[str] = mapped_column(db.String(512), nullable=False)
    original_chat_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        db.Enum("pending", "in_progress", "completed", "error"),
        default="pending",
        nullable=False,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Metadata
    message_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    entity_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    original_created_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    persona_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Audit
    imported_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    imported_by: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Quality filtering
    quality_rating: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, comment="1-5 star quality rating")
    exclude_from_export: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False, index=True, comment="Exclude from final dataset export"
    )
    quality_notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True, comment="Reviewer notes about quality issues")
    quality_reviewed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True, comment="When quality was last reviewed")
    quality_reviewed_by: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="User who reviewed quality"
    )

    # Relationships
    messages = db.relationship(
        "AnonymizationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AnonymizationMessage.message_number",
    )
    imported_by_user = db.relationship("User", foreign_keys=[imported_by])
    updated_by_user = db.relationship("User", foreign_keys=[updated_by])
    quality_reviewed_by_user = db.relationship("User", foreign_keys=[quality_reviewed_by])

    @staticmethod
    def _metadata_list(metadata: Optional[dict], key: str) -> List[str]:
        """Extract normalized string list from metadata.derived[key]."""
        if not isinstance(metadata, dict):
            return []

        derived = metadata.get("derived")
        if not isinstance(derived, dict):
            return []

        values = derived.get(key)
        if not isinstance(values, list):
            return []

        normalized: List[str] = []
        for value in values:
            text = str(value).strip()
            if text and text not in normalized:
                normalized.append(text)
        return normalized

    @classmethod
    def _build_metadata_summary(cls, metadata: Optional[dict]) -> Dict[str, Any]:
        """Return lightweight metadata summary for table views."""
        return {
            "models": cls._metadata_list(metadata, "models"),
            "providers": cls._metadata_list(metadata, "providers"),
            "courses": cls._metadata_list(metadata, "courses"),
        }

    def to_dict(self, include_messages: bool = False, include_metadata: bool = False) -> Dict:
        """Serialize to dictionary."""
        data = {
            "id": self.id,
            "source_file_path": self.source_file_path,
            "original_chat_id": self.original_chat_id,
            "title": self.title,
            "status": self.status,
            "error_message": self.error_message,
            "message_count": self.message_count,
            "entity_count": self.entity_count,
            "original_created_at": self.original_created_at.isoformat() if self.original_created_at else None,
            "persona": self.persona_json,
            "metadata_summary": self._build_metadata_summary(self.metadata_json),
            "imported_at": self.imported_at.isoformat() if self.imported_at else None,
            "imported_by": self.imported_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "quality_rating": self.quality_rating,
            "exclude_from_export": self.exclude_from_export,
            "quality_notes": self.quality_notes,
            "quality_reviewed_at": self.quality_reviewed_at.isoformat() if self.quality_reviewed_at else None,
            "quality_reviewed_by": self.quality_reviewed_by,
        }

        if include_messages:
            data["messages"] = [msg.to_dict(include_entities=True) for msg in self.messages]

        if include_metadata:
            data["metadata"] = self.metadata_json

        return data


class AnonymizationMessage(db.Model):
    """Message with original and anonymized content."""

    __tablename__ = "anonymization_messages"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("anonymization_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message data
    message_number: Mapped[int] = mapped_column(db.Integer, nullable=False)
    author: Mapped[str] = mapped_column(db.String(255), nullable=False)
    original_content: Mapped[str] = mapped_column(db.Text, nullable=False)
    anonymized_content: Mapped[str] = mapped_column(db.Text, nullable=False)

    # Version tracking
    current_version: Mapped[int] = mapped_column(db.Integer, default=1, nullable=False)
    is_manually_edited: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    conversation = db.relationship("AnonymizationConversation", back_populates="messages")
    entities = db.relationship(
        "AnonymizationEntity", back_populates="message", cascade="all, delete-orphan"
    )
    versions = db.relationship(
        "AnonymizationMessageVersion",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="AnonymizationMessageVersion.version_number",
    )

    __table_args__ = (db.UniqueConstraint("conversation_id", "message_number", name="unique_conversation_message"),)

    def to_dict(self, include_entities: bool = False, include_versions: bool = False) -> Dict:
        """Serialize to dictionary."""
        data = {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "message_number": self.message_number,
            "author": self.author,
            "original_content": self.original_content,
            "anonymized_content": self.anonymized_content,
            "current_version": self.current_version,
            "is_manually_edited": self.is_manually_edited,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_entities:
            data["entities"] = [entity.to_dict() for entity in self.entities]

        if include_versions:
            data["versions"] = [version.to_dict() for version in self.versions]

        return data


class AnonymizationEntity(db.Model):
    """Detected entity in a message."""

    __tablename__ = "anonymization_entities"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("anonymization_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Entity data
    label: Mapped[str] = mapped_column(
        db.Enum("PER", "LOC", "ORG", "DATE", "AGE", "PHONE", "MAIL", "AHV", "PLZ", "MISC"),
        nullable=False,
        index=True,
    )
    original_text: Mapped[str] = mapped_column(db.String(512), nullable=False)
    replacement_text: Mapped[str] = mapped_column(db.String(512), nullable=False)
    start_pos: Mapped[int] = mapped_column(db.Integer, nullable=False)
    end_pos: Mapped[int] = mapped_column(db.Integer, nullable=False)

    # Group tracking
    group_key: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)
    group_mode: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    db_hit: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message = db.relationship("AnonymizationMessage", back_populates="entities")

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "label": self.label,
            "original_text": self.original_text,
            "replacement_text": self.replacement_text,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "group_key": self.group_key,
            "group_mode": self.group_mode,
            "db_hit": self.db_hit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnonymizationMessageVersion(db.Model):
    """Message edit history."""

    __tablename__ = "anonymization_message_versions"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("anonymization_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Version data
    version_number: Mapped[int] = mapped_column(db.Integer, nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    change_description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Audit
    changed_by: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message = db.relationship("AnonymizationMessage", back_populates="versions")
    changed_by_user = db.relationship("User")

    __table_args__ = (db.UniqueConstraint("message_id", "version_number", name="unique_message_version"),)

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "version_number": self.version_number,
            "content": self.content,
            "change_description": self.change_description,
            "changed_by": self.changed_by,
            "changed_by_username": self.changed_by_user.username if self.changed_by_user else None,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }
