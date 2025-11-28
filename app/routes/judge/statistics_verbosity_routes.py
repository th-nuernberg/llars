"""Verbosity analysis routes for LLM-as-Judge statistics."""

from flask import Blueprint, jsonify
from collections import defaultdict

from db.db import db
from db.tables import (
    JudgeSession,
    JudgeComparison, JudgeComparisonStatus,
    JudgeEvaluation, JudgeWinner,
    PillarThread
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission

statistics_verbosity_bp = Blueprint('judge_statistics_verbosity', __name__)


@statistics_verbosity_bp.route('/sessions/<int:session_id>/verbosity-analysis', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_verbosity_analysis(session_id: int):
    """
    Analyze if there's a verbosity bias in the evaluations.

    Checks if longer responses tend to win more often.
    """
    session = JudgeSession.query.get_or_404(session_id)

    comparisons = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.COMPLETED
    ).all()

    if not comparisons:
        return jsonify({
            'session_id': session_id,
            'error': 'Keine abgeschlossenen Vergleiche gefunden',
            'total_comparisons': 0
        })

    # Collect verbosity data
    verbosity_data = []

    for comp in comparisons:
        evaluation = JudgeEvaluation.query.filter_by(comparison_id=comp.id).first()
        if not evaluation:
            continue

        # Get thread lengths (approximate by message count or could fetch actual content)
        thread_a = PillarThread.query.get(comp.thread_a_id)
        thread_b = PillarThread.query.get(comp.thread_b_id)

        if not thread_a or not thread_b:
            continue

        # Use message_count as proxy for verbosity (or could calculate actual length)
        len_a = thread_a.message_count or 0
        len_b = thread_b.message_count or 0

        winner = evaluation.winner.value if evaluation.winner else None

        # Determine if longer won
        if winner == 'A':
            longer_won = len_a > len_b
            shorter_won = len_a < len_b
        elif winner == 'B':
            longer_won = len_b > len_a
            shorter_won = len_b < len_a
        else:
            longer_won = False
            shorter_won = False

        verbosity_data.append({
            'comparison_id': comp.id,
            'length_a': len_a,
            'length_b': len_b,
            'winner': winner,
            'longer_won': longer_won,
            'shorter_won': shorter_won,
            'length_diff': abs(len_a - len_b),
            'length_ratio': max(len_a, len_b) / min(len_a, len_b) if min(len_a, len_b) > 0 else float('inf')
        })

    # Calculate statistics
    total = len(verbosity_data)
    longer_wins = sum(1 for v in verbosity_data if v['longer_won'])
    shorter_wins = sum(1 for v in verbosity_data if v['shorter_won'])
    ties = total - longer_wins - shorter_wins

    # Analyze by length difference buckets
    small_diff = [v for v in verbosity_data if v['length_diff'] <= 2]
    medium_diff = [v for v in verbosity_data if 2 < v['length_diff'] <= 5]
    large_diff = [v for v in verbosity_data if v['length_diff'] > 5]

    def bucket_stats(bucket):
        if not bucket:
            return {'count': 0, 'longer_win_rate': 0, 'shorter_win_rate': 0}
        longer = sum(1 for v in bucket if v['longer_won'])
        shorter = sum(1 for v in bucket if v['shorter_won'])
        return {
            'count': len(bucket),
            'longer_win_rate': round(longer / len(bucket), 3) if bucket else 0,
            'shorter_win_rate': round(shorter / len(bucket), 3) if bucket else 0
        }

    return jsonify({
        'session_id': session_id,
        'session_name': session.name,
        'total_comparisons': total,
        'summary': {
            'longer_wins': longer_wins,
            'shorter_wins': shorter_wins,
            'ties_or_equal': ties,
            'longer_win_rate': round(longer_wins / total, 3) if total > 0 else 0,
            'shorter_win_rate': round(shorter_wins / total, 3) if total > 0 else 0,
            'verbosity_bias_detected': longer_wins / total > 0.6 if total > 0 else False
        },
        'by_length_difference': {
            'small_diff_le_2': bucket_stats(small_diff),
            'medium_diff_3_5': bucket_stats(medium_diff),
            'large_diff_gt_5': bucket_stats(large_diff)
        },
        'details': verbosity_data[:50]  # Limit to first 50 for response size
    })
