"""
Markdown Collab Routes Module

Provides REST endpoints for Markdown Collab workspaces and documents.

Blueprint:
- markdown_collab_bp: /api/markdown-collab
"""

from .markdown_collab_routes import markdown_collab_bp

__all__ = ["markdown_collab_bp"]

