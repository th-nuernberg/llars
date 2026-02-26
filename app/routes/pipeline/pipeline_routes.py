"""
Pipeline API Routes.

CRUD + lifecycle endpoints for automated LLM evaluation pipeline runs.
"""

import logging

from flask import Blueprint, g, jsonify, request
from auth.decorators import authentik_required
from auth.access_control import require_pipeline_run_owner
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission

logger = logging.getLogger(__name__)

# =============================================================================
# BLUEPRINT
# =============================================================================

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/api/pipeline')


# =============================================================================
# CRUD
# =============================================================================


@pipeline_bp.route('/runs', methods=['POST'])
@authentik_required
@require_permission('feature:pipeline:create')
@handle_api_errors(logger_name='pipeline')
def create_run():
    """Create a new pipeline run."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    data = request.get_json() or {}

    if not data.get('name'):
        raise ValidationError("Pipeline name is required")
    if not data.get('candidate_models'):
        raise ValidationError("At least one candidate model is required")

    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

    run = PipelineOrchestratorService.create_run(
        name=data['name'],
        config=data.get('config', {}),
        candidate_models=data['candidate_models'],
        created_by=username,
        description=data.get('description'),
        scenario_type=data.get('scenario_type', 'greenfield'),
        reference_model_id=data.get('reference_model_id'),
        source_scenario_id=data.get('source_scenario_id'),
        max_iterations=data.get('max_iterations', 10),
        budget_tokens_total=data.get('budget_tokens_total', 500000),
    )

    logger.info("[PipelineAPI] User %s created run %d: %s", username, run.id, run.name)

    auto_start = data.get('auto_start', False)
    if auto_start:
        PipelineOrchestratorService.start_run(run.id)
        logger.info("[PipelineAPI] Auto-started run %d", run.id)

    return jsonify({
        'success': True,
        'run': run.to_dict(),
    }), 201


@pipeline_bp.route('/runs', methods=['GET'])
@authentik_required
@require_permission('feature:pipeline:view')
@handle_api_errors(logger_name='pipeline')
def list_runs():
    """List all pipeline runs for the current user."""
    from db.models.pipeline import PipelineRun

    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

    status_filter = request.args.get('status')
    limit = min(int(request.args.get('limit', 50)), 200)

    from db.models.pipeline import PipelineStatus
    status = PipelineStatus(status_filter) if status_filter else None

    runs = PipelineRun.get_runs_for_user(username, status=status, limit=limit)

    return jsonify({
        'success': True,
        'runs': [r.to_summary_dict() for r in runs],
    })


@pipeline_bp.route('/runs/<int:run_id>', methods=['GET'])
@authentik_required
@require_permission('feature:pipeline:view')
@handle_api_errors(logger_name='pipeline')
def get_run(run_id: int):
    """Get full run details including all iterations (for live-join)."""
    from db.models.pipeline import PipelineRun

    run = PipelineRun.query.get(run_id)
    if not run:
        raise NotFoundError(f'Pipeline run {run_id} not found')

    require_pipeline_run_owner(run_id, g.authentik_user)

    return jsonify({
        'success': True,
        'run': run.to_dict(include_iterations=True),
    })


@pipeline_bp.route('/runs/<int:run_id>', methods=['DELETE'])
@authentik_required
@require_permission('feature:pipeline:manage')
@handle_api_errors(logger_name='pipeline')
def delete_run(run_id: int):
    """Delete a pipeline run."""
    from db.models.pipeline import PipelineRun, PipelineStatus
    from db import db

    run = PipelineRun.query.get(run_id)
    if not run:
        raise NotFoundError(f'Pipeline run {run_id} not found')

    require_pipeline_run_owner(run_id, g.authentik_user)

    if run.status == PipelineStatus.RUNNING:
        raise ValidationError("Cannot delete a running pipeline. Pause or cancel it first.")

    db.session.delete(run)
    db.session.commit()

    logger.info("[PipelineAPI] Deleted run %d", run_id)
    return jsonify({'success': True}), 200


# =============================================================================
# LIFECYCLE
# =============================================================================


@pipeline_bp.route('/runs/<int:run_id>/start', methods=['POST'])
@authentik_required
@require_permission('feature:pipeline:create')
@handle_api_errors(logger_name='pipeline')
def start_run(run_id: int):
    """Start or resume a pipeline run."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    require_pipeline_run_owner(run_id, g.authentik_user)
    run = PipelineOrchestratorService.start_run(run_id)

    logger.info("[PipelineAPI] Started run %d", run_id)
    return jsonify({
        'success': True,
        'run': run.to_dict(),
    })


@pipeline_bp.route('/runs/<int:run_id>/pause', methods=['POST'])
@authentik_required
@require_permission('feature:pipeline:create')
@handle_api_errors(logger_name='pipeline')
def pause_run(run_id: int):
    """Pause a running pipeline."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    require_pipeline_run_owner(run_id, g.authentik_user)
    run = PipelineOrchestratorService.pause_run(run_id)

    logger.info("[PipelineAPI] Paused run %d", run_id)
    return jsonify({
        'success': True,
        'run': run.to_dict(),
    })


@pipeline_bp.route('/runs/<int:run_id>/cancel', methods=['POST'])
@authentik_required
@require_permission('feature:pipeline:create')
@handle_api_errors(logger_name='pipeline')
def cancel_run(run_id: int):
    """Cancel a pipeline run."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    require_pipeline_run_owner(run_id, g.authentik_user)
    run = PipelineOrchestratorService.cancel_run(run_id)

    logger.info("[PipelineAPI] Cancelled run %d", run_id)
    return jsonify({
        'success': True,
        'run': run.to_dict(),
    })


@pipeline_bp.route('/runs/<int:run_id>/review', methods=['POST'])
@authentik_required
@require_permission('feature:pipeline:manage')
@handle_api_errors(logger_name='pipeline')
def submit_review(run_id: int):
    """Submit human review decision (continue, deploy, or reject)."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    require_pipeline_run_owner(run_id, g.authentik_user)
    data = request.get_json() or {}
    decision = data.get('decision')

    if decision not in ('continue', 'deploy', 'reject'):
        raise ValidationError("Decision must be 'continue', 'deploy', or 'reject'")

    run = PipelineOrchestratorService.handle_review(run_id, decision)

    logger.info("[PipelineAPI] Review for run %d: %s", run_id, decision)
    return jsonify({
        'success': True,
        'run': run.to_dict(),
    })


# =============================================================================
# ITERATION DETAILS
# =============================================================================


@pipeline_bp.route('/runs/<int:run_id>/iterations/<int:iteration_number>', methods=['GET'])
@authentik_required
@require_permission('feature:pipeline:view')
@handle_api_errors(logger_name='pipeline')
def get_iteration(run_id: int, iteration_number: int):
    """Get details of a specific iteration."""
    from db.models.pipeline import PipelineIteration

    require_pipeline_run_owner(run_id, g.authentik_user)

    iteration = PipelineIteration.query.filter_by(
        run_id=run_id,
        iteration_number=iteration_number,
    ).first()

    if not iteration:
        raise NotFoundError(
            f'Iteration {iteration_number} not found for run {run_id}'
        )

    return jsonify({
        'success': True,
        'iteration': iteration.to_dict(),
    })


@pipeline_bp.route('/runs/<int:run_id>/best-configs', methods=['GET'])
@authentik_required
@require_permission('feature:pipeline:view')
@handle_api_errors(logger_name='pipeline')
def get_best_configs(run_id: int):
    """Get top-K configurations from a pipeline run."""
    from db.models.pipeline import PipelineRun, PipelineIteration, PipelineIterationStatus

    run = PipelineRun.query.get(run_id)
    if not run:
        raise NotFoundError(f'Pipeline run {run_id} not found')

    require_pipeline_run_owner(run_id, g.authentik_user)

    limit = min(int(request.args.get('limit', 5)), 20)

    completed = PipelineIteration.query.filter_by(
        run_id=run_id,
        status=PipelineIterationStatus.COMPLETED,
    ).order_by(PipelineIteration.iteration_number.desc()).limit(limit).all()

    configs = []
    for it in completed:
        if it.scores_json:
            configs.append({
                'iteration': it.iteration_number,
                'scores': it.scores_json,
                'prompt_variants': it.prompt_variants_json,
                'agent_reasoning': it.agent_reasoning,
                'delta_to_best': it.delta_to_best,
            })

    configs.sort(key=lambda c: c.get('delta_to_best') or 0, reverse=True)

    return jsonify({
        'success': True,
        'best_config': run.best_config_json,
        'top_configs': configs[:limit],
    })
