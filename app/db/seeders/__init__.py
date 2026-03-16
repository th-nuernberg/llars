"""
Database Seeders Module

Provides a clean API for running all database seeders.
All seeder functions use lazy imports to avoid circular dependencies.
"""
import os
from .feature_types import initialize_feature_function_types
from .categories import initialize_consulting_category_types
from .kaimo import initialize_kaimo_defaults, seed_kaimo_demo_cases
from .schema_patches import apply_schema_patches
from .users import (
    seed_user_groups,
    seed_bootstrap_admin,
    seed_avatar_seeds,
    seed_collab_colors,
)
from .permissions import initialize_permissions
from .rag import initialize_rag_system
from .chatbots import initialize_default_chatbots
from .chatbot_prompt_settings import initialize_chatbot_prompt_settings
from .markdown_collab import initialize_markdown_collab_defaults
from .latex_collab import initialize_latex_collab_defaults
from .scenarios import seed_demo_scenarios
from .prompts import seed_demo_prompts
from .demo_video_data import seed_demo_video_data
from .conferences import seed_demo_conferences
from .anonymization_pipeline import seed_anonymization_demo_data
from .research_groups import seed_research_groups, seed_migrate_conferences_to_group
from .legal_assistant import initialize_legal_assistant
from .analytics_settings import initialize_analytics_settings
from db.models.llm_model import seed_default_models
from services.ai_assist import FieldPromptService


def _backfill_user_provider_model_colors(db):
    """Assign colors to existing user providers that lack model_colors in config_json."""
    try:
        from db.models.user_llm_provider import UserLLMProvider
        from db.models.llm_model import LLMModel

        providers = UserLLMProvider.query.all()
        if not providers:
            return

        all_colors = LLMModel.get_all_assigned_colors()
        changed = 0
        for provider in providers:
            config = provider.config_json or {}
            selected = config.get('selected_models', [])
            single = config.get('model_id', '')
            models = selected if selected else ([single] if single else [])
            if not models:
                continue

            existing_colors = config.get('model_colors', {})
            if not isinstance(existing_colors, dict):
                existing_colors = {}

            # Skip if all models already have colors
            if existing_colors and all(m in existing_colors for m in models):
                continue

            for model in models:
                if model in existing_colors:
                    continue
                color = LLMModel.generate_color(model, existing_colors=all_colors)
                existing_colors[model] = color
                all_colors.append(color)

            config['model_colors'] = existing_colors
            provider.config_json = config
            # Force SQLAlchemy dirty detection for JSON column
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(provider, 'config_json')
            changed += 1

        if changed:
            db.session.commit()
            print(f"  Backfilled model colors for {changed} user provider(s)")
    except Exception as e:
        print(f"  Warning: model color backfill failed: {e}")
        db.session.rollback()


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

    # Backfill model colors for user providers that lack them
    _backfill_user_provider_model_colors(db)

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

    # Seed research groups (runs in all modes, idempotent)
    seed_research_groups(db)

    # Seed demo data in development mode only
    project_state = os.getenv('PROJECT_STATE', 'development').lower()
    if project_state == 'development':
        seed_demo_scenarios(db)
        seed_demo_prompts()
        seed_kaimo_demo_cases(db)
        # Seed demo video data (IJCAI 2026 demo)
        seed_demo_video_data(db)
        # Seed conference manager demo data
        seed_demo_conferences(db)
        # Seed anonymization pipeline demo conversations
        seed_anonymization_demo_data(db)
    else:
        print(f"Demo-Daten übersprungen (PROJECT_STATE={project_state})")

    # Migrate ungrouped conference data to NLP-Group (production fallback)
    seed_migrate_conferences_to_group(db)


__all__ = [
    'run_all_seeders',
    'apply_schema_patches',
    'initialize_feature_function_types',
    'initialize_consulting_category_types',
    'initialize_kaimo_defaults',
    'seed_kaimo_demo_cases',
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
    'seed_demo_video_data',
    'seed_demo_conferences',
    'seed_research_groups',
    'seed_migrate_conferences_to_group',
    'seed_anonymization_demo_data',
]
