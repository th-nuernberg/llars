"""
Pydantic Schemas for LLM Evaluator Structured Outputs.

These schemas define the expected output format for each evaluation task type.
They enable:
1. Constrained Decoding - LLM must produce valid JSON matching the schema
2. Validation - Responses are validated before storage
3. Transparency - Structured reasoning is captured for analysis

Usage:
    from schemas.evaluation_schemas import RankingEvaluationResult, get_schema_for_task_type

    # Get schema for a task type
    schema = get_schema_for_task_type("ranking")

    # Validate LLM response
    result = RankingEvaluationResult.model_validate(llm_response)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Optional, Dict, Any, Type
from enum import Enum


# =============================================================================
# Base Schemas
# =============================================================================

class EvaluatorMeta(BaseModel):
    """Metadata for LLM evaluations."""
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    model_version: Optional[str] = Field(None, description="Model version used")
    prompt_version: Optional[str] = Field(None, description="Prompt template version")
    input_tokens: Optional[int] = Field(None, description="Input token count")
    output_tokens: Optional[int] = Field(None, description="Output token count")


class BaseEvaluationResult(BaseModel):
    """Base schema for all evaluation results."""

    reasoning: str = Field(
        min_length=20,
        max_length=2000,
        description="Detailed reasoning for the evaluation decision"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0=very uncertain, 1=very certain)"
    )
    meta: Optional[EvaluatorMeta] = Field(None, description="Evaluation metadata")

    class Config:
        extra = "allow"  # Allow additional fields for forward compatibility


# =============================================================================
# Ranking Schema
# =============================================================================

class BucketReasoning(BaseModel):
    """Reasoning for a single bucket in ranking."""

    feature_ids: List[int] = Field(
        description="List of feature IDs assigned to this bucket"
    )
    reasoning: str = Field(
        min_length=10,
        max_length=500,
        description="Why these features belong in this bucket"
    )


class RankingEvaluationResult(BaseEvaluationResult):
    """
    Structured ranking result.

    Features are categorized into quality buckets:
    - gut (good): High-quality features
    - mittel (medium): Acceptable features
    - schlecht (bad): Low-quality features
    - neutral: Not clearly categorizable
    """

    buckets: Dict[Literal["gut", "mittel", "schlecht", "neutral"], BucketReasoning] = Field(
        description="Bucket assignments with reasoning"
    )
    overall_assessment: str = Field(
        min_length=30,
        max_length=500,
        description="Overall assessment of feature quality for this thread"
    )

    @field_validator("buckets")
    @classmethod
    def validate_all_buckets_present(cls, v):
        """Ensure all four buckets are present."""
        required = {"gut", "mittel", "schlecht", "neutral"}
        if set(v.keys()) != required:
            missing = required - set(v.keys())
            raise ValueError(f"Missing buckets: {missing}")
        return v

    def get_all_feature_ids(self) -> List[int]:
        """Get all feature IDs across all buckets."""
        ids = []
        for bucket in self.buckets.values():
            ids.extend(bucket.feature_ids)
        return ids

    def to_legacy_format(self) -> Dict[str, List[int]]:
        """Convert to legacy bucket format for backward compatibility."""
        return {k: v.feature_ids for k, v in self.buckets.items()}

    class Config:
        json_schema_extra = {
            "example": {
                "buckets": {
                    "gut": {"feature_ids": [1, 3], "reasoning": "Precise and relevant analysis."},
                    "mittel": {"feature_ids": [2, 5], "reasoning": "Usable but could be improved."},
                    "schlecht": {"feature_ids": [4], "reasoning": "Superficial without added value."},
                    "neutral": {"feature_ids": [], "reasoning": "No features in this category."}
                },
                "overall_assessment": "The majority of features show good quality...",
                "reasoning": "The evaluation is based on precision, relevance, and clarity...",
                "confidence": 0.85
            }
        }


# =============================================================================
# Rating Schema
# =============================================================================

class FeatureRating(BaseModel):
    """Rating for a single feature."""

    feature_id: int = Field(description="ID of the rated feature")
    rating: int = Field(ge=1, le=5, description="Rating from 1 (poor) to 5 (excellent)")
    reasoning: str = Field(
        min_length=10,
        max_length=300,
        description="Explanation for this rating"
    )
    strengths: Optional[List[str]] = Field(None, max_length=5, description="Feature strengths")
    weaknesses: Optional[List[str]] = Field(None, max_length=5, description="Feature weaknesses")


class RatingEvaluationResult(BaseEvaluationResult):
    """
    Structured rating result.

    Each feature is rated on a 1-5 scale with detailed reasoning.
    """

    ratings: List[FeatureRating] = Field(
        min_length=1,
        description="Ratings for each feature"
    )
    average_rating: float = Field(
        ge=1.0,
        le=5.0,
        description="Average rating across all features"
    )
    thread_summary: str = Field(
        min_length=20,
        max_length=500,
        description="Summary of the conversation context"
    )

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility."""
        return {
            "ratings": [
                {"feature_id": r.feature_id, "rating": r.rating}
                for r in self.ratings
            ]
        }

    class Config:
        json_schema_extra = {
            "example": {
                "ratings": [
                    {
                        "feature_id": 1,
                        "rating": 4,
                        "reasoning": "Clear and concise analysis of client needs.",
                        "strengths": ["Well formulated", "Relevant"],
                        "weaknesses": ["Could be more detailed"]
                    }
                ],
                "average_rating": 3.8,
                "thread_summary": "Consultation about loan application...",
                "reasoning": "Features show generally good quality...",
                "confidence": 0.8
            }
        }


# =============================================================================
# Authenticity Schema
# =============================================================================

class AuthenticityIndicator(BaseModel):
    """Indicator supporting the authenticity decision."""

    indicator: str = Field(
        min_length=5,
        max_length=200,
        description="Description of the indicator"
    )
    supports: Literal["real", "fake"] = Field(
        description="Which hypothesis this indicator supports"
    )
    weight: float = Field(
        ge=0.0,
        le=1.0,
        description="Importance weight of this indicator"
    )


class AuthenticityEvaluationResult(BaseEvaluationResult):
    """
    Structured authenticity (fake/real) evaluation result.

    Determines whether a conversation is likely human-written or AI-generated.
    """

    vote: Literal["real", "fake"] = Field(
        description="Final decision: real (human) or fake (AI-generated)"
    )
    confidence_score: int = Field(
        ge=1,
        le=5,
        description="Confidence level 1-5 (for UI compatibility)"
    )
    indicators: List[AuthenticityIndicator] = Field(
        min_length=2,
        max_length=10,
        description="Indicators that led to the decision"
    )
    linguistic_analysis: str = Field(
        min_length=30,
        max_length=500,
        description="Analysis of linguistic patterns"
    )
    behavioral_analysis: str = Field(
        min_length=30,
        max_length=500,
        description="Analysis of conversational behavior"
    )

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility."""
        return {
            "vote": self.vote,
            "confidence": self.confidence_score
        }

    class Config:
        json_schema_extra = {
            "example": {
                "vote": "fake",
                "confidence_score": 4,
                "indicators": [
                    {"indicator": "Unnaturally consistent writing style", "supports": "fake", "weight": 0.8},
                    {"indicator": "No typos or corrections", "supports": "fake", "weight": 0.6},
                    {"indicator": "Emotional response seems genuine", "supports": "real", "weight": 0.4}
                ],
                "linguistic_analysis": "The text shows unusually perfect grammar and sentence structure...",
                "behavioral_analysis": "The client's behavior appears too linear and predictable...",
                "reasoning": "Multiple indicators suggest AI generation...",
                "confidence": 0.75
            }
        }


# =============================================================================
# Mail Rating Schema
# =============================================================================

class QualityCriterion(BaseModel):
    """Evaluation of a single quality criterion."""

    name: str = Field(min_length=2, max_length=50, description="Criterion name")
    score: int = Field(ge=1, le=5, description="Score 1-5")
    reasoning: str = Field(
        min_length=10,
        max_length=300,
        description="Explanation for this score"
    )


class MailRatingEvaluationResult(BaseEvaluationResult):
    """
    Structured mail/conversation rating result.

    Evaluates overall quality of an email consultation conversation.
    """

    overall_rating: int = Field(
        ge=1,
        le=5,
        description="Overall rating 1-5"
    )
    criteria: List[QualityCriterion] = Field(
        min_length=3,
        max_length=6,
        description="Ratings for individual criteria"
    )
    strengths: List[str] = Field(
        min_length=1,
        max_length=5,
        description="Identified strengths"
    )
    areas_for_improvement: List[str] = Field(
        default=[],
        max_length=5,
        description="Areas that could be improved"
    )
    summary: str = Field(
        min_length=30,
        max_length=500,
        description="Summary evaluation"
    )

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility."""
        return {
            "rating": self.overall_rating,
            "reasoning": self.summary
        }

    class Config:
        json_schema_extra = {
            "example": {
                "overall_rating": 4,
                "criteria": [
                    {"name": "Empathy", "score": 5, "reasoning": "Very empathetic responses..."},
                    {"name": "Expertise", "score": 4, "reasoning": "Competent advice..."},
                    {"name": "Clarity", "score": 4, "reasoning": "Clear communication..."},
                    {"name": "Helpfulness", "score": 4, "reasoning": "Engaged and supportive..."},
                    {"name": "Solution-orientation", "score": 3, "reasoning": "Could be more concrete..."}
                ],
                "strengths": ["Empathetic communication", "Professional expertise"],
                "areas_for_improvement": ["More concrete action recommendations"],
                "summary": "Overall good consultation with strengths in empathy...",
                "reasoning": "The evaluation is based on multiple quality dimensions...",
                "confidence": 0.85
            }
        }


# =============================================================================
# Comparison Schema
# =============================================================================

class ComparisonEvaluationResult(BaseEvaluationResult):
    """
    Structured comparison result.

    Compares two texts/responses and determines a winner.
    """

    winner: Literal["A", "B", "TIE"] = Field(
        description="Winner: A, B, or TIE (equal quality)"
    )
    confidence_score: int = Field(
        ge=1,
        le=5,
        description="Confidence level 1-5"
    )
    comparison_aspects: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Detailed comparison by aspect"
    )

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility."""
        return {
            "winner": self.winner,
            "confidence": self.confidence_score,
            "reasoning": self.reasoning
        }

    class Config:
        json_schema_extra = {
            "example": {
                "winner": "A",
                "confidence_score": 4,
                "comparison_aspects": [
                    {"aspect": "Clarity", "winner": "A", "reasoning": "Text A is clearer..."},
                    {"aspect": "Completeness", "winner": "B", "reasoning": "Text B is more complete..."}
                ],
                "reasoning": "Text A wins due to better overall clarity and structure...",
                "confidence": 0.8
            }
        }


# =============================================================================
# Classification Schema
# =============================================================================

class ClassificationEvaluationResult(BaseEvaluationResult):
    """
    Structured text classification result.

    Classifies text into predefined categories.
    """

    label: str = Field(
        min_length=1,
        max_length=100,
        description="Assigned label/category"
    )
    confidence_score: int = Field(
        ge=1,
        le=5,
        description="Confidence level 1-5"
    )
    alternative_labels: List[Dict[str, Any]] = Field(
        default=[],
        max_length=3,
        description="Alternative labels with probabilities"
    )
    key_phrases: List[str] = Field(
        min_length=1,
        max_length=5,
        description="Key phrases that led to the classification"
    )

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility."""
        return {
            "label": self.label,
            "confidence": self.confidence_score,
            "reasoning": self.reasoning
        }

    class Config:
        json_schema_extra = {
            "example": {
                "label": "complaint",
                "confidence_score": 4,
                "alternative_labels": [
                    {"label": "inquiry", "probability": 0.2},
                    {"label": "feedback", "probability": 0.1}
                ],
                "key_phrases": ["dissatisfied", "complaint", "unacceptable"],
                "reasoning": "The text contains clear complaint indicators...",
                "confidence": 0.8
            }
        }


# =============================================================================
# Schema Registry
# =============================================================================

TASK_TYPE_SCHEMAS: Dict[str, Type[BaseEvaluationResult]] = {
    "ranking": RankingEvaluationResult,
    "rating": RatingEvaluationResult,
    "authenticity": AuthenticityEvaluationResult,
    "mail_rating": MailRatingEvaluationResult,
    "comparison": ComparisonEvaluationResult,
    "text_classification": ClassificationEvaluationResult,
    "labeling": ClassificationEvaluationResult,
}


def get_schema_for_task_type(task_type: str) -> Type[BaseEvaluationResult]:
    """
    Get the appropriate Pydantic schema for a task type.

    Args:
        task_type: One of: ranking, rating, authenticity, mail_rating, comparison, text_classification, labeling

    Returns:
        The corresponding Pydantic model class

    Raises:
        ValueError: If task_type is not recognized
    """
    schema = TASK_TYPE_SCHEMAS.get(task_type)
    if schema is None:
        raise ValueError(
            f"Unknown task type: {task_type}. "
            f"Supported types: {list(TASK_TYPE_SCHEMAS.keys())}"
        )
    return schema
