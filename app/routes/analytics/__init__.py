"""
Analytics Routes

Provides endpoints for Matomo tracking configuration.

Endpoints (under /api):
    GET    /analytics/config                 (public) Runtime config for the frontend
    GET    /admin/analytics/settings         (admin)  Read settings
    PATCH  /admin/analytics/settings         (admin)  Update settings
"""

from routes.auth import data_bp as analytics_bp

from . import analytics_routes

__all__ = ["analytics_bp"]

