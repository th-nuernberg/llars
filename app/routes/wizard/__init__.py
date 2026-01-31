"""
Wizard API Blueprint

Provides REST API endpoints for programmatic Scenario Wizard access.
Enables Claude Code and other API clients to create evaluation scenarios.
"""

from flask import Blueprint

bp = Blueprint('wizard', __name__, url_prefix='/api/wizard')

from . import wizard_routes  # noqa: F401, E402
