"""
Unit tests for ConferenceService and ConferenceSeriesService.

Tests conference CRUD, paper management, author management,
submission tracking, and statistics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestConferenceCRUD:
    """Tests for conference creation, retrieval, update, and deletion."""

    def test_CONF_001_create_conference(self, app, db, app_context):
        """[CONF-001] Should create a conference with all fields."""
        from services.conference_service import ConferenceService

        data = {
            'name': 'Neural Information Processing Systems',
            'acronym': 'NeurIPS',
            'year': 2026,
            'city': 'Vancouver',
            'country': 'Canada',
            'core_ranking': 'A*',
            'website_url': 'https://neurips.cc',
        }

        result = ConferenceService.create_conference(data, 'admin')

        assert result is not None
        assert result['name'] == 'Neural Information Processing Systems'
        assert result['acronym'] == 'NeurIPS'
        assert result['year'] == 2026
        assert result['city'] == 'Vancouver'
        assert result['core_ranking'] == 'A*'

    def test_CONF_002_create_conference_default_ranking(self, app, db, app_context):
        """[CONF-002] Should default to Unranked when no ranking specified."""
        from services.conference_service import ConferenceService

        data = {'name': 'Test Conf', 'acronym': 'TC', 'year': 2026}
        result = ConferenceService.create_conference(data, 'admin')

        assert result['core_ranking'] == 'Unranked'

    def test_CONF_003_create_conference_invalid_ranking(self, app, db, app_context):
        """[CONF-003] Should default to Unranked for invalid ranking value."""
        from services.conference_service import ConferenceService

        data = {'name': 'Invalid Rank', 'acronym': 'IR', 'year': 2026, 'core_ranking': 'X*'}
        result = ConferenceService.create_conference(data, 'admin')

        assert result['core_ranking'] == 'Unranked'

    def test_CONF_004_get_conference(self, app, db, app_context):
        """[CONF-004] Should retrieve a conference by ID."""
        from services.conference_service import ConferenceService

        data = {'name': 'Get Test', 'acronym': 'GT', 'year': 2026}
        created = ConferenceService.create_conference(data, 'admin')
        fetched = ConferenceService.get_conference(created['id'])

        assert fetched is not None
        assert fetched['id'] == created['id']
        assert fetched['name'] == 'Get Test'

    def test_CONF_005_get_conference_not_found(self, app, db, app_context):
        """[CONF-005] Should return None for non-existent conference."""
        from services.conference_service import ConferenceService

        result = ConferenceService.get_conference(99999)
        assert result is None

    def test_CONF_006_list_conferences(self, app, db, app_context):
        """[CONF-006] Should list all conferences."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {'name': 'Conf A', 'acronym': 'CA', 'year': 2026}, 'admin'
        )
        ConferenceService.create_conference(
            {'name': 'Conf B', 'acronym': 'CB', 'year': 2025}, 'admin'
        )

        results = ConferenceService.list_conferences()
        assert len(results) == 2

    def test_CONF_007_list_conferences_filter_year(self, app, db, app_context):
        """[CONF-007] Should filter conferences by year."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {'name': 'C 2025', 'acronym': 'C25', 'year': 2025}, 'admin'
        )
        ConferenceService.create_conference(
            {'name': 'C 2026', 'acronym': 'C26', 'year': 2026}, 'admin'
        )

        results = ConferenceService.list_conferences(year=2025)
        assert len(results) == 1
        assert results[0]['year'] == 2025

    def test_CONF_008_list_conferences_filter_ranking(self, app, db, app_context):
        """[CONF-008] Should filter conferences by CORE ranking."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {'name': 'A* Conf', 'acronym': 'AS', 'year': 2026, 'core_ranking': 'A*'}, 'admin'
        )
        ConferenceService.create_conference(
            {'name': 'B Conf', 'acronym': 'BC', 'year': 2026, 'core_ranking': 'B'}, 'admin'
        )

        results = ConferenceService.list_conferences(core_ranking='A*')
        assert len(results) == 1
        assert results[0]['core_ranking'] == 'A*'

    def test_CONF_009_list_conferences_search(self, app, db, app_context):
        """[CONF-009] Should search conferences by name or acronym."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {'name': 'Neural Information', 'acronym': 'NeurIPS', 'year': 2026}, 'admin'
        )
        ConferenceService.create_conference(
            {'name': 'Other Conf', 'acronym': 'OC', 'year': 2026}, 'admin'
        )

        results = ConferenceService.list_conferences(search='neural')
        assert len(results) == 1
        assert results[0]['acronym'] == 'NeurIPS'

    def test_CONF_010_update_conference(self, app, db, app_context):
        """[CONF-010] Should update conference fields."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_conference(
            {'name': 'Original', 'acronym': 'OR', 'year': 2026}, 'admin'
        )

        updated = ConferenceService.update_conference(
            created['id'],
            {'name': 'Updated Name', 'city': 'Berlin', 'country': 'Germany'},
            'admin',
        )

        assert updated is not None
        assert updated['name'] == 'Updated Name'
        assert updated['city'] == 'Berlin'
        assert updated['country'] == 'Germany'

    def test_CONF_011_update_conference_not_found(self, app, db, app_context):
        """[CONF-011] Should return None when updating non-existent conference."""
        from services.conference_service import ConferenceService

        result = ConferenceService.update_conference(99999, {'name': 'Nope'}, 'admin')
        assert result is None

    def test_CONF_012_delete_conference(self, app, db, app_context):
        """[CONF-012] Should delete a conference."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_conference(
            {'name': 'Delete Me', 'acronym': 'DM', 'year': 2026}, 'admin'
        )

        result = ConferenceService.delete_conference(created['id'])
        assert result is True

        fetched = ConferenceService.get_conference(created['id'])
        assert fetched is None

    def test_CONF_013_delete_conference_not_found(self, app, db, app_context):
        """[CONF-013] Should return False for non-existent conference deletion."""
        from services.conference_service import ConferenceService

        result = ConferenceService.delete_conference(99999)
        assert result is False


class TestPaperCRUD:
    """Tests for paper creation, retrieval, update, and deletion."""

    def test_CONF_014_create_paper(self, app, db, app_context):
        """[CONF-014] Should create a paper with all fields."""
        from services.conference_service import ConferenceService

        data = {
            'title': 'Attention Is All You Need',
            'status': 'planning',
            'description': 'Transformer architecture paper',
            'keywords': ['transformer', 'attention'],
        }

        result = ConferenceService.create_paper(data, 'researcher')

        assert result is not None
        assert result['title'] == 'Attention Is All You Need'
        assert result['status'] == 'planning'

    def test_CONF_015_create_paper_default_status(self, app, db, app_context):
        """[CONF-015] Should default to 'planning' status."""
        from services.conference_service import ConferenceService

        data = {'title': 'New Paper'}
        result = ConferenceService.create_paper(data, 'researcher')

        assert result['status'] == 'planning'

    def test_CONF_016_create_paper_with_conference(self, app, db, app_context):
        """[CONF-016] Should create a paper linked to a conference."""
        from services.conference_service import ConferenceService

        conf = ConferenceService.create_conference(
            {'name': 'Paper Conf', 'acronym': 'PC', 'year': 2026}, 'admin'
        )
        data = {'title': 'Linked Paper', 'conference_id': conf['id']}
        result = ConferenceService.create_paper(data, 'researcher')

        assert result['conference_id'] == conf['id']

    def test_CONF_017_get_paper(self, app, db, app_context):
        """[CONF-017] Should retrieve a paper by ID."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper({'title': 'Get Paper'}, 'researcher')
        fetched = ConferenceService.get_paper(created['id'])

        assert fetched is not None
        assert fetched['title'] == 'Get Paper'

    def test_CONF_018_get_paper_not_found(self, app, db, app_context):
        """[CONF-018] Should return None for non-existent paper."""
        from services.conference_service import ConferenceService

        result = ConferenceService.get_paper(99999)
        assert result is None

    def test_CONF_019_list_papers(self, app, db, app_context):
        """[CONF-019] Should list all papers."""
        from services.conference_service import ConferenceService

        ConferenceService.create_paper({'title': 'Paper 1'}, 'researcher')
        ConferenceService.create_paper({'title': 'Paper 2'}, 'researcher')

        results = ConferenceService.list_papers()
        assert len(results) == 2

    def test_CONF_020_list_papers_filter_status(self, app, db, app_context):
        """[CONF-020] Should filter papers by status."""
        from services.conference_service import ConferenceService

        ConferenceService.create_paper({'title': 'Planning', 'status': 'planning'}, 'r')
        ConferenceService.create_paper({'title': 'Submitted', 'status': 'submitted'}, 'r')

        results = ConferenceService.list_papers(status='submitted')
        assert len(results) == 1
        assert results[0]['status'] == 'submitted'

    def test_CONF_021_list_papers_search(self, app, db, app_context):
        """[CONF-021] Should search papers by title."""
        from services.conference_service import ConferenceService

        ConferenceService.create_paper({'title': 'Transformer Paper'}, 'r')
        ConferenceService.create_paper({'title': 'CNN Paper'}, 'r')

        results = ConferenceService.list_papers(search='transformer')
        assert len(results) == 1

    def test_CONF_022_update_paper(self, app, db, app_context):
        """[CONF-022] Should update paper fields."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper({'title': 'Original Title'}, 'researcher')

        updated = ConferenceService.update_paper(
            created['id'],
            {'title': 'Updated Title', 'status': 'in_progress'},
            'researcher',
        )

        assert updated is not None
        assert updated['title'] == 'Updated Title'
        assert updated['status'] == 'in_progress'

    def test_CONF_023_update_paper_not_found(self, app, db, app_context):
        """[CONF-023] Should return None for non-existent paper update."""
        from services.conference_service import ConferenceService

        result = ConferenceService.update_paper(99999, {'title': 'Nope'}, 'researcher')
        assert result is None

    def test_CONF_024_update_paper_status(self, app, db, app_context):
        """[CONF-024] Should update paper status for Kanban drag-and-drop."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper({'title': 'Status Paper'}, 'researcher')
        result = ConferenceService.update_paper_status(created['id'], 'submitted', 'researcher')

        assert result is not None
        assert result['status'] == 'submitted'

    def test_CONF_025_update_paper_status_invalid(self, app, db, app_context):
        """[CONF-025] Should return None for invalid status value."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper({'title': 'Invalid Status'}, 'researcher')
        result = ConferenceService.update_paper_status(created['id'], 'invalid_status', 'researcher')

        assert result is None

    def test_CONF_026_delete_paper(self, app, db, app_context):
        """[CONF-026] Should delete a paper."""
        from services.conference_service import ConferenceService

        created = ConferenceService.create_paper({'title': 'Delete Paper'}, 'researcher')
        result = ConferenceService.delete_paper(created['id'])
        assert result is True

        fetched = ConferenceService.get_paper(created['id'])
        assert fetched is None

    def test_CONF_027_delete_paper_not_found(self, app, db, app_context):
        """[CONF-027] Should return False for non-existent paper deletion."""
        from services.conference_service import ConferenceService

        result = ConferenceService.delete_paper(99999)
        assert result is False


class TestPaperAuthors:
    """Tests for paper author management."""

    def test_CONF_028_set_paper_authors(self, app, db, app_context):
        """[CONF-028] Should set authors for a paper."""
        from services.conference_service import ConferenceService

        paper = ConferenceService.create_paper({'title': 'Author Test'}, 'researcher')
        authors = [
            {'external_name': 'Alice Smith', 'author_order': 0, 'is_corresponding': True},
            {'external_name': 'Bob Jones', 'author_order': 1, 'is_corresponding': False},
        ]

        result = ConferenceService.set_paper_authors(paper['id'], authors, 'researcher')

        assert len(result) == 2
        assert result[0]['external_name'] == 'Alice Smith'
        assert result[0]['is_corresponding'] is True
        assert result[1]['external_name'] == 'Bob Jones'

    def test_CONF_029_set_paper_authors_replaces_existing(self, app, db, app_context):
        """[CONF-029] Should replace all existing authors."""
        from services.conference_service import ConferenceService

        paper = ConferenceService.create_paper({'title': 'Replace Authors'}, 'r')
        ConferenceService.set_paper_authors(
            paper['id'], [{'external_name': 'Old Author', 'author_order': 0}], 'r'
        )

        result = ConferenceService.set_paper_authors(
            paper['id'], [{'external_name': 'New Author', 'author_order': 0}], 'r'
        )

        assert len(result) == 1
        assert result[0]['external_name'] == 'New Author'

    def test_CONF_030_set_paper_authors_not_found(self, app, db, app_context):
        """[CONF-030] Should return empty list for non-existent paper."""
        from services.conference_service import ConferenceService

        result = ConferenceService.set_paper_authors(99999, [], 'r')
        assert result == []

    def test_CONF_031_create_paper_with_authors(self, app, db, app_context):
        """[CONF-031] Should create a paper with authors in one call."""
        from services.conference_service import ConferenceService

        data = {
            'title': 'Paper With Authors',
            'authors': [
                {'external_name': 'Author A', 'author_order': 0},
                {'external_name': 'Author B', 'author_order': 1},
            ],
        }

        result = ConferenceService.create_paper(data, 'researcher')
        assert result is not None
        assert len(result['authors']) == 2


class TestConferenceStats:
    """Tests for conference statistics."""

    def test_CONF_032_get_stats(self, app, db, app_context):
        """[CONF-032] Should return aggregated statistics."""
        from services.conference_service import ConferenceService

        ConferenceService.create_conference(
            {'name': 'Stats Conf', 'acronym': 'SC', 'year': 2026}, 'admin'
        )
        ConferenceService.create_paper({'title': 'Stats Paper 1', 'status': 'planning'}, 'r')
        ConferenceService.create_paper({'title': 'Stats Paper 2', 'status': 'submitted'}, 'r')

        stats = ConferenceService.get_stats()

        assert stats['total_conferences'] >= 1
        assert stats['total_papers'] >= 2
        assert 'papers_by_status' in stats
        assert 'upcoming_deadlines' in stats

    def test_CONF_033_get_stats_with_group_filter(self, app, db, app_context):
        """[CONF-033] Should filter stats by group_id."""
        from services.conference_service import ConferenceService

        # Create conferences without group
        ConferenceService.create_conference(
            {'name': 'No Group', 'acronym': 'NG', 'year': 2026}, 'admin'
        )

        stats = ConferenceService.get_stats(group_id=99999)
        assert stats['total_conferences'] == 0


class TestConferenceSeriesService:
    """Tests for ConferenceSeriesService."""

    def test_CONF_034_create_series(self, app, db, app_context):
        """[CONF-034] Should create a conference series."""
        from services.conference_service import ConferenceSeriesService

        data = {
            'name': 'Neural Information Processing Systems',
            'acronym': 'NeurIPS',
            'core_ranking': 'A*',
        }
        result = ConferenceSeriesService.create_series(data, 'admin')

        assert result is not None
        assert result['name'] == 'Neural Information Processing Systems'
        assert result['acronym'] == 'NeurIPS'

    def test_CONF_035_get_series(self, app, db, app_context):
        """[CONF-035] Should retrieve a series by ID."""
        from services.conference_service import ConferenceSeriesService

        created = ConferenceSeriesService.create_series(
            {'name': 'Get Series', 'acronym': 'GS'}, 'admin'
        )
        fetched = ConferenceSeriesService.get_series(created['id'])

        assert fetched is not None
        assert fetched['id'] == created['id']

    def test_CONF_036_get_series_not_found(self, app, db, app_context):
        """[CONF-036] Should return None for non-existent series."""
        from services.conference_service import ConferenceSeriesService

        result = ConferenceSeriesService.get_series(99999)
        assert result is None

    def test_CONF_037_list_series(self, app, db, app_context):
        """[CONF-037] Should list all conference series."""
        from services.conference_service import ConferenceSeriesService

        ConferenceSeriesService.create_series({'name': 'Series A', 'acronym': 'SA'}, 'admin')
        ConferenceSeriesService.create_series({'name': 'Series B', 'acronym': 'SB'}, 'admin')

        results = ConferenceSeriesService.list_series()
        assert len(results) >= 2

    def test_CONF_038_list_series_search(self, app, db, app_context):
        """[CONF-038] Should search series by name or acronym."""
        from services.conference_service import ConferenceSeriesService

        ConferenceSeriesService.create_series({'name': 'Findable Series', 'acronym': 'FS'}, 'admin')
        ConferenceSeriesService.create_series({'name': 'Other', 'acronym': 'OT'}, 'admin')

        results = ConferenceSeriesService.list_series(search='findable')
        assert len(results) == 1

    def test_CONF_039_update_series(self, app, db, app_context):
        """[CONF-039] Should update series fields."""
        from services.conference_service import ConferenceSeriesService

        created = ConferenceSeriesService.create_series(
            {'name': 'Original Series', 'acronym': 'OS'}, 'admin'
        )
        updated = ConferenceSeriesService.update_series(
            created['id'], {'name': 'Updated Series'}, 'admin'
        )

        assert updated is not None
        assert updated['name'] == 'Updated Series'

    def test_CONF_040_update_series_not_found(self, app, db, app_context):
        """[CONF-040] Should return None for non-existent series update."""
        from services.conference_service import ConferenceSeriesService

        result = ConferenceSeriesService.update_series(99999, {'name': 'Nope'}, 'admin')
        assert result is None

    def test_CONF_041_delete_series(self, app, db, app_context):
        """[CONF-041] Should delete a series."""
        from services.conference_service import ConferenceSeriesService

        created = ConferenceSeriesService.create_series(
            {'name': 'Delete Series', 'acronym': 'DS'}, 'admin'
        )
        result = ConferenceSeriesService.delete_series(created['id'])
        assert result is True

    def test_CONF_042_delete_series_not_found(self, app, db, app_context):
        """[CONF-042] Should return False for non-existent series."""
        from services.conference_service import ConferenceSeriesService

        result = ConferenceSeriesService.delete_series(99999)
        assert result is False

    def test_CONF_043_find_series_by_acronym(self, app, db, app_context):
        """[CONF-043] Should find series by acronym (case-insensitive)."""
        from services.conference_service import ConferenceSeriesService

        ConferenceSeriesService.create_series({'name': 'AAAI Conference', 'acronym': 'AAAI'}, 'admin')

        result = ConferenceSeriesService.find_series_by_acronym('aaai')
        assert result is not None
        assert result['acronym'] == 'AAAI'

    def test_CONF_044_get_new_edition_defaults(self, app, db, app_context):
        """[CONF-044] Should provide defaults for a new edition based on series."""
        from services.conference_service import ConferenceSeriesService, ConferenceService

        series = ConferenceSeriesService.create_series(
            {'name': 'Defaults Test', 'acronym': 'DT', 'core_ranking': 'A'}, 'admin'
        )
        ConferenceService.create_conference(
            {'name': 'DT 2025', 'acronym': 'DT', 'year': 2025, 'series_id': series['id'],
             'city': 'Munich', 'country': 'Germany'},
            'admin',
        )

        defaults = ConferenceSeriesService.get_new_edition_defaults(series['id'])
        assert defaults is not None
        assert defaults['year'] == 2026
        assert defaults['city'] == 'Munich'
        assert defaults['country'] == 'Germany'


class TestParseDatetime:
    """Tests for the _parse_datetime helper."""

    def test_CONF_045_parse_datetime_none(self, app, db, app_context):
        """[CONF-045] Should return None for None input."""
        from services.conference_service import _parse_datetime

        assert _parse_datetime(None) is None
        assert _parse_datetime('') is None

    def test_CONF_046_parse_datetime_iso_string(self, app, db, app_context):
        """[CONF-046] Should parse ISO format datetime strings."""
        from services.conference_service import _parse_datetime

        result = _parse_datetime('2026-06-15T10:00:00')
        assert result is not None
        assert result.year == 2026
        assert result.month == 6

    def test_CONF_047_parse_datetime_with_z(self, app, db, app_context):
        """[CONF-047] Should handle Z suffix in datetime strings."""
        from services.conference_service import _parse_datetime

        result = _parse_datetime('2026-06-15T10:00:00Z')
        assert result is not None

    def test_CONF_048_parse_datetime_object(self, app, db, app_context):
        """[CONF-048] Should return datetime objects as-is."""
        from services.conference_service import _parse_datetime

        dt = datetime(2026, 6, 15)
        result = _parse_datetime(dt)
        assert result is dt

    def test_CONF_049_parse_datetime_invalid(self, app, db, app_context):
        """[CONF-049] Should return None for invalid datetime strings."""
        from services.conference_service import _parse_datetime

        assert _parse_datetime('not-a-date') is None
        assert _parse_datetime(12345) is None
