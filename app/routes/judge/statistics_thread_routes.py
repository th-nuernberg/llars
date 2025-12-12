"""Thread performance analysis routes for LLM-as-Judge statistics."""

import statistics as stats_module
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
from decorators.error_handler import handle_api_errors

statistics_thread_bp = Blueprint('judge_statistics_thread', __name__)

# Likert metrics tracked for consistency analysis
LIKERT_METRICS = ['counsellor_coherence', 'client_coherence', 'quality', 'empathy', 'authenticity', 'solution_orientation']


@statistics_thread_bp.route('/sessions/<int:session_id>/thread-performance', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge_statistics')
def get_thread_performance(session_id: int):
    """
    Analyze individual thread performance within a session.

    Shows which threads consistently win/lose and their usage frequency.
    Also tracks Likert score consistency across comparisons.
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

    # Track thread statistics
    thread_stats = defaultdict(lambda: {
        'wins': 0,
        'losses': 0,
        'ties': 0,
        'total': 0,
        'pillar': None,
        'as_position_a': 0,
        'as_position_b': 0,
        'wins_as_a': 0,
        'wins_as_b': 0,
        # Likert scores received (for consistency tracking)
        'likert_scores': {metric: [] for metric in LIKERT_METRICS}
    })

    # Global Likert score tracking (for overall consistency)
    global_likert_scores = {metric: [] for metric in LIKERT_METRICS}

    # Pillar summary
    pillar_summary = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0, 'threads': set()})

    for comp in comparisons:
        evaluation = JudgeEvaluation.query.filter_by(comparison_id=comp.id).first()
        if not evaluation:
            continue

        winner = evaluation.winner.value if evaluation.winner else None

        # Update thread A stats
        thread_stats[comp.thread_a_id]['total'] += 1
        thread_stats[comp.thread_a_id]['pillar'] = comp.pillar_a
        thread_stats[comp.thread_a_id]['as_position_a'] += 1
        pillar_summary[comp.pillar_a]['threads'].add(comp.thread_a_id)

        # Update thread B stats
        thread_stats[comp.thread_b_id]['total'] += 1
        thread_stats[comp.thread_b_id]['pillar'] = comp.pillar_b
        thread_stats[comp.thread_b_id]['as_position_b'] += 1
        pillar_summary[comp.pillar_b]['threads'].add(comp.thread_b_id)

        # Track Likert scores for each thread
        for metric in LIKERT_METRICS:
            score_a = getattr(evaluation, f'{metric}_a', None)
            score_b = getattr(evaluation, f'{metric}_b', None)

            if score_a is not None:
                thread_stats[comp.thread_a_id]['likert_scores'][metric].append(score_a)
                global_likert_scores[metric].append(score_a)
            if score_b is not None:
                thread_stats[comp.thread_b_id]['likert_scores'][metric].append(score_b)
                global_likert_scores[metric].append(score_b)

        if winner == 'A':
            thread_stats[comp.thread_a_id]['wins'] += 1
            thread_stats[comp.thread_a_id]['wins_as_a'] += 1
            thread_stats[comp.thread_b_id]['losses'] += 1
            pillar_summary[comp.pillar_a]['wins'] += 1
            pillar_summary[comp.pillar_b]['losses'] += 1
        elif winner == 'B':
            thread_stats[comp.thread_b_id]['wins'] += 1
            thread_stats[comp.thread_b_id]['wins_as_b'] += 1
            thread_stats[comp.thread_a_id]['losses'] += 1
            pillar_summary[comp.pillar_b]['wins'] += 1
            pillar_summary[comp.pillar_a]['losses'] += 1
        else:  # TIE
            thread_stats[comp.thread_a_id]['ties'] += 1
            thread_stats[comp.thread_b_id]['ties'] += 1
            pillar_summary[comp.pillar_a]['ties'] += 1
            pillar_summary[comp.pillar_b]['ties'] += 1

    # Convert to list and calculate win rates
    threads_list = []
    for thread_id, stats in thread_stats.items():
        if stats['total'] == 0:
            continue

        win_rate = stats['wins'] / stats['total']
        loss_rate = stats['losses'] / stats['total']

        # Calculate Likert consistency for this thread
        likert_consistency = {}
        consistency_score = 1.0  # Start with perfect consistency

        for metric in LIKERT_METRICS:
            scores = stats['likert_scores'][metric]
            if len(scores) >= 2:
                mean_score = stats_module.mean(scores)
                std_dev = stats_module.stdev(scores)
                likert_consistency[metric] = {
                    'mean': round(mean_score, 2),
                    'std_dev': round(std_dev, 2),
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores),
                    'is_consistent': std_dev < 0.5  # Low std dev = consistent
                }
                # Penalize consistency score for high variance
                if std_dev >= 1.0:
                    consistency_score *= 0.8
                elif std_dev >= 0.5:
                    consistency_score *= 0.9

        threads_list.append({
            'thread_id': thread_id,
            'pillar': stats['pillar'],
            'usage_count': stats['total'],
            'wins': stats['wins'],
            'losses': stats['losses'],
            'ties': stats['ties'],
            'win_rate': round(win_rate, 3),
            'loss_rate': round(loss_rate, 3),
            'as_position_a': stats['as_position_a'],
            'as_position_b': stats['as_position_b'],
            'wins_as_a': stats['wins_as_a'],
            'wins_as_b': stats['wins_as_b'],
            'position_a_win_rate': round(stats['wins_as_a'] / stats['as_position_a'], 3) if stats['as_position_a'] > 0 else 0,
            'position_b_win_rate': round(stats['wins_as_b'] / stats['as_position_b'], 3) if stats['as_position_b'] > 0 else 0,
            'is_consistent_winner': win_rate > 0.7 and stats['total'] >= 3,
            'is_consistent_loser': loss_rate > 0.7 and stats['total'] >= 3,
            'likert_consistency': likert_consistency,
            'likert_consistency_score': round(consistency_score, 2)
        })

    # Sort by usage count (most used first)
    threads_list.sort(key=lambda x: x['usage_count'], reverse=True)

    # Calculate sampling balance
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
                'mean': round(stats_module.mean(scores), 2),
                'std_dev': round(stats_module.stdev(scores), 2),
                'min': min(scores),
                'max': max(scores),
                'count': len(scores),
                'is_consistent': stats_module.stdev(scores) < 1.0  # More lenient for global
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
        'pillar_summary': {
            k: {**v, 'threads': list(v['threads'])}
            for k, v in pillar_summary.items()
        },
        'consistent_winners': [t for t in threads_list if t['is_consistent_winner']],
        'consistent_losers': [t for t in threads_list if t['is_consistent_loser']],
        'likert_consistency': {
            'global': global_likert_consistency,
            'inconsistent_threads': inconsistent_threads,
            'metrics_tracked': LIKERT_METRICS
        }
    })
