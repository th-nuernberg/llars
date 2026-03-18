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

from auth.decorators import authentik_required, api_key_or_token_required
from auth.access_control import require_generation_job_owner, require_generation_job_access
from db import db
from db.models import GeneratedOutputStatus, GenerationJobShare, GenerationJobStatus, User
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from services.generation import BatchGenerationService, OutputExportService
from services.system_settings_service import get_batch_generation_max_parallel
from services.user_profile_service import serialize_user_brief

logger = logging.getLogger(__name__)

# =============================================================================
# BLUEPRINT
# =============================================================================

generation_bp = Blueprint('generation', __name__, url_prefix='/api/generation')


# =============================================================================
# JOB MANAGEMENT
# =============================================================================


@generation_bp.route('/jobs', methods=['POST'])
@api_key_or_token_required
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
@api_key_or_token_required
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

    # Parse and validate query params
    status_str = request.args.get('status')
    try:
        status = GenerationJobStatus(status_str) if status_str else None
    except ValueError:
        raise ValidationError(f'Invalid status: {status_str}')
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
    except (ValueError, TypeError):
        raise ValidationError('Invalid limit parameter')

    # Get own jobs
    jobs = BatchGenerationService.get_jobs_for_user(
        username,
        status=status,
        limit=limit
    )

    # Get shared jobs
    user_id = getattr(user, 'id', None)
    shared_jobs = BatchGenerationService.get_shared_jobs_for_user(
        user_id, status=status, limit=limit
    ) if user_id else []

    return jsonify({
        'success': True,
        'jobs': jobs,
        'shared_jobs': shared_jobs,
        'total': len(jobs),
    })


@generation_bp.route('/jobs/<int:job_id>', methods=['GET'])
@api_key_or_token_required
@require_permission('feature:generation:view')
@handle_api_errors(logger_name='generation')
def get_job(job_id: int):
    """
    Get details for a specific job.

    Returns:
        200: Job details
        404: Job not found
    """
    require_generation_job_access(job_id, g.authentik_user)

    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

    # Use get_job_status to include currently_processing for reconnection support
    job_data = BatchGenerationService.get_job_status(job_id)

    # Add sharing metadata
    is_owner = job_data.get('created_by') == username
    job_data['is_shared'] = not is_owner
    if is_owner:
        shares = GenerationJobShare.query.filter_by(job_id=job_id).all()
        job_data['shared_with'] = [
            {
                'share_id': s.id,
                **serialize_user_brief(s.shared_with_user),
                'created_at': s.created_at.isoformat() if s.created_at else None,
            }
            for s in shares
        ]

    return jsonify({
        'success': True,
        'job': job_data,
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
    require_generation_job_owner(job_id, g.authentik_user)
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
@api_key_or_token_required
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
    require_generation_job_owner(job_id, g.authentik_user)
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
    require_generation_job_owner(job_id, g.authentik_user)
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
    require_generation_job_owner(job_id, g.authentik_user)
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
    require_generation_job_access(job_id, g.authentik_user)
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
    require_generation_job_access(output['job_id'], g.authentik_user)

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
    require_generation_job_access(job_id, g.authentik_user)
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
    require_generation_job_access(job_id, g.authentik_user)
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
    Create an evaluation scenario from job outputs (server-side).

    This endpoint creates a scenario directly from the DB without requiring
    the client to transfer all output data. The wizard sends only config.

    Request body:
    {
        "scenario_name": "My Evaluation",
        "evaluation_type": "ranking",
        "description": "...",                   // optional
        "config_json": {},                      // optional
        "eval_config": {},                      // optional wizard eval config
        "invited_users": [                      // optional
            {"user_id": 123, "role": "EVALUATOR"}
        ],
        "llm_evaluators": ["Global/OpenAI/..."],// optional
        "split_by_prompt": false                // optional, for ranking
    }

    Returns:
        201: Scenario created
        400: Invalid request or no outputs
        404: Job not found
    """
    # Shared users can also create scenarios from batch results
    require_generation_job_access(job_id, g.authentik_user)
    data = request.get_json() or {}

    # Validate required fields
    if not data.get('scenario_name'):
        raise ValidationError("scenario_name is required")
    if not data.get('evaluation_type'):
        raise ValidationError("evaluation_type is required")

    # Get current user
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

    # Build config_json by merging provided config with wizard fields
    config_json = data.get('config_json') or {}

    # Merge eval_config from wizard
    if data.get('eval_config'):
        config_json['eval_config'] = data['eval_config']

    # Merge LLM evaluators (may come at top level or inside config_json from wizard)
    llm_evaluators = data.get('llm_evaluators') or config_json.get('llm_evaluators') or []
    if llm_evaluators:
        config_json['enable_llm_evaluation'] = True
        config_json['llm_evaluators'] = llm_evaluators

    # Create scenario
    scenario = OutputExportService.create_evaluation_scenario(
        job_id=job_id,
        scenario_name=data['scenario_name'],
        evaluation_type=data['evaluation_type'],
        created_by=username,
        description=data.get('description'),
        config_json=config_json,
        split_by_prompt=data.get('split_by_prompt', False),
    )

    # Handle owner_as_assessor: promote owner to assessor if requested
    if data.get('owner_as_assessor'):
        from db.models import ScenarioUsers, ScenarioRoles
        owner_su = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id,
            access_level='OWNER',
        ).first()
        if owner_su:
            owner_su.role = ScenarioRoles.ASSESSOR
            owner_su.is_assessor = True
            owner_su.is_viewer = False
            owner_su.evaluation_role = 'assessor'

    # Invite users if provided
    invited_users = data.get('invited_users', [])
    if invited_users and scenario.id:
        from db.models import User, ScenarioUsers, ScenarioRoles
        for invite in invited_users:
            invite_user_id = invite.get('user_id')
            invite_role = invite.get('role', 'EVALUATOR')
            if not invite_user_id:
                continue
            # Skip if already added (e.g. creator)
            existing = ScenarioUsers.query.filter_by(
                scenario_id=scenario.id,
                user_id=invite_user_id
            ).first()
            if existing:
                continue
            role_enum = getattr(ScenarioRoles, invite_role, ScenarioRoles.EVALUATOR)
            # Map legacy role enum to new flags
            is_assessor = role_enum in (ScenarioRoles.EVALUATOR, ScenarioRoles.ASSESSOR)
            is_viewer = role_enum == ScenarioRoles.VIEWER
            scenario_user = ScenarioUsers(
                scenario_id=scenario.id,
                user_id=invite_user_id,
                role=role_enum,
                access_level='MEMBER',
                is_assessor=is_assessor,
                is_viewer=is_viewer,
                manager_role='none' if is_assessor else ('viewer' if is_viewer else 'none'),
                evaluation_role='assessor' if is_assessor else 'none',
            )
            db.session.add(scenario_user)
        db.session.commit()

    logger.info(
        "[GenAPI] User %s created scenario %d from job %d (%d invited users)",
        username, scenario.id, job_id, len(invited_users)
    )

    # Auto-start LLM assessors if configured
    if llm_evaluators:
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        logger.info(
            "[GenAPI] Auto-starting LLM assessors for scenario %d: %s",
            scenario.id, llm_evaluators,
        )
        LLMAITaskRunner.run_for_scenario_async(
            scenario.id,
            model_ids=llm_evaluators,
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
    require_generation_job_access(job_id, g.authentik_user)
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
# SETTINGS
# =============================================================================


@generation_bp.route('/settings/max-parallel', methods=['GET'])
@authentik_required
@require_permission('feature:generation:view')
@handle_api_errors(logger_name='generation')
def get_max_parallel():
    """
    Get the admin-configured maximum parallelism for generation jobs.

    Frontend uses this to set the slider max for user-selectable parallelism.

    Returns:
        200: { max_parallel: N }
    """
    max_parallel = max(1, min(int(get_batch_generation_max_parallel() or 5), 16))

    return jsonify({
        'success': True,
        'max_parallel': max_parallel,
    })


# =============================================================================
# SHARING
# =============================================================================


@generation_bp.route('/jobs/<int:job_id>/share', methods=['POST'])
@authentik_required
@require_permission('feature:generation:manage')
@handle_api_errors(logger_name='generation')
def share_job(job_id: int):
    """
    Share a job with another user (read-only access).

    Request body:
    {
        "username": "researcher"
    }

    Returns:
        200: Share created
        400: Invalid username or already shared
        404: Job or user not found
    """
    require_generation_job_owner(job_id, g.authentik_user)
    data = request.get_json() or {}

    target_username = data.get('username')
    if not target_username:
        raise ValidationError("username is required")

    # Prevent self-share
    current_username = g.authentik_user.username
    if target_username == current_username:
        raise ValidationError("Cannot share a job with yourself")

    target_user = User.query.filter_by(username=target_username).first()
    if not target_user:
        raise NotFoundError(f'User "{target_username}" not found')

    # Check for existing share
    existing = GenerationJobShare.query.filter_by(
        job_id=job_id,
        shared_with_user_id=target_user.id
    ).first()
    if existing:
        raise ValidationError(f'Job already shared with "{target_username}"')

    share = GenerationJobShare(
        job_id=job_id,
        shared_with_user_id=target_user.id
    )
    db.session.add(share)
    db.session.commit()

    logger.info("[GenAPI] User shared job %d with %s", job_id, target_username)

    # Notify via Socket.IO so shared user's list refreshes
    _emit_share_updated(job_id)

    return jsonify({
        'success': True,
        'share': {
            'share_id': share.id,
            'username': target_username,
        },
        'message': f'Job shared with "{target_username}"',
    })


@generation_bp.route('/jobs/<int:job_id>/unshare', methods=['POST'])
@authentik_required
@require_permission('feature:generation:manage')
@handle_api_errors(logger_name='generation')
def unshare_job(job_id: int):
    """
    Remove a share from a job.

    Request body:
    {
        "username": "researcher"
    }

    Returns:
        200: Share removed
        404: Share not found
    """
    require_generation_job_owner(job_id, g.authentik_user)
    data = request.get_json() or {}

    target_username = data.get('username')
    if not target_username:
        raise ValidationError("username is required")

    target_user = User.query.filter_by(username=target_username).first()
    if not target_user:
        raise NotFoundError(f'User "{target_username}" not found')

    share = GenerationJobShare.query.filter_by(
        job_id=job_id,
        shared_with_user_id=target_user.id
    ).first()
    if not share:
        raise NotFoundError(f'No share found for "{target_username}"')

    db.session.delete(share)
    db.session.commit()

    logger.info("[GenAPI] User unshared job %d from %s", job_id, target_username)

    _emit_share_updated(job_id)

    return jsonify({
        'success': True,
        'message': f'Share removed for "{target_username}"',
    })


def _emit_share_updated(job_id: int) -> None:
    """Emit Socket.IO event when shares change so clients refresh their list."""
    try:
        from main import socketio
        from services.generation.socket_rooms import GENERATION_OVERVIEW_ROOM
        socketio.emit(
            'generation:share_updated',
            {'job_id': job_id},
            room=GENERATION_OVERVIEW_ROOM,
        )
    except Exception as e:
        logger.warning("[GenAPI] Could not emit share_updated: %s", e)


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
