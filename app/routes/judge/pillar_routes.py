"""Pillar management routes for LLM-as-Judge."""

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from db.db import db
from db.tables import (
    PillarThread, EmailThread
)
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)

pillar_bp = Blueprint('judge_pillars', __name__)


# ============================================================================
# PILLAR MANAGEMENT
# ============================================================================

@pillar_bp.route('/pillars', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def list_pillars():
    """
    List all pillars with thread counts.

    Returns:
        JSON array of pillar info
    """
    # Get thread counts per pillar
    pillar_counts = db.session.query(
        PillarThread.pillar_number,
        PillarThread.pillar_name,
        func.count(PillarThread.id).label('thread_count')
    ).group_by(
        PillarThread.pillar_number,
        PillarThread.pillar_name
    ).all()

    # Build response with all 5 pillars
    pillar_names = {
        1: "Rollenspiele",
        2: "Feature aus Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch generiert",
        5: "Live-Testungen"
    }

    pillar_colors = {
        1: "#f44336",  # red
        2: "#ff9800",  # orange
        3: "#4caf50",  # green
        4: "#2196f3",  # blue
        5: "#9c27b0"   # purple
    }

    result = []
    count_map = {p[0]: (p[1], p[2]) for p in pillar_counts}

    for num in range(1, 6):
        name, count = count_map.get(num, (pillar_names[num], 0))
        result.append({
            'number': num,
            'name': name or pillar_names[num],
            'thread_count': count,
            'color': pillar_colors[num]
        })

    return jsonify(result)


@pillar_bp.route('/pillars/<int:pillar_number>/threads', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def get_pillar_threads(pillar_number: int):
    """
    Get threads assigned to a specific pillar.

    Returns:
        JSON array of thread info
    """
    pillar_threads = PillarThread.query.filter_by(
        pillar_number=pillar_number
    ).all()

    threads = []
    for pt in pillar_threads:
        thread = EmailThread.query.get(pt.thread_id)
        if thread:
            threads.append({
                'id': thread.id,
                'subject': thread.subject if hasattr(thread, 'subject') else f'Thread {thread.id}',
                'pillar_id': pt.id,
                'metadata': pt.metadata_json
            })

    return jsonify({
        'pillar': pillar_number,
        'threads': threads,
        'count': len(threads)
    })


@pillar_bp.route('/pillars/<int:pillar_number>/assign', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
def assign_thread_to_pillar(pillar_number: int):
    """
    Assign a thread to a pillar.

    Body:
        thread_id: ID of the thread to assign
        metadata: Optional metadata dict

    Returns:
        JSON with assignment info
    """
    data = request.get_json()
    thread_id = data.get('thread_id')

    if not thread_id:
        raise ValidationError('thread_id ist erforderlich')

    # Check if thread exists
    thread = EmailThread.query.get(thread_id)
    if not thread:
        raise NotFoundError('Thread nicht gefunden')

    # Check if already assigned
    existing = PillarThread.query.filter_by(
        thread_id=thread_id,
        pillar_number=pillar_number
    ).first()

    if existing:
        raise ConflictError('Thread ist bereits dieser Säule zugeordnet')

    pillar_names = {
        1: "Rollenspiele",
        2: "Feature aus Säule 1",
        3: "Anonymisierte Daten",
        4: "Synthetisch generiert",
        5: "Live-Testungen"
    }

    pillar_thread = PillarThread(
        thread_id=thread_id,
        pillar_number=pillar_number,
        pillar_name=pillar_names.get(pillar_number, f"Säule {pillar_number}"),
        metadata_json=data.get('metadata', {})
    )

    db.session.add(pillar_thread)
    db.session.commit()

    return jsonify({
        'id': pillar_thread.id,
        'thread_id': thread_id,
        'pillar_number': pillar_number,
        'message': 'Thread zugeordnet'
    }), 201
