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
from services.llm_registry_service import resolve_model_registry

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

        # Determine per-model status
        if completed >= total_threads:
            model_status = 'completed'
        elif errors > 0 and completed + errors >= total_threads:
            model_status = 'failed'
        elif errors > 0 and completed + errors < total_threads:
            model_status = 'stopped'
        elif completed > 0:
            model_status = 'running'
        else:
            model_status = 'pending'

        model_progress[model_id] = {
            'completed': completed,
            'errors': errors,
            'total': total_threads,
            'progress_percent': (completed / total_threads * 100) if total_threads > 0 else 0,
            'status': model_status,
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
    elif total_errors > 0 and total_completed + total_errors >= total_tasks:
        status = 'completed'  # All items attempted (some failed)
    elif total_errors > 0 and total_completed + total_errors < total_tasks:
        # Some items failed but not all attempted → likely stopped/aborted
        status = 'stopped'
    elif total_completed > 0:
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
        'model_registry': resolve_model_registry(llm_evaluators) if llm_evaluators else {},
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


@llm_evaluation_bp.get('/<int:scenario_id>/errors')
@authentik_required
@handle_api_errors(logger_name='llm_evaluation')
def get_evaluation_errors(scenario_id):
    """
    Get LLM evaluation error details for a scenario.

    Returns error details for failed evaluations, optionally filtered
    by model_id. Used on-demand when user opens the error dialog.

    Args:
        scenario_id: Scenario ID

    Query params:
        model_id: Optional model ID to filter errors

    Returns:
        JSON with error details list
    """
    from db.models import RatingScenarios, LLMTaskResult, EvaluationItem

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    model_id = request.args.get('model_id')

    query = LLMTaskResult.query.filter(
        LLMTaskResult.scenario_id == scenario_id,
        LLMTaskResult.error.isnot(None),
    )
    if model_id:
        query = query.filter(LLMTaskResult.model_id == model_id)

    error_results = query.order_by(LLMTaskResult.updated_at.desc()).all()

    # Build item label lookup
    thread_ids = [r.item_id for r in error_results]
    items = {}
    if thread_ids:
        item_rows = EvaluationItem.query.filter(EvaluationItem.item_id.in_(thread_ids)).all()
        items = {item.item_id: item for item in item_rows}

    errors = []
    for r in error_results:
        item = items.get(r.item_id)
        errors.append({
            'id': r.id,
            'model_id': r.model_id,
            'thread_id': r.item_id,
            'item_label': getattr(item, 'subject', None) or f'Item {r.item_id}',
            'error': r.error,
            'updated_at': r.updated_at.isoformat() if r.updated_at else None,
        })

    return jsonify({
        'scenario_id': scenario_id,
        'model_id': model_id,
        'total_errors': len(errors),
        'errors': errors,
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
