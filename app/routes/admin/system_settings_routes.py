"""
Admin routes for system-wide settings management.
"""

from flask import jsonify, request

from db.database import db
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


@data_bp.get("/system/communication-status")
def get_communication_status():
    """
    Get communication feature status (public endpoint).

    Returns whether communication (messaging, calls) is globally enabled.
    Used by the frontend to gate UI elements before checking per-user permissions.
    """
    settings = _get_or_create_settings()
    return jsonify({
        'success': True,
        'communication_enabled': settings.communication_enabled,
    })


@data_bp.get("/system/password-reset-status")
def get_password_reset_status():
    """
    Get self-service password-reset status (public endpoint).

    Returns whether the self-service "forgot password" flow is globally
    enabled. Used by the login page to show/hide the reset link before the
    user is authenticated.
    """
    settings = _get_or_create_settings()
    return jsonify({
        'success': True,
        'self_service_password_reset_enabled': settings.self_service_password_reset_enabled,
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
        'llm_ai_log_response_max': (int, 0, 10000),      # 0 - 10000 chars
        'llm_ai_log_prompt_max': (int, 0, 10000),        # 0 - 10000 chars
        'batch_generation_max_parallel': (int, 1, 16),   # 1 - 16 parallel outputs
    }

    bool_fields = {
        'llm_ai_log_responses',
        'llm_ai_log_prompts',
        'referral_system_enabled',
        'self_registration_enabled',
        'communication_enabled',
        'self_service_password_reset_enabled',
    }

    string_fields = {
        'llm_ai_log_tasks',
        'default_referral_role',
    }

    errors = []
    updated_fields = []

    def _coerce_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(int(value))
        if isinstance(value, str):
            val = value.strip().lower()
            if val in {'1', 'true', 'yes', 'on'}:
                return True
            if val in {'0', 'false', 'no', 'off', ''}:
                return False
        raise ValueError("Invalid boolean")

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

    for key in bool_fields:
        if key not in payload:
            continue
        try:
            coerced = _coerce_bool(payload.get(key))
        except (TypeError, ValueError):
            errors.append(f"Invalid value for {key}")
            continue
        setattr(settings, key, coerced)
        updated_fields.append(key)

    for key in string_fields:
        if key not in payload:
            continue
        raw = payload.get(key)
        if raw is None:
            value = ""
        else:
            value = str(raw).strip()
        # Only apply comma normalization for task lists, not display names
        if key in {'llm_ai_log_tasks'}:
            value = ",".join([part.strip().lower() for part in value.split(",") if part.strip()])
        if len(value) > 255:
            value = value[:255]
        setattr(settings, key, value)
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

    # Broadcast communication status change to all connected clients
    if 'communication_enabled' in updated_fields:
        try:
            from main import socketio
            socketio.emit('communication:status_changed', {
                'communication_enabled': settings.communication_enabled,
            })
        except Exception:
            pass

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
