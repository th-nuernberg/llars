"""
Research Groups Seeder

Seeds initial research groups and assigns existing conference data
to the NLP-Group. This runs both in development and production:
- Creates groups (idempotent)
- Migrates ungrouped conferences/papers/series to NLP-Group
"""

import logging

logger = logging.getLogger(__name__)


def seed_research_groups(db):
    """
    Seed research groups with initial members.
    Idempotent: skips if groups already exist.
    """
    from db.models.conference import (
        ResearchGroup, ResearchGroupMember, ResearchGroupRole,
    )
    from db.models.user import User

    # Skip if groups already exist
    if ResearchGroup.query.first():
        return

    logger.info("Seeding research groups...")

    # ── NLP-Group ──────────────────────────────────────
    nlp_group = ResearchGroup(
        name="NLP-Group",
        slug="nlp-group",
        description="Natural Language Processing Research Group",
        created_by="ieb-steigerwald",
    )
    db.session.add(nlp_group)
    db.session.flush()

    # Add members
    members = [
        ("ieb-steigerwald", ResearchGroupRole.OWNER),
        ("ieb-rudolph", ResearchGroupRole.MEMBER),
        ("ieb-albrecht", ResearchGroupRole.MEMBER),
    ]
    for username, role in members:
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.add(ResearchGroupMember(
                group_id=nlp_group.id,
                user_id=user.id,
                role=role,
                added_by="ieb-steigerwald",
            ))

    # ── KIZ (empty group for testing, no members) ──────
    kiz_group = ResearchGroup(
        name="KIZ",
        slug="kiz",
        description="Competence Center for Information Systems",
        created_by="admin",
    )
    db.session.add(kiz_group)

    db.session.commit()
    logger.info("Research groups seeded: NLP-Group, KIZ (empty)")


def seed_migrate_conferences_to_group(db):
    """
    Assign all conferences/papers/series with group_id=NULL to NLP-Group.
    This is the production migration fallback.
    Idempotent: only updates NULL group_id rows.
    """
    from db.models.conference import (
        ResearchGroup, Conference, Paper, ConferenceSeries,
    )

    nlp_group = ResearchGroup.query.filter_by(slug="nlp-group").first()
    if not nlp_group:
        return

    # Migrate conferences
    migrated_confs = (
        Conference.query
        .filter(Conference.group_id.is_(None))
        .update({Conference.group_id: nlp_group.id}, synchronize_session='fetch')
    )

    # Migrate papers
    migrated_papers = (
        Paper.query
        .filter(Paper.group_id.is_(None))
        .update({Paper.group_id: nlp_group.id}, synchronize_session='fetch')
    )

    # Migrate series
    migrated_series = (
        ConferenceSeries.query
        .filter(ConferenceSeries.group_id.is_(None))
        .update({ConferenceSeries.group_id: nlp_group.id}, synchronize_session='fetch')
    )

    if migrated_confs or migrated_papers or migrated_series:
        db.session.commit()
        logger.info(
            f"Migrated to NLP-Group: {migrated_confs} conferences, "
            f"{migrated_papers} papers, {migrated_series} series"
        )
