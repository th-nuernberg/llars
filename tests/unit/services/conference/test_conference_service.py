"""
Unit Tests: Conference Service
==============================

Tests for the conference and paper management service.

Test IDs:
- CONF-001 to CONF-010: Conference CRUD
- CONF-020 to CONF-030: Paper CRUD
- CONF-040 to CONF-050: Author Management
- CONF-060 to CONF-070: Filters and Search
- CONF-080 to CONF-090: Statistics

Status: Implemented
"""

import pytest
from datetime import datetime, timedelta


class TestConferenceCRUD:
    """Conference CRUD Tests."""

    def test_CONF_001_create_conference(self, app, db, app_context):
        """[CONF-001] Create conference with required fields."""
        from services.conference_service import ConferenceService

        data = {
            "name": "International Joint Conference on AI",
            "acronym": "IJCAI",
            "year": 2026,
            "core_ranking": "A*",
        }
        result = ConferenceService.create_conference(data, "researcher")

        assert result["name"] == "International Joint Conference on AI"
        assert result["acronym"] == "IJCAI"
        assert result["year"] == 2026
        assert result["core_ranking"] == "A*"
        assert result["created_by"] == "researcher"
        assert result["id"] is not None

    def test_CONF_002_create_conference_with_dates(self, app, db, app_context):
        """[CONF-002] Create conference with all date fields."""
        from services.conference_service import ConferenceService

        data = {
            "name": "NeurIPS",
            "acronym": "NeurIPS",
            "year": 2026,
            "submission_deadline": "2026-05-15T23:59:00",
            "notification_date": "2026-08-01T00:00:00",
            "start_date": "2026-12-01T00:00:00",
            "end_date": "2026-12-05T00:00:00",
            "city": "Vancouver",
            "country": "Canada",
            "website_url": "https://neurips.cc",
        }
        result = ConferenceService.create_conference(data, "researcher")

        assert result["submission_deadline"] is not None
        assert result["city"] == "Vancouver"
        assert result["country"] == "Canada"

    def test_CONF_003_get_conference(self, app, db, app_context):
        """[CONF-003] Get conference by ID."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_conference(
            {"name": "AAAI", "acronym": "AAAI", "year": 2026}, "researcher"
        )
        result = ConferenceService.get_conference(created["id"])

        assert result is not None
        assert result["acronym"] == "AAAI"

    def test_CONF_004_get_conference_not_found(self, app, db, app_context):
        """[CONF-004] Get non-existent conference returns None."""
        from services.conference_service import ConferenceService

        result = ConferenceService.get_conference(99999)
        assert result is None

    def test_CONF_005_update_conference(self, app, db, app_context):
        """[CONF-005] Update conference fields."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_conference(
            {"name": "AAAI", "acronym": "AAAI", "year": 2026}, "researcher"
        )
        result = ConferenceService.update_conference(
            created["id"],
            {"name": "AAAI Conference", "core_ranking": "A*", "city": "Philadelphia"},
            "admin",
        )

        assert result["name"] == "AAAI Conference"
        assert result["core_ranking"] == "A*"
        assert result["city"] == "Philadelphia"
        assert result["updated_by"] == "admin"

    def test_CONF_006_update_conference_not_found(self, app, db, app_context):
        """[CONF-006] Update non-existent conference returns None."""
        from services.conference_service import ConferenceService

        result = ConferenceService.update_conference(99999, {"name": "Test"}, "admin")
        assert result is None

    def test_CONF_007_delete_conference(self, app, db, app_context):
        """[CONF-007] Delete conference."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_conference(
            {"name": "AAAI", "acronym": "AAAI", "year": 2026}, "researcher"
        )
        deleted = ConferenceService.delete_conference(created["id"])
        assert deleted is True
        assert ConferenceService.get_conference(created["id"]) is None

    def test_CONF_008_delete_conference_not_found(self, app, db, app_context):
        """[CONF-008] Delete non-existent conference returns False."""
        from services.conference_service import ConferenceService

        deleted = ConferenceService.delete_conference(99999)
        assert deleted is False

    def test_CONF_009_list_conferences(self, app, db, app_context):
        """[CONF-009] List all conferences."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {"name": "IJCAI", "acronym": "IJCAI", "year": 2026}, "researcher"
        )
        ConferenceService.create_conference(
            {"name": "NeurIPS", "acronym": "NeurIPS", "year": 2026}, "researcher"
        )

        result = ConferenceService.list_conferences()
        assert len(result) == 2

    def test_CONF_010_conference_default_ranking(self, app, db, app_context):
        """[CONF-010] Conference defaults to Unranked."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_conference(
            {"name": "Local Workshop", "acronym": "LW", "year": 2026}, "researcher"
        )
        assert created["core_ranking"] == "Unranked"


class TestPaperCRUD:
    """Paper CRUD Tests."""

    def test_CONF_020_create_paper(self, app, db, app_context):
        """[CONF-020] Create paper with required fields."""
        from services.conference_service import ConferenceService

        result = ConferenceService.create_paper(
            {"title": "Evaluating LLMs for Email Summarization"}, "researcher"
        )

        assert result["title"] == "Evaluating LLMs for Email Summarization"
        assert result["status"] == "planning"
        assert result["created_by"] == "researcher"
        assert result["id"] is not None

    def test_CONF_021_create_paper_with_conference(self, app, db, app_context):
        """[CONF-021] Create paper linked to a conference."""
        from services.conference_service import ConferenceService

        conf = ConferenceService.create_conference(
            {"name": "IJCAI", "acronym": "IJCAI", "year": 2026}, "researcher"
        )
        paper = ConferenceService.create_paper(
            {"title": "My Paper", "conference_id": conf["id"], "status": "in_progress"},
            "researcher",
        )

        assert paper["conference_id"] == conf["id"]
        assert paper["conference"]["acronym"] == "IJCAI"
        assert paper["status"] == "in_progress"

    def test_CONF_022_get_paper(self, app, db, app_context):
        """[CONF-022] Get paper by ID."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper(
            {"title": "Test Paper"}, "researcher"
        )
        result = ConferenceService.get_paper(created["id"])
        assert result is not None
        assert result["title"] == "Test Paper"

    def test_CONF_023_update_paper(self, app, db, app_context):
        """[CONF-023] Update paper fields."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper(
            {"title": "Draft Paper"}, "researcher"
        )
        result = ConferenceService.update_paper(
            created["id"],
            {"title": "Final Paper", "status": "submitted"},
            "researcher",
        )

        assert result["title"] == "Final Paper"
        assert result["status"] == "submitted"

    def test_CONF_024_update_paper_status(self, app, db, app_context):
        """[CONF-024] Lightweight status update (Kanban)."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper(
            {"title": "My Paper"}, "researcher"
        )
        result = ConferenceService.update_paper_status(
            created["id"], "accepted", "researcher"
        )

        assert result["status"] == "accepted"

    def test_CONF_025_update_paper_status_invalid(self, app, db, app_context):
        """[CONF-025] Invalid status returns None."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper(
            {"title": "My Paper"}, "researcher"
        )
        result = ConferenceService.update_paper_status(
            created["id"], "invalid_status", "researcher"
        )
        assert result is None

    def test_CONF_026_delete_paper(self, app, db, app_context):
        """[CONF-026] Delete paper."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper(
            {"title": "To Delete"}, "researcher"
        )
        deleted = ConferenceService.delete_paper(created["id"])
        assert deleted is True
        assert ConferenceService.get_paper(created["id"]) is None

    def test_CONF_027_delete_conference_keeps_papers(self, app, db, app_context):
        """[CONF-027] Deleting conference sets paper.conference_id to NULL."""
        from services.conference_service import ConferenceService

        conf = ConferenceService.create_conference(
            {"name": "IJCAI", "acronym": "IJCAI", "year": 2026}, "researcher"
        )
        paper = ConferenceService.create_paper(
            {"title": "My Paper", "conference_id": conf["id"]}, "researcher"
        )

        ConferenceService.delete_conference(conf["id"])

        updated_paper = ConferenceService.get_paper(paper["id"])
        assert updated_paper is not None
        assert updated_paper["conference_id"] is None


class TestAuthorManagement:
    """Author management tests."""

    def test_CONF_040_set_paper_authors(self, app, db, app_context):
        """[CONF-040] Set authors on a paper."""
        from services.conference_service import ConferenceService

        paper = ConferenceService.create_paper(
            {"title": "Authored Paper"}, "researcher"
        )
        authors = ConferenceService.set_paper_authors(
            paper["id"],
            [
                {"external_name": "Alice Smith", "author_order": 0, "is_corresponding": True},
                {"external_name": "Bob Jones", "author_order": 1, "is_corresponding": False},
            ],
            "researcher",
        )

        assert len(authors) == 2
        assert authors[0]["external_name"] == "Alice Smith"
        assert authors[0]["is_corresponding"] is True
        assert authors[1]["external_name"] == "Bob Jones"

    def test_CONF_041_replace_paper_authors(self, app, db, app_context):
        """[CONF-041] Replacing authors removes old ones."""
        from services.conference_service import ConferenceService

        paper = ConferenceService.create_paper(
            {"title": "Authored Paper"}, "researcher"
        )
        ConferenceService.set_paper_authors(
            paper["id"],
            [{"external_name": "Alice", "author_order": 0}],
            "researcher",
        )
        authors = ConferenceService.set_paper_authors(
            paper["id"],
            [{"external_name": "Charlie", "author_order": 0}],
            "researcher",
        )

        assert len(authors) == 1
        assert authors[0]["external_name"] == "Charlie"

    def test_CONF_042_create_paper_with_authors(self, app, db, app_context):
        """[CONF-042] Create paper with authors in one call."""
        from services.conference_service import ConferenceService

        paper = ConferenceService.create_paper(
            {
                "title": "Co-authored Paper",
                "authors": [
                    {"external_name": "Author 1", "author_order": 0},
                    {"external_name": "Author 2", "author_order": 1},
                ],
            },
            "researcher",
        )

        assert len(paper["authors"]) == 2


class TestFiltersAndSearch:
    """Filter and search tests."""

    def test_CONF_060_filter_conferences_by_year(self, app, db, app_context):
        """[CONF-060] Filter conferences by year."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {"name": "A", "acronym": "A", "year": 2025}, "researcher"
        )
        ConferenceService.create_conference(
            {"name": "B", "acronym": "B", "year": 2026}, "researcher"
        )

        result = ConferenceService.list_conferences(year=2026)
        assert len(result) == 1
        assert result[0]["year"] == 2026

    def test_CONF_061_filter_conferences_by_ranking(self, app, db, app_context):
        """[CONF-061] Filter conferences by CORE ranking."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {"name": "Top", "acronym": "T", "year": 2026, "core_ranking": "A*"}, "researcher"
        )
        ConferenceService.create_conference(
            {"name": "Mid", "acronym": "M", "year": 2026, "core_ranking": "B"}, "researcher"
        )

        result = ConferenceService.list_conferences(core_ranking="A*")
        assert len(result) == 1
        assert result[0]["core_ranking"] == "A*"

    def test_CONF_062_search_conferences(self, app, db, app_context):
        """[CONF-062] Search conferences by name/acronym."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {"name": "Neural Info Processing", "acronym": "NeurIPS", "year": 2026}, "researcher"
        )
        ConferenceService.create_conference(
            {"name": "AAAI Conference", "acronym": "AAAI", "year": 2026}, "researcher"
        )

        result = ConferenceService.list_conferences(search="neur")
        assert len(result) == 1
        assert result[0]["acronym"] == "NeurIPS"

    def test_CONF_063_filter_papers_by_status(self, app, db, app_context):
        """[CONF-063] Filter papers by status."""
        from services.conference_service import ConferenceService

        ConferenceService.create_paper(
            {"title": "Planning Paper", "status": "planning"}, "researcher"
        )
        ConferenceService.create_paper(
            {"title": "Submitted Paper", "status": "submitted"}, "researcher"
        )

        result = ConferenceService.list_papers(status="submitted")
        assert len(result) == 1
        assert result[0]["title"] == "Submitted Paper"

    def test_CONF_064_filter_papers_by_conference(self, app, db, app_context):
        """[CONF-064] Filter papers by conference."""
        from services.conference_service import ConferenceService

        conf = ConferenceService.create_conference(
            {"name": "IJCAI", "acronym": "IJCAI", "year": 2026}, "researcher"
        )
        ConferenceService.create_paper(
            {"title": "IJCAI Paper", "conference_id": conf["id"]}, "researcher"
        )
        ConferenceService.create_paper(
            {"title": "Unlinked Paper"}, "researcher"
        )

        result = ConferenceService.list_papers(conference_id=conf["id"])
        assert len(result) == 1
        assert result[0]["title"] == "IJCAI Paper"


class TestStatistics:
    """Statistics tests."""

    def test_CONF_080_get_stats_empty(self, app, db, app_context):
        """[CONF-080] Stats on empty database."""
        from services.conference_service import ConferenceService

        stats = ConferenceService.get_stats()
        assert stats["total_conferences"] == 0
        assert stats["total_papers"] == 0

    def test_CONF_081_get_stats_with_data(self, app, db, app_context):
        """[CONF-081] Stats with conferences and papers."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {
                "name": "IJCAI",
                "acronym": "IJCAI",
                "year": 2026,
                "submission_deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            },
            "researcher",
        )
        ConferenceService.create_paper(
            {"title": "Paper 1", "status": "planning"}, "researcher"
        )
        ConferenceService.create_paper(
            {"title": "Paper 2", "status": "submitted"}, "researcher"
        )

        stats = ConferenceService.get_stats()
        assert stats["total_conferences"] == 1
        assert stats["total_papers"] == 2
        assert "planning" in stats["papers_by_status"]
        assert "submitted" in stats["papers_by_status"]
        assert len(stats["upcoming_deadlines"]) == 1
