"""
Admin routes for system-wide settings management.
"""

from flask import jsonify, request

from db.db import db
from db.models.system_settings import SystemSettings
from decorators.permission_decorator import require_permission
from auth.auth_utils import AuthUtils
from routes.auth import data_bp
from services.system_settings_service import invalidate_cache


def _get_or_create_settings() -> SystemSettings:
    """Get or create the singleton settings row."""
    settings = SystemSettings.query.get(1)
    if settings is None:
        settings = SystemSettings(id=1)
        db.session.add(settings)
        db.session.commit()
    return settings


@data_bp.get("/admin/system/settings")
@require_permission("admin:system:configure")
def get_system_settings():
    """Get all system settings for admin panel."""
    settings = _get_or_create_settings()
    return jsonify({
        'success': True,
        'settings': settings.to_dict()
    })


@data_bp.patch("/admin/system/settings")
@require_permission("admin:system:configure")
def update_system_settings():
    """Update system settings."""
    settings = _get_or_create_settings()
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify({'success': False, 'error': 'JSON object expected'}), 400

    updatable_fields = {
        'crawl_timeout_seconds': (int, 60, 86400),       # 1 min - 24 hours
        'embedding_timeout_seconds': (int, 60, 86400),   # 1 min - 24 hours
        'crawler_default_max_pages': (int, 1, 10000),    # 1 - 10000 pages
        'crawler_default_max_depth': (int, 1, 10),       # 1 - 10 levels
        'rag_default_chunk_size': (int, 100, 10000),     # 100 - 10000 chars
        'rag_default_chunk_overlap': (int, 0, 5000),     # 0 - 5000 chars
    }

    errors = []
    updated_fields = []

    for key, (expected_type, min_val, max_val) in updatable_fields.items():
        if key not in payload:
            continue

        value = payload.get(key)
        try:
            coerced = expected_type(value)
            coerced = max(min_val, min(max_val, coerced))  # Clamp to range
        except (TypeError, ValueError):
            errors.append(f"Invalid value for {key}")
            continue

        setattr(settings, key, coerced)
        updated_fields.append(key)

    if errors:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': errors
        }), 400

    db.session.commit()

    # Invalidate the settings cache so changes take effect immediately
    invalidate_cache()

    # Log the event
    try:
        from services.system_event_service import SystemEventService

        acting_username = AuthUtils.extract_username_without_validation() or "admin"
        SystemEventService.log_event(
            event_type="admin.system_settings_updated",
            severity="info",
            username=acting_username,
            entity_type="system",
            entity_id="settings",
            message=f"System settings updated by '{acting_username}'",
            details={"updated_fields": updated_fields},
        )
    except Exception:
        pass

    return jsonify({
        'success': True,
        'settings': settings.to_dict(),
        'updated_fields': updated_fields
    })
