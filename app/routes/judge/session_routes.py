"""Session management routes for LLM-as-Judge.

This module handles core session CRUD operations and configuration.
Control operations (start/stop/pause) are in session_control_routes.py.
Debug endpoints are in session_debug_routes.py.
Health monitoring is in session_health_routes.py.
"""

from datetime import datetime
from itertools import combinations
import random

from flask import Blueprint, request, jsonify, g

from db.database import db
from db.tables import (
    JudgeSession, JudgeSessionStatus,
    JudgeComparison, JudgeComparisonStatus,
    PillarThread, PillarStatistics, EmailThread
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from routes.judge.session_helpers import configure_session_comparisons

session_bp = Blueprint('judge_sessions', __name__)


# ============================================================================
# ESTIMATION & MODES
# ============================================================================

@session_bp.route('/estimate', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def estimate_comparisons_endpoint():
    """
    Estimate the number of comparisons for a given configuration.

    This endpoint helps the UI show expected workload before creating a session.
    Requires comparison view permissions.

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
        raise ValidationError('pillar_ids is required')

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
        # Return 200 with informative message (not an error, just empty data)
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
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
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


# ============================================================================
# SESSION CRUD
# ============================================================================

@session_bp.route('/sessions', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def list_sessions():
    """
    List all Judge sessions for the current user.

    Returns:
        JSON array of session objects with progress info
    """
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

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
@handle_api_errors(logger_name='judge')
def get_session(session_id: int):
    """
    Get details of a specific session.

    Args:
        session_id: ID of the session

    Returns:
        JSON object with session details
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

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


@session_bp.route('/sessions', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
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
    import logging
    data = request.get_json() or {}
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

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
            configure_session_comparisons(
                session, pillar_ids, comparison_mode, samples_per_pillar,
                position_swap, repetitions_per_pair, max_threads_per_pillar
            )
            db.session.commit()
        except Exception as e:
            logging.getLogger(__name__).warning(f"Auto-configure failed: {e}")

    return jsonify({
        'session_id': session.id,
        'id': session.id,
        'name': session.name,
        'status': session.status.value,
        'total_comparisons': session.total_comparisons,
        'comparison_mode': comparison_mode
    }), 201


# ============================================================================
# SESSION CONFIGURATION
# ============================================================================

@session_bp.route('/sessions/<int:session_id>/configure', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
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
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

    if session.status not in [JudgeSessionStatus.CREATED, JudgeSessionStatus.QUEUED]:
        raise ValidationError(
            f'Session kann nicht mehr konfiguriert werden (Status: {session.status.value})'
        )

    data = request.get_json()

    pillars = data.get('pillars', [1, 2, 3, 4, 5])
    comparison_mode = data.get('comparison_mode', 'all_pairs')
    specific_pairs = data.get('specific_pairs', [])
    samples_per_pillar = min(data.get('samples_per_pillar', 10), 50)
    position_swap = data.get('position_swap', True)

    # Generate comparison pairs
    if comparison_mode == 'all_pairs':
        pairs = list(combinations(sorted(pillars), 2))
    else:
        pairs = [(min(p), max(p)) for p in specific_pairs if len(p) == 2]

    # Get threads for each pillar
    pillar_threads = {}
    for pillar in pillars:
        threads = PillarThread.query.filter_by(pillar_number=pillar).all()
        if threads:
            pillar_threads[pillar] = [t.thread_id for t in threads]
        else:
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

        sample_a = random.sample(threads_a, min(len(threads_a), samples_per_pillar))
        sample_b = random.sample(threads_b, min(len(threads_b), samples_per_pillar))

        for ta, tb in zip(sample_a, sample_b):
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

    db.session.bulk_save_objects(comparisons)

    session.config_json = {
        'pillars': pillars,
        'comparison_mode': comparison_mode,
        'specific_pairs': specific_pairs,
        'samples_per_pillar': samples_per_pillar,
        'position_swap': position_swap
    }
    session.total_comparisons = len(comparisons)
    session.status = JudgeSessionStatus.QUEUED

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
