"""
Evaluation API Routes.

Provides REST endpoints for evaluation metrics and results.
Separate from LLM-specific evaluation routes.
"""

import logging
from flask import Blueprint, jsonify

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError

logger = logging.getLogger(__name__)

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/evaluation')


@evaluation_bp.get('/<int:scenario_id>/agreement-metrics')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_agreement_metrics(scenario_id):
    """
    Get inter-rater agreement metrics for a scenario.

    Calculates and returns metrics including:
    - Krippendorff's Alpha
    - Cohen's Kappa (for 2 raters)
    - Fleiss' Kappa (for 3+ raters)
    - Kendall's Tau
    - Spearman's Rho
    - Percent Agreement

    Args:
        scenario_id: Scenario ID to analyze

    Query Parameters:
        include_llm: Include LLM evaluators (default: true)
        include_human: Include human evaluators (default: true)

    Returns:
        JSON with agreement metrics and interpretations
    """
    from flask import request
    from db.models import RatingScenarios
    from services.evaluation.agreement_metrics_service import AgreementMetricsService

    # Verify scenario exists
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Parse query parameters
    include_llm = request.args.get('include_llm', 'true').lower() == 'true'
    include_human = request.args.get('include_human', 'true').lower() == 'true'

    # Calculate metrics
    metrics = AgreementMetricsService.calculate_all_metrics(
        scenario_id=scenario_id,
        include_llm=include_llm,
        include_human=include_human,
    )

    # Check for errors
    if 'error' in metrics:
        return jsonify({
            'scenario_id': scenario_id,
            'error': metrics['error'],
            'metrics': {},
            'rater_count': 0,
            'item_count': 0,
        })

    return jsonify(metrics)
