"""
Rating Routes Module

Provides endpoints for email thread rating, feature ranking, and mail rating management.
Consolidates RatingRoutes, RankingRoutes, and mail_rating modules.

Blueprint:
- rating_bp: Consolidated rating and ranking routes (/api)
"""

from flask import Blueprint

# Import data_blueprint from auth module for backwards compatibility
from routes.auth import data_bp as rating_bp

# Import route handlers
from . import rating_routes
from . import ranking_routes
from . import mail_rating_threads
from . import mail_rating_history
from . import mail_rating_messages
from . import mail_rating_stats

__all__ = ['rating_bp']
