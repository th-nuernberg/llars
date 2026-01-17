"""
Agreement Metrics Service.

Calculates inter-rater reliability metrics for LLM and human evaluations:
- Krippendorff's Alpha (ordinal, nominal, interval)
- Cohen's Kappa (pairwise)
- Fleiss' Kappa (multi-rater)
- Kendall's Tau (rank correlation)
- Spearman's Rho (rank correlation)
- Percent Agreement
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
import math

from db import db
from db.models import (
    Feature,
    LLMTaskResult,
    RatingScenarios,
    ScenarioThreads,
    ScenarioUsers,
    UserFeatureRanking,
    UserFeatureRating,
    UserMailHistoryRating,
    UserAuthenticityVote,
)

logger = logging.getLogger(__name__)


class AgreementMetricsService:
    """
    Service for calculating inter-rater agreement metrics.

    Supports multiple metric types for different evaluation scenarios.
    """

    # Metric descriptions for UI tooltips
    METRIC_DESCRIPTIONS = {
        "krippendorff_alpha": {
            "name": "Krippendorff's Alpha",
            "description": "Measures agreement for multiple raters, handling missing data. Values: <0 = worse than random, 0 = random agreement, 1 = perfect agreement. Recommended: α ≥ 0.667 for tentative conclusions, α ≥ 0.800 for reliable conclusions.",
            "range": "-1.0 to 1.0",
        },
        "cohens_kappa": {
            "name": "Cohen's Kappa",
            "description": "Measures agreement between two raters, accounting for chance. Values: <0 = worse than chance, 0 = chance agreement, 1 = perfect agreement. Interpretation: 0.41-0.60 = moderate, 0.61-0.80 = substantial, 0.81-1.00 = almost perfect.",
            "range": "-1.0 to 1.0",
        },
        "fleiss_kappa": {
            "name": "Fleiss' Kappa",
            "description": "Extends Cohen's Kappa for multiple raters. Same interpretation as Cohen's Kappa but for 3+ raters evaluating the same items.",
            "range": "-1.0 to 1.0",
        },
        "kendall_tau": {
            "name": "Kendall's Tau",
            "description": "Measures ordinal association between rankings. Values: -1 = perfect disagreement, 0 = no association, 1 = perfect agreement. Robust to outliers.",
            "range": "-1.0 to 1.0",
        },
        "spearman_rho": {
            "name": "Spearman's Rho",
            "description": "Non-parametric rank correlation. Similar to Pearson but uses ranks instead of raw values. Less sensitive to outliers than Pearson.",
            "range": "-1.0 to 1.0",
        },
        "percent_agreement": {
            "name": "Percent Agreement",
            "description": "Simple percentage of identical ratings. Easy to interpret but doesn't account for chance agreement. Use alongside other metrics.",
            "range": "0% to 100%",
        },
        "icc": {
            "name": "ICC (Intraclass Correlation)",
            "description": "Measures reliability of ratings by comparing variability within subjects to total variability. ICC(2,1) for single rater reliability. Values: <0.50 = poor, 0.50-0.75 = moderate, 0.75-0.90 = good, >0.90 = excellent.",
            "range": "0.0 to 1.0",
        },
        "kendall_w": {
            "name": "Kendall's W (Concordance)",
            "description": "Measures agreement among multiple raters on rankings. Values: 0 = no agreement, 1 = perfect agreement. W > 0.7 indicates strong agreement.",
            "range": "0.0 to 1.0",
        },
        "mae": {
            "name": "MAE (Mean Absolute Error)",
            "description": "Average absolute difference between predictions and ground truth. Lower is better. Useful when ground truth labels are available.",
            "range": "0.0 to max_scale",
        },
        "rmse": {
            "name": "RMSE (Root Mean Squared Error)",
            "description": "Square root of average squared differences. Penalizes large errors more than MAE. Lower is better.",
            "range": "0.0 to max_scale",
        },
        "bradley_terry": {
            "name": "Bradley-Terry Score",
            "description": "Estimates item strength from pairwise comparisons. Higher scores indicate items that win more comparisons. Useful for ranking items by preference.",
            "range": "0.0 to 1.0 (normalized)",
        },
        "macro_f1": {
            "name": "Macro F1 Score",
            "description": "Average F1 across all classes (unweighted). Treats all classes equally regardless of frequency. Good for imbalanced datasets.",
            "range": "0.0 to 1.0",
        },
        "micro_f1": {
            "name": "Micro F1 Score",
            "description": "F1 calculated from total TP, FP, FN across classes. Weighted by class frequency. Better reflects overall performance.",
            "range": "0.0 to 1.0",
        },
    }

    @staticmethod
    def calculate_all_metrics(
        scenario_id: int,
        *,
        include_llm: bool = True,
        include_human: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate all agreement metrics for a scenario.

        Args:
            scenario_id: Scenario ID to analyze
            include_llm: Include LLM evaluators
            include_human: Include human evaluators

        Returns:
            Dict with metrics, details, and descriptions
        """
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            return {"error": "Scenario not found"}

        # Get task type
        from db.models import FeatureFunctionType
        function_type = FeatureFunctionType.query.filter_by(
            function_type_id=scenario.function_type_id
        ).first()
        task_type = function_type.name if function_type else None

        # Collect evaluations
        evaluations = AgreementMetricsService._collect_evaluations(
            scenario_id=scenario_id,
            task_type=task_type,
            include_llm=include_llm,
            include_human=include_human,
        )

        if not evaluations["raters"]:
            return {"error": "No evaluations found"}

        # Calculate metrics based on task type
        metrics = {}
        if task_type == "ranking":
            metrics = AgreementMetricsService._calculate_ranking_metrics(evaluations)
        elif task_type == "rating":
            metrics = AgreementMetricsService._calculate_rating_metrics(evaluations)
        elif task_type == "authenticity":
            metrics = AgreementMetricsService._calculate_authenticity_metrics(evaluations)
        elif task_type == "mail_rating":
            metrics = AgreementMetricsService._calculate_mail_rating_metrics(evaluations)
        elif task_type == "comparison":
            metrics = AgreementMetricsService._calculate_comparison_metrics(evaluations)
        elif task_type == "text_classification":
            metrics = AgreementMetricsService._calculate_classification_metrics(evaluations)

        return {
            "scenario_id": scenario_id,
            "task_type": task_type,
            "rater_count": len(evaluations["raters"]),
            "raters": evaluations["raters"],
            "item_count": len(evaluations["items"]),
            "metrics": metrics,
            "metric_descriptions": AgreementMetricsService.METRIC_DESCRIPTIONS,
        }

    @staticmethod
    def _collect_evaluations(
        *,
        scenario_id: int,
        task_type: str,
        include_llm: bool,
        include_human: bool,
    ) -> Dict[str, Any]:
        """Collect all evaluations for a scenario into a common format."""
        evaluations = {
            "raters": [],
            "items": [],
            "data": defaultdict(dict),  # data[item_id][rater_id] = value
        }

        # Get thread IDs
        thread_ids = [
            t.thread_id for t in
            ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
        ]
        evaluations["items"] = thread_ids

        # Collect LLM evaluations
        if include_llm:
            llm_results = LLMTaskResult.query.filter(
                LLMTaskResult.scenario_id == scenario_id,
                LLMTaskResult.task_type == task_type,
                LLMTaskResult.payload_json.isnot(None),
            ).all()

            llm_raters = set()
            for result in llm_results:
                rater_id = f"llm:{result.model_id}"
                llm_raters.add(rater_id)
                value = AgreementMetricsService._extract_value(
                    result.payload_json, task_type
                )
                if value is not None:
                    evaluations["data"][result.thread_id][rater_id] = value

            evaluations["raters"].extend(sorted(llm_raters))

        # Collect human evaluations
        if include_human:
            human_raters = AgreementMetricsService._collect_human_evaluations(
                scenario_id, task_type, thread_ids, evaluations
            )
            evaluations["raters"].extend(sorted(human_raters))

        return evaluations

    @staticmethod
    def _collect_human_evaluations(
        scenario_id: int,
        task_type: str,
        thread_ids: List[int],
        evaluations: Dict[str, Any],
    ) -> set:
        """Collect human evaluations based on task type."""
        human_raters = set()

        if task_type == "ranking":
            # Join through Feature to get thread_id
            rankings = db.session.query(
                UserFeatureRanking, Feature.thread_id
            ).join(
                Feature, UserFeatureRanking.feature_id == Feature.feature_id
            ).filter(
                Feature.thread_id.in_(thread_ids),
            ).all()

            for ranking, thread_id in rankings:
                rater_id = f"human:{ranking.user_id}"
                human_raters.add(rater_id)
                value = ranking.bucket
                if value:
                    evaluations["data"][thread_id][rater_id] = value

        elif task_type == "rating":
            # Join through Feature to get thread_id
            # UserFeatureRating uses rating_content, not rating
            ratings = db.session.query(
                UserFeatureRating, Feature.thread_id
            ).join(
                Feature, UserFeatureRating.feature_id == Feature.feature_id
            ).filter(
                Feature.thread_id.in_(thread_ids),
            ).all()

            for rating, thread_id in ratings:
                rater_id = f"human:{rating.user_id}"
                human_raters.add(rater_id)
                if rating.rating_content is not None:
                    evaluations["data"][thread_id][rater_id] = rating.rating_content

        elif task_type == "mail_rating":
            # UserMailHistoryRating has direct thread_id
            ratings = UserMailHistoryRating.query.filter(
                UserMailHistoryRating.thread_id.in_(thread_ids),
            ).all()

            for rating in ratings:
                rater_id = f"human:{rating.user_id}"
                human_raters.add(rater_id)
                # Use overall_rating as the primary rating field
                if rating.overall_rating is not None:
                    evaluations["data"][rating.thread_id][rater_id] = rating.overall_rating

        elif task_type == "authenticity":
            votes = UserAuthenticityVote.query.filter(
                UserAuthenticityVote.thread_id.in_(thread_ids),
            ).all()

            for vote in votes:
                rater_id = f"human:{vote.user_id}"
                human_raters.add(rater_id)
                if vote.vote:
                    evaluations["data"][vote.thread_id][rater_id] = vote.vote

        return human_raters

    @staticmethod
    def _extract_value(payload: Dict[str, Any], task_type: str) -> Any:
        """Extract the relevant value from an LLM evaluation payload."""
        if not payload:
            return None

        if task_type == "ranking":
            # Return bucket assignments as a dict
            if "buckets" in payload:
                return payload["buckets"]
            return {k: v for k, v in payload.items() if k in ["gut", "mittel", "schlecht", "neutral"]}

        elif task_type == "rating":
            # Return average rating or ratings dict
            if "average_rating" in payload:
                return payload["average_rating"]
            if "ratings" in payload:
                ratings = payload["ratings"]
                if isinstance(ratings, list) and ratings:
                    return sum(r.get("rating", 0) for r in ratings) / len(ratings)
            return None

        elif task_type == "authenticity":
            return payload.get("vote")

        elif task_type == "mail_rating":
            return payload.get("overall_rating") or payload.get("rating")

        elif task_type == "comparison":
            return payload.get("winner")

        elif task_type == "text_classification":
            return payload.get("label")

        return None

    @staticmethod
    def _calculate_ranking_metrics(evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for ranking evaluations."""
        data = evaluations["data"]
        raters = evaluations["raters"]
        items = evaluations["items"]

        # For ranking, calculate various agreement metrics
        results = {}

        # Krippendorff's Alpha for ordinal/ranking data
        alpha = AgreementMetricsService._krippendorff_alpha(data, raters, items, "ordinal")
        if alpha is not None:
            results["krippendorff_alpha"] = {
                "value": alpha,
                "interpretation": AgreementMetricsService._interpret_alpha(alpha),
            }

        if len(raters) >= 2:
            # Calculate pairwise Kendall's Tau
            tau_values = []
            for i, r1 in enumerate(raters):
                for r2 in raters[i + 1:]:
                    tau = AgreementMetricsService._kendall_tau_for_buckets(
                        data, r1, r2, items
                    )
                    if tau is not None:
                        tau_values.append(tau)

            if tau_values:
                results["kendall_tau"] = {
                    "value": sum(tau_values) / len(tau_values),
                    "pairwise_values": tau_values,
                    "interpretation": AgreementMetricsService._interpret_correlation(
                        sum(tau_values) / len(tau_values)
                    ),
                }

            # Kendall's W (Coefficient of Concordance)
            kendall_w = AgreementMetricsService._kendall_w(data, raters, items)
            if kendall_w is not None:
                results["kendall_w"] = {
                    "value": kendall_w,
                    "interpretation": AgreementMetricsService._interpret_kendall_w(kendall_w),
                }

        # Calculate Fleiss' Kappa for bucket assignments
        kappa = AgreementMetricsService._fleiss_kappa_for_buckets(data, raters, items)
        if kappa is not None:
            results["fleiss_kappa"] = {
                "value": kappa,
                "interpretation": AgreementMetricsService._interpret_kappa(kappa),
            }

        # Percent agreement
        percent = AgreementMetricsService._percent_agreement(data, raters, items)
        if percent is not None:
            results["percent_agreement"] = {
                "value": percent,
                "interpretation": f"{percent:.1f}% der Bewertungen stimmen überein",
            }

        return results

    @staticmethod
    def _calculate_rating_metrics(evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for rating evaluations."""
        return AgreementMetricsService._calculate_numeric_metrics(evaluations)

    @staticmethod
    def _calculate_mail_rating_metrics(evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for mail rating evaluations."""
        return AgreementMetricsService._calculate_numeric_metrics(evaluations)

    @staticmethod
    def _calculate_numeric_metrics(evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for numeric (ordinal) evaluations."""
        data = evaluations["data"]
        raters = evaluations["raters"]
        items = evaluations["items"]

        results = {}

        # Krippendorff's Alpha for ordinal data
        alpha = AgreementMetricsService._krippendorff_alpha(data, raters, items, "ordinal")
        if alpha is not None:
            results["krippendorff_alpha"] = {
                "value": alpha,
                "interpretation": AgreementMetricsService._interpret_alpha(alpha),
            }

        # ICC (Intraclass Correlation Coefficient)
        icc = AgreementMetricsService._icc(data, raters, items)
        if icc is not None:
            results["icc"] = {
                "value": icc,
                "interpretation": AgreementMetricsService._interpret_icc(icc),
            }

        # Percent agreement
        percent = AgreementMetricsService._percent_agreement(data, raters, items)
        if percent is not None:
            results["percent_agreement"] = {
                "value": percent,
                "interpretation": f"{percent:.1f}% der Bewertungen stimmen überein",
            }

        # Pairwise Cohen's Kappa
        if len(raters) == 2:
            kappa = AgreementMetricsService._cohens_kappa(data, raters[0], raters[1], items)
            if kappa is not None:
                results["cohens_kappa"] = {
                    "value": kappa,
                    "interpretation": AgreementMetricsService._interpret_kappa(kappa),
                }

        # Spearman's Rho
        if len(raters) >= 2:
            rho_values = []
            for i, r1 in enumerate(raters):
                for r2 in raters[i + 1:]:
                    rho = AgreementMetricsService._spearman_rho(data, r1, r2, items)
                    if rho is not None:
                        rho_values.append(rho)

            if rho_values:
                avg_rho = sum(rho_values) / len(rho_values)
                results["spearman_rho"] = {
                    "value": avg_rho,
                    "interpretation": AgreementMetricsService._interpret_correlation(avg_rho),
                }

        # Kendall's W (Coefficient of Concordance)
        if len(raters) >= 2:
            kendall_w = AgreementMetricsService._kendall_w(data, raters, items)
            if kendall_w is not None:
                results["kendall_w"] = {
                    "value": kendall_w,
                    "interpretation": AgreementMetricsService._interpret_kendall_w(kendall_w),
                }

        # MAE and RMSE (against consensus)
        mae, rmse = AgreementMetricsService._mae_rmse(data, raters, items)
        if mae is not None:
            results["mae"] = {
                "value": mae,
                "interpretation": f"Mittlere Abweichung vom Konsens: {mae:.2f}",
            }
        if rmse is not None:
            results["rmse"] = {
                "value": rmse,
                "interpretation": f"RMSE vom Konsens: {rmse:.2f}",
            }

        return results

    @staticmethod
    def _calculate_authenticity_metrics(evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for authenticity (binary) evaluations."""
        return AgreementMetricsService._calculate_categorical_metrics(evaluations)

    @staticmethod
    def _calculate_comparison_metrics(evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for comparison evaluations."""
        return AgreementMetricsService._calculate_categorical_metrics(evaluations)

    @staticmethod
    def _calculate_classification_metrics(evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for classification evaluations."""
        return AgreementMetricsService._calculate_categorical_metrics(evaluations)

    @staticmethod
    def _calculate_categorical_metrics(evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for categorical (nominal) evaluations."""
        data = evaluations["data"]
        raters = evaluations["raters"]
        items = evaluations["items"]

        results = {}

        # Krippendorff's Alpha for nominal data
        alpha = AgreementMetricsService._krippendorff_alpha(data, raters, items, "nominal")
        if alpha is not None:
            results["krippendorff_alpha"] = {
                "value": alpha,
                "interpretation": AgreementMetricsService._interpret_alpha(alpha),
            }

        # Cohen's Kappa (for exactly 2 raters)
        if len(raters) == 2:
            cohens = AgreementMetricsService._cohens_kappa(data, raters[0], raters[1], items)
            if cohens is not None:
                results["cohens_kappa"] = {
                    "value": cohens,
                    "interpretation": AgreementMetricsService._interpret_kappa(cohens),
                }

        # Fleiss' Kappa (for 3+ raters, but also works for 2)
        kappa = AgreementMetricsService._fleiss_kappa(data, raters, items)
        if kappa is not None:
            results["fleiss_kappa"] = {
                "value": kappa,
                "interpretation": AgreementMetricsService._interpret_kappa(kappa),
            }

        # Percent agreement
        percent = AgreementMetricsService._percent_agreement(data, raters, items)
        if percent is not None:
            results["percent_agreement"] = {
                "value": percent,
                "interpretation": f"{percent:.1f}% der Bewertungen stimmen überein",
            }

        return results

    # ==========================================================================
    # Metric Implementations
    # ==========================================================================

    @staticmethod
    def _krippendorff_alpha(
        data: Dict[int, Dict[str, Any]],
        raters: List[str],
        items: List[int],
        level: str = "ordinal",
    ) -> Optional[float]:
        """
        Calculate Krippendorff's Alpha.

        Simplified implementation for ordinal and nominal data.
        """
        # Build reliability matrix
        values_list = []
        for item in items:
            item_values = []
            for rater in raters:
                val = data.get(item, {}).get(rater)
                if val is not None:
                    try:
                        item_values.append(float(val))
                    except (ValueError, TypeError):
                        item_values.append(val)
            if len(item_values) >= 2:
                values_list.append(item_values)

        if len(values_list) < 2:
            return None

        # Calculate observed disagreement
        all_pairs = []
        for item_values in values_list:
            for i, v1 in enumerate(item_values):
                for v2 in item_values[i + 1:]:
                    all_pairs.append((v1, v2))

        if not all_pairs:
            return None

        # Calculate Do (observed disagreement)
        do_sum = 0
        for v1, v2 in all_pairs:
            if level == "nominal":
                do_sum += 0 if v1 == v2 else 1
            else:  # ordinal/interval
                try:
                    do_sum += (float(v1) - float(v2)) ** 2
                except (ValueError, TypeError):
                    do_sum += 0 if v1 == v2 else 1

        do = do_sum / len(all_pairs) if all_pairs else 0

        # Calculate De (expected disagreement)
        all_values = []
        for item_values in values_list:
            all_values.extend(item_values)

        de_sum = 0
        pair_count = 0
        for i, v1 in enumerate(all_values):
            for v2 in all_values[i + 1:]:
                if level == "nominal":
                    de_sum += 0 if v1 == v2 else 1
                else:
                    try:
                        de_sum += (float(v1) - float(v2)) ** 2
                    except (ValueError, TypeError):
                        de_sum += 0 if v1 == v2 else 1
                pair_count += 1

        de = de_sum / pair_count if pair_count > 0 else 1

        # Calculate alpha
        if de == 0:
            return 1.0 if do == 0 else None

        alpha = 1 - (do / de)
        return round(alpha, 4)

    @staticmethod
    def _cohens_kappa(
        data: Dict[int, Dict[str, Any]],
        rater1: str,
        rater2: str,
        items: List[int],
    ) -> Optional[float]:
        """Calculate Cohen's Kappa for two raters."""
        # Get paired ratings
        pairs = []
        for item in items:
            v1 = data.get(item, {}).get(rater1)
            v2 = data.get(item, {}).get(rater2)
            if v1 is not None and v2 is not None:
                pairs.append((v1, v2))

        if len(pairs) < 2:
            return None

        # Calculate observed agreement
        po = sum(1 for v1, v2 in pairs if v1 == v2) / len(pairs)

        # Calculate expected agreement
        categories = set(v for pair in pairs for v in pair)
        pe = 0
        for cat in categories:
            p1 = sum(1 for v1, _ in pairs if v1 == cat) / len(pairs)
            p2 = sum(1 for _, v2 in pairs if v2 == cat) / len(pairs)
            pe += p1 * p2

        if pe == 1:
            return 1.0 if po == 1 else None

        kappa = (po - pe) / (1 - pe)
        return round(kappa, 4)

    @staticmethod
    def _fleiss_kappa(
        data: Dict[int, Dict[str, Any]],
        raters: List[str],
        items: List[int],
    ) -> Optional[float]:
        """Calculate Fleiss' Kappa for multiple raters."""
        # Build matrix: items x categories
        categories = set()
        for item in items:
            for rater in raters:
                val = data.get(item, {}).get(rater)
                if val is not None:
                    categories.add(val)

        categories = sorted(categories, key=str)
        if len(categories) < 2:
            return None

        n_items = 0
        n_raters_per_item = []
        category_counts = {cat: [] for cat in categories}

        for item in items:
            item_ratings = []
            for rater in raters:
                val = data.get(item, {}).get(rater)
                if val is not None:
                    item_ratings.append(val)

            if len(item_ratings) >= 2:
                n_items += 1
                n_raters_per_item.append(len(item_ratings))
                for cat in categories:
                    count = sum(1 for v in item_ratings if v == cat)
                    category_counts[cat].append(count)

        if n_items < 2:
            return None

        n = sum(n_raters_per_item) / n_items  # Average raters per item

        # Calculate P_bar (mean of P_i)
        p_values = []
        for i in range(n_items):
            n_i = n_raters_per_item[i]
            if n_i < 2:
                continue
            sum_nij_sq = sum(category_counts[cat][i] ** 2 for cat in categories)
            p_i = (sum_nij_sq - n_i) / (n_i * (n_i - 1))
            p_values.append(p_i)

        if not p_values:
            return None

        p_bar = sum(p_values) / len(p_values)

        # Calculate P_e (expected agreement)
        p_j_values = []
        for cat in categories:
            total = sum(category_counts[cat])
            p_j = total / (n_items * n)
            p_j_values.append(p_j ** 2)

        p_e = sum(p_j_values)

        if p_e == 1:
            return 1.0 if p_bar == 1 else None

        kappa = (p_bar - p_e) / (1 - p_e)
        return round(kappa, 4)

    @staticmethod
    def _fleiss_kappa_for_buckets(
        data: Dict[int, Dict[str, Any]],
        raters: List[str],
        items: List[int],
    ) -> Optional[float]:
        """Calculate Fleiss' Kappa for bucket-based rankings."""
        # Flatten bucket assignments to per-feature ratings
        categories = ["gut", "mittel", "schlecht", "neutral"]

        # For each item, aggregate bucket assignments
        aggregated = {}
        for item in items:
            item_cats = []
            for rater in raters:
                buckets = data.get(item, {}).get(rater)
                if isinstance(buckets, dict):
                    # Find the bucket with most items or first non-empty
                    for cat in categories:
                        bucket_data = buckets.get(cat)
                        if bucket_data:
                            if isinstance(bucket_data, dict) and bucket_data.get("feature_ids"):
                                item_cats.append(cat)
                                break
                            elif isinstance(bucket_data, list) and bucket_data:
                                item_cats.append(cat)
                                break
            if item_cats:
                aggregated[item] = item_cats

        if len(aggregated) < 2:
            return None

        # Simplified Fleiss calculation
        total_ratings = sum(len(v) for v in aggregated.values())
        if total_ratings < 4:
            return None

        # Count category frequencies
        cat_counts = {cat: 0 for cat in categories}
        for item_cats in aggregated.values():
            for cat in item_cats:
                cat_counts[cat] += 1

        # Calculate expected agreement
        p_e = sum((count / total_ratings) ** 2 for count in cat_counts.values())

        # Calculate observed agreement (simplified)
        agreement_count = 0
        for item_cats in aggregated.values():
            if len(item_cats) >= 2 and len(set(item_cats)) == 1:
                agreement_count += 1

        p_o = agreement_count / len(aggregated) if aggregated else 0

        if p_e == 1:
            return 1.0 if p_o == 1 else None

        kappa = (p_o - p_e) / (1 - p_e)
        return round(kappa, 4)

    @staticmethod
    def _spearman_rho(
        data: Dict[int, Dict[str, Any]],
        rater1: str,
        rater2: str,
        items: List[int],
    ) -> Optional[float]:
        """Calculate Spearman's rank correlation."""
        # Get paired numeric values
        pairs = []
        for item in items:
            v1 = data.get(item, {}).get(rater1)
            v2 = data.get(item, {}).get(rater2)
            if v1 is not None and v2 is not None:
                try:
                    pairs.append((float(v1), float(v2)))
                except (ValueError, TypeError):
                    continue

        if len(pairs) < 3:
            return None

        # Rank the values
        x_vals = [p[0] for p in pairs]
        y_vals = [p[1] for p in pairs]

        x_ranks = AgreementMetricsService._rank_values(x_vals)
        y_ranks = AgreementMetricsService._rank_values(y_vals)

        # Calculate correlation
        n = len(pairs)
        d_squared_sum = sum((x_ranks[i] - y_ranks[i]) ** 2 for i in range(n))

        rho = 1 - (6 * d_squared_sum) / (n * (n ** 2 - 1))
        return round(rho, 4)

    @staticmethod
    def _kendall_tau_for_buckets(
        data: Dict[int, Dict[str, Any]],
        rater1: str,
        rater2: str,
        items: List[int],
    ) -> Optional[float]:
        """Calculate Kendall's Tau for bucket assignments."""
        # Convert buckets to numeric values
        bucket_values = {"gut": 4, "mittel": 3, "schlecht": 1, "neutral": 2}

        pairs = []
        for item in items:
            b1 = data.get(item, {}).get(rater1)
            b2 = data.get(item, {}).get(rater2)

            if isinstance(b1, dict) and isinstance(b2, dict):
                # Find dominant bucket for each rater
                v1 = AgreementMetricsService._get_dominant_bucket(b1, bucket_values)
                v2 = AgreementMetricsService._get_dominant_bucket(b2, bucket_values)
                if v1 is not None and v2 is not None:
                    pairs.append((v1, v2))

        if len(pairs) < 3:
            return None

        # Calculate Kendall's Tau
        concordant = 0
        discordant = 0

        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                x_diff = pairs[i][0] - pairs[j][0]
                y_diff = pairs[i][1] - pairs[j][1]

                if x_diff * y_diff > 0:
                    concordant += 1
                elif x_diff * y_diff < 0:
                    discordant += 1

        total = concordant + discordant
        if total == 0:
            return None

        tau = (concordant - discordant) / total
        return round(tau, 4)

    @staticmethod
    def _get_dominant_bucket(
        buckets: Dict[str, Any],
        bucket_values: Dict[str, int],
    ) -> Optional[int]:
        """Get the numeric value for the dominant bucket."""
        max_count = 0
        dominant = None

        for bucket, data in buckets.items():
            if bucket not in bucket_values:
                continue
            count = 0
            if isinstance(data, dict):
                count = len(data.get("feature_ids", []))
            elif isinstance(data, list):
                count = len(data)

            if count > max_count:
                max_count = count
                dominant = bucket

        return bucket_values.get(dominant) if dominant else None

    @staticmethod
    def _percent_agreement(
        data: Dict[int, Dict[str, Any]],
        raters: List[str],
        items: List[int],
    ) -> Optional[float]:
        """Calculate simple percent agreement."""
        total_comparisons = 0
        agreements = 0

        for item in items:
            item_values = []
            for rater in raters:
                val = data.get(item, {}).get(rater)
                if val is not None:
                    item_values.append(val)

            if len(item_values) >= 2:
                # Check pairwise agreement
                for i, v1 in enumerate(item_values):
                    for v2 in item_values[i + 1:]:
                        total_comparisons += 1
                        if v1 == v2:
                            agreements += 1

        if total_comparisons == 0:
            return None

        return round((agreements / total_comparisons) * 100, 2)

    @staticmethod
    def _rank_values(values: List[float]) -> List[float]:
        """Convert values to ranks (handling ties)."""
        sorted_pairs = sorted(enumerate(values), key=lambda x: x[1])
        ranks = [0.0] * len(values)

        i = 0
        while i < len(sorted_pairs):
            j = i
            # Find all tied values
            while j < len(sorted_pairs) and sorted_pairs[j][1] == sorted_pairs[i][1]:
                j += 1

            # Assign average rank to ties
            avg_rank = (i + j + 1) / 2
            for k in range(i, j):
                ranks[sorted_pairs[k][0]] = avg_rank

            i = j

        return ranks

    # ==========================================================================
    # Interpretation Helpers
    # ==========================================================================

    @staticmethod
    def _interpret_alpha(value: float) -> str:
        """Interpret Krippendorff's Alpha value."""
        if value >= 0.8:
            return "Zuverlässige Übereinstimmung (reliable)"
        elif value >= 0.667:
            return "Ausreichende Übereinstimmung (tentative)"
        elif value >= 0.4:
            return "Moderate Übereinstimmung"
        elif value > 0:
            return "Geringe Übereinstimmung"
        else:
            return "Keine oder negative Übereinstimmung"

    @staticmethod
    def _interpret_kappa(value: float) -> str:
        """Interpret Cohen's/Fleiss' Kappa value."""
        if value >= 0.81:
            return "Fast perfekte Übereinstimmung (almost perfect)"
        elif value >= 0.61:
            return "Substanzielle Übereinstimmung (substantial)"
        elif value >= 0.41:
            return "Moderate Übereinstimmung (moderate)"
        elif value >= 0.21:
            return "Ausreichende Übereinstimmung (fair)"
        elif value > 0:
            return "Geringe Übereinstimmung (slight)"
        else:
            return "Keine Übereinstimmung (poor)"

    @staticmethod
    def _interpret_correlation(value: float) -> str:
        """Interpret correlation coefficient (Kendall/Spearman)."""
        abs_val = abs(value)
        direction = "positive" if value >= 0 else "negative"

        if abs_val >= 0.8:
            strength = "Sehr starke"
        elif abs_val >= 0.6:
            strength = "Starke"
        elif abs_val >= 0.4:
            strength = "Moderate"
        elif abs_val >= 0.2:
            strength = "Schwache"
        else:
            strength = "Sehr schwache"

        return f"{strength} {direction} Korrelation"

    @staticmethod
    def _interpret_icc(value: float) -> str:
        """Interpret ICC value."""
        if value >= 0.90:
            return "Exzellente Reliabilität (excellent)"
        elif value >= 0.75:
            return "Gute Reliabilität (good)"
        elif value >= 0.50:
            return "Moderate Reliabilität (moderate)"
        else:
            return "Geringe Reliabilität (poor)"

    @staticmethod
    def _interpret_kendall_w(value: float) -> str:
        """Interpret Kendall's W value."""
        if value >= 0.9:
            return "Sehr hohe Übereinstimmung"
        elif value >= 0.7:
            return "Hohe Übereinstimmung"
        elif value >= 0.5:
            return "Moderate Übereinstimmung"
        elif value >= 0.3:
            return "Schwache Übereinstimmung"
        else:
            return "Sehr schwache Übereinstimmung"

    # ==========================================================================
    # New Metric Implementations
    # ==========================================================================

    @staticmethod
    def _icc(
        data: Dict[int, Dict[str, Any]],
        raters: List[str],
        items: List[int],
    ) -> Optional[float]:
        """
        Calculate ICC(2,1) - Two-way random effects, single measures.

        This is appropriate when raters are a random sample and each rater
        rates all items.
        """
        if len(raters) < 2 or len(items) < 2:
            return None

        # Build ratings matrix: items x raters
        ratings = []
        valid_items = []
        for item in items:
            item_ratings = []
            all_valid = True
            for rater in raters:
                val = data.get(item, {}).get(rater)
                if val is not None:
                    try:
                        item_ratings.append(float(val))
                    except (ValueError, TypeError):
                        all_valid = False
                        break
                else:
                    all_valid = False
                    break

            if all_valid and len(item_ratings) == len(raters):
                ratings.append(item_ratings)
                valid_items.append(item)

        n = len(ratings)  # Number of items
        k = len(raters)   # Number of raters

        if n < 2:
            return None

        # Calculate means
        grand_mean = sum(sum(row) for row in ratings) / (n * k)
        item_means = [sum(row) / k for row in ratings]
        rater_means = [sum(ratings[i][j] for i in range(n)) / n for j in range(k)]

        # Calculate sum of squares
        ss_total = sum(
            (ratings[i][j] - grand_mean) ** 2
            for i in range(n)
            for j in range(k)
        )

        ss_between_items = k * sum((m - grand_mean) ** 2 for m in item_means)
        ss_between_raters = n * sum((m - grand_mean) ** 2 for m in rater_means)
        ss_error = ss_total - ss_between_items - ss_between_raters

        # Mean squares
        ms_between_items = ss_between_items / (n - 1) if n > 1 else 0
        ms_error = ss_error / ((n - 1) * (k - 1)) if (n > 1 and k > 1) else 0
        ms_between_raters = ss_between_raters / (k - 1) if k > 1 else 0

        # ICC(2,1) formula
        denominator = ms_between_items + (k - 1) * ms_error + (k / n) * (ms_between_raters - ms_error)
        if denominator == 0:
            return None

        icc = (ms_between_items - ms_error) / denominator
        return round(max(0, min(1, icc)), 4)  # Clamp to [0, 1]

    @staticmethod
    def _kendall_w(
        data: Dict[int, Dict[str, Any]],
        raters: List[str],
        items: List[int],
    ) -> Optional[float]:
        """
        Calculate Kendall's W (Coefficient of Concordance).

        Measures agreement among multiple raters when ranking items.
        """
        if len(raters) < 2 or len(items) < 2:
            return None

        # Build rank matrix
        # For each rater, rank the items by their rating values
        rank_matrix = []  # raters x items

        for rater in raters:
            rater_values = []
            for item in items:
                val = data.get(item, {}).get(rater)
                if val is not None:
                    try:
                        rater_values.append((item, float(val)))
                    except (ValueError, TypeError):
                        return None
                else:
                    return None

            # Rank the values for this rater
            sorted_items = sorted(rater_values, key=lambda x: x[1])
            item_ranks = {item: 0.0 for item, _ in rater_values}

            i = 0
            while i < len(sorted_items):
                j = i
                while j < len(sorted_items) and sorted_items[j][1] == sorted_items[i][1]:
                    j += 1
                avg_rank = (i + j + 1) / 2
                for k in range(i, j):
                    item_ranks[sorted_items[k][0]] = avg_rank
                i = j

            rank_matrix.append([item_ranks[item] for item in items])

        n = len(items)
        m = len(raters)

        # Calculate rank sums for each item
        rank_sums = [sum(rank_matrix[r][i] for r in range(m)) for i in range(n)]
        mean_rank_sum = sum(rank_sums) / n

        # Calculate S (sum of squared deviations)
        s = sum((rs - mean_rank_sum) ** 2 for rs in rank_sums)

        # Calculate W
        # W = 12 * S / (m^2 * (n^3 - n))
        denominator = m ** 2 * (n ** 3 - n)
        if denominator == 0:
            return None

        w = (12 * s) / denominator
        return round(max(0, min(1, w)), 4)  # Clamp to [0, 1]

    @staticmethod
    def _mae_rmse(
        data: Dict[int, Dict[str, Any]],
        raters: List[str],
        items: List[int],
        ground_truth: Optional[Dict[int, float]] = None,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate MAE and RMSE against ground truth or consensus.

        If no ground_truth provided, uses mean of all raters as reference.
        """
        if len(raters) < 1 or len(items) < 1:
            return None, None

        errors = []

        for item in items:
            # Get all ratings for this item
            item_ratings = []
            for rater in raters:
                val = data.get(item, {}).get(rater)
                if val is not None:
                    try:
                        item_ratings.append(float(val))
                    except (ValueError, TypeError):
                        continue

            if not item_ratings:
                continue

            # Determine reference value
            if ground_truth and item in ground_truth:
                ref = ground_truth[item]
            else:
                # Use mean as consensus
                ref = sum(item_ratings) / len(item_ratings)

            # Calculate errors for each rating
            for rating in item_ratings:
                errors.append(abs(rating - ref))

        if not errors:
            return None, None

        mae = sum(errors) / len(errors)
        rmse = math.sqrt(sum(e ** 2 for e in errors) / len(errors))

        return round(mae, 4), round(rmse, 4)

    @staticmethod
    def _bradley_terry(
        comparisons: List[Tuple[Any, Any, Any]],  # (item_a, item_b, winner)
    ) -> Optional[Dict[Any, float]]:
        """
        Calculate Bradley-Terry scores from pairwise comparisons.

        Uses iterative algorithm to estimate item strengths.
        Returns normalized scores (0-1).
        """
        if not comparisons:
            return None

        # Collect all items
        items = set()
        for a, b, winner in comparisons:
            items.add(a)
            items.add(b)

        items = list(items)
        if len(items) < 2:
            return None

        # Initialize scores (all equal)
        scores = {item: 1.0 for item in items}

        # Count wins and losses for each item
        wins = {item: 0 for item in items}
        total = {item: 0 for item in items}

        for a, b, winner in comparisons:
            total[a] += 1
            total[b] += 1
            if winner == a:
                wins[a] += 1
            elif winner == b:
                wins[b] += 1
            else:  # Tie
                wins[a] += 0.5
                wins[b] += 0.5

        # Iterative estimation (simplified MM algorithm)
        for _ in range(100):  # Max iterations
            new_scores = {}
            for item in items:
                if total[item] == 0:
                    new_scores[item] = scores[item]
                    continue

                # Sum of 1/(p_i + p_j) for all comparisons involving item
                denominator = 0
                for a, b, _ in comparisons:
                    if a == item:
                        denominator += 1 / (scores[item] + scores[b])
                    elif b == item:
                        denominator += 1 / (scores[a] + scores[item])

                if denominator > 0:
                    new_scores[item] = wins[item] / denominator
                else:
                    new_scores[item] = scores[item]

            # Normalize
            total_score = sum(new_scores.values())
            if total_score > 0:
                new_scores = {k: v / total_score for k, v in new_scores.items()}

            # Check convergence
            max_diff = max(abs(new_scores[i] - scores[i]) for i in items)
            scores = new_scores
            if max_diff < 0.0001:
                break

        return {k: round(v, 4) for k, v in scores.items()}

    @staticmethod
    def _f1_scores(
        data: Dict[int, Dict[str, Any]],
        raters: List[str],
        items: List[int],
        ground_truth: Optional[Dict[int, str]] = None,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate Macro and Micro F1 scores.

        Requires ground truth labels.
        Returns (macro_f1, micro_f1).
        """
        if not ground_truth or not raters or not items:
            return None, None

        # Collect all classes
        classes = set(ground_truth.values())
        for item in items:
            for rater in raters:
                val = data.get(item, {}).get(rater)
                if val is not None:
                    classes.add(str(val))

        classes = list(classes)
        if len(classes) < 2:
            return None, None

        # Initialize confusion counts per class
        class_stats = {
            c: {"tp": 0, "fp": 0, "fn": 0}
            for c in classes
        }

        # Count predictions vs ground truth
        for item in items:
            true_label = ground_truth.get(item)
            if true_label is None:
                continue

            for rater in raters:
                pred = data.get(item, {}).get(rater)
                if pred is None:
                    continue
                pred = str(pred)

                for c in classes:
                    if pred == c and true_label == c:
                        class_stats[c]["tp"] += 1
                    elif pred == c and true_label != c:
                        class_stats[c]["fp"] += 1
                    elif pred != c and true_label == c:
                        class_stats[c]["fn"] += 1

        # Calculate per-class F1
        f1_scores = []
        total_tp = 0
        total_fp = 0
        total_fn = 0

        for c in classes:
            tp = class_stats[c]["tp"]
            fp = class_stats[c]["fp"]
            fn = class_stats[c]["fn"]

            total_tp += tp
            total_fp += fp
            total_fn += fn

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            f1_scores.append(f1)

        # Macro F1 (average of per-class F1)
        macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else None

        # Micro F1 (from total counts)
        micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        micro_f1 = (
            2 * micro_precision * micro_recall / (micro_precision + micro_recall)
            if (micro_precision + micro_recall) > 0 else None
        )

        return (
            round(macro_f1, 4) if macro_f1 is not None else None,
            round(micro_f1, 4) if micro_f1 is not None else None
        )
