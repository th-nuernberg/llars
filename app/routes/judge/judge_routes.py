"""
LLM-as-Judge API Routes for LLARS.

Provides REST API endpoints for:
- Managing Judge Sessions
- Configuring comparisons
- Starting/pausing evaluations
- Retrieving results and statistics
"""

from datetime import datetime
from typing import List, Optional
import random
from itertools import combinations

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from db.db import db
from db.tables import (
    JudgeSession, JudgeSessionStatus,
    JudgeComparison, JudgeComparisonStatus,
    JudgeEvaluation, JudgeWinner,
    PillarThread, PillarStatistics,
    EmailThread
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission

judge_bp = Blueprint('judge', __name__, url_prefix='/api/judge')


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@judge_bp.route('/sessions-debug', methods=['GET'])
def list_sessions_debug():
    """
    DEBUG ONLY: List all sessions without authentication.
    """
    import os
    if os.environ.get('FLASK_ENV') != 'development':
        return jsonify({'error': 'Debug endpoint disabled'}), 403

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


@judge_bp.route('/estimate', methods=['POST'])
def estimate_comparisons_endpoint():
    """
    Estimate the number of comparisons for a given configuration.

    This endpoint helps the UI show expected workload before creating a session.
    No authentication required for estimation.

    Body:
        pillar_ids: List of pillar IDs [1, 3, 5]
        comparison_mode: 'pillar_sample', 'round_robin', 'free_for_all'
        samples_per_pillar: For pillar_sample mode (default: 10)
        max_threads_per_pillar: Optional thread limit
        position_swap: Whether position swap is enabled (default: true)

    Returns:
        JSON with estimation details including comparison counts and duration estimates
    """
    from services.judge.comparison_generator import ComparisonGenerator

    data = request.get_json() or {}

    pillar_ids = data.get('pillar_ids', [])
    # Support both 'comparison_mode' and 'mode' parameter names
    comparison_mode = data.get('comparison_mode') or data.get('mode', 'pillar_sample')
    samples_per_pillar = min(data.get('samples_per_pillar', 10), 50)
    max_threads_per_pillar = data.get('max_threads_per_pillar')
    position_swap = data.get('position_swap', True)

    if not pillar_ids:
        return jsonify({
            'error': 'pillar_ids is required',
            'total_comparisons': 0
        }), 400

    # Get actual thread counts from database
    pillar_threads = {}
    for pillar in pillar_ids:
        threads = PillarThread.query.filter_by(pillar_number=pillar).all()
        if threads:
            pillar_threads[pillar] = [t.thread_id for t in threads]
        else:
            pillar_threads[pillar] = []

    # Check if we have any threads
    total_threads = sum(len(t) for t in pillar_threads.values())
    if total_threads == 0:
        return jsonify({
            'error': 'No threads available for the selected pillars',
            'total_comparisons': 0,
            'pillars': pillar_ids,
            'threads_per_pillar': {p: 0 for p in pillar_ids}
        }), 200

    # Use the generator to estimate
    generator = ComparisonGenerator()
    estimate = generator.estimate(
        pillar_threads=pillar_threads,
        mode=comparison_mode,
        samples_per_pillar=samples_per_pillar,
        position_swap=position_swap,
        max_threads_per_pillar=max_threads_per_pillar
    )

    return jsonify(estimate)


@judge_bp.route('/comparison-modes', methods=['GET'])
def get_comparison_modes():
    """
    Get available comparison modes with descriptions.

    Returns:
        JSON array of available modes with details
    """
    modes = [
        {
            'id': 'pillar_sample',
            'name': 'Pillar Sample',
            'name_de': 'Säulen-Stichprobe',
            'description': 'Random samples per pillar pair. Fast overview.',
            'description_de': 'Zufällige Stichproben pro Säulen-Paar. Schneller Überblick.',
            'complexity': 'low',
            'recommended_for': 'Quick quality comparison between pillars'
        },
        {
            'id': 'round_robin',
            'name': 'Round Robin',
            'name_de': 'Rundenturnier',
            'description': 'Every thread from pillar A vs every thread from pillar B.',
            'description_de': 'Jeder Thread einer Säule gegen jeden Thread der anderen.',
            'complexity': 'medium',
            'recommended_for': 'Comprehensive pillar comparison with thread-level stats'
        },
        {
            'id': 'free_for_all',
            'name': 'Free For All',
            'name_de': 'Jeder gegen Jeden',
            'description': 'Every thread against every other thread, regardless of pillar.',
            'description_de': 'Jeder Thread gegen jeden anderen Thread, unabhängig von Säule.',
            'complexity': 'high',
            'recommended_for': 'Complete thread ranking, ELO scores, finding best/worst threads'
        }
    ]
    return jsonify(modes)


@judge_bp.route('/sessions', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def list_sessions():
    """
    List all Judge sessions for the current user.

    Returns:
        JSON array of session objects with progress info
    """
    username = g.authentik_user

    sessions = JudgeSession.query.filter_by(
        user_id=username
    ).order_by(JudgeSession.created_at.desc()).all()

    # Calculate pillar counts from config
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
            'progress': (s.completed_comparisons / s.total_comparisons * 100)
                        if s.total_comparisons > 0 else 0,
            'pillar_count': pillar_count,
            'current_comparison_id': s.current_comparison_id,
            'created_at': s.created_at.isoformat() if s.created_at else None,
            'started_at': s.started_at.isoformat() if s.started_at else None,
            'completed_at': s.completed_at.isoformat() if s.completed_at else None,
            'config': s.config_json
        })

    return jsonify(result)


@judge_bp.route('/sessions/<int:session_id>', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_session(session_id: int):
    """
    Get details of a specific session.

    Args:
        session_id: ID of the session

    Returns:
        JSON object with session details
    """
    session = JudgeSession.query.get_or_404(session_id)

    # Get current comparison if running
    current_comparison = None
    if session.current_comparison_id:
        comp = JudgeComparison.query.get(session.current_comparison_id)
        if comp:
            current_comparison = {
                'id': comp.id,
                'thread_a_id': comp.thread_a_id,
                'thread_b_id': comp.thread_b_id,
                'pillar_a': comp.pillar_a,
                'pillar_b': comp.pillar_b,
                'status': comp.status.value
            }

    return jsonify({
        'id': session.id,
        'name': session.name,
        'status': session.status.value,
        'total_comparisons': session.total_comparisons,
        'completed_comparisons': session.completed_comparisons,
        'progress': (session.completed_comparisons / session.total_comparisons * 100)
                    if session.total_comparisons > 0 else 0,
        'current_comparison': current_comparison,
        'config': session.config_json,
        'created_at': session.created_at.isoformat() if session.created_at else None,
        'started_at': session.started_at.isoformat() if session.started_at else None,
        'completed_at': session.completed_at.isoformat() if session.completed_at else None
    })


@judge_bp.route('/sessions-debug', methods=['POST'])
def create_session_debug():
    """
    DEBUG ONLY: Create session without authentication.
    Remove in production!
    """
    import os
    if os.environ.get('FLASK_ENV') != 'development':
        return jsonify({'error': 'Debug endpoint disabled'}), 403

    data = request.get_json() or {}

    session_name = data.get('session_name') or data.get('name') or f'Debug Session {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    pillar_ids = data.get('pillar_ids', [])
    comparison_mode = data.get('comparison_mode', 'pillar_sample')  # New default
    samples_per_pillar = min(data.get('samples_per_pillar', 10), 50)
    position_swap = data.get('position_swap', True)
    repetitions_per_pair = min(max(data.get('repetitions_per_pair', 1), 1), 5)
    max_threads_per_pillar = data.get('max_threads_per_pillar')  # Optional limit
    worker_count = min(max(data.get('worker_count', 1), 1), 5)  # 1-5 workers

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
            _configure_session_comparisons(
                session, pillar_ids, comparison_mode, samples_per_pillar,
                position_swap, repetitions_per_pair, max_threads_per_pillar
            )
            db.session.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Auto-configure failed: {e}")
            db.session.rollback()

    return jsonify({
        'session_id': session.id,
        'name': session.name,
        'status': session.status.value,
        'total_comparisons': session.total_comparisons,
        'comparison_mode': comparison_mode
    }), 201


@judge_bp.route('/sessions', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def create_session():
    """
    Create a new Judge session with optional configuration.

    Body:
        name OR session_name: Session name
        pillar_ids: List of pillar IDs to include [1, 2, 3, 4, 5]
        comparison_mode: 'pillar_sample', 'round_robin', 'free_for_all' (default: pillar_sample)
        samples_per_pillar: Number of threads per pillar for pillar_sample (default: 10)
        max_threads_per_pillar: Optional limit on threads per pillar (for round_robin/free_for_all)
        position_swap: Whether to run position-swap (default: true)
        repetitions_per_pair: How many times each pair is compared (default: 1, max: 5)
        worker_count: Number of parallel workers (default: 1, max: 5)

    Returns:
        JSON with created session ID
    """
    data = request.get_json() or {}
    username = g.authentik_user

    # Support both 'name' and 'session_name' for flexibility
    session_name = data.get('session_name') or data.get('name') or f'Evaluation {datetime.now().strftime("%Y-%m-%d %H:%M")}'

    # Extract configuration from request
    pillar_ids = data.get('pillar_ids', [])
    comparison_mode = data.get('comparison_mode', 'pillar_sample')
    samples_per_pillar = min(data.get('samples_per_pillar', 10), 50)
    max_threads_per_pillar = data.get('max_threads_per_pillar')
    position_swap = data.get('position_swap', True)
    repetitions_per_pair = min(max(data.get('repetitions_per_pair', 1), 1), 5)
    worker_count = min(max(data.get('worker_count', 1), 1), 5)

    # Build config JSON
    config_json = {
        'pillars': pillar_ids,
        'comparison_mode': comparison_mode,
        'samples_per_pillar': samples_per_pillar,
        'max_threads_per_pillar': max_threads_per_pillar,
        'position_swap': position_swap,
        'repetitions_per_pair': repetitions_per_pair,
        'worker_count': worker_count
    }

    session = JudgeSession(
        user_id=username,
        name=session_name,
        config_json=config_json,
        status=JudgeSessionStatus.CREATED,
        total_comparisons=0,
        completed_comparisons=0
    )

    db.session.add(session)
    db.session.commit()

    # For free_for_all mode, we only need 1+ pillars (can compare within same pillar)
    min_pillars = 1 if comparison_mode == 'free_for_all' else 2

    if pillar_ids and len(pillar_ids) >= min_pillars:
        try:
            _configure_session_comparisons(
                session, pillar_ids, comparison_mode, samples_per_pillar,
                position_swap, repetitions_per_pair, max_threads_per_pillar
            )
            db.session.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Auto-configure failed: {e}")

    return jsonify({
        'session_id': session.id,
        'id': session.id,
        'name': session.name,
        'status': session.status.value,
        'total_comparisons': session.total_comparisons,
        'comparison_mode': comparison_mode
    }), 201


def _configure_session_comparisons(
    session,
    pillars,
    comparison_mode,
    samples_per_pillar,
    position_swap,
    repetitions_per_pair=1,
    max_threads_per_pillar=None
):
    """
    Helper to configure session comparisons using the ComparisonGenerator.

    Supports three modes:
    - pillar_sample (default): Random samples per pillar pair
    - round_robin: All threads of pillar A vs all threads of pillar B
    - free_for_all: Every thread against every other thread

    Args:
        session: JudgeSession object
        pillars: List of pillar numbers
        comparison_mode: 'pillar_sample', 'round_robin', 'free_for_all', or 'all_pairs' (legacy)
        samples_per_pillar: Number of samples for pillar_sample mode
        position_swap: Whether to create A|B and B|A versions
        repetitions_per_pair: Number of repetitions (only for pillar_sample)
        max_threads_per_pillar: Optional limit on threads per pillar
    """
    from services.judge.comparison_generator import ComparisonGenerator
    import logging

    logger = logging.getLogger(__name__)

    # Get threads for each pillar
    pillar_threads = {}
    for pillar in pillars:
        threads = PillarThread.query.filter_by(pillar_number=pillar).all()
        if threads:
            pillar_threads[pillar] = [t.thread_id for t in threads]

    if not pillar_threads:
        logger.warning("No threads available for any pillar")
        return

    # Use the new ComparisonGenerator
    generator = ComparisonGenerator()

    result = generator.generate(
        pillar_threads=pillar_threads,
        mode=comparison_mode,
        samples_per_pillar=samples_per_pillar,
        position_swap=position_swap,
        max_threads_per_pillar=max_threads_per_pillar,
        repetitions=repetitions_per_pair
    )

    # Create JudgeComparison objects from the generated pairs
    comparisons = []
    for idx, pair in enumerate(result.comparisons):
        comp = JudgeComparison(
            session_id=session.id,
            thread_a_id=pair.thread_a_id,
            thread_b_id=pair.thread_b_id,
            pillar_a=pair.pillar_a,
            pillar_b=pair.pillar_b,
            position_order=pair.position_order,
            queue_position=idx,
            status=JudgeComparisonStatus.PENDING
        )
        comparisons.append(comp)

    # Bulk insert for efficiency
    db.session.bulk_save_objects(comparisons)

    # Update session
    session.total_comparisons = len(comparisons)
    session.status = JudgeSessionStatus.QUEUED

    logger.info(
        f"Configured session {session.id} with {len(comparisons)} comparisons "
        f"using {result.mode.value} mode"
    )


@judge_bp.route('/sessions/<int:session_id>/configure', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def configure_session(session_id: int):
    """
    Configure which pillars to compare in the session.

    Body:
        pillars: List of pillar numbers to include [1, 2, 3, 4, 5]
        comparison_mode: "all_pairs" or "specific"
        specific_pairs: Optional list of pairs [[1,3], [2,4]]
        samples_per_pillar: Number of threads per pillar (default: 10)
        position_swap: Whether to run position-swap (default: true)

    Returns:
        JSON with configuration summary
    """
    session = JudgeSession.query.get_or_404(session_id)

    if session.status not in [JudgeSessionStatus.CREATED, JudgeSessionStatus.QUEUED]:
        return jsonify({
            'error': 'Session kann nicht mehr konfiguriert werden',
            'status': session.status.value
        }), 400

    data = request.get_json()

    pillars = data.get('pillars', [1, 2, 3, 4, 5])
    comparison_mode = data.get('comparison_mode', 'all_pairs')
    specific_pairs = data.get('specific_pairs', [])
    samples_per_pillar = min(data.get('samples_per_pillar', 10), 50)  # Max 50
    position_swap = data.get('position_swap', True)

    # Generate comparison pairs
    if comparison_mode == 'all_pairs':
        # All unique pairs of pillars
        pairs = list(combinations(sorted(pillars), 2))
    else:
        # Specific pairs
        pairs = [(min(p), max(p)) for p in specific_pairs if len(p) == 2]

    # Get threads for each pillar
    pillar_threads = {}
    for pillar in pillars:
        threads = PillarThread.query.filter_by(pillar_number=pillar).all()
        if threads:
            pillar_threads[pillar] = [t.thread_id for t in threads]
        else:
            # If no PillarThread mappings, use some EmailThreads as fallback
            all_threads = EmailThread.query.limit(samples_per_pillar).all()
            pillar_threads[pillar] = [t.id for t in all_threads]

    # Create comparisons
    comparisons = []
    queue_position = 0

    for pillar_a, pillar_b in pairs:
        threads_a = pillar_threads.get(pillar_a, [])
        threads_b = pillar_threads.get(pillar_b, [])

        if not threads_a or not threads_b:
            continue

        # Sample threads
        sample_a = random.sample(threads_a, min(len(threads_a), samples_per_pillar))
        sample_b = random.sample(threads_b, min(len(threads_b), samples_per_pillar))

        # Create pairs (zip for equal matching)
        for ta, tb in zip(sample_a, sample_b):
            # First comparison: A | B
            comparisons.append(JudgeComparison(
                session_id=session.id,
                thread_a_id=ta,
                thread_b_id=tb,
                pillar_a=pillar_a,
                pillar_b=pillar_b,
                position_order=1,
                status=JudgeComparisonStatus.PENDING,
                queue_position=queue_position
            ))
            queue_position += 1

            # Second comparison: B | A (position swap)
            if position_swap:
                comparisons.append(JudgeComparison(
                    session_id=session.id,
                    thread_a_id=tb,
                    thread_b_id=ta,
                    pillar_a=pillar_b,
                    pillar_b=pillar_a,
                    position_order=2,
                    status=JudgeComparisonStatus.PENDING,
                    queue_position=queue_position
                ))
                queue_position += 1

    # Save comparisons
    db.session.bulk_save_objects(comparisons)

    # Update session
    session.config_json = {
        'pillars': pillars,
        'comparison_mode': comparison_mode,
        'specific_pairs': specific_pairs,
        'samples_per_pillar': samples_per_pillar,
        'position_swap': position_swap
    }
    session.total_comparisons = len(comparisons)
    session.status = JudgeSessionStatus.QUEUED

    # Initialize statistics
    for pillar_a, pillar_b in pairs:
        stat = PillarStatistics(
            session_id=session.id,
            pillar_a=pillar_a,
            pillar_b=pillar_b,
            wins_a=0,
            wins_b=0,
            ties=0
        )
        db.session.add(stat)

    db.session.commit()

    return jsonify({
        'session_id': session.id,
        'total_comparisons': len(comparisons),
        'pillar_pairs': pairs,
        'status': 'queued'
    })


@judge_bp.route('/sessions/<int:session_id>/start-debug', methods=['POST'])
def start_session_debug(session_id: int):
    """
    DEBUG ONLY: Start session without authentication.
    Remove in production!
    """
    import os
    if os.environ.get('FLASK_ENV') != 'development':
        return jsonify({'error': 'Debug endpoint disabled'}), 403

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


@judge_bp.route('/sessions/<int:session_id>/start', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def start_session(session_id: int):
    """
    Start processing the session queue.

    Query params:
        auto_sync: If 'true', sync KIA data before starting

    Returns:
        JSON with session status
    """
    session = JudgeSession.query.get_or_404(session_id)

    # Allow starting from CREATED, QUEUED, or PAUSED status
    if session.status not in [JudgeSessionStatus.CREATED, JudgeSessionStatus.QUEUED, JudgeSessionStatus.PAUSED]:
        return jsonify({
            'error': f'Session kann nicht gestartet werden (Status: {session.status.value})'
        }), 400

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


@judge_bp.route('/sessions/<int:session_id>/resume', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
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
    session = JudgeSession.query.get_or_404(session_id)

    # Allow resuming from RUNNING, PAUSED, or QUEUED status
    if session.status not in [JudgeSessionStatus.RUNNING, JudgeSessionStatus.PAUSED, JudgeSessionStatus.QUEUED]:
        return jsonify({
            'error': f'Session kann nicht fortgesetzt werden (Status: {session.status.value})'
        }), 400

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


@judge_bp.route('/sessions/<int:session_id>/pause', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def pause_session(session_id: int):
    """
    Pause a running session.

    Returns:
        JSON with session status
    """
    session = JudgeSession.query.get_or_404(session_id)

    if session.status != JudgeSessionStatus.RUNNING:
        return jsonify({
            'error': f'Session ist nicht am Laufen (Status: {session.status.value})'
        }), 400

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


@judge_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@authentik_required
@require_permission('feature:comparison:edit')
def delete_session(session_id: int):
    """
    Delete a session and all its data.

    Returns:
        JSON confirmation
    """
    session = JudgeSession.query.get_or_404(session_id)

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


@judge_bp.route('/sessions/<int:session_id>/workers', methods=['GET'])
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


@judge_bp.route('/sessions/<int:session_id>/health', methods=['GET'])
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


# ============================================================================
# CURRENT COMPARISON & LIVE VIEW
# ============================================================================

@judge_bp.route('/sessions/<int:session_id>/current', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_current_comparison(session_id: int):
    """
    Get the currently running comparison with thread data.

    Returns:
        JSON with current comparison and thread contents in frontend-compatible format
    """
    session = JudgeSession.query.get_or_404(session_id)

    if not session.current_comparison_id:
        return jsonify(None)

    comparison = JudgeComparison.query.get(session.current_comparison_id)
    if not comparison:
        return jsonify(None)

    # Pillar names for display
    pillar_names = {
        1: "Rollenspiele",
        2: "Feature Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch",
        5: "Live-Test"
    }

    # Load thread messages
    thread_a_messages = _load_thread_messages(comparison.thread_a_id)
    thread_b_messages = _load_thread_messages(comparison.thread_b_id)

    # Get evaluation if exists
    evaluation = JudgeEvaluation.query.filter_by(comparison_id=comparison.id).first()

    # Generate the prompt that will be/was sent to the LLM
    from services.judge.judge_service import JudgeService
    judge_service = JudgeService.__new__(JudgeService)
    judge_service.PILLAR_NAMES = pillar_names

    # Format thread content for prompt display
    def format_messages_for_display(messages):
        lines = []
        for i, msg in enumerate(messages, 1):
            role = "BERATER" if msg.get('role') == 'assistant' else "RATSUCHENDE"
            lines.append(f"[Nachricht {i} - {role}]:")
            lines.append(msg.get('content', '').strip()[:500])
            lines.append("")
        return "\n".join(lines)

    thread_a_formatted = format_messages_for_display(thread_a_messages)
    thread_b_formatted = format_messages_for_display(thread_b_messages)

    # Build the actual prompt sent to LLM
    llm_prompt = f"""Vergleiche die folgenden zwei E-Mail-Beratungsverläufe und bestimme, welcher qualitativ besser ist.

=== VERLAUF A (Säule {comparison.pillar_a}: {pillar_names.get(comparison.pillar_a, f'Säule {comparison.pillar_a}')}) ===

{thread_a_formatted}

=== VERLAUF B (Säule {comparison.pillar_b}: {pillar_names.get(comparison.pillar_b, f'Säule {comparison.pillar_b}')}) ===

{thread_b_formatted}

---

Führe nun eine detaillierte Bewertung durch:
1. Analysiere beide Verläufe im Chain-of-Thought
2. Bewerte jedes der 6 Kriterien für beide Verläufe (1-5)
3. Bestimme den Gewinner (A, B, oder TIE)

Antworte NUR mit einem validen JSON-Objekt gemäß dem Schema."""

    result = {
        'comparison_id': comparison.id,
        'comparison_index': comparison.queue_position,
        'thread_a_id': comparison.thread_a_id,
        'thread_b_id': comparison.thread_b_id,
        'thread_a_messages': thread_a_messages,
        'thread_b_messages': thread_b_messages,
        'pillar_a': comparison.pillar_a,
        'pillar_b': comparison.pillar_b,
        'pillar_a_name': pillar_names.get(comparison.pillar_a, f'Säule {comparison.pillar_a}'),
        'pillar_b_name': pillar_names.get(comparison.pillar_b, f'Säule {comparison.pillar_b}'),
        'position_order': comparison.position_order,
        'status': comparison.status.value,
        'llm_status': 'completed' if evaluation else ('running' if comparison.status == JudgeComparisonStatus.RUNNING else 'pending'),
        'llm_prompt': llm_prompt,
        'llm_system_prompt': """Du bist ein Experte für die Bewertung von Beratungsgesprächen im Kontext psychologischer Online-Beratung.
Deine Aufgabe ist es, zwei E-Mail-Verläufe zwischen Beratenden und Ratsuchenden zu vergleichen und zu bewerten."""
    }

    if evaluation:
        result['winner'] = evaluation.winner.value if evaluation.winner else None
        result['confidence_score'] = evaluation.confidence
        result['reasoning'] = evaluation.reasoning
        # Add chain of thought if available
        if evaluation.evaluation_json:
            cot = evaluation.evaluation_json.get('chain_of_thought', {})
            result['chain_of_thought'] = [
                {'step_name': 'Überblick', 'reasoning': cot.get('step_1_overview', '')},
                {'step_name': 'Stärken A', 'reasoning': cot.get('step_2_strengths_a', '')},
                {'step_name': 'Stärken B', 'reasoning': cot.get('step_3_strengths_b', '')},
                {'step_name': 'Schwächen A', 'reasoning': cot.get('step_4_weaknesses_a', '')},
                {'step_name': 'Schwächen B', 'reasoning': cot.get('step_5_weaknesses_b', '')},
                {'step_name': 'Vergleich', 'reasoning': cot.get('step_6_comparison', '')}
            ]

    return jsonify(result)


def _load_thread_messages(thread_id: int):
    """Load messages for a thread in frontend-compatible format."""
    from db.tables import Message, EmailThread

    messages = Message.query.filter_by(
        thread_id=thread_id
    ).order_by(Message.timestamp).all()

    return [{
        'role': 'assistant' if getattr(msg, 'is_counsellor', False) or 'berater' in (msg.sender or '').lower() else 'user',
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
    } for msg in messages]


@judge_bp.route('/sessions/<int:session_id>/queue', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_session_queue(session_id: int):
    """
    Get the pending comparisons queue for a session.

    Returns:
        JSON with pending and running comparisons, plus summary stats
    """
    session = JudgeSession.query.get_or_404(session_id)

    # Pillar names
    pillar_names = {
        1: "Rollenspiele",
        2: "Feature Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch",
        5: "Live-Test"
    }

    # Get pending and running comparisons
    pending = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.PENDING
    ).order_by(JudgeComparison.queue_position).all()

    running = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.RUNNING
    ).first()

    completed_count = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.COMPLETED
    ).count()

    failed_count = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.FAILED
    ).count()

    def format_comparison(comp, idx=None):
        return {
            'comparison_id': comp.id,
            'queue_position': comp.queue_position,
            'pillar_a': comp.pillar_a,
            'pillar_b': comp.pillar_b,
            'pillar_a_name': pillar_names.get(comp.pillar_a, f'Säule {comp.pillar_a}'),
            'pillar_b_name': pillar_names.get(comp.pillar_b, f'Säule {comp.pillar_b}'),
            'position_order': comp.position_order,
            'status': comp.status.value
        }

    return jsonify({
        'session_id': session_id,
        'session_status': session.status.value,
        'current': format_comparison(running) if running else None,
        'pending': [format_comparison(c) for c in pending],
        'stats': {
            'total': session.total_comparisons,
            'pending': len(pending),
            'running': 1 if running else 0,
            'completed': completed_count,
            'failed': failed_count,
            'progress_percent': round((completed_count / session.total_comparisons * 100) if session.total_comparisons > 0 else 0, 1)
        }
    })


@judge_bp.route('/sessions/<int:session_id>/comparisons', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_session_comparisons(session_id: int):
    """
    Get all comparisons for a session with their evaluation status.

    Returns:
        JSON array of comparisons with pillar info and results
    """
    session = JudgeSession.query.get_or_404(session_id)

    # Pillar names for display
    pillar_names = {
        1: "Rollenspiele",
        2: "Feature Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch",
        5: "Live-Test"
    }

    comparisons = JudgeComparison.query.filter_by(
        session_id=session_id
    ).order_by(JudgeComparison.queue_position).all()

    results = []
    for idx, comp in enumerate(comparisons):
        # Get evaluation if completed
        evaluation = JudgeEvaluation.query.filter_by(
            comparison_id=comp.id
        ).first()

        result = {
            'comparison_id': comp.id,
            'comparison_index': idx,
            'thread_a_id': comp.thread_a_id,
            'thread_b_id': comp.thread_b_id,
            'pillar_a': comp.pillar_a,
            'pillar_b': comp.pillar_b,
            'pillar_a_name': pillar_names.get(comp.pillar_a, f'Säule {comp.pillar_a}'),
            'pillar_b_name': pillar_names.get(comp.pillar_b, f'Säule {comp.pillar_b}'),
            'position_order': comp.position_order,
            'status': comp.status.value,
            'started_at': comp.started_at.isoformat() if comp.started_at else None,
            'completed_at': comp.completed_at.isoformat() if comp.completed_at else None
        }

        if evaluation:
            result['winner'] = evaluation.winner.value if evaluation.winner else None
            result['confidence_score'] = evaluation.confidence
            result['reasoning'] = evaluation.reasoning
            result['evaluated_at'] = evaluation.created_at.isoformat() if evaluation.created_at else None
            result['raw_response'] = evaluation.raw_response
            result['scores'] = {
                'counsellor_coherence': {'a': evaluation.counsellor_coherence_a, 'b': evaluation.counsellor_coherence_b},
                'client_coherence': {'a': evaluation.client_coherence_a, 'b': evaluation.client_coherence_b},
                'quality': {'a': evaluation.quality_a, 'b': evaluation.quality_b},
                'empathy': {'a': evaluation.empathy_a, 'b': evaluation.empathy_b},
                'authenticity': {'a': evaluation.authenticity_a, 'b': evaluation.authenticity_b},
                'solution_orientation': {'a': evaluation.solution_orientation_a, 'b': evaluation.solution_orientation_b}
            }

        results.append(result)

    return jsonify(results)


def _load_thread_preview(thread_id: int) -> dict:
    """Load thread with messages for preview."""
    from db.tables import EmailThread, EmailMessage

    thread = EmailThread.query.get(thread_id)
    if not thread:
        return {'id': thread_id, 'subject': 'Nicht gefunden', 'messages': []}

    messages = EmailMessage.query.filter_by(
        thread_id=thread_id
    ).order_by(EmailMessage.timestamp).all()

    return {
        'id': thread_id,
        'subject': thread.subject if hasattr(thread, 'subject') else f'Thread {thread_id}',
        'messages': [{
            'id': msg.id,
            'content': msg.content[:500] + '...' if len(msg.content) > 500 else msg.content,
            'is_counsellor': msg.is_counsellor if hasattr(msg, 'is_counsellor') else False,
            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
        } for msg in messages]
    }


# ============================================================================
# RESULTS & STATISTICS
# ============================================================================

@judge_bp.route('/sessions/<int:session_id>/results', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_session_results(session_id: int):
    """
    Get aggregated results for a session.

    Returns:
        JSON with pillar_metrics, win_matrix, and total_comparisons
    """
    session = JudgeSession.query.get_or_404(session_id)

    # Pillar names for display
    pillar_names = {
        1: "Rollenspiele",
        2: "Feature Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch",
        5: "Live-Test"
    }

    # Get all pillar statistics
    stats = PillarStatistics.query.filter_by(session_id=session_id).all()

    # Build win matrix and calculate pillar metrics
    win_matrix = {}
    pillar_wins = {}  # pillar -> wins
    pillar_losses = {}  # pillar -> losses
    pillar_total = {}  # pillar -> total comparisons
    pillar_confidence_sum = {}  # pillar -> sum of confidence
    pillar_confidence_count = {}  # pillar -> count

    for s in stats:
        # Win matrix keys
        key_a_vs_b = f"{s.pillar_a}_vs_{s.pillar_b}"
        key_b_vs_a = f"{s.pillar_b}_vs_{s.pillar_a}"

        win_matrix[key_a_vs_b] = s.wins_a
        win_matrix[key_b_vs_a] = s.wins_b

        # Aggregate wins/losses per pillar
        pillar_wins[s.pillar_a] = pillar_wins.get(s.pillar_a, 0) + s.wins_a
        pillar_wins[s.pillar_b] = pillar_wins.get(s.pillar_b, 0) + s.wins_b
        pillar_losses[s.pillar_a] = pillar_losses.get(s.pillar_a, 0) + s.wins_b
        pillar_losses[s.pillar_b] = pillar_losses.get(s.pillar_b, 0) + s.wins_a

        total = s.wins_a + s.wins_b + s.ties
        pillar_total[s.pillar_a] = pillar_total.get(s.pillar_a, 0) + total
        pillar_total[s.pillar_b] = pillar_total.get(s.pillar_b, 0) + total

        if s.avg_confidence:
            pillar_confidence_sum[s.pillar_a] = pillar_confidence_sum.get(s.pillar_a, 0) + s.avg_confidence
            pillar_confidence_sum[s.pillar_b] = pillar_confidence_sum.get(s.pillar_b, 0) + s.avg_confidence
            pillar_confidence_count[s.pillar_a] = pillar_confidence_count.get(s.pillar_a, 0) + 1
            pillar_confidence_count[s.pillar_b] = pillar_confidence_count.get(s.pillar_b, 0) + 1

    # Build pillar_metrics array
    all_pillars = set(pillar_wins.keys()) | set(pillar_losses.keys())
    pillar_metrics = []

    for pillar in all_pillars:
        wins = pillar_wins.get(pillar, 0)
        losses = pillar_losses.get(pillar, 0)
        total = pillar_total.get(pillar, 0)
        conf_sum = pillar_confidence_sum.get(pillar, 0)
        conf_count = pillar_confidence_count.get(pillar, 1)

        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.5
        avg_conf = conf_sum / conf_count if conf_count > 0 else 0.5
        score = (win_rate * 0.7 + avg_conf * 0.3) * 5  # Score 0-5

        pillar_metrics.append({
            'pillar': pillar,
            'name': pillar_names.get(pillar, f'Säule {pillar}'),
            'wins': wins,
            'losses': losses,
            'total_comparisons': total,
            'win_rate': win_rate,
            'avg_confidence': avg_conf,
            'score': score
        })

    # Sort by score descending
    pillar_metrics.sort(key=lambda x: x['score'], reverse=True)

    return jsonify({
        'session_id': session_id,
        'session_name': session.name,
        'total_comparisons': session.total_comparisons,
        'completed_comparisons': session.completed_comparisons,
        'pillar_metrics': pillar_metrics,
        'win_matrix': win_matrix
    })


@judge_bp.route('/sessions/<int:session_id>/statistics', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_pillar_statistics(session_id: int):
    """
    Get aggregated pillar statistics for a session.

    Returns:
        JSON with pillar matrix and overall stats
    """
    stats = PillarStatistics.query.filter_by(session_id=session_id).all()

    # Build matrix
    matrix = {}
    overall = {
        'total_comparisons': 0,
        'total_ties': 0,
        'pillar_wins': {}  # pillar -> total wins
    }

    for s in stats:
        key = f"{s.pillar_a}_vs_{s.pillar_b}"
        total = s.wins_a + s.wins_b + s.ties

        matrix[key] = {
            'pillar_a': s.pillar_a,
            'pillar_b': s.pillar_b,
            'wins_a': s.wins_a,
            'wins_b': s.wins_b,
            'ties': s.ties,
            'total': total,
            'win_rate_a': (s.wins_a / total * 100) if total > 0 else 0,
            'win_rate_b': (s.wins_b / total * 100) if total > 0 else 0,
            'avg_confidence': s.avg_confidence
        }

        # Aggregate
        overall['total_comparisons'] += total
        overall['total_ties'] += s.ties
        overall['pillar_wins'][s.pillar_a] = overall['pillar_wins'].get(s.pillar_a, 0) + s.wins_a
        overall['pillar_wins'][s.pillar_b] = overall['pillar_wins'].get(s.pillar_b, 0) + s.wins_b

    # Sort pillars by total wins
    pillar_ranking = sorted(
        overall['pillar_wins'].items(),
        key=lambda x: x[1],
        reverse=True
    )

    return jsonify({
        'matrix': matrix,
        'overall': overall,
        'pillar_ranking': [{'pillar': p, 'wins': w} for p, w in pillar_ranking]
    })


@judge_bp.route('/sessions/<int:session_id>/verbosity-analysis', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_verbosity_analysis(session_id: int):
    """
    Analyze verbosity bias - do longer threads win more often?

    Returns:
        JSON with verbosity bias metrics
    """
    from db.tables import Message

    session = JudgeSession.query.get_or_404(session_id)

    # Get all completed comparisons with evaluations
    comparisons = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.COMPLETED
    ).all()

    if not comparisons:
        return jsonify({
            'session_id': session_id,
            'total_analyzed': 0,
            'longer_wins': 0,
            'shorter_wins': 0,
            'ties': 0,
            'verbosity_bias_rate': 0,
            'avg_length_winner': 0,
            'avg_length_loser': 0,
            'comparisons': []
        })

    # Calculate thread lengths and analyze
    results = []
    longer_wins = 0
    shorter_wins = 0
    ties = 0
    winner_lengths = []
    loser_lengths = []

    for comp in comparisons:
        # Get evaluation
        evaluation = JudgeEvaluation.query.filter_by(comparison_id=comp.id).first()
        if not evaluation:
            continue

        # Calculate thread lengths (character count of all messages)
        messages_a = Message.query.filter_by(thread_id=comp.thread_a_id).all()
        messages_b = Message.query.filter_by(thread_id=comp.thread_b_id).all()

        length_a = sum(len(m.content or '') for m in messages_a)
        length_b = sum(len(m.content or '') for m in messages_b)

        # Determine winner and verbosity relationship
        winner = evaluation.winner.value if evaluation.winner else None

        if winner == 'A':
            if length_a > length_b:
                longer_wins += 1
                winner_lengths.append(length_a)
                loser_lengths.append(length_b)
            elif length_b > length_a:
                shorter_wins += 1
                winner_lengths.append(length_a)
                loser_lengths.append(length_b)
            else:
                ties += 1
        elif winner == 'B':
            if length_b > length_a:
                longer_wins += 1
                winner_lengths.append(length_b)
                loser_lengths.append(length_a)
            elif length_a > length_b:
                shorter_wins += 1
                winner_lengths.append(length_b)
                loser_lengths.append(length_a)
            else:
                ties += 1
        else:  # TIE
            ties += 1

        results.append({
            'comparison_id': comp.id,
            'thread_a_length': length_a,
            'thread_b_length': length_b,
            'winner': winner,
            'longer_thread': 'A' if length_a > length_b else ('B' if length_b > length_a else 'TIE'),
            'longer_won': (winner == 'A' and length_a > length_b) or (winner == 'B' and length_b > length_a)
        })

    total = longer_wins + shorter_wins + ties
    verbosity_bias_rate = longer_wins / total if total > 0 else 0

    return jsonify({
        'session_id': session_id,
        'total_analyzed': total,
        'longer_wins': longer_wins,
        'shorter_wins': shorter_wins,
        'ties': ties,
        'verbosity_bias_rate': verbosity_bias_rate,
        'avg_length_winner': sum(winner_lengths) / len(winner_lengths) if winner_lengths else 0,
        'avg_length_loser': sum(loser_lengths) / len(loser_lengths) if loser_lengths else 0,
        'comparisons': results
    })


@judge_bp.route('/sessions/<int:session_id>/thread-performance', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_thread_performance(session_id: int):
    """
    Analyze individual thread performance across all comparisons.

    Returns:
        - Per-thread statistics (wins, losses, ties, usage count)
        - Threads ranked by performance (consistent winners/losers)
        - Likert scale consistency analysis per thread
        - Can be used to validate if LLM ratings are consistent

    This helps identify:
    1. Threads that consistently lose (might be low quality)
    2. Threads that consistently win (might be high quality)
    3. Threads used frequently vs. rarely (sampling coverage)
    4. Threads with consistent vs. inconsistent Likert ratings
    """
    from collections import defaultdict
    import statistics
    from db.tables import EmailThread

    session = JudgeSession.query.get_or_404(session_id)

    # Get all completed comparisons
    comparisons = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.COMPLETED
    ).all()

    if not comparisons:
        return jsonify({
            'session_id': session_id,
            'total_threads': 0,
            'threads': [],
            'pillar_summary': {},
            'likert_consistency': {}
        })

    # Likert metrics we track
    LIKERT_METRICS = ['counsellor_coherence', 'client_coherence', 'quality', 'empathy', 'authenticity', 'solution_orientation']

    # Track thread statistics
    thread_stats = defaultdict(lambda: {
        'thread_id': None,
        'pillar': None,
        'usage_count': 0,
        'wins': 0,
        'losses': 0,
        'ties': 0,
        'opponents': [],
        'opponents_beaten': [],
        'opponents_lost_to': [],
        # Likert scores across all comparisons
        'likert_scores': {metric: [] for metric in LIKERT_METRICS}
    })

    for comp in comparisons:
        # evaluations is a list - get the first (latest) evaluation
        if not comp.evaluations:
            continue

        eval_data = comp.evaluations[0]  # Get first evaluation
        # winner is a JudgeWinner Enum - get string value for comparison
        winner = eval_data.winner.value if hasattr(eval_data.winner, 'value') else str(eval_data.winner)  # 'A', 'B', or 'TIE'

        thread_a = comp.thread_a_id
        thread_b = comp.thread_b_id
        pillar_a = comp.pillar_a
        pillar_b = comp.pillar_b

        # Initialize thread entries
        if thread_stats[thread_a]['thread_id'] is None:
            thread_stats[thread_a]['thread_id'] = thread_a
            thread_stats[thread_a]['pillar'] = pillar_a
            thread_stats[thread_a]['likert_scores'] = {metric: [] for metric in LIKERT_METRICS}

        if thread_stats[thread_b]['thread_id'] is None:
            thread_stats[thread_b]['thread_id'] = thread_b
            thread_stats[thread_b]['pillar'] = pillar_b
            thread_stats[thread_b]['likert_scores'] = {metric: [] for metric in LIKERT_METRICS}

        # Count usage
        thread_stats[thread_a]['usage_count'] += 1
        thread_stats[thread_b]['usage_count'] += 1

        # Track opponents
        thread_stats[thread_a]['opponents'].append(thread_b)
        thread_stats[thread_b]['opponents'].append(thread_a)

        # Collect Likert scores for Thread A
        for metric in LIKERT_METRICS:
            score_a = getattr(eval_data, f'{metric}_a', None)
            score_b = getattr(eval_data, f'{metric}_b', None)
            if score_a is not None:
                thread_stats[thread_a]['likert_scores'][metric].append(score_a)
            if score_b is not None:
                thread_stats[thread_b]['likert_scores'][metric].append(score_b)

        # Count wins/losses/ties
        if winner == 'A':
            thread_stats[thread_a]['wins'] += 1
            thread_stats[thread_a]['opponents_beaten'].append(thread_b)
            thread_stats[thread_b]['losses'] += 1
            thread_stats[thread_b]['opponents_lost_to'].append(thread_a)
        elif winner == 'B':
            thread_stats[thread_b]['wins'] += 1
            thread_stats[thread_b]['opponents_beaten'].append(thread_a)
            thread_stats[thread_a]['losses'] += 1
            thread_stats[thread_a]['opponents_lost_to'].append(thread_b)
        else:  # TIE
            thread_stats[thread_a]['ties'] += 1
            thread_stats[thread_b]['ties'] += 1

    # Calculate win rates and prepare output
    threads_list = []
    pillar_summary = defaultdict(lambda: {
        'pillar': None,
        'total_threads': 0,
        'total_comparisons': 0,
        'avg_win_rate': 0,
        'consistent_winners': 0,
        'consistent_losers': 0
    })

    # Global Likert consistency tracking
    global_likert_scores = {metric: [] for metric in LIKERT_METRICS}

    for thread_id, stats in thread_stats.items():
        total = stats['wins'] + stats['losses'] + stats['ties']
        win_rate = stats['wins'] / total if total > 0 else 0
        loss_rate = stats['losses'] / total if total > 0 else 0

        # Determine consistency (>70% win or >70% loss rate with min 3 comparisons)
        is_consistent_winner = win_rate >= 0.7 and total >= 3
        is_consistent_loser = loss_rate >= 0.7 and total >= 3

        # Calculate Likert consistency per thread
        # Standard deviation: low = consistent, high = inconsistent
        likert_summary = {}
        likert_consistency_score = 0  # Average consistency across all metrics
        metrics_with_data = 0

        for metric in LIKERT_METRICS:
            scores = stats['likert_scores'].get(metric, [])
            if len(scores) >= 2:
                mean_score = statistics.mean(scores)
                std_dev = statistics.stdev(scores)
                likert_summary[metric] = {
                    'mean': round(mean_score, 2),
                    'std_dev': round(std_dev, 2),
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores),
                    'is_consistent': std_dev < 0.5  # Threshold for consistency
                }
                # Lower std_dev = more consistent = higher score
                likert_consistency_score += max(0, 1 - std_dev)
                metrics_with_data += 1
                # Add to global tracking
                global_likert_scores[metric].extend(scores)
            elif len(scores) == 1:
                likert_summary[metric] = {
                    'mean': scores[0],
                    'std_dev': 0,
                    'min': scores[0],
                    'max': scores[0],
                    'count': 1,
                    'is_consistent': True  # Only one data point
                }
                global_likert_scores[metric].extend(scores)

        if metrics_with_data > 0:
            likert_consistency_score = round(likert_consistency_score / metrics_with_data, 3)

        thread_entry = {
            'thread_id': thread_id,
            'pillar': stats['pillar'],
            'usage_count': stats['usage_count'],
            'unique_opponents': len(set(stats['opponents'])),
            'wins': stats['wins'],
            'losses': stats['losses'],
            'ties': stats['ties'],
            'win_rate': round(win_rate, 3),
            'loss_rate': round(loss_rate, 3),
            'is_consistent_winner': is_consistent_winner,
            'is_consistent_loser': is_consistent_loser,
            'performance_score': round(win_rate - loss_rate, 3),  # -1 to +1
            'likert_scores': likert_summary,
            'likert_consistency_score': likert_consistency_score  # 0-1, higher = more consistent
        }
        threads_list.append(thread_entry)

        # Aggregate by pillar
        pillar = stats['pillar']
        if pillar:
            pillar_summary[pillar]['pillar'] = pillar
            pillar_summary[pillar]['total_threads'] += 1
            pillar_summary[pillar]['total_comparisons'] += stats['usage_count']
            pillar_summary[pillar]['avg_win_rate'] += win_rate
            if is_consistent_winner:
                pillar_summary[pillar]['consistent_winners'] += 1
            if is_consistent_loser:
                pillar_summary[pillar]['consistent_losers'] += 1

    # Finalize pillar averages
    for pillar, summary in pillar_summary.items():
        if summary['total_threads'] > 0:
            summary['avg_win_rate'] = round(
                summary['avg_win_rate'] / summary['total_threads'], 3
            )

    # Sort threads by performance score (best first)
    threads_list.sort(key=lambda x: x['performance_score'], reverse=True)

    # Calculate coverage statistics
    total_threads = len(threads_list)
    total_usage = sum(t['usage_count'] for t in threads_list)
    avg_usage = total_usage / total_threads if total_threads > 0 else 0

    # Find outliers (used much more or less than average)
    over_sampled = [t for t in threads_list if t['usage_count'] > avg_usage * 1.5]
    under_sampled = [t for t in threads_list if t['usage_count'] < avg_usage * 0.5]

    # Calculate global Likert consistency (are LLM ratings consistent overall?)
    global_likert_consistency = {}
    for metric in LIKERT_METRICS:
        scores = global_likert_scores[metric]
        if len(scores) >= 2:
            global_likert_consistency[metric] = {
                'mean': round(statistics.mean(scores), 2),
                'std_dev': round(statistics.stdev(scores), 2),
                'min': min(scores),
                'max': max(scores),
                'count': len(scores),
                'is_consistent': statistics.stdev(scores) < 1.0  # More lenient for global
            }

    # Find threads with inconsistent Likert scores (potential quality issues)
    inconsistent_threads = [
        t for t in threads_list
        if t.get('likert_consistency_score', 1) < 0.5 and t['usage_count'] >= 3
    ]

    return jsonify({
        'session_id': session_id,
        'total_threads': total_threads,
        'total_comparisons': len(comparisons),
        'avg_usage_per_thread': round(avg_usage, 2),
        'coverage_stats': {
            'over_sampled_count': len(over_sampled),
            'under_sampled_count': len(under_sampled),
            'evenly_sampled_count': total_threads - len(over_sampled) - len(under_sampled)
        },
        'threads': threads_list,
        'pillar_summary': dict(pillar_summary),
        'consistent_winners': [t for t in threads_list if t['is_consistent_winner']],
        'consistent_losers': [t for t in threads_list if t['is_consistent_loser']],
        'likert_consistency': {
            'global': global_likert_consistency,
            'inconsistent_threads': inconsistent_threads,
            'metrics_tracked': LIKERT_METRICS
        }
    })


@judge_bp.route('/sessions/<int:session_id>/position-swap-analysis', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_position_swap_analysis(session_id: int):
    """
    Detailed Position-Swap Consistency Analysis following best practices from:
    - Zheng et al. (2023): "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
    - "Judging the Judges: A Systematic Investigation of Position Bias in Pairwise Comparative Assessments"

    Metrics calculated:
    1. Position Consistency Rate: % of swapped pairs where winner is the same
    2. Consistent Wins: Same thread wins regardless of position
    3. Consistent Ties: Both evaluations result in TIE
    4. Position Bias Direction: Primacy (first preferred) vs Recency (last preferred)
    5. Likert Score Deltas: How much do scores change when positions swap?

    Returns detailed pair-by-pair analysis for inspection.
    """
    import statistics
    from collections import defaultdict

    session = JudgeSession.query.get_or_404(session_id)

    # Get all completed comparisons
    comparisons = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.COMPLETED
    ).all()

    if not comparisons:
        return jsonify({
            'session_id': session_id,
            'error': 'Keine abgeschlossenen Vergleiche gefunden',
            'total_pairs': 0
        })

    # Group comparisons by thread pair (to find swapped pairs)
    # Key: frozenset({thread_a_id, thread_b_id}) -> list of comparisons
    pair_groups = defaultdict(list)
    for comp in comparisons:
        pair_key = frozenset({comp.thread_a_id, comp.thread_b_id})
        evaluation = JudgeEvaluation.query.filter_by(comparison_id=comp.id).first()
        if evaluation:
            pair_groups[pair_key].append({
                'comparison': comp,
                'evaluation': evaluation
            })

    # Analyze each swapped pair
    LIKERT_METRICS = ['counsellor_coherence', 'client_coherence', 'quality', 'empathy', 'authenticity', 'solution_orientation']

    # Counters
    total_swap_pairs = 0  # Pairs that have both A|B and B|A
    consistent_wins = 0   # Same thread wins in both positions
    consistent_ties = 0   # Both result in TIE
    inconsistent = 0      # Different outcomes
    primacy_bias = 0      # First position preferred when inconsistent
    recency_bias = 0      # Second position preferred when inconsistent

    # Detailed pair analysis
    pair_analyses = []

    # Likert consistency tracking
    likert_deltas = {metric: [] for metric in LIKERT_METRICS}

    for pair_key, group in pair_groups.items():
        # Need at least 2 evaluations (original and swapped) for analysis
        if len(group) < 2:
            continue

        # Find original (A|B) and swapped (B|A) comparisons
        # Group by position_order or by which thread is in position A
        threads = list(pair_key)
        t1, t2 = threads[0], threads[1]

        # Separate into "t1 as A" and "t2 as A" groups
        t1_as_a = [g for g in group if g['comparison'].thread_a_id == t1]
        t2_as_a = [g for g in group if g['comparison'].thread_a_id == t2]

        # Analyze each original-swapped pair
        for orig in t1_as_a:
            for swap in t2_as_a:
                total_swap_pairs += 1

                orig_eval = orig['evaluation']
                swap_eval = swap['evaluation']
                orig_comp = orig['comparison']
                swap_comp = swap['comparison']

                # Determine winner in terms of actual thread (not position)
                # Original: A=t1, B=t2 -> winner 'A' means t1 wins
                # Swapped:  A=t2, B=t1 -> winner 'A' means t2 wins, 'B' means t1 wins
                orig_winner = orig_eval.winner.value if orig_eval.winner else None
                swap_winner = swap_eval.winner.value if swap_eval.winner else None

                # Convert to actual thread winner
                if orig_winner == 'A':
                    orig_thread_winner = t1
                elif orig_winner == 'B':
                    orig_thread_winner = t2
                else:
                    orig_thread_winner = 'TIE'

                if swap_winner == 'A':
                    swap_thread_winner = t2  # In swapped, A is t2
                elif swap_winner == 'B':
                    swap_thread_winner = t1  # In swapped, B is t1
                else:
                    swap_thread_winner = 'TIE'

                # Determine consistency
                is_consistent = False
                consistency_type = None
                bias_direction = None

                if orig_thread_winner == swap_thread_winner:
                    is_consistent = True
                    if orig_thread_winner == 'TIE':
                        consistent_ties += 1
                        consistency_type = 'consistent_tie'
                    else:
                        consistent_wins += 1
                        consistency_type = 'consistent_win'
                else:
                    inconsistent += 1
                    consistency_type = 'inconsistent'

                    # Determine bias direction
                    # Primacy: Position A always wins
                    # Recency: Position B always wins
                    if orig_winner == 'A' and swap_winner == 'A':
                        primacy_bias += 1
                        bias_direction = 'primacy'
                    elif orig_winner == 'B' and swap_winner == 'B':
                        recency_bias += 1
                        bias_direction = 'recency'
                    else:
                        # Mixed - one wins in orig, TIE in swap or vice versa
                        bias_direction = 'mixed'

                # Calculate Likert score deltas
                # Compare scores for the SAME thread across both evaluations
                likert_comparison = {}
                for metric in LIKERT_METRICS:
                    # In original: t1 is A, t2 is B
                    orig_t1_score = getattr(orig_eval, f'{metric}_a', None)
                    orig_t2_score = getattr(orig_eval, f'{metric}_b', None)

                    # In swapped: t2 is A, t1 is B
                    swap_t1_score = getattr(swap_eval, f'{metric}_b', None)  # t1 is now B
                    swap_t2_score = getattr(swap_eval, f'{metric}_a', None)  # t2 is now A

                    # Calculate deltas (same thread, different position)
                    delta_t1 = None
                    delta_t2 = None

                    if orig_t1_score is not None and swap_t1_score is not None:
                        delta_t1 = swap_t1_score - orig_t1_score
                        likert_deltas[metric].append(abs(delta_t1))

                    if orig_t2_score is not None and swap_t2_score is not None:
                        delta_t2 = swap_t2_score - orig_t2_score
                        likert_deltas[metric].append(abs(delta_t2))

                    likert_comparison[metric] = {
                        'thread_1': {
                            'original_score': orig_t1_score,  # t1 as A
                            'swapped_score': swap_t1_score,   # t1 as B
                            'delta': delta_t1
                        },
                        'thread_2': {
                            'original_score': orig_t2_score,  # t2 as B
                            'swapped_score': swap_t2_score,   # t2 as A
                            'delta': delta_t2
                        }
                    }

                # Build pair analysis
                pair_analyses.append({
                    'thread_1_id': t1,
                    'thread_2_id': t2,
                    'original': {
                        'comparison_id': orig_comp.id,
                        'position': f't{t1}_as_A',
                        'winner_position': orig_winner,
                        'winner_thread': orig_thread_winner,
                        'confidence': orig_eval.confidence,
                        'pillar_a': orig_comp.pillar_a,
                        'pillar_b': orig_comp.pillar_b
                    },
                    'swapped': {
                        'comparison_id': swap_comp.id,
                        'position': f't{t2}_as_A',
                        'winner_position': swap_winner,
                        'winner_thread': swap_thread_winner,
                        'confidence': swap_eval.confidence,
                        'pillar_a': swap_comp.pillar_a,
                        'pillar_b': swap_comp.pillar_b
                    },
                    'is_consistent': is_consistent,
                    'consistency_type': consistency_type,
                    'bias_direction': bias_direction,
                    'likert_comparison': likert_comparison,
                    'confidence_delta': abs((orig_eval.confidence or 0) - (swap_eval.confidence or 0))
                })

    # Calculate summary statistics
    consistency_rate = (consistent_wins + consistent_ties) / total_swap_pairs if total_swap_pairs > 0 else 0
    inconsistency_rate = inconsistent / total_swap_pairs if total_swap_pairs > 0 else 0

    # Bias direction summary
    bias_summary = {
        'primacy_count': primacy_bias,
        'recency_count': recency_bias,
        'primacy_rate': primacy_bias / inconsistent if inconsistent > 0 else 0,
        'recency_rate': recency_bias / inconsistent if inconsistent > 0 else 0,
        'dominant_bias': 'primacy' if primacy_bias > recency_bias else ('recency' if recency_bias > primacy_bias else 'balanced')
    }

    # Likert stability analysis
    likert_stability = {}
    for metric in LIKERT_METRICS:
        deltas = likert_deltas[metric]
        if deltas:
            likert_stability[metric] = {
                'mean_delta': round(statistics.mean(deltas), 3),
                'max_delta': max(deltas),
                'std_delta': round(statistics.stdev(deltas), 3) if len(deltas) > 1 else 0,
                'stable_count': sum(1 for d in deltas if d <= 1),  # Delta ≤ 1 is stable
                'unstable_count': sum(1 for d in deltas if d > 1),
                'stability_rate': sum(1 for d in deltas if d <= 1) / len(deltas)
            }

    # Interpretation and recommendations
    interpretation = {
        'overall_quality': 'excellent' if consistency_rate >= 0.8 else ('good' if consistency_rate >= 0.6 else ('fair' if consistency_rate >= 0.4 else 'poor')),
        'position_bias_present': inconsistency_rate > 0.2,
        'recommendations': []
    }

    if consistency_rate < 0.6:
        interpretation['recommendations'].append('Low consistency rate suggests significant position bias. Consider using majority voting or averaging scores.')
    if bias_summary['dominant_bias'] == 'primacy' and bias_summary['primacy_rate'] > 0.6:
        interpretation['recommendations'].append('Strong primacy bias detected. The model tends to prefer the first option.')
    if bias_summary['dominant_bias'] == 'recency' and bias_summary['recency_rate'] > 0.6:
        interpretation['recommendations'].append('Strong recency bias detected. The model tends to prefer the last option.')
    if not interpretation['recommendations']:
        interpretation['recommendations'].append('Position-swap consistency is acceptable. Results are reliable.')

    # Sort pair analyses: inconsistent first, then by confidence delta
    pair_analyses.sort(key=lambda x: (x['is_consistent'], -x['confidence_delta']))

    return jsonify({
        'session_id': session_id,
        'session_name': session.name,

        # Summary Statistics (MT-Bench style)
        'summary': {
            'total_swap_pairs': total_swap_pairs,
            'consistency_rate': round(consistency_rate, 4),
            'inconsistency_rate': round(inconsistency_rate, 4),
            'consistent_wins': consistent_wins,
            'consistent_ties': consistent_ties,
            'inconsistent': inconsistent
        },

        # Position Bias Analysis
        'position_bias': bias_summary,

        # Likert Score Stability
        'likert_stability': likert_stability,

        # Interpretation
        'interpretation': interpretation,

        # Detailed Pair Analysis (for inspection)
        'pairs': pair_analyses,

        # References
        'methodology': {
            'description': 'Position-Swap Consistency Analysis based on MT-Bench methodology',
            'metrics_explanation': {
                'consistency_rate': {
                    'description': 'Percentage of swapped pairs where the same thread wins (or both TIE)',
                    'source': 'MT-Bench',
                    'source_url': 'https://arxiv.org/abs/2306.05685'
                },
                'primacy_bias': {
                    'description': 'Tendency to prefer the first option (Position A)',
                    'source': 'Judging the Judges',
                    'source_url': 'https://arxiv.org/abs/2406.07791'
                },
                'recency_bias': {
                    'description': 'Tendency to prefer the last option (Position B)',
                    'source': 'Judging the Judges',
                    'source_url': 'https://arxiv.org/abs/2406.07791'
                },
                'likert_stability': {
                    'description': 'How much Likert scores change for the same thread when position changes',
                    'source': 'Auto-J / JudgeLM calibration',
                    'source_url': 'https://arxiv.org/abs/2310.05470'
                }
            },
            'references': [
                {
                    'title': 'Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena',
                    'authors': 'Zheng et al.',
                    'year': 2023,
                    'url': 'https://arxiv.org/abs/2306.05685',
                    'key_contribution': 'Consistency metric, position swap methodology'
                },
                {
                    'title': 'Judging the Judges: Position Bias in Pairwise Assessments',
                    'authors': 'Shi et al.',
                    'year': 2024,
                    'url': 'https://arxiv.org/abs/2406.07791',
                    'key_contribution': 'Primacy/Recency bias classification'
                },
                {
                    'title': 'Generative Judge for Evaluating Alignment',
                    'authors': 'Li et al. (Auto-J)',
                    'year': 2023,
                    'url': 'https://arxiv.org/abs/2310.05470',
                    'key_contribution': 'Score calibration via position shuffling'
                }
            ]
        }
    })


# ============================================================================
# PILLAR MANAGEMENT
# ============================================================================

@judge_bp.route('/pillars', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def list_pillars():
    """
    List all pillars with thread counts.

    Returns:
        JSON array of pillar info
    """
    # Get thread counts per pillar
    pillar_counts = db.session.query(
        PillarThread.pillar_number,
        PillarThread.pillar_name,
        func.count(PillarThread.id).label('thread_count')
    ).group_by(
        PillarThread.pillar_number,
        PillarThread.pillar_name
    ).all()

    # Build response with all 5 pillars
    pillar_names = {
        1: "Rollenspiele",
        2: "Feature aus Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch generiert",
        5: "Live-Testungen"
    }

    pillar_colors = {
        1: "#f44336",  # red
        2: "#ff9800",  # orange
        3: "#4caf50",  # green
        4: "#2196f3",  # blue
        5: "#9c27b0"   # purple
    }

    result = []
    count_map = {p[0]: (p[1], p[2]) for p in pillar_counts}

    for num in range(1, 6):
        name, count = count_map.get(num, (pillar_names[num], 0))
        result.append({
            'number': num,
            'name': name or pillar_names[num],
            'thread_count': count,
            'color': pillar_colors[num]
        })

    return jsonify(result)


@judge_bp.route('/pillars/<int:pillar_number>/threads', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_pillar_threads(pillar_number: int):
    """
    Get threads assigned to a specific pillar.

    Returns:
        JSON array of thread info
    """
    pillar_threads = PillarThread.query.filter_by(
        pillar_number=pillar_number
    ).all()

    threads = []
    for pt in pillar_threads:
        thread = EmailThread.query.get(pt.thread_id)
        if thread:
            threads.append({
                'id': thread.id,
                'subject': thread.subject if hasattr(thread, 'subject') else f'Thread {thread.id}',
                'pillar_id': pt.id,
                'metadata': pt.metadata_json
            })

    return jsonify({
        'pillar': pillar_number,
        'threads': threads,
        'count': len(threads)
    })


@judge_bp.route('/pillars/<int:pillar_number>/assign', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def assign_thread_to_pillar(pillar_number: int):
    """
    Assign a thread to a pillar.

    Body:
        thread_id: ID of the thread to assign
        metadata: Optional metadata dict

    Returns:
        JSON with assignment info
    """
    data = request.get_json()
    thread_id = data.get('thread_id')

    if not thread_id:
        return jsonify({'error': 'thread_id ist erforderlich'}), 400

    # Check if thread exists
    thread = EmailThread.query.get(thread_id)
    if not thread:
        return jsonify({'error': 'Thread nicht gefunden'}), 404

    # Check if already assigned
    existing = PillarThread.query.filter_by(
        thread_id=thread_id,
        pillar_number=pillar_number
    ).first()

    if existing:
        return jsonify({'error': 'Thread ist bereits dieser Säule zugeordnet'}), 400

    pillar_names = {
        1: "Rollenspiele",
        2: "Feature aus Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch generiert",
        5: "Live-Testungen"
    }

    pillar_thread = PillarThread(
        thread_id=thread_id,
        pillar_number=pillar_number,
        pillar_name=pillar_names.get(pillar_number, f"Säule {pillar_number}"),
        metadata_json=data.get('metadata', {})
    )

    db.session.add(pillar_thread)
    db.session.commit()

    return jsonify({
        'id': pillar_thread.id,
        'thread_id': thread_id,
        'pillar_number': pillar_number,
        'message': 'Thread zugeordnet'
    }), 201


# ============================================================================
# EXPORT
# ============================================================================

@judge_bp.route('/sessions/<int:session_id>/export', methods=['GET'])
@authentik_required
@require_permission('data:export')
def export_session(session_id: int):
    """
    Export session results as JSON.

    Returns:
        JSON with complete session data
    """
    session = JudgeSession.query.get_or_404(session_id)

    # Get all comparisons with evaluations
    comparisons = JudgeComparison.query.filter_by(
        session_id=session_id
    ).order_by(JudgeComparison.queue_position).all()

    export_data = {
        'session': {
            'id': session.id,
            'name': session.name,
            'status': session.status.value,
            'config': session.config_json,
            'total_comparisons': session.total_comparisons,
            'completed_comparisons': session.completed_comparisons,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'completed_at': session.completed_at.isoformat() if session.completed_at else None
        },
        'comparisons': [],
        'statistics': []
    }

    for comp in comparisons:
        comp_data = {
            'id': comp.id,
            'thread_a_id': comp.thread_a_id,
            'thread_b_id': comp.thread_b_id,
            'pillar_a': comp.pillar_a,
            'pillar_b': comp.pillar_b,
            'position_order': comp.position_order,
            'status': comp.status.value,
            'evaluation': None
        }

        # Get evaluation if exists
        eval = JudgeEvaluation.query.filter_by(comparison_id=comp.id).first()
        if eval:
            comp_data['evaluation'] = {
                'winner': eval.winner.value,
                'confidence': eval.confidence,
                'reasoning': eval.reasoning,
                'scores': eval.evaluation_json,
                'latency_ms': eval.llm_latency_ms
            }

        export_data['comparisons'].append(comp_data)

    # Get statistics
    stats = PillarStatistics.query.filter_by(session_id=session_id).all()
    for s in stats:
        export_data['statistics'].append({
            'pillar_a': s.pillar_a,
            'pillar_b': s.pillar_b,
            'wins_a': s.wins_a,
            'wins_b': s.wins_b,
            'ties': s.ties,
            'avg_confidence': s.avg_confidence
        })

    return jsonify(export_data)


# ============================================================================
# KIA DATA SYNC
# ============================================================================

@judge_bp.route('/kia/status', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_kia_sync_status():
    """
    Get sync status for all KIA pillars.

    Shows which pillars have data available in GitLab
    and how many are synced to the database.

    Returns:
        JSON with pillar sync status
    """
    from services.judge.kia_sync_service import get_kia_sync_service

    try:
        sync_service = get_kia_sync_service()
        status = sync_service.get_sync_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'gitlab_connected': False,
            'pillars': {}
        }), 500


@judge_bp.route('/kia/check', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def check_kia_availability():
    """
    Check which pillars have data available in GitLab.

    Does not sync, just checks availability.

    Returns:
        JSON with availability per pillar
    """
    from services.judge.kia_sync_service import get_kia_sync_service

    try:
        sync_service = get_kia_sync_service()
        availability = sync_service.check_pillar_availability()

        return jsonify({
            'pillars': {
                num: {
                    'number': status.pillar_number,
                    'name': status.pillar_name,
                    'status': status.status.value,
                    'file_count': status.file_count,
                    'error': status.error_message
                }
                for num, status in availability.items()
            },
            'gitlab_connected': sync_service._get_project_id() is not None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@judge_bp.route('/kia/sync', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def sync_kia_data():
    """
    Sync KIA data from GitLab repository.

    Body:
        pillar: (optional) Specific pillar number to sync (1-5)
                If not provided, syncs all available pillars
        force: (optional) If true, re-imports existing data

    Returns:
        JSON with sync results
    """
    from services.judge.kia_sync_service import get_kia_sync_service

    data = request.get_json() or {}
    pillar = data.get('pillar')
    force = data.get('force', False)
    gitlab_token = data.get('gitlab_token')  # Optional token override

    try:
        sync_service = get_kia_sync_service(gitlab_token)

        if pillar:
            # Sync specific pillar
            if pillar not in range(1, 6):
                return jsonify({'error': 'Pillar muss zwischen 1 und 5 sein'}), 400

            result = sync_service.sync_pillar(pillar, force)
            return jsonify({
                'success': result.success,
                'pillar': pillar,
                'files_processed': result.files_processed,
                'threads_created': result.threads_created,
                'threads_updated': result.threads_updated,
                'threads_skipped': result.threads_skipped,
                'errors': result.errors
            })
        else:
            # Sync all pillars
            results = sync_service.sync_all_pillars(force)

            summary = {
                'total_success': sum(1 for r in results.values() if r.success),
                'total_failed': sum(1 for r in results.values() if not r.success),
                'total_threads_created': sum(r.threads_created for r in results.values()),
                'total_threads_updated': sum(r.threads_updated for r in results.values()),
                'pillars': {}
            }

            for pillar_num, result in results.items():
                summary['pillars'][pillar_num] = {
                    'success': result.success,
                    'files_processed': result.files_processed,
                    'threads_created': result.threads_created,
                    'threads_updated': result.threads_updated,
                    'threads_skipped': result.threads_skipped,
                    'errors': result.errors
                }

            return jsonify(summary)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@judge_bp.route('/kia/sync/<int:pillar_number>', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def sync_specific_pillar(pillar_number: int):
    """
    Sync a specific pillar from GitLab.

    Args:
        pillar_number: Pillar to sync (1-5)

    Query params:
        force: If 'true', re-imports existing data

    Returns:
        JSON with sync result
    """
    from services.judge.kia_sync_service import get_kia_sync_service

    if pillar_number not in range(1, 6):
        return jsonify({'error': 'Pillar muss zwischen 1 und 5 sein'}), 400

    force = request.args.get('force', 'false').lower() == 'true'

    try:
        sync_service = get_kia_sync_service()
        result = sync_service.sync_pillar(pillar_number, force)

        return jsonify({
            'success': result.success,
            'pillar': pillar_number,
            'files_processed': result.files_processed,
            'threads_created': result.threads_created,
            'threads_updated': result.threads_updated,
            'threads_skipped': result.threads_skipped,
            'errors': result.errors
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@judge_bp.route('/kia/config', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_kia_config():
    """
    Get KIA sync configuration.

    Returns:
        JSON with current configuration
    """
    from services.judge.kia_sync_service import PILLAR_CONFIG, KIASyncService
    import os

    return jsonify({
        'gitlab_host': KIASyncService.GITLAB_HOST,
        'project_path': KIASyncService.PROJECT_PATH,
        'has_token': bool(os.environ.get('GITLAB_TOKEN') or os.environ.get('KIA_GITLAB_TOKEN')),
        'pillars': {
            num: {
                'name': config['name'],
                'path': config['path']
            }
            for num, config in PILLAR_CONFIG.items()
        }
    })


@judge_bp.route('/kia/config', methods=['POST'])
@authentik_required
@require_permission('admin:permissions:manage')
def set_kia_token():
    """
    Set GitLab token for KIA sync.

    Body:
        gitlab_token: Personal access token for GitLab

    Returns:
        JSON with confirmation
    """
    data = request.get_json()
    token = data.get('gitlab_token')

    if not token:
        return jsonify({'error': 'gitlab_token ist erforderlich'}), 400

    # Store token in environment (for this process only)
    import os
    os.environ['KIA_GITLAB_TOKEN'] = token

    # Reset the sync service to use new token
    from services.judge.kia_sync_service import get_kia_sync_service
    sync_service = get_kia_sync_service(token)

    # Test connection
    project_id = sync_service._get_project_id()

    if project_id:
        return jsonify({
            'success': True,
            'message': 'GitLab Token gesetzt und verbunden',
            'project_id': project_id
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Token gesetzt, aber Verbindung fehlgeschlagen'
        }), 400
