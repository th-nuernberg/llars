"""
Admin routes for system-wide settings management.
"""

import os
import re

from flask import jsonify, request

from db.database import db
from db.models.system_settings import SystemSettings
from decorators.permission_decorator import require_permission
from auth.auth_utils import AuthUtils
from routes.auth import data_bp
from services.system_settings_service import invalidate_cache
from services.zotero.encryption import encrypt_api_key


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


@data_bp.get("/system/ai-assistant")
def get_ai_assistant_settings():
    """
    Get AI assistant settings (public endpoint).

    Returns the AI assistant configuration needed by the frontend
    for displaying AI features and reserving the AI color.
    """
    settings = _get_or_create_settings()
    return jsonify({
        'success': True,
        'ai_assistant': {
            'enabled': settings.ai_assistant_enabled,
            'color': settings.ai_assistant_color,
            'username': settings.ai_assistant_username,
        }
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
        'ai_assistant_enabled',
    }

    string_fields = {
        'llm_ai_log_tasks',
        'default_referral_role',
        'ai_assistant_username',
    }

    # Color fields with hex validation
    color_fields = {
        'ai_assistant_color',
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

    # Handle color fields with hex validation
    hex_color_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
    for key in color_fields:
        if key not in payload:
            continue
        raw = payload.get(key)
        if raw is None:
            errors.append(f"Color value for {key} cannot be null")
            continue
        value = str(raw).strip()
        if not hex_color_pattern.match(value):
            errors.append(f"Invalid hex color for {key}: must be #RRGGBB format")
            continue
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


# ============================================================
# Zotero OAuth Settings
# ============================================================


def _get_zotero_oauth_status():
    """
    Get Zotero OAuth status from both env and database.
    Returns info about which source is active.
    """
    # Check environment variables
    env_key = os.environ.get("ZOTERO_CLIENT_KEY", "").strip()
    env_secret = os.environ.get("ZOTERO_CLIENT_SECRET", "").strip()
    env_configured = bool(env_key and env_secret)

    # Check database
    settings = _get_or_create_settings()
    db_configured = bool(
        settings.zotero_oauth_enabled and
        settings.zotero_client_key and
        settings.zotero_client_secret_encrypted
    )

    # Determine active source
    if env_configured:
        active_source = "env"
    elif db_configured:
        active_source = "database"
    else:
        active_source = "none"

    return {
        "env": {
            "configured": env_configured,
            "client_key": env_key if env_configured else None,
            # Never expose secrets, just show if set
            "client_secret_set": bool(env_secret),
        },
        "database": {
            "enabled": settings.zotero_oauth_enabled,
            "configured": db_configured,
            "client_key": settings.zotero_client_key or "",
            "client_secret_set": bool(settings.zotero_client_secret_encrypted),
        },
        "active_source": active_source,
        "oauth_available": active_source != "none",
    }


@data_bp.get("/admin/system/zotero-oauth")
@require_permission("admin:system:configure")
def get_zotero_oauth_settings():
    """
    Get Zotero OAuth configuration status.

    Shows both environment and database configuration,
    and indicates which source is currently active.
    """
    status = _get_zotero_oauth_status()
    return jsonify({
        'success': True,
        'zotero_oauth': status
    })


@data_bp.patch("/admin/system/zotero-oauth")
@require_permission("admin:system:configure")
def update_zotero_oauth_settings():
    """
    Update Zotero OAuth configuration in database.

    This is a fallback/override for when env vars are not set.
    If env vars are set, they take priority over database settings.

    Request body:
        {
            "enabled": bool,
            "client_key": str,
            "client_secret": str  # Only if changing
        }
    """
    settings = _get_or_create_settings()
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return jsonify({'success': False, 'error': 'JSON object expected'}), 400

    updated_fields = []

    # Update enabled flag
    if 'enabled' in payload:
        settings.zotero_oauth_enabled = bool(payload['enabled'])
        updated_fields.append('zotero_oauth_enabled')

    # Update client key
    if 'client_key' in payload:
        client_key = str(payload['client_key']).strip()
        settings.zotero_client_key = client_key if client_key else None
        updated_fields.append('zotero_client_key')

    # Update client secret (encrypted)
    if 'client_secret' in payload:
        client_secret = str(payload['client_secret']).strip()
        if client_secret:
            settings.zotero_client_secret_encrypted = encrypt_api_key(client_secret)
            updated_fields.append('zotero_client_secret')
        # Empty string clears the secret
        elif client_secret == '':
            settings.zotero_client_secret_encrypted = None
            updated_fields.append('zotero_client_secret')

    db.session.commit()
    invalidate_cache()

    # Log the event
    try:
        from services.system_event_service import SystemEventService

        acting_username = AuthUtils.extract_username_without_validation() or "admin"
        SystemEventService.log_event(
            event_type="admin.zotero_oauth_updated",
            severity="info",
            username=acting_username,
            entity_type="system",
            entity_id="zotero_oauth",
            message=f"Zotero OAuth settings updated by '{acting_username}'",
            details={"updated_fields": updated_fields},
        )
    except Exception:
        pass

    status = _get_zotero_oauth_status()
    return jsonify({
        'success': True,
        'zotero_oauth': status,
        'updated_fields': updated_fields
    })
