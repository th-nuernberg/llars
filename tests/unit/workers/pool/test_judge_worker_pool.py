"""
Tests for JudgeWorkerPool - manages multiple parallel workers.

Covers:
- Pool initialization and worker count clamping
- Pool lifecycle (start, stop)
- Worker management and status reporting
- Stream state for reconnect support
- Module-level pool management functions
"""

import threading
from unittest.mock import MagicMock, patch, call

import pytest


class TestJudgeWorkerPoolInit:
    """Test JudgeWorkerPool initialization."""

    def test_JWP_001_init_clamps_worker_count_upper(self):
        """JWP_001: Worker count is clamped to MAX_WORKERS."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=1, worker_count=10, app=MagicMock())
        assert pool.worker_count == 5  # MAX_WORKERS

    def test_JWP_002_init_clamps_worker_count_lower(self):
        """JWP_002: Worker count is clamped to minimum 1."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=1, worker_count=0, app=MagicMock())
        assert pool.worker_count == 1

    def test_JWP_003_init_defaults(self):
        """JWP_003: Pool initializes with correct defaults."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        mock_app = MagicMock()
        pool = JudgeWorkerPool(session_id=42, worker_count=3, app=mock_app)

        assert pool.session_id == 42
        assert pool.worker_count == 3
        assert pool.app is mock_app
        assert pool.workers == []
        assert pool.running is False


class TestJudgeWorkerPoolStartStop:
    """Test pool start and stop lifecycle."""

    def test_JWP_010_start_creates_workers(self):
        """JWP_010: Start creates and starts correct number of workers."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=1, worker_count=3, app=MagicMock())

        with patch('workers.pool.judge_worker_pool.PooledJudgeWorker') as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            pool.start()

            assert pool.running is True
            assert MockWorker.call_count == 3
            assert mock_instance.start.call_count == 3
            assert len(pool.workers) == 3

    def test_JWP_011_start_when_running_returns_early(self):
        """JWP_011: Starting when already running logs warning."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=1, worker_count=2, app=MagicMock())
        pool.running = True

        with patch('workers.pool.judge_worker_pool.PooledJudgeWorker') as MockWorker:
            pool.start()
            MockWorker.assert_not_called()

    def test_JWP_012_stop_stops_all_workers(self):
        """JWP_012: Stop stops all workers and clears list."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=1, worker_count=2, app=MagicMock())
        pool.running = True

        mock_workers = [MagicMock(), MagicMock()]
        pool.workers = list(mock_workers)

        pool.stop()

        for w in mock_workers:
            w.stop.assert_called_once()
        assert pool.running is False
        assert pool.workers == []

    def test_JWP_013_is_running_checks_workers(self):
        """JWP_013: is_running returns True if any worker is running."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=1, worker_count=2, app=MagicMock())

        w1 = MagicMock()
        w1.running = False
        w2 = MagicMock()
        w2.running = True
        pool.workers = [w1, w2]

        assert pool.is_running() is True

    def test_JWP_014_is_running_false_when_none_active(self):
        """JWP_014: is_running returns False when no workers are running."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=1, worker_count=2, app=MagicMock())

        w1 = MagicMock()
        w1.running = False
        pool.workers = [w1]

        assert pool.is_running() is False


class TestJudgeWorkerPoolStatus:
    """Test pool status and stream state reporting."""

    def test_JWP_020_get_status_returns_all_workers(self):
        """JWP_020: get_status returns status for all workers."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=5, worker_count=2, app=MagicMock())
        pool.running = True

        w1 = MagicMock()
        w1.worker_id = 0
        w1.running = True
        w1.current_comparison_id = 42
        w2 = MagicMock()
        w2.worker_id = 1
        w2.running = False
        w2.current_comparison_id = None
        pool.workers = [w1, w2]

        status = pool.get_status()

        assert status['session_id'] == 5
        assert status['worker_count'] == 2
        assert status['running'] is True
        assert len(status['workers']) == 2
        assert status['workers'][0]['worker_id'] == 0
        assert status['workers'][0]['running'] is True

    def test_JWP_021_get_worker_streams_returns_stream_states(self):
        """JWP_021: get_worker_streams returns stream state per worker."""
        from workers.pool.judge_worker_pool import JudgeWorkerPool

        pool = JudgeWorkerPool(session_id=5, worker_count=1, app=MagicMock())

        w1 = MagicMock()
        w1.get_stream_state.return_value = {
            'worker_id': 0,
            'running': True,
            'is_streaming': True,
            'stream_content': 'partial...'
        }
        pool.workers = [w1]

        result = pool.get_worker_streams()
        assert result['session_id'] == 5
        assert len(result['workers']) == 1
        assert result['workers'][0]['is_streaming'] is True


class TestPooledJudgeWorker:
    """Test PooledJudgeWorker individual worker."""

    def test_JWP_030_pooled_worker_init(self):
        """JWP_030: PooledJudgeWorker initializes with correct attributes."""
        from workers.pool.judge_worker_pool import PooledJudgeWorker, JudgeWorkerPool

        mock_pool = MagicMock(spec=JudgeWorkerPool)
        worker = PooledJudgeWorker(
            session_id=1, worker_id=2, pool=mock_pool, app=MagicMock()
        )

        assert worker.session_id == 1
        assert worker.worker_id == 2
        assert worker.pool is mock_pool
        assert worker.running is False
        assert worker.stream_content == ""
        assert worker.is_streaming is False
        assert worker.current_comparison_id is None

    def test_JWP_031_get_stream_state_returns_dict(self):
        """JWP_031: get_stream_state returns correct structure."""
        from workers.pool.judge_worker_pool import PooledJudgeWorker

        worker = PooledJudgeWorker(
            session_id=1, worker_id=0, pool=MagicMock(), app=MagicMock()
        )
        worker.stream_content = "Hello world"
        worker.is_streaming = True
        worker.current_comparison_id = 99

        state = worker.get_stream_state()

        assert state['worker_id'] == 0
        assert state['is_streaming'] is True
        assert state['current_comparison_id'] == 99
        assert state['stream_content'] == "Hello world"
        assert state['stream_length'] == 11

    def test_JWP_032_start_creates_daemon_thread(self):
        """JWP_032: Start creates a daemon thread."""
        from workers.pool.judge_worker_pool import PooledJudgeWorker

        worker = PooledJudgeWorker(
            session_id=1, worker_id=0, pool=MagicMock(), app=MagicMock()
        )

        with patch.object(worker, '_run'):
            worker.start()

            assert worker.running is True
            assert worker.thread is not None
            assert worker.thread.daemon is True

            worker.stop()

    def test_JWP_033_start_does_nothing_if_running(self):
        """JWP_033: Start returns if already running."""
        from workers.pool.judge_worker_pool import PooledJudgeWorker

        worker = PooledJudgeWorker(
            session_id=1, worker_id=0, pool=MagicMock(), app=MagicMock()
        )
        worker.running = True

        worker.start()
        assert worker.thread is None  # No new thread created

    def test_JWP_034_stop_joins_thread(self):
        """JWP_034: Stop joins alive thread."""
        from workers.pool.judge_worker_pool import PooledJudgeWorker

        worker = PooledJudgeWorker(
            session_id=1, worker_id=0, pool=MagicMock(), app=MagicMock()
        )
        worker.running = True
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        worker.thread = mock_thread

        worker.stop()

        assert worker.running is False
        mock_thread.join.assert_called_once_with(timeout=5.0)

    def test_JWP_035_run_sets_running_false_on_complete(self):
        """JWP_035: _run sets running=False and clears comparison after completion."""
        from workers.pool.judge_worker_pool import PooledJudgeWorker

        mock_app = MagicMock()
        worker = PooledJudgeWorker(
            session_id=1, worker_id=0, pool=MagicMock(), app=mock_app
        )
        worker.running = True
        worker.current_comparison_id = 42

        with patch.object(worker, '_process_queue'):
            worker._run()

        assert worker.running is False
        assert worker.current_comparison_id is None

    def test_JWP_036_run_handles_exception_in_process_queue(self):
        """JWP_036: _run handles exceptions from _process_queue."""
        from workers.pool.judge_worker_pool import PooledJudgeWorker

        mock_app = MagicMock()
        worker = PooledJudgeWorker(
            session_id=1, worker_id=0, pool=MagicMock(), app=mock_app
        )
        worker.running = True

        with patch.object(worker, '_process_queue', side_effect=RuntimeError("fail")):
            worker._run()

        assert worker.running is False


class TestPoolManagementFunctions:
    """Test module-level pool management functions."""

    def test_JWP_040_trigger_pool_creates_and_starts(self):
        """JWP_040: trigger_judge_worker_pool creates pool and starts it."""
        from workers.pool.judge_worker_pool import trigger_judge_worker_pool
        from workers.pool.worker_pool_constants import _pools, _pool_lock

        _pools.clear()

        with patch('workers.pool.judge_worker_pool.current_app') as mock_ca:
            mock_ca._get_current_object.return_value = MagicMock()
            with patch('workers.pool.judge_worker_pool.JudgeWorkerPool') as MockPool:
                mock_pool = MagicMock()
                MockPool.return_value = mock_pool

                trigger_judge_worker_pool(session_id=10, worker_count=3)

                MockPool.assert_called_once()
                mock_pool.start.assert_called_once()

        _pools.clear()

    def test_JWP_041_trigger_stops_existing_pool(self):
        """JWP_041: trigger_judge_worker_pool stops existing pool."""
        from workers.pool.judge_worker_pool import trigger_judge_worker_pool
        from workers.pool.worker_pool_constants import _pools

        old_pool = MagicMock()
        _pools[10] = old_pool

        with patch('workers.pool.judge_worker_pool.current_app') as mock_ca:
            mock_ca._get_current_object.return_value = MagicMock()
            with patch('workers.pool.judge_worker_pool.JudgeWorkerPool') as MockPool:
                MockPool.return_value = MagicMock()
                trigger_judge_worker_pool(session_id=10, worker_count=2)

        old_pool.stop.assert_called_once()
        _pools.clear()

    def test_JWP_042_stop_pool(self):
        """JWP_042: stop_judge_worker_pool stops and removes pool."""
        from workers.pool.judge_worker_pool import stop_judge_worker_pool
        from workers.pool.worker_pool_constants import _pools

        mock_pool = MagicMock()
        _pools[10] = mock_pool

        stop_judge_worker_pool(session_id=10)

        mock_pool.stop.assert_called_once()
        assert 10 not in _pools

    def test_JWP_043_stop_pool_missing(self):
        """JWP_043: stop_judge_worker_pool handles missing pool gracefully."""
        from workers.pool.judge_worker_pool import stop_judge_worker_pool
        from workers.pool.worker_pool_constants import _pools

        _pools.clear()
        # Should not raise
        stop_judge_worker_pool(session_id=999)

    def test_JWP_044_get_pool_status_returns_status(self):
        """JWP_044: get_pool_status returns pool status dict."""
        from workers.pool.judge_worker_pool import get_pool_status
        from workers.pool.worker_pool_constants import _pools

        mock_pool = MagicMock()
        mock_pool.get_status.return_value = {'session_id': 10, 'running': True}
        _pools[10] = mock_pool

        status = get_pool_status(10)
        assert status['session_id'] == 10
        assert status['running'] is True

        _pools.clear()

    def test_JWP_045_get_pool_status_missing(self):
        """JWP_045: get_pool_status returns None for missing pool."""
        from workers.pool.judge_worker_pool import get_pool_status
        from workers.pool.worker_pool_constants import _pools

        _pools.clear()
        assert get_pool_status(999) is None

    def test_JWP_046_get_worker_streams_returns_streams(self):
        """JWP_046: get_worker_streams returns stream states."""
        from workers.pool.judge_worker_pool import get_worker_streams
        from workers.pool.worker_pool_constants import _pools

        mock_pool = MagicMock()
        mock_pool.get_worker_streams.return_value = {'session_id': 5, 'workers': []}
        _pools[5] = mock_pool

        result = get_worker_streams(5)
        assert result is not None

        _pools.clear()

    def test_JWP_047_get_worker_streams_missing(self):
        """JWP_047: get_worker_streams returns None for missing pool."""
        from workers.pool.judge_worker_pool import get_worker_streams
        from workers.pool.worker_pool_constants import _pools

        _pools.clear()
        assert get_worker_streams(999) is None
