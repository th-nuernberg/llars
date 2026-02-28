"""Conference & Paper Management database models.

Tables for tracking conferences (deadlines, rankings, venues)
and papers (status, authors, submissions).
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


class Conference(db.Model):
    __tablename__ = "conferences"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    acronym: Mapped[str] = mapped_column(db.String(100), nullable=False)
    year: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)
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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "acronym": self.acronym,
            "year": self.year,
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
    conference_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("conferences.id", ondelete="SET NULL"),
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

    authors = db.relationship(
        "PaperAuthor",
        backref=db.backref("paper", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PaperAuthor.author_order",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value if self.status else "planning",
            "conference_id": self.conference_id,
            "conference": self.conference.to_dict() if self.conference else None,
            "overleaf_url": self.overleaf_url,
            "external_url": self.external_url,
            "keywords": self.keywords or [],
            "description": self.description,
            "notes": self.notes,
            "authors": [a.to_dict() for a in self.authors] if self.authors else [],
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
            "external_name": self.external_name,
            "display_name": self.user.username if self.user else self.external_name,
            "author_order": self.author_order,
            "is_corresponding": self.is_corresponding,
        }
