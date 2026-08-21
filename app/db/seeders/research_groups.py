"""
Research Groups Seeder

Seeds initial research groups and assigns existing conference data
to the NLP-Group. This runs both in development and production:
- Creates groups (idempotent, all modes)
- Adds demo members only in development mode
- Migrates ungrouped conferences/papers/series to NLP-Group
"""

import json
import logging
import os

from sqlalchemy import text

logger = logging.getLogger(__name__)


def _is_development():
    return os.getenv('PROJECT_STATE', 'development').lower() == 'development'


def _normalize_legacy_keywords_value(raw_value):
    """
    Coerce legacy keyword payloads into the list shape expected by the app.

    Conference manager forms submit keywords as arrays, but older rows can still
    contain plain text blobs from before the JSON constraint was introduced.
    """
    if raw_value is None:
        return []

    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode('utf-8', errors='ignore')

    parsed_value = raw_value
    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
        if not raw_value:
            return []
        try:
            parsed_value = json.loads(raw_value)
        except json.JSONDecodeError:
            return [raw_value]

    if parsed_value is None:
        return []
    if isinstance(parsed_value, list):
        return [str(item).strip() for item in parsed_value if str(item).strip()]
    if isinstance(parsed_value, str):
        parsed_value = parsed_value.strip()
        return [parsed_value] if parsed_value else []

    normalized = str(parsed_value).strip()
    return [normalized] if normalized else []


def _normalize_invalid_keywords_for_table(db, table_name):
    """
    Repair legacy rows whose keyword payload is plain text instead of JSON.

    MariaDB revalidates the JSON CHECK constraint on every UPDATE, so a later
    group_id migration fails even though it does not touch the keywords column.
    """
    invalid_rows = db.session.execute(
        text(f"""
            SELECT id, keywords
            FROM {table_name}
            WHERE group_id IS NULL
              AND keywords IS NOT NULL
              AND JSON_VALID(keywords) = 0
        """)
    ).mappings()

    normalized_rows = 0
    for row in invalid_rows:
        normalized_keywords = _normalize_legacy_keywords_value(row['keywords'])
        db.session.execute(
            text(f"UPDATE {table_name} SET keywords = :keywords WHERE id = :row_id"),
            {
                'row_id': row['id'],
                'keywords': json.dumps(normalized_keywords, ensure_ascii=False),
            }
        )
        normalized_rows += 1

    if normalized_rows:
        logger.warning(
            "Normalized %s legacy keyword rows in %s before group migration",
            normalized_rows,
            table_name,
        )

    return normalized_rows


def seed_research_groups(db):
    """
    Seed research groups with initial members.
    Idempotent: skips if groups already exist.
    Groups are always created; demo members only in development.
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
        created_by="admin",
    )
    db.session.add(nlp_group)
    db.session.flush()

    # ── KIZ ───────────────────────────────────────────
    kiz_group = ResearchGroup(
        name="KIZ",
        slug="kiz",
        description="Competence Center for Information Systems",
        created_by="admin",
    )
    db.session.add(kiz_group)
    db.session.flush()

    # ── Demo members (development only) ───────────────
    if _is_development():
        nlp_members = [
            ("admin", ResearchGroupRole.OWNER),
            ("researcher", ResearchGroupRole.MEMBER),
        ]
        for username, role in nlp_members:
            user = User.query.filter_by(username=username).first()
            if user:
                db.session.add(ResearchGroupMember(
                    group_id=nlp_group.id,
                    user_id=user.id,
                    role=role,
                    added_by="admin",
                ))

        kiz_members = [
            ("admin", ResearchGroupRole.OWNER),
            ("evaluator", ResearchGroupRole.MEMBER),
        ]
        for username, role in kiz_members:
            user = User.query.filter_by(username=username).first()
            if user:
                db.session.add(ResearchGroupMember(
                    group_id=kiz_group.id,
                    user_id=user.id,
                    role=role,
                    added_by="admin",
                ))

        logger.info("Research groups seeded with demo members: NLP-Group, KIZ")
    else:
        logger.info("Research groups seeded (empty, production mode): NLP-Group, KIZ")

    db.session.commit()


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

    _normalize_invalid_keywords_for_table(db, 'conferences')
    _normalize_invalid_keywords_for_table(db, 'papers')
    _normalize_invalid_keywords_for_table(db, 'conference_series')

    # Commit normalization so MariaDB sees valid JSON before bulk UPDATE
    db.session.commit()

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
