"""Results and statistics routes for LLM-as-Judge.

Core session results and pillar statistics. Additional analysis endpoints
are split into separate modules:
- statistics_verbosity_routes.py: Verbosity bias analysis
- statistics_thread_routes.py: Thread performance analysis
- statistics_position_routes.py: Position-swap consistency analysis
"""

from flask import Blueprint, jsonify

from db.db import db
from db.tables import (
    JudgeSession,
    PillarStatistics
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission

statistics_bp = Blueprint('judge_statistics', __name__)


# ============================================================================
# RESULTS & STATISTICS
# ============================================================================

@statistics_bp.route('/sessions/<int:session_id>/results', methods=['GET'])
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
    pillar_wins = {}
    pillar_losses = {}
    pillar_total = {}
    pillar_confidence_sum = {}
    pillar_confidence_count = {}

    for s in stats:
        key_a_vs_b = f"{s.pillar_a}_vs_{s.pillar_b}"
        key_b_vs_a = f"{s.pillar_b}_vs_{s.pillar_a}"

        win_matrix[key_a_vs_b] = s.wins_a
        win_matrix[key_b_vs_a] = s.wins_b

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
        score = (win_rate * 0.7 + avg_conf * 0.3) * 5

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

    pillar_metrics.sort(key=lambda x: x['score'], reverse=True)

    return jsonify({
        'session_id': session_id,
        'session_name': session.name,
        'total_comparisons': session.total_comparisons,
        'completed_comparisons': session.completed_comparisons,
        'pillar_metrics': pillar_metrics,
        'win_matrix': win_matrix
    })


@statistics_bp.route('/sessions/<int:session_id>/statistics', methods=['GET'])
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
        'pillar_wins': {}
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

        overall['total_comparisons'] += total
        overall['total_ties'] += s.ties
        overall['pillar_wins'][s.pillar_a] = overall['pillar_wins'].get(s.pillar_a, 0) + s.wins_a
        overall['pillar_wins'][s.pillar_b] = overall['pillar_wins'].get(s.pillar_b, 0) + s.wins_b

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
