"""Session control routes (start, pause, resume, delete) for LLM-as-Judge."""

from datetime import datetime
from flask import Blueprint, request, jsonify, g

from db.db import db
from db.tables import (
    JudgeSession, JudgeSessionStatus,
    JudgeComparison, JudgeComparisonStatus
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)

session_control_bp = Blueprint('judge_sessions_control', __name__)


@session_control_bp.route('/sessions/<int:session_id>/start', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
def start_session(session_id: int):
    """
    Start processing the session queue.

    Query params:
        auto_sync: If 'true', sync KIA data before starting

    Returns:
        JSON with session status
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

    # Allow starting from CREATED, QUEUED, or PAUSED status
    if session.status not in [JudgeSessionStatus.CREATED, JudgeSessionStatus.QUEUED, JudgeSessionStatus.PAUSED]:
        raise ValidationError(
            f'Session kann nicht gestartet werden (Status: {session.status.value})'
        )

    # Optional: Auto-sync KIA data before starting
    auto_sync = request.args.get('auto_sync', 'false').lower() == 'true'
    sync_result = None

    if auto_sync:
        try:
            from services.judge.kia_sync_service import get_kia_sync_service
            sync_service = get_kia_sync_service()

            # Only sync if we have a token configured
            if sync_service._get_project_id():
                results = sync_service.sync_all_pillars(force=False)
                sync_result = {
                    'synced': True,
                    'threads_created': sum(r.threads_created for r in results.values()),
                    'threads_updated': sum(r.threads_updated for r in results.values())
                }
        except Exception as e:
            sync_result = {'synced': False, 'error': str(e)}

    session.status = JudgeSessionStatus.RUNNING
    session.started_at = datetime.now()
    db.session.commit()

    # Get worker_count from session config (default: 1)
    worker_count = 1
    if session.config_json:
        worker_count = session.config_json.get('worker_count', 1)

    # Trigger background worker pool
    from workers.judge_worker_pool import trigger_judge_worker_pool
    trigger_judge_worker_pool(session_id, worker_count)

    response = {
        'session_id': session.id,
        'status': 'running',
        'worker_count': worker_count,
        'message': 'Evaluation gestartet'
    }

    if sync_result:
        response['sync_result'] = sync_result

    return jsonify(response)


@session_control_bp.route('/sessions/<int:session_id>/resume', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
def resume_session(session_id: int):
    """
    Resume a session after backend restart or interruption.

    This endpoint:
    1. Resets any "running" comparisons back to "pending"
    2. Restarts the worker pool
    3. Works even if session status is already "running" (handles backend restarts)

    Returns:
        JSON with session status and reset count
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

    # Allow resuming from RUNNING, PAUSED, or QUEUED status
    if session.status not in [JudgeSessionStatus.RUNNING, JudgeSessionStatus.PAUSED, JudgeSessionStatus.QUEUED]:
        raise ValidationError(
            f'Session kann nicht fortgesetzt werden (Status: {session.status.value})'
        )

    # Reset any "running" comparisons back to "pending" (handles interrupted comparisons)
    reset_count = JudgeComparison.query.filter(
        JudgeComparison.session_id == session_id,
        JudgeComparison.status == JudgeComparisonStatus.RUNNING
    ).update({
        'status': JudgeComparisonStatus.PENDING,
        'worker_id': None
    })

    # Also clear any orphaned worker_id assignments
    JudgeComparison.query.filter(
        JudgeComparison.session_id == session_id,
        JudgeComparison.status == JudgeComparisonStatus.PENDING,
        JudgeComparison.worker_id != None
    ).update({'worker_id': None})

    session.status = JudgeSessionStatus.RUNNING
    if not session.started_at:
        session.started_at = datetime.now()
    db.session.commit()

    # Get worker_count from session config (default: 1)
    worker_count = 1
    if session.config_json:
        worker_count = session.config_json.get('worker_count', 1)

    # Trigger background worker pool
    from workers.judge_worker_pool import trigger_judge_worker_pool
    trigger_judge_worker_pool(session_id, worker_count)

    return jsonify({
        'session_id': session.id,
        'status': 'running',
        'worker_count': worker_count,
        'comparisons_reset': reset_count,
        'message': f'Session fortgesetzt, {reset_count} unterbrochene Vergleiche zurückgesetzt'
    })


@session_control_bp.route('/sessions/<int:session_id>/pause', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
def pause_session(session_id: int):
    """
    Pause a running session.

    Returns:
        JSON with session status
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

    if session.status != JudgeSessionStatus.RUNNING:
        raise ValidationError(
            f'Session ist nicht am Laufen (Status: {session.status.value})'
        )

    session.status = JudgeSessionStatus.PAUSED
    db.session.commit()

    # Stop worker pool
    from workers.judge_worker_pool import stop_judge_worker_pool
    stop_judge_worker_pool(session_id)

    return jsonify({
        'session_id': session.id,
        'status': 'paused',
        'message': 'Evaluation pausiert'
    })


@session_control_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
def delete_session(session_id: int):
    """
    Delete a session and all its data.

    Returns:
        JSON confirmation
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

    # Stop worker pool if running
    if session.status == JudgeSessionStatus.RUNNING:
        from workers.judge_worker_pool import stop_judge_worker_pool
        stop_judge_worker_pool(session_id)

    # Delete cascades to comparisons, evaluations, statistics
    db.session.delete(session)
    db.session.commit()

    return jsonify({
        'message': 'Session gelöscht',
        'session_id': session_id
    })
