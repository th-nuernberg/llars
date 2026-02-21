"""
Import Routes for LLARS Data Importer.

Provides REST API endpoints for the import wizard workflow.
"""

from flask import Blueprint

bp = Blueprint('import', __name__, url_prefix='/api/import')

from . import import_routes  # noqa: E402, F401
