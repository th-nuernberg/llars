"""
Pipeline Routes Package.

Provides API endpoints for the automated LLM evaluation pipeline.
"""

from routes.pipeline.pipeline_routes import pipeline_bp
from routes.pipeline.pipeline_admin_routes import pipeline_admin_bp

__all__ = ['pipeline_bp', 'pipeline_admin_bp']
