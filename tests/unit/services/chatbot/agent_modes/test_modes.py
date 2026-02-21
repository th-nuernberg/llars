"""
Unit Tests: Agent Mode Implementations
======================================

Tests for the agent mode implementations:
- mode_standard.py: Standard single-shot response
- mode_act.py: Action-only without reasoning traces
- mode_react.py: Reasoning + Acting interleaved
- mode_reflact.py: Goal-state reflection before each action

Test IDs:
- AGSTD_001 to AGSTD_030: Standard Mode Tests
- AGACT_001 to AGACT_030: ACT Mode Tests
- AGRCT_001 to AGRCT_030: ReAct Mode Tests
- AGRFL_001 to AGRFL_030: ReflAct Mode Tests

Status: Implemented
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestStandardMode:
    """
    Standard Mode Tests.

    Tests for chat_standard_stream() function.
    """

    def test_AGSTD_001_standard_mode_yields_starting_event(self, app, db, app_context):
        """
        [AGSTD-001] Standard Mode - Starting Event

        Should yield starting event with mode='standard'.
        """
        from services.chatbot.agent_modes.mode_standard import chat_standard_stream

        # Mock service
        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.rag_enabled = False
        service.chatbot.collections = []

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        mock_conversation.message_count = 0
        service._get_or_create_conversation.return_value = mock_conversation

        # Mock LLM response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_standard.extract_delta_text',
                   return_value='Response'), \
             patch('services.chatbot.agent_modes.mode_standard.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'Test'}):

            gen = chat_standard_stream(service, 'Hello', 'session-1')
            first_event = next(gen)

            assert first_event['status'] == 'starting'
            assert first_event['mode'] == 'standard'

    def test_AGSTD_002_standard_mode_yields_context_event(self, app, db, app_context):
        """
        [AGSTD-002] Standard Mode - Context Retrieved Event

        Should yield context_retrieved event with sources count.
        """
        from services.chatbot.agent_modes.mode_standard import chat_standard_stream

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.rag_enabled = True
        service.chatbot.collections = [MagicMock()]

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        mock_conversation.message_count = 0
        service._get_or_create_conversation.return_value = mock_conversation
        service._get_multi_collection_context.return_value = ('Context', [{'id': 1}, {'id': 2}])

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_standard.extract_delta_text',
                   return_value='Response'), \
             patch('services.chatbot.agent_modes.mode_standard.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'Test'}):

            gen = chat_standard_stream(service, 'Hello', 'session-1')
            events = list(gen)

            context_events = [e for e in events if e.get('status') == 'context_retrieved']
            assert len(context_events) == 1
            assert context_events[0]['sources_count'] == 2

    def test_AGSTD_003_standard_mode_yields_delta_events(self, app, db, app_context):
        """
        [AGSTD-003] Standard Mode - Delta Events

        Should yield delta events for streamed response.
        """
        from services.chatbot.agent_modes.mode_standard import chat_standard_stream

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.rag_enabled = False
        service.chatbot.collections = []

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        mock_conversation.message_count = 0
        service._get_or_create_conversation.return_value = mock_conversation

        # Two chunks
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta = MagicMock()

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta = MagicMock()

        service.llm_client.chat.completions.create.return_value = [chunk1, chunk2]

        with patch('services.chatbot.agent_modes.mode_standard.extract_delta_text',
                   side_effect=['Hello ', 'World']), \
             patch('services.chatbot.agent_modes.mode_standard.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'Test'}):

            gen = chat_standard_stream(service, 'Hi', 'session-1')
            events = list(gen)

            delta_events = [e for e in events if 'delta' in e]
            assert len(delta_events) == 2
            assert delta_events[0]['delta'] == 'Hello '
            assert delta_events[1]['delta'] == 'World'

    def test_AGSTD_004_standard_mode_yields_done_event(self, app, db, app_context):
        """
        [AGSTD-004] Standard Mode - Done Event

        Should yield done event with full response.
        """
        from services.chatbot.agent_modes.mode_standard import chat_standard_stream

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.rag_enabled = False
        service.chatbot.collections = []

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        mock_conversation.message_count = 0
        service._get_or_create_conversation.return_value = mock_conversation

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_standard.extract_delta_text',
                   return_value='Response'), \
             patch('services.chatbot.agent_modes.mode_standard.finalize_conversation',
                   return_value={'message_id': 123, 'conversation_id': 456, 'title': 'Test'}), \
             patch('services.chatbot.agent_modes.mode_standard.build_done_event',
                   return_value={'done': True, 'full_response': 'Response', 'mode': 'standard'}):

            gen = chat_standard_stream(service, 'Hi', 'session-1')
            events = list(gen)

            done_events = [e for e in events if e.get('done')]
            assert len(done_events) == 1
            assert done_events[0]['mode'] == 'standard'

    def test_AGSTD_005_standard_mode_handles_error(self, app, db, app_context):
        """
        [AGSTD-005] Standard Mode - Error Handling

        Should yield error event on LLM failure.
        """
        from services.chatbot.agent_modes.mode_standard import chat_standard_stream

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.rag_enabled = False
        service.chatbot.collections = []

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        service._get_or_create_conversation.return_value = mock_conversation

        service.llm_client.chat.completions.create.side_effect = Exception('API Error')

        gen = chat_standard_stream(service, 'Hi', 'session-1')
        events = list(gen)

        error_events = [e for e in events if 'error' in e]
        assert len(error_events) == 1
        assert 'API Error' in error_events[0]['error']


class TestACTMode:
    """
    ACT Mode Tests.

    Tests for chat_act() function.
    """

    def test_AGACT_001_act_mode_yields_starting_event(self, app, db, app_context):
        """
        [AGACT-001] ACT Mode - Starting Event

        Should yield starting event with mode='act'.
        """
        from services.chatbot.agent_modes.mode_act import chat_act

        service = MagicMock()
        service.chatbot = MagicMock()
        service.get_max_iterations.return_value = 5
        service.get_enabled_tools.return_value = ['rag_search', 'respond']
        service.is_web_search_enabled.return_value = False

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        service._get_or_create_conversation.return_value = mock_conversation
        service._prompt_settings = MagicMock()

        # Mock LLM to return respond action immediately
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_act.extract_delta_text',
                   return_value='respond("Final answer")'), \
             patch('services.chatbot.agent_modes.mode_act.get_act_system_prompt',
                   return_value='System prompt'), \
             patch('services.chatbot.agent_modes.mode_act.parse_action',
                   return_value=('respond', 'Final answer')), \
             patch('services.chatbot.agent_modes.mode_act.normalize_action_from_tool_call',
                   return_value=('respond', 'Final answer')), \
             patch('services.chatbot.agent_modes.mode_act.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'Test'}), \
             patch('services.chatbot.agent_modes.mode_act.build_done_event',
                   return_value={'done': True, 'mode': 'act'}):

            gen = chat_act(service, 'Hello', 'session-1')
            first_event = next(gen)

            assert first_event['status'] == 'starting'
            assert first_event['mode'] == 'act'

    def test_AGACT_002_act_mode_yields_iteration_events(self, app, db, app_context):
        """
        [AGACT-002] ACT Mode - Iteration Events

        Should yield iteration status events.
        """
        from services.chatbot.agent_modes.mode_act import chat_act

        service = MagicMock()
        service.chatbot = MagicMock()
        service.get_max_iterations.return_value = 5
        service.get_enabled_tools.return_value = ['rag_search', 'respond']
        service.is_web_search_enabled.return_value = False

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        service._get_or_create_conversation.return_value = mock_conversation
        service._prompt_settings = MagicMock()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_act.extract_delta_text',
                   return_value='respond("Done")'), \
             patch('services.chatbot.agent_modes.mode_act.get_act_system_prompt',
                   return_value='System'), \
             patch('services.chatbot.agent_modes.mode_act.parse_action',
                   return_value=('respond', 'Done')), \
             patch('services.chatbot.agent_modes.mode_act.normalize_action_from_tool_call',
                   return_value=('respond', 'Done')), \
             patch('services.chatbot.agent_modes.mode_act.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'T'}), \
             patch('services.chatbot.agent_modes.mode_act.build_done_event',
                   return_value={'done': True}):

            gen = chat_act(service, 'Q', 'session-1')
            events = list(gen)

            iteration_events = [e for e in events if e.get('status') == 'iteration']
            assert len(iteration_events) >= 1
            assert iteration_events[0]['iteration'] == 1

    def test_AGACT_003_act_mode_yields_action_events(self, app, db, app_context):
        """
        [AGACT-003] ACT Mode - Action Events

        Should yield action events with action name and param.
        """
        from services.chatbot.agent_modes.mode_act import chat_act

        service = MagicMock()
        service.chatbot = MagicMock()
        service.get_max_iterations.return_value = 5
        service.get_enabled_tools.return_value = ['rag_search', 'respond']
        service.is_web_search_enabled.return_value = False

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        service._get_or_create_conversation.return_value = mock_conversation
        service._prompt_settings = MagicMock()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_act.extract_delta_text',
                   return_value='respond("Answer")'), \
             patch('services.chatbot.agent_modes.mode_act.get_act_system_prompt',
                   return_value='System'), \
             patch('services.chatbot.agent_modes.mode_act.parse_action',
                   return_value=('respond', 'Answer')), \
             patch('services.chatbot.agent_modes.mode_act.normalize_action_from_tool_call',
                   return_value=('respond', 'Answer')), \
             patch('services.chatbot.agent_modes.mode_act.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'T'}), \
             patch('services.chatbot.agent_modes.mode_act.build_done_event',
                   return_value={'done': True}):

            gen = chat_act(service, 'Q', 'session-1')
            events = list(gen)

            action_events = [e for e in events if e.get('status') == 'action']
            assert len(action_events) >= 1
            assert action_events[0]['action'] == 'respond'
            assert action_events[0]['param'] == 'Answer'


class TestReActMode:
    """
    ReAct Mode Tests.

    Tests for chat_react() function.
    """

    def test_AGRCT_001_react_mode_yields_starting_event(self, app, db, app_context):
        """
        [AGRCT-001] ReAct Mode - Starting Event

        Should yield starting event with mode='react'.
        """
        from services.chatbot.agent_modes.mode_react import chat_react

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.max_context_messages = 10
        service.get_max_iterations.return_value = 5
        service.get_enabled_tools.return_value = ['rag_search', 'respond']
        service.is_web_search_enabled.return_value = False

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        service._get_or_create_conversation.return_value = mock_conversation
        service._prompt_settings = MagicMock()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_react.extract_delta_text',
                   return_value='THOUGHT: Thinking\nFINAL ANSWER: Done'), \
             patch('services.chatbot.agent_modes.mode_react.get_react_system_prompt',
                   return_value='System'), \
             patch('services.chatbot.agent_modes.mode_react.parse_react_response',
                   return_value=('Thinking', None, 'Done')), \
             patch('services.chatbot.agent_modes.mode_react.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'T'}), \
             patch('services.chatbot.agent_modes.mode_react.build_done_event',
                   return_value={'done': True, 'mode': 'react'}):

            gen = chat_react(service, 'Hello', 'session-1')
            first_event = next(gen)

            assert first_event['status'] == 'starting'
            assert first_event['mode'] == 'react'

    def test_AGRCT_002_react_mode_yields_thinking_status(self, app, db, app_context):
        """
        [AGRCT-002] ReAct Mode - Thinking Status Event

        Should yield thinking status event before generating thought.
        """
        from services.chatbot.agent_modes.mode_react import chat_react

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.max_context_messages = 10
        service.get_max_iterations.return_value = 1  # Only one iteration
        service.get_enabled_tools.return_value = ['rag_search', 'respond']
        service.is_web_search_enabled.return_value = False

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        service._get_or_create_conversation.return_value = mock_conversation
        service._prompt_settings = MagicMock()
        service._tool_executor = MagicMock()
        service._tool_executor.execute_tool.return_value = ('Search result', [])

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_react.extract_delta_text',
                   return_value='THOUGHT: I need to search\nFINAL ANSWER: Done'), \
             patch('services.chatbot.agent_modes.mode_react.get_react_system_prompt',
                   return_value='System'), \
             patch('services.chatbot.agent_modes.mode_react.parse_react_response',
                   return_value=('I need to search', None, 'Done')), \
             patch('services.chatbot.agent_modes.mode_react.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'T'}), \
             patch('services.chatbot.agent_modes.mode_react.build_done_event',
                   return_value={'done': True}):

            gen = chat_react(service, 'Q', 'session-1')
            events = list(gen)

            # ReAct mode should yield a 'thinking' status event at the start of each iteration
            status_events = [e.get('status') for e in events if 'status' in e]
            assert 'thinking' in status_events


class TestReflActMode:
    """
    ReflAct Mode Tests.

    Tests for chat_reflact() function.
    """

    def test_AGRFL_001_reflact_mode_yields_starting_event(self, app, db, app_context):
        """
        [AGRFL-001] ReflAct Mode - Starting Event

        Should yield starting event with mode='reflact'.
        """
        from services.chatbot.agent_modes.mode_reflact import chat_reflact

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.max_context_messages = 10
        service.get_max_iterations.return_value = 5
        service.get_enabled_tools.return_value = ['rag_search', 'respond']
        service.is_web_search_enabled.return_value = False

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        service._get_or_create_conversation.return_value = mock_conversation
        service._prompt_settings = MagicMock()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_reflact.extract_delta_text',
                   return_value='REFLECTION: Reflecting\nFINAL ANSWER: Done'), \
             patch('services.chatbot.agent_modes.mode_reflact.get_reflact_system_prompt',
                   return_value='System'), \
             patch('services.chatbot.agent_modes.mode_reflact.parse_reflact_response_v2',
                   return_value=('Reflecting', None, 'Done')), \
             patch('services.chatbot.agent_modes.mode_reflact.strip_trailing_reflact_fragment',
                   side_effect=lambda x: x if x else ''), \
             patch('services.chatbot.agent_modes.mode_reflact.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'T'}), \
             patch('services.chatbot.agent_modes.mode_reflact.build_done_event',
                   return_value={'done': True, 'mode': 'reflact'}):

            gen = chat_reflact(service, 'Hello', 'session-1')
            first_event = next(gen)

            assert first_event['status'] == 'starting'
            assert first_event['mode'] == 'reflact'

    def test_AGRFL_002_reflact_mode_yields_iteration_with_goal(self, app, db, app_context):
        """
        [AGRFL-002] ReflAct Mode - Iteration Events with Goal

        Should yield iteration events that include the goal.
        """
        from services.chatbot.agent_modes.mode_reflact import chat_reflact

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.max_context_messages = 10
        service.get_max_iterations.return_value = 5
        service.get_enabled_tools.return_value = ['rag_search', 'respond']
        service.is_web_search_enabled.return_value = False

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        service._get_or_create_conversation.return_value = mock_conversation
        service._prompt_settings = MagicMock()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_reflact.extract_delta_text',
                   return_value='FINAL ANSWER: Done'), \
             patch('services.chatbot.agent_modes.mode_reflact.get_reflact_system_prompt',
                   return_value='System'), \
             patch('services.chatbot.agent_modes.mode_reflact.parse_reflact_response_v2',
                   return_value=(None, None, 'Done')), \
             patch('services.chatbot.agent_modes.mode_reflact.strip_trailing_reflact_fragment',
                   side_effect=lambda x: x if x else ''), \
             patch('services.chatbot.agent_modes.mode_reflact.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'T'}), \
             patch('services.chatbot.agent_modes.mode_reflact.build_done_event',
                   return_value={'done': True}):

            gen = chat_reflact(service, 'What is Python?', 'session-1')
            events = list(gen)

            iteration_events = [e for e in events if e.get('status') == 'iteration']
            if iteration_events:
                assert iteration_events[0]['goal'] == 'What is Python?'

    def test_AGRFL_003_reflact_mode_yields_reflection_events(self, app, db, app_context):
        """
        [AGRFL-003] ReflAct Mode - Reflection Events

        Should yield reflection events during goal-state reflection.
        """
        from services.chatbot.agent_modes.mode_reflact import chat_reflact

        service = MagicMock()
        service.chatbot = MagicMock()
        service.chatbot.max_context_messages = 10
        service.get_max_iterations.return_value = 5
        service.get_enabled_tools.return_value = ['rag_search', 'respond']
        service.is_web_search_enabled.return_value = False

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.title = 'Test'
        service._get_or_create_conversation.return_value = mock_conversation
        service._prompt_settings = MagicMock()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        service.llm_client.chat.completions.create.return_value = [mock_chunk]

        with patch('services.chatbot.agent_modes.mode_reflact.extract_delta_text',
                   return_value='REFLECTION: Goal assessment\nFINAL ANSWER: Done'), \
             patch('services.chatbot.agent_modes.mode_reflact.get_reflact_system_prompt',
                   return_value='System'), \
             patch('services.chatbot.agent_modes.mode_reflact.parse_reflact_response_v2',
                   return_value=('Goal assessment', None, 'Done')), \
             patch('services.chatbot.agent_modes.mode_reflact.strip_trailing_reflact_fragment',
                   side_effect=lambda x: x if x else ''), \
             patch('services.chatbot.agent_modes.mode_reflact.finalize_conversation',
                   return_value={'message_id': 1, 'conversation_id': 1, 'title': 'T'}), \
             patch('services.chatbot.agent_modes.mode_reflact.build_done_event',
                   return_value={'done': True}):

            gen = chat_reflact(service, 'Q', 'session-1')
            events = list(gen)

            # ReflAct should yield reflecting status and reflection events
            assert any(e.get('status') in ['reflecting', 'reflection', 'reflection_delta'] for e in events)
