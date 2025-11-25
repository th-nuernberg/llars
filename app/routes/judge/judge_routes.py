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
    comparison_mode = data.get('comparison_mode', 'all_pairs')
    samples_per_pillar = min(data.get('samples_per_pillar', 10), 50)
    position_swap = data.get('position_swap', True)

    config_json = {
        'pillars': pillar_ids,
        'comparison_mode': comparison_mode,
        'samples_per_pillar': samples_per_pillar,
        'position_swap': position_swap
    }

    session = JudgeSession(
        user_id='admin',  # Default to admin for debug endpoint
        name=session_name,
        config_json=config_json,
        status=JudgeSessionStatus.CREATED,
        total_comparisons=0,
        completed_comparisons=0
    )

    db.session.add(session)
    db.session.commit()

    if pillar_ids and len(pillar_ids) >= 2:
        try:
            _configure_session_comparisons(session, pillar_ids, comparison_mode, samples_per_pillar, position_swap)
            db.session.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Auto-configure failed: {e}")
            db.session.rollback()

    return jsonify({
        'session_id': session.id,
        'name': session.name,
        'status': session.status.value,
        'total_comparisons': session.total_comparisons
    }), 201


@judge_bp.route('/sessions', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def create_session():
    """
    Create a new Judge session with optional configuration.

    Body:
        name OR session_name: Session name
        pillar_ids: Optional list of pillar IDs to include [1, 2, 3, 4, 5]
        comparison_mode: "all_pairs" or "specific" (default: all_pairs)
        samples_per_pillar: Number of threads per pillar (default: 10)
        position_swap: Whether to run position-swap (default: true)

    Returns:
        JSON with created session ID
    """
    data = request.get_json() or {}
    username = g.authentik_user

    # Support both 'name' and 'session_name' for flexibility
    session_name = data.get('session_name') or data.get('name') or f'Evaluation {datetime.now().strftime("%Y-%m-%d %H:%M")}'

    # Extract configuration from request
    pillar_ids = data.get('pillar_ids', [])
    comparison_mode = data.get('comparison_mode', 'all_pairs')
    samples_per_pillar = min(data.get('samples_per_pillar', 10), 50)
    position_swap = data.get('position_swap', True)

    # Build config JSON
    config_json = {
        'pillars': pillar_ids,
        'comparison_mode': comparison_mode,
        'samples_per_pillar': samples_per_pillar,
        'position_swap': position_swap
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

    # If pillars provided, auto-configure comparisons
    if pillar_ids and len(pillar_ids) >= 2:
        try:
            _configure_session_comparisons(session, pillar_ids, comparison_mode, samples_per_pillar, position_swap)
            db.session.commit()
        except Exception as e:
            # Log but don't fail - can be configured later
            import logging
            logging.getLogger(__name__).warning(f"Auto-configure failed: {e}")

    return jsonify({
        'session_id': session.id,
        'id': session.id,  # Keep for backwards compatibility
        'name': session.name,
        'status': session.status.value,
        'total_comparisons': session.total_comparisons
    }), 201


def _configure_session_comparisons(session, pillars, comparison_mode, samples_per_pillar, position_swap):
    """Helper to configure session comparisons."""
    from itertools import combinations

    # Generate comparison pairs
    if comparison_mode == 'all_pairs':
        pairs = list(combinations(sorted(pillars), 2))
    else:
        pairs = []

    # Get threads for each pillar
    pillar_threads = {}
    for pillar in pillars:
        threads = PillarThread.query.filter_by(pillar_number=pillar).all()
        if threads:
            pillar_threads[pillar] = threads

    if not pillar_threads:
        return  # No threads available yet

    # Create comparisons
    queue_position = 0
    for pillar_a, pillar_b in pairs:
        threads_a = pillar_threads.get(pillar_a, [])
        threads_b = pillar_threads.get(pillar_b, [])

        if not threads_a or not threads_b:
            continue

        # Sample threads
        import random
        sample_a = random.sample(threads_a, min(samples_per_pillar, len(threads_a)))
        sample_b = random.sample(threads_b, min(samples_per_pillar, len(threads_b)))

        # Create comparisons for each sample pair
        for ta in sample_a:
            for tb in sample_b[:1]:  # One-to-one for now
                # Original order (position_order: 1 = AB, 2 = BA)
                comp = JudgeComparison(
                    session_id=session.id,
                    thread_a_id=ta.thread_id,
                    thread_b_id=tb.thread_id,
                    pillar_a=pillar_a,
                    pillar_b=pillar_b,
                    position_order=1,  # AB
                    queue_position=queue_position,
                    status=JudgeComparisonStatus.PENDING
                )
                db.session.add(comp)
                queue_position += 1

                # Swapped order if enabled
                if position_swap:
                    comp_swap = JudgeComparison(
                        session_id=session.id,
                        thread_a_id=tb.thread_id,
                        thread_b_id=ta.thread_id,
                        pillar_a=pillar_b,
                        pillar_b=pillar_a,
                        position_order=2,  # BA
                        queue_position=queue_position,
                        status=JudgeComparisonStatus.PENDING
                    )
                    db.session.add(comp_swap)
                    queue_position += 1

    session.total_comparisons = queue_position
    session.status = JudgeSessionStatus.QUEUED


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

    from workers.judge_worker import trigger_judge_worker
    trigger_judge_worker(session_id)

    return jsonify({
        'session_id': session.id,
        'status': 'running',
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

    # Trigger background worker
    from workers.judge_worker import trigger_judge_worker
    trigger_judge_worker(session_id)

    response = {
        'session_id': session.id,
        'status': 'running',
        'message': 'Evaluation gestartet'
    }

    if sync_result:
        response['sync_result'] = sync_result

    return jsonify(response)


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

    # Stop worker
    from workers.judge_worker import stop_judge_worker
    stop_judge_worker(session_id)

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

    # Stop worker if running
    if session.status == JudgeSessionStatus.RUNNING:
        from workers.judge_worker import stop_judge_worker
        stop_judge_worker(session_id)

    # Delete cascades to comparisons, evaluations, statistics
    db.session.delete(session)
    db.session.commit()

    return jsonify({
        'message': 'Session gelöscht',
        'session_id': session_id
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
    from app.db.tables import EmailThread, EmailMessage

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
