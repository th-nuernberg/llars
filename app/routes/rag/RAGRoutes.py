"""
RAG Document Management Routes - DEPRECATED

⚠️ DEPRECATION NOTICE ⚠️
This file is deprecated and kept for backward compatibility only.

RAG routes have been split into modular files:
- routes/rag/collection_routes.py  - Collection management
- routes/rag/document_routes.py    - Document management
- routes/rag/search_routes.py      - Search and statistics
- routes/rag/admin_routes.py       - Admin and processing queue

All routes are now registered via routes/rag/__init__.py which creates
a unified rag_bp blueprint with prefix /api/rag

To use the new structure:
    from routes.rag import rag_bp
    app.register_blueprint(rag_bp)

This file will be removed in a future version. Please update any direct
imports from RAGRoutes to use the new modular structure.

Original Documentation (OUTDATED):
===================================

Provides API endpoints for managing RAG documents, collections, and retrieval.
All routes are protected with appropriate permissions.

Routes:
    Collections:
        GET    /api/rag/collections                - List all collections
        GET    /api/rag/collections/<id>           - Get collection details
        POST   /api/rag/collections                - Create new collection
        PUT    /api/rag/collections/<id>           - Update collection
        DELETE /api/rag/collections/<id>           - Delete collection
        GET    /api/rag/collections/<id>/stats     - Get collection statistics

    Documents:
        GET    /api/rag/documents                  - List all documents (with filters)
        GET    /api/rag/documents/<id>             - Get document details
        POST   /api/rag/documents/upload           - Upload new document
        PUT    /api/rag/documents/<id>             - Update document metadata
        DELETE /api/rag/documents/<id>             - Delete document
        GET    /api/rag/documents/<id>/download    - Download document file
        POST   /api/rag/documents/<id>/reprocess   - Reprocess document
        GET    /api/rag/documents/<id>/chunks      - Get document chunks

    Search & Retrieval:
        POST   /api/rag/search                     - Search documents
        POST   /api/rag/retrieve                   - RAG retrieval (with context)
        GET    /api/rag/retrieval-logs             - Get retrieval analytics

    Statistics:
        GET    /api/rag/stats/overview             - System overview stats
        GET    /api/rag/stats/popular-documents    - Most retrieved documents
        GET    /api/rag/stats/popular-queries      - Most common queries

    Processing Queue:
        GET    /api/rag/processing-queue           - Get processing queue status
        POST   /api/rag/processing-queue/<id>/retry - Retry failed processing
"""

import warnings

# Issue deprecation warning when this module is imported
warnings.warn(
    "RAGRoutes.py is deprecated. Use 'from routes.rag import rag_bp' instead. "
    "This file will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# For backward compatibility, re-export the new modular blueprints
# This allows existing code that imports from RAGRoutes to continue working
from routes.rag.collection_routes import rag_collection_bp
from routes.rag.document_routes import rag_document_bp
from routes.rag.search_routes import rag_search_bp
from routes.rag.admin_routes import rag_admin_bp

__all__ = [
    'rag_collection_bp',
    'rag_document_bp',
    'rag_search_bp',
    'rag_admin_bp'
]
