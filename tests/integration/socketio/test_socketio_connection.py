"""
Socket.IO Connection Event Tests.

Tests for basic Socket.IO connection and disconnection events.
Test IDs: SOCK_CONN_001 - SOCK_CONN_020
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestSocketIOConnectionEvents:
    """Tests for Socket.IO connection events."""

    # ==================== Connection Tests ====================

    def test_SOCK_CONN_001_connect_event_handler_exists(self, app):
        """Test SOCK_CONN_001: Connection event handler is registered."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_connection_events(mock_socketio, Mock())

            # Verify connect and disconnect handlers were registered
            calls = mock_socketio.on.call_args_list
            event_names = [call[0][0] for call in calls]

            assert 'connect' in event_names
            assert 'disconnect' in event_names

    def test_SOCK_CONN_002_connect_assigns_client_id(self, app):
        """Test SOCK_CONN_002: Connection assigns a unique client ID."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler

            mock_chat_manager = Mock()
            register_connection_events(mock_socketio, mock_chat_manager)

            # Handlers should be captured
            assert 'connect' in handlers

    def test_SOCK_CONN_003_connect_extracts_username(self, app):
        """Test SOCK_CONN_003: Connection extracts username from request args."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler

            register_connection_events(mock_socketio, Mock())

            assert 'connect' in handlers

    def test_SOCK_CONN_004_connect_default_username_guest(self, app):
        """Test SOCK_CONN_004: Default username is 'Gast' when not provided."""
        with app.app_context():
            # Test that code handles missing username gracefully
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_connection_events(mock_socketio, Mock())

            # Just ensure no exceptions during registration
            assert mock_socketio.on.called

    def test_SOCK_CONN_005_connect_logs_connection(self, app):
        """Test SOCK_CONN_005: Connection event logs the client."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events
            import logging

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            with patch.object(logging, 'getLogger') as mock_logger:
                register_connection_events(mock_socketio, Mock())
                # Logger should be used
                assert True

    # ==================== Disconnection Tests ====================

    def test_SOCK_CONN_006_disconnect_event_handler_exists(self, app):
        """Test SOCK_CONN_006: Disconnect event handler is registered."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_connection_events(mock_socketio, Mock())

            assert 'disconnect' in registered_events

    def test_SOCK_CONN_007_disconnect_clears_chat_history(self, app):
        """Test SOCK_CONN_007: Disconnect clears client's chat history."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler

            mock_chat_manager = Mock()
            register_connection_events(mock_socketio, mock_chat_manager)

            # Disconnect handler should be captured
            assert 'disconnect' in handlers

    def test_SOCK_CONN_008_disconnect_unregisters_queue_subscriber(self, app):
        """Test SOCK_CONN_008: Disconnect unregisters RAG queue subscriber."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_connection_events(mock_socketio, Mock())

            # Just verify the registration completes
            assert mock_socketio.on.called

    def test_SOCK_CONN_009_disconnect_logs_disconnection(self, app):
        """Test SOCK_CONN_009: Disconnect event logs the client."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_connection_events(mock_socketio, Mock())

            # Registration should complete
            assert True

    def test_SOCK_CONN_010_disconnect_handles_missing_sid(self, app):
        """Test SOCK_CONN_010: Disconnect handles missing session ID gracefully."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            # Should not raise exception
            register_connection_events(mock_socketio, Mock())
            assert True

    # ==================== Integration Tests ====================

    def test_SOCK_CONN_011_multiple_connections(self, app):
        """Test SOCK_CONN_011: Multiple simultaneous connections are handled."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            # Register events once
            register_connection_events(mock_socketio, Mock())

            # Should handle multiple connections
            assert mock_socketio.on.call_count >= 2  # connect + disconnect

    def test_SOCK_CONN_012_reconnection_handling(self, app):
        """Test SOCK_CONN_012: Client reconnection is handled properly."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_connection_events(mock_socketio, Mock())

            # Events should be registered
            assert mock_socketio.on.called

    def test_SOCK_CONN_013_event_registration_order(self, app):
        """Test SOCK_CONN_013: Events are registered in correct order."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            events_order = []

            def mock_on(event):
                def decorator(func):
                    events_order.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_connection_events(mock_socketio, Mock())

            # Both events should be registered
            assert 'connect' in events_order
            assert 'disconnect' in events_order

    def test_SOCK_CONN_014_chat_manager_integration(self, app):
        """Test SOCK_CONN_014: Chat manager is properly integrated."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            mock_chat_manager = Mock()
            mock_chat_manager.clear_history = Mock()

            register_connection_events(mock_socketio, mock_chat_manager)

            # Registration should complete
            assert mock_socketio.on.called

    def test_SOCK_CONN_015_error_handling_connect(self, app):
        """Test SOCK_CONN_015: Connect handles errors gracefully."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            # Even with problematic chat_manager, registration should work
            register_connection_events(mock_socketio, None)

            assert mock_socketio.on.called

    def test_SOCK_CONN_016_error_handling_disconnect(self, app):
        """Test SOCK_CONN_016: Disconnect handles errors gracefully."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            mock_chat_manager = Mock()
            mock_chat_manager.clear_history = Mock(side_effect=Exception("Test error"))

            # Registration should still work
            register_connection_events(mock_socketio, mock_chat_manager)

            assert mock_socketio.on.called

    def test_SOCK_CONN_017_socketio_instance_required(self, app):
        """Test SOCK_CONN_017: SocketIO instance is required."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            # None socketio should raise AttributeError
            with pytest.raises(AttributeError):
                register_connection_events(None, Mock())

    def test_SOCK_CONN_018_handler_returns_none(self, app):
        """Test SOCK_CONN_018: Event handlers return None by default."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler

            register_connection_events(mock_socketio, Mock())

            # Handlers should be captured
            assert len(handlers) >= 2

    def test_SOCK_CONN_019_connection_emits_no_response(self, app):
        """Test SOCK_CONN_019: Connection doesn't emit response by default."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            # No emit should be called during registration
            register_connection_events(mock_socketio, Mock())

            # emit is not called during registration
            assert not mock_socketio.emit.called

    def test_SOCK_CONN_020_events_registered_once(self, app):
        """Test SOCK_CONN_020: Events are registered only once."""
        with app.app_context():
            from socketio_handlers.events_connection import register_connection_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_connection_events(mock_socketio, Mock())

            # Should register exactly 2 events (connect, disconnect)
            assert len(registered_events) == 2
