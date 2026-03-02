"""
Conference Manager Routes Registry

Combines all conference manager routes into a single blueprint.
Routes are organized into separate modules:

- conference_crud_routes: Conference CRUD endpoints
- paper_crud_routes: Paper CRUD and author management endpoints
"""

from flask import Blueprint

# Create main blueprint
conference_manager_bp = Blueprint("conference_manager", __name__, url_prefix="/api/conference-manager")

# Import sub-blueprints
from .conference_crud_routes import conference_crud_bp
from .paper_crud_routes import paper_crud_bp
from .conference_wizard_routes import conference_wizard_bp
from .series_crud_routes import series_crud_bp

# Register all sub-blueprints
conference_manager_bp.register_blueprint(conference_crud_bp)
conference_manager_bp.register_blueprint(paper_crud_bp)
conference_manager_bp.register_blueprint(conference_wizard_bp)
conference_manager_bp.register_blueprint(series_crud_bp)
