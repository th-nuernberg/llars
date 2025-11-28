"""Results and statistics routes for LLM-as-Judge."""

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from db.db import db
from db.tables import (
    JudgeSession,
    JudgeComparison, JudgeComparisonStatus,
    JudgeEvaluation, JudgeWinner,
    PillarStatistics, PillarThread
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


@statistics_bp.route('/sessions/<int:session_id>/verbosity-analysis', methods=['GET'])
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


@statistics_bp.route('/sessions/<int:session_id>/thread-performance', methods=['GET'])
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


@statistics_bp.route('/sessions/<int:session_id>/position-swap-analysis', methods=['GET'])
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
