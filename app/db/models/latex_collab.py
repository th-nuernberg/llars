"""LaTeX Collab database models (workspaces, documents, assets, commits, compile jobs, comments)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import LONGBLOB, LONGTEXT

from db import db


class LatexWorkspaceVisibility(Enum):
    private = "private"
    team = "team"
    org = "org"


class LatexNodeType(Enum):
    folder = "folder"
    file = "file"


class LatexWorkspace(db.Model):
    __tablename__ = "latex_workspaces"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    owner_username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    visibility: Mapped[LatexWorkspaceVisibility] = mapped_column(
        db.Enum(LatexWorkspaceVisibility),
        nullable=False,
        default=LatexWorkspaceVisibility.private,
    )
    main_document_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    latest_compile_job_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_compile_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = db.relationship(
        "LatexWorkspaceMember",
        backref=db.backref("workspace", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    main_document = db.relationship("LatexDocument", foreign_keys=[main_document_id], post_update=True)
    latest_compile_job = db.relationship("LatexCompileJob", foreign_keys=[latest_compile_job_id], post_update=True)


class LatexWorkspaceMember(db.Model):
    __tablename__ = "latex_workspace_members"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    added_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    added_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("workspace_id", "username", name="unique_latex_workspace_member"),
    )


class LatexDocument(db.Model):
    __tablename__ = "latex_documents"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    node_type: Mapped[LatexNodeType] = mapped_column(db.Enum(LatexNodeType), nullable=False, default=LatexNodeType.file)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    order_index: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)

    # Room name used by yjs-server (e.g. "latex_123"). For folders/binary files this can be NULL.
    yjs_doc_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, unique=True)
    # JSON-encoded Yjs state update (Array<number>) as stringified JSON, stored in MySQL JSON.
    content: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    # Plain-text cache for server-side compile and commits.
    content_text: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)

    asset_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    last_editor_username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspace = db.relationship(
        "LatexWorkspace",
        foreign_keys=[workspace_id],
        backref=db.backref("documents", cascade="all, delete-orphan", lazy="selectin"),
    )
    parent = db.relationship(
        "LatexDocument",
        remote_side=[id],
        backref=db.backref("children", cascade="all, delete-orphan", passive_deletes=True, lazy="selectin"),
    )
    asset = db.relationship("LatexAsset", backref=db.backref("documents", lazy="selectin"))


class LatexAsset(db.Model):
    __tablename__ = "latex_assets"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(db.String(200), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(db.BigInteger, nullable=False, default=0)
    sha256: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True, index=True)
    data: Mapped[bytes] = mapped_column(LONGBLOB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class LatexCommit(db.Model):
    __tablename__ = "latex_commits"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    author_username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    message: Mapped[str] = mapped_column(db.Text, nullable=False)
    diff_summary: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    # Snapshot for current document (used for inline diffs)
    content_snapshot: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)
    # Full workspace snapshot for compile and history restore
    workspace_snapshot: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    workspace = db.relationship("LatexWorkspace", backref=db.backref("commits", cascade="all, delete-orphan", lazy="selectin"))
    document = db.relationship("LatexDocument", backref=db.backref("commits", lazy="selectin"))


class LatexCompileJob(db.Model):
    __tablename__ = "latex_compile_jobs"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_commits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="queued")
    error_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    log_text: Mapped[Optional[str]] = mapped_column(LONGTEXT, nullable=True)
    pdf_blob: Mapped[Optional[bytes]] = mapped_column(LONGBLOB, nullable=True)
    synctex_blob: Mapped[Optional[bytes]] = mapped_column(LONGBLOB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    workspace = db.relationship(
        "LatexWorkspace",
        foreign_keys=[workspace_id],
        backref=db.backref("compile_jobs", lazy="selectin"),
    )
    commit = db.relationship("LatexCommit", backref=db.backref("compile_jobs", lazy="selectin"))


class LatexComment(db.Model):
    __tablename__ = "latex_comments"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    range_start: Mapped[int] = mapped_column(db.Integer, nullable=False)
    range_end: Mapped[int] = mapped_column(db.Integer, nullable=False)
    body: Mapped[str] = mapped_column(db.Text, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    document = db.relationship("LatexDocument", backref=db.backref("comments", cascade="all, delete-orphan", lazy="selectin"))
