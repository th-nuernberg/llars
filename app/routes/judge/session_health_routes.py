"""Session health and worker status routes for LLM-as-Judge."""

from flask import Blueprint, jsonify

from db.tables import (
    JudgeSession, JudgeSessionStatus,
    JudgeComparison, JudgeComparisonStatus
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission

session_health_bp = Blueprint('judge_sessions_health', __name__)


@session_health_bp.route('/sessions/<int:session_id>/workers', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_worker_pool_status(session_id: int):
    """
    Get the status of all workers for a session.

    Returns:
        JSON with worker pool status including each worker's current task
    """
    session = JudgeSession.query.get_or_404(session_id)

    from workers.judge_worker_pool import get_pool_status
    pool_status = get_pool_status(session_id)

    if not pool_status:
        # No active pool - return static info from config
        worker_count = 1
        if session.config_json:
            worker_count = session.config_json.get('worker_count', 1)

        return jsonify({
            'session_id': session_id,
            'worker_count': worker_count,
            'running': False,
            'workers': []
        })

    # Enrich worker status with comparison details
    enriched_workers = []
    for worker in pool_status.get('workers', []):
        worker_info = {
            'worker_id': worker['worker_id'],
            'running': worker['running'],
            'current_comparison': None
        }

        if worker.get('current_comparison_id'):
            comparison = JudgeComparison.query.get(worker['current_comparison_id'])
            if comparison:
                worker_info['current_comparison'] = {
                    'id': comparison.id,
                    'thread_a_id': comparison.thread_a_id,
                    'thread_b_id': comparison.thread_b_id,
                    'pillar_a': comparison.pillar_a,
                    'pillar_b': comparison.pillar_b,
                    'position_order': comparison.position_order
                }

        enriched_workers.append(worker_info)

    return jsonify({
        'session_id': session_id,
        'worker_count': pool_status.get('worker_count', 1),
        'running': pool_status.get('running', False),
        'workers': enriched_workers
    })


@session_health_bp.route('/sessions/<int:session_id>/health', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_session_health(session_id: int):
    """
    Get detailed health status of a session.

    This endpoint determines if a session needs recovery:
    - Session status is RUNNING but no worker pool is active
    - There are orphaned RUNNING comparisons (started but never finished)
    - Backend was restarted while session was in progress

    Returns:
        JSON with health status and recovery recommendation
    """
    session = JudgeSession.query.get_or_404(session_id)

    from workers.judge_worker_pool import get_pool_status
    pool_status = get_pool_status(session_id)

    # Count orphaned running comparisons (indicates interrupted work)
    orphaned_running = JudgeComparison.query.filter(
        JudgeComparison.session_id == session_id,
        JudgeComparison.status == JudgeComparisonStatus.RUNNING
    ).count()

    # Count pending comparisons
    pending_count = JudgeComparison.query.filter(
        JudgeComparison.session_id == session_id,
        JudgeComparison.status == JudgeComparisonStatus.PENDING
    ).count()

    # Determine actual running state
    workers_actually_running = False
    if pool_status:
        workers_actually_running = pool_status.get('running', False) and \
            any(w.get('running', False) for w in pool_status.get('workers', []))

    # Health status determination
    needs_recovery = False
    recovery_reason = None

    if session.status == JudgeSessionStatus.RUNNING:
        if not workers_actually_running:
            needs_recovery = True
            recovery_reason = 'workers_stopped'
        elif orphaned_running > 0 and not workers_actually_running:
            needs_recovery = True
            recovery_reason = 'orphaned_comparisons'
    elif session.status == JudgeSessionStatus.PAUSED:
        if orphaned_running > 0:
            needs_recovery = True
            recovery_reason = 'orphaned_comparisons'

    # Determine effective status (what the user should see)
    effective_status = session.status.value
    if session.status == JudgeSessionStatus.RUNNING and not workers_actually_running:
        effective_status = 'interrupted'  # Special status for UI

    return jsonify({
        'session_id': session_id,
        'db_status': session.status.value,
        'effective_status': effective_status,
        'workers_running': workers_actually_running,
        'pending_comparisons': pending_count,
        'orphaned_running': orphaned_running,
        'needs_recovery': needs_recovery,
        'recovery_reason': recovery_reason,
        'completed': session.completed_comparisons,
        'total': session.total_comparisons
    })
