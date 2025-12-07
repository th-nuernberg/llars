"""
LLM Routes Module

Provides endpoints for LLM model management and configuration.

Blueprint:
- llm_bp: LLM model management routes (/api/llm)
"""

from flask import Blueprint

# Create LLM blueprint
llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')

# Import route handlers
from . import llm_routes

__all__ = ['llm_bp']
