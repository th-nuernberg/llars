"""LLM Task Results.

Stores LLM evaluator outputs for scenario tasks without creating user accounts.
Extended with reasoning, prompt tracking, and performance metrics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import db


class LLMTaskResult(db.Model):
    """
    Stores results from LLM evaluators for scenario tasks.

    Extended fields:
    - reasoning_json: Structured reasoning from the LLM
    - prompt_template_id: Which prompt template was used
    - prompt_version: Version of the prompt for reproducibility
    - input_tokens, output_tokens: Token counts
    - processing_time_ms: Time taken for the evaluation
    """

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

    # Result data
    payload_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    raw_response: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # NEW: Structured reasoning (separate from payload for easier querying)
    reasoning_json: Mapped[Optional[dict]] = mapped_column(
        db.JSON,
        nullable=True,
        comment="Structured reasoning from LLM (chain-of-thought, indicators, etc.)"
    )

    # NEW: Prompt tracking for reproducibility
    prompt_template_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("prompt_templates.id", ondelete="SET NULL"),
        nullable=True,
        comment="Which prompt template was used"
    )
    prompt_version: Mapped[Optional[str]] = mapped_column(
        db.String(20),
        nullable=True,
        comment="Version of the prompt for reproducibility"
    )

    # NEW: Token tracking
    input_tokens: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        nullable=True,
        comment="Number of input tokens"
    )
    output_tokens: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        nullable=True,
        comment="Number of output tokens"
    )

    # NEW: Performance tracking
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        nullable=True,
        comment="Processing time in milliseconds"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    prompt_template = relationship("PromptTemplate", lazy="selectin")

    __table_args__ = (
        db.UniqueConstraint(
            "scenario_id",
            "thread_id",
            "model_id",
            "task_type",
            name="uix_llm_task_result",
        ),
    )

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used."""
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    @property
    def has_reasoning(self) -> bool:
        """Check if result has structured reasoning."""
        return self.reasoning_json is not None and len(self.reasoning_json) > 0

    def to_dict(self, include_raw: bool = False) -> dict:
        """Convert to dictionary for API responses."""
        result = {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "thread_id": self.thread_id,
            "model_id": self.model_id,
            "task_type": self.task_type,
            "payload_json": self.payload_json,
            "reasoning_json": self.reasoning_json,
            "error": self.error,
            "prompt_template_id": self.prompt_template_id,
            "prompt_version": self.prompt_version,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_raw:
            result["raw_response"] = self.raw_response
        return result

    def __repr__(self) -> str:
        return f"<LLMTaskResult {self.id}: {self.model_id}/{self.task_type} for thread {self.thread_id}>"

