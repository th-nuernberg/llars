"""Zotero integration database models for LLARS."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import LONGTEXT

from db import db


class ZoteroLibraryType(Enum):
    """Type of Zotero library."""
    user = "user"
    group = "group"


class ZoteroConnection(db.Model):
    """
    Stores Zotero account connection for a LLARS user.
    Each user can have one Zotero account linked.
    """
    __tablename__ = "zotero_connections"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    zotero_user_id: Mapped[str] = mapped_column(db.String(50), nullable=False)
    zotero_username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    # API key encrypted with Fernet (from cryptography library)
    api_key_encrypted: Mapped[str] = mapped_column(db.Text, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationship
    user = db.relationship("User", backref=db.backref("zotero_connection", uselist=False, cascade="all, delete-orphan"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "zotero_user_id": self.zotero_user_id,
            "zotero_username": self.zotero_username,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
        }


class WorkspaceZoteroLibrary(db.Model):
    """
    Links a Zotero library (user library, group library, or collection) to a LaTeX workspace.
    The BibTeX content is stored as a real file in the workspace (LatexDocument).
    """
    __tablename__ = "workspace_zotero_libraries"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    zotero_connection_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("zotero_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The document that stores the .bib file content
    document_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    library_type: Mapped[ZoteroLibraryType] = mapped_column(
        db.Enum(ZoteroLibraryType),
        nullable=False,
    )
    library_id: Mapped[str] = mapped_column(db.String(50), nullable=False)  # userID or groupID
    library_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    # If collection_key is NULL, the entire library is linked; otherwise, only that collection
    collection_key: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    collection_name: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    # Filename for the .bib file in the workspace
    bib_filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    # Auto-sync settings
    auto_sync_enabled: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    auto_sync_interval_minutes: Mapped[int] = mapped_column(db.Integer, default=30, nullable=False)
    # Tracking
    item_count: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    last_sync_error: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workspace = db.relationship(
        "LatexWorkspace",
        backref=db.backref("zotero_libraries", cascade="all, delete-orphan", lazy="selectin"),
    )
    zotero_connection = db.relationship(
        "ZoteroConnection",
        backref=db.backref("workspace_libraries", cascade="all, delete-orphan", lazy="selectin"),
    )
    document = db.relationship(
        "LatexDocument",
        backref=db.backref("zotero_library_link", uselist=False),
    )

    __table_args__ = (
        # Each library/collection can only be linked once per workspace
        db.UniqueConstraint(
            "workspace_id", "library_id", "collection_key",
            name="unique_workspace_zotero_library"
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "zotero_connection_id": self.zotero_connection_id,
            "document_id": self.document_id,
            "library_type": self.library_type.value,
            "library_id": self.library_id,
            "library_name": self.library_name,
            "collection_key": self.collection_key,
            "collection_name": self.collection_name,
            "bib_filename": self.bib_filename,
            "auto_sync_enabled": self.auto_sync_enabled,
            "auto_sync_interval_minutes": self.auto_sync_interval_minutes,
            "item_count": self.item_count,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "last_sync_error": self.last_sync_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ZoteroSyncLog(db.Model):
    """
    Logs Zotero sync operations for debugging and auditing.
    """
    __tablename__ = "zotero_sync_logs"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_library_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("workspace_zotero_libraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggered_by: Mapped[str] = mapped_column(db.String(50), nullable=False)  # "manual", "auto", "system"
    triggered_by_username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    status: Mapped[str] = mapped_column(db.String(20), nullable=False)  # "success", "failed", "partial"
    items_fetched: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    items_updated: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    workspace_library = db.relationship(
        "WorkspaceZoteroLibrary",
        backref=db.backref("sync_logs", cascade="all, delete-orphan", lazy="dynamic"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_library_id": self.workspace_library_id,
            "triggered_by": self.triggered_by,
            "triggered_by_username": self.triggered_by_username,
            "status": self.status,
            "items_fetched": self.items_fetched,
            "items_updated": self.items_updated,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
