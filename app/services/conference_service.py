"""
Conference Service

Handles all conference and paper management business logic including:
- Conference series management
- Conference CRUD operations
- Paper CRUD with author management
- Filtering, search, and statistics
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from db.database import db


class ConferenceSeriesService:
    """Service for managing conference series (e.g. NeurIPS, AAAI)."""

    @staticmethod
    def list_series(search: Optional[str] = None, group_id: Optional[int] = None) -> List[Dict[str, Any]]:
        from db.models import ConferenceSeries

        query = ConferenceSeries.query.order_by(ConferenceSeries.acronym.asc())
        if group_id:
            query = query.filter(ConferenceSeries.group_id == group_id)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    ConferenceSeries.name.ilike(pattern),
                    ConferenceSeries.acronym.ilike(pattern),
                )
            )
        return [s.to_dict() for s in query.all()]

    @staticmethod
    def get_series(series_id: int) -> Optional[Dict[str, Any]]:
        from db.models import ConferenceSeries

        series = ConferenceSeries.query.get(series_id)
        return series.to_dict() if series else None

    @staticmethod
    def create_series(data: Dict[str, Any], username: str) -> Dict[str, Any]:
        from db.models import ConferenceSeries, CoreRanking

        ranking = None
        if data.get("core_ranking"):
            try:
                ranking = CoreRanking(data["core_ranking"])
            except ValueError:
                pass

        series = ConferenceSeries(
            name=data["name"],
            acronym=data["acronym"],
            group_id=data.get("group_id"),
            core_ranking=ranking,
            website_url=data.get("website_url"),
            keywords=data.get("keywords"),
            notes=data.get("notes"),
            created_by=username,
        )
        db.session.add(series)
        db.session.commit()
        return series.to_dict()

    @staticmethod
    def update_series(series_id: int, data: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
        from db.models import ConferenceSeries, CoreRanking

        series = ConferenceSeries.query.get(series_id)
        if not series:
            return None

        for field in ["name", "acronym", "website_url", "keywords", "notes"]:
            if field in data:
                setattr(series, field, data[field])

        if "core_ranking" in data:
            try:
                series.core_ranking = CoreRanking(data["core_ranking"]) if data["core_ranking"] else None
            except ValueError:
                pass

        series.updated_by = username
        db.session.commit()
        return series.to_dict()

    @staticmethod
    def delete_series(series_id: int) -> bool:
        from db.models import ConferenceSeries

        series = ConferenceSeries.query.get(series_id)
        if not series:
            return False
        db.session.delete(series)
        db.session.commit()
        return True

    @staticmethod
    def find_series_by_acronym(acronym: str) -> Optional[Dict[str, Any]]:
        from db.models import ConferenceSeries

        series = ConferenceSeries.query.filter(
            ConferenceSeries.acronym.ilike(acronym)
        ).first()
        return series.to_dict() if series else None

    @staticmethod
    def get_new_edition_defaults(series_id: int) -> Optional[Dict[str, Any]]:
        """Pre-fill defaults for a new conference edition based on series + latest edition."""
        from db.models import ConferenceSeries, Conference

        series = ConferenceSeries.query.get(series_id)
        if not series:
            return None

        latest = (
            Conference.query
            .filter(Conference.series_id == series_id)
            .order_by(Conference.year.desc())
            .first()
        )

        defaults = {
            "series_id": series.id,
            "name": series.name,
            "acronym": series.acronym,
            "core_ranking": series.core_ranking.value if series.core_ranking else "Unranked",
            "keywords": series.keywords or [],
            "website_url": series.website_url,
        }

        if latest:
            defaults["year"] = latest.year + 1
            defaults["city"] = latest.city
            defaults["country"] = latest.country
        else:
            defaults["year"] = datetime.utcnow().year + 1

        return defaults


class ConferenceService:
    """Core service for conference and paper management."""

    # ── Conference CRUD ──────────────────────────────────────────

    @staticmethod
    def list_conferences(
        year: Optional[int] = None,
        core_ranking: Optional[str] = None,
        search: Optional[str] = None,
        group_id: Optional[int] = None,
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

        if group_id:
            query = query.filter(Conference.group_id == group_id)

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
            group_id=data.get("group_id"),
            series_id=data.get("series_id"),
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
            "name", "acronym", "year", "series_id", "city", "country",
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
        group_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List papers with optional filters."""
        from db.models import Paper, PaperStatus

        query = Paper.query.order_by(Paper.updated_at.desc())

        if group_id:
            query = query.filter(Paper.group_id == group_id)

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
            group_id=data.get("group_id"),
            conference_id=data.get("conference_id"),
            latex_workspace_id=data.get("latex_workspace_id"),
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
            "title", "conference_id", "latex_workspace_id", "overleaf_url",
            "external_url", "keywords", "description", "notes",
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

    # ── Submission History ─────────────────────────────────────────

    @staticmethod
    def add_submission(paper_id: int, data: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
        """Add a submission entry and sync paper's conference_id + status."""
        from db.models import Paper, PaperSubmission, SubmissionStatus

        paper = Paper.query.get(paper_id)
        if not paper:
            return None

        status = SubmissionStatus.SUBMITTED
        if data.get("status"):
            try:
                status = SubmissionStatus(data["status"])
            except ValueError:
                pass

        submission = PaperSubmission(
            paper_id=paper_id,
            conference_id=data.get("conference_id"),
            status=status,
            submitted_at=_parse_datetime(data.get("submitted_at")),
            decided_at=_parse_datetime(data.get("decided_at")),
            notes=data.get("notes"),
        )
        db.session.add(submission)
        db.session.flush()

        ConferenceService._sync_paper_from_submissions(paper)
        paper.updated_by = username
        db.session.commit()
        return paper.to_dict()

    @staticmethod
    def update_submission(submission_id: int, data: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
        """Update a submission entry and re-sync paper."""
        from db.models import PaperSubmission, SubmissionStatus

        submission = PaperSubmission.query.get(submission_id)
        if not submission:
            return None

        if "conference_id" in data:
            submission.conference_id = data["conference_id"]
        if "status" in data:
            try:
                submission.status = SubmissionStatus(data["status"])
            except ValueError:
                pass
        if "submitted_at" in data:
            submission.submitted_at = _parse_datetime(data["submitted_at"])
        if "decided_at" in data:
            submission.decided_at = _parse_datetime(data["decided_at"])
        if "notes" in data:
            submission.notes = data["notes"]

        paper = submission.paper
        ConferenceService._sync_paper_from_submissions(paper)
        paper.updated_by = username
        db.session.commit()
        return paper.to_dict()

    @staticmethod
    def delete_submission(submission_id: int, username: str) -> Optional[Dict[str, Any]]:
        """Delete a submission entry and re-sync paper."""
        from db.models import PaperSubmission

        submission = PaperSubmission.query.get(submission_id)
        if not submission:
            return None

        paper = submission.paper
        db.session.delete(submission)
        db.session.flush()

        ConferenceService._sync_paper_from_submissions(paper)
        paper.updated_by = username
        db.session.commit()
        return paper.to_dict()

    @staticmethod
    def _sync_paper_from_submissions(paper):
        """Set paper's conference_id and status based on the latest submission."""
        from db.models import PaperStatus, PaperSubmission

        latest = (
            PaperSubmission.query
            .filter_by(paper_id=paper.id)
            .order_by(PaperSubmission.created_at.desc())
            .first()
        )

        if not latest:
            return

        paper.conference_id = latest.conference_id

        status_map = {
            "submitted": PaperStatus.SUBMITTED,
            "accepted": PaperStatus.ACCEPTED,
            "rejected": PaperStatus.REJECTED,
            "withdrawn": PaperStatus.PLANNING,
        }
        mapped = status_map.get(latest.status.value)
        if mapped:
            paper.status = mapped

    # ── Statistics ───────────────────────────────────────────────

    @staticmethod
    def get_stats(group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get aggregated statistics for the dashboard."""
        from db.models import Conference, Paper, PaperStatus
        from sqlalchemy import func

        conf_query = Conference.query
        paper_query = db.session.query(Paper.status, func.count(Paper.id))
        upcoming_query = Conference.query

        if group_id:
            conf_query = conf_query.filter(Conference.group_id == group_id)
            paper_query = paper_query.filter(Paper.group_id == group_id)
            upcoming_query = upcoming_query.filter(Conference.group_id == group_id)

        total_conferences = conf_query.count()

        # Papers by status
        status_counts = paper_query.group_by(Paper.status).all()
        papers_by_status = {s.value: c for s, c in status_counts}

        # Upcoming deadlines (next 5)
        upcoming = (
            upcoming_query
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
