"""
OnCoCo Debug Routes - Debug and admin endpoints (development only).

Provides endpoints for:
- Classifying single sentences (testing)
- Listing all analyses (admin)
- Starting/completing analyses (admin)
- Recomputing statistics (recovery)
"""

import logging
from collections import defaultdict
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app

from db.db import db
from db.tables import (
    OnCoCoAnalysis, OnCoCoAnalysisStatus,
    OnCoCoSentenceLabel, OnCoCoPillarStatistics,
    OnCoCoTransitionMatrix
)
from auth.decorators import debug_route_protected
from services.oncoco import (
    get_oncoco_service,
    get_label_display_name, get_label_level2
)

logger = logging.getLogger(__name__)

oncoco_debug_bp = Blueprint('oncoco_debug', __name__)


# ============================================================================
# DEBUG ENDPOINTS (Development only)
# ============================================================================

@oncoco_debug_bp.route('/debug/classify', methods=['POST'])
@debug_route_protected
def debug_classify():
    """
    DEBUG: Classify a single sentence.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header or api_key query param.
    Only available in development mode.
    """
    data = request.get_json()
    if not data or 'sentence' not in data:
        return jsonify({'error': 'sentence is required'}), 400

    service = get_oncoco_service()

    if not service.is_model_available():
        return jsonify({'error': 'Model not available'}), 500

    result = service.classify_sentence(
        data['sentence'],
        role_hint=data.get('role_hint')
    )

    return jsonify({
        'sentence': result.sentence,
        'label': result.label,
        'label_display': get_label_display_name(result.label, 'de'),
        'label_level2': result.label_level2,
        'label_level2_display': get_label_display_name(result.label_level2, 'de'),
        'confidence': result.confidence,
        'role': result.role,
        'top_3': [
            {'label': l, 'display': get_label_display_name(l, 'de'), 'confidence': c}
            for l, c in result.top_3
        ]
    })


@oncoco_debug_bp.route('/debug/analyses', methods=['GET'])
@debug_route_protected
def debug_list_analyses():
    """
    DEBUG: List all analyses.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header or api_key query param.
    Only available in development mode.
    """
    analyses = OnCoCoAnalysis.query.order_by(OnCoCoAnalysis.created_at.desc()).all()

    result = []
    for a in analyses:
        result.append({
            'id': a.id,
            'name': a.name,
            'user_id': a.user_id,
            'status': a.status.value,
            'total_threads': a.total_threads,
            'processed_threads': a.processed_threads,
            'total_sentences': a.total_sentences,
            'created_at': a.created_at.isoformat() if a.created_at else None
        })

    return jsonify(result)


@oncoco_debug_bp.route('/debug/analyses/<int:analysis_id>/start', methods=['POST'])
@debug_route_protected
def debug_start_analysis(analysis_id: int):
    """
    DEBUG: Start or resume an analysis.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header or api_key query param.
    Only available in development mode.
    """
    # Import helper functions from analysis routes
    from routes.oncoco.oncoco_analysis_routes import _run_analysis_background

    analysis = OnCoCoAnalysis.query.get_or_404(analysis_id)
    # Handle POST with no body or non-JSON content type
    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}
    force_resume = data.get('force', False)

    # Allow resuming stuck 'running' analyses with force flag
    if analysis.status == OnCoCoAnalysisStatus.RUNNING:
        if not force_resume:
            return jsonify({
                'error': 'Analysis is already running. Use force=true to resume if stuck.',
                'hint': 'The analysis may be stuck after a server restart. Use force=true to resume.'
            }), 400
        logger.info(f"[OnCoCo] Force resuming stuck analysis {analysis_id}")

    if analysis.status not in [OnCoCoAnalysisStatus.PENDING, OnCoCoAnalysisStatus.FAILED, OnCoCoAnalysisStatus.RUNNING]:
        return jsonify({
            'error': f'Cannot start analysis in {analysis.status.value} status'
        }), 400

    # Check model availability
    service = get_oncoco_service()
    if not service.is_model_available():
        return jsonify({
            'error': 'OnCoCo model not available. Please check model path.'
        }), 500

    # Update status
    analysis.status = OnCoCoAnalysisStatus.RUNNING
    analysis.started_at = datetime.utcnow()
    analysis.error_message = None
    db.session.commit()

    # Start background processing
    try:
        socketio = current_app.extensions.get('socketio')
        app = current_app._get_current_object()

        should_resume = force_resume and analysis.processed_threads > 0

        socketio.start_background_task(
            _run_analysis_background,
            app,
            analysis.id,
            socketio,
            should_resume
        )

        action = 'resumed' if should_resume else 'started'
        logger.info(f"[OnCoCo DEBUG] Analysis {analysis_id} {action} in background (resume={should_resume})")
        return jsonify({
            'message': f'Analysis {action}',
            'status': analysis.status.value,
            'resumed': should_resume,
            'processed_threads': analysis.processed_threads,
            'total_threads': analysis.total_threads
        })
    except Exception as e:
        logger.error(f"[OnCoCo] Failed to start analysis {analysis_id}: {e}")
        analysis.status = OnCoCoAnalysisStatus.FAILED
        analysis.error_message = str(e)
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@oncoco_debug_bp.route('/debug/analyses/<int:analysis_id>/complete', methods=['POST'])
@debug_route_protected
def debug_complete_analysis(analysis_id: int):
    """
    DEBUG: Mark a stuck analysis as completed.
    Use this when an analysis reached 100% but status is still 'running' (e.g., after server restart).
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header or api_key query param.
    Only available in development mode.
    """
    analysis = OnCoCoAnalysis.query.get_or_404(analysis_id)

    # Only allow completing 'running' analyses that have reached 100%
    if analysis.status != OnCoCoAnalysisStatus.RUNNING:
        return jsonify({
            'error': f'Cannot complete analysis in {analysis.status.value} status. Only running analyses can be completed.',
            'current_status': analysis.status.value
        }), 400

    if analysis.total_threads == 0:
        return jsonify({
            'error': 'Analysis has no threads configured',
            'total_threads': analysis.total_threads
        }), 400

    progress = (analysis.processed_threads / analysis.total_threads * 100) if analysis.total_threads > 0 else 0

    if progress < 100:
        return jsonify({
            'error': f'Analysis is not complete yet ({progress:.1f}%). Wait for it to finish or use force=true.',
            'progress': progress,
            'processed_threads': analysis.processed_threads,
            'total_threads': analysis.total_threads
        }), 400

    # Mark as completed
    analysis.status = OnCoCoAnalysisStatus.COMPLETED
    analysis.completed_at = datetime.utcnow()
    db.session.commit()

    logger.info(f"[OnCoCo DEBUG] Analysis {analysis_id} marked as completed (was stuck at 100%)")

    return jsonify({
        'message': 'Analysis marked as completed',
        'analysis_id': analysis_id,
        'status': analysis.status.value,
        'processed_threads': analysis.processed_threads,
        'total_threads': analysis.total_threads,
        'total_sentences': analysis.total_sentences
    })


@oncoco_debug_bp.route('/debug/analyses/<int:analysis_id>/recompute-stats', methods=['POST'])
@debug_route_protected
def debug_recompute_statistics(analysis_id: int):
    """
    DEBUG: Recompute pillar statistics and transition matrices from existing sentence labels.
    Use this when an analysis was interrupted before statistics were computed.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header or api_key query param.
    Only available in development mode.
    """
    analysis = OnCoCoAnalysis.query.get_or_404(analysis_id)

    # Get all sentence labels for this analysis
    sentence_labels = OnCoCoSentenceLabel.query.filter_by(analysis_id=analysis_id).all()

    if not sentence_labels:
        return jsonify({
            'error': 'No sentence labels found for this analysis',
            'analysis_id': analysis_id
        }), 404

    # Delete existing statistics (if any)
    OnCoCoPillarStatistics.query.filter_by(analysis_id=analysis_id).delete()
    OnCoCoTransitionMatrix.query.filter_by(analysis_id=analysis_id).delete()
    db.session.commit()

    # Rebuild pillar statistics from sentence labels
    service = get_oncoco_service()

    pillar_stats = defaultdict(lambda: {
        'threads': set(),
        'messages': 0,
        'sentences': 0,
        'counselor_sentences': 0,
        'client_sentences': 0,
        'labels': defaultdict(int),
        'labels_level2': defaultdict(int),
        'all_labels': [],
        'confidences': []
    })

    for sl in sentence_labels:
        ps = pillar_stats[sl.pillar_number]
        ps['threads'].add(sl.thread_id)
        ps['sentences'] += 1
        ps['confidences'].append(sl.confidence)
        ps['labels'][sl.label] += 1
        ps['all_labels'].append(sl.label)

        # Aggregate to level2
        level2 = get_label_level2(sl.label)
        ps['labels_level2'][level2] += 1

        if sl.role == 'counselor':
            ps['counselor_sentences'] += 1
        else:
            ps['client_sentences'] += 1

    # Count unique messages per pillar
    for sl in sentence_labels:
        ps = pillar_stats[sl.pillar_number]
        # We don't have message_id in sentence labels, so we estimate
        # by counting unique (thread_id, message_index) combinations
        # For now, just set messages = sentences (approximation)

    # Compute and store statistics for each pillar
    stats_created = 0
    matrices_created = 0

    for pillar_number, ps in pillar_stats.items():
        if ps['sentences'] == 0:
            continue

        # Convert defaultdicts to regular dicts
        labels_dict = dict(ps['labels'])
        labels_level2_dict = dict(ps['labels_level2'])

        # Compute transition matrix
        counts, probs = service.compute_transition_matrix(ps['all_labels'], use_level2=False)
        counts_l2, probs_l2 = service.compute_transition_matrix(ps['all_labels'], use_level2=True)

        # Compute metrics
        impact_factor_ratio = service.compute_impact_factor_ratio(labels_dict)
        ra_score = service.compute_resource_activation_score(labels_dict)
        mi_score = service.compute_mutual_information(counts)
        avg_confidence = sum(ps['confidences']) / len(ps['confidences']) if ps['confidences'] else 0

        # Store pillar statistics
        pillar_stat = OnCoCoPillarStatistics(
            analysis_id=analysis_id,
            pillar_number=pillar_number,
            total_threads=len(ps['threads']),
            total_messages=ps['sentences'],  # Approximation
            total_sentences=ps['sentences'],
            counselor_sentences=ps['counselor_sentences'],
            client_sentences=ps['client_sentences'],
            label_distribution_json=labels_dict,
            label_distribution_level2_json=labels_level2_dict,
            impact_factor_ratio=impact_factor_ratio,
            mi_score=mi_score,
            resource_activation_score=ra_score,
            avg_confidence=avg_confidence
        )
        db.session.add(pillar_stat)
        stats_created += 1

        # Store transition matrices
        # level: 0 = full detail, 2 = level2 aggregated
        tm_full = OnCoCoTransitionMatrix(
            analysis_id=analysis_id,
            pillar_number=pillar_number,
            level=0,  # 0 = full detail
            matrix_counts_json=counts,
            matrix_probs_json=probs,
            total_transitions=len(ps['all_labels']) - 1 if ps['all_labels'] else 0
        )
        db.session.add(tm_full)
        matrices_created += 1

        tm_l2 = OnCoCoTransitionMatrix(
            analysis_id=analysis_id,
            pillar_number=pillar_number,
            level=2,  # 2 = level2 aggregated
            matrix_counts_json=counts_l2,
            matrix_probs_json=probs_l2,
            total_transitions=len(ps['all_labels']) - 1 if ps['all_labels'] else 0
        )
        db.session.add(tm_l2)
        matrices_created += 1

    db.session.commit()

    logger.info(f"[OnCoCo DEBUG] Recomputed statistics for analysis {analysis_id}: {stats_created} pillar stats, {matrices_created} transition matrices")

    return jsonify({
        'message': 'Statistics recomputed successfully',
        'analysis_id': analysis_id,
        'sentence_labels_processed': len(sentence_labels),
        'pillar_statistics_created': stats_created,
        'transition_matrices_created': matrices_created,
        'pillars': list(pillar_stats.keys())
    })
