"""
User Demographics Model.

Captures one-time demographic survey data for users (typically collected at
first login when arriving via a referral link). Used for cohort/research
analysis. The survey is shown exactly once per user — once `completed_at`
is set, the overlay never appears again.

All fields are optional ("keine Angabe" / "prefer not to say"); we only treat
the survey as completed when the user submits it explicitly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import db


class UserDemographics(db.Model):
    """
    Per-user demographic profile (1:1 with User).

    Values are kept as opaque strings (controlled vocabulary defined in the
    frontend survey) so we can extend the option list without DB migrations.
    """

    __tablename__ = "user_demographics"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Controlled-vocabulary values: 'female', 'male', 'non_binary', 'no_answer'
    gender: Mapped[Optional[str]] = mapped_column(db.String(32), nullable=True)

    # 'under_29', '30_49', '50_64', '65_plus', 'no_answer'
    age_range: Mapped[Optional[str]] = mapped_column(db.String(32), nullable=True)

    # 'phd', 'master', 'bachelor', 'vocational', 'abitur',
    # 'realschule', 'no_formal', 'no_answer'
    education: Mapped[Optional[str]] = mapped_column(db.String(32), nullable=True)

    # Free-text profession field (optional, e.g. "Onlineberater*in")
    profession: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Referral context if relevant — link.id at the time the user filled the survey
    referral_link_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("referral_links.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Set once the user submits the survey. NULL = survey not yet completed.
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    user = relationship("User", backref=db.backref("demographics", uselist=False, cascade="all, delete-orphan"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "gender": self.gender,
            "age_range": self.age_range,
            "education": self.education,
            "profession": self.profession,
            "referral_link_id": self.referral_link_id,
            "completed": self.completed_at is not None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
