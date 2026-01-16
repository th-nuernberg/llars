"""
Token Tracking Service for LLM Usage.

Tracks token usage per user, scenario, and model.
Enforces budget limits and calculates costs.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from db import db
from db.models import LLMUsageTracking, UserTokenBudget

logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """Raised when a user exceeds their token budget."""

    def __init__(
        self,
        message: str,
        *,
        current_usage: int,
        limit: int,
        requested: int,
    ):
        super().__init__(message)
        self.current_usage = current_usage
        self.limit = limit
        self.requested = requested


# Approximate costs per 1M tokens (in USD)
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Anthropic
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    # Default for unknown models
    "_default": {"input": 1.00, "output": 3.00},
}


class TokenTrackingService:
    """Service for tracking LLM token usage and enforcing budgets."""

    @staticmethod
    def check_budget(
        user_id: int,
        estimated_tokens: int,
    ) -> Dict[str, Any]:
        """
        Check if user has enough budget for the estimated tokens.

        Args:
            user_id: User ID to check
            estimated_tokens: Estimated tokens to use

        Returns:
            Dict with budget info: {can_proceed, current_usage, limit, remaining, warning}

        Raises:
            BudgetExceededError: If hard limit is enabled and exceeded
        """
        budget = UserTokenBudget.get_or_create(user_id)

        can_proceed, message = budget.can_use_tokens(estimated_tokens)
        remaining = budget.monthly_token_limit - budget.current_month_usage
        warning_threshold = int(
            budget.monthly_token_limit * budget.warning_threshold_percent / 100
        )
        show_warning = budget.current_month_usage >= warning_threshold

        result = {
            "can_proceed": can_proceed,
            "current_usage": budget.current_month_usage,
            "limit": budget.monthly_token_limit,
            "remaining": max(0, remaining),
            "warning": show_warning,
            "is_hard_limit": budget.is_hard_limit,
            "warning_threshold_percent": budget.warning_threshold_percent,
        }

        if not can_proceed and budget.is_hard_limit:
            raise BudgetExceededError(
                f"Token budget exceeded: {budget.current_month_usage}/{budget.monthly_token_limit}",
                current_usage=budget.current_month_usage,
                limit=budget.monthly_token_limit,
                requested=estimated_tokens,
            )

        return result

    @staticmethod
    def track_usage(
        *,
        user_id: int,
        model_id: str,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
        scenario_id: Optional[int] = None,
        thread_id: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        prompt_template_id: Optional[int] = None,
    ) -> LLMUsageTracking:
        """
        Track token usage for an LLM call.

        Args:
            user_id: User who initiated the call
            model_id: Model used
            task_type: Type of task (ranking, rating, etc.)
            input_tokens: Input token count
            output_tokens: Output token count
            scenario_id: Optional scenario ID
            thread_id: Optional thread ID
            processing_time_ms: Optional processing time
            success: Whether the call succeeded
            error_message: Optional error message
            prompt_template_id: Optional prompt template ID used

        Returns:
            Created LLMUsageTracking record
        """
        # Calculate estimated cost
        total_tokens = input_tokens + output_tokens
        estimated_cost = TokenTrackingService.calculate_cost(
            model_id, input_tokens, output_tokens
        )

        # Create tracking record (note: total_tokens is a computed property)
        tracking = LLMUsageTracking(
            user_id=user_id,
            scenario_id=scenario_id,
            thread_id=thread_id,
            model_id=model_id,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost,
            processing_time_ms=processing_time_ms,
            success=success,
            error_message=error_message,
            prompt_template_id=prompt_template_id,
        )
        db.session.add(tracking)

        # Update user's monthly budget
        if success:
            budget = UserTokenBudget.get_or_create(user_id)
            budget.add_usage(total_tokens)

        db.session.commit()

        logger.debug(
            "Tracked %d tokens for user %d, model %s, task %s (cost: $%.6f)",
            total_tokens, user_id, model_id, task_type, estimated_cost
        )
        return tracking

    @staticmethod
    def calculate_cost(
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Calculate estimated cost in USD.

        Args:
            model_id: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Find matching cost entry
        costs = MODEL_COSTS.get(model_id)

        # Try partial match for model variants
        if not costs:
            for key in MODEL_COSTS:
                if key != "_default" and key in model_id:
                    costs = MODEL_COSTS[key]
                    break

        # Fall back to default
        if not costs:
            costs = MODEL_COSTS["_default"]

        # Calculate cost (prices are per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]

        return round(input_cost + output_cost, 6)

    @staticmethod
    def get_user_usage_summary(
        user_id: int,
        *,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get usage summary for a user.

        Args:
            user_id: User ID
            month: Optional month filter (1-12)
            year: Optional year filter

        Returns:
            Dict with usage statistics
        """
        now = datetime.utcnow()
        month = month or now.month
        year = year or now.year

        usage = LLMUsageTracking.get_user_monthly_usage(user_id, year, month)
        budget = UserTokenBudget.get_or_create(user_id)

        # Get breakdown by model
        by_model = LLMUsageTracking.query.filter(
            LLMUsageTracking.user_id == user_id,
            db.extract("month", LLMUsageTracking.created_at) == month,
            db.extract("year", LLMUsageTracking.created_at) == year,
        ).with_entities(
            LLMUsageTracking.model_id,
            db.func.sum(LLMUsageTracking.input_tokens + LLMUsageTracking.output_tokens).label("tokens"),
            db.func.sum(LLMUsageTracking.estimated_cost_usd).label("cost"),
            db.func.count(LLMUsageTracking.id).label("calls"),
        ).group_by(LLMUsageTracking.model_id).all()

        # Get breakdown by task type
        by_task = LLMUsageTracking.query.filter(
            LLMUsageTracking.user_id == user_id,
            db.extract("month", LLMUsageTracking.created_at) == month,
            db.extract("year", LLMUsageTracking.created_at) == year,
        ).with_entities(
            LLMUsageTracking.task_type,
            db.func.sum(LLMUsageTracking.input_tokens + LLMUsageTracking.output_tokens).label("tokens"),
            db.func.count(LLMUsageTracking.id).label("calls"),
        ).group_by(LLMUsageTracking.task_type).all()

        return {
            "user_id": user_id,
            "month": month,
            "year": year,
            "total_tokens": usage.get("total_tokens", 0),
            "total_cost_usd": usage.get("total_cost", 0),
            "total_calls": usage.get("call_count", 0),
            "budget": {
                "limit": budget.monthly_token_limit,
                "used": budget.current_month_usage,
                "remaining": max(0, budget.monthly_token_limit - budget.current_month_usage),
                "usage_percent": round(
                    (budget.current_month_usage / budget.monthly_token_limit) * 100, 1
                ) if budget.monthly_token_limit > 0 else 0,
            },
            "by_model": [
                {
                    "model_id": row.model_id,
                    "tokens": row.tokens or 0,
                    "cost_usd": float(row.cost or 0),
                    "calls": row.calls or 0,
                }
                for row in by_model
            ],
            "by_task": [
                {
                    "task_type": row.task_type,
                    "tokens": row.tokens or 0,
                    "calls": row.calls or 0,
                }
                for row in by_task
            ],
        }

    @staticmethod
    def get_scenario_usage(scenario_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a scenario.

        Args:
            scenario_id: Scenario ID

        Returns:
            Dict with scenario usage statistics
        """
        usage = LLMUsageTracking.get_scenario_usage(scenario_id)

        # Get breakdown by model
        by_model = LLMUsageTracking.query.filter_by(
            scenario_id=scenario_id
        ).with_entities(
            LLMUsageTracking.model_id,
            db.func.sum(LLMUsageTracking.total_tokens).label("tokens"),
            db.func.sum(LLMUsageTracking.estimated_cost_usd).label("cost"),
            db.func.count(LLMUsageTracking.id).label("calls"),
        ).group_by(LLMUsageTracking.model_id).all()

        return {
            "scenario_id": scenario_id,
            "total_tokens": usage.get("total_tokens", 0),
            "total_cost_usd": usage.get("total_cost", 0),
            "total_calls": usage.get("call_count", 0),
            "by_model": [
                {
                    "model_id": row.model_id,
                    "tokens": row.tokens or 0,
                    "cost_usd": float(row.cost or 0),
                    "calls": row.calls or 0,
                }
                for row in by_model
            ],
        }

    @staticmethod
    def set_user_budget(
        user_id: int,
        *,
        monthly_limit: Optional[int] = None,
        warning_threshold: Optional[int] = None,
        is_hard_limit: Optional[bool] = None,
    ) -> UserTokenBudget:
        """
        Set user's token budget settings.

        Args:
            user_id: User ID
            monthly_limit: New monthly limit (tokens)
            warning_threshold: Warning threshold percentage
            is_hard_limit: Whether to enforce as hard limit

        Returns:
            Updated UserTokenBudget
        """
        budget = UserTokenBudget.get_or_create(user_id)

        if monthly_limit is not None:
            budget.monthly_token_limit = monthly_limit
        if warning_threshold is not None:
            budget.warning_threshold_percent = warning_threshold
        if is_hard_limit is not None:
            budget.is_hard_limit = is_hard_limit

        db.session.commit()
        return budget

    @staticmethod
    def reset_monthly_usage(user_id: Optional[int] = None) -> int:
        """
        Reset monthly usage counters.

        Args:
            user_id: Optional specific user ID, or all users if None

        Returns:
            Number of budgets reset
        """
        query = UserTokenBudget.query
        if user_id:
            query = query.filter_by(user_id=user_id)

        count = 0
        for budget in query.all():
            budget.current_month_usage = 0
            budget.last_reset_date = datetime.utcnow()
            count += 1

        db.session.commit()
        logger.info("Reset monthly usage for %d users", count)
        return count

    @staticmethod
    def get_all_budgets() -> List[Dict[str, Any]]:
        """Get all user budgets for admin overview."""
        budgets = UserTokenBudget.query.all()
        return [
            {
                "user_id": b.user_id,
                "monthly_limit": b.monthly_token_limit,
                "current_usage": b.current_month_usage,
                "remaining": max(0, b.monthly_token_limit - b.current_month_usage),
                "usage_percent": round(
                    (b.current_month_usage / b.monthly_token_limit) * 100, 1
                ) if b.monthly_token_limit > 0 else 0,
                "is_hard_limit": b.is_hard_limit,
                "last_reset_date": b.last_reset_date.isoformat() if b.last_reset_date else None,
            }
            for b in budgets
        ]
