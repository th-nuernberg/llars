"""
OnCoCo Pillar Routes - Pillar data management endpoints.

Provides endpoints for:
- Getting pillar status (local DB + GitLab availability)
- Syncing pillar data from GitLab
"""

import logging
from flask import Blueprint, request, jsonify

from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from services.judge.kia_sync_service import get_kia_sync_service

logger = logging.getLogger(__name__)

oncoco_pillar_bp = Blueprint('oncoco_pillar', __name__)


# ============================================================================
# PILLAR DATA STATUS
# ============================================================================

@oncoco_pillar_bp.route('/pillars', methods=['GET'])
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


@oncoco_pillar_bp.route('/pillars/sync', methods=['POST'])
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
