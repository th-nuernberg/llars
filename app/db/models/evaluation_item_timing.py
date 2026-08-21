"""Per-case evaluation timing.

Generic "time on item" measure for ALL evaluation types (rating, mail_rating,
ranking, comparison, communication_comparison, authenticity, labeling): one row
per (user, item, scenario) holding the milliseconds a rater spent on that single
case before the first save.

Why a separate, central table (not a column per vote model)
-----------------------------------------------------------
The six evaluation types persist their votes in six different tables, and some
(rating, ranking) write *several* rows per (user, item) — one per dimension /
feature — so there is no single natural row to hang the per-case duration on.
A dedicated (user, item, scenario) table gives every type ONE unambiguous timing
row, a single write path, and a single join in the export builders.

Labeling already logs a richer per-case row in ``LabelingCopilotLog`` (which
also carries co-pilot acceptance/helpful data). Labeling additionally writes
here so the export can read one uniform source; historical labeling data still
falls back to the co-pilot log's ``time_on_item_ms``.

First-write-only
----------------
``time_on_item_ms`` is the *time to first save* for a case. Revisits and
corrections must not overwrite it (see ``ItemTimingService.record_item_timing``),
mirroring ``LabelingCopilotLog.time_on_item_ms``.

See: app/services/evaluation/item_timing_service.py (write path),
app/services/evaluation/results_export_service.py (export join + derived
created_at-delta fallback column).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class EvaluationItemTiming(db.Model):
    """Per-annotator time-on-item for one evaluated case (any function type)."""

    __tablename__ = "evaluation_item_timings"

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

    # Span this timing belongs to; '' = whole item (every type except
    # conversation labeling). See ItemLabelingEvaluation.span_id for the
    # NOT NULL DEFAULT '' rationale.
    #
    # Without this column conversation labeling could not measure at all: the
    # first span of a conversation would write the row and the remaining ~91
    # would collide with the unique key, so "time per span" — the number the
    # amortisation estimate rests on — would silently never be recorded.
    span_id: Mapped[str] = mapped_column(
        db.String(64), nullable=False, default="", server_default=""
    )

    # Function type name at capture time (ranking/rating/mail_rating/comparison/
    # communication_comparison/authenticity/labeling/conversation_labeling) —
    # denormalised for export filtering; the authoritative type lives on the
    # scenario.
    function_type: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True)

    # Milliseconds from item display to first saved vote for this case.
    # First-write only: revisits/corrections don't overwrite it.
    time_on_item_ms: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "item_id", "scenario_id", "span_id",
            name="uix_user_item_scenario_span_timing",
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "item_id": self.item_id,
            "user_id": self.user_id,
            "span_id": self.span_id,
            "function_type": self.function_type,
            "time_on_item_ms": self.time_on_item_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<EvaluationItemTiming s{self.scenario_id}/i{self.item_id}/u{self.user_id} "
            f"time_on_item_ms={self.time_on_item_ms}>"
        )
