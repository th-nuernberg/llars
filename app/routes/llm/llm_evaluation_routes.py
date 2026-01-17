"""
LLM Evaluation API Routes.

Provides REST endpoints for LLM evaluation progress tracking
and result retrieval.
"""

import json
import logging
from flask import Blueprint, jsonify, g, request

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

llm_evaluation_bp = Blueprint('llm_evaluation', __name__, url_prefix='/api/evaluation/llm')


@llm_evaluation_bp.get('/<int:scenario_id>/progress')
@authentik_required
@handle_api_errors(logger_name='llm_evaluation')
def get_evaluation_progress(scenario_id):
    """
    Get LLM evaluation progress for a scenario.

    Returns progress statistics for all LLM evaluators assigned
    to the scenario, including completed evaluations, errors, and
    overall progress percentage.

    Args:
        scenario_id: Scenario ID

    Returns:
        JSON with progress statistics
    """
    from db.models import RatingScenarios, LLMTaskResult, ScenarioThreads

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Get total threads
    total_threads = ScenarioThreads.query.filter_by(
        scenario_id=scenario_id
    ).count()

    # Get LLM evaluators from config
    config = scenario.config_json
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    elif not isinstance(config, dict):
        config = {}

    llm_evaluators = config.get('llm_evaluators')
    if not llm_evaluators:
        llm_evaluators = config.get('selected_llms') or []

    normalized_models = []
    for model in llm_evaluators:
        if isinstance(model, str):
            mid = model.strip()
        elif isinstance(model, dict):
            mid = str(model.get('model_id') or '').strip()
        else:
            continue
        if mid and mid not in normalized_models:
            normalized_models.append(mid)
    llm_evaluators = normalized_models

    # Get completed evaluations per model
    model_progress = {}
    for model_id in llm_evaluators:
        completed = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            model_id=model_id,
        ).filter(LLMTaskResult.payload_json.isnot(None)).count()

        errors = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            model_id=model_id,
        ).filter(LLMTaskResult.error.isnot(None)).count()

        model_progress[model_id] = {
            'completed': completed,
            'errors': errors,
            'total': total_threads,
            'progress_percent': (completed / total_threads * 100) if total_threads > 0 else 0
        }

    # Calculate overall progress
    total_tasks = total_threads * len(llm_evaluators) if llm_evaluators else total_threads
    total_completed = sum(m['completed'] for m in model_progress.values())
    total_errors = sum(m['errors'] for m in model_progress.values())

    # Determine status
    if total_tasks == 0:
        status = 'idle'
    elif total_completed >= total_tasks:
        status = 'completed'
    elif total_completed > 0 or total_errors > 0:
        status = 'running'
    else:
        status = 'idle'

    return jsonify({
        'scenario_id': scenario_id,
        'status': status,
        'progress': {
            'total': total_tasks,
            'completed': total_completed,
            'pending': total_tasks - total_completed - total_errors,
            'failed': total_errors,
            'percent': (total_completed / total_tasks * 100) if total_tasks > 0 else 0
        },
        'total_threads': total_threads,
        'llm_evaluators': llm_evaluators,
        'model_progress': model_progress,
        'results': [],  # Full results require separate call
        'agreement_metrics': None,  # Calculated on demand
        'token_usage': {
            'total_tokens': 0,
            'total_cost_usd': 0.0,
            'by_model': []
        }
    })


@llm_evaluation_bp.get('/result/<int:result_id>')
@authentik_required
@handle_api_errors(logger_name='llm_evaluation')
def get_evaluation_result(result_id):
    """
    Get a specific LLM evaluation result.

    Args:
        result_id: Result ID

    Returns:
        JSON with evaluation result details
    """
    from db.models import LLMTaskResult

    result = LLMTaskResult.query.get(result_id)
    if not result:
        raise NotFoundError(f'Result {result_id} not found')

    return jsonify(result.to_dict(include_raw=False))


@llm_evaluation_bp.post('/<int:scenario_id>/start')
@authentik_required
@handle_api_errors(logger_name='llm_evaluation')
def start_evaluation(scenario_id):
    """
    Start LLM evaluation for a scenario.

    This triggers the LLM evaluators to process all threads
    in the scenario. Progress can be monitored via Socket.IO
    or the progress endpoint.

    Args:
        scenario_id: Scenario ID

    Body:
        model_id: Optional specific model to run (runs all if not specified)

    Returns:
        JSON with status
    """
    from db.models import RatingScenarios

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    data = request.get_json(silent=True) or {}
    model_id = data.get('model_id')

    username = getattr(g.authentik_user, 'username', str(g.authentik_user))

    if model_id:
        from services.llm.llm_access_service import LLMAccessService
        if not LLMAccessService.user_can_access_model(username, model_id):
            raise ValidationError(f'No access to LLM model: {model_id}')

    from services.llm.llm_ai_task_runner import LLMAITaskRunner
    LLMAITaskRunner.run_for_scenario_async(
        scenario_id,
        model_ids=[model_id] if model_id else None,
    )

    logger.info(f"LLM evaluation start requested for scenario {scenario_id}")

    return jsonify({
        'success': True,
        'scenario_id': scenario_id,
        'message': 'Evaluation start queued',
        'model_id': model_id
    })


@llm_evaluation_bp.post('/<int:scenario_id>/stop')
@authentik_required
@handle_api_errors(logger_name='llm_evaluation')
def stop_evaluation(scenario_id):
    """
    Stop running LLM evaluation for a scenario.

    Args:
        scenario_id: Scenario ID

    Returns:
        JSON with status
    """
    from db.models import RatingScenarios

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # TODO: Implement evaluation stopping
    logger.info(f"LLM evaluation stop requested for scenario {scenario_id}")

    return jsonify({
        'success': True,
        'scenario_id': scenario_id,
        'message': 'Evaluation stop requested'
    })
