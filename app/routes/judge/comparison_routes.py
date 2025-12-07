"""Comparison retrieval routes for LLM-as-Judge."""

from flask import Blueprint, request, jsonify, g

from db.db import db
from db.tables import (
    JudgeSession,
    JudgeComparison, JudgeComparisonStatus,
    JudgeEvaluation,
    EmailThread, Message
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)

comparison_bp = Blueprint('judge_comparisons', __name__)


# ============================================================================
# COMPARISON RETRIEVAL
# ============================================================================

@comparison_bp.route('/sessions/<int:session_id>/current', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def get_current_comparison(session_id: int):
    """
    Get the currently running comparison with thread data.

    Returns:
        JSON with current comparison and thread contents in frontend-compatible format
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

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


@comparison_bp.route('/sessions/<int:session_id>/queue', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def get_session_queue(session_id: int):
    """
    Get the pending comparisons queue for a session.

    Returns:
        JSON with pending and running comparisons, plus summary stats
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

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


@comparison_bp.route('/sessions/<int:session_id>/comparisons', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def get_session_comparisons(session_id: int):
    """
    Get all comparisons for a session with their evaluation status.

    Returns:
        JSON array of comparisons with pillar info and results
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

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
