# latex_collab_routes.py
"""
LaTeX Collab API Routes - Main Blueprint Registration

This module re-exports all LaTeX Collab blueprints for registration in the main app.
The routes are split into focused modules:

- latex_workspace_routes.py: Workspace CRUD + member management
- latex_document_routes.py: Document/node CRUD + tree operations
- latex_commit_routes.py: Commits, baselines, rollback, change tracking
- latex_comment_routes.py: Document comments/annotations
- latex_asset_routes.py: Binary file uploads (images, PDFs)
- latex_compile_routes.py: Compilation, PDF generation, SyncTeX
- latex_helpers.py: Shared helper functions
"""

from flask import Blueprint

# Import all sub-blueprints
from routes.latex_collab.latex_workspace_routes import latex_workspace_bp
from routes.latex_collab.latex_document_routes import latex_document_bp
from routes.latex_collab.latex_commit_routes import latex_commit_bp
from routes.latex_collab.latex_comment_routes import latex_comment_bp
from routes.latex_collab.latex_asset_routes import latex_asset_bp
from routes.latex_collab.latex_compile_routes import latex_compile_bp

# Main blueprint for backwards compatibility
# Note: This blueprint itself has no routes - all routes are in sub-blueprints
latex_collab_bp = Blueprint("latex_collab", __name__, url_prefix="/api/latex-collab")

# Export all blueprints for registration
__all__ = [
    'latex_collab_bp',
    'latex_workspace_bp',
    'latex_document_bp',
    'latex_commit_bp',
    'latex_comment_bp',
    'latex_asset_bp',
    'latex_compile_bp',
]


def register_latex_collab_routes(app):
    """
    Register all LaTeX Collab blueprints with the Flask app.

    Usage in main.py:
        from routes.latex_collab.latex_collab_routes import register_latex_collab_routes
        register_latex_collab_routes(app)
    """
    app.register_blueprint(latex_workspace_bp)
    app.register_blueprint(latex_document_bp)
    app.register_blueprint(latex_commit_bp)
    app.register_blueprint(latex_comment_bp)
    app.register_blueprint(latex_asset_bp)
    app.register_blueprint(latex_compile_bp)
