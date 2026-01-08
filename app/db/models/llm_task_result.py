"""LLM Task Results.

Stores LLM evaluator outputs for scenario tasks without creating user accounts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class LLMTaskResult(db.Model):
    __tablename__ = "llm_task_results"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("rating_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    thread_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("email_threads.thread_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(db.String(50), nullable=False, index=True)
    payload_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    raw_response: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "scenario_id",
            "thread_id",
            "model_id",
            "task_type",
            name="uix_llm_task_result",
        ),
    )

