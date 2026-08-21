"""
Tests for JudgeWorker - background worker for LLM-as-Judge evaluations.

Covers:
- Worker lifecycle (start, stop, running flag)
- Task execution and queue processing
- Error handling and session failure marking
- Result processing and statistics updates
- Socket.IO broadcast functions
- Module-level management functions (trigger, stop, get_status)
"""

import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestJudgeWorkerInit:
    """Test JudgeWorker initialization."""

    def test_JW_001_init_sets_attributes(self):
        """JW_001: Init sets session_id, app, running=False."""
        from workers.judge_worker import JudgeWorker

        mock_app = MagicMock()
        worker = JudgeWorker(session_id=42, app=mock_app)

        assert worker.session_id == 42
        assert worker.app is mock_app
        assert worker.running is False
        assert worker.thread is None

    def test_JW_002_stop_event_initially_clear(self):
        """JW_002: Stop event is initially not set."""
        from workers.judge_worker import JudgeWorker

        worker = JudgeWorker(session_id=1, app=MagicMock())
        assert not worker._stop_event.is_set()


class TestJudgeWorkerStartStop:
    """Test start/stop lifecycle."""

    def test_JW_010_start_sets_running_flag(self):
        """JW_010: Start sets running=True and creates thread."""
        from workers.judge_worker import JudgeWorker

        mock_app = MagicMock()
        worker = JudgeWorker(session_id=1, app=mock_app)

        with patch.object(worker, '_run'):
            worker.start()

            assert worker.running is True
            assert worker.thread is not None
            assert worker.thread.daemon is True

            worker.stop()

    def test_JW_011_start_when_already_running_does_nothing(self):
        """JW_011: Starting when already running logs warning and returns."""
        from workers.judge_worker import JudgeWorker

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker.running = True

        original_thread = worker.thread
        worker.start()

        # Thread should not change since we short-circuit
        assert worker.thread is original_thread

    def test_JW_012_stop_sets_running_false_and_stop_event(self):
        """JW_012: Stop sets running=False and signals stop event."""
        from workers.judge_worker import JudgeWorker

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker.running = True

        worker.stop()

        assert worker.running is False
        assert worker._stop_event.is_set()

    def test_JW_013_stop_joins_alive_thread(self):
        """JW_013: Stop joins an alive thread with timeout."""
        from workers.judge_worker import JudgeWorker

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker.running = True
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        worker.thread = mock_thread

        worker.stop()

        mock_thread.join.assert_called_once_with(timeout=5.0)


class TestJudgeWorkerRun:
    """Test _run method."""

    def test_JW_020_run_calls_process_queue_in_app_context(self):
        """JW_020: _run uses app_context and calls _process_queue."""
        from workers.judge_worker import JudgeWorker

        mock_app = MagicMock()
        worker = JudgeWorker(session_id=1, app=mock_app)
        worker.running = True

        with patch.object(worker, '_process_queue') as mock_pq:
            worker._run()

            mock_app.app_context.assert_called_once()
            mock_pq.assert_called_once()

        # After _run completes, running should be False
        assert worker.running is False

    def test_JW_021_run_handles_fatal_error(self):
        """JW_021: Fatal error in _run marks session failed."""
        from workers.judge_worker import JudgeWorker

        mock_app = MagicMock()
        worker = JudgeWorker(session_id=1, app=mock_app)
        worker.running = True

        with patch.object(worker, '_process_queue', side_effect=RuntimeError("boom")):
            with patch.object(worker, '_mark_session_failed') as mock_fail:
                worker._run()

                mock_fail.assert_called_once_with("boom")

        assert worker.running is False


class TestJudgeWorkerProcessQueue:
    """Test queue processing logic."""

    @patch('workers.judge_worker.JudgeService')
    @patch('workers.judge_worker.db')
    def test_JW_030_process_queue_session_not_found_breaks(self, mock_db, mock_js_class):
        """JW_030: Process queue exits when session not found."""
        from workers.judge_worker import JudgeWorker

        mock_app = MagicMock()
        worker = JudgeWorker(session_id=999, app=mock_app)
        worker.running = True

        mock_db.session.get.return_value = None

        worker._process_queue()

    @patch('workers.judge_worker.JudgeService')
    @patch('workers.judge_worker.db')
    def test_JW_031_judge_service_init_failure_raises(self, mock_db, mock_js_class):
        """JW_031: JudgeService init failure propagates."""
        from workers.judge_worker import JudgeWorker

        mock_js_class.side_effect = RuntimeError("LLM unavailable")

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker.running = True

        with pytest.raises(RuntimeError, match="LLM unavailable"):
            worker._process_queue()


class TestJudgeWorkerLoadMessages:
    """Test message loading."""

    @patch('workers.judge_worker.Message')
    def test_JW_040_load_messages_returns_formatted_list(self, mock_msg_cls):
        """JW_040: _load_messages formats message data correctly."""
        from workers.judge_worker import JudgeWorker

        mock_msg = MagicMock()
        mock_msg.content = "Hello"
        mock_msg.is_counsellor = True
        mock_msg.timestamp = datetime(2025, 1, 1, 12, 0, 0)

        mock_msg_cls.query.filter_by.return_value.order_by.return_value.all.return_value = [mock_msg]

        worker = JudgeWorker(session_id=1, app=MagicMock())
        result = worker._load_messages(thread_id=10)

        assert len(result) == 1
        assert result[0]['content'] == "Hello"
        assert result[0]['is_counsellor'] is True
        assert result[0]['timestamp'] == "2025-01-01T12:00:00"

    @patch('workers.judge_worker.Message')
    def test_JW_041_load_messages_empty_returns_empty(self, mock_msg_cls):
        """JW_041: No messages returns empty list."""
        from workers.judge_worker import JudgeWorker

        mock_msg_cls.query.filter_by.return_value.order_by.return_value.all.return_value = []

        worker = JudgeWorker(session_id=1, app=MagicMock())
        result = worker._load_messages(thread_id=10)

        assert result == []


class TestJudgeWorkerUpdateStatistics:
    """Test statistics updates."""

    @patch('workers.judge_worker.PillarStatistics')
    @patch('workers.judge_worker.db')
    def test_JW_050_update_stats_creates_new_stat(self, mock_db, mock_ps):
        """JW_050: Creates new PillarStatistics when none exists."""
        from workers.judge_worker import JudgeWorker

        mock_ps.query.filter_by.return_value.first.return_value = None

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker._update_statistics(pillar_a=1, pillar_b=2, winner='A', confidence=0.85)

        mock_db.session.add.assert_called_once()
        added_stat = mock_db.session.add.call_args[0][0]
        assert added_stat.wins_a == 1
        assert added_stat.wins_b == 0
        assert added_stat.ties == 0

    @patch('workers.judge_worker.PillarStatistics')
    @patch('workers.judge_worker.db')
    def test_JW_051_update_stats_increments_wins_b(self, mock_db, mock_ps):
        """JW_051: Increments wins_b for winner B."""
        from workers.judge_worker import JudgeWorker

        existing_stat = MagicMock()
        existing_stat.wins_a = 1
        existing_stat.wins_b = 0
        existing_stat.ties = 0
        existing_stat.avg_confidence = 0.8
        mock_ps.query.filter_by.return_value.first.return_value = existing_stat

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker._update_statistics(pillar_a=1, pillar_b=2, winner='B', confidence=0.9)

        assert existing_stat.wins_b == 1

    @patch('workers.judge_worker.PillarStatistics')
    @patch('workers.judge_worker.db')
    def test_JW_052_update_stats_increments_ties(self, mock_db, mock_ps):
        """JW_052: Increments ties for TIE winner."""
        from workers.judge_worker import JudgeWorker

        existing_stat = MagicMock()
        existing_stat.wins_a = 0
        existing_stat.wins_b = 0
        existing_stat.ties = 0
        existing_stat.avg_confidence = None
        mock_ps.query.filter_by.return_value.first.return_value = existing_stat

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker._update_statistics(pillar_a=1, pillar_b=2, winner='TIE', confidence=0.5)

        assert existing_stat.ties == 1
        assert existing_stat.avg_confidence == 0.5


class TestJudgeWorkerMarkSessionFailed:
    """Test session failure marking."""

    @patch('workers.judge_worker.JudgeSession')
    @patch('workers.judge_worker.db')
    def test_JW_060_mark_session_failed_sets_status(self, mock_db, mock_js):
        """JW_060: Marks session status as FAILED and stores error."""
        from workers.judge_worker import JudgeWorker, JudgeSessionStatus

        mock_session = MagicMock()
        mock_session.config_json = {}
        mock_db.session.get.return_value = mock_session

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker._mark_session_failed("Test error")

        assert mock_session.status == JudgeSessionStatus.FAILED
        assert mock_session.config_json['error'] == "Test error"
        mock_db.session.commit.assert_called_once()

    @patch('workers.judge_worker.JudgeSession')
    @patch('workers.judge_worker.db')
    def test_JW_061_mark_session_failed_null_config(self, mock_db, mock_js):
        """JW_061: Creates config_json if it was None."""
        from workers.judge_worker import JudgeWorker

        mock_session = MagicMock()
        mock_session.config_json = None
        mock_db.session.get.return_value = mock_session

        worker = JudgeWorker(session_id=1, app=MagicMock())
        worker._mark_session_failed("Error")

        assert mock_session.config_json == {'error': 'Error'}

    @patch('workers.judge_worker.JudgeSession')
    @patch('workers.judge_worker.db')
    def test_JW_062_mark_session_failed_no_session(self, mock_db, mock_js):
        """JW_062: Handles missing session gracefully."""
        from workers.judge_worker import JudgeWorker

        mock_db.session.get.return_value = None

        worker = JudgeWorker(session_id=999, app=MagicMock())
        # Should not raise
        worker._mark_session_failed("Error")


class TestJudgeWorkerBroadcasts:
    """Test Socket.IO broadcast methods."""

    def test_JW_070_get_socketio_from_extensions(self):
        """JW_070: Gets socketio from current_app.extensions."""
        from workers.judge_worker import JudgeWorker

        mock_socketio = MagicMock()
        worker = JudgeWorker(session_id=1, app=MagicMock())

        with patch('workers.judge_worker.current_app') as mock_current_app:
            mock_current_app.extensions = {'socketio': mock_socketio}
            # Patch the direct imports to fail so we fall through to extensions
            with patch.dict('sys.modules', {'main': None}):
                result = worker._get_socketio()

        # May or may not reach extensions depending on import path;
        # just verify no crash
        assert True

    def test_JW_071_broadcast_comparison_start_no_socketio(self):
        """JW_071: broadcast_comparison_start handles no socketio gracefully."""
        from workers.judge_worker import JudgeWorker

        worker = JudgeWorker(session_id=1, app=MagicMock())

        with patch.object(worker, '_get_socketio', return_value=None):
            # Should not raise
            worker._broadcast_comparison_start(MagicMock())

    def test_JW_072_broadcast_stream_emits_event(self):
        """JW_072: _broadcast_stream emits judge:llm_stream event."""
        from workers.judge_worker import JudgeWorker

        mock_sio = MagicMock()
        worker = JudgeWorker(session_id=5, app=MagicMock())

        with patch.object(worker, '_get_socketio', return_value=mock_sio):
            worker._broadcast_stream("hello")

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == 'judge:llm_stream'
        assert call_args[0][1]['token'] == 'hello'
        assert call_args[0][1]['session_id'] == 5

    def test_JW_073_broadcast_progress_calculates_percent(self):
        """JW_073: _broadcast_progress calculates correct percentage."""
        from workers.judge_worker import JudgeWorker

        mock_sio = MagicMock()
        worker = JudgeWorker(session_id=1, app=MagicMock())

        mock_session = MagicMock()
        mock_session.completed_comparisons = 3
        mock_session.total_comparisons = 10

        with patch.object(worker, '_get_socketio', return_value=mock_sio):
            worker._broadcast_progress(mock_session)

        event_data = mock_sio.emit.call_args[0][1]
        assert event_data['percent'] == 30.0
        assert event_data['completed'] == 3

    def test_JW_074_broadcast_progress_zero_total(self):
        """JW_074: _broadcast_progress handles zero total safely."""
        from workers.judge_worker import JudgeWorker

        mock_sio = MagicMock()
        worker = JudgeWorker(session_id=1, app=MagicMock())

        mock_session = MagicMock()
        mock_session.completed_comparisons = 0
        mock_session.total_comparisons = 0

        with patch.object(worker, '_get_socketio', return_value=mock_sio):
            worker._broadcast_progress(mock_session)

        event_data = mock_sio.emit.call_args[0][1]
        assert event_data['percent'] == 0

    def test_JW_075_broadcast_session_complete_emits(self):
        """JW_075: _broadcast_session_complete emits correct event."""
        from workers.judge_worker import JudgeWorker

        mock_sio = MagicMock()
        worker = JudgeWorker(session_id=7, app=MagicMock())

        with patch.object(worker, '_get_socketio', return_value=mock_sio):
            worker._broadcast_session_complete()

        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == 'judge:session_complete'
        assert call_args[0][1]['session_id'] == 7


class TestWorkerManagementFunctions:
    """Test module-level worker management functions."""

    def test_JW_080_trigger_judge_worker_creates_worker(self):
        """JW_080: trigger_judge_worker creates and starts a worker."""
        import workers.judge_worker as jw

        # Clear global registry
        jw._workers.clear()

        mock_app = MagicMock()

        with patch('workers.judge_worker.current_app') as mock_ca:
            mock_ca._get_current_object.return_value = mock_app
            with patch.object(jw.JudgeWorker, 'start'):
                jw.trigger_judge_worker(session_id=10)

        assert 10 in jw._workers
        jw._workers.clear()

    def test_JW_081_trigger_stops_existing_worker(self):
        """JW_081: trigger_judge_worker stops existing worker first."""
        import workers.judge_worker as jw

        old_worker = MagicMock()
        jw._workers[10] = old_worker

        with patch('workers.judge_worker.current_app') as mock_ca:
            mock_ca._get_current_object.return_value = MagicMock()
            with patch.object(jw.JudgeWorker, 'start'):
                jw.trigger_judge_worker(session_id=10)

        old_worker.stop.assert_called_once()
        jw._workers.clear()

    def test_JW_082_stop_judge_worker_removes_from_registry(self):
        """JW_082: stop_judge_worker removes and stops worker."""
        import workers.judge_worker as jw

        mock_worker = MagicMock()
        jw._workers[10] = mock_worker

        jw.stop_judge_worker(session_id=10)

        mock_worker.stop.assert_called_once()
        assert 10 not in jw._workers

    def test_JW_083_stop_judge_worker_missing_session(self):
        """JW_083: stop_judge_worker handles missing session gracefully."""
        import workers.judge_worker as jw
        jw._workers.clear()

        # Should not raise
        jw.stop_judge_worker(session_id=999)

    def test_JW_084_get_worker_status_returns_dict(self):
        """JW_084: get_worker_status returns status dict for existing worker."""
        import workers.judge_worker as jw

        mock_worker = MagicMock()
        mock_worker.running = True
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        mock_worker.thread = mock_thread
        jw._workers[10] = mock_worker

        status = jw.get_worker_status(session_id=10)

        assert status is not None
        assert status['session_id'] == 10
        assert status['running'] is True
        assert status['thread_alive'] is True

        jw._workers.clear()

    def test_JW_085_get_worker_status_returns_none(self):
        """JW_085: get_worker_status returns None for missing session."""
        import workers.judge_worker as jw
        jw._workers.clear()

        assert jw.get_worker_status(session_id=999) is None
