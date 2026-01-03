"""
Unit Tests: Agent Helpers Module
================================

Tests for agent_modes/agent_helpers.py which provides shared helper
methods used across all agent modes.

Test IDs:
- AGHLP_001 to AGHLP_020: LLM Call Tests
- AGHLP_021 to AGHLP_040: Finalization Tests
- AGHLP_041 to AGHLP_060: Done Event Tests
- AGHLP_061 to AGHLP_080: Adaptive Response Tests
- AGHLP_081 to AGHLP_099: Sync Agent Execution Tests

Status: Implemented
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestCallLLMSync:
    """
    Synchronous LLM Call Tests.

    Tests for call_llm_sync() function.
    """

    def test_AGHLP_001_call_llm_sync_success(self, app, app_context):
        """
        [AGHLP-001] Call LLM Sync - Successful Response

        Should return extracted message text.
        """
        from services.chatbot.agent_modes.agent_helpers import call_llm_sync

        llm_client = MagicMock()
        chatbot = MagicMock()
        chatbot.model_name = 'gpt-4'
        chatbot.temperature = 0.7
        chatbot.top_p = 0.9
        chatbot.max_tokens = None

        # Mock response
        mock_message = MagicMock()
        mock_message.content = 'Test response'
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        llm_client.chat.completions.create.return_value = mock_response

        messages = [{'role': 'user', 'content': 'Hello'}]

        with patch('services.chatbot.agent_modes.agent_helpers.extract_message_text',
                   return_value='Test response'):
            result = call_llm_sync(llm_client, chatbot, messages)

        assert result == 'Test response'
        llm_client.chat.completions.create.assert_called_once()

    def test_AGHLP_002_call_llm_sync_empty_choices(self, app, app_context):
        """
        [AGHLP-002] Call LLM Sync - Empty Choices

        Should return empty string when no choices in response.
        """
        from services.chatbot.agent_modes.agent_helpers import call_llm_sync

        llm_client = MagicMock()
        chatbot = MagicMock()
        chatbot.model_name = 'gpt-4'
        chatbot.temperature = 0.7
        chatbot.top_p = 0.9
        chatbot.max_tokens = None

        mock_response = MagicMock()
        mock_response.choices = []
        llm_client.chat.completions.create.return_value = mock_response

        messages = [{'role': 'user', 'content': 'Hello'}]

        result = call_llm_sync(llm_client, chatbot, messages)

        assert result == ''

    def test_AGHLP_003_call_llm_sync_exception(self, app, app_context):
        """
        [AGHLP-003] Call LLM Sync - Exception Handling

        Should return empty string on exception.
        """
        from services.chatbot.agent_modes.agent_helpers import call_llm_sync

        llm_client = MagicMock()
        chatbot = MagicMock()
        chatbot.model_name = 'gpt-4'
        chatbot.temperature = 0.7
        chatbot.top_p = 0.9
        chatbot.max_tokens = None

        llm_client.chat.completions.create.side_effect = Exception('API Error')

        messages = [{'role': 'user', 'content': 'Hello'}]

        result = call_llm_sync(llm_client, chatbot, messages)

        assert result == ''


class TestStreamLLMResponse:
    """
    Streaming LLM Response Tests.

    Tests for stream_llm_response() function.
    """

    def test_AGHLP_011_stream_llm_response_success(self, app, app_context):
        """
        [AGHLP-011] Stream LLM Response - Successful Streaming

        Should yield delta text chunks and return accumulated text.
        """
        from services.chatbot.agent_modes.agent_helpers import stream_llm_response

        llm_client = MagicMock()
        chatbot = MagicMock()
        chatbot.model_name = 'gpt-4'
        chatbot.temperature = 0.7
        chatbot.top_p = 0.9
        chatbot.max_tokens = None

        # Mock streaming response
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta = MagicMock()

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta = MagicMock()

        llm_client.chat.completions.create.return_value = [chunk1, chunk2]

        messages = [{'role': 'user', 'content': 'Hello'}]

        with patch('services.chatbot.agent_modes.agent_helpers.extract_delta_text',
                   side_effect=['Hello ', 'World']):
            gen = stream_llm_response(llm_client, chatbot, messages)
            chunks = list(gen)

        assert chunks == ['Hello ', 'World']

    def test_AGHLP_012_stream_llm_response_empty_delta(self, app, app_context):
        """
        [AGHLP-012] Stream LLM Response - Empty Delta

        Should skip empty delta text.
        """
        from services.chatbot.agent_modes.agent_helpers import stream_llm_response

        llm_client = MagicMock()
        chatbot = MagicMock()
        chatbot.model_name = 'gpt-4'
        chatbot.temperature = 0.7
        chatbot.top_p = 0.9
        chatbot.max_tokens = None

        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta = MagicMock()

        llm_client.chat.completions.create.return_value = [chunk]

        messages = []

        with patch('services.chatbot.agent_modes.agent_helpers.extract_delta_text',
                   return_value=''):
            gen = stream_llm_response(llm_client, chatbot, messages)
            chunks = list(gen)

        assert chunks == []

    def test_AGHLP_013_stream_llm_response_exception(self, app, app_context):
        """
        [AGHLP-013] Stream LLM Response - Exception Handling

        Should handle exceptions gracefully.
        """
        from services.chatbot.agent_modes.agent_helpers import stream_llm_response

        llm_client = MagicMock()
        chatbot = MagicMock()
        chatbot.model_name = 'gpt-4'
        chatbot.temperature = 0.7
        chatbot.top_p = 0.9
        chatbot.max_tokens = None

        llm_client.chat.completions.create.side_effect = Exception('Stream Error')

        messages = []

        gen = stream_llm_response(llm_client, chatbot, messages)
        chunks = list(gen)

        assert chunks == []


class TestBuildDoneEvent:
    """
    Done Event Builder Tests.

    Tests for build_done_event() function.
    """

    def test_AGHLP_041_build_done_event_basic(self, app, app_context):
        """
        [AGHLP-041] Build Done Event - Basic Structure

        Should return complete done event dict.
        """
        from services.chatbot.agent_modes.agent_helpers import build_done_event

        conversation_info = {
            'message_id': 123,
            'conversation_id': 456,
            'title': 'Test Conversation'
        }

        result = build_done_event(
            response='Final answer',
            sources=[{'id': 1, 'content': 'Source text'}],
            include_sources=True,
            mode='react',
            iterations=3,
            reasoning_steps=[{'type': 'thought', 'content': 'Thinking...'}],
            conversation_info=conversation_info
        )

        assert result['done'] is True
        assert result['full_response'] == 'Final answer'
        assert len(result['sources']) == 1
        assert result['mode'] == 'react'
        assert result['iterations'] == 3
        assert result['conversation_id'] == 456
        assert result['title'] == 'Test Conversation'
        assert result['message_id'] == 123

    def test_AGHLP_042_build_done_event_no_sources(self, app, app_context):
        """
        [AGHLP-042] Build Done Event - Without Sources

        Should return empty sources when include_sources is False.
        """
        from services.chatbot.agent_modes.agent_helpers import build_done_event

        conversation_info = {
            'message_id': 1,
            'conversation_id': 2,
            'title': 'Test'
        }

        result = build_done_event(
            response='Response',
            sources=[{'id': 1}],
            include_sources=False,
            mode='act',
            iterations=1,
            reasoning_steps=[],
            conversation_info=conversation_info
        )

        assert result['sources'] == []

    def test_AGHLP_043_build_done_event_adaptive_exit(self, app, app_context):
        """
        [AGHLP-043] Build Done Event - With Adaptive Exit

        Should include adaptive_exit flag.
        """
        from services.chatbot.agent_modes.agent_helpers import build_done_event

        conversation_info = {
            'message_id': 1,
            'conversation_id': 2,
            'title': 'Test'
        }

        result = build_done_event(
            response='Response',
            sources=[],
            include_sources=True,
            mode='react',
            iterations=2,
            reasoning_steps=[],
            conversation_info=conversation_info,
            adaptive_exit=True
        )

        assert result.get('adaptive_exit') is True

    def test_AGHLP_044_build_done_event_with_goal(self, app, app_context):
        """
        [AGHLP-044] Build Done Event - With Goal

        Should include goal for reflact mode.
        """
        from services.chatbot.agent_modes.agent_helpers import build_done_event

        conversation_info = {
            'message_id': 1,
            'conversation_id': 2,
            'title': 'Test'
        }

        result = build_done_event(
            response='Response',
            sources=[],
            include_sources=True,
            mode='reflact',
            iterations=3,
            reasoning_steps=[],
            conversation_info=conversation_info,
            goal='Answer the user question about X'
        )

        assert result.get('goal') == 'Answer the user question about X'

    def test_AGHLP_045_build_done_event_no_optional_fields(self, app, app_context):
        """
        [AGHLP-045] Build Done Event - Without Optional Fields

        Should not include adaptive_exit or goal when not set.
        """
        from services.chatbot.agent_modes.agent_helpers import build_done_event

        conversation_info = {
            'message_id': 1,
            'conversation_id': 2,
            'title': 'Test'
        }

        result = build_done_event(
            response='Response',
            sources=[],
            include_sources=True,
            mode='standard',
            iterations=1,
            reasoning_steps=[],
            conversation_info=conversation_info
        )

        assert 'adaptive_exit' not in result
        assert 'goal' not in result


class TestRunAgentSync:
    """
    Synchronous Agent Execution Tests.

    Tests for run_agent_sync() function.
    """

    def test_AGHLP_081_run_agent_sync_success(self, app, app_context):
        """
        [AGHLP-081] Run Agent Sync - Successful Completion

        Should consume generator and return final result.
        """
        from services.chatbot.agent_modes.agent_helpers import run_agent_sync

        def mock_generator():
            yield {'status': 'starting'}
            yield {'status': 'iteration', 'iteration': 1}
            yield {'delta': 'Hello'}
            yield {
                'done': True,
                'full_response': 'Hello World',
                'sources': [{'id': 1}],
                'conversation_id': 123,
                'title': 'Test',
                'message_id': 456,
                'mode': 'react',
                'iterations': 2,
                'reasoning_steps': [{'type': 'thought'}]
            }

        result = run_agent_sync(
            agent_generator=mock_generator(),
            session_id='session-123',
            conversation_id=123,
            mode='react',
            task_type='lookup'
        )

        assert result['response'] == 'Hello World'
        assert result['conversation_id'] == 123
        assert result['session_id'] == 'session-123'
        assert result['mode'] == 'react'
        assert result['iterations'] == 2

    def test_AGHLP_082_run_agent_sync_no_done_event(self, app, app_context):
        """
        [AGHLP-082] Run Agent Sync - No Done Event

        Should return fallback when generator completes without done event.
        """
        from services.chatbot.agent_modes.agent_helpers import run_agent_sync

        def mock_generator():
            yield {'status': 'starting'}
            yield {'status': 'error', 'message': 'Something went wrong'}
            # Generator ends without done event

        result = run_agent_sync(
            agent_generator=mock_generator(),
            session_id='session-123',
            conversation_id=None,
            mode='act',
            task_type='multihop',
            unknown_answer='I cannot answer that.'
        )

        assert result['response'] == 'I cannot answer that.'
        assert result['sources'] == []
        assert result['iterations'] == 0

    def test_AGHLP_083_run_agent_sync_with_files(self, app, app_context):
        """
        [AGHLP-083] Run Agent Sync - With Files

        Should count processed files.
        """
        from services.chatbot.agent_modes.agent_helpers import run_agent_sync

        def mock_generator():
            yield {'done': True, 'full_response': 'Done', 'sources': [],
                   'conversation_id': 1, 'title': 'T', 'message_id': 1,
                   'mode': 'standard', 'iterations': 1}

        result = run_agent_sync(
            agent_generator=mock_generator(),
            session_id='s1',
            conversation_id=1,
            mode='standard',
            task_type='lookup',
            files=[{'name': 'file1.pdf'}, {'name': 'file2.txt'}]
        )

        assert result['files_processed'] == 2

    def test_AGHLP_084_run_agent_sync_measures_time(self, app, app_context):
        """
        [AGHLP-084] Run Agent Sync - Response Time Measurement

        Should measure response time in milliseconds.
        """
        from services.chatbot.agent_modes.agent_helpers import run_agent_sync

        def mock_generator():
            yield {'done': True, 'full_response': 'Done', 'sources': [],
                   'conversation_id': 1, 'title': 'T', 'message_id': 1,
                   'mode': 'standard', 'iterations': 1}

        result = run_agent_sync(
            agent_generator=mock_generator(),
            session_id='s1',
            conversation_id=1,
            mode='standard',
            task_type='lookup'
        )

        assert 'response_time_ms' in result
        assert isinstance(result['response_time_ms'], int)
        assert result['response_time_ms'] >= 0

    def test_AGHLP_085_run_agent_sync_extracts_reasoning_steps(self, app, app_context):
        """
        [AGHLP-085] Run Agent Sync - Extracts Reasoning Steps

        Should extract reasoning steps from done event.
        """
        from services.chatbot.agent_modes.agent_helpers import run_agent_sync

        def mock_generator():
            yield {
                'done': True,
                'full_response': 'Answer',
                'sources': [],
                'conversation_id': 1,
                'title': 'T',
                'message_id': 1,
                'mode': 'react',
                'iterations': 3,
                'reasoning_steps': [
                    {'type': 'thought', 'content': 'I need to search'},
                    {'type': 'action', 'action': 'rag_search', 'param': 'query'},
                    {'type': 'observation', 'content': 'Found results'}
                ]
            }

        result = run_agent_sync(
            agent_generator=mock_generator(),
            session_id='s1',
            conversation_id=1,
            mode='react',
            task_type='multihop'
        )

        assert len(result['reasoning_steps']) == 3
        assert result['reasoning_steps'][0]['type'] == 'thought'


class TestFinalizeConversation:
    """
    Conversation Finalization Tests.

    Tests for finalize_conversation() function.
    """

    def test_AGHLP_021_finalize_conversation_basic(self, app, db, app_context):
        """
        [AGHLP-021] Finalize Conversation - Basic Flow

        Should save message and update conversation.
        """
        from services.chatbot.agent_modes.agent_helpers import finalize_conversation

        # Mock conversation
        conversation = MagicMock()
        conversation.id = 1
        conversation.message_count = 0
        conversation.title = 'Test Conversation'

        # Mock save function
        mock_message = MagicMock()
        mock_message.id = 123
        save_func = MagicMock(return_value=mock_message)

        # Mock title function
        title_func = MagicMock()

        result = finalize_conversation(
            db=db,
            conversation=conversation,
            message='User question',
            response='Assistant answer',
            sources=[{'id': 1}],
            include_sources=True,
            mode='react',
            iterations=2,
            reasoning_steps=[{'type': 'thought'}],
            save_message_func=save_func,
            maybe_set_title_func=title_func
        )

        assert result['message_id'] == 123
        assert result['conversation_id'] == 1
        assert result['title'] == 'Test Conversation'
        assert conversation.message_count == 2

    def test_AGHLP_022_finalize_conversation_with_retrieval_time(self, app, db, app_context):
        """
        [AGHLP-022] Finalize Conversation - With Retrieval Time

        Should include retrieval_time_ms in metadata.
        """
        from services.chatbot.agent_modes.agent_helpers import finalize_conversation

        conversation = MagicMock()
        conversation.id = 1
        conversation.message_count = 0
        conversation.title = 'Test'

        mock_message = MagicMock()
        mock_message.id = 1
        save_func = MagicMock(return_value=mock_message)

        finalize_conversation(
            db=db,
            conversation=conversation,
            message='Q',
            response='A',
            sources=[],
            include_sources=True,
            mode='standard',
            iterations=1,
            reasoning_steps=[],
            save_message_func=save_func,
            maybe_set_title_func=MagicMock(),
            retrieval_time_ms=150
        )

        # Check the stream_metadata passed to save_func
        call_kwargs = save_func.call_args
        assert call_kwargs[1]['stream_metadata']['retrieval_time_ms'] == 150

    def test_AGHLP_023_finalize_conversation_adaptive_exit(self, app, db, app_context):
        """
        [AGHLP-023] Finalize Conversation - Adaptive Exit

        Should include adaptive_exit in metadata.
        """
        from services.chatbot.agent_modes.agent_helpers import finalize_conversation

        conversation = MagicMock()
        conversation.id = 1
        conversation.message_count = 0
        conversation.title = 'Test'

        mock_message = MagicMock()
        mock_message.id = 1
        save_func = MagicMock(return_value=mock_message)

        finalize_conversation(
            db=db,
            conversation=conversation,
            message='Q',
            response='A',
            sources=[],
            include_sources=True,
            mode='react',
            iterations=2,
            reasoning_steps=[],
            save_message_func=save_func,
            maybe_set_title_func=MagicMock(),
            adaptive_exit=True
        )

        call_kwargs = save_func.call_args
        assert call_kwargs[1]['stream_metadata']['adaptive_exit'] is True

    def test_AGHLP_024_finalize_conversation_no_sources(self, app, db, app_context):
        """
        [AGHLP-024] Finalize Conversation - Without Sources

        Should pass empty sources when include_sources is False.
        """
        from services.chatbot.agent_modes.agent_helpers import finalize_conversation

        conversation = MagicMock()
        conversation.id = 1
        conversation.message_count = 0
        conversation.title = 'Test'

        mock_message = MagicMock()
        mock_message.id = 1
        save_func = MagicMock(return_value=mock_message)

        finalize_conversation(
            db=db,
            conversation=conversation,
            message='Q',
            response='A',
            sources=[{'id': 1}, {'id': 2}],
            include_sources=False,
            mode='act',
            iterations=1,
            reasoning_steps=[],
            save_message_func=save_func,
            maybe_set_title_func=MagicMock()
        )

        call_kwargs = save_func.call_args
        assert call_kwargs[1]['rag_sources'] == []
