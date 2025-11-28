"""
LLM-as-Judge Routes Module

Provides all Judge-related API endpoints, split into sub-modules:
- session_routes: Session CRUD and configuration
- session_control_routes: Start/stop/pause/resume
- session_debug_routes: Debug endpoints (dev only)
- session_health_routes: Health and worker status
- comparison_routes: Comparison retrieval and queue
- statistics_routes: Results and statistics
- pillar_routes: Pillar management
- export_routes: Data export
- kia_sync_routes: KIA GitLab synchronization
"""

from flask import Blueprint

# Main blueprint for /api/judge
judge_bp = Blueprint('judge', __name__, url_prefix='/api/judge')

# Import sub-blueprints
from routes.judge.session_routes import session_bp
from routes.judge.session_control_routes import session_control_bp
from routes.judge.session_debug_routes import session_debug_bp
from routes.judge.session_health_routes import session_health_bp
from routes.judge.comparison_routes import comparison_bp
from routes.judge.statistics_routes import statistics_bp
from routes.judge.pillar_routes import pillar_bp
from routes.judge.export_routes import export_bp
from routes.judge.kia_sync_routes import kia_sync_bp

# Register all sub-blueprints with the main judge blueprint
judge_bp.register_blueprint(session_bp)
judge_bp.register_blueprint(session_control_bp)
judge_bp.register_blueprint(session_debug_bp)
judge_bp.register_blueprint(session_health_bp)
judge_bp.register_blueprint(comparison_bp)
judge_bp.register_blueprint(statistics_bp)
judge_bp.register_blueprint(pillar_bp)
judge_bp.register_blueprint(export_bp)
judge_bp.register_blueprint(kia_sync_bp)

__all__ = ['judge_bp']
