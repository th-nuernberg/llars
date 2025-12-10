"""
Database Seeders Module

Provides a clean API for running all database seeders.
All seeder functions use lazy imports to avoid circular dependencies.
"""
import os
from .feature_types import initialize_feature_function_types
from .categories import initialize_consulting_category_types
from .kaimo import initialize_kaimo_defaults
from .users import seed_user_groups
from .permissions import initialize_permissions
from .rag import initialize_rag_system
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

    # Seed permissions and roles (includes RAG system initialization)
    initialize_permissions(db)

    # Seed user groups (only if START_SEEDER is true)
    start_seeder = os.getenv('START_SEEDER', 'false').lower()
    if start_seeder == 'true':
        seed_user_groups(db)
    else:
        print(f"Seeder übersprungen (START_SEEDER={start_seeder})")

    # Seed demo scenarios in development mode
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
    'initialize_permissions',
    'initialize_rag_system',
    'seed_demo_scenarios',
]
