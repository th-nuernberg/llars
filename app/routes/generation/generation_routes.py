"""
Generation API Routes.

REST API endpoints for batch generation jobs.

All routes require authentication and use standardized error handling.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from flask import Blueprint, g, jsonify, request, send_file

from auth.decorators import authentik_required
from db.models import GeneratedOutputStatus, GenerationJobStatus
from decorators.error_handler import handle_api_errors, ValidationError
from decorators.permission_decorator import require_permission
from services.generation import BatchGenerationService, OutputExportService

logger = logging.getLogger(__name__)

# =============================================================================
# BLUEPRINT
# =============================================================================

generation_bp = Blueprint('generation', __name__, url_prefix='/api/generation')


# =============================================================================
# JOB MANAGEMENT
# =============================================================================


@generation_bp.route('/jobs', methods=['POST'])
@authentik_required
@require_permission('feature:generation:create')
@handle_api_errors(logger_name='generation')
def create_job():
    """
    Create a new batch generation job.

    Request body:
    {
        "name": "Job name",
        "description": "Optional description",
        "config": {
            "sources": {"type": "scenario", "scenario_id": 123},
            "prompts": [{"template_id": 1, "variant_name": "Standard"}],
            "llm_models": ["gpt-4"],
            "generation_params": {"temperature": 0.7}
        }
    }

    Returns:
        201: Job created successfully
        400: Invalid configuration
    """
    data = request.get_json() or {}

    # Validate required fields
    if not data.get('name'):
        raise ValidationError("Job name is required")
    if not data.get('config'):
        raise ValidationError("Job config is required")

    # Get current user
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

    # Create job
    job = BatchGenerationService.create_job(
        name=data['name'],
        config=data['config'],
        created_by=username,
        description=data.get('description'),
    )

    logger.info("[GenAPI] User %s created job %d: %s", username, job.id, job.name)

    # Auto-start job in background (runs independently of user session)
    auto_start = data.get('auto_start', True)  # Default to auto-start
    if auto_start:
        try:
            from main import socketio
        except ImportError:
            socketio = None

        BatchGenerationService.start_job(job.id, socketio=socketio)
        logger.info("[GenAPI] Auto-started job %d", job.id)

    return jsonify({
        'success': True,
        'job': job.to_dict(),
        'auto_started': auto_start,
    }), 201


@generation_bp.route('/jobs', methods=['GET'])
@authentik_required
@require_permission('feature:generation:view')
@handle_api_errors(logger_name='generation')
def list_jobs():
    """
    List generation jobs for the current user.

    Query params:
        status: Optional status filter (created, running, completed, etc.)
        limit: Max number of jobs (default 50)

    Returns:
        200: List of jobs
    """
    # Get current user
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

    # Parse query params
    status_str = request.args.get('status')
    status = GenerationJobStatus(status_str) if status_str else None
    limit = min(int(request.args.get('limit', 50)), 100)

    # Get jobs
    jobs = BatchGenerationService.get_jobs_for_user(
        username,
        status=status,
        limit=limit
    )

    return jsonify({
        'success': True,
        'jobs': jobs,
        'total': len(jobs),
    })


@generation_bp.route('/jobs/<int:job_id>', methods=['GET'])
@authentik_required
@require_permission('feature:generation:view')
@handle_api_errors(logger_name='generation')
def get_job(job_id: int):
    """
    Get details for a specific job.

    Returns:
        200: Job details
        404: Job not found
    """
    job = BatchGenerationService.get_job(job_id)

    return jsonify({
        'success': True,
        'job': job.to_dict(include_outputs=True),
    })


@generation_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@authentik_required
@require_permission('feature:generation:manage')
@handle_api_errors(logger_name='generation')
def delete_job(job_id: int):
    """
    Delete a generation job.

    Only completed, failed, or cancelled jobs can be deleted.

    Returns:
        200: Job deleted
        400: Job cannot be deleted (still active)
        404: Job not found
    """
    BatchGenerationService.delete_job(job_id)

    logger.info("[GenAPI] Deleted job %d", job_id)

    return jsonify({
        'success': True,
        'message': f'Job {job_id} deleted',
    })


# =============================================================================
# JOB LIFECYCLE
# =============================================================================


@generation_bp.route('/jobs/<int:job_id>/start', methods=['POST'])
@authentik_required
@require_permission('feature:generation:manage')
@handle_api_errors(logger_name='generation')
def start_job(job_id: int):
    """
    Start a generation job.

    The job will be processed asynchronously.

    Returns:
        200: Job started
        400: Job cannot be started
        404: Job not found
    """
    # Get socketio instance for progress events
    try:
        from main import socketio
    except ImportError:
        socketio = None

    job = BatchGenerationService.start_job(job_id, socketio=socketio)

    logger.info("[GenAPI] Started job %d", job_id)

    return jsonify({
        'success': True,
        'job': job.to_dict(),
        'message': 'Job started',
    })


@generation_bp.route('/jobs/<int:job_id>/pause', methods=['POST'])
@authentik_required
@require_permission('feature:generation:manage')
@handle_api_errors(logger_name='generation')
def pause_job(job_id: int):
    """
    Pause a running job.

    Returns:
        200: Job paused
        400: Job cannot be paused
        404: Job not found
    """
    job = BatchGenerationService.pause_job(job_id)

    logger.info("[GenAPI] Paused job %d", job_id)

    return jsonify({
        'success': True,
        'job': job.to_dict(),
        'message': 'Job paused',
    })


@generation_bp.route('/jobs/<int:job_id>/cancel', methods=['POST'])
@authentik_required
@require_permission('feature:generation:manage')
@handle_api_errors(logger_name='generation')
def cancel_job(job_id: int):
    """
    Cancel a job.

    Returns:
        200: Job cancelled
        400: Job cannot be cancelled
        404: Job not found
    """
    job = BatchGenerationService.cancel_job(job_id)

    logger.info("[GenAPI] Cancelled job %d", job_id)

    return jsonify({
        'success': True,
        'job': job.to_dict(),
        'message': 'Job cancelled',
    })


# =============================================================================
# OUTPUTS
# =============================================================================


@generation_bp.route('/jobs/<int:job_id>/outputs', methods=['GET'])
@authentik_required
@require_permission('feature:generation:view')
@handle_api_errors(logger_name='generation')
def get_job_outputs(job_id: int):
    """
    Get outputs for a job with pagination.

    Query params:
        page: Page number (default 1)
        per_page: Items per page (default 50, max 100)
        status: Optional status filter
        include_prompts: Include rendered prompts (default false)

    Returns:
        200: Paginated outputs
        404: Job not found
    """
    # Parse query params
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 100)
    status_str = request.args.get('status')
    status = GeneratedOutputStatus(status_str) if status_str else None
    include_prompts = request.args.get('include_prompts', 'false').lower() == 'true'

    # Get outputs
    result = BatchGenerationService.get_job_outputs(
        job_id,
        status=status,
        page=page,
        per_page=per_page,
        include_prompts=include_prompts
    )

    return jsonify({
        'success': True,
        **result,
    })


@generation_bp.route('/outputs/<int:output_id>', methods=['GET'])
@authentik_required
@require_permission('feature:generation:view')
@handle_api_errors(logger_name='generation')
def get_output(output_id: int):
    """
    Get a single output by ID.

    Returns:
        200: Output details
        404: Output not found
    """
    output = BatchGenerationService.get_output(output_id)

    return jsonify({
        'success': True,
        'output': output,
    })


# =============================================================================
# EXPORT
# =============================================================================


@generation_bp.route('/jobs/<int:job_id>/export/csv', methods=['POST'])
@authentik_required
@require_permission('feature:generation:export')
@handle_api_errors(logger_name='generation')
def export_csv(job_id: int):
    """
    Export job outputs to CSV.

    Request body (optional):
    {
        "include_prompts": false,
        "status": "completed"
    }

    Returns:
        200: CSV file download
        404: Job not found
    """
    data = request.get_json() or {}

    include_prompts = data.get('include_prompts', False)
    status_str = data.get('status')
    status = GeneratedOutputStatus(status_str) if status_str else None

    # Generate CSV
    csv_buffer = OutputExportService.export_to_csv(
        job_id,
        include_prompts=include_prompts,
        status_filter=status
    )

    # Get job name for filename
    job = BatchGenerationService.get_job(job_id)
    filename = f"generation_{job_id}_{job.name.replace(' ', '_')}.csv"

    logger.info("[GenAPI] Exported job %d to CSV", job_id)

    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@generation_bp.route('/jobs/<int:job_id>/export/json', methods=['POST'])
@authentik_required
@require_permission('feature:generation:export')
@handle_api_errors(logger_name='generation')
def export_json(job_id: int):
    """
    Export job outputs to JSON.

    Request body (optional):
    {
        "include_prompts": true,
        "status": "completed"
    }

    Returns:
        200: JSON export
        404: Job not found
    """
    data = request.get_json() or {}

    include_prompts = data.get('include_prompts', True)
    status_str = data.get('status')
    status = GeneratedOutputStatus(status_str) if status_str else None

    # Generate JSON
    result = OutputExportService.export_to_json(
        job_id,
        include_prompts=include_prompts,
        status_filter=status
    )

    logger.info("[GenAPI] Exported job %d to JSON", job_id)

    return jsonify({
        'success': True,
        'export': result,
    })


# =============================================================================
# SCENARIO CREATION
# =============================================================================


@generation_bp.route('/jobs/<int:job_id>/to-scenario', methods=['POST'])
@authentik_required
@require_permission('feature:generation:to_scenario')
@handle_api_errors(logger_name='generation')
def create_scenario_from_job(job_id: int):
    """
    Create an evaluation scenario from job outputs.

    Request body:
    {
        "scenario_name": "My Evaluation",
        "evaluation_type": "ranking",
        "config_json": {}  // optional
    }

    Returns:
        201: Scenario created
        400: Invalid request or no outputs
        404: Job not found
    """
    data = request.get_json() or {}

    # Validate required fields
    if not data.get('scenario_name'):
        raise ValidationError("scenario_name is required")
    if not data.get('evaluation_type'):
        raise ValidationError("evaluation_type is required")

    # Get current user
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

    # Create scenario
    scenario = OutputExportService.create_evaluation_scenario(
        job_id=job_id,
        scenario_name=data['scenario_name'],
        evaluation_type=data['evaluation_type'],
        created_by=username,
        config_json=data.get('config_json'),
    )

    logger.info(
        "[GenAPI] User %s created scenario %d from job %d",
        username, scenario.id, job_id
    )

    return jsonify({
        'success': True,
        'scenario_id': scenario.id,
        'scenario_name': scenario.scenario_name,
        'message': f'Scenario created with {len(scenario.scenario_items)} items',
    }), 201


# =============================================================================
# STATISTICS & ESTIMATION
# =============================================================================


@generation_bp.route('/jobs/<int:job_id>/statistics', methods=['GET'])
@authentik_required
@require_permission('feature:generation:view')
@handle_api_errors(logger_name='generation')
def get_job_statistics(job_id: int):
    """
    Get detailed statistics for a job.

    Returns:
        200: Job statistics
        404: Job not found
    """
    stats = OutputExportService.get_job_statistics(job_id)

    return jsonify({
        'success': True,
        'statistics': stats,
    })


@generation_bp.route('/estimate', methods=['POST'])
@authentik_required
@require_permission('feature:generation:view')
@handle_api_errors(logger_name='generation')
def estimate_cost():
    """
    Estimate cost for a job configuration.

    Request body:
    {
        "config": {
            "sources": {"type": "scenario", "scenario_id": 123},
            "prompts": [{"template_id": 1}],
            "llm_models": ["gpt-4"]
        }
    }

    Returns:
        200: Cost estimate
        400: Invalid configuration
    """
    data = request.get_json() or {}

    if not data.get('config'):
        raise ValidationError("config is required")

    estimate = BatchGenerationService.estimate_cost(data['config'])

    return jsonify({
        'success': True,
        'estimate': estimate,
    })


# =============================================================================
# HEALTH CHECK
# =============================================================================


@generation_bp.route('/health', methods=['GET'])
@handle_api_errors(logger_name='generation')
def health_check():
    """Health check endpoint for generation service."""
    return jsonify({
        'success': True,
        'service': 'generation',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
    })
