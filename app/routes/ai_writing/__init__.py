"""
AI Writing Routes Module

Provides API endpoints for the AI Writing Assistant.

Blueprint:
- ai_writing_bp: AI writing assistant routes (/api/ai-writing)
"""

from .routes import ai_writing_blueprint as ai_writing_bp

__all__ = ['ai_writing_bp']
