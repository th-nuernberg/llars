"""
Prompts Routes Module

Provides endpoints for user prompt management, sharing, and collaboration.

Blueprint:
- prompts_bp: Prompt management routes (/api/prompts)
"""

from flask import Blueprint

# Create prompts blueprint - uses data_bp for backwards compatibility
from routes.auth import data_bp as prompts_bp

# Import route handlers
from . import prompt_routes

__all__ = ['prompts_bp']
