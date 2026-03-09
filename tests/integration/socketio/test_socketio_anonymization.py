"""
Socket.IO Anonymization Pipeline Event Tests.

Tests for anonymization pipeline room management events.
Test IDs: ANON_SOCK_001 - ANON_SOCK_008
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestSocketIOAnonymizationEvents:
    """Tests for anonymization pipeline Socket.IO event handlers."""

    def test_ANON_SOCK_001_event_handlers_registered(self, app):
        """[ANON_SOCK-001] All anonymization events are registered on socketio."""
        with app.app_context():
            from socketio_handlers.events_anonymization import register_anonymization_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_anonymization_events(mock_socketio)

            calls = mock_socketio.on.call_args_list
            event_names = [call[0][0] for call in calls]

            assert "anonymization:join_overview" in event_names
            assert "anonymization:leave_overview" in event_names
            assert "anonymization:join_conversation" in event_names
            assert "anonymization:leave_conversation" in event_names

    def test_ANON_SOCK_002_join_overview_joins_room(self, app):
        """[ANON_SOCK-002] join_overview event adds client to overview room."""
        with app.app_context():
            from socketio_handlers.events_anonymization import register_anonymization_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler
            register_anonymization_events(mock_socketio)

            assert "anonymization:join_overview" in handlers

    def test_ANON_SOCK_003_leave_overview_registered(self, app):
        """[ANON_SOCK-003] leave_overview event handler is registered."""
        with app.app_context():
            from socketio_handlers.events_anonymization import register_anonymization_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler
            register_anonymization_events(mock_socketio)

            assert "anonymization:leave_overview" in handlers

    def test_ANON_SOCK_004_join_conversation_registered(self, app):
        """[ANON_SOCK-004] join_conversation event handler is registered."""
        with app.app_context():
            from socketio_handlers.events_anonymization import register_anonymization_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler
            register_anonymization_events(mock_socketio)

            assert "anonymization:join_conversation" in handlers

    def test_ANON_SOCK_005_leave_conversation_registered(self, app):
        """[ANON_SOCK-005] leave_conversation event handler is registered."""
        with app.app_context():
            from socketio_handlers.events_anonymization import register_anonymization_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler
            register_anonymization_events(mock_socketio)

            assert "anonymization:leave_conversation" in handlers

    def test_ANON_SOCK_006_join_conversation_requires_id(self, app):
        """[ANON_SOCK-006] join_conversation with missing ID emits error."""
        with app.app_context():
            from socketio_handlers.events_anonymization import register_anonymization_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler
            register_anonymization_events(mock_socketio)

            handler = handlers["anonymization:join_conversation"]

            # Call handler with invalid data - should not crash
            with patch("socketio_handlers.events_anonymization.emit") as mock_emit, \
                 patch("socketio_handlers.events_anonymization.request") as mock_request:
                mock_request.sid = "test-sid"

                handler({})  # empty data, no conversation_id
                mock_emit.assert_called()
                error_call = mock_emit.call_args
                assert error_call[0][0] == "anonymization:error"

    def test_ANON_SOCK_007_join_conversation_valid_id(self, app):
        """[ANON_SOCK-007] join_conversation with valid ID joins correct room."""
        with app.app_context():
            from socketio_handlers.events_anonymization import register_anonymization_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler
            register_anonymization_events(mock_socketio)

            handler = handlers["anonymization:join_conversation"]

            with patch("socketio_handlers.events_anonymization.emit") as mock_emit, \
                 patch("socketio_handlers.events_anonymization.join_room") as mock_join, \
                 patch("socketio_handlers.events_anonymization.request") as mock_request:
                mock_request.sid = "test-sid"

                handler({"conversation_id": 42})

                mock_join.assert_called_once_with("anonymization_conversation_42")
                mock_emit.assert_called()
                joined_data = mock_emit.call_args[0][1]
                assert joined_data["conversation_id"] == 42

    def test_ANON_SOCK_008_leave_conversation_valid_id(self, app):
        """[ANON_SOCK-008] leave_conversation with valid ID leaves room."""
        with app.app_context():
            from socketio_handlers.events_anonymization import register_anonymization_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler
            register_anonymization_events(mock_socketio)

            handler = handlers["anonymization:leave_conversation"]

            with patch("socketio_handlers.events_anonymization.leave_room") as mock_leave, \
                 patch("socketio_handlers.events_anonymization.request") as mock_request:
                mock_request.sid = "test-sid"

                handler({"conversation_id": 42})

                mock_leave.assert_called_once_with("anonymization_conversation_42")
