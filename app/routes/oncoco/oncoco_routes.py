"""
OnCoCo Analysis API Routes for LLARS.

Provides REST API endpoints for:
- Creating and managing OnCoCo analyses
- Retrieving analysis results
- Getting label distributions and transition matrices
- Comparing pillars
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy import func

from db.db import db
from db.tables import (
    OnCoCoAnalysis, OnCoCoAnalysisStatus,
    OnCoCoSentenceLabel, OnCoCoPillarStatistics,
    OnCoCoTransitionMatrix, PillarThread, EmailThread, Message
)
from auth.decorators import authentik_required, debug_route_protected
from decorators.permission_decorator import require_permission
from services.oncoco import (
    get_oncoco_service, OnCoCoService,
    ONCOCO_LABELS, LABEL_HIERARCHY,
    get_label_display_name, get_label_level2
)
from services.judge.kia_sync_service import (
    get_kia_sync_service, PILLAR_CONFIG, SyncStatus
)
from socketio_handlers.events_oncoco import (
    emit_oncoco_progress, emit_oncoco_sentence, emit_oncoco_complete
)

logger = logging.getLogger(__name__)

oncoco_bp = Blueprint('oncoco', __name__, url_prefix='/api/oncoco')


# ============================================================================
# MODEL & LABEL INFO
# ============================================================================

@oncoco_bp.route('/info', methods=['GET'])
@authentik_required
def get_oncoco_info():
    """
    Get information about the OnCoCo model and label system.

    Returns:
        JSON object with model info and label counts
    """
    service = get_oncoco_service()

    return jsonify({
        'model': service.get_model_info(),
        'labels': {
            'total': len(ONCOCO_LABELS),
            'counselor': len([l for l in ONCOCO_LABELS if l.startswith('CO-')]),
            'client': len([l for l in ONCOCO_LABELS if l.startswith('CL-')]),
            'hierarchy_levels': len(LABEL_HIERARCHY)
        },
        'pillars': {
            pid: {'name': cfg['name'], 'path': cfg['path']}
            for pid, cfg in PILLAR_CONFIG.items()
        }
    })


@oncoco_bp.route('/labels', methods=['GET'])
@authentik_required
def get_labels():
    """
    Get all OnCoCo labels with metadata.

    Query params:
        role: Filter by 'counselor' or 'client'
        level: 'full' or 'level2' for aggregated view

    Returns:
        JSON object with labels
    """
    role = request.args.get('role')
    level = request.args.get('level', 'full')

    if level == 'level2':
        labels = LABEL_HIERARCHY
        if role:
            labels = {k: v for k, v in labels.items() if v.get('role') == role}
    else:
        labels = ONCOCO_LABELS
        if role:
            labels = {k: v for k, v in labels.items() if v.get('role') == role}

    return jsonify({
        'labels': labels,
        'count': len(labels)
    })


# ============================================================================
# PILLAR DATA STATUS
# ============================================================================

@oncoco_bp.route('/pillars', methods=['GET'])
@authentik_required
def get_pillars_status():
    """
    Get status of all pillars (local DB + GitLab availability).

    Returns:
        JSON object with pillar status
    """
    sync_service = get_kia_sync_service()
    status = sync_service.get_sync_status()

    return jsonify(status)


@oncoco_bp.route('/pillars/sync', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def sync_pillars():
    """
    Sync pillar data from GitLab.

    Body:
        pillars: List of pillar numbers to sync (optional, defaults to all)
        force: Force re-import even if data exists

    Returns:
        JSON object with sync results
    """
    data = request.get_json() or {}
    pillar_numbers = data.get('pillars')
    force = data.get('force', False)

    sync_service = get_kia_sync_service()

    if pillar_numbers:
        results = {}
        for pn in pillar_numbers:
            result = sync_service.sync_pillar(pn, force=force)
            results[pn] = {
                'success': result.success,
                'threads_created': result.threads_created,
                'threads_updated': result.threads_updated,
                'threads_skipped': result.threads_skipped,
                'errors': result.errors
            }
    else:
        sync_results = sync_service.sync_all_pillars(force=force)
        results = {
            pn: {
                'success': r.success,
                'threads_created': r.threads_created,
                'threads_updated': r.threads_updated,
                'threads_skipped': r.threads_skipped,
                'errors': r.errors
            }
            for pn, r in sync_results.items()
        }

    return jsonify({
        'message': 'Sync complete',
        'results': results
    })


# ============================================================================
# ANALYSIS MANAGEMENT
# ============================================================================

@oncoco_bp.route('/analyses', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def list_analyses():
    """
    List all OnCoCo analyses for the current user.

    Returns:
        JSON array of analysis objects
    """
    username = g.authentik_user

    analyses = OnCoCoAnalysis.query.filter_by(
        user_id=username
    ).order_by(OnCoCoAnalysis.created_at.desc()).all()

    result = []
    for a in analyses:
        pillar_count = 0
        if a.config_json and 'pillars' in a.config_json:
            pillar_count = len(a.config_json['pillars'])

        result.append({
            'id': a.id,
            'name': a.name,
            'status': a.status.value,
            'total_threads': a.total_threads,
            'processed_threads': a.processed_threads,
            'total_sentences': a.total_sentences,
            'progress': (a.processed_threads / a.total_threads * 100)
                       if a.total_threads > 0 else 0,
            'pillar_count': pillar_count,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'started_at': a.started_at.isoformat() if a.started_at else None,
            'completed_at': a.completed_at.isoformat() if a.completed_at else None,
            'config': a.config_json
        })

    return jsonify(result)


@oncoco_bp.route('/analyses', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def create_analysis():
    """
    Create a new OnCoCo analysis.

    Body:
        name: Analysis name
        pillars: List of pillar numbers to analyze
        config: Additional configuration

    Returns:
        JSON object with created analysis
    """
    username = g.authentik_user
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400

    pillar_numbers = data.get('pillars', [1, 3, 5])  # Default active pillars

    # Count threads to process
    total_threads = PillarThread.query.filter(
        PillarThread.pillar_number.in_(pillar_numbers)
    ).count()

    if total_threads == 0:
        return jsonify({
            'error': 'No threads found for selected pillars. Please sync data first.'
        }), 400

    config = {
        'pillars': pillar_numbers,
        'use_level2': data.get('use_level2', True),
        'batch_size': data.get('batch_size', 16),
        **data.get('config', {})
    }

    analysis = OnCoCoAnalysis(
        user_id=username,
        name=data['name'],
        status=OnCoCoAnalysisStatus.PENDING,
        config_json=config,
        total_threads=total_threads,
        processed_threads=0,
        total_sentences=0
    )

    db.session.add(analysis)
    db.session.commit()

    logger.info(f"[OnCoCo] Created analysis {analysis.id} for user {username}")

    return jsonify({
        'id': analysis.id,
        'name': analysis.name,
        'status': analysis.status.value,
        'total_threads': total_threads,
        'config': config
    }), 201


@oncoco_bp.route('/analyses/<int:analysis_id>', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_analysis(analysis_id: int):
    """
    Get details of a specific analysis.

    Args:
        analysis_id: ID of the analysis

    Returns:
        JSON object with analysis details
    """
    analysis = OnCoCoAnalysis.query.get_or_404(analysis_id)

    # Get pillar statistics
    pillar_stats = OnCoCoPillarStatistics.query.filter_by(
        analysis_id=analysis_id
    ).all()

    pillar_data = {}
    for ps in pillar_stats:
        pillar_data[ps.pillar_number] = {
            'pillar_number': ps.pillar_number,
            'total_threads': ps.total_threads,
            'total_messages': ps.total_messages,
            'total_sentences': ps.total_sentences,
            'counselor_sentences': ps.counselor_sentences,
            'client_sentences': ps.client_sentences,
            'label_distribution': ps.label_distribution_json,
            'label_distribution_level2': ps.label_distribution_level2_json,
            'impact_factor_ratio': ps.impact_factor_ratio,
            'mi_score': ps.mi_score,
            'resource_activation_score': ps.resource_activation_score,
            'avg_confidence': ps.avg_confidence
        }

    return jsonify({
        'id': analysis.id,
        'name': analysis.name,
        'status': analysis.status.value,
        'total_threads': analysis.total_threads,
        'processed_threads': analysis.processed_threads,
        'total_sentences': analysis.total_sentences,
        'progress': (analysis.processed_threads / analysis.total_threads * 100)
                   if analysis.total_threads > 0 else 0,
        'config': analysis.config_json,
        'pillar_statistics': pillar_data,
        'error_message': analysis.error_message,
        'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
        'started_at': analysis.started_at.isoformat() if analysis.started_at else None,
        'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None
    })


@oncoco_bp.route('/analyses/<int:analysis_id>/start', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
def start_analysis(analysis_id: int):
    """
    Start or resume an OnCoCo analysis.

    This will classify all sentences in the selected threads.
    Progress updates are sent via Socket.IO.

    If the analysis is stuck in 'running' status (e.g., after server restart),
    it can be resumed by passing force=true in the request body.

    Args:
        analysis_id: ID of the analysis

    Returns:
        JSON object with status
    """
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
        # Reset to pending to allow restart, keeping existing progress
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

    # Start background processing using Flask-SocketIO background task
    try:
        socketio = current_app.extensions.get('socketio')
        app = current_app._get_current_object()  # Get actual app object for context

        # Determine if we should resume (skip already processed threads)
        should_resume = force_resume and analysis.processed_threads > 0

        # Start analysis in background thread
        socketio.start_background_task(
            _run_analysis_background,
            app,
            analysis.id,
            socketio,
            should_resume
        )

        action = 'resumed' if should_resume else 'started'
        logger.info(f"[OnCoCo] Analysis {analysis_id} {action} in background (resume={should_resume})")
        return jsonify({
            'message': f'Analysis {action}',
            'status': analysis.status.value,
            'resumed': should_resume
        })
    except Exception as e:
        logger.error(f"[OnCoCo] Failed to start analysis {analysis_id}: {e}")
        analysis.status = OnCoCoAnalysisStatus.FAILED
        analysis.error_message = str(e)
        db.session.commit()
        return jsonify({'error': str(e)}), 500


def _run_analysis_background(app, analysis_id: int, socketio, resume: bool = False):
    """
    Background wrapper for _run_analysis that handles app context.

    Args:
        app: Flask application instance
        analysis_id: ID of the analysis to run
        socketio: Socket.IO instance for live updates
        resume: If True, skip already processed threads (for resuming stuck analyses)
    """
    with app.app_context():
        analysis = OnCoCoAnalysis.query.get(analysis_id)
        if not analysis:
            logger.error(f"[OnCoCo] Analysis {analysis_id} not found")
            return

        try:
            _run_analysis(analysis, socketio=socketio, resume=resume)
        except Exception as e:
            logger.error(f"[OnCoCo] Analysis {analysis_id} failed: {e}")
            analysis.status = OnCoCoAnalysisStatus.FAILED
            analysis.error_message = str(e)
            db.session.commit()


def _run_analysis(analysis: OnCoCoAnalysis, socketio=None, resume: bool = False):
    """
    Run the OnCoCo analysis on all threads.

    This is called synchronously for now, but can be moved to a background worker.
    Emits Socket.IO events for live progress updates if socketio is provided.

    Args:
        analysis: The analysis to run
        socketio: Socket.IO instance for live updates
        resume: If True, skip already processed threads (for resuming stuck analyses)
    """
    import time
    start_time = time.time()

    service = get_oncoco_service()
    config = analysis.config_json or {}
    pillar_numbers = config.get('pillars', [1, 3, 5])

    # Get hardware info once at start
    hardware_info = service.get_hardware_info()

    # For resume: get already processed thread IDs
    processed_thread_ids = set()
    if resume:
        existing_labels = OnCoCoSentenceLabel.query.filter_by(
            analysis_id=analysis.id
        ).with_entities(OnCoCoSentenceLabel.thread_id).distinct().all()
        processed_thread_ids = {t[0] for t in existing_labels}
        logger.info(f"[OnCoCo] Resuming analysis {analysis.id}, skipping {len(processed_thread_ids)} already processed threads")

    # Initialize pillar statistics
    pillar_stats = {pn: {
        'threads': 0,
        'messages': 0,
        'sentences': 0,
        'counselor_sentences': 0,
        'client_sentences': 0,
        'labels': {},
        'labels_level2': {},
        'all_labels': [],
        'confidences': []
    } for pn in pillar_numbers}

    # If resuming, load existing stats from already processed sentences
    if resume and processed_thread_ids:
        existing_sentences = OnCoCoSentenceLabel.query.filter_by(analysis_id=analysis.id).all()
        for sent in existing_sentences:
            pn = sent.pillar_number
            if pn in pillar_stats:
                ps = pillar_stats[pn]
                ps['sentences'] += 1
                ps['labels'][sent.label] = ps['labels'].get(sent.label, 0) + 1
                ps['labels_level2'][sent.label_level2] = ps['labels_level2'].get(sent.label_level2, 0) + 1
                ps['all_labels'].append(sent.label)
                ps['confidences'].append(sent.confidence)
                if sent.role == 'counselor':
                    ps['counselor_sentences'] += 1
                else:
                    ps['client_sentences'] += 1

    total_sentences = analysis.total_sentences if resume else 0
    processed_threads = analysis.processed_threads if resume else 0
    current_thread_info = None
    current_message_info = None
    last_sentence_info = None

    # Process each pillar
    for pillar_number in pillar_numbers:
        pillar_threads = PillarThread.query.filter_by(
            pillar_number=pillar_number
        ).all()

        pillar_name = PILLAR_CONFIG.get(pillar_number, {}).get('name', f'Saeule {pillar_number}')

        for pt in pillar_threads:
            # Skip already processed threads when resuming
            if resume and pt.thread_id in processed_thread_ids:
                continue

            # Get messages for this thread
            messages = Message.query.filter_by(
                thread_id=pt.thread_id
            ).order_by(Message.timestamp.asc()).all()

            if not messages:
                continue

            # Update current thread info
            current_thread_info = {
                'thread_id': pt.thread_id,
                'pillar_number': pillar_number,
                'pillar_name': pillar_name,
                'message_count': len(messages)
            }

            # Analyze each message
            for msg_idx, msg in enumerate(messages):
                # Determine role hint
                sender_lower = (msg.sender or '').lower()
                role_hint = None
                if any(term in sender_lower for term in ['berater', 'counsellor', 'counselor', 'assistant', 'bot']):
                    role_hint = "counselor"
                elif any(term in sender_lower for term in ['klient', 'client', 'user', 'ratsuchend']):
                    role_hint = "client"

                # Update current message info
                current_message_info = {
                    'message_id': msg.message_id,
                    'message_index': msg_idx + 1,
                    'total_messages': len(messages),
                    'sender': msg.sender or 'Unknown',
                    'content_preview': (msg.content or '')[:100] + '...' if len(msg.content or '') > 100 else (msg.content or '')
                }

                # Analyze message
                msg_analysis = service.analyze_message(
                    message_id=msg.message_id,
                    sender=msg.sender or '',
                    content=msg.content or '',
                    role_hint=role_hint
                )

                # Store sentence labels
                for idx, sent in enumerate(msg_analysis.sentences):
                    sentence_label = OnCoCoSentenceLabel(
                        analysis_id=analysis.id,
                        thread_id=pt.thread_id,
                        message_id=msg.message_id,
                        pillar_number=pillar_number,
                        sentence_index=idx,
                        sentence_text=sent.sentence[:1000],  # Truncate long sentences
                        role=sent.role,
                        label=sent.label,
                        label_level2=sent.label_level2,
                        confidence=sent.confidence,
                        top_3_json=sent.top_3
                    )
                    db.session.add(sentence_label)

                    # Track last sentence for display
                    last_sentence_info = {
                        'text': sent.sentence[:80] + '...' if len(sent.sentence) > 80 else sent.sentence,
                        'label': sent.label,
                        'label_display': get_label_display_name(sent.label, 'de'),
                        'confidence': round(sent.confidence * 100, 1),
                        'role': sent.role
                    }

                    # Update pillar stats
                    ps = pillar_stats[pillar_number]
                    ps['sentences'] += 1
                    ps['labels'][sent.label] = ps['labels'].get(sent.label, 0) + 1
                    ps['labels_level2'][sent.label_level2] = ps['labels_level2'].get(sent.label_level2, 0) + 1
                    ps['all_labels'].append(sent.label)
                    ps['confidences'].append(sent.confidence)

                    if sent.role == 'counselor':
                        ps['counselor_sentences'] += 1
                    else:
                        ps['client_sentences'] += 1

                    total_sentences += 1

                pillar_stats[pillar_number]['messages'] += 1

            pillar_stats[pillar_number]['threads'] += 1
            processed_threads += 1

            # Update progress every thread (more frequent updates)
            elapsed = time.time() - start_time
            analysis.processed_threads = processed_threads
            analysis.total_sentences = total_sentences
            db.session.commit()

            # Emit Socket.IO progress event with detailed info
            if socketio:
                emit_oncoco_progress(
                    socketio,
                    analysis.id,
                    processed_threads,
                    analysis.total_threads,
                    total_sentences,
                    current_thread=current_thread_info,
                    current_message=current_message_info,
                    hardware_info=hardware_info,
                    timing_info={
                        'elapsed': elapsed,
                        'last_sentence': last_sentence_info
                    }
                )

    # Compute and store pillar statistics
    for pillar_number, ps in pillar_stats.items():
        if ps['sentences'] == 0:
            continue

        # Compute transition matrix
        counts, probs = service.compute_transition_matrix(ps['all_labels'], use_level2=False)
        counts_l2, probs_l2 = service.compute_transition_matrix(ps['all_labels'], use_level2=True)

        # Compute metrics
        impact_factor_ratio = service.compute_impact_factor_ratio(ps['labels'])
        ra_score = service.compute_resource_activation_score(ps['labels'])
        mi_score = service.compute_mutual_information(counts)
        avg_confidence = sum(ps['confidences']) / len(ps['confidences']) if ps['confidences'] else 0

        # Store pillar statistics
        pillar_stat = OnCoCoPillarStatistics(
            analysis_id=analysis.id,
            pillar_number=pillar_number,
            total_threads=ps['threads'],
            total_messages=ps['messages'],
            total_sentences=ps['sentences'],
            counselor_sentences=ps['counselor_sentences'],
            client_sentences=ps['client_sentences'],
            label_distribution_json=ps['labels'],
            label_distribution_level2_json=ps['labels_level2'],
            impact_factor_ratio=impact_factor_ratio,
            mi_score=mi_score,
            resource_activation_score=ra_score,
            avg_confidence=avg_confidence
        )
        db.session.add(pillar_stat)

        # Store transition matrices
        # level: 0 = full detail, 2 = level2 aggregated
        tm_full = OnCoCoTransitionMatrix(
            analysis_id=analysis.id,
            pillar_number=pillar_number,
            level=0,  # 0 = full detail
            matrix_counts_json=counts,
            matrix_probs_json=probs,
            total_transitions=len(ps['all_labels']) - 1
        )
        db.session.add(tm_full)

        tm_l2 = OnCoCoTransitionMatrix(
            analysis_id=analysis.id,
            pillar_number=pillar_number,
            level=2,  # 2 = level2 aggregated
            matrix_counts_json=counts_l2,
            matrix_probs_json=probs_l2,
            total_transitions=len(ps['all_labels']) - 1
        )
        db.session.add(tm_l2)

    # Update analysis status
    total_duration = time.time() - start_time
    analysis.processed_threads = processed_threads
    analysis.total_sentences = total_sentences
    analysis.status = OnCoCoAnalysisStatus.COMPLETED
    analysis.completed_at = datetime.utcnow()
    db.session.commit()

    # Emit completion event with timing info
    if socketio:
        emit_oncoco_complete(
            socketio,
            analysis.id,
            'completed',
            total_sentences,
            duration_seconds=total_duration,
            hardware_info=hardware_info
        )

    logger.info(f"[OnCoCo] Analysis {analysis.id} completed: {processed_threads} threads, {total_sentences} sentences in {total_duration:.1f}s")


@oncoco_bp.route('/analyses/<int:analysis_id>', methods=['DELETE'])
@authentik_required
@require_permission('feature:comparison:edit')
def delete_analysis(analysis_id: int):
    """
    Delete an OnCoCo analysis and all related data.

    Args:
        analysis_id: ID of the analysis

    Returns:
        JSON object with status
    """
    analysis = OnCoCoAnalysis.query.get_or_404(analysis_id)

    # Delete related data
    OnCoCoSentenceLabel.query.filter_by(analysis_id=analysis_id).delete()
    OnCoCoPillarStatistics.query.filter_by(analysis_id=analysis_id).delete()
    OnCoCoTransitionMatrix.query.filter_by(analysis_id=analysis_id).delete()

    db.session.delete(analysis)
    db.session.commit()

    logger.info(f"[OnCoCo] Deleted analysis {analysis_id}")

    return jsonify({'message': 'Analysis deleted'})


# ============================================================================
# ANALYSIS RESULTS
# ============================================================================

@oncoco_bp.route('/analyses/<int:analysis_id>/sentences', methods=['GET'])
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


@oncoco_bp.route('/analyses/<int:analysis_id>/distribution', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_analysis_distribution(analysis_id: int):
    """
    Get label distribution for an analysis.

    Query params:
        pillar: Filter by pillar number
        level: 'full' or 'level2' (default: 'level2')

    Returns:
        JSON object with label distribution
    """
    pillar = request.args.get('pillar', type=int)
    level = request.args.get('level', 'level2')

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
        'pillar': pillar
    })


@oncoco_bp.route('/analyses/<int:analysis_id>/transition-matrix', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def get_transition_matrix(analysis_id: int):
    """
    Get transition matrix for an analysis.

    Query params:
        pillar: Filter by pillar number (required for specific pillar)
        level: 'full' or 'level2' (default: 'level2')
        format: 'matrix' or 'list' (default: 'matrix')

    Returns:
        JSON object with transition matrix
    """
    pillar = request.args.get('pillar', type=int)
    level_param = request.args.get('level', 'level2')
    output_format = request.args.get('format', 'matrix')

    # Convert level parameter to integer: 'full' -> 0, 'level2' -> 2
    level_int = 0 if level_param == 'full' else 2

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


@oncoco_bp.route('/analyses/<int:analysis_id>/comparison', methods=['GET'])
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


# ============================================================================
# DEBUG ENDPOINTS (Development only)
# ============================================================================

@oncoco_bp.route('/debug/classify', methods=['POST'])
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


@oncoco_bp.route('/debug/analyses', methods=['GET'])
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


@oncoco_bp.route('/debug/analyses/<int:analysis_id>/start', methods=['POST'])
@debug_route_protected
def debug_start_analysis(analysis_id: int):
    """
    DEBUG: Start or resume an analysis.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header or api_key query param.
    Only available in development mode.
    """
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


@oncoco_bp.route('/debug/analyses/<int:analysis_id>/complete', methods=['POST'])
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


@oncoco_bp.route('/debug/analyses/<int:analysis_id>/recompute-stats', methods=['POST'])
@debug_route_protected
def debug_recompute_statistics(analysis_id: int):
    """
    DEBUG: Recompute pillar statistics and transition matrices from existing sentence labels.
    Use this when an analysis was interrupted before statistics were computed.
    Requires SYSTEM_ADMIN_API_KEY via X-API-Key header or api_key query param.
    Only available in development mode.
    """
    from collections import defaultdict

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
