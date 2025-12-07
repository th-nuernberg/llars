"""
OnCoCo Matrix Routes - Statistical matrix comparison endpoints.

Provides endpoints for:
- Computing statistical comparison metrics for transition matrices
- Performing significance tests (chi-square, permutation)
- Calculating effect sizes and identifying outliers
"""

import logging
import numpy as np
from flask import Blueprint, request, jsonify
from scipy import stats as scipy_stats
from scipy.spatial.distance import jensenshannon

from db.tables import OnCoCoTransitionMatrix
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from services.oncoco import get_label_display_name
from services.judge.kia_sync_service import PILLAR_CONFIG

logger = logging.getLogger(__name__)

oncoco_matrix_bp = Blueprint('oncoco_matrix', __name__)


# ============================================================================
# STATISTICAL MATRIX COMPARISON
# ============================================================================

@oncoco_matrix_bp.route('/analyses/<int:analysis_id>/matrix-comparison', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='oncoco')
def get_matrix_comparison_metrics(analysis_id: int):
    """
    Get statistical comparison metrics for transition matrices across pillars.

    Implements scientifically validated metrics for comparing Markov chain transition matrices:
    - Frobenius Distance: Overall matrix difference measure
    - Jensen-Shannon Divergence: Row-wise probability distribution comparison
    - Chi-Square Test: Statistical significance of differences
    - Permutation Test: Non-parametric significance test
    - Effect Size: Practical significance of differences

    Query params:
        level: 'full' or 'level2' (default: 'level2')
        smoothing: Laplace smoothing parameter (default: 1.0)
        n_permutations: Number of permutations for permutation test (default: 1000)

    Returns:
        JSON object with comparison metrics and statistical tests

    References:
        - Anderson & Goodman (1957): Chi-square tests for Markov chains
        - Vautard et al. (1990): Monte Carlo significance tests for transition matrices
        - Lin (1991): Jensen-Shannon divergence for probability distributions
    """
    level_param = request.args.get('level', 'level2')
    smoothing_alpha = request.args.get('smoothing', 1.0, type=float)
    n_permutations = request.args.get('n_permutations', 1000, type=int)

    # Convert level parameter to integer
    level_int = 0 if level_param == 'full' else 2

    # Get all transition matrices for this analysis
    matrices = OnCoCoTransitionMatrix.query.filter_by(
        analysis_id=analysis_id,
        level=level_int
    ).all()

    if len(matrices) < 2:
        raise ValidationError('Need at least 2 pillars for comparison',
                            details={'pillars_found': len(matrices)})

    # Convert matrices to numpy arrays with consistent labels
    all_labels = set()
    for m in matrices:
        counts = m.matrix_counts_json or {}
        for from_label in counts:
            all_labels.add(from_label)
            for to_label in counts[from_label]:
                all_labels.add(to_label)

    sorted_labels = sorted(all_labels)
    n_labels = len(sorted_labels)
    label_to_idx = {label: i for i, label in enumerate(sorted_labels)}

    def dict_to_matrix(counts_dict, probs_dict):
        """Convert dict format to numpy matrices."""
        counts = np.zeros((n_labels, n_labels))
        probs = np.zeros((n_labels, n_labels))

        for from_label, transitions in (counts_dict or {}).items():
            if from_label in label_to_idx:
                i = label_to_idx[from_label]
                for to_label, count in transitions.items():
                    if to_label in label_to_idx:
                        j = label_to_idx[to_label]
                        counts[i, j] = count

        for from_label, transitions in (probs_dict or {}).items():
            if from_label in label_to_idx:
                i = label_to_idx[from_label]
                for to_label, prob in transitions.items():
                    if to_label in label_to_idx:
                        j = label_to_idx[to_label]
                        probs[i, j] = prob

        return counts, probs

    def apply_laplace_smoothing(counts, alpha=1.0):
        """
        Apply Laplace (additive) smoothing to handle zero counts.

        Reference: Additive smoothing - Wikipedia
        https://en.wikipedia.org/wiki/Additive_smoothing
        """
        k = counts.shape[1]
        smoothed_counts = counts + alpha
        row_sums = smoothed_counts.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        smoothed_probs = smoothed_counts / row_sums
        return smoothed_probs

    def frobenius_distance(A, B):
        """
        Compute Frobenius norm of difference between two matrices.

        ||A - B||_F = sqrt(sum((A_ij - B_ij)^2))

        Reference: Data Science Stack Exchange - Comparing transition matrices
        https://datascience.stackexchange.com/questions/18457/comparing-transition-matrices-for-markov-chains
        """
        return np.linalg.norm(A - B, 'fro')

    def jensen_shannon_per_row(P, Q):
        """
        Compute Jensen-Shannon divergence for each row (from-state).

        JSD(P||Q) = 0.5 * KL(P||M) + 0.5 * KL(Q||M), where M = 0.5 * (P + Q)

        Reference: Jensen-Shannon divergence - Wikipedia
        https://en.wikipedia.org/wiki/Jensen–Shannon_divergence
        """
        jsd_values = []
        for i in range(P.shape[0]):
            p_row = P[i]
            q_row = Q[i]
            # Handle zero rows
            if p_row.sum() == 0 and q_row.sum() == 0:
                jsd_values.append(0.0)
            elif p_row.sum() == 0 or q_row.sum() == 0:
                jsd_values.append(1.0)  # Maximum divergence
            else:
                # Normalize to ensure valid probability distributions
                p_norm = p_row / p_row.sum() if p_row.sum() > 0 else p_row
                q_norm = q_row / q_row.sum() if q_row.sum() > 0 else q_row
                jsd_values.append(jensenshannon(p_norm, q_norm))
        return np.array(jsd_values)

    def chi_square_test_per_row(counts_A, counts_B):
        """
        Perform chi-square test for each row (from-state).

        Tests H0: The transition probabilities from state i are the same in both matrices.

        Reference: Anderson & Goodman (1957) - Statistical Inference about Markov Chains
        https://link.springer.com/article/10.1007/BF01032010
        """
        results = []
        for i in range(counts_A.shape[0]):
            row_A = counts_A[i]
            row_B = counts_B[i]

            # Skip rows with no observations
            if row_A.sum() == 0 and row_B.sum() == 0:
                results.append({'chi2': 0, 'p_value': 1.0, 'dof': 0, 'valid': False})
                continue

            # Create contingency table
            contingency = np.vstack([row_A, row_B])

            # Remove columns with all zeros
            non_zero_cols = contingency.sum(axis=0) > 0
            contingency = contingency[:, non_zero_cols]

            if contingency.shape[1] < 2:
                results.append({'chi2': 0, 'p_value': 1.0, 'dof': 0, 'valid': False})
                continue

            try:
                chi2, p_value, dof, expected = scipy_stats.chi2_contingency(contingency)
                results.append({
                    'chi2': float(chi2),
                    'p_value': float(p_value),
                    'dof': int(dof),
                    'valid': True
                })
            except Exception:
                results.append({'chi2': 0, 'p_value': 1.0, 'dof': 0, 'valid': False})

        return results

    def permutation_test(counts_A, counts_B, n_perms=1000):
        """
        Perform permutation test for overall matrix difference.

        Tests H0: Both matrices come from the same underlying distribution.

        Reference: Vautard et al. (1990) - Statistical Significance Test for Transition Matrices
        https://journals.ametsoc.org/view/journals/atsc/47/15/1520-0469_1990_047_1926_sstftm_2_0_co_2.xml
        """
        # Compute observed statistic
        probs_A = apply_laplace_smoothing(counts_A, smoothing_alpha)
        probs_B = apply_laplace_smoothing(counts_B, smoothing_alpha)
        observed_dist = frobenius_distance(probs_A, probs_B)

        # Combine counts
        combined = counts_A + counts_B
        total_A = counts_A.sum()
        total_B = counts_B.sum()

        # Permutation distribution
        more_extreme = 0
        for _ in range(n_perms):
            # Randomly split combined counts
            perm_A = np.zeros_like(combined)
            perm_B = np.zeros_like(combined)

            for i in range(combined.shape[0]):
                for j in range(combined.shape[1]):
                    if combined[i, j] > 0:
                        # Randomly assign each count to A or B
                        n = int(combined[i, j])
                        assignments = np.random.binomial(n, total_A / (total_A + total_B))
                        perm_A[i, j] = assignments
                        perm_B[i, j] = n - assignments

            perm_probs_A = apply_laplace_smoothing(perm_A, smoothing_alpha)
            perm_probs_B = apply_laplace_smoothing(perm_B, smoothing_alpha)
            perm_dist = frobenius_distance(perm_probs_A, perm_probs_B)

            if perm_dist >= observed_dist:
                more_extreme += 1

        p_value = (more_extreme + 1) / (n_perms + 1)  # Add 1 for observed
        return {
            'observed_distance': float(observed_dist),
            'p_value': float(p_value),
            'n_permutations': n_perms,
            'more_extreme_count': more_extreme
        }

    def compute_effect_size(counts_A, counts_B, probs_A, probs_B):
        """
        Compute effect size metrics for matrix comparison.

        Includes:
        - Normalized Frobenius distance (0-1 scale)
        - Cramér's V (for overall association)
        - Element-wise effect sizes

        Reference: Effect size - Wikipedia
        https://en.wikipedia.org/wiki/Effect_size
        """
        # Normalized Frobenius (max possible is sqrt(2*n) for probability matrices)
        frob_dist = frobenius_distance(probs_A, probs_B)
        max_frob = np.sqrt(2 * probs_A.shape[0])
        normalized_frob = frob_dist / max_frob if max_frob > 0 else 0

        # Cramér's V for overall contingency
        total_counts = counts_A + counts_B
        n_total = total_counts.sum()

        if n_total > 0:
            try:
                # Flatten and compute chi-square
                flat_A = counts_A.flatten()
                flat_B = counts_B.flatten()
                contingency = np.vstack([flat_A, flat_B])

                # Remove zero columns
                non_zero = contingency.sum(axis=0) > 0
                contingency = contingency[:, non_zero]

                if contingency.shape[1] >= 2:
                    chi2, _, _, _ = scipy_stats.chi2_contingency(contingency)
                    min_dim = min(contingency.shape[0] - 1, contingency.shape[1] - 1)
                    cramers_v = np.sqrt(chi2 / (n_total * min_dim)) if min_dim > 0 else 0
                else:
                    cramers_v = 0
            except Exception:
                cramers_v = 0
        else:
            cramers_v = 0

        return {
            'normalized_frobenius': float(normalized_frob),
            'cramers_v': float(cramers_v),
            'interpretation': {
                'frobenius': 'small' if normalized_frob < 0.1 else 'medium' if normalized_frob < 0.3 else 'large',
                'cramers_v': 'negligible' if cramers_v < 0.1 else 'small' if cramers_v < 0.3 else 'medium' if cramers_v < 0.5 else 'large'
            }
        }

    def identify_outlier_transitions(probs_A, probs_B, threshold=2.0):
        """
        Identify transitions that differ significantly between matrices.

        Uses z-score based threshold on probability differences.
        """
        diff = np.abs(probs_A - probs_B)
        mean_diff = np.nanmean(diff)
        std_diff = np.nanstd(diff)

        if std_diff == 0:
            return []

        outliers = []
        for i in range(diff.shape[0]):
            for j in range(diff.shape[1]):
                z_score = (diff[i, j] - mean_diff) / std_diff
                if z_score > threshold:
                    outliers.append({
                        'from_label': sorted_labels[i],
                        'to_label': sorted_labels[j],
                        'prob_A': float(probs_A[i, j]),
                        'prob_B': float(probs_B[i, j]),
                        'difference': float(diff[i, j]),
                        'z_score': float(z_score)
                    })

        return sorted(outliers, key=lambda x: -x['z_score'])[:20]  # Top 20

    def identify_missing_transitions(counts_A, counts_B):
        """
        Identify transitions that exist in one matrix but not the other.

        These are potential sampling artifacts or true differences.
        """
        missing_in_A = []
        missing_in_B = []

        for i in range(counts_A.shape[0]):
            for j in range(counts_A.shape[1]):
                if counts_A[i, j] == 0 and counts_B[i, j] > 0:
                    missing_in_A.append({
                        'from_label': sorted_labels[i],
                        'to_label': sorted_labels[j],
                        'count_in_other': int(counts_B[i, j])
                    })
                elif counts_B[i, j] == 0 and counts_A[i, j] > 0:
                    missing_in_B.append({
                        'from_label': sorted_labels[i],
                        'to_label': sorted_labels[j],
                        'count_in_other': int(counts_A[i, j])
                    })

        return {
            'missing_in_A': sorted(missing_in_A, key=lambda x: -x['count_in_other'])[:10],
            'missing_in_B': sorted(missing_in_B, key=lambda x: -x['count_in_other'])[:10]
        }

    # Prepare matrices for comparison
    pillar_data = {}
    for m in matrices:
        counts, probs = dict_to_matrix(m.matrix_counts_json, m.matrix_probs_json)
        smoothed_probs = apply_laplace_smoothing(counts, smoothing_alpha)
        pillar_data[m.pillar_number] = {
            'counts': counts,
            'probs': probs,
            'smoothed_probs': smoothed_probs,
            'total_transitions': m.total_transitions,
            'pillar_name': PILLAR_CONFIG.get(m.pillar_number, {}).get('name', f'Säule {m.pillar_number}')
        }

    # Compute pairwise comparisons
    pillar_numbers = sorted(pillar_data.keys())
    pairwise_comparisons = []

    for i, pn_a in enumerate(pillar_numbers):
        for pn_b in pillar_numbers[i+1:]:
            data_A = pillar_data[pn_a]
            data_B = pillar_data[pn_b]

            # Compute all metrics
            frob_dist = frobenius_distance(data_A['smoothed_probs'], data_B['smoothed_probs'])
            jsd_per_row = jensen_shannon_per_row(data_A['smoothed_probs'], data_B['smoothed_probs'])
            chi_sq_results = chi_square_test_per_row(data_A['counts'], data_B['counts'])
            perm_result = permutation_test(data_A['counts'], data_B['counts'], n_permutations)
            effect_size = compute_effect_size(data_A['counts'], data_B['counts'],
                                             data_A['smoothed_probs'], data_B['smoothed_probs'])
            outliers = identify_outlier_transitions(data_A['smoothed_probs'], data_B['smoothed_probs'])
            missing = identify_missing_transitions(data_A['counts'], data_B['counts'])

            # Aggregate chi-square results
            valid_chi_sq = [r for r in chi_sq_results if r['valid']]
            significant_rows = sum(1 for r in valid_chi_sq if r['p_value'] < 0.05)

            pairwise_comparisons.append({
                'pillar_a': {
                    'number': pn_a,
                    'name': data_A['pillar_name'],
                    'total_transitions': data_A['total_transitions']
                },
                'pillar_b': {
                    'number': pn_b,
                    'name': data_B['pillar_name'],
                    'total_transitions': data_B['total_transitions']
                },
                'metrics': {
                    'frobenius_distance': float(frob_dist),
                    'mean_jsd': float(np.nanmean(jsd_per_row)),
                    'max_jsd': float(np.nanmax(jsd_per_row)),
                    'jsd_per_row': {sorted_labels[i]: float(v) for i, v in enumerate(jsd_per_row) if not np.isnan(v)}
                },
                'statistical_tests': {
                    'chi_square': {
                        'significant_rows': significant_rows,
                        'total_rows': len(valid_chi_sq),
                        'proportion_significant': significant_rows / len(valid_chi_sq) if valid_chi_sq else 0,
                        'row_details': {sorted_labels[i]: chi_sq_results[i] for i in range(len(chi_sq_results))}
                    },
                    'permutation_test': perm_result
                },
                'effect_size': effect_size,
                'outlier_transitions': outliers,
                'missing_transitions': missing
            })

    # Build response
    response = {
        'analysis_id': analysis_id,
        'level': level_param,
        'labels': sorted_labels,
        'label_displays': {l: get_label_display_name(l, 'de') for l in sorted_labels},
        'n_labels': n_labels,
        'smoothing_alpha': smoothing_alpha,
        'pillars': {
            pn: {
                'name': data['pillar_name'],
                'total_transitions': data['total_transitions']
            }
            for pn, data in pillar_data.items()
        },
        'pairwise_comparisons': pairwise_comparisons,
        'methodology': {
            'frobenius_distance': {
                'description': 'Frobenius-Norm der Differenz zweier Matrizen. Misst den Gesamtunterschied.',
                'formula': '||A - B||_F = sqrt(sum((A_ij - B_ij)²))',
                'interpretation': 'Kleinere Werte bedeuten ähnlichere Matrizen. 0 = identisch.',
                'reference': 'https://datascience.stackexchange.com/questions/18457/comparing-transition-matrices-for-markov-chains'
            },
            'jensen_shannon_divergence': {
                'description': 'Symmetrische Divergenz-Metrik für Wahrscheinlichkeitsverteilungen (pro Zeile).',
                'formula': 'JSD(P||Q) = 0.5 * KL(P||M) + 0.5 * KL(Q||M), M = 0.5*(P+Q)',
                'interpretation': 'Werte zwischen 0 (identisch) und 1 (völlig unterschiedlich).',
                'reference': 'https://en.wikipedia.org/wiki/Jensen–Shannon_divergence'
            },
            'chi_square_test': {
                'description': 'Chi-Quadrat-Test für jede Zeile (Von-Zustand). Testet ob Übergangswahrscheinlichkeiten gleich sind.',
                'null_hypothesis': 'H₀: Übergangswahrscheinlichkeiten von Zustand i sind in beiden Matrizen gleich.',
                'interpretation': 'p < 0.05 bedeutet signifikanter Unterschied auf 5%-Niveau.',
                'reference': 'Anderson & Goodman (1957), https://link.springer.com/article/10.1007/BF01032010'
            },
            'permutation_test': {
                'description': 'Non-parametrischer Test für Gesamt-Signifikanz. Permutiert Beobachtungen zwischen Matrizen.',
                'null_hypothesis': 'H₀: Beide Matrizen stammen aus derselben Verteilung.',
                'interpretation': 'p < 0.05 bedeutet die Matrizen sind signifikant unterschiedlich.',
                'reference': 'Vautard et al. (1990), https://journals.ametsoc.org/view/journals/atsc/47/15/1520-0469_1990_047_1926_sstftm_2_0_co_2.xml'
            },
            'effect_size': {
                'description': 'Praktische Bedeutsamkeit des Unterschieds (unabhängig von Stichprobengröße).',
                'cramers_v_interpretation': {
                    '<0.1': 'vernachlässigbar',
                    '0.1-0.3': 'schwach',
                    '0.3-0.5': 'mittel',
                    '>0.5': 'stark'
                },
                'reference': 'https://en.wikipedia.org/wiki/Effect_size'
            },
            'laplace_smoothing': {
                'description': 'Additive Glättung für Null-Werte. Verhindert log(0) und Division durch 0.',
                'formula': 'P_smoothed(i→j) = (count(i→j) + α) / (total_from_i + α × k)',
                'alpha_used': smoothing_alpha,
                'reference': 'https://en.wikipedia.org/wiki/Additive_smoothing'
            }
        }
    }

    return jsonify(response)
