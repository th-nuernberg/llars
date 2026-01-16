"""
Development-only routes for testing.

These routes are only available when FLASK_ENV=development or DEBUG=True.
They provide functionality for downloading test datasets and seeding scenarios.
"""

from flask import Blueprint

bp = Blueprint('dev', __name__, url_prefix='/api/dev')

# Import routes after blueprint creation to avoid circular imports
from . import test_data_routes  # noqa: F401, E402
