"""
Tests for Pydantic evaluation schemas.

These tests verify that the structured output schemas correctly
validate LLM responses for all task types.
"""

import pytest
from pydantic import ValidationError


class TestRankingEvaluationResult:
    """Tests for RankingEvaluationResult schema."""

    def test_EVAL_001_valid_ranking_result(self):
        """Valid ranking result should pass validation."""
        from schemas.evaluation_schemas import RankingEvaluationResult

        data = {
            "buckets": {
                "gut": {"feature_ids": [1, 3], "reasoning": "Precise and relevant analysis."},
                "mittel": {"feature_ids": [2, 5], "reasoning": "Usable but needs improvement."},
                "schlecht": {"feature_ids": [4], "reasoning": "Superficial without value."},
                "neutral": {"feature_ids": [], "reasoning": "No features in this category."}
            },
            "overall_assessment": "The majority of features show good quality with room for improvement.",
            "reasoning": "The evaluation is based on precision, relevance, and clarity of the features.",
            "confidence": 0.85
        }

        result = RankingEvaluationResult.model_validate(data)
        assert result.confidence == 0.85
        assert result.buckets["gut"].feature_ids == [1, 3]
        assert len(result.get_all_feature_ids()) == 5

    def test_EVAL_002_missing_bucket_fails(self):
        """Missing bucket should fail validation."""
        from schemas.evaluation_schemas import RankingEvaluationResult

        data = {
            "buckets": {
                "gut": {"feature_ids": [1], "reasoning": "Good features."},
                "mittel": {"feature_ids": [], "reasoning": "None."},
                # Missing "schlecht" and "neutral"
            },
            "overall_assessment": "Assessment text here for testing purposes.",
            "reasoning": "Detailed reasoning for the evaluation decision.",
            "confidence": 0.7
        }

        with pytest.raises(ValidationError) as exc_info:
            RankingEvaluationResult.model_validate(data)

        assert "Missing buckets" in str(exc_info.value) or "buckets" in str(exc_info.value)

    def test_EVAL_003_to_legacy_format(self):
        """Legacy format conversion should work."""
        from schemas.evaluation_schemas import RankingEvaluationResult

        data = {
            "buckets": {
                "gut": {"feature_ids": [1], "reasoning": "Good quality feature with clear analysis."},
                "mittel": {"feature_ids": [2], "reasoning": "Medium quality feature needs work."},
                "schlecht": {"feature_ids": [3], "reasoning": "Bad quality feature is superficial."},
                "neutral": {"feature_ids": [4], "reasoning": "Neutral feature not categorizable."}
            },
            "overall_assessment": "Overall assessment text for the evaluation.",
            "reasoning": "Detailed reasoning about the evaluation process.",
            "confidence": 0.8
        }

        result = RankingEvaluationResult.model_validate(data)
        legacy = result.to_legacy_format()

        assert legacy == {"gut": [1], "mittel": [2], "schlecht": [3], "neutral": [4]}


class TestRatingEvaluationResult:
    """Tests for RatingEvaluationResult schema."""

    def test_EVAL_004_valid_rating_result(self):
        """Valid rating result should pass validation."""
        from schemas.evaluation_schemas import RatingEvaluationResult

        data = {
            "ratings": [
                {
                    "feature_id": 1,
                    "rating": 4,
                    "reasoning": "Clear and concise analysis of client needs.",
                    "strengths": ["Well formulated", "Relevant"],
                    "weaknesses": ["Could be more detailed"]
                },
                {
                    "feature_id": 2,
                    "rating": 3,
                    "reasoning": "Acceptable but lacks depth.",
                }
            ],
            "average_rating": 3.5,
            "thread_summary": "Consultation about loan application with follow-up questions.",
            "reasoning": "Features show generally good quality with room for improvement.",
            "confidence": 0.8
        }

        result = RatingEvaluationResult.model_validate(data)
        assert result.average_rating == 3.5
        assert len(result.ratings) == 2
        assert result.ratings[0].rating == 4

    def test_EVAL_005_invalid_rating_range(self):
        """Rating outside 1-5 range should fail."""
        from schemas.evaluation_schemas import RatingEvaluationResult

        data = {
            "ratings": [
                {
                    "feature_id": 1,
                    "rating": 6,  # Invalid: > 5
                    "reasoning": "This rating is too high."
                }
            ],
            "average_rating": 6.0,  # Also invalid
            "thread_summary": "Thread summary text here.",
            "reasoning": "Reasoning text here for the evaluation.",
            "confidence": 0.5
        }

        with pytest.raises(ValidationError):
            RatingEvaluationResult.model_validate(data)


class TestAuthenticityEvaluationResult:
    """Tests for AuthenticityEvaluationResult schema."""

    def test_EVAL_006_valid_authenticity_result(self):
        """Valid authenticity result should pass validation."""
        from schemas.evaluation_schemas import AuthenticityEvaluationResult

        data = {
            "vote": "fake",
            "confidence_score": 4,
            "indicators": [
                {"indicator": "Unnaturally consistent style", "supports": "fake", "weight": 0.8},
                {"indicator": "No typos", "supports": "fake", "weight": 0.6}
            ],
            "linguistic_analysis": "The text shows unusually perfect grammar and sentence structure throughout.",
            "behavioral_analysis": "The client's behavior appears too linear and predictable for natural conversation.",
            "reasoning": "Multiple indicators suggest AI generation including perfect grammar.",
            "confidence": 0.75
        }

        result = AuthenticityEvaluationResult.model_validate(data)
        assert result.vote == "fake"
        assert result.confidence_score == 4
        assert len(result.indicators) == 2

    def test_EVAL_007_invalid_vote_value(self):
        """Invalid vote value should fail."""
        from schemas.evaluation_schemas import AuthenticityEvaluationResult

        data = {
            "vote": "maybe",  # Invalid: must be "real" or "fake"
            "confidence_score": 3,
            "indicators": [
                {"indicator": "Test", "supports": "real", "weight": 0.5}
            ],
            "linguistic_analysis": "Analysis text here for linguistic patterns.",
            "behavioral_analysis": "Analysis text here for behavioral patterns.",
            "reasoning": "Reasoning text here for the decision.",
            "confidence": 0.5
        }

        with pytest.raises(ValidationError):
            AuthenticityEvaluationResult.model_validate(data)


class TestMailRatingEvaluationResult:
    """Tests for MailRatingEvaluationResult schema."""

    def test_EVAL_008_valid_mail_rating_result(self):
        """Valid mail rating result should pass validation."""
        from schemas.evaluation_schemas import MailRatingEvaluationResult

        data = {
            "overall_rating": 4,
            "criteria": [
                {"name": "Empathy", "score": 5, "reasoning": "Very empathetic responses."},
                {"name": "Expertise", "score": 4, "reasoning": "Competent advice."},
                {"name": "Clarity", "score": 4, "reasoning": "Clear communication."}
            ],
            "strengths": ["Empathetic communication", "Professional expertise"],
            "areas_for_improvement": ["More concrete recommendations"],
            "summary": "Overall good consultation with strengths in empathy and expertise.",
            "reasoning": "The evaluation is based on multiple quality dimensions.",
            "confidence": 0.85
        }

        result = MailRatingEvaluationResult.model_validate(data)
        assert result.overall_rating == 4
        assert len(result.criteria) == 3
        assert result.strengths[0] == "Empathetic communication"


class TestComparisonEvaluationResult:
    """Tests for ComparisonEvaluationResult schema."""

    def test_EVAL_009_valid_comparison_result(self):
        """Valid comparison result should pass validation."""
        from schemas.evaluation_schemas import ComparisonEvaluationResult

        data = {
            "winner": "A",
            "confidence_score": 4,
            "comparison_aspects": [
                {"aspect": "Clarity", "winner": "A", "reasoning": "Text A is clearer."},
                {"aspect": "Completeness", "winner": "B", "reasoning": "Text B is more complete."}
            ],
            "reasoning": "Text A wins due to better overall clarity and structure.",
            "confidence": 0.8
        }

        result = ComparisonEvaluationResult.model_validate(data)
        assert result.winner == "A"
        assert result.confidence_score == 4

    def test_EVAL_010_tie_result(self):
        """TIE result should be valid."""
        from schemas.evaluation_schemas import ComparisonEvaluationResult

        data = {
            "winner": "TIE",
            "confidence_score": 5,
            "reasoning": "Both texts are equally good in quality and clarity.",
            "confidence": 0.9
        }

        result = ComparisonEvaluationResult.model_validate(data)
        assert result.winner == "TIE"


class TestClassificationEvaluationResult:
    """Tests for ClassificationEvaluationResult schema."""

    def test_EVAL_011_valid_classification_result(self):
        """Valid classification result should pass validation."""
        from schemas.evaluation_schemas import ClassificationEvaluationResult

        data = {
            "label": "complaint",
            "confidence_score": 4,
            "alternative_labels": [
                {"label": "inquiry", "probability": 0.2},
                {"label": "feedback", "probability": 0.1}
            ],
            "key_phrases": ["dissatisfied", "complaint", "unacceptable"],
            "reasoning": "The text contains clear complaint indicators.",
            "confidence": 0.8
        }

        result = ClassificationEvaluationResult.model_validate(data)
        assert result.label == "complaint"
        assert len(result.key_phrases) == 3


class TestGetSchemaForTaskType:
    """Tests for the schema registry function."""

    def test_EVAL_012_get_ranking_schema(self):
        """Should return RankingEvaluationResult for ranking task."""
        from schemas.evaluation_schemas import get_schema_for_task_type, RankingEvaluationResult

        schema = get_schema_for_task_type("ranking")
        assert schema == RankingEvaluationResult

    def test_EVAL_013_get_rating_schema(self):
        """Should return RatingEvaluationResult for rating task."""
        from schemas.evaluation_schemas import get_schema_for_task_type, RatingEvaluationResult

        schema = get_schema_for_task_type("rating")
        assert schema == RatingEvaluationResult

    def test_EVAL_014_get_authenticity_schema(self):
        """Should return AuthenticityEvaluationResult for authenticity task."""
        from schemas.evaluation_schemas import get_schema_for_task_type, AuthenticityEvaluationResult

        schema = get_schema_for_task_type("authenticity")
        assert schema == AuthenticityEvaluationResult

    def test_EVAL_015_unknown_task_type_raises(self):
        """Unknown task type should raise ValueError."""
        from schemas.evaluation_schemas import get_schema_for_task_type

        with pytest.raises(ValueError) as exc_info:
            get_schema_for_task_type("unknown_type")

        assert "Unknown task type" in str(exc_info.value)

    def test_EVAL_016_all_task_types_have_schemas(self):
        """All defined task types should have schemas."""
        from schemas.evaluation_schemas import TASK_TYPE_SCHEMAS, get_schema_for_task_type

        for task_type in TASK_TYPE_SCHEMAS.keys():
            schema = get_schema_for_task_type(task_type)
            assert schema is not None
