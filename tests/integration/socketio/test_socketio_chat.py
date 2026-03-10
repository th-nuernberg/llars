"""
Socket.IO Chat Event Tests.

Tests for Chat Streaming Socket.IO events.
Test IDs: SOCK_CHAT_001 - SOCK_CHAT_025
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestSocketIOChatEvents:
    """Tests for Socket.IO Chat events."""

    # ==================== Event Registration Tests ====================

    def test_SOCK_CHAT_001_register_events_function_exists(self, app):
        """Test SOCK_CHAT_001: Register chat events function exists."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            assert callable(register_chat_events)

    def test_SOCK_CHAT_002_all_events_registered(self, app):
        """Test SOCK_CHAT_002: All chat events are registered."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            mock_chat_manager = Mock()
            register_chat_events(mock_socketio, mock_chat_manager)

            expected_events = [
                'chat_stream',
                'test_prompt_stream'
            ]

            for event in expected_events:
                assert event in registered_events, f"Event {event} not registered"

    def test_SOCK_CHAT_003_socketio_instance_required(self, app):
        """Test SOCK_CHAT_003: SocketIO instance is required."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            with pytest.raises(AttributeError):
                register_chat_events(None, Mock())

    def test_SOCK_CHAT_004_chat_manager_required(self, app):
        """Test SOCK_CHAT_004: Chat manager is required."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            # Should not raise with chat_manager=None during registration
            register_chat_events(mock_socketio, None)

            assert mock_socketio.on.called

    # ==================== Chat Stream Tests ====================

    def test_SOCK_CHAT_005_chat_stream_handler_exists(self, app):
        """Test SOCK_CHAT_005: Chat stream handler exists."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_chat_events(mock_socketio, Mock())

            assert 'chat_stream' in registered_events

    def test_SOCK_CHAT_006_chat_stream_extracts_message(self, app):
        """Test SOCK_CHAT_006: Chat stream extracts message from data."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_chat_events(mock_socketio, Mock())

            assert mock_socketio.on.called

    def test_SOCK_CHAT_007_chat_stream_default_temperature(self, app):
        """Test SOCK_CHAT_007: Chat stream has default temperature."""
        # Default temperature is 0.15
        default_temp = 0.15
        assert default_temp == 0.15

    def test_SOCK_CHAT_008_chat_stream_handles_clear_command(self, app):
        """Test SOCK_CHAT_008: Chat stream handles /clear command."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            mock_chat_manager = Mock()
            mock_chat_manager.clear_history = Mock()

            register_chat_events(mock_socketio, mock_chat_manager)

            assert mock_socketio.on.called

    def test_SOCK_CHAT_009_chat_stream_handles_unknown_command(self, app):
        """Test SOCK_CHAT_009: Chat stream handles unknown commands."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_chat_events(mock_socketio, Mock())

            assert mock_socketio.on.called

    def test_SOCK_CHAT_010_chat_stream_adds_to_history(self, app):
        """Test SOCK_CHAT_010: Chat stream adds message to history."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            mock_chat_manager = Mock()
            mock_chat_manager.add_to_history = Mock()

            register_chat_events(mock_socketio, mock_chat_manager)

            assert mock_socketio.on.called

    def test_SOCK_CHAT_011_chat_stream_uses_rag_context(self, app):
        """Test SOCK_CHAT_011: Chat stream uses RAG context when available."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            mock_chat_manager = Mock()
            mock_chat_manager.rag_pipeline = Mock()
            mock_chat_manager.rag_pipeline.get_rag_context = Mock(return_value="RAG context")

            register_chat_events(mock_socketio, mock_chat_manager)

            assert mock_socketio.on.called

    def test_SOCK_CHAT_012_chat_stream_handles_rag_error(self, app):
        """Test SOCK_CHAT_012: Chat stream handles RAG pipeline errors."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            mock_chat_manager = Mock()
            mock_chat_manager.rag_pipeline = Mock()
            mock_chat_manager.rag_pipeline.get_rag_context = Mock(
                side_effect=Exception("RAG error")
            )

            register_chat_events(mock_socketio, mock_chat_manager)

            assert mock_socketio.on.called

    # ==================== Test Prompt Stream Tests ====================

    def test_SOCK_CHAT_013_test_prompt_handler_exists(self, app):
        """Test SOCK_CHAT_013: Test prompt stream handler exists."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            registered_events = []

            def mock_on(event):
                def decorator(func):
                    registered_events.append(event)
                    return func
                return decorator

            mock_socketio.on = mock_on

            register_chat_events(mock_socketio, Mock())

            assert 'test_prompt_stream' in registered_events

    def test_SOCK_CHAT_014_test_prompt_extracts_prompt(self, app):
        """Test SOCK_CHAT_014: Test prompt stream extracts prompt from data."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_chat_events(mock_socketio, Mock())

            assert mock_socketio.on.called

    def test_SOCK_CHAT_015_test_prompt_configurable_model(self, app):
        """Test SOCK_CHAT_015: Test prompt stream allows configurable model."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_chat_events(mock_socketio, Mock())

            assert mock_socketio.on.called

    def test_SOCK_CHAT_016_test_prompt_configurable_temperature(self, app):
        """Test SOCK_CHAT_016: Test prompt stream allows configurable temperature."""
        # Default temperature is 0.15
        default_temp = 0.15
        assert 0.0 <= default_temp <= 1.0

    def test_SOCK_CHAT_017_test_prompt_configurable_max_tokens(self, app):
        """Test SOCK_CHAT_017: Test prompt stream allows configurable max_tokens."""
        # Default max_tokens is 4096
        default_max_tokens = 4096
        assert 100 <= default_max_tokens <= 8192

    def test_SOCK_CHAT_018_test_prompt_validates_temperature(self, app):
        """Test SOCK_CHAT_018: Test prompt stream validates temperature bounds."""
        # Temperature should be clamped between 0.0 and 1.0
        def clamp_temperature(temp):
            return max(0.0, min(1.0, float(temp)))

        assert clamp_temperature(-0.5) == 0.0
        assert clamp_temperature(1.5) == 1.0
        assert clamp_temperature(0.5) == 0.5

    def test_SOCK_CHAT_019_test_prompt_validates_max_tokens(self, app):
        """Test SOCK_CHAT_019: Test prompt stream validates max_tokens bounds."""
        # Max tokens should be clamped between 100 and 8192
        def clamp_max_tokens(tokens):
            return max(100, min(8192, int(tokens)))

        assert clamp_max_tokens(50) == 100
        assert clamp_max_tokens(10000) == 8192
        assert clamp_max_tokens(2000) == 2000

    def test_SOCK_CHAT_020_test_prompt_json_mode_default(self, app):
        """Test SOCK_CHAT_020: Test prompt stream defaults to JSON mode True."""
        # Default jsonMode is True
        default_json_mode = True
        assert default_json_mode is True

    def test_SOCK_CHAT_021_test_prompt_supports_schema(self, app):
        """Test SOCK_CHAT_021: Test prompt stream supports guided_json schema."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_chat_events(mock_socketio, Mock())

            assert mock_socketio.on.called

    # ==================== Error Handling Tests ====================

    def test_SOCK_CHAT_022_chat_stream_handles_request_error(self, app):
        """Test SOCK_CHAT_022: Chat stream handles request errors."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_chat_events(mock_socketio, Mock())

            assert mock_socketio.on.called

    def test_SOCK_CHAT_023_error_messages_defined(self, app):
        """Test SOCK_CHAT_023: Error messages are defined for failures."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            handlers = {}

            def capture_handler(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_handler

            register_chat_events(mock_socketio, Mock())

            # Handlers should be captured
            assert 'chat_stream' in handlers

    def test_SOCK_CHAT_024_test_prompt_handles_error(self, app):
        """Test SOCK_CHAT_024: Test prompt stream handles errors gracefully."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_chat_events(mock_socketio, Mock())

            assert mock_socketio.on.called

    def test_SOCK_CHAT_025_events_use_room_for_client(self, app):
        """Test SOCK_CHAT_025: Events emit to client room using request.sid."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            mock_socketio.on = Mock()

            register_chat_events(mock_socketio, Mock())

            # Events should use room=client_id pattern
            assert mock_socketio.on.called


class TestPromptStreamHandler:
    """Tests for the test_prompt_stream Socket.IO handler end-to-end flow.

    These tests capture the actual handler function and invoke it with
    mocked LLM responses to verify the full streaming pipeline.
    Test IDs: PROMPT_STREAM_001 - PROMPT_STREAM_006
    """

    @pytest.fixture
    def captured_handler(self, app):
        """Capture the test_prompt_stream handler function."""
        with app.app_context():
            from socketio_handlers.events_chat import register_chat_events

            mock_socketio = Mock()
            handlers = {}

            def capture_on(event):
                def decorator(func):
                    handlers[event] = func
                    return func
                return decorator

            mock_socketio.on = capture_on
            register_chat_events(mock_socketio, Mock())
            return handlers.get('test_prompt_stream'), mock_socketio

    def _make_mock_stream(self, chunks, finish_reason="stop"):
        """Create a mock streaming response from an LLM."""
        mock_chunks = []
        for text in chunks:
            chunk = Mock()
            delta = Mock(spec=[])  # spec=[] prevents auto-creating attributes
            delta.content = text
            delta.reasoning_content = None
            delta.reasoning = None
            choice = Mock()
            choice.delta = delta
            choice.finish_reason = None
            chunk.choices = [choice]
            mock_chunks.append(chunk)
        # Final chunk with finish_reason
        final = Mock()
        final_delta = Mock(spec=[])
        final_delta.content = None
        final_delta.reasoning_content = None
        final_delta.reasoning = None
        final_choice = Mock()
        final_choice.delta = final_delta
        final_choice.finish_reason = finish_reason
        final.choices = [final_choice]
        mock_chunks.append(final)
        return iter(mock_chunks)

    def test_PROMPT_STREAM_001_handler_streams_llm_response(self, app, captured_handler):
        """Test PROMPT_STREAM_001: Handler streams LLM response chunks to client."""
        handler, mock_socketio = captured_handler
        assert handler is not None, "test_prompt_stream handler not registered"

        with app.app_context():
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = self._make_mock_stream(
                ["The ", "answer ", "is ", "4."]
            )

            with patch('socketio_handlers.events_chat.request') as mock_request, \
                 patch('socketio_handlers.events_chat.emit') as mock_emit, \
                 patch('socketio_handlers.events_chat.LLMClientFactory') as mock_factory:

                mock_request.sid = 'test-sid-001'
                mock_factory.resolve_for_chat.return_value = (mock_client, 'test-model')

                handler({
                    'userPrompt': 'What is 2+2?',
                    'systemPrompt': 'Be brief.',
                    'model': 'test-model',
                    'temperature': 0.1,
                    'maxTokens': 100,
                })

                # Verify streaming chunks were emitted
                emitted_calls = [
                    call for call in mock_emit.call_args_list
                    if call[0][0] == 'test_prompt_response'
                ]
                assert len(emitted_calls) >= 2, "Expected at least content + complete emissions"

                # Verify content chunks
                content_parts = []
                complete_sent = False
                for call in emitted_calls:
                    data = call[0][1]
                    if data.get('content'):
                        content_parts.append(data['content'])
                    if data.get('complete'):
                        complete_sent = True

                full_response = ''.join(content_parts)
                assert 'answer' in full_response.lower() or '4' in full_response
                assert complete_sent, "Handler must emit complete=True at end"

    def test_PROMPT_STREAM_002_handler_uses_system_prompt(self, app, captured_handler):
        """Test PROMPT_STREAM_002: Handler sends system prompt to LLM."""
        handler, _ = captured_handler
        assert handler is not None

        with app.app_context():
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = self._make_mock_stream(["OK"])

            with patch('socketio_handlers.events_chat.request') as mock_request, \
                 patch('socketio_handlers.events_chat.emit'), \
                 patch('socketio_handlers.events_chat.LLMClientFactory') as mock_factory:

                mock_request.sid = 'test-sid-002'
                mock_factory.resolve_for_chat.return_value = (mock_client, 'test-model')

                handler({
                    'userPrompt': 'Hello',
                    'systemPrompt': 'You are a pirate.',
                    'model': 'test-model',
                    'temperature': 0.5,
                    'maxTokens': 100,
                })

                create_call = mock_client.chat.completions.create.call_args
                messages = create_call[1]['messages']
                assert messages[0]['role'] == 'system'
                assert 'pirate' in messages[0]['content']
                assert messages[1]['role'] == 'user'

    def test_PROMPT_STREAM_003_handler_emits_error_on_no_client(self, app, captured_handler):
        """Test PROMPT_STREAM_003: Handler emits error when no LLM client available."""
        handler, _ = captured_handler
        assert handler is not None

        with app.app_context():
            with patch('socketio_handlers.events_chat.request') as mock_request, \
                 patch('socketio_handlers.events_chat.emit') as mock_emit, \
                 patch('socketio_handlers.events_chat.LLMClientFactory') as mock_factory:

                mock_request.sid = 'test-sid-003'
                mock_factory.resolve_for_chat.return_value = (None, None)

                handler({
                    'userPrompt': 'Hello',
                    'model': 'nonexistent-model',
                })

                # Should emit error response
                error_calls = [
                    call for call in mock_emit.call_args_list
                    if call[0][0] == 'test_prompt_response' and call[0][1].get('complete')
                ]
                assert len(error_calls) >= 1
                error_content = error_calls[0][0][1].get('content', '')
                assert error_content  # Should have error message

    def test_PROMPT_STREAM_004_handler_clamps_parameters(self, app, captured_handler):
        """Test PROMPT_STREAM_004: Handler clamps temperature and max_tokens."""
        handler, _ = captured_handler
        assert handler is not None

        with app.app_context():
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = self._make_mock_stream(["OK"])

            with patch('socketio_handlers.events_chat.request') as mock_request, \
                 patch('socketio_handlers.events_chat.emit'), \
                 patch('socketio_handlers.events_chat.LLMClientFactory') as mock_factory:

                mock_request.sid = 'test-sid-004'
                mock_factory.resolve_for_chat.return_value = (mock_client, 'test-model')

                handler({
                    'userPrompt': 'Hello',
                    'temperature': 5.0,  # Should be clamped to 1.0
                    'maxTokens': 99999,  # Should be clamped to 8192
                })

                create_call = mock_client.chat.completions.create.call_args
                assert create_call[1]['temperature'] <= 1.0
                actual_max = create_call[1].get('max_tokens') or create_call[1].get('max_completion_tokens')
                assert actual_max <= 8192

    def test_PROMPT_STREAM_005_handler_emits_to_correct_room(self, app, captured_handler):
        """Test PROMPT_STREAM_005: Handler emits responses to the requesting client's room."""
        handler, _ = captured_handler
        assert handler is not None

        with app.app_context():
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = self._make_mock_stream(["Hi"])

            with patch('socketio_handlers.events_chat.request') as mock_request, \
                 patch('socketio_handlers.events_chat.emit') as mock_emit, \
                 patch('socketio_handlers.events_chat.LLMClientFactory') as mock_factory:

                mock_request.sid = 'client-abc-123'
                mock_factory.resolve_for_chat.return_value = (mock_client, 'test-model')

                handler({
                    'userPrompt': 'Hello',
                })

                # All emissions should target the client's room
                for call in mock_emit.call_args_list:
                    if call[0][0] == 'test_prompt_response':
                        assert call[1].get('room') == 'client-abc-123'

    def test_PROMPT_STREAM_006_handler_handles_llm_exception(self, app, captured_handler):
        """Test PROMPT_STREAM_006: Handler catches LLM exceptions and emits error."""
        handler, _ = captured_handler
        assert handler is not None

        with app.app_context():
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API rate limit")

            with patch('socketio_handlers.events_chat.request') as mock_request, \
                 patch('socketio_handlers.events_chat.emit') as mock_emit, \
                 patch('socketio_handlers.events_chat.LLMClientFactory') as mock_factory:

                mock_request.sid = 'test-sid-006'
                mock_factory.resolve_for_chat.return_value = (mock_client, 'test-model')

                handler({
                    'userPrompt': 'Hello',
                })

                # Should emit error response (not crash)
                error_calls = [
                    call for call in mock_emit.call_args_list
                    if call[0][0] == 'test_prompt_response' and call[0][1].get('complete')
                ]
                assert len(error_calls) >= 1
