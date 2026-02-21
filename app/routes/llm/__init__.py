"""
LLM Routes Module

Provides endpoints for LLM model management and configuration.

Blueprints:
- llm_bp: LLM model management routes (/api/llm)
- llm_evaluation_bp: LLM evaluation routes (/api/evaluation/llm)
"""

from flask import Blueprint

# Create LLM blueprint
llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')

# Import route handlers
from . import llm_routes
from .llm_evaluation_routes import llm_evaluation_bp

__all__ = ['llm_bp', 'llm_evaluation_bp']
