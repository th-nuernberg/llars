"""Durable queue state for expensive scenario stats recomputation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class ScenarioStatsJob(db.Model):
    __tablename__ = "scenario_stats_jobs"

    STATUS_IDLE = "idle"
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_FAILED = "failed"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("rating_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        db.String(20),
        nullable=False,
        default=STATUS_IDLE,
        index=True,
    )
    priority: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    request_token: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    processing_token: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    worker_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    lease_expires_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True, index=True)
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    last_requested_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

