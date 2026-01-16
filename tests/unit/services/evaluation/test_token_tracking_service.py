"""
Tests for TokenTrackingService.

Tests token usage tracking, budget management, and cost calculation.
"""

import pytest
from datetime import date


class TestTokenTrackingService:
    """Tests for TokenTrackingService."""

    def test_TOKEN_001_check_budget_within_limit(self, app, db):
        """Should allow usage within budget limit."""
        from services.evaluation.token_tracking_service import TokenTrackingService
        from db.models import UserTokenBudget

        with app.app_context():
            # Create user budget
            budget = UserTokenBudget(
                user_id=1,
                monthly_token_limit=100000,
                current_month_usage=0,
            )
            db.session.add(budget)
            db.session.commit()

            result = TokenTrackingService.check_budget(user_id=1, estimated_tokens=5000)

            assert result["can_proceed"] is True
            assert result["remaining"] == 100000
            assert result["warning"] is False

    def test_TOKEN_002_check_budget_exceeds_soft_limit(self, app, db):
        """Should allow but warn when near limit."""
        from services.evaluation.token_tracking_service import TokenTrackingService
        from db.models import UserTokenBudget

        with app.app_context():
            budget = UserTokenBudget(
                user_id=1,
                monthly_token_limit=100000,
                current_month_usage=85000,  # 85% used
                warning_threshold_percent=80,
                is_hard_limit=False,
                last_reset_date=date.today(),  # Prevent auto-reset
            )
            db.session.add(budget)
            db.session.commit()

            result = TokenTrackingService.check_budget(user_id=1, estimated_tokens=5000)

            assert result["can_proceed"] is True
            assert result["warning"] is True

    def test_TOKEN_003_check_budget_exceeds_hard_limit(self, app, db):
        """Should raise error when hard limit exceeded."""
        from services.evaluation.token_tracking_service import (
            TokenTrackingService,
            BudgetExceededError,
        )
        from db.models import UserTokenBudget

        with app.app_context():
            budget = UserTokenBudget(
                user_id=1,
                monthly_token_limit=100000,
                current_month_usage=98000,
                is_hard_limit=True,
                last_reset_date=date.today(),  # Prevent auto-reset
            )
            db.session.add(budget)
            db.session.commit()

            with pytest.raises(BudgetExceededError) as exc_info:
                TokenTrackingService.check_budget(user_id=1, estimated_tokens=5000)

            assert exc_info.value.current_usage == 98000
            assert exc_info.value.limit == 100000
            assert exc_info.value.requested == 5000

    def test_TOKEN_004_track_usage_creates_record(self, app, db):
        """Should create a usage tracking record."""
        from services.evaluation.token_tracking_service import TokenTrackingService
        from db.models import LLMUsageTracking, UserTokenBudget

        with app.app_context():
            # Create budget first
            budget = UserTokenBudget(user_id=1, monthly_token_limit=1000000)
            db.session.add(budget)
            db.session.commit()

            tracking = TokenTrackingService.track_usage(
                user_id=1,
                model_id="gpt-4o",
                task_type="ranking",
                input_tokens=500,
                output_tokens=200,
                scenario_id=1,
                thread_id=1,
                processing_time_ms=1500,
            )

            assert tracking.id is not None
            assert tracking.total_tokens == 700
            assert tracking.model_id == "gpt-4o"
            assert tracking.estimated_cost_usd > 0

            # Verify budget updated
            db.session.refresh(budget)
            assert budget.current_month_usage == 700

    def test_TOKEN_005_calculate_cost_known_model(self, app, db):
        """Should calculate cost for known models."""
        from services.evaluation.token_tracking_service import TokenTrackingService

        # GPT-4o costs: input $2.50, output $10.00 per 1M tokens
        cost = TokenTrackingService.calculate_cost(
            model_id="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )

        # Expected: (1000/1M * 2.50) + (500/1M * 10.00) = 0.0025 + 0.005 = 0.0075
        assert 0.007 <= cost <= 0.008

    def test_TOKEN_006_calculate_cost_unknown_model(self, app, db):
        """Should use default cost for unknown models."""
        from services.evaluation.token_tracking_service import TokenTrackingService

        cost = TokenTrackingService.calculate_cost(
            model_id="unknown-model-xyz",
            input_tokens=1000,
            output_tokens=500,
        )

        # Should use default costs
        assert cost > 0

    def test_TOKEN_007_get_user_usage_summary(self, app, db):
        """Should return usage summary for a user."""
        from services.evaluation.token_tracking_service import TokenTrackingService
        from db.models import UserTokenBudget

        with app.app_context():
            # Create budget
            budget = UserTokenBudget(
                user_id=1,
                monthly_token_limit=1000000,
                current_month_usage=0,
            )
            db.session.add(budget)
            db.session.commit()

            # Track some usage
            TokenTrackingService.track_usage(
                user_id=1,
                model_id="gpt-4o",
                task_type="ranking",
                input_tokens=500,
                output_tokens=200,
            )
            TokenTrackingService.track_usage(
                user_id=1,
                model_id="gpt-4o-mini",
                task_type="rating",
                input_tokens=300,
                output_tokens=100,
            )

            summary = TokenTrackingService.get_user_usage_summary(user_id=1)

            assert summary["total_tokens"] == 1100
            assert summary["total_calls"] == 2
            assert len(summary["by_model"]) == 2
            assert len(summary["by_task"]) == 2
            assert summary["budget"]["used"] == 1100

    def test_TOKEN_008_set_user_budget(self, app, db):
        """Should update user budget settings."""
        from services.evaluation.token_tracking_service import TokenTrackingService
        from db.models import UserTokenBudget

        with app.app_context():
            # Create initial budget
            budget = UserTokenBudget(
                user_id=1,
                monthly_token_limit=100000,
                warning_threshold_percent=80,
                is_hard_limit=True,
            )
            db.session.add(budget)
            db.session.commit()

            # Update budget
            updated = TokenTrackingService.set_user_budget(
                user_id=1,
                monthly_limit=500000,
                warning_threshold=90,
                is_hard_limit=False,
            )

            assert updated.monthly_token_limit == 500000
            assert updated.warning_threshold_percent == 90
            assert updated.is_hard_limit is False

    def test_TOKEN_009_reset_monthly_usage(self, app, db):
        """Should reset monthly usage counters."""
        from services.evaluation.token_tracking_service import TokenTrackingService
        from db.models import UserTokenBudget

        with app.app_context():
            # Create budgets with usage
            for user_id in [1, 2, 3]:
                budget = UserTokenBudget(
                    user_id=user_id,
                    monthly_token_limit=100000,
                    current_month_usage=50000,
                )
                db.session.add(budget)
            db.session.commit()

            # Reset all
            count = TokenTrackingService.reset_monthly_usage()

            assert count == 3

            # Verify all reset
            for user_id in [1, 2, 3]:
                budget = UserTokenBudget.query.filter_by(user_id=user_id).first()
                assert budget.current_month_usage == 0

    def test_TOKEN_010_reset_monthly_usage_single_user(self, app, db):
        """Should reset only specific user when ID given."""
        from services.evaluation.token_tracking_service import TokenTrackingService
        from db.models import UserTokenBudget

        with app.app_context():
            # Create budgets
            for user_id in [1, 2]:
                budget = UserTokenBudget(
                    user_id=user_id,
                    monthly_token_limit=100000,
                    current_month_usage=50000,
                )
                db.session.add(budget)
            db.session.commit()

            # Reset only user 1
            count = TokenTrackingService.reset_monthly_usage(user_id=1)

            assert count == 1

            # Verify only user 1 reset
            budget1 = UserTokenBudget.query.filter_by(user_id=1).first()
            budget2 = UserTokenBudget.query.filter_by(user_id=2).first()
            assert budget1.current_month_usage == 0
            assert budget2.current_month_usage == 50000

    def test_TOKEN_011_get_all_budgets(self, app, db):
        """Should return all user budgets for admin view."""
        from services.evaluation.token_tracking_service import TokenTrackingService
        from db.models import UserTokenBudget

        with app.app_context():
            # Create budgets
            for user_id in [1, 2, 3]:
                budget = UserTokenBudget(
                    user_id=user_id,
                    monthly_token_limit=100000 * user_id,
                    current_month_usage=10000 * user_id,
                )
                db.session.add(budget)
            db.session.commit()

            budgets = TokenTrackingService.get_all_budgets()

            assert len(budgets) == 3
            for b in budgets:
                assert "user_id" in b
                assert "monthly_limit" in b
                assert "current_usage" in b
                assert "usage_percent" in b
