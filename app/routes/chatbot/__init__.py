"""
Chatbot Routes Module

Provides endpoints for chatbot interactions and document-based Q&A.

Blueprint:
- chatbot_bp: Chatbot interface routes (/api/chatbot)
"""

from .chatbot_routes import chatbot_blueprint as chatbot_bp

__all__ = ['chatbot_bp']
