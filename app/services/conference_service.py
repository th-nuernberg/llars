"""
Conference Service

Handles all conference and paper management business logic including:
- Conference CRUD operations
- Paper CRUD with author management
- Filtering, search, and statistics
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from db.database import db


class ConferenceService:
    """Core service for conference and paper management."""

    # ── Conference CRUD ──────────────────────────────────────────

    @staticmethod
    def list_conferences(
        year: Optional[int] = None,
        core_ranking: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List conferences with optional filters."""
        from db.models import Conference, CoreRanking

        # MariaDB doesn't support NULLS LAST, use CASE expression instead
        query = Conference.query.order_by(
            db.case(
                (Conference.submission_deadline.is_(None), 1),
                else_=0,
            ),
            Conference.submission_deadline.asc(),
            Conference.year.desc(),
        )

        if year:
            query = query.filter(Conference.year == year)

        if core_ranking:
            try:
                ranking_enum = CoreRanking(core_ranking)
                query = query.filter(Conference.core_ranking == ranking_enum)
            except ValueError:
                pass

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Conference.name.ilike(pattern),
                    Conference.acronym.ilike(pattern),
                    Conference.city.ilike(pattern),
                    Conference.country.ilike(pattern),
                )
            )

        return [c.to_dict() for c in query.all()]

    @staticmethod
    def get_conference(conference_id: int) -> Optional[Dict[str, Any]]:
        """Get a single conference by ID."""
        from db.models import Conference

        conf = Conference.query.get(conference_id)
        return conf.to_dict() if conf else None

    @staticmethod
    def create_conference(data: Dict[str, Any], username: str) -> Dict[str, Any]:
        """Create a new conference."""
        from db.models import Conference, CoreRanking

        ranking = CoreRanking.UNRANKED
        if data.get("core_ranking"):
            try:
                ranking = CoreRanking(data["core_ranking"])
            except ValueError:
                pass

        conference = Conference(
            name=data["name"],
            acronym=data["acronym"],
            year=data["year"],
            core_ranking=ranking,
            submission_deadline=_parse_datetime(data.get("submission_deadline")),
            notification_date=_parse_datetime(data.get("notification_date")),
            start_date=_parse_datetime(data.get("start_date")),
            end_date=_parse_datetime(data.get("end_date")),
            city=data.get("city"),
            country=data.get("country"),
            website_url=data.get("website_url"),
            keywords=data.get("keywords"),
            notes=data.get("notes"),
            created_by=username,
        )
        db.session.add(conference)
        db.session.commit()
        return conference.to_dict()

    @staticmethod
    def update_conference(conference_id: int, data: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
        """Update an existing conference."""
        from db.models import Conference, CoreRanking

        conference = Conference.query.get(conference_id)
        if not conference:
            return None

        updatable = [
            "name", "acronym", "year", "city", "country",
            "website_url", "keywords", "notes",
        ]
        for field in updatable:
            if field in data:
                setattr(conference, field, data[field])

        if "core_ranking" in data:
            try:
                conference.core_ranking = CoreRanking(data["core_ranking"])
            except ValueError:
                pass

        date_fields = ["submission_deadline", "notification_date", "start_date", "end_date"]
        for field in date_fields:
            if field in data:
                setattr(conference, field, _parse_datetime(data[field]))

        conference.updated_by = username
        db.session.commit()
        return conference.to_dict()

    @staticmethod
    def delete_conference(conference_id: int) -> bool:
        """Delete a conference. Papers keep their data but lose the FK reference."""
        from db.models import Conference

        conference = Conference.query.get(conference_id)
        if not conference:
            return False
        db.session.delete(conference)
        db.session.commit()
        return True

    # ── Paper CRUD ───────────────────────────────────────────────

    @staticmethod
    def list_papers(
        status: Optional[str] = None,
        conference_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List papers with optional filters."""
        from db.models import Paper, PaperStatus

        query = Paper.query.order_by(Paper.updated_at.desc())

        if status:
            try:
                status_enum = PaperStatus(status)
                query = query.filter(Paper.status == status_enum)
            except ValueError:
                pass

        if conference_id:
            query = query.filter(Paper.conference_id == conference_id)

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Paper.title.ilike(pattern),
                    Paper.description.ilike(pattern),
                )
            )

        return [p.to_dict() for p in query.all()]

    @staticmethod
    def get_paper(paper_id: int) -> Optional[Dict[str, Any]]:
        """Get a single paper by ID."""
        from db.models import Paper

        paper = Paper.query.get(paper_id)
        return paper.to_dict() if paper else None

    @staticmethod
    def create_paper(data: Dict[str, Any], username: str) -> Dict[str, Any]:
        """Create a new paper."""
        from db.models import Paper, PaperStatus

        status = PaperStatus.PLANNING
        if data.get("status"):
            try:
                status = PaperStatus(data["status"])
            except ValueError:
                pass

        paper = Paper(
            title=data["title"],
            status=status,
            conference_id=data.get("conference_id"),
            overleaf_url=data.get("overleaf_url"),
            external_url=data.get("external_url"),
            keywords=data.get("keywords"),
            description=data.get("description"),
            notes=data.get("notes"),
            created_by=username,
        )
        db.session.add(paper)
        db.session.commit()

        # Set authors if provided
        if data.get("authors"):
            ConferenceService.set_paper_authors(paper.id, data["authors"], username)

        return paper.to_dict()

    @staticmethod
    def update_paper(paper_id: int, data: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
        """Update an existing paper."""
        from db.models import Paper, PaperStatus

        paper = Paper.query.get(paper_id)
        if not paper:
            return None

        updatable = [
            "title", "conference_id", "overleaf_url", "external_url",
            "keywords", "description", "notes",
        ]
        for field in updatable:
            if field in data:
                setattr(paper, field, data[field])

        if "status" in data:
            try:
                paper.status = PaperStatus(data["status"])
            except ValueError:
                pass

        paper.updated_by = username

        if "authors" in data:
            ConferenceService.set_paper_authors(paper_id, data["authors"], username)

        db.session.commit()
        return paper.to_dict()

    @staticmethod
    def update_paper_status(paper_id: int, status: str, username: str) -> Optional[Dict[str, Any]]:
        """Lightweight status update (for Kanban drag-and-drop)."""
        from db.models import Paper, PaperStatus

        paper = Paper.query.get(paper_id)
        if not paper:
            return None

        try:
            paper.status = PaperStatus(status)
        except ValueError:
            return None

        paper.updated_by = username
        db.session.commit()
        return paper.to_dict()

    @staticmethod
    def delete_paper(paper_id: int) -> bool:
        """Delete a paper and its authors (cascade)."""
        from db.models import Paper

        paper = Paper.query.get(paper_id)
        if not paper:
            return False
        db.session.delete(paper)
        db.session.commit()
        return True

    # ── Author Management ────────────────────────────────────────

    @staticmethod
    def set_paper_authors(paper_id: int, authors_list: List[Dict], username: str) -> List[Dict]:
        """
        Replace all authors of a paper with the given list.

        Each author dict should have:
        - user_id (int, optional): LLARS user
        - external_name (str, optional): free-text for external authors
        - author_order (int): ordering
        - is_corresponding (bool): flag
        """
        from db.models import Paper, PaperAuthor

        paper = Paper.query.get(paper_id)
        if not paper:
            return []

        # Remove existing authors
        PaperAuthor.query.filter_by(paper_id=paper_id).delete()

        # Add new authors
        for idx, author_data in enumerate(authors_list):
            author = PaperAuthor(
                paper_id=paper_id,
                user_id=author_data.get("user_id"),
                external_name=author_data.get("external_name"),
                author_order=author_data.get("author_order", idx),
                is_corresponding=author_data.get("is_corresponding", False),
            )
            db.session.add(author)

        paper.updated_by = username
        db.session.commit()
        return [a.to_dict() for a in PaperAuthor.query.filter_by(paper_id=paper_id).order_by(PaperAuthor.author_order).all()]

    # ── Statistics ───────────────────────────────────────────────

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Get aggregated statistics for the dashboard."""
        from db.models import Conference, Paper, PaperStatus
        from sqlalchemy import func

        total_conferences = Conference.query.count()

        # Papers by status
        status_counts = (
            db.session.query(Paper.status, func.count(Paper.id))
            .group_by(Paper.status)
            .all()
        )
        papers_by_status = {s.value: c for s, c in status_counts}

        # Upcoming deadlines (next 5)
        upcoming = (
            Conference.query
            .filter(Conference.submission_deadline >= datetime.utcnow())
            .order_by(Conference.submission_deadline.asc())
            .limit(5)
            .all()
        )

        return {
            "total_conferences": total_conferences,
            "total_papers": sum(papers_by_status.values()),
            "papers_by_status": papers_by_status,
            "upcoming_deadlines": [
                {
                    "id": c.id,
                    "acronym": c.acronym,
                    "year": c.year,
                    "submission_deadline": c.submission_deadline.isoformat() if c.submission_deadline else None,
                }
                for c in upcoming
            ],
        }


def _parse_datetime(value) -> Optional[datetime]:
    """Parse a datetime string or return None."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
