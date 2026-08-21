"""
Authentication Routes Module

Provides authentication and user management endpoints.
Includes both legacy auth (backwards compatibility) and data management routes.

Blueprints:
- auth_bp: Authentication routes (/auth)
- data_bp: Data management routes (/api)
"""

from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__)
data_bp = Blueprint('data', __name__)

# Import route handlers
from . import auth_routes
from . import data_routes
from . import password_reset_routes  # noqa: F401 — attaches routes to auth_bp

__all__ = ['auth_bp', 'data_bp']
