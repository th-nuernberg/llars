"""
Database Seeders Module

Provides a clean API for running all database seeders.
All seeder functions use lazy imports to avoid circular dependencies.
"""
import os
from .feature_types import initialize_feature_function_types
from .categories import initialize_consulting_category_types
from .kaimo import initialize_kaimo_defaults
from .users import seed_user_groups, seed_bootstrap_admin
from .permissions import initialize_permissions
from .rag import initialize_rag_system
from .chatbots import initialize_default_chatbots
from .chatbot_prompt_settings import initialize_chatbot_prompt_settings
from .markdown_collab import initialize_markdown_collab_defaults
from .scenarios import seed_demo_scenarios


def run_all_seeders(db):
    """
    Run all database seeders in the correct order.

    This function is called during application startup to ensure
    all required data is seeded into the database.

    Args:
        db: SQLAlchemy database instance
    """
    # Seed feature function types
    initialize_feature_function_types(db)

    # Seed consulting categories
    initialize_consulting_category_types(db)

    # Seed KAIMO defaults
    initialize_kaimo_defaults(db)

    # Seed user groups (always needed for bootstrap admin)
    seed_user_groups(db)

    # Seed permissions and roles (includes RAG system initialization)
    initialize_permissions(db)

    # ALWAYS create bootstrap admin user (uses SYSTEM_ADMIN_API_KEY from .env)
    # This ensures the admin user exists for API access
    seed_bootstrap_admin(db)

    # Initialize RAG system (default collection + scan /app/rag_docs)
    initialize_rag_system(db)

    # Create default chatbots (admin-only standard bot)
    initialize_default_chatbots(db)

    # Ensure every chatbot has prompt settings
    initialize_chatbot_prompt_settings(db)

    # Create Markdown Collab demo workspace/tree
    initialize_markdown_collab_defaults(db)

    # Seed demo scenarios in development mode only
    project_state = os.getenv('PROJECT_STATE', 'development').lower()
    if project_state == 'development':
        seed_demo_scenarios(db)
    else:
        print(f"Demo-Szenarien übersprungen (PROJECT_STATE={project_state})")


__all__ = [
    'run_all_seeders',
    'initialize_feature_function_types',
    'initialize_consulting_category_types',
    'initialize_kaimo_defaults',
    'seed_user_groups',
    'seed_bootstrap_admin',
    'initialize_permissions',
    'initialize_rag_system',
    'initialize_default_chatbots',
    'initialize_chatbot_prompt_settings',
    'initialize_markdown_collab_defaults',
    'seed_demo_scenarios',
]
