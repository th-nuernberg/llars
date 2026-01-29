"""
Migration script for scenario role restructuring.

This script updates the scenario_users table to rename roles:
- RATER -> EVALUATOR (users who can rate/evaluate/interact)
- EVALUATOR -> VIEWER (users who can only view, read-only access)

The OWNER role remains unchanged.

Run this migration BEFORE deploying the new code to production.

Usage:
    python -m app.db.migrations.migrate_scenario_roles

Or via Flask shell:
    from app.db.migrations.migrate_scenario_roles import migrate_roles
    migrate_roles()
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def get_migration_sql() -> Tuple[str, str, str]:
    """
    Get the SQL statements for the migration.

    Returns a tuple of (step1, step2, step3) SQL statements.
    Order matters to avoid constraint violations:
    1. RATER -> TEMP_EVAL (temporary placeholder)
    2. EVALUATOR -> VIEWER (old evaluator becomes viewer)
    3. TEMP_EVAL -> EVALUATOR (old rater becomes evaluator)
    """
    step1 = "UPDATE scenario_users SET role = 'TEMP_EVAL' WHERE role = 'Rater';"
    step2 = "UPDATE scenario_users SET role = 'Viewer' WHERE role = 'Evaluator';"
    step3 = "UPDATE scenario_users SET role = 'Evaluator' WHERE role = 'TEMP_EVAL';"

    return step1, step2, step3


def migrate_roles(dry_run: bool = False) -> dict:
    """
    Execute the role migration.

    Args:
        dry_run: If True, only shows what would be changed without committing.

    Returns:
        Dict with migration statistics.
    """
    from db.database import db
    from db.models.scenario import ScenarioUsers

    # Count current roles before migration
    rater_count = ScenarioUsers.query.filter_by(role='Rater').count()
    evaluator_count = ScenarioUsers.query.filter_by(role='Evaluator').count()
    owner_count = ScenarioUsers.query.filter_by(role='Owner').count()

    logger.info(f"Current role distribution:")
    logger.info(f"  - Owner: {owner_count}")
    logger.info(f"  - Rater: {rater_count} (will become Evaluator)")
    logger.info(f"  - Evaluator: {evaluator_count} (will become Viewer)")

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        return {
            'dry_run': True,
            'raters_to_migrate': rater_count,
            'evaluators_to_migrate': evaluator_count,
            'owners_unchanged': owner_count,
        }

    # Execute migration in order
    step1, step2, step3 = get_migration_sql()

    try:
        # Step 1: RATER -> TEMP_EVAL
        result1 = db.session.execute(db.text(step1))
        logger.info(f"Step 1: Moved {result1.rowcount} Raters to TEMP_EVAL")

        # Step 2: EVALUATOR -> VIEWER
        result2 = db.session.execute(db.text(step2))
        logger.info(f"Step 2: Moved {result2.rowcount} Evaluators to Viewer")

        # Step 3: TEMP_EVAL -> EVALUATOR
        result3 = db.session.execute(db.text(step3))
        logger.info(f"Step 3: Moved {result3.rowcount} TEMP_EVAL to Evaluator")

        db.session.commit()
        logger.info("Migration completed successfully!")

        # Verify final state
        new_evaluator_count = ScenarioUsers.query.filter_by(role='Evaluator').count()
        new_viewer_count = ScenarioUsers.query.filter_by(role='Viewer').count()

        logger.info(f"Final role distribution:")
        logger.info(f"  - Owner: {owner_count}")
        logger.info(f"  - Evaluator: {new_evaluator_count}")
        logger.info(f"  - Viewer: {new_viewer_count}")

        return {
            'dry_run': False,
            'raters_migrated': rater_count,
            'evaluators_migrated': evaluator_count,
            'owners_unchanged': owner_count,
            'new_evaluator_count': new_evaluator_count,
            'new_viewer_count': new_viewer_count,
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"Migration failed: {e}")
        raise


def rollback_roles() -> dict:
    """
    Rollback the role migration (for emergency use).

    This reverses the changes:
    - EVALUATOR -> RATER
    - VIEWER -> EVALUATOR
    """
    from db.database import db
    from db.models.scenario import ScenarioUsers

    evaluator_count = ScenarioUsers.query.filter_by(role='Evaluator').count()
    viewer_count = ScenarioUsers.query.filter_by(role='Viewer').count()

    logger.warning("Rolling back role migration...")

    try:
        # Reverse order
        step1 = "UPDATE scenario_users SET role = 'TEMP_RATER' WHERE role = 'Evaluator';"
        step2 = "UPDATE scenario_users SET role = 'Evaluator' WHERE role = 'Viewer';"
        step3 = "UPDATE scenario_users SET role = 'Rater' WHERE role = 'TEMP_RATER';"

        db.session.execute(db.text(step1))
        db.session.execute(db.text(step2))
        db.session.execute(db.text(step3))

        db.session.commit()
        logger.info("Rollback completed successfully!")

        return {
            'evaluators_rolled_back': evaluator_count,
            'viewers_rolled_back': viewer_count,
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"Rollback failed: {e}")
        raise


if __name__ == '__main__':
    import sys
    import os

    # Add app to path for standalone execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

    from main import create_app

    logging.basicConfig(level=logging.INFO)

    app = create_app()
    with app.app_context():
        # Check for --dry-run flag
        dry_run = '--dry-run' in sys.argv
        rollback = '--rollback' in sys.argv

        if rollback:
            result = rollback_roles()
        else:
            result = migrate_roles(dry_run=dry_run)

        print(f"\nResult: {result}")
