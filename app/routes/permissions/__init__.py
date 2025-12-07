"""
Permissions Routes Module

Provides API endpoints for managing permissions, roles, and user permissions.
All routes are protected with admin permissions.

Blueprint:
- permissions_bp: Permission management routes (/api/permissions)
"""

from flask import Blueprint

# Create permissions blueprint - uses data_bp for backwards compatibility
from routes.auth import data_bp as permissions_bp

# Import route handlers
from . import permission_routes

__all__ = ['permissions_bp']
