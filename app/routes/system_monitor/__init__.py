"""
System Monitor Routes

Endpoints (under /api):
    GET  /admin/system/events
    GET  /admin/system/events/stream   (SSE)
    POST /admin/system/events/ci-cd   (system API key)
"""

from routes.auth import data_bp as system_monitor_bp

from . import system_monitor_routes

__all__ = ["system_monitor_bp"]
