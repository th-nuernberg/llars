"""Debug routes for LLM-as-Judge sessions.

These endpoints are only available in development mode and require
the System Admin API Key for authentication.

Security: Uses @debug_route_protected which:
- In development: Requires System Admin API Key (X-API-Key header)
- In production: Completely disabled (returns 403)
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from db.db import db
from db.tables import (
    JudgeSession, JudgeSessionStatus,
    JudgeComparisonStatus,
    PillarThread
)
from auth.decorators import debug_route_protected
from decorators.error_handler import handle_api_errors

session_debug_bp = Blueprint('judge_sessions_debug', __name__)


@session_debug_bp.route('/sessions-debug', methods=['GET'])
@debug_route_protected
@handle_api_errors(logger_name='judge_debug')
def list_sessions_debug():
    """
    DEBUG ONLY: List all sessions.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header.
    Only available in development mode.
    """

    sessions = JudgeSession.query.order_by(JudgeSession.created_at.desc()).all()

    result = []
    for s in sessions:
        pillar_count = 0
        if s.config_json and 'pillars' in s.config_json:
            pillar_count = len(s.config_json['pillars'])

        result.append({
            'session_id': s.id,
            'session_name': s.name,
            'status': s.status.value,
            'total_comparisons': s.total_comparisons,
            'completed_comparisons': s.completed_comparisons,
            'progress': (s.completed_comparisons / s.total_comparisons * 100) if s.total_comparisons > 0 else 0,
            'pillar_count': pillar_count,
            'created_at': s.created_at.isoformat() if s.created_at else None,
        })

    return jsonify(result)


@session_debug_bp.route('/sessions-debug', methods=['POST'])
@debug_route_protected
@handle_api_errors(logger_name='judge_debug')
def create_session_debug():
    """
    DEBUG ONLY: Create session.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header.
    Only available in development mode.
    """
    from routes.judge.session_helpers import configure_session_comparisons

    data = request.get_json() or {}

    session_name = data.get('session_name') or data.get('name') or f'Debug Session {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    pillar_ids = data.get('pillar_ids', [])
    comparison_mode = data.get('comparison_mode', 'pillar_sample')
    samples_per_pillar = min(data.get('samples_per_pillar', 10), 50)
    position_swap = data.get('position_swap', True)
    repetitions_per_pair = min(max(data.get('repetitions_per_pair', 1), 1), 5)
    max_threads_per_pillar = data.get('max_threads_per_pillar')
    worker_count = min(max(data.get('worker_count', 1), 1), 5)

    config_json = {
        'pillars': pillar_ids,
        'comparison_mode': comparison_mode,
        'samples_per_pillar': samples_per_pillar,
        'position_swap': position_swap,
        'repetitions_per_pair': repetitions_per_pair,
        'max_threads_per_pillar': max_threads_per_pillar,
        'worker_count': worker_count
    }

    session = JudgeSession(
        user_id='admin',
        name=session_name,
        config_json=config_json,
        status=JudgeSessionStatus.CREATED,
        total_comparisons=0,
        completed_comparisons=0
    )

    db.session.add(session)
    db.session.commit()

    # For free_for_all mode, we only need 1+ pillars
    min_pillars = 1 if comparison_mode == 'free_for_all' else 2

    if pillar_ids and len(pillar_ids) >= min_pillars:
        try:
            configure_session_comparisons(
                session, pillar_ids, comparison_mode, samples_per_pillar,
                position_swap, repetitions_per_pair, max_threads_per_pillar
            )
            db.session.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Auto-configure failed: {e}")
            # Delete the session if configuration failed
            db.session.rollback()
            db.session.delete(session)
            db.session.commit()
            return jsonify({
                'error': 'Configuration failed',
                'message': f'Failed to create comparisons: {str(e)}',
                'hint': 'Database might be busy. Please try again.'
            }), 500

    # Verify comparisons were created
    if session.total_comparisons == 0:
        db.session.delete(session)
        db.session.commit()
        return jsonify({
            'error': 'No comparisons created',
            'message': 'Session would have 0 comparisons. Check pillar selection.',
            'hint': 'Select at least 2 pillars with threads for pillar_sample mode.'
        }), 400

    return jsonify({
        'session_id': session.id,
        'name': session.name,
        'status': session.status.value,
        'total_comparisons': session.total_comparisons,
        'comparison_mode': comparison_mode
    }), 201


@session_debug_bp.route('/sessions/<int:session_id>/start-debug', methods=['POST'])
@debug_route_protected
@handle_api_errors(logger_name='judge_debug')
def start_session_debug(session_id: int):
    """
    DEBUG ONLY: Start session.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header.
    Only available in development mode.
    """
    session = JudgeSession.query.get_or_404(session_id)

    # Reset to QUEUED if needed for restart
    if session.status == JudgeSessionStatus.RUNNING:
        session.status = JudgeSessionStatus.QUEUED
        db.session.commit()

    session.status = JudgeSessionStatus.RUNNING
    session.started_at = datetime.now()
    db.session.commit()

    # Get worker_count from session config (default: 1)
    worker_count = 1
    if session.config_json:
        worker_count = session.config_json.get('worker_count', 1)

    from workers.judge_worker_pool import trigger_judge_worker_pool
    trigger_judge_worker_pool(session_id, worker_count)

    return jsonify({
        'session_id': session.id,
        'status': 'running',
        'worker_count': worker_count,
        'message': 'DEBUG: Evaluation gestartet'
    })
