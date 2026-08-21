"""
Tests for worker_pool_statistics - statistics updates and session management.

Covers:
- Pillar statistics creation and updates
- Win/tie counting
- Running average confidence calculation
- Retry logic on IntegrityError
- Atomic progress increment
- Session completion detection
- Session total retrieval

Note: These functions use deferred imports (inside function body), so we
must patch at the import source (e.g. 'db.database.db') or use sys.modules.
"""

from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

import pytest


class TestUpdatePillarStatistics:
    """Test pillar statistics update logic."""

    def test_WPS_001_creates_new_stat_on_first_call(self):
        """WPS_001: Creates new PillarStatistics record when none exists."""
        mock_db = MagicMock()
        mock_ps = MagicMock()
        mock_ps.query.filter_by.return_value.first.return_value = None

        with patch.dict('sys.modules', {}):
            with patch('db.database.db', mock_db):
                with patch('db.tables.PillarStatistics', mock_ps):
                    from workers.pool.worker_pool_statistics import update_pillar_statistics

                    result = update_pillar_statistics(
                        session_id=1, worker_id=0,
                        pillar_a=10, pillar_b=20,
                        winner='A', confidence=0.9
                    )

        assert result is True
        mock_db.session.add.assert_called_once()

    def test_WPS_002_increments_wins_a(self):
        """WPS_002: Increments wins_a when winner is 'A'."""
        mock_db = MagicMock()
        stat = MagicMock()
        stat.wins_a = 2
        stat.wins_b = 1
        stat.ties = 0
        stat.avg_confidence = 0.8
        mock_ps = MagicMock()
        mock_ps.query.filter_by.return_value.first.return_value = stat

        with patch('db.database.db', mock_db):
            with patch('db.tables.PillarStatistics', mock_ps):
                from workers.pool.worker_pool_statistics import update_pillar_statistics

                result = update_pillar_statistics(
                    session_id=1, worker_id=0,
                    pillar_a=10, pillar_b=20,
                    winner='A', confidence=0.9
                )

        assert result is True
        assert stat.wins_a == 3

    def test_WPS_003_increments_wins_b(self):
        """WPS_003: Increments wins_b when winner is 'B'."""
        mock_db = MagicMock()
        stat = MagicMock()
        stat.wins_a = 0
        stat.wins_b = 0
        stat.ties = 0
        stat.avg_confidence = None
        mock_ps = MagicMock()
        mock_ps.query.filter_by.return_value.first.return_value = stat

        with patch('db.database.db', mock_db):
            with patch('db.tables.PillarStatistics', mock_ps):
                from workers.pool.worker_pool_statistics import update_pillar_statistics

                result = update_pillar_statistics(
                    session_id=1, worker_id=0,
                    pillar_a=10, pillar_b=20,
                    winner='B', confidence=0.7
                )

        assert result is True
        assert stat.wins_b == 1

    def test_WPS_004_increments_ties(self):
        """WPS_004: Increments ties when winner is 'TIE'."""
        mock_db = MagicMock()
        stat = MagicMock()
        stat.wins_a = 0
        stat.wins_b = 0
        stat.ties = 1
        stat.avg_confidence = 0.5
        mock_ps = MagicMock()
        mock_ps.query.filter_by.return_value.first.return_value = stat

        with patch('db.database.db', mock_db):
            with patch('db.tables.PillarStatistics', mock_ps):
                from workers.pool.worker_pool_statistics import update_pillar_statistics

                result = update_pillar_statistics(
                    session_id=1, worker_id=0,
                    pillar_a=10, pillar_b=20,
                    winner='TIE', confidence=0.6
                )

        assert result is True
        assert stat.ties == 2

    def test_WPS_005_sets_initial_avg_confidence(self):
        """WPS_005: Sets avg_confidence directly on first update."""
        mock_db = MagicMock()
        stat = MagicMock()
        stat.wins_a = 0
        stat.wins_b = 0
        stat.ties = 0
        stat.avg_confidence = None
        mock_ps = MagicMock()
        mock_ps.query.filter_by.return_value.first.return_value = stat

        with patch('db.database.db', mock_db):
            with patch('db.tables.PillarStatistics', mock_ps):
                from workers.pool.worker_pool_statistics import update_pillar_statistics

                update_pillar_statistics(
                    session_id=1, worker_id=0,
                    pillar_a=10, pillar_b=20,
                    winner='A', confidence=0.85
                )

        assert stat.avg_confidence == 0.85

    def test_WPS_006_calculates_running_avg_confidence(self):
        """WPS_006: Computes running average for subsequent updates."""
        mock_db = MagicMock()
        stat = MagicMock()
        stat.wins_a = 1
        stat.wins_b = 0
        stat.ties = 0
        stat.avg_confidence = 0.8
        mock_ps = MagicMock()
        mock_ps.query.filter_by.return_value.first.return_value = stat

        with patch('db.database.db', mock_db):
            with patch('db.tables.PillarStatistics', mock_ps):
                from workers.pool.worker_pool_statistics import update_pillar_statistics

                update_pillar_statistics(
                    session_id=1, worker_id=0,
                    pillar_a=10, pillar_b=20,
                    winner='A', confidence=1.0
                )

        # After increment: wins_a=2, total=2
        # avg = (0.8 * 1 + 1.0) / 2 = 0.9
        assert stat.avg_confidence == pytest.approx(0.9, abs=0.001)

    def test_WPS_007_retries_on_integrity_error(self):
        """WPS_007: Retries on IntegrityError from race condition."""
        from sqlalchemy.exc import IntegrityError

        mock_db = MagicMock()
        stat = MagicMock()
        stat.wins_a = 0
        stat.wins_b = 0
        stat.ties = 0
        stat.avg_confidence = None

        mock_ps = MagicMock()
        call_count = [0]

        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return None
            return stat

        mock_ps.query.filter_by.return_value.first.side_effect = side_effect

        flush_count = [0]

        def flush_side_effect():
            flush_count[0] += 1
            if flush_count[0] == 1:
                raise IntegrityError("dup", {}, None)

        mock_db.session.flush.side_effect = flush_side_effect

        with patch('db.database.db', mock_db):
            with patch('db.tables.PillarStatistics', mock_ps):
                from workers.pool.worker_pool_statistics import update_pillar_statistics

                result = update_pillar_statistics(
                    session_id=1, worker_id=0,
                    pillar_a=10, pillar_b=20,
                    winner='A', confidence=0.8
                )

        assert result is True
        mock_db.session.rollback.assert_called()


class TestAtomicIncrementProgress:
    """Test atomic progress increment."""

    def test_WPS_010_atomic_increment_returns_new_value(self):
        """WPS_010: Returns new completed_comparisons value."""
        mock_db = MagicMock()
        mock_db.session.execute.return_value.scalar.return_value = 5

        with patch('db.database.db', mock_db):
            from workers.pool.worker_pool_statistics import atomic_increment_progress
            result = atomic_increment_progress(session_id=1, worker_id=0)

        assert result == 5
        assert mock_db.session.execute.call_count == 2
        mock_db.session.commit.assert_called_once()

    def test_WPS_011_atomic_increment_returns_zero_on_error(self):
        """WPS_011: Returns 0 on database error."""
        mock_db = MagicMock()
        mock_db.session.execute.side_effect = RuntimeError("DB down")

        with patch('db.database.db', mock_db):
            from workers.pool.worker_pool_statistics import atomic_increment_progress
            result = atomic_increment_progress(session_id=1, worker_id=0)

        assert result == 0
        mock_db.session.rollback.assert_called_once()

    def test_WPS_012_atomic_increment_handles_none_scalar(self):
        """WPS_012: Returns 0 when scalar returns None."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.session.execute.return_value = mock_result

        with patch('db.database.db', mock_db):
            from workers.pool.worker_pool_statistics import atomic_increment_progress
            result = atomic_increment_progress(session_id=1, worker_id=0)

        assert result == 0


class TestTryCompleteSession:
    """Test session completion detection."""

    def test_WPS_020_returns_false_session_not_found(self):
        """WPS_020: Returns False when session not found."""
        mock_db = MagicMock()
        mock_db.session.get.return_value = None

        with patch('db.database.db', mock_db):
            with patch('db.tables.JudgeSession', MagicMock()):
                with patch('db.tables.JudgeSessionStatus', MagicMock()):
                    with patch('db.tables.JudgeComparison', MagicMock()):
                        with patch('db.tables.JudgeComparisonStatus', MagicMock()):
                            from workers.pool.worker_pool_statistics import try_complete_session
                            result = try_complete_session(session_id=999, worker_id=0)

        assert result is False

    def test_WPS_021_returns_false_when_still_pending(self):
        """WPS_021: Returns False when pending comparisons remain."""
        mock_db = MagicMock()
        mock_jss = MagicMock()
        mock_jc = MagicMock()

        mock_session = MagicMock()
        mock_session.status = mock_jss.RUNNING
        mock_db.session.get.return_value = mock_session

        mock_jc.query.filter_by.return_value.count.side_effect = [5, 0]

        with patch('db.database.db', mock_db):
            with patch('db.tables.JudgeSession', MagicMock()):
                with patch('db.tables.JudgeSessionStatus', mock_jss):
                    with patch('db.tables.JudgeComparison', mock_jc):
                        with patch('db.tables.JudgeComparisonStatus', MagicMock()):
                            from workers.pool.worker_pool_statistics import try_complete_session
                            result = try_complete_session(session_id=1, worker_id=0)

        assert result is False


class TestGetSessionTotal:
    """Test session total retrieval."""

    def test_WPS_030_returns_total_comparisons(self):
        """WPS_030: Returns total_comparisons from session."""
        mock_js = MagicMock()
        mock_session = MagicMock()
        mock_session.total_comparisons = 42
        mock_js.query.get.return_value = mock_session

        with patch('db.tables.JudgeSession', mock_js):
            from workers.pool.worker_pool_statistics import get_session_total
            assert get_session_total(session_id=1) == 42

    def test_WPS_031_returns_zero_for_missing_session(self):
        """WPS_031: Returns 0 when session not found."""
        mock_js = MagicMock()
        mock_js.query.get.return_value = None

        with patch('db.tables.JudgeSession', mock_js):
            from workers.pool.worker_pool_statistics import get_session_total
            assert get_session_total(session_id=999) == 0
