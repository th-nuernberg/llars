"""
Migration: create the Mail-Center tables ``email_log`` + ``referral_invitation``.

Backs the Admin Mail-Center (see ``.claude/plans/admin-mail-center-concept.md``
and ``app/db/models/email_log.py``):

``email_log``
    Central audit row written for *every* outbound mail (welcome / reset /
    invitation / announcement). No full bodies are ever stored — only
    subject / type / recipient / status, plus an optional <=280-char preview
    in ``meta_json`` for invitation/announcement.

``referral_invitation``
    Ties one invitation mail to a referral link and flips to *accepted* when a
    matching email registers via that link.

Idempotent — each ``CREATE TABLE IF NOT EXISTS`` is a no-op when the table
already exists, so this is safe to run on every startup. The models also live
under ``db.create_all()``; this explicit migration exists so the schema can be
applied deterministically (FK ordering, indices) without relying on metadata
reflection and to match the project's migration convention.

Usage:
    python -m app.db.migrations.migrate_mail_center_tables
"""

import logging

logger = logging.getLogger(__name__)

_EMAIL_LOG = 'email_log'
_REFERRAL_INVITATION = 'referral_invitation'

# email_log: FK to users + referral_links are SET NULL so deleting a user /
# link never drops the audit row (we keep the recipient_email string anyway).
_CREATE_EMAIL_LOG = f"""
    CREATE TABLE IF NOT EXISTS {_EMAIL_LOG} (
        id                   INT          NOT NULL AUTO_INCREMENT,
        created_at           DATETIME     NOT NULL,
        mail_type            VARCHAR(32)  NOT NULL,
        recipient_email      VARCHAR(320) NOT NULL,
        recipient_user_id    INT          NULL,
        subject              VARCHAR(512) NOT NULL,
        status               VARCHAR(16)  NOT NULL,
        error                TEXT         NULL,
        triggered_by_user_id INT          NULL,
        referral_link_id     INT          NULL,
        scenario_id          INT          NULL,
        meta_json            JSON         NULL,
        PRIMARY KEY (id),
        INDEX ix_email_log_created_at (created_at),
        INDEX ix_email_log_mail_type (mail_type),
        INDEX ix_email_log_recipient_email (recipient_email),
        INDEX ix_email_log_status (status),
        INDEX ix_email_log_recipient_user_id (recipient_user_id),
        INDEX ix_email_log_triggered_by (triggered_by_user_id),
        INDEX ix_email_log_referral_link_id (referral_link_id),
        INDEX ix_email_log_scenario_id (scenario_id)
    )
"""

_CREATE_REFERRAL_INVITATION = f"""
    CREATE TABLE IF NOT EXISTS {_REFERRAL_INVITATION} (
        id               INT          NOT NULL AUTO_INCREMENT,
        referral_link_id INT          NOT NULL,
        email            VARCHAR(320) NOT NULL,
        invited_at       DATETIME     NOT NULL,
        email_log_id     INT          NULL,
        accepted_user_id INT          NULL,
        accepted_at      DATETIME     NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uq_referral_invitation_link_email (referral_link_id, email),
        INDEX ix_referral_invitation_link (referral_link_id),
        INDEX ix_referral_invitation_email (email),
        INDEX ix_referral_invitation_accepted_user (accepted_user_id)
    )
"""


def _table_exists(tbl: str) -> bool:
    from db.database import db
    res = db.session.execute(db.text("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME  = :tbl
        AND   TABLE_SCHEMA = DATABASE()
    """), {'tbl': tbl})
    return (res.scalar() or 0) > 0


def migrate_mail_center_tables(dry_run: bool = False) -> dict:
    """Create the Mail-Center tables. Idempotent — no-op when both exist."""
    from db.database import db

    email_log_exists = _table_exists(_EMAIL_LOG)
    invitation_exists = _table_exists(_REFERRAL_INVITATION)

    if email_log_exists and invitation_exists:
        return {
            'dry_run': dry_run,
            'created': [],
            'already_existed': [_EMAIL_LOG, _REFERRAL_INVITATION],
        }

    if dry_run:
        return {
            'dry_run': True,
            'created': [t for t, exists in (
                (_EMAIL_LOG, email_log_exists),
                (_REFERRAL_INVITATION, invitation_exists),
            ) if not exists],
            'already_existed': [t for t, exists in (
                (_EMAIL_LOG, email_log_exists),
                (_REFERRAL_INVITATION, invitation_exists),
            ) if exists],
        }

    created = []
    try:
        if not email_log_exists:
            db.session.execute(db.text(_CREATE_EMAIL_LOG))
            created.append(_EMAIL_LOG)
        if not invitation_exists:
            db.session.execute(db.text(_CREATE_REFERRAL_INVITATION))
            created.append(_REFERRAL_INVITATION)
        db.session.commit()
        for tbl in created:
            logger.info("[Migration] created table %s", tbl)
    except Exception as exc:
        db.session.rollback()
        logger.error("[Migration] Failed to create Mail-Center tables: %s", exc)
        raise

    return {'dry_run': False, 'created': created, 'already_existed': []}


if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from main import create_app
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    with app.app_context():
        result = migrate_mail_center_tables(dry_run='--dry-run' in sys.argv)
        print(f"\nResult: {result}")
