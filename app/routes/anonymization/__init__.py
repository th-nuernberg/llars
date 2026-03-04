"""Anonymization Pipeline Routes

Batch processing and manual review of conversation anonymization.
"""

from flask import Blueprint

# Main blueprint for /api/anonymization
anonymization_bp = Blueprint('anonymization', __name__, url_prefix='/api/anonymization')

# Import sub-blueprints
from routes.anonymization.conversation_routes import conversation_bp
from routes.anonymization.export_routes import export_bp

# Register sub-blueprints with the main anonymization blueprint
anonymization_bp.register_blueprint(conversation_bp)
anonymization_bp.register_blueprint(export_bp)

__all__ = ['anonymization_bp']
