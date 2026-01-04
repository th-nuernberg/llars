from __future__ import annotations

from typing import Any, Dict, Optional

from flask import jsonify, request

from db.database import db
from db.models.analytics_settings import AnalyticsSettings
from decorators.permission_decorator import require_permission
from auth.auth_utils import AuthUtils
from routes.auth import data_bp


def _normalize_base_url(value: Optional[str]) -> str:
    if not value:
        return "/analytics/"
    normalized = str(value).strip()
    if not normalized:
        return "/analytics/"
    if not normalized.endswith("/"):
        normalized = f"{normalized}/"
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return normalized
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized


def _get_or_create_settings() -> AnalyticsSettings:
    settings = AnalyticsSettings.query.get(1)
    if settings is None:
        settings = AnalyticsSettings(id=1)
        db.session.add(settings)
        db.session.commit()
    return settings


def _serialize_settings(settings: AnalyticsSettings) -> Dict[str, Any]:
    return {
        "matomo_enabled": bool(settings.matomo_enabled),
        "matomo_base_url": _normalize_base_url(getattr(settings, "matomo_base_url", None)),
        "matomo_site_id": int(settings.matomo_site_id or 1),
        "include_query": bool(settings.include_query),
        "disable_cookies": bool(settings.disable_cookies),
        "require_consent": bool(settings.require_consent),
        "require_cookie_consent": bool(settings.require_cookie_consent),
        "set_user_id": bool(settings.set_user_id),
        "dimension_route_id": int(getattr(settings, "dimension_route_id", 0) or 0),
        "dimension_module_id": int(getattr(settings, "dimension_module_id", 0) or 0),
        "dimension_entity_id": int(getattr(settings, "dimension_entity_id", 0) or 0),
        "dimension_view_id": int(getattr(settings, "dimension_view_id", 0) or 0),
        "dimension_role_id": int(getattr(settings, "dimension_role_id", 0) or 0),
        "track_clicks": bool(settings.track_clicks),
        "track_hovers": bool(settings.track_hovers),
        "hover_min_ms": int(settings.hover_min_ms or 0),
        "hover_sample_rate": float(settings.hover_sample_rate or 0.0),
        "heartbeat_enabled": bool(settings.heartbeat_enabled),
        "heartbeat_seconds": int(settings.heartbeat_seconds or 0),
    }


@data_bp.get("/analytics/config")
def get_analytics_config():
    """Public runtime config for the frontend."""
    settings = _get_or_create_settings()
    return jsonify(_serialize_settings(settings))


@data_bp.get("/admin/analytics/settings")
@require_permission("admin:system:configure")
def get_admin_analytics_settings():
    settings = _get_or_create_settings()
    return jsonify(_serialize_settings(settings))


@data_bp.patch("/admin/analytics/settings")
@require_permission("admin:system:configure")
def patch_admin_analytics_settings():
    settings = _get_or_create_settings()
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Bad Request", "message": "JSON object expected"}), 400

    updatable_fields = {
        "matomo_enabled": bool,
        "matomo_base_url": str,
        "matomo_site_id": int,
        "include_query": bool,
        "disable_cookies": bool,
        "require_consent": bool,
        "require_cookie_consent": bool,
        "set_user_id": bool,
        "dimension_route_id": int,
        "dimension_module_id": int,
        "dimension_entity_id": int,
        "dimension_view_id": int,
        "dimension_role_id": int,
        "track_clicks": bool,
        "track_hovers": bool,
        "hover_min_ms": int,
        "hover_sample_rate": float,
        "heartbeat_enabled": bool,
        "heartbeat_seconds": int,
    }

    errors = []
    for key, expected_type in updatable_fields.items():
        if key not in payload:
            continue

        value = payload.get(key)
        try:
            if expected_type is bool:
                coerced = bool(value)
            elif expected_type is int:
                coerced = int(value)
            elif expected_type is float:
                coerced = float(value)
            else:
                coerced = str(value)
        except (TypeError, ValueError):
            errors.append(f"Invalid value for {key}")
            continue

        if key == "matomo_base_url":
            coerced = _normalize_base_url(coerced)
        elif key == "matomo_site_id":
            coerced = max(1, coerced)
        elif key.startswith("dimension_"):
            coerced = max(0, coerced)
        elif key == "hover_min_ms":
            coerced = max(0, coerced)
        elif key == "hover_sample_rate":
            coerced = min(1.0, max(0.0, coerced))
        elif key == "heartbeat_seconds":
            coerced = max(5, coerced)

        setattr(settings, key, coerced)

    if errors:
        return jsonify({"error": "Bad Request", "message": "Validation failed", "details": errors}), 400

    db.session.commit()

    try:
        from services.system_event_service import SystemEventService

        acting_username = AuthUtils.extract_username_without_validation() or "admin"
        SystemEventService.log_event(
            event_type="admin.analytics_settings_updated",
            severity="info",
            username=acting_username,
            entity_type="analytics",
            entity_id="settings",
            message=f"Analytics settings updated by '{acting_username}'",
            details={"updated_fields": [k for k in updatable_fields.keys() if k in payload]},
        )
    except Exception:
        pass

    return jsonify(_serialize_settings(settings))
