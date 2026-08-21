"""
Convergence Service.

Analyzes evaluation scores across iterations to determine whether the
pipeline should continue, has converged, or needs human escalation.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConvergenceService:
    """Analyzes pipeline convergence based on scores and history."""

    @classmethod
    def analyze(
        cls,
        current_scores: Dict[str, Any],
        history: List[Dict[str, Any]],
        thresholds: Dict[str, Any],
        max_plateau_iterations: int = 3,
    ) -> Dict[str, Any]:
        """
        Analyze current scores vs. history and decide next action.

        Args:
            current_scores: Scores from the current iteration
                {"dimensions": {"dim_id": avg_score}, "avg_score": float}
            history: Previous iteration results
            thresholds: Target thresholds
                {"global_threshold": float, "dimension_thresholds": {"dim_id": float}}
            max_plateau_iterations: How many iterations without improvement before escalation

        Returns:
            {
                "action": "continue" | "converged" | "escalate",
                "reason": str,
                "reasoning": str (detailed explanation),
                "delta": float (improvement vs previous best),
                "avg_score": float,
                "is_new_best": bool,
            }
        """
        current_avg = current_scores.get('avg_score', 0)
        dimensions = current_scores.get('dimensions', {})

        global_threshold = thresholds.get('global_threshold', 4.0)
        dim_thresholds = thresholds.get('dimension_thresholds', {})
        epsilon = thresholds.get('convergence_epsilon', 0.05)

        # Calculate best historical score
        best_avg = 0
        if history:
            best_avg = max(
                h.get('scores', {}).get('avg_score', 0)
                for h in history
            )

        delta = round(current_avg - best_avg, 3) if history else 0
        is_new_best = current_avg > best_avg if history else True

        # Check if all dimensions meet their thresholds
        all_above = cls._check_thresholds(
            dimensions, global_threshold, dim_thresholds
        )

        # Build reasoning
        reasoning_parts = []

        if not history:
            reasoning_parts.append(
                f"Baseline established. Average score: {current_avg:.2f}/{global_threshold:.1f}."
            )
        else:
            if is_new_best:
                reasoning_parts.append(
                    f"New best score: {current_avg:.2f} (delta: +{delta:.3f})."
                )
            else:
                reasoning_parts.append(
                    f"Score: {current_avg:.2f}, best remains {best_avg:.2f} "
                    f"(delta: {delta:.3f})."
                )

        # Report dimension status
        weak_dims = []
        for dim_id, score in dimensions.items():
            threshold = dim_thresholds.get(dim_id, global_threshold)
            if score < threshold:
                weak_dims.append(f"{dim_id} ({score:.2f}/{threshold:.1f})")

        if weak_dims:
            reasoning_parts.append(
                f"Dimensions below threshold: {', '.join(weak_dims)}."
            )
        elif dimensions:
            reasoning_parts.append("All dimensions meet thresholds.")

        reasoning = " ".join(reasoning_parts)

        # Decision logic
        if all_above and current_avg >= global_threshold:
            return {
                'action': 'converged',
                'reason': 'all_thresholds_met',
                'reasoning': reasoning + " Converged - all targets met.",
                'delta': delta,
                'avg_score': current_avg,
                'is_new_best': is_new_best,
            }

        # Check for plateau (no improvement over N iterations)
        if len(history) >= max_plateau_iterations:
            recent_deltas = cls._calculate_recent_deltas(history, max_plateau_iterations)
            if all(abs(d) < epsilon for d in recent_deltas):
                return {
                    'action': 'escalate',
                    'reason': 'plateau',
                    'reasoning': (
                        reasoning +
                        f" Plateau detected: no significant improvement "
                        f"(delta < {epsilon}) over last {max_plateau_iterations} iterations."
                    ),
                    'delta': delta,
                    'avg_score': current_avg,
                    'is_new_best': is_new_best,
                }

        return {
            'action': 'continue',
            'reason': 'improvement_possible',
            'reasoning': reasoning + " Continuing optimization.",
            'delta': delta,
            'avg_score': current_avg,
            'is_new_best': is_new_best,
        }

    @classmethod
    def _check_thresholds(
        cls,
        dimensions: Dict[str, float],
        global_threshold: float,
        dim_thresholds: Dict[str, float],
    ) -> bool:
        """Check if all dimensions meet their respective thresholds."""
        if not dimensions:
            return False

        for dim_id, score in dimensions.items():
            threshold = dim_thresholds.get(dim_id, global_threshold)
            if score < threshold:
                return False

        return True

    @classmethod
    def _calculate_recent_deltas(
        cls,
        history: List[Dict[str, Any]],
        n: int,
    ) -> List[float]:
        """Calculate score deltas for the last N iterations."""
        if len(history) < 2:
            return []

        recent = history[-n:]
        deltas = []
        for i in range(1, len(recent)):
            prev_avg = recent[i - 1].get('scores', {}).get('avg_score', 0)
            curr_avg = recent[i].get('scores', {}).get('avg_score', 0)
            deltas.append(curr_avg - prev_avg)

        return deltas
