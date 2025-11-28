"""OnCoCo Routes Module

This module provides REST API endpoints for OnCoCo (Online Counseling Communication) analysis.

The module is organized into logical sub-modules:
- oncoco_info_routes: Model and label information
- oncoco_pillar_routes: Pillar data management
- oncoco_analysis_routes: Analysis CRUD and execution
- oncoco_results_routes: Results and statistics
- oncoco_matrix_routes: Matrix comparison metrics
- oncoco_debug_routes: Debug and admin endpoints
"""

from flask import Blueprint

# Create main blueprint
oncoco_bp = Blueprint('oncoco', __name__, url_prefix='/api/oncoco')

# Import sub-blueprints
from routes.oncoco.oncoco_info_routes import oncoco_info_bp
from routes.oncoco.oncoco_pillar_routes import oncoco_pillar_bp
from routes.oncoco.oncoco_analysis_routes import oncoco_analysis_bp
from routes.oncoco.oncoco_results_routes import oncoco_results_bp
from routes.oncoco.oncoco_matrix_routes import oncoco_matrix_bp
from routes.oncoco.oncoco_debug_routes import oncoco_debug_bp

# Register all sub-blueprints with the main oncoco blueprint
oncoco_bp.register_blueprint(oncoco_info_bp)
oncoco_bp.register_blueprint(oncoco_pillar_bp)
oncoco_bp.register_blueprint(oncoco_analysis_bp)
oncoco_bp.register_blueprint(oncoco_results_bp)
oncoco_bp.register_blueprint(oncoco_matrix_bp)
oncoco_bp.register_blueprint(oncoco_debug_bp)

__all__ = ['oncoco_bp']
