"""Markdown Collab database models (workspaces, documents, commits).

These tables back the Markdown Collab feature described in:
docs/docs/projekte/markdown collab/markdown-collab-konzept.md
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class MarkdownWorkspaceVisibility(Enum):
    private = "private"
    team = "team"
    org = "org"


class MarkdownNodeType(Enum):
    folder = "folder"
    file = "file"


class MarkdownWorkspace(db.Model):
    __tablename__ = "markdown_workspaces"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    owner_username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    visibility: Mapped[MarkdownWorkspaceVisibility] = mapped_column(
        db.Enum(MarkdownWorkspaceVisibility),
        nullable=False,
        default=MarkdownWorkspaceVisibility.private,
    )
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = db.relationship(
        "MarkdownWorkspaceMember",
        backref=db.backref("workspace", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MarkdownWorkspaceMember(db.Model):
    """Explicit workspace membership (sharing/invites)."""
    __tablename__ = "markdown_workspace_members"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("markdown_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    added_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    added_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("workspace_id", "username", name="unique_markdown_workspace_member"),
    )


class MarkdownDocument(db.Model):
    """
    Represents both folders and markdown files in a workspace.

    The collaborative state is stored in `content` as a JSON-encoded Yjs update
    (compatible with the existing yjs-server persistence used for prompts).
    """
    __tablename__ = "markdown_documents"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("markdown_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("markdown_documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    node_type: Mapped[MarkdownNodeType] = mapped_column(db.Enum(MarkdownNodeType), nullable=False, default=MarkdownNodeType.file)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    order_index: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)

    # Room name used by yjs-server (e.g. "markdown_123"). For folders this can be NULL.
    yjs_doc_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, unique=True)

    # JSON-encoded Yjs state update (Array<number>) as stringified JSON, stored in MySQL JSON.
    content: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    last_editor_username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspace = db.relationship("MarkdownWorkspace", backref=db.backref("documents", cascade="all, delete-orphan", lazy="selectin"))
    parent = db.relationship(
        "MarkdownDocument",
        remote_side=[id],
        backref=db.backref("children", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin"),
    )


class MarkdownCommit(db.Model):
    __tablename__ = "markdown_commits"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("markdown_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    message: Mapped[str] = mapped_column(db.Text, nullable=False)
    diff_summary: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    # Full document content at commit time for character-level diff comparison
    content_snapshot: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    document = db.relationship("MarkdownDocument", backref=db.backref("commits", cascade="all, delete-orphan", lazy="selectin"))
