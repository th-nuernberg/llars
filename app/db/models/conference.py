"""Conference & Paper Management database models.

Tables for tracking conferences (deadlines, rankings, venues),
papers (status, authors, submissions), and research groups.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class CoreRanking(Enum):
    A_STAR = "A*"
    A = "A"
    B = "B"
    C = "C"
    UNRANKED = "Unranked"


class PaperStatus(Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PUBLISHED = "published"


class SubmissionStatus(Enum):
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ResearchGroupRole(Enum):
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class ResearchGroupRequestStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ── Research Group Models ────────────────────────────────────


class ResearchGroup(db.Model):
    __tablename__ = "research_groups"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = db.relationship(
        "ResearchGroupMember",
        backref=db.backref("group", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    access_requests = db.relationship(
        "ResearchGroupAccessRequest",
        backref=db.backref("group", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "member_count": len(self.members) if self.members else 0,
        }

    def to_dict_brief(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
        }


class ResearchGroupMember(db.Model):
    __tablename__ = "research_group_members"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("research_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ResearchGroupRole] = mapped_column(
        db.Enum(ResearchGroupRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ResearchGroupRole.MEMBER,
    )
    added_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    added_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", lazy="selectin")

    __table_args__ = (
        db.UniqueConstraint("group_id", "user_id", name="unique_group_user"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "avatar_seed": self.user.get_avatar_seed() if self.user else None,
            "role": self.role.value if self.role else "member",
            "added_by": self.added_by,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }


class ResearchGroupAccessRequest(db.Model):
    __tablename__ = "research_group_access_requests"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("research_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requester_username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[ResearchGroupRequestStatus] = mapped_column(
        db.Enum(ResearchGroupRequestStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ResearchGroupRequestStatus.PENDING,
    )
    message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("group_id", "requester_username", name="unique_group_requester"),
    )


class ConferenceSeries(db.Model):
    __tablename__ = "conference_series"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    acronym: Mapped[str] = mapped_column(db.String(100), nullable=False, unique=True)
    group_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("research_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    core_ranking: Mapped[Optional[CoreRanking]] = mapped_column(
        db.Enum(CoreRanking, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    website_url: Mapped[Optional[str]] = mapped_column(db.String(2048), nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    editions = db.relationship(
        "Conference",
        backref=db.backref("series", lazy="selectin"),
        lazy="selectin",
        order_by="Conference.year.desc()",
    )

    def to_dict(self) -> dict:
        editions_brief = [e.to_dict_brief() for e in (self.editions or [])]
        return {
            "id": self.id,
            "name": self.name,
            "acronym": self.acronym,
            "core_ranking": self.core_ranking.value if self.core_ranking else None,
            "website_url": self.website_url,
            "keywords": self.keywords or [],
            "notes": self.notes,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "edition_count": len(editions_brief),
            "editions": editions_brief,
        }


class Conference(db.Model):
    __tablename__ = "conferences"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    acronym: Mapped[str] = mapped_column(db.String(100), nullable=False)
    year: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)
    group_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("research_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    series_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("conference_series.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    core_ranking: Mapped[CoreRanking] = mapped_column(
        db.Enum(CoreRanking, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=CoreRanking.UNRANKED,
    )
    submission_deadline: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True, index=True)
    notification_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(db.String(2048), nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    papers = db.relationship(
        "Paper",
        backref=db.backref("conference", lazy="selectin"),
        lazy="selectin",
    )

    __table_args__ = (
        db.UniqueConstraint("acronym", "year", name="unique_conference_year"),
    )

    def to_dict_brief(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "acronym": self.acronym,
            "year": self.year,
            "core_ranking": self.core_ranking.value if self.core_ranking else "Unranked",
            "submission_deadline": self.submission_deadline.isoformat() if self.submission_deadline else None,
            "city": self.city,
            "country": self.country,
        }

    def to_dict(self) -> dict:
        series_brief = None
        if self.series:
            series_brief = {
                "id": self.series.id,
                "name": self.series.name,
                "acronym": self.series.acronym,
            }
        return {
            "id": self.id,
            "name": self.name,
            "acronym": self.acronym,
            "year": self.year,
            "series_id": self.series_id,
            "series": series_brief,
            "core_ranking": self.core_ranking.value if self.core_ranking else "Unranked",
            "submission_deadline": self.submission_deadline.isoformat() if self.submission_deadline else None,
            "notification_date": self.notification_date.isoformat() if self.notification_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "city": self.city,
            "country": self.country,
            "website_url": self.website_url,
            "keywords": self.keywords or [],
            "notes": self.notes,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "paper_count": len(self.papers) if self.papers else 0,
        }


class Paper(db.Model):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(db.String(500), nullable=False)
    status: Mapped[PaperStatus] = mapped_column(
        db.Enum(PaperStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=PaperStatus.PLANNING,
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("research_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    conference_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("conferences.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    latex_workspace_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("latex_workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    overleaf_url: Mapped[Optional[str]] = mapped_column(db.String(2048), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(db.String(2048), nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    latex_workspace = db.relationship("LatexWorkspace", lazy="selectin")

    authors = db.relationship(
        "PaperAuthor",
        backref=db.backref("paper", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PaperAuthor.author_order",
    )

    submissions = db.relationship(
        "PaperSubmission",
        backref=db.backref("paper", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PaperSubmission.created_at.desc()",
    )

    def to_dict(self) -> dict:
        ws_brief = None
        if self.latex_workspace:
            ws_brief = {"id": self.latex_workspace.id, "name": self.latex_workspace.name}
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value if self.status else "planning",
            "conference_id": self.conference_id,
            "conference": self.conference.to_dict() if self.conference else None,
            "latex_workspace_id": self.latex_workspace_id,
            "latex_workspace": ws_brief,
            "overleaf_url": self.overleaf_url,
            "external_url": self.external_url,
            "keywords": self.keywords or [],
            "description": self.description,
            "notes": self.notes,
            "authors": [a.to_dict() for a in self.authors] if self.authors else [],
            "submissions": [s.to_dict() for s in self.submissions] if self.submissions else [],
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PaperAuthor(db.Model):
    __tablename__ = "paper_authors"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_name: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    author_order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    is_corresponding: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", lazy="selectin")

    __table_args__ = (
        db.UniqueConstraint("paper_id", "user_id", name="unique_paper_user"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "avatar_seed": self.user.get_avatar_seed() if self.user else None,
            "external_name": self.external_name,
            "display_name": self.user.username if self.user else self.external_name,
            "author_order": self.author_order,
            "is_corresponding": self.is_corresponding,
        }


class PaperSubmission(db.Model):
    __tablename__ = "paper_submissions"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conference_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("conferences.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        db.Enum(SubmissionStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=SubmissionStatus.SUBMITTED,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)

    conference = db.relationship("Conference", lazy="selectin")

    def to_dict(self) -> dict:
        conf_brief = None
        if self.conference:
            conf_brief = {
                "id": self.conference.id,
                "acronym": self.conference.acronym,
                "year": self.conference.year,
                "name": self.conference.name,
            }
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "conference_id": self.conference_id,
            "conference": conf_brief,
            "status": self.status.value if self.status else "submitted",
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
