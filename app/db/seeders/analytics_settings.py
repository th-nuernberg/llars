"""Seed the default analytics settings."""

from __future__ import annotations

from typing import Any, Dict


DEFAULT_ANALYTICS_SETTINGS: Dict[str, Any] = {
    # Matomo core
    "matomo_enabled": True,
    "matomo_base_url": "/analytics/",
    "matomo_site_id": 1,
    # Privacy/consent
    "include_query": False,
    "disable_cookies": False,
    "require_consent": False,
    "require_cookie_consent": False,
    "set_user_id": True,
    # Interaction tracking
    "track_clicks": True,
    "track_hovers": False,
    "hover_min_ms": 400,
    "hover_sample_rate": 1.0,
    # Time on page
    "heartbeat_enabled": True,
    "heartbeat_seconds": 15,
}


def initialize_analytics_settings(db) -> None:
    """
    Ensure analytics settings row exists and is populated with defaults.

    Safe to run multiple times (idempotent).
    """
    from db.models.analytics_settings import AnalyticsSettings

    settings = AnalyticsSettings.query.get(1)
    created = False
    if settings is None:
        settings = AnalyticsSettings(id=1)
        db.session.add(settings)
        created = True

    changed = created
    for key, value in DEFAULT_ANALYTICS_SETTINGS.items():
        if getattr(settings, key, None) is None:
            setattr(settings, key, value)
            changed = True

    if changed:
        db.session.commit()
        print("✅ Analytics settings initialized")

