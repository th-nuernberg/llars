"""
OnCoCo Analysis Routes - Analysis CRUD and execution endpoints.

Provides endpoints for:
- Creating and managing OnCoCo analyses
- Starting/resuming analysis execution
- Deleting analyses
"""

import logging
import time
from datetime import datetime

from flask import Blueprint, request, jsonify, g, current_app

from db.db import db
from db.tables import (
    OnCoCoAnalysis, OnCoCoAnalysisStatus,
    OnCoCoSentenceLabel, OnCoCoPillarStatistics,
    OnCoCoTransitionMatrix, PillarThread, Message
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from services.oncoco import (
    get_oncoco_service,
    get_label_display_name, get_label_level2
)
from services.judge.kia_sync_service import PILLAR_CONFIG
from socketio_handlers.events_oncoco import (
    emit_oncoco_progress, emit_oncoco_complete
)

logger = logging.getLogger(__name__)

oncoco_analysis_bp = Blueprint('oncoco_analysis', __name__)


# ============================================================================
# ANALYSIS MANAGEMENT
# ============================================================================

@oncoco_analysis_bp.route('/analyses', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='oncoco')
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


@oncoco_analysis_bp.route('/analyses', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='oncoco')
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
        raise ValidationError('Name is required')

    pillar_numbers = data.get('pillars', [1, 3, 5])  # Default active pillars

    # Count threads to process
    total_threads = PillarThread.query.filter(
        PillarThread.pillar_number.in_(pillar_numbers)
    ).count()

    if total_threads == 0:
        raise ValidationError('No threads found for selected pillars. Please sync data first.')

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


@oncoco_analysis_bp.route('/analyses/<int:analysis_id>', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='oncoco')
def get_analysis(analysis_id: int):
    """
    Get details of a specific analysis.

    Args:
        analysis_id: ID of the analysis

    Returns:
        JSON object with analysis details
    """
    analysis = OnCoCoAnalysis.query.get(analysis_id)
    if not analysis:
        raise NotFoundError(f'Analysis {analysis_id} not found')

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


@oncoco_analysis_bp.route('/analyses/<int:analysis_id>/start', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='oncoco')
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
    analysis = OnCoCoAnalysis.query.get(analysis_id)
    if not analysis:
        raise NotFoundError(f'Analysis {analysis_id} not found')
    # Handle POST with no body or non-JSON content type
    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}
    force_resume = data.get('force', False)

    # Allow resuming stuck 'running' analyses with force flag
    if analysis.status == OnCoCoAnalysisStatus.RUNNING:
        if not force_resume:
            raise ValidationError('Analysis is already running. Use force=true to resume if stuck.',
                                details={'hint': 'The analysis may be stuck after a server restart. Use force=true to resume.'})
        # Reset to pending to allow restart, keeping existing progress
        logger.info(f"[OnCoCo] Force resuming stuck analysis {analysis_id}")

    if analysis.status not in [OnCoCoAnalysisStatus.PENDING, OnCoCoAnalysisStatus.FAILED, OnCoCoAnalysisStatus.RUNNING]:
        raise ValidationError(f'Cannot start analysis in {analysis.status.value} status')

    # Check model availability
    service = get_oncoco_service()
    if not service.is_model_available():
        raise ValidationError('OnCoCo model not available. Please check model path.')

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
            'success': True,
            'message': f'Analysis {action}',
            'status': analysis.status.value,
            'resumed': should_resume
        })
    except Exception as e:
        logger.error(f"[OnCoCo] Failed to start analysis {analysis_id}: {e}")
        analysis.status = OnCoCoAnalysisStatus.FAILED
        analysis.error_message = str(e)
        db.session.commit()
        raise


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
                # Prefer explicit role field if available
                explicit_role = getattr(msg, 'role', None) or getattr(msg, 'sender_role', None)
                if explicit_role:
                    explicit_role_lower = explicit_role.lower()
                    if 'counsel' in explicit_role_lower or 'berater' in explicit_role_lower:
                        role_hint = "counselor"
                    elif 'client' in explicit_role_lower or 'ratsuch' in explicit_role_lower:
                        role_hint = "client"
                elif any(term in sender_lower for term in ['berater', 'counsellor', 'counselor', 'assistant', 'bot']):
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


@oncoco_analysis_bp.route('/analyses/<int:analysis_id>', methods=['DELETE'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='oncoco')
def delete_analysis(analysis_id: int):
    """
    Delete an OnCoCo analysis and all related data.

    Args:
        analysis_id: ID of the analysis

    Returns:
        JSON object with status
    """
    analysis = OnCoCoAnalysis.query.get(analysis_id)
    if not analysis:
        raise NotFoundError(f'Analysis {analysis_id} not found')

    # Delete related data
    OnCoCoSentenceLabel.query.filter_by(analysis_id=analysis_id).delete()
    OnCoCoPillarStatistics.query.filter_by(analysis_id=analysis_id).delete()
    OnCoCoTransitionMatrix.query.filter_by(analysis_id=analysis_id).delete()

    db.session.delete(analysis)
    db.session.commit()

    logger.info(f"[OnCoCo] Deleted analysis {analysis_id}")

    return jsonify({'success': True, 'message': 'Analysis deleted'})
