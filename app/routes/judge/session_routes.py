"""Session management routes for LLM-as-Judge."""

from datetime import datetime
from flask import Blueprint, request, jsonify, g

from db.db import db
from db.tables import (
    JudgeSession, JudgeSessionStatus,
    JudgeComparison, JudgeComparisonStatus,
    PillarThread
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission

session_bp = Blueprint('judge_sessions', __name__)


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@session_bp.route('/sessions-debug', methods=['GET'])
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


@session_bp.route('/estimate', methods=['POST'])
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


@session_bp.route('/comparison-modes', methods=['GET'])
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


@session_bp.route('/sessions', methods=['GET'])
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


@session_bp.route('/sessions/<int:session_id>', methods=['GET'])
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


@session_bp.route('/sessions-debug', methods=['POST'])
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


@session_bp.route('/sessions', methods=['POST'])
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


@session_bp.route('/sessions/<int:session_id>/configure', methods=['POST'])
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
    from itertools import combinations
    from db.tables import PillarStatistics, EmailThread
    import random

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
    from db.tables import PillarStatistics
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


@session_bp.route('/sessions/<int:session_id>/start-debug', methods=['POST'])
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


@session_bp.route('/sessions/<int:session_id>/start', methods=['POST'])
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


@session_bp.route('/sessions/<int:session_id>/resume', methods=['POST'])
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


@session_bp.route('/sessions/<int:session_id>/pause', methods=['POST'])
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


@session_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
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


@session_bp.route('/sessions/<int:session_id>/workers', methods=['GET'])
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


@session_bp.route('/sessions/<int:session_id>/health', methods=['GET'])
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
