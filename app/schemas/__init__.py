"""
LLARS Pydantic Schemas

Contains two types of schemas:
1. LLM Output Schemas (evaluation_schemas.py) - Structured output validation for LLM evaluators
2. Evaluation Data Schemas (evaluation_data_schemas.py) - Unified data format for evaluation items
"""

# LLM Output Schemas (for validating LLM responses)
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

# Evaluation Data Schemas (for API data format)
from schemas.evaluation_data_schemas import (
    # Enums
    SchemaVersion,
    EvaluationType,
    SourceType,
    ContentType,
    RankingMode,
    LabelingMode,
    # Base structures
    LocalizedString,
    Source,
    Message,
    ConversationContent,
    Reference,
    Item,
    GroundTruth,
    # Ranking
    Bucket,
    RankingGroup,
    SimpleRankingConfig,
    MultiGroupRankingConfig,
    RankingConfig,
    # Rating
    Scale,
    Dimension,
    RatingConfig,
    MailRatingConfig,
    # Comparison
    ComparisonConfig,
    # Authenticity
    AuthenticityOption,
    AuthenticityConfig,
    # Labeling
    LabelOption,
    LabelingConfig,
    # Main schema
    EvaluationData,
    EvaluationConfig,
    # Factory functions
    create_default_ranking_buckets,
    create_default_rating_dimensions,
    create_default_scale,
    create_simple_ranking_config,
    create_rating_config,
)

__all__ = [
    # === LLM Output Schemas ===
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

    # === Evaluation Data Schemas ===
    # Enums
    "SchemaVersion",
    "EvaluationType",
    "SourceType",
    "ContentType",
    "RankingMode",
    "LabelingMode",
    # Base structures
    "LocalizedString",
    "Source",
    "Message",
    "ConversationContent",
    "Reference",
    "Item",
    "GroundTruth",
    # Ranking
    "Bucket",
    "RankingGroup",
    "SimpleRankingConfig",
    "MultiGroupRankingConfig",
    "RankingConfig",
    # Rating
    "Scale",
    "Dimension",
    "RatingConfig",
    "MailRatingConfig",
    # Comparison
    "ComparisonConfig",
    # Authenticity
    "AuthenticityOption",
    "AuthenticityConfig",
    # Labeling
    "LabelOption",
    "LabelingConfig",
    # Main schema
    "EvaluationData",
    "EvaluationConfig",
    # Factory functions
    "create_default_ranking_buckets",
    "create_default_rating_dimensions",
    "create_default_scale",
    "create_simple_ranking_config",
    "create_rating_config",
]
