"""
Migration: referral_links demo-content provisioning.

Adds one column that lets a referral link hand out working material (not just
scenario memberships) to everyone who registers through it — built for the
IJCAI conference QR link, generic enough for any future demo link:

- ``provision_json`` (LONGTEXT NULL) -> what registrants receive:
  ``{"clone_prompt_ids": [<UserPrompt.prompt_id>, ...],
     "share_job_ids":    [<GenerationJob.id>, ...]}``
  Prompts are cloned (own editable copy per user), generation jobs are shared
  read-only. Applied by ReferralService.provision_demo_content.

Defaults keep existing links unchanged: NULL = provision nothing.

Usage:
    python -m app.db.migrations.migrate_referral_link_provisioning
"""

import logging

logger = logging.getLogger(__name__)


_COLUMNS = (
    ('provision_json', 'LONGTEXT NULL'),
)


def _column_exists(column: str) -> bool:
    from db.database import db
    res = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME  = 'referral_links'
        AND   COLUMN_NAME = :col
        AND   TABLE_SCHEMA = DATABASE()
    """), {'col': column})
    return (res.scalar() or 0) > 0


def migrate_referral_link_provisioning(dry_run: bool = False) -> dict:
    """Add the provision_json column. Idempotent."""
    from db.database import db

    added = []
    already = []

    for column, ddl in _COLUMNS:
        if _column_exists(column):
            already.append(column)
            continue
        if dry_run:
            continue
        try:
            db.session.execute(db.text(
                f"ALTER TABLE referral_links ADD COLUMN {column} {ddl}"
            ))
            added.append(column)
        except Exception as exc:
            db.session.rollback()
            logger.error("[Migration] Failed to add %s on referral_links: %s", column, exc)
            raise

    if added and not dry_run:
        db.session.commit()
        logger.info("[Migration] referral_links — added columns: %s", added)

    return {
        'dry_run': dry_run,
        'columns_added': added,
        'already_existed': already,
    }


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from main import create_app
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    with app.app_context():
        result = migrate_referral_link_provisioning(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
