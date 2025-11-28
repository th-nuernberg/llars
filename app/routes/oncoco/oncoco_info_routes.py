"""
OnCoCo Info Routes - Model and label information endpoints.

Provides endpoints for:
- Getting OnCoCo model information
- Retrieving label metadata and hierarchy
"""

import logging
from flask import Blueprint, request, jsonify

from auth.decorators import authentik_required
from services.oncoco import (
    get_oncoco_service,
    ONCOCO_LABELS, LABEL_HIERARCHY
)
from services.judge.kia_sync_service import PILLAR_CONFIG

logger = logging.getLogger(__name__)

oncoco_info_bp = Blueprint('oncoco_info', __name__)


# ============================================================================
# MODEL & LABEL INFO
# ============================================================================

@oncoco_info_bp.route('/info', methods=['GET'])
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


@oncoco_info_bp.route('/labels', methods=['GET'])
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
