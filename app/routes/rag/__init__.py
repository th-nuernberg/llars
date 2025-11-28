"""
RAG Document Management Package

This package provides routes for managing RAG documents, collections, and retrieval.

The RAG routes are split into logical modules:
- collection_routes: Collection management (list, create, update, delete)
- document_routes: Document management (upload, download, list, update, delete)
- search_routes: Search, retrieval, and statistics
- admin_routes: Admin operations and processing queue

All routes are registered under the main rag_bp blueprint with prefix /api/rag
"""

from flask import Blueprint

# Create main RAG blueprint
rag_bp = Blueprint('rag', __name__, url_prefix='/api/rag')

# Import sub-blueprints
from routes.rag.collection_routes import rag_collection_bp
from routes.rag.document_routes import rag_document_bp
from routes.rag.search_routes import rag_search_bp
from routes.rag.admin_routes import rag_admin_bp

# Register sub-blueprints (without url_prefix since main blueprint already has /api/rag)
rag_bp.register_blueprint(rag_collection_bp)
rag_bp.register_blueprint(rag_document_bp)
rag_bp.register_blueprint(rag_search_bp)
rag_bp.register_blueprint(rag_admin_bp)

# Export main blueprint
__all__ = ['rag_bp']

# Legacy import for backward compatibility (deprecated)
from . import RAGRoutes
