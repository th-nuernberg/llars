"""
Routes Package

Feature-based route organization for LLARS.
All blueprints are registered via routes/registry.py

Module structure:
- auth/: Authentication and data management
- rating/: Email rating, ranking, and mail rating
- permissions/: Permission and role management
- comparison/: LLM comparison sessions
- prompts/: User prompt management
- llm/: LLM model management
- judge/: LLM-as-Judge
- oncoco/: OnCoCo analysis
- rag/: RAG document management
- chatbot/: Chatbot interface
- crawler/: Web crawler
- scenarios/: Scenario management
- kaimo/: KAIMO project
"""

# Export main blueprints for backwards compatibility
from .auth import auth_bp as auth_blueprint, data_bp as data_blueprint
from .judge import judge_bp
from .oncoco import oncoco_bp

__all__ = ['auth_blueprint', 'data_blueprint', 'judge_bp', 'oncoco_bp']