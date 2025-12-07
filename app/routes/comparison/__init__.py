"""
Comparison Routes Module

Provides endpoints for LLM comparison sessions and persona-based ratings.

Blueprint:
- comparison_bp: Comparison session routes (/api/comparison)
"""

from flask import Blueprint

# Create comparison blueprint - uses data_bp for backwards compatibility
from routes.auth import data_bp as comparison_bp

# Import route handlers
from . import comparison_routes

__all__ = ['comparison_bp']
