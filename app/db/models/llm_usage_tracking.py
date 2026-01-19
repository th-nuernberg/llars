"""
LLM Usage Tracking Models.

Tracks token usage per user, scenario, and model for budget enforcement
and analytics.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy import func

from db import db


class LLMUsageTracking(db.Model):
    """
    Tracks individual LLM API calls and their token usage.

    Records:
    - Who made the call (user_id)
    - Which scenario/thread it was for
    - Which model was used
    - Token counts (input/output)
    - Estimated costs
    - Processing time
    """

    __tablename__ = "llm_usage_tracking"

    # Primary key
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # User who triggered the evaluation
    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Context
    scenario_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("rating_scenarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    item_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("evaluation_items.item_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    # Backwards compatibility: thread_id is a synonym for item_id
    thread_id = synonym('item_id')

    # Model info
    model_id: Mapped[str] = mapped_column(
        db.String(100),
        nullable=False,
        index=True,
        comment="LLM model identifier (e.g., gpt-4o, claude-3-5-sonnet)"
    )
    task_type: Mapped[str] = mapped_column(
        db.String(50),
        nullable=False,
        index=True,
        comment="Task type: ranking, rating, authenticity, etc."
    )

    # Token counts
    input_tokens: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=0
    )
    output_tokens: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=0
    )
    # Note: total_tokens is computed in queries, not stored

    # Cost tracking
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(
        db.Numeric(10, 6),
        nullable=True,
        comment="Estimated cost in USD based on model pricing"
    )

    # Prompt tracking
    prompt_template_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey("prompt_templates.id", ondelete="SET NULL"),
        nullable=True
    )
    prompt_version: Mapped[Optional[str]] = mapped_column(
        db.String(20),
        nullable=True,
        comment="Version of prompt used for reproducibility"
    )

    # Performance
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        nullable=True,
        comment="Time taken for the LLM call in milliseconds"
    )

    # Status
    success: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Relationships
    user = relationship("User", backref="llm_usage_records", lazy="selectin")
    prompt_template = relationship("PromptTemplate", lazy="selectin")

    # Indexes for common queries
    __table_args__ = (
        db.Index("ix_llm_usage_user_month", "user_id", "created_at"),
        db.Index("ix_llm_usage_scenario", "scenario_id", "model_id"),
        db.Index("ix_llm_usage_model_task", "model_id", "task_type"),
    )

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens."""
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scenario_id": self.scenario_id,
            "thread_id": self.thread_id,
            "model_id": self.model_id,
            "task_type": self.task_type,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": float(self.estimated_cost_usd) if self.estimated_cost_usd else None,
            "prompt_template_id": self.prompt_template_id,
            "prompt_version": self.prompt_version,
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_user_monthly_usage(cls, user_id: int, year: int = None, month: int = None) -> dict:
        """Get total token usage for a user in a specific month."""
        if year is None or month is None:
            today = date.today()
            year = today.year
            month = today.month

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        result = db.session.query(
            func.sum(cls.input_tokens).label("input_tokens"),
            func.sum(cls.output_tokens).label("output_tokens"),
            func.sum(cls.estimated_cost_usd).label("total_cost"),
            func.count(cls.id).label("call_count")
        ).filter(
            cls.user_id == user_id,
            cls.created_at >= start_date,
            cls.created_at < end_date,
            cls.success == True  # noqa: E712
        ).first()

        return {
            "user_id": user_id,
            "year": year,
            "month": month,
            "input_tokens": result.input_tokens or 0,
            "output_tokens": result.output_tokens or 0,
            "total_tokens": (result.input_tokens or 0) + (result.output_tokens or 0),
            "total_cost_usd": float(result.total_cost) if result.total_cost else 0.0,
            "call_count": result.call_count or 0,
        }

    @classmethod
    def get_scenario_usage(cls, scenario_id: int) -> dict:
        """Get token usage breakdown for a scenario."""
        results = db.session.query(
            cls.model_id,
            func.sum(cls.input_tokens).label("input_tokens"),
            func.sum(cls.output_tokens).label("output_tokens"),
            func.sum(cls.estimated_cost_usd).label("total_cost"),
            func.count(cls.id).label("call_count"),
            func.avg(cls.processing_time_ms).label("avg_time_ms")
        ).filter(
            cls.scenario_id == scenario_id
        ).group_by(cls.model_id).all()

        return {
            "scenario_id": scenario_id,
            "by_model": [
                {
                    "model_id": r.model_id,
                    "input_tokens": r.input_tokens or 0,
                    "output_tokens": r.output_tokens or 0,
                    "total_tokens": (r.input_tokens or 0) + (r.output_tokens or 0),
                    "total_cost_usd": float(r.total_cost) if r.total_cost else 0.0,
                    "call_count": r.call_count or 0,
                    "avg_time_ms": float(r.avg_time_ms) if r.avg_time_ms else None,
                }
                for r in results
            ]
        }

    def __repr__(self) -> str:
        return f"<LLMUsageTracking {self.id}: {self.model_id} ({self.total_tokens} tokens)>"


class UserTokenBudget(db.Model):
    """
    Manages token budgets per user.

    Features:
    - Monthly token limits
    - Automatic reset
    - Warning thresholds
    - Hard/soft limits
    """

    __tablename__ = "user_token_budgets"

    # Primary key
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # User reference
    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Budget configuration
    monthly_token_limit: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=1000000,  # 1M tokens default
        comment="Maximum tokens per month"
    )

    # Current usage (cached for quick checks)
    current_month_usage: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=0,
        comment="Cached current month usage"
    )
    last_reset_date: Mapped[Optional[date]] = mapped_column(
        db.Date,
        nullable=True,
        comment="Date of last monthly reset"
    )

    # Threshold configuration
    warning_threshold_percent: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        default=80,
        comment="Percentage at which to warn user"
    )
    is_hard_limit: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=True,
        comment="If True, block usage when limit reached"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", backref="token_budget", lazy="selectin", uselist=False)

    @property
    def usage_percent(self) -> float:
        """Calculate current usage percentage."""
        if self.monthly_token_limit <= 0:
            return 0.0
        return (self.current_month_usage / self.monthly_token_limit) * 100

    @property
    def remaining_tokens(self) -> int:
        """Calculate remaining tokens for the month."""
        return max(0, self.monthly_token_limit - self.current_month_usage)

    @property
    def is_over_warning(self) -> bool:
        """Check if usage is over warning threshold."""
        return self.usage_percent >= self.warning_threshold_percent

    @property
    def is_over_limit(self) -> bool:
        """Check if usage is over the limit."""
        return self.current_month_usage >= self.monthly_token_limit

    def can_use_tokens(self, token_count: int) -> tuple[bool, str]:
        """
        Check if user can use the specified number of tokens.

        Returns:
            Tuple of (allowed, message)
        """
        # Check for monthly reset
        self._check_monthly_reset()

        if not self.is_hard_limit:
            return True, "Soft limit - usage allowed"

        if self.current_month_usage + token_count > self.monthly_token_limit:
            return False, f"Token budget exceeded. Limit: {self.monthly_token_limit}, Used: {self.current_month_usage}"

        if self.is_over_warning:
            return True, f"Warning: {self.usage_percent:.1f}% of monthly budget used"

        return True, "OK"

    def add_usage(self, token_count: int) -> None:
        """Add token usage to the current month."""
        self._check_monthly_reset()
        self.current_month_usage += token_count
        db.session.add(self)

    def _check_monthly_reset(self) -> None:
        """Reset usage if we're in a new month."""
        today = date.today()
        if self.last_reset_date is None or (
            today.year != self.last_reset_date.year or
            today.month != self.last_reset_date.month
        ):
            self.current_month_usage = 0
            self.last_reset_date = today
            db.session.add(self)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "monthly_token_limit": self.monthly_token_limit,
            "current_month_usage": self.current_month_usage,
            "remaining_tokens": self.remaining_tokens,
            "usage_percent": round(self.usage_percent, 2),
            "warning_threshold_percent": self.warning_threshold_percent,
            "is_hard_limit": self.is_hard_limit,
            "is_over_warning": self.is_over_warning,
            "is_over_limit": self.is_over_limit,
            "last_reset_date": self.last_reset_date.isoformat() if self.last_reset_date else None,
        }

    @classmethod
    def get_or_create(cls, user_id: int) -> "UserTokenBudget":
        """Get existing budget or create default one for user."""
        budget = cls.query.filter_by(user_id=user_id).first()
        if not budget:
            budget = cls(user_id=user_id)
            db.session.add(budget)
            db.session.flush()
        return budget

    def __repr__(self) -> str:
        return f"<UserTokenBudget {self.user_id}: {self.current_month_usage}/{self.monthly_token_limit}>"
