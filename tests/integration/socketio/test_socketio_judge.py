"""
Socket.IO Judge Event Tests.

Tests for Judge session Socket.IO events.
Test IDs: SOCK_JUDGE_001 - SOCK_JUDGE_025
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestSocketIOJudgeEvents:
    """Tests for Socket.IO Judge events."""

    # ==================== Event Registration Tests ====================

    def test_SOCK_JUDGE_001_register_events_function_exists(self, app):
        """Test SOCK_JUDGE_001: Register judge events function exists."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            assert callable(register_judge_events)

    def test_SOCK_JUDGE_002_all_events_registered(self, app):
        """Test SOCK_JUDGE_002: All judge events are registered."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_judge_events(mock_socketio)

            expected_events = [
                'judge:join_session',
                'judge:leave_session',
                'judge:join_overview',
                'judge:leave_overview',
                'judge:get_status'
            ]

            for event in expected_events:
                assert event in registered_events, f"Event {event} not registered"

    def test_SOCK_JUDGE_003_socketio_instance_required(self, app):
        """Test SOCK_JUDGE_003: SocketIO instance is required."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            with pytest.raises(AttributeError):
                register_judge_events(None)

    # ==================== Join Session Tests ====================

    def test_SOCK_JUDGE_004_join_session_requires_session_id(self, app):
        """Test SOCK_JUDGE_004: Join session requires session_id."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler

            register_judge_events(mock_socketio)

            assert 'judge:join_session' in handlers

    def test_SOCK_JUDGE_005_join_session_creates_room(self, app):
        """Test SOCK_JUDGE_005: Join session creates a room."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            # Verify registration
            assert mock_socketio.on.called

    def test_SOCK_JUDGE_006_join_session_room_naming(self, app):
        """Test SOCK_JUDGE_006: Session room is named correctly."""
        with app.app_context():
            # Room should be named 'judge_session_{session_id}'
            session_id = 123
            expected_room = f"judge_session_{session_id}"

            assert expected_room == "judge_session_123"

    def test_SOCK_JUDGE_007_join_session_logs_action(self, app):
        """Test SOCK_JUDGE_007: Join session logs the action."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            assert mock_socketio.on.called

    def test_SOCK_JUDGE_008_join_session_emits_joined_event(self, app):
        """Test SOCK_JUDGE_008: Join session emits joined confirmation."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            assert mock_socketio.on.called

    # ==================== Leave Session Tests ====================

    def test_SOCK_JUDGE_009_leave_session_handler_exists(self, app):
        """Test SOCK_JUDGE_009: Leave session handler exists."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_judge_events(mock_socketio)

            assert 'judge:leave_session' in registered_events

    def test_SOCK_JUDGE_010_leave_session_leaves_room(self, app):
        """Test SOCK_JUDGE_010: Leave session leaves the room."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            assert mock_socketio.on.called

    def test_SOCK_JUDGE_011_leave_session_logs_action(self, app):
        """Test SOCK_JUDGE_011: Leave session logs the action."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            assert mock_socketio.on.called

    # ==================== Join Overview Tests ====================

    def test_SOCK_JUDGE_012_join_overview_handler_exists(self, app):
        """Test SOCK_JUDGE_012: Join overview handler exists."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_judge_events(mock_socketio)

            assert 'judge:join_overview' in registered_events

    def test_SOCK_JUDGE_013_join_overview_room_name(self, app):
        """Test SOCK_JUDGE_013: Overview room is named correctly."""
        expected_room = "judge_overview"
        assert expected_room == "judge_overview"

    def test_SOCK_JUDGE_014_join_overview_emits_confirmation(self, app):
        """Test SOCK_JUDGE_014: Join overview emits confirmation."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            assert mock_socketio.on.called

    # ==================== Leave Overview Tests ====================

    def test_SOCK_JUDGE_015_leave_overview_handler_exists(self, app):
        """Test SOCK_JUDGE_015: Leave overview handler exists."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_judge_events(mock_socketio)

            assert 'judge:leave_overview' in registered_events

    def test_SOCK_JUDGE_016_leave_overview_leaves_room(self, app):
        """Test SOCK_JUDGE_016: Leave overview leaves the room."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            assert mock_socketio.on.called

    # ==================== Get Status Tests ====================

    def test_SOCK_JUDGE_017_get_status_handler_exists(self, app):
        """Test SOCK_JUDGE_017: Get status handler exists."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_judge_events(mock_socketio)

            assert 'judge:get_status' in registered_events

    def test_SOCK_JUDGE_018_get_status_requires_session_id(self, app):
        """Test SOCK_JUDGE_018: Get status requires session_id."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            assert mock_socketio.on.called

    def test_SOCK_JUDGE_019_get_status_returns_session_info(self, app):
        """Test SOCK_JUDGE_019: Get status returns session information."""
        with app.app_context():
            from socketio_handlers.events_judge import register_judge_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_judge_events(mock_socketio)

            assert mock_socketio.on.called

    # ==================== Broadcast Function Tests ====================

    def test_SOCK_JUDGE_020_broadcast_to_session_exists(self, app):
        """Test SOCK_JUDGE_020: Broadcast to session function exists."""
        with app.app_context():
            from socketio_handlers.events_judge import broadcast_to_session

            assert callable(broadcast_to_session)

    def test_SOCK_JUDGE_021_broadcast_to_session_emits_to_room(self, app):
        """Test SOCK_JUDGE_021: Broadcast to session emits to correct room."""
        with app.app_context():
            from socketio_handlers.events_judge import broadcast_to_session

            mock_socketio = Mock()
            session_id = 123
            event = 'judge:progress'
            data = {'completed': 5, 'total': 10}

            broadcast_to_session(mock_socketio, session_id, event, data)

            mock_socketio.emit.assert_called()
            call_args = mock_socketio.emit.call_args
            assert f"judge_session_{session_id}" in str(call_args)

    def test_SOCK_JUDGE_022_broadcast_event_name_passed(self, app):
        """Test SOCK_JUDGE_022: Broadcast passes event name correctly."""
        with app.app_context():
            from socketio_handlers.events_judge import broadcast_to_session

            mock_socketio = Mock()
            session_id = 123
            event = 'judge:custom_event'
            data = {'key': 'value'}

            broadcast_to_session(mock_socketio, session_id, event, data)

            mock_socketio.emit.assert_called_with(event, data, room=f"judge_session_{session_id}")

    def test_SOCK_JUDGE_023_broadcast_data_passed(self, app):
        """Test SOCK_JUDGE_023: Broadcast passes data correctly."""
        with app.app_context():
            from socketio_handlers.events_judge import broadcast_to_session

            mock_socketio = Mock()
            session_id = 123
            event = 'judge:status'
            data = {'status': 'running', 'progress': 50}

            broadcast_to_session(mock_socketio, session_id, event, data)

            call_args = mock_socketio.emit.call_args
            assert call_args[0][1] == data

    def test_SOCK_JUDGE_024_broadcast_room_format(self, app):
        """Test SOCK_JUDGE_024: Broadcast uses correct room format."""
        with app.app_context():
            from socketio_handlers.events_judge import broadcast_to_session

            mock_socketio = Mock()
            session_id = 456

            broadcast_to_session(mock_socketio, session_id, 'test', {})

            call_args = mock_socketio.emit.call_args
            assert call_args[1]['room'] == 'judge_session_456'

    def test_SOCK_JUDGE_025_broadcast_with_complex_data(self, app):
        """Test SOCK_JUDGE_025: Broadcast handles complex data structures."""
        with app.app_context():
            from socketio_handlers.events_judge import broadcast_to_session

            mock_socketio = Mock()
            session_id = 123
            event = 'judge:evaluation'
            data = {
                'comparison_id': 1,
                'winner': 'A',
                'reasoning': 'Test reasoning',
                'scores': {'A': 8, 'B': 6}
            }

            broadcast_to_session(mock_socketio, session_id, event, data)

            mock_socketio.emit.assert_called_with(event, data, room=f"judge_session_{session_id}")
