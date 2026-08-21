"""Labeling Co-Pilot Log.

Study-grade logging for the labeling co-pilot (LLM pre-annotation):
one row per (user, item, scenario) in copilot-enabled labeling scenarios -
including hidden-control items (shown=False), because the anchoring analysis
and the time study need the without-copilot condition as well.

Suggestions themselves are cached in LLMTaskResult (task_type='copilot_labeling');
this table snapshots what was actually shown at labeling time, so later prompt
re-runs cannot retroactively change study data.

See: .claude/plans/labeling-copilot-design.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class LabelingCopilotLog(db.Model):
    """Per-annotator co-pilot log for one labeled item (audit trail + metrics)."""

    __tablename__ = "labeling_copilot_logs"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("rating_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("evaluation_items.item_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    # Span this log entry belongs to; '' = whole item (classic labeling).
    # See ItemLabelingEvaluation.span_id for why this is NOT NULL DEFAULT ''.
    # Conversation labeling logs one acceptance decision per span, so the
    # co-pilot's acceptance rate stays meaningful at span granularity.
    span_id: Mapped[str] = mapped_column(
        db.String(64), nullable=False, default="", server_default=""
    )

    # Cache row the shown suggestions came from (null if generation failed/missing)
    suggestion_result_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("llm_task_results.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Server-derived visibility: False = hidden-control item OR no suggestion
    # available. Never taken from the client (hidden control must stay covert).
    shown: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)

    # Snapshot of the suggestions at labeling time (label ids for SQL aggregation,
    # full JSON incl. rationale/evidence/confidence for export & qualitative review)
    suggested_label: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    suggested_label_2: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    suggestions_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    model_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    prompt_version: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Final human decision (mirrors ItemLabelingEvaluation.category_id)
    final_label: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Server-computed: primary suggestion chosen / any suggestion chosen.
    # NULL when nothing was shown (control items have no acceptance semantics).
    accepted: Mapped[Optional[bool]] = mapped_column(db.Boolean, nullable=True)
    accepted_any: Mapped[Optional[bool]] = mapped_column(db.Boolean, nullable=True)

    # "Was this suggestion helpful?" thumbs on the suggestion card
    # (PsyDefConv handbook A.8: "Record whether the suggestion was helpful.")
    helpful: Mapped[Optional[bool]] = mapped_column(db.Boolean, nullable=True)

    # Time from item display to first saved label; first-write only so
    # revisits/corrections don't overwrite the primary timing measure.
    time_on_item_ms: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "item_id", "scenario_id", "span_id",
            name="uix_user_item_scenario_span_copilot_log",
        ),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses/exports."""
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "item_id": self.item_id,
            "user_id": self.user_id,
            "span_id": self.span_id,
            "shown": self.shown,
            "suggested_label": self.suggested_label,
            "suggested_label_2": self.suggested_label_2,
            "suggestions_json": self.suggestions_json,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "final_label": self.final_label,
            "accepted": self.accepted,
            "accepted_any": self.accepted_any,
            "helpful": self.helpful,
            "time_on_item_ms": self.time_on_item_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<LabelingCopilotLog s{self.scenario_id}/i{self.item_id}/u{self.user_id} "
            f"shown={self.shown} accepted={self.accepted}>"
        )
