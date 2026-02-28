"""
Conference Manager Routes Module

Provides REST endpoints for conference tracking and paper management.

Blueprint:
- conference_manager_bp: /api/conference-manager
"""

from .conference_routes import conference_manager_bp

__all__ = ["conference_manager_bp"]
