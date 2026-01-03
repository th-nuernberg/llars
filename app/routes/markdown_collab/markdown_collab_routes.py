# markdown_collab_routes.py
"""
Markdown Collab Routes Registry

This module combines all markdown collab routes into a single blueprint.
Routes are organized into separate modules for maintainability:

- markdown_workspace_routes: Workspace and member management
- markdown_document_routes: Document CRUD and commits
- markdown_collab_helpers: Shared helper functions
"""

from flask import Blueprint

# Create main blueprint
markdown_collab_bp = Blueprint("markdown_collab", __name__, url_prefix="/api/markdown-collab")

# Import sub-blueprints
from .markdown_workspace_routes import markdown_workspace_bp
from .markdown_document_routes import markdown_document_bp

# Register all sub-blueprints
markdown_collab_bp.register_blueprint(markdown_workspace_bp)
markdown_collab_bp.register_blueprint(markdown_document_bp)
