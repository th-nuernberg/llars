"""
Crawler Routes Module

Provides endpoints for web crawling and content extraction.

Blueprint:
- crawler_bp: Web crawler routes (/api/crawler)
"""

from .crawler_routes import crawler_blueprint as crawler_bp

__all__ = ['crawler_bp']
