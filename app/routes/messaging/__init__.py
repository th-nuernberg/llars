"""
Messaging Routes Module

Provides REST endpoints for conversations, messages, encryption, and AI features.

Blueprint:
- messaging_bp: /api/messaging

Global gate: All endpoints return 403 when communication is disabled in SystemSettings.
"""

from flask import Blueprint, jsonify

# Create main blueprint
messaging_bp = Blueprint("messaging", __name__, url_prefix="/api/messaging")


@messaging_bp.before_request
def _check_communication_enabled():
    """Block all messaging requests when communication is globally disabled."""
    from services.system_settings_service import is_communication_enabled
    if not is_communication_enabled():
        return jsonify({
            'success': False,
            'error': 'Communication features are disabled',
        }), 403


# Import sub-blueprints
from .conversation_routes import conversation_bp
from .message_routes import message_bp
from .encryption_routes import encryption_bp
from .ai_routes import ai_bp

# Register all sub-blueprints
messaging_bp.register_blueprint(conversation_bp)
messaging_bp.register_blueprint(message_bp)
messaging_bp.register_blueprint(encryption_bp)
messaging_bp.register_blueprint(ai_bp)

__all__ = ["messaging_bp"]
