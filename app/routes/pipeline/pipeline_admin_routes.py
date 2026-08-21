"""
Pipeline Admin API Routes.

Admin-only endpoints for managing pipeline runs externally via API key.
Protected by @system_api_key_required — no Authentik session needed.

Usage:
    API_KEY="llars-admin-key-change-in-production-12345"
    BASE="http://localhost:55080/api/pipeline/admin"

    # Create + start a test run
    curl -X POST "$BASE/test-run" -H "X-API-Key: $API_KEY" -H "Content-Type: application/json"

    # List all runs
    curl "$BASE/runs" -H "X-API-Key: $API_KEY"

    # Check run status
    curl "$BASE/runs/1/status" -H "X-API-Key: $API_KEY"

    # Get full run details
    curl "$BASE/runs/1" -H "X-API-Key: $API_KEY"

    # Start / pause / cancel
    curl -X POST "$BASE/runs/1/start" -H "X-API-Key: $API_KEY"
    curl -X POST "$BASE/runs/1/pause" -H "X-API-Key: $API_KEY"
    curl -X POST "$BASE/runs/1/cancel" -H "X-API-Key: $API_KEY"

    # Submit review decision
    curl -X POST "$BASE/runs/1/review" -H "X-API-Key: $API_KEY" \\
         -H "Content-Type: application/json" -d '{"decision": "deploy"}'

    # Cleanup all test data
    curl -X DELETE "$BASE/cleanup" -H "X-API-Key: $API_KEY"
"""

import logging

from flask import Blueprint, jsonify, request
from auth.decorators import system_api_key_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

pipeline_admin_bp = Blueprint(
    'pipeline_admin', __name__, url_prefix='/api/pipeline/admin',
)


# =============================================================================
# TEST RUN (create + start in one call)
# =============================================================================


@pipeline_admin_bp.route('/test-run', methods=['POST'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def create_test_run():
    """Create and optionally start a test pipeline run with sensible defaults."""
    from services.pipeline.pipeline_test_service import PipelineTestService

    data = request.get_json() or {}

    result = PipelineTestService.create_test_run(
        name=data.get('name'),
        task_spec=data.get('task_spec'),
        candidate_models=data.get('candidate_models'),
        eval_model_id=data.get('eval_model_id'),
        meta_model_id=data.get('meta_model_id'),
        max_iterations=data.get('max_iterations', 3),
        budget_tokens_total=data.get('budget_tokens_total', 200000),
        auto_start=data.get('auto_start', True),
    )

    logger.info("[PipelineAdmin] Test run created: %d", result['run']['id'])
    return jsonify({'success': True, **result}), 201


# =============================================================================
# RUNS - LIST & DETAILS
# =============================================================================


@pipeline_admin_bp.route('/runs', methods=['GET'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def list_runs():
    """List all pipeline runs (no user filter for admin)."""
    from db.models.pipeline import PipelineRun, PipelineStatus

    status_filter = request.args.get('status')
    limit = min(int(request.args.get('limit', 50)), 200)

    query = PipelineRun.query.order_by(PipelineRun.created_at.desc())

    if status_filter:
        query = query.filter_by(status=PipelineStatus(status_filter))

    runs = query.limit(limit).all()

    return jsonify({
        'success': True,
        'runs': [r.to_summary_dict() for r in runs],
        'total': PipelineRun.query.count(),
    })


@pipeline_admin_bp.route('/runs/<int:run_id>', methods=['GET'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def get_run(run_id: int):
    """Get full run details including all iterations."""
    from db.models.pipeline import PipelineRun

    run = PipelineRun.query.get(run_id)
    if not run:
        raise NotFoundError(f'Pipeline run {run_id} not found')

    return jsonify({
        'success': True,
        'run': run.to_dict(include_iterations=True),
    })


@pipeline_admin_bp.route('/runs/<int:run_id>/status', methods=['GET'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def get_run_status(run_id: int):
    """Compact status check for polling."""
    from db.models.pipeline import PipelineRun

    run = PipelineRun.query.get(run_id)
    if not run:
        raise NotFoundError(f'Pipeline run {run_id} not found')

    return jsonify({
        'success': True,
        'id': run.id,
        'name': run.name,
        'status': run.status.value,
        'current_iteration': run.current_iteration,
        'max_iterations': run.max_iterations,
        'budget_percent': run.budget_percent,
        'best_score': (run.best_config_json or {}).get('avg_score'),
        'error_message': run.error_message,
        'started_at': run.started_at.isoformat() if run.started_at else None,
        'completed_at': run.completed_at.isoformat() if run.completed_at else None,
    })


# =============================================================================
# LIFECYCLE
# =============================================================================


@pipeline_admin_bp.route('/runs/<int:run_id>/start', methods=['POST'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def start_run(run_id: int):
    """Start or resume a pipeline run."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    run = PipelineOrchestratorService.start_run(run_id)

    logger.info("[PipelineAdmin] Started run %d", run_id)
    return jsonify({'success': True, 'run': run.to_dict()})


@pipeline_admin_bp.route('/runs/<int:run_id>/pause', methods=['POST'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def pause_run(run_id: int):
    """Pause a running pipeline."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    run = PipelineOrchestratorService.pause_run(run_id)

    logger.info("[PipelineAdmin] Paused run %d", run_id)
    return jsonify({'success': True, 'run': run.to_dict()})


@pipeline_admin_bp.route('/runs/<int:run_id>/cancel', methods=['POST'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def cancel_run(run_id: int):
    """Cancel a pipeline run."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    run = PipelineOrchestratorService.cancel_run(run_id)

    logger.info("[PipelineAdmin] Cancelled run %d", run_id)
    return jsonify({'success': True, 'run': run.to_dict()})


@pipeline_admin_bp.route('/runs/<int:run_id>/review', methods=['POST'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def submit_review(run_id: int):
    """Submit human review decision (continue, deploy, or reject)."""
    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

    data = request.get_json() or {}
    decision = data.get('decision')

    if decision not in ('continue', 'deploy', 'reject'):
        raise ValidationError("Decision must be 'continue', 'deploy', or 'reject'")

    run = PipelineOrchestratorService.handle_review(run_id, decision)

    logger.info("[PipelineAdmin] Review for run %d: %s", run_id, decision)
    return jsonify({'success': True, 'run': run.to_dict()})


# =============================================================================
# CLEANUP
# =============================================================================


@pipeline_admin_bp.route('/cleanup', methods=['DELETE'])
@system_api_key_required
@handle_api_errors(logger_name='pipeline_admin')
def cleanup():
    """Delete all test pipeline runs and test scenarios."""
    from services.pipeline.pipeline_test_service import PipelineTestService

    result = PipelineTestService.cleanup_test_data()

    logger.info("[PipelineAdmin] Cleanup completed: %s", result)
    return jsonify({'success': True, **result})
