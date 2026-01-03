# chatbot_routes.py
"""
Chatbot Routes Registry

This module combines all chatbot-related routes into a single blueprint.
Routes are organized into separate modules for maintainability:

- chatbot_crud_routes: CRUD operations (create, read, update, delete, duplicate)
- chatbot_collection_routes: Collection assignment and management
- chatbot_chat_routes: Chat functionality and capabilities
- chatbot_conversation_routes: Conversation management and message rating
- chatbot_stats_routes: Statistics and analytics
- chatbot_wizard_routes: Builder wizard session management
"""

from flask import Blueprint

# Create main blueprint
chatbot_blueprint = Blueprint('chatbot', __name__, url_prefix='/api/chatbots')

# Import sub-blueprints
from .chatbot_crud_routes import chatbot_crud_bp
from .chatbot_collection_routes import chatbot_collection_bp
from .chatbot_chat_routes import chatbot_chat_bp
from .chatbot_conversation_routes import chatbot_conversation_bp
from .chatbot_stats_routes import chatbot_stats_bp
from .chatbot_wizard_routes import chatbot_wizard_bp

# Register all sub-blueprints
chatbot_blueprint.register_blueprint(chatbot_crud_bp)
chatbot_blueprint.register_blueprint(chatbot_collection_bp)
chatbot_blueprint.register_blueprint(chatbot_chat_bp)
chatbot_blueprint.register_blueprint(chatbot_conversation_bp)
chatbot_blueprint.register_blueprint(chatbot_stats_bp)
chatbot_blueprint.register_blueprint(chatbot_wizard_bp)
