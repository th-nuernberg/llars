"""Export routes for LLM-as-Judge."""

from datetime import datetime
from flask import Blueprint, request, jsonify, g, Response

from db.db import db
from db.tables import (
    JudgeSession,
    JudgeComparison,
    JudgeEvaluation, JudgeWinner,
    EmailThread, Message,
    PillarStatistics
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)

export_bp = Blueprint('judge_export', __name__)


# ============================================================================
# EXPORT
# ============================================================================

@export_bp.route('/sessions/<int:session_id>/export', methods=['GET'])
@authentik_required
@require_permission('data:export')
@handle_api_errors(logger_name='judge')
def export_session(session_id: int):
    """
    Export session results as JSON.

    Returns:
        JSON with complete session data
    """
    session = JudgeSession.query.get(session_id)
    if not session:
        raise NotFoundError(f'Session {session_id} not found')

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
