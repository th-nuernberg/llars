"""
Database Seeders Module

Provides a clean API for running all database seeders.
All seeder functions use lazy imports to avoid circular dependencies.
"""
import os
from .feature_types import initialize_feature_function_types
from .categories import initialize_consulting_category_types
from .kaimo import initialize_kaimo_defaults
from .schema_patches import apply_schema_patches
from .users import seed_user_groups, seed_bootstrap_admin, seed_avatar_seeds, seed_collab_colors
from .permissions import initialize_permissions
from .rag import initialize_rag_system
from .chatbots import initialize_default_chatbots
from .chatbot_prompt_settings import initialize_chatbot_prompt_settings
from .markdown_collab import initialize_markdown_collab_defaults
from .latex_collab import initialize_latex_collab_defaults
from .scenarios import seed_demo_scenarios
from .prompts import seed_demo_prompts
from .legal_assistant import initialize_legal_assistant
from .analytics_settings import initialize_analytics_settings
from db.models.llm_model import seed_default_models
from services.ai_assist import FieldPromptService


def run_all_seeders(db):
    """
    Run all database seeders in the correct order.

    This function is called during application startup to ensure
    all required data is seeded into the database.

    Args:
        db: SQLAlchemy database instance
    """
    # Apply idempotent schema patches before any model queries run.
    apply_schema_patches(db)

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

    # Create default analytics settings (Matomo tracking config)
    initialize_analytics_settings(db)

    # ALWAYS create bootstrap admin user (uses SYSTEM_ADMIN_API_KEY from .env)
    # This ensures the admin user exists for API access
    seed_bootstrap_admin(db)

    # Ensure stable avatar seeds for all users
    seed_avatar_seeds(db)
    # Ensure every user has a collab color
    seed_collab_colors(db)

    # Seed default LLM models (embedding, reranker, etc.)
    # Must be called BEFORE initialize_rag_system as RAG requires embedding model
    seed_default_models()

    # Initialize RAG system (default collection + scan /app/data/rag/standard)
    initialize_rag_system(db)

    # Create default chatbots (admin-only standard bot)
    initialize_default_chatbots(db)

    # Ensure every chatbot has prompt settings
    initialize_chatbot_prompt_settings(db)

    # Initialize Legal Assistant chatbot with German laws
    initialize_legal_assistant(db)

    # Create Markdown Collab demo workspace/tree
    initialize_markdown_collab_defaults(db)

    # Create LaTeX Collab demo workspace with LLARS paper
    initialize_latex_collab_defaults(db)

    # Seed default field prompts for AI-Assist feature
    FieldPromptService.seed_defaults()

    # Seed demo scenarios and prompts in development mode only
    project_state = os.getenv('PROJECT_STATE', 'development').lower()
    if project_state == 'development':
        seed_demo_scenarios(db)
        seed_demo_prompts()
    else:
        print(f"Demo-Szenarien übersprungen (PROJECT_STATE={project_state})")


__all__ = [
    'run_all_seeders',
    'apply_schema_patches',
    'initialize_feature_function_types',
    'initialize_consulting_category_types',
    'initialize_kaimo_defaults',
    'seed_user_groups',
    'seed_bootstrap_admin',
    'seed_avatar_seeds',
    'seed_collab_colors',
    'initialize_permissions',
    'seed_default_models',
    'initialize_rag_system',
    'initialize_default_chatbots',
    'initialize_chatbot_prompt_settings',
    'initialize_legal_assistant',
    'initialize_markdown_collab_defaults',
    'initialize_latex_collab_defaults',
    'initialize_analytics_settings',
    'seed_demo_scenarios',
    'seed_demo_prompts',
]
