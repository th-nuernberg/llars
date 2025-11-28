"""
OnCoCo Results Routes - Analysis results and statistics endpoints.

Provides endpoints for:
- Getting sentence-level classifications
- Retrieving label distributions
- Getting transition matrices
- Comparing pillars
"""

import logging
from flask import Blueprint, request, jsonify
from sqlalchemy import func

from db.db import db
from db.tables import (
    OnCoCoAnalysis,
    OnCoCoSentenceLabel, OnCoCoPillarStatistics,
    OnCoCoTransitionMatrix
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from services.oncoco import (
    get_oncoco_service,
    get_label_display_name
)
from services.judge.kia_sync_service import PILLAR_CONFIG

logger = logging.getLogger(__name__)

oncoco_results_bp = Blueprint('oncoco_results', __name__)


# ============================================================================
# ANALYSIS RESULTS
# ============================================================================

@oncoco_results_bp.route('/analyses/<int:analysis_id>/sentences', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_analysis_sentences(analysis_id: int):
    """
    Get sentence-level classifications for an analysis.

    Query params:
        pillar: Filter by pillar number
        thread_id: Filter by thread ID
        label: Filter by label
        role: Filter by role (counselor/client)
        limit: Max results (default 100)
        offset: Pagination offset

    Returns:
        JSON array of sentence classifications
    """
    query = OnCoCoSentenceLabel.query.filter_by(analysis_id=analysis_id)

    # Apply filters
    pillar = request.args.get('pillar', type=int)
    if pillar:
        query = query.filter_by(pillar_number=pillar)

    thread_id = request.args.get('thread_id', type=int)
    if thread_id:
        query = query.filter_by(thread_id=thread_id)

    label = request.args.get('label')
    if label:
        query = query.filter_by(label=label)

    role = request.args.get('role')
    if role:
        query = query.filter_by(role=role)

    # Pagination
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    total = query.count()
    sentences = query.order_by(
        OnCoCoSentenceLabel.thread_id,
        OnCoCoSentenceLabel.message_id,
        OnCoCoSentenceLabel.sentence_index
    ).offset(offset).limit(limit).all()

    result = [{
        'id': s.id,
        'thread_id': s.thread_id,
        'message_id': s.message_id,
        'pillar_number': s.pillar_number,
        'sentence_index': s.sentence_index,
        'sentence_text': s.sentence_text,
        'role': s.role,
        'label': s.label,
        'label_display': get_label_display_name(s.label, 'de'),
        'label_level2': s.label_level2,
        'label_level2_display': get_label_display_name(s.label_level2, 'de'),
        'confidence': s.confidence,
        'top_3': s.top_3_json
    } for s in sentences]

    return jsonify({
        'sentences': result,
        'total': total,
        'limit': limit,
        'offset': offset
    })


@oncoco_results_bp.route('/analyses/<int:analysis_id>/distribution', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_analysis_distribution(analysis_id: int):
    """
    Get label distribution for an analysis.

    Query params:
        pillar: Filter by pillar number
        level: 'full' or 'level2' (default: 'level2')
        role: 'counselor' or 'client' (optional) to filter by speaker role

    Returns:
        JSON object with label distribution
    """
    pillar = request.args.get('pillar', type=int)
    level = request.args.get('level', 'level2')
    role = request.args.get('role')

    allowed_roles = {'counselor', 'client'}
    if role and role not in allowed_roles:
        return jsonify({'error': 'Invalid role'}), 400

    # If a role filter is provided, compute distribution from sentence labels to respect speaker separation
    if role:
        label_column = OnCoCoSentenceLabel.label_level2 if level == 'level2' else OnCoCoSentenceLabel.label
        query = db.session.query(label_column, func.count(OnCoCoSentenceLabel.id)).filter(
            OnCoCoSentenceLabel.analysis_id == analysis_id,
            OnCoCoSentenceLabel.role == role
        )
        if pillar:
            query = query.filter(OnCoCoSentenceLabel.pillar_number == pillar)
        if level == 'level2':
            query = query.filter(OnCoCoSentenceLabel.label_level2.isnot(None))

        distribution = {}
        for label_value, count in query.group_by(label_column).all():
            if label_value:
                distribution[label_value] = distribution.get(label_value, 0) + count
    else:
        if pillar:
            stats = OnCoCoPillarStatistics.query.filter_by(
                analysis_id=analysis_id,
                pillar_number=pillar
            ).first()

            if not stats:
                return jsonify({'error': 'Pillar statistics not found'}), 404

            distribution = stats.label_distribution_level2_json if level == 'level2' else stats.label_distribution_json
        else:
            # Aggregate across all pillars
            all_stats = OnCoCoPillarStatistics.query.filter_by(
                analysis_id=analysis_id
            ).all()

            distribution = {}
            for stats in all_stats:
                src = stats.label_distribution_level2_json if level == 'level2' else stats.label_distribution_json
                for label, count in (src or {}).items():
                    distribution[label] = distribution.get(label, 0) + count

    # Add display names
    result = []
    for label, count in sorted(distribution.items(), key=lambda x: -x[1]):
        result.append({
            'label': label,
            'display_name': get_label_display_name(label, 'de'),
            'count': count,
            'role': 'counselor' if label.startswith('CO-') else 'client'
        })

    return jsonify({
        'distribution': result,
        'level': level,
        'pillar': pillar,
        'role': role or 'all'
    })


@oncoco_results_bp.route('/analyses/<int:analysis_id>/transition-matrix', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_transition_matrix(analysis_id: int):
    """
    Get transition matrix for an analysis.

    Query params:
        pillar: Filter by pillar number (required for specific pillar)
        level: 'full' or 'level2' (default: 'level2')
        format: 'matrix' or 'list' (default: 'matrix')
        role: 'counselor' or 'client' (optional) to filter by speaker role

    Returns:
        JSON object with transition matrix
    """
    pillar = request.args.get('pillar', type=int)
    level_param = request.args.get('level', 'level2')
    output_format = request.args.get('format', 'matrix')
    role = request.args.get('role')

    allowed_roles = {'counselor', 'client'}
    if role and role not in allowed_roles:
        return jsonify({'error': 'Invalid role'}), 400

    # Convert level parameter to integer: 'full' -> 0, 'level2' -> 2
    level_int = 0 if level_param == 'full' else 2

    # If role filter is provided, compute transition matrix directly from sentence labels with role separation
    if role:
        label_column = OnCoCoSentenceLabel.label if level_param == 'full' else OnCoCoSentenceLabel.label_level2
        query = OnCoCoSentenceLabel.query.filter_by(
            analysis_id=analysis_id,
            role=role
        )
        if pillar:
            query = query.filter_by(pillar_number=pillar)
        if level_param != 'full':
            query = query.filter(OnCoCoSentenceLabel.label_level2.isnot(None))

        # Preserve conversation order: pillar -> thread -> message -> sentence
        query = query.order_by(
            OnCoCoSentenceLabel.pillar_number.asc(),
            OnCoCoSentenceLabel.thread_id.asc(),
            OnCoCoSentenceLabel.message_id.asc(),
            OnCoCoSentenceLabel.sentence_index.asc()
        )

        label_values = [getattr(sl, 'label' if level_param == 'full' else 'label_level2') for sl in query.all() if getattr(sl, 'label' if level_param == 'full' else 'label_level2')]

        service = get_oncoco_service()
        counts, probs = service.compute_transition_matrix(label_values, use_level2=False)

        total_transitions = len(label_values) - 1 if label_values else 0
        all_labels = sorted(set(counts.keys()) | set(
            label for transitions in counts.values() for label in transitions.keys()
        ))

        if output_format == 'list':
            links = []
            for from_label, transitions in probs.items():
                for to_label, prob in transitions.items():
                    count = counts.get(from_label, {}).get(to_label, 0)
                    if count > 0:
                        links.append({
                            'source': from_label,
                            'source_display': get_label_display_name(from_label, 'de'),
                            'target': to_label,
                            'target_display': get_label_display_name(to_label, 'de'),
                            'value': count,
                            'probability': prob
                        })

            return jsonify({
                'links': sorted(links, key=lambda x: -x['value']),
                'level': level_param,
                'pillar': pillar,
                'role': role,
                'total_transitions': total_transitions
            })

        return jsonify({
            'labels': all_labels,
            'label_displays': {l: get_label_display_name(l, 'de') for l in all_labels},
            'counts': counts,
            'probabilities': probs,
            'level': level_param,
            'pillar': pillar,
            'role': role,
            'total_transitions': total_transitions
        })

    query = OnCoCoTransitionMatrix.query.filter_by(
        analysis_id=analysis_id,
        level=level_int
    )

    if pillar:
        query = query.filter_by(pillar_number=pillar)

    matrices = query.all()

    if not matrices:
        return jsonify({'error': 'Transition matrix not found'}), 404

    # Aggregate if multiple pillars
    if len(matrices) > 1:
        combined_counts = {}
        total_transitions = 0

        for m in matrices:
            for from_label, transitions in (m.matrix_counts_json or {}).items():
                if from_label not in combined_counts:
                    combined_counts[from_label] = {}
                for to_label, count in transitions.items():
                    combined_counts[from_label][to_label] = combined_counts[from_label].get(to_label, 0) + count
            total_transitions += m.total_transitions or 0

        # Recompute probabilities
        combined_probs = {}
        for from_label, transitions in combined_counts.items():
            total = sum(transitions.values())
            combined_probs[from_label] = {
                to_label: count / total if total > 0 else 0
                for to_label, count in transitions.items()
            }

        result_counts = combined_counts
        result_probs = combined_probs
    else:
        result_counts = matrices[0].matrix_counts_json or {}
        result_probs = matrices[0].matrix_probs_json or {}
        total_transitions = matrices[0].total_transitions or 0

    if output_format == 'list':
        # Convert to list format for Sankey diagrams
        links = []
        for from_label, transitions in result_probs.items():
            for to_label, prob in transitions.items():
                count = result_counts.get(from_label, {}).get(to_label, 0)
                if count > 0:
                    links.append({
                        'source': from_label,
                        'source_display': get_label_display_name(from_label, 'de'),
                        'target': to_label,
                        'target_display': get_label_display_name(to_label, 'de'),
                        'value': count,
                        'probability': prob
                    })

        return jsonify({
            'links': sorted(links, key=lambda x: -x['value']),
            'level': level_param,
            'pillar': pillar,
            'total_transitions': total_transitions
        })

    # Return matrix format
    # Get all labels for ordering
    all_labels = sorted(set(result_counts.keys()) | set(
        label for transitions in result_counts.values() for label in transitions.keys()
    ))

    return jsonify({
        'labels': all_labels,
        'label_displays': {l: get_label_display_name(l, 'de') for l in all_labels},
        'counts': result_counts,
        'probabilities': result_probs,
        'level': level_param,
        'pillar': pillar,
        'total_transitions': total_transitions
    })


@oncoco_results_bp.route('/analyses/<int:analysis_id>/comparison', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def compare_pillars(analysis_id: int):
    """
    Compare pillars within an analysis.

    Returns:
        JSON object with pillar comparison data
    """
    stats = OnCoCoPillarStatistics.query.filter_by(
        analysis_id=analysis_id
    ).all()

    if not stats:
        return jsonify({'error': 'No pillar statistics found'}), 404

    comparison = []
    for ps in stats:
        comparison.append({
            'pillar_number': ps.pillar_number,
            'pillar_name': PILLAR_CONFIG.get(ps.pillar_number, {}).get('name', f'Säule {ps.pillar_number}'),
            'metrics': {
                'total_threads': ps.total_threads,
                'total_messages': ps.total_messages,
                'total_sentences': ps.total_sentences,
                'counselor_sentences': ps.counselor_sentences,
                'client_sentences': ps.client_sentences,
                'counselor_ratio': ps.counselor_sentences / ps.total_sentences if ps.total_sentences > 0 else 0,
                'impact_factor_ratio': ps.impact_factor_ratio,
                'resource_activation_score': ps.resource_activation_score,
                'mi_score': ps.mi_score,
                'avg_confidence': ps.avg_confidence
            },
            'label_distribution_level2': ps.label_distribution_level2_json
        })

    return jsonify({
        'pillars': comparison,
        'analysis_id': analysis_id
    })
