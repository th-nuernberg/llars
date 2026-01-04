"""KIA GitLab sync routes for LLM-as-Judge."""

from flask import Blueprint, request, jsonify, g

from db.database import db
from db.tables import PillarThread, EmailThread
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)

kia_sync_bp = Blueprint('judge_kia_sync', __name__)


# ============================================================================
# KIA DATA SYNC
# ============================================================================

@kia_sync_bp.route('/kia/status', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def get_kia_sync_status():
    """
    Get sync status for all KIA pillars.

    Shows which pillars have data available in GitLab
    and how many are synced to the database.

    Returns:
        JSON with pillar sync status
    """
    from services.judge.kia_sync_service import get_kia_sync_service

    sync_service = get_kia_sync_service()
    status = sync_service.get_sync_status()
    return jsonify(status)


@kia_sync_bp.route('/kia/check', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def check_kia_availability():
    """
    Check which pillars have data available in GitLab.

    Does not sync, just checks availability.

    Returns:
        JSON with availability per pillar
    """
    from services.judge.kia_sync_service import get_kia_sync_service

    sync_service = get_kia_sync_service()
    availability = sync_service.check_pillar_availability()

    return jsonify({
        'pillars': {
            num: {
                'number': status.pillar_number,
                'name': status.pillar_name,
                'status': status.status.value,
                'file_count': status.file_count,
                'error': status.error_message
            }
            for num, status in availability.items()
        },
        'gitlab_connected': sync_service._get_project_id() is not None
    })


@kia_sync_bp.route('/kia/sync', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
def sync_kia_data():
    """
    Sync KIA data from GitLab repository.

    Body:
        pillar: (optional) Specific pillar number to sync (1-5)
                If not provided, syncs all available pillars
        force: (optional) If true, re-imports existing data

    Returns:
        JSON with sync results
    """
    from services.judge.kia_sync_service import get_kia_sync_service

    data = request.get_json() or {}
    pillar = data.get('pillar')
    force = data.get('force', False)
    gitlab_token = data.get('gitlab_token')  # Optional token override

    sync_service = get_kia_sync_service(gitlab_token)

    if pillar:
        # Sync specific pillar
        if pillar not in range(1, 6):
            raise ValidationError('Pillar muss zwischen 1 und 5 sein')

        result = sync_service.sync_pillar(pillar, force)
        return jsonify({
            'success': result.success,
            'pillar': pillar,
            'files_processed': result.files_processed,
            'threads_created': result.threads_created,
            'threads_updated': result.threads_updated,
            'threads_skipped': result.threads_skipped,
            'errors': result.errors
        })
    else:
        # Sync all pillars
        results = sync_service.sync_all_pillars(force)

        summary = {
            'total_success': sum(1 for r in results.values() if r.success),
            'total_failed': sum(1 for r in results.values() if not r.success),
            'total_threads_created': sum(r.threads_created for r in results.values()),
            'total_threads_updated': sum(r.threads_updated for r in results.values()),
            'pillars': {}
        }

        for pillar_num, result in results.items():
            summary['pillars'][pillar_num] = {
                'success': result.success,
                'files_processed': result.files_processed,
                'threads_created': result.threads_created,
                'threads_updated': result.threads_updated,
                'threads_skipped': result.threads_skipped,
                'errors': result.errors
            }

        return jsonify(summary)


@kia_sync_bp.route('/kia/sync/<int:pillar_number>', methods=['POST'])
@authentik_required
@require_permission('feature:comparison:edit')
@handle_api_errors(logger_name='judge')
def sync_specific_pillar(pillar_number: int):
    """
    Sync a specific pillar from GitLab.

    Args:
        pillar_number: Pillar to sync (1-5)

    Query params:
        force: If 'true', re-imports existing data

    Returns:
        JSON with sync result
    """
    from services.judge.kia_sync_service import get_kia_sync_service

    if pillar_number not in range(1, 6):
        raise ValidationError('Pillar muss zwischen 1 und 5 sein')

    force = request.args.get('force', 'false').lower() == 'true'

    sync_service = get_kia_sync_service()
    result = sync_service.sync_pillar(pillar_number, force)

    return jsonify({
        'success': result.success,
        'pillar': pillar_number,
        'files_processed': result.files_processed,
        'threads_created': result.threads_created,
        'threads_updated': result.threads_updated,
        'threads_skipped': result.threads_skipped,
        'errors': result.errors
    })


@kia_sync_bp.route('/kia/config', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
@handle_api_errors(logger_name='judge')
def get_kia_config():
    """
    Get KIA sync configuration.

    Returns:
        JSON with current configuration
    """
    from services.judge.kia_sync_service import PILLAR_CONFIG, KIASyncService
    import os

    return jsonify({
        'gitlab_host': KIASyncService.GITLAB_HOST,
        'project_path': KIASyncService.PROJECT_PATH,
        'has_token': bool(os.environ.get('GITLAB_TOKEN') or os.environ.get('KIA_GITLAB_TOKEN')),
        'pillars': {
            num: {
                'name': config['name'],
                'path': config['path']
            }
            for num, config in PILLAR_CONFIG.items()
        }
    })


@kia_sync_bp.route('/kia/config', methods=['POST'])
@authentik_required
@require_permission('admin:permissions:manage')
@handle_api_errors(logger_name='judge')
def set_kia_token():
    """
    Set GitLab token for KIA sync.

    Body:
        gitlab_token: Personal access token for GitLab

    Returns:
        JSON with confirmation
    """
    data = request.get_json()
    token = data.get('gitlab_token')

    if not token:
        raise ValidationError('gitlab_token ist erforderlich')

    # Store token in environment (for this process only)
    import os
    os.environ['KIA_GITLAB_TOKEN'] = token

    # Reset the sync service to use new token
    from services.judge.kia_sync_service import get_kia_sync_service
    sync_service = get_kia_sync_service(token)

    # Test connection
    project_id = sync_service._get_project_id()

    if project_id:
        return jsonify({
            'success': True,
            'message': 'GitLab Token gesetzt und verbunden',
            'project_id': project_id
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Token gesetzt, aber Verbindung fehlgeschlagen'
        }), 400
