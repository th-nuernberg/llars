"""
LaTeX Collab Routes

Blueprints:
    - latex_workspace_bp: Workspace CRUD + members
    - latex_document_bp: Document/node CRUD + tree
    - latex_commit_bp: Commits, baselines, rollback
    - latex_comment_bp: Document comments
    - latex_asset_bp: Binary file uploads
    - latex_compile_bp: Compilation, PDF, SyncTeX
"""

from .latex_collab_routes import (
    latex_collab_bp,
    latex_workspace_bp,
    latex_document_bp,
    latex_commit_bp,
    latex_comment_bp,
    latex_asset_bp,
    latex_compile_bp,
    register_latex_collab_routes,
)

__all__ = [
    "latex_collab_bp",
    "latex_workspace_bp",
    "latex_document_bp",
    "latex_commit_bp",
    "latex_comment_bp",
    "latex_asset_bp",
    "latex_compile_bp",
    "register_latex_collab_routes",
]
