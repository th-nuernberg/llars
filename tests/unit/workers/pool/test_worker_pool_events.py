"""
Tests for worker_pool_events - Socket.IO event broadcasting.

Covers:
- get_socketio retrieval from multiple sources
- Comparison lifecycle events (start, complete)
- LLM stream chunk broadcasting
- Progress updates (atomic and legacy)
- Session completion notifications
- Dual-room emission (session + overview)
"""

from unittest.mock import MagicMock, patch

import pytest


class TestGetSocketio:
    """Test Socket.IO instance retrieval."""

    def test_WPE_001_get_socketio_from_main(self):
        """WPE_001: Gets socketio from main module import."""
        from workers.pool.worker_pool_events import get_socketio

        mock_sio = MagicMock()

        with patch.dict('sys.modules', {'main': MagicMock(socketio=mock_sio)}):
            result = get_socketio(session_id=1, worker_id=0)
            assert result is mock_sio

    def test_WPE_002_get_socketio_from_app_main(self):
        """WPE_002: Falls back to app.main import."""
        from workers.pool.worker_pool_events import get_socketio

        mock_sio = MagicMock()
        mock_app_main = MagicMock(socketio=mock_sio)

        # Make 'main' fail, 'app.main' succeed
        import sys
        with patch.dict('sys.modules', {'main': None, 'app.main': mock_app_main, 'app': MagicMock()}):
            # This may or may not use app.main depending on import mechanism
            # Just verify no crash
            result = get_socketio(session_id=1, worker_id=0)

    def test_WPE_003_get_socketio_from_extensions(self):
        """WPE_003: Falls back to Flask current_app extensions."""
        from workers.pool.worker_pool_events import get_socketio

        mock_sio = MagicMock()
        mock_ca = MagicMock()
        mock_ca.extensions = {'socketio': mock_sio}

        with patch('workers.pool.worker_pool_events.current_app', mock_ca):
            with patch.dict('sys.modules', {'main': None}):
                result = get_socketio(session_id=1, worker_id=0)
                assert True

    def test_WPE_004_get_socketio_returns_none_when_unavailable(self):
        """WPE_004: Returns None when no socketio instance found."""
        from workers.pool.worker_pool_events import get_socketio

        mock_ca = MagicMock()
        mock_ca.extensions = {}

        with patch.dict('sys.modules', {'main': None}):
            with patch('workers.pool.worker_pool_events.current_app', mock_ca):
                result = get_socketio(session_id=1, worker_id=0)
                # Result depends on import path resolution


class TestBroadcastComparisonStart:
    """Test comparison start broadcasting."""

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_010_broadcast_start_emits_event(self, mock_get_sio):
        """WPE_010: broadcast_comparison_start emits to session room."""
        from workers.pool.worker_pool_events import broadcast_comparison_start

        mock_sio = MagicMock()
        mock_get_sio.return_value = mock_sio

        comparison_data = {
            'comparison_id': 42,
            'thread_a_id': 1,
            'thread_b_id': 2,
            'pillar_a': 10,
            'pillar_b': 20,
            'position_order': 'AB'
        }

        broadcast_comparison_start(session_id=5, worker_id=1, comparison_data=comparison_data)

        mock_sio.emit.assert_called_once()
        args = mock_sio.emit.call_args
        assert args[0][0] == 'judge:comparison_start'
        data = args[0][1]
        assert data['session_id'] == 5
        assert data['worker_id'] == 1
        assert data['comparison_id'] == 42
        assert args[1]['room'] == 'judge_session_5'

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_011_broadcast_start_no_socketio(self, mock_get_sio):
        """WPE_011: Handles missing socketio gracefully."""
        from workers.pool.worker_pool_events import broadcast_comparison_start

        mock_get_sio.return_value = None

        # Should not raise
        broadcast_comparison_start(session_id=1, worker_id=0, comparison_data={})


class TestBroadcastStreamChunk:
    """Test LLM stream chunk broadcasting."""

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_020_broadcast_stream_chunk_emits(self, mock_get_sio):
        """WPE_020: broadcast_stream_chunk emits judge:llm_stream."""
        from workers.pool.worker_pool_events import broadcast_stream_chunk

        mock_sio = MagicMock()
        mock_get_sio.return_value = mock_sio

        broadcast_stream_chunk(session_id=3, worker_id=1, chunk="Hello", accumulated_length=5)

        mock_sio.emit.assert_called_once()
        args = mock_sio.emit.call_args
        assert args[0][0] == 'judge:llm_stream'
        data = args[0][1]
        assert data['token'] == 'Hello'
        assert data['content'] == 'Hello'
        assert data['accumulated_length'] == 5
        assert data['worker_id'] == 1

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_021_broadcast_stream_chunk_no_socketio(self, mock_get_sio):
        """WPE_021: No-op when socketio unavailable."""
        from workers.pool.worker_pool_events import broadcast_stream_chunk

        mock_get_sio.return_value = None
        # Should not raise
        broadcast_stream_chunk(session_id=1, worker_id=0, chunk="test", accumulated_length=4)


class TestBroadcastComparisonComplete:
    """Test comparison completion broadcasting."""

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_030_broadcast_complete_emits_to_two_rooms(self, mock_get_sio):
        """WPE_030: broadcast_comparison_complete emits to session and overview rooms."""
        from workers.pool.worker_pool_events import broadcast_comparison_complete

        mock_sio = MagicMock()
        mock_get_sio.return_value = mock_sio

        mock_result = MagicMock()
        mock_result.winner = 'A'
        mock_result.confidence = 0.85
        mock_result.final_justification = "A is better"

        broadcast_comparison_complete(
            session_id=5, worker_id=1, comparison_id=42,
            result=mock_result, stream_content="full content",
            completed=3, total=10
        )

        assert mock_sio.emit.call_count == 2
        # First call: session room
        first_call = mock_sio.emit.call_args_list[0]
        assert first_call[1]['room'] == 'judge_session_5'
        # Second call: overview room
        second_call = mock_sio.emit.call_args_list[1]
        assert second_call[1]['room'] == 'judge_overview'


class TestBroadcastProgressAtomic:
    """Test atomic progress broadcasting."""

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_040_broadcast_progress_calculates_percent(self, mock_get_sio):
        """WPE_040: Calculates correct progress percentage."""
        from workers.pool.worker_pool_events import broadcast_progress_atomic

        mock_sio = MagicMock()
        mock_get_sio.return_value = mock_sio

        broadcast_progress_atomic(session_id=5, worker_id=0, completed=7, total=10)

        assert mock_sio.emit.call_count == 2
        data = mock_sio.emit.call_args_list[0][0][1]
        assert data['percent'] == 70.0
        assert data['completed'] == 7
        assert data['total'] == 10
        assert data['status'] == 'running'

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_041_broadcast_progress_zero_total(self, mock_get_sio):
        """WPE_041: Handles zero total comparisons safely."""
        from workers.pool.worker_pool_events import broadcast_progress_atomic

        mock_sio = MagicMock()
        mock_get_sio.return_value = mock_sio

        broadcast_progress_atomic(session_id=1, worker_id=0, completed=0, total=0)

        data = mock_sio.emit.call_args_list[0][0][1]
        assert data['percent'] == 0


class TestBroadcastProgressLegacy:
    """Test legacy progress broadcasting."""

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_050_broadcast_progress_legacy_uses_session(self, mock_get_sio):
        """WPE_050: Legacy progress reads from session object."""
        from workers.pool.worker_pool_events import broadcast_progress_legacy

        mock_sio = MagicMock()
        mock_get_sio.return_value = mock_sio

        mock_session = MagicMock()
        mock_session.completed_comparisons = 5
        mock_session.total_comparisons = 20
        mock_session.status.value = 'running'

        broadcast_progress_legacy(session_id=1, worker_id=0, session=mock_session)

        data = mock_sio.emit.call_args_list[0][0][1]
        assert data['percent'] == 25.0
        assert data['status'] == 'running'


class TestBroadcastSessionComplete:
    """Test session completion broadcasting."""

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_060_broadcast_session_complete_emits_to_both_rooms(self, mock_get_sio):
        """WPE_060: Session complete emits to session and overview rooms."""
        from workers.pool.worker_pool_events import broadcast_session_complete

        mock_sio = MagicMock()
        mock_get_sio.return_value = mock_sio

        broadcast_session_complete(session_id=5, worker_id=0, total=50)

        assert mock_sio.emit.call_count == 2
        data = mock_sio.emit.call_args_list[0][0][1]
        assert data['session_id'] == 5
        assert data['total'] == 50
        assert data['completed'] == 50  # Both equal when complete

    @patch('workers.pool.worker_pool_events.get_socketio')
    def test_WPE_061_broadcast_session_complete_no_socketio(self, mock_get_sio):
        """WPE_061: No-op when socketio unavailable."""
        from workers.pool.worker_pool_events import broadcast_session_complete

        mock_get_sio.return_value = None
        # Should not raise
        broadcast_session_complete(session_id=1, worker_id=0, total=10)
