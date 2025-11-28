"""Position-swap consistency analysis routes for LLM-as-Judge statistics.

Based on methodologies from:
- Zheng et al. (2023): "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
- "Judging the Judges: A Systematic Investigation of Position Bias in Pairwise Comparative Assessments"
"""

import statistics as stats_module
from flask import Blueprint, jsonify
from collections import defaultdict

from db.db import db
from db.tables import (
    JudgeSession,
    JudgeComparison, JudgeComparisonStatus,
    JudgeEvaluation, JudgeWinner
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission

statistics_position_bp = Blueprint('judge_statistics_position', __name__)

# Likert metrics tracked for consistency analysis
LIKERT_METRICS = ['counsellor_coherence', 'client_coherence', 'quality', 'empathy', 'authenticity', 'solution_orientation']


@statistics_position_bp.route('/sessions/<int:session_id>/position-swap-analysis', methods=['GET'])
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
    total_swap_pairs = 0
    consistent_wins = 0
    consistent_ties = 0
    inconsistent = 0
    primacy_bias = 0
    recency_bias = 0

    pair_analyses = []
    likert_deltas = {metric: [] for metric in LIKERT_METRICS}

    for pair_key, group in pair_groups.items():
        if len(group) < 2:
            continue

        threads = list(pair_key)
        t1, t2 = threads[0], threads[1]

        t1_as_a = [g for g in group if g['comparison'].thread_a_id == t1]
        t2_as_a = [g for g in group if g['comparison'].thread_a_id == t2]

        for orig in t1_as_a:
            for swap in t2_as_a:
                total_swap_pairs += 1

                orig_eval = orig['evaluation']
                swap_eval = swap['evaluation']
                orig_comp = orig['comparison']
                swap_comp = swap['comparison']

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
                    swap_thread_winner = t2
                elif swap_winner == 'B':
                    swap_thread_winner = t1
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

                    if orig_winner == 'A' and swap_winner == 'A':
                        primacy_bias += 1
                        bias_direction = 'primacy'
                    elif orig_winner == 'B' and swap_winner == 'B':
                        recency_bias += 1
                        bias_direction = 'recency'
                    else:
                        bias_direction = 'mixed'

                # Calculate Likert score deltas
                likert_comparison = {}
                for metric in LIKERT_METRICS:
                    orig_t1_score = getattr(orig_eval, f'{metric}_a', None)
                    orig_t2_score = getattr(orig_eval, f'{metric}_b', None)
                    swap_t1_score = getattr(swap_eval, f'{metric}_b', None)
                    swap_t2_score = getattr(swap_eval, f'{metric}_a', None)

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
                            'original_score': orig_t1_score,
                            'swapped_score': swap_t1_score,
                            'delta': delta_t1
                        },
                        'thread_2': {
                            'original_score': orig_t2_score,
                            'swapped_score': swap_t2_score,
                            'delta': delta_t2
                        }
                    }

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
                'mean_delta': round(stats_module.mean(deltas), 3),
                'max_delta': max(deltas),
                'std_delta': round(stats_module.stdev(deltas), 3) if len(deltas) > 1 else 0,
                'stable_count': sum(1 for d in deltas if d <= 1),
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

    pair_analyses.sort(key=lambda x: (x['is_consistent'], -x['confidence_delta']))

    return jsonify({
        'session_id': session_id,
        'session_name': session.name,
        'summary': {
            'total_swap_pairs': total_swap_pairs,
            'consistency_rate': round(consistency_rate, 4),
            'inconsistency_rate': round(inconsistency_rate, 4),
            'consistent_wins': consistent_wins,
            'consistent_ties': consistent_ties,
            'inconsistent': inconsistent
        },
        'position_bias': bias_summary,
        'likert_stability': likert_stability,
        'interpretation': interpretation,
        'pairs': pair_analyses,
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
