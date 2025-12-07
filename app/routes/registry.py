"""
Blueprint Registry

Central registry for all Flask blueprints in LLARS.
This file provides a single entry point to register all routes.

Structure:
- Feature-based organization
- Clear separation of concerns
- Easy to add/remove blueprints
"""

from flask import Flask


def register_all_blueprints(app: Flask) -> None:
    """
    Register all blueprints with the Flask app.

    Args:
        app: Flask application instance
    """

    # ============================================================
    # Authentication & Authorization
    # ============================================================

    # Legacy auth routes (backwards compatibility)
    from routes.auth import auth_bp, data_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(data_bp, url_prefix='/api')

    # Authentik OIDC authentication
    from routes.authentik_routes import authentik_auth_blueprint
    app.register_blueprint(authentik_auth_blueprint, url_prefix='/auth/authentik')

    # Permissions & Roles management
    # Note: Uses data_bp which is already registered above
    from routes import permissions

    # ============================================================
    # Core Features
    # ============================================================

    # Rating & Ranking (Email thread rating and feature ranking)
    # Note: Uses data_bp which is already registered above
    from routes import rating

    # User Prompts (Prompt management and sharing)
    # Note: Uses data_bp which is already registered above
    from routes import prompts

    # Comparison (LLM comparison sessions)
    # Note: Uses data_bp which is already registered above
    from routes import comparison

    # Scenarios (Scenario management and distribution)
    # Note: Uses data_bp which is already registered above
    from routes import scenarios

    # ============================================================
    # LLM & AI Features
    # ============================================================

    # LLM Models management
    from routes.llm import llm_bp
    app.register_blueprint(llm_bp, url_prefix='/api/llm')

    # LLM-as-Judge (Automated evaluation)
    from routes.judge import judge_bp
    app.register_blueprint(judge_bp)

    # OnCoCo Analysis
    from routes.oncoco import oncoco_bp
    app.register_blueprint(oncoco_bp)

    # ============================================================
    # Document & Knowledge Management
    # ============================================================

    # RAG Pipeline (Document management, collections, search)
    from routes.rag import rag_bp
    app.register_blueprint(rag_bp)

    # Chatbot
    from routes.chatbot import chatbot_bp
    app.register_blueprint(chatbot_bp)

    # Web Crawler
    from routes.crawler import crawler_bp
    app.register_blueprint(crawler_bp)

    # ============================================================
    # Project-Specific Features
    # ============================================================

    # KAIMO Project
    from routes.kaimo import kaimo_bp
    app.register_blueprint(kaimo_bp)


def get_blueprint_info() -> dict:
    """
    Get information about all registered blueprints.
    Useful for debugging and documentation.

    Returns:
        Dictionary with blueprint information
    """
    return {
        'authentication': [
            {'name': 'auth', 'prefix': '/auth', 'description': 'Legacy authentication (backwards compatibility)'},
            {'name': 'authentik_auth', 'prefix': '/auth/authentik', 'description': 'Authentik OIDC authentication'},
        ],
        'authorization': [
            {'name': 'permissions', 'prefix': '/api/permissions', 'description': 'Permissions and roles management'},
        ],
        'core_features': [
            {'name': 'rating', 'prefix': '/api', 'description': 'Email thread rating and feature ranking'},
            {'name': 'prompts', 'prefix': '/api/prompts', 'description': 'User prompt management and sharing'},
            {'name': 'comparison', 'prefix': '/api/comparison', 'description': 'LLM comparison sessions'},
            {'name': 'scenarios', 'prefix': '/api/scenarios', 'description': 'Scenario management'},
        ],
        'llm_features': [
            {'name': 'llm', 'prefix': '/api/llm', 'description': 'LLM model management'},
            {'name': 'judge', 'prefix': '/api/judge', 'description': 'LLM-as-Judge automated evaluation'},
            {'name': 'oncoco', 'prefix': '/api/oncoco', 'description': 'OnCoCo analysis'},
        ],
        'knowledge_management': [
            {'name': 'rag', 'prefix': '/api/rag', 'description': 'RAG document management and search'},
            {'name': 'chatbot', 'prefix': '/api/chatbot', 'description': 'Chatbot interface'},
            {'name': 'crawler', 'prefix': '/api/crawler', 'description': 'Web crawler'},
        ],
        'projects': [
            {'name': 'kaimo', 'prefix': '/api/kaimo', 'description': 'KAIMO project routes'},
        ]
    }


__all__ = ['register_all_blueprints', 'get_blueprint_info']
