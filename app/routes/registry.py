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

    # Import all modules that attach routes to the shared data blueprint
    # BEFORE registering the blueprint. Flask disallows adding routes to a
    # blueprint after it has been registered.
    from routes import permissions
    from routes import users

    # ============================================================
    # Core Features
    # ============================================================

    # Rating & Ranking (Email thread rating and feature ranking)
    from routes import rating

    # User Prompts (Prompt management and sharing)
    from routes import prompts

    # Comparison (LLM comparison sessions)
    from routes import comparison

    # Scenarios (Scenario management and distribution)
    from routes import scenarios

    # Authentik OIDC authentication
    from routes.authentik_routes import authentik_auth_blueprint

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

    # Markdown Collab
    from routes.markdown_collab import markdown_collab_bp
    app.register_blueprint(markdown_collab_bp)

    # Web Crawler
    from routes.crawler import crawler_bp
    app.register_blueprint(crawler_bp)

    # ============================================================
    # Project-Specific Features
    # ============================================================

    # KAIMO Project
    from routes.kaimo import kaimo_bp

    # ============================================================
    # Register blueprints AFTER all routes have been attached
    # ============================================================
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(data_bp, url_prefix='/api')
    app.register_blueprint(authentik_auth_blueprint, url_prefix='/auth/authentik')
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
            {'name': 'markdown_collab', 'prefix': '/api/markdown-collab', 'description': 'Markdown Collab workspaces and documents'},
        ],
        'projects': [
            {'name': 'kaimo', 'prefix': '/api/kaimo', 'description': 'KAIMO project routes'},
        ]
    }


__all__ = ['register_all_blueprints', 'get_blueprint_info']
