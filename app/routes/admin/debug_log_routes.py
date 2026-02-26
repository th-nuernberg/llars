"""
Admin routes for per-user debug log management.

Ermöglicht Admins, für einzelne User kurzzeitig detaillierte
Fehler-Logs und Console-Output in Production zu aktivieren.

Endpoints:
    GET  /api/admin/debug-logs              → Alle User mit aktivem Debug
    GET  /api/admin/debug-logs/<username>    → Status für einzelnen User
    POST /api/admin/debug-logs/<username>    → Debug aktivieren (mit TTL)
    DELETE /api/admin/debug-logs/<username>  → Debug deaktivieren
"""

from flask import jsonify, request

from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors
from routes.auth import data_bp
from services.debug_log_service import (
    enable_user_debug,
    disable_user_debug,
    get_user_debug_status,
    get_all_debug_users,
    DEFAULT_DEBUG_TTL_SECONDS,
    MAX_DEBUG_TTL_SECONDS,
)


@data_bp.get('/admin/debug-logs')
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='debug_logs')
def list_debug_users():
    """Gibt alle User mit aktivem Debug-Modus zurück."""
    users = get_all_debug_users()
    return jsonify({
        'success': True,
        'debug_users': users,
        'total': len(users),
    })


@data_bp.get('/admin/debug-logs/<string:username>')
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='debug_logs')
def get_debug_status(username: str):
    """Gibt den Debug-Status für einen einzelnen User zurück."""
    status = get_user_debug_status(username)
    return jsonify({
        'success': True,
        **status,
    })


@data_bp.post('/admin/debug-logs/<string:username>')
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='debug_logs')
def enable_debug(username: str):
    """
    Aktiviert Debug-Logging für einen User.

    Request body (optional):
        {
            "ttl_minutes": 30  // Standard: 30 Min, Max: 1440 Min (24h)
        }
    """
    data = request.get_json(silent=True) or {}
    ttl_minutes = data.get('ttl_minutes')

    ttl_seconds = None
    if ttl_minutes is not None:
        try:
            ttl_seconds = int(float(ttl_minutes) * 60)
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'error': 'ttl_minutes must be a number'
            }), 400

    result = enable_user_debug(username, ttl_seconds=ttl_seconds)

    # Event loggen
    try:
        from services.system_event_service import SystemEventService
        from auth.auth_utils import AuthUtils

        acting_admin = AuthUtils.extract_username_without_validation() or 'admin'
        SystemEventService.log_event(
            event_type='admin.debug_log_enabled',
            severity='info',
            username=acting_admin,
            entity_type='user',
            entity_id=username,
            message=f'Debug logging enabled for "{username}" by "{acting_admin}" '
                    f'(TTL: {result["ttl_minutes"]} min)',
            details={'ttl_seconds': result['ttl_seconds']},
        )
    except Exception:
        pass

    return jsonify({'success': True, **result})


@data_bp.delete('/admin/debug-logs/<string:username>')
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='debug_logs')
def disable_debug(username: str):
    """Deaktiviert Debug-Logging für einen User sofort."""
    result = disable_user_debug(username)

    # Event loggen
    try:
        from services.system_event_service import SystemEventService
        from auth.auth_utils import AuthUtils

        acting_admin = AuthUtils.extract_username_without_validation() or 'admin'
        SystemEventService.log_event(
            event_type='admin.debug_log_disabled',
            severity='info',
            username=acting_admin,
            entity_type='user',
            entity_id=username,
            message=f'Debug logging disabled for "{username}" by "{acting_admin}"',
        )
    except Exception:
        pass

    return jsonify({'success': True, **result})
