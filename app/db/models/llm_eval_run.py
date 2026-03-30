"""Durable queue state for LLM evaluator runs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class LLMEvalRun(db.Model):
    __tablename__ = "llm_eval_runs"

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
    )
    model_id: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    task_type: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        db.String(20),
        nullable=False,
        default=STATUS_IDLE,
        index=True,
    )
    requested_all: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    thread_ids_json: Mapped[Optional[Any]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="Subset of thread or comparison session IDs requested for the next run",
    )
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

    __table_args__ = (
        db.UniqueConstraint("scenario_id", "model_id", name="uix_llm_eval_run_scenario_model"),
    )

