"""
AI Writing Services

Services for the AI Writing Assistant integration in LaTeX/Markdown Collab.

Services:
- completion_service: Ghost text completion
- rewrite_service: Text rewriting/expansion
- chat_service: Conversational AI assistant
- citation_service: RAG-based citation finding
"""

from .completion_service import CompletionService
from .rewrite_service import RewriteService
from .chat_service import AIChatService
from .citation_service import CitationService

__all__ = [
    'CompletionService',
    'RewriteService',
    'AIChatService',
    'CitationService'
]
