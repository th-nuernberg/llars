"""
Admin User Management Routes

Provides API endpoints for managing users in the LLARS database.
All routes are protected with `admin:users:manage`.

Endpoints (under /api):
    GET    /admin/users
    POST   /admin/users
    PATCH  /admin/users/<username>
    DELETE /admin/users/<username>
"""

# Attach routes to the shared /api blueprint (data_bp)
from routes.auth import data_bp as users_bp

# Import route handlers (registers endpoints on users_bp)
from . import user_admin_routes

__all__ = ['users_bp']

