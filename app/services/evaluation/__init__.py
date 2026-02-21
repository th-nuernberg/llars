"""
Evaluation Services for LLM Evaluators.

This module provides services for:
- Prompt template management
- Token usage tracking
- Structured output validation
- Agreement metrics calculation
- Multi-dimensional rating
- Schema transformation (DB → unified EvaluationData format)

SCHEMA GROUND TRUTH:
--------------------
Die einheitlichen Evaluation-Schemas sind definiert in:
- Backend: app/schemas/evaluation_data_schemas.py (Pydantic Models)
- Frontend: llars-frontend/src/schemas/evaluationSchemas.ts (TypeScript + Zod)

Alle Module, die Evaluation-Daten verarbeiten, MÜSSEN diese Schemas verwenden:
- Batch Generation
- Data Upload / Import
- Scenario Manager
- Evaluation API
- LLM Prompts

Siehe: .claude/plans/evaluation-data-schemas.md für Dokumentation
"""

from services.evaluation.prompt_template_service import (
    PromptTemplateService,
    DEFAULT_PROMPTS,
)
from services.evaluation.token_tracking_service import (
    TokenTrackingService,
    BudgetExceededError,
)
from services.evaluation.agreement_metrics_service import (
    AgreementMetricsService,
)
from services.evaluation.dimensional_rating_service import (
    DimensionalRatingService,
    DEFAULT_DIMENSIONS,
)
from services.evaluation.schema_transformer_service import (
    SchemaTransformer,
)

__all__ = [
    "PromptTemplateService",
    "DEFAULT_PROMPTS",
    "TokenTrackingService",
    "BudgetExceededError",
    "AgreementMetricsService",
    "DimensionalRatingService",
    "DEFAULT_DIMENSIONS",
    "SchemaTransformer",
]
