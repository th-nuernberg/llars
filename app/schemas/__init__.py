"""
LLARS Pydantic Schemas

Structured output schemas for LLM evaluators and API validation.
"""

from schemas.evaluation_schemas import (
    # Base
    EvaluatorMeta,
    BaseEvaluationResult,
    # Ranking
    BucketReasoning,
    RankingEvaluationResult,
    # Rating
    FeatureRating,
    RatingEvaluationResult,
    # Authenticity
    AuthenticityIndicator,
    AuthenticityEvaluationResult,
    # Mail Rating
    QualityCriterion,
    MailRatingEvaluationResult,
    # Comparison
    ComparisonEvaluationResult,
    # Classification
    ClassificationEvaluationResult,
    # Helper
    get_schema_for_task_type,
    TASK_TYPE_SCHEMAS,
)

__all__ = [
    # Base
    "EvaluatorMeta",
    "BaseEvaluationResult",
    # Ranking
    "BucketReasoning",
    "RankingEvaluationResult",
    # Rating
    "FeatureRating",
    "RatingEvaluationResult",
    # Authenticity
    "AuthenticityIndicator",
    "AuthenticityEvaluationResult",
    # Mail Rating
    "QualityCriterion",
    "MailRatingEvaluationResult",
    # Comparison
    "ComparisonEvaluationResult",
    # Classification
    "ClassificationEvaluationResult",
    # Helper
    "get_schema_for_task_type",
    "TASK_TYPE_SCHEMAS",
]
