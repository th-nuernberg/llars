"""
Unit Tests: Agent Config Module
===============================

Tests for agent_modes/agent_config.py which handles configuration
access and parsing for agent chat service.

Test IDs:
- AGCFG_001 to AGCFG_020: Agent Mode Tests
- AGCFG_021 to AGCFG_040: Task Type Tests
- AGCFG_041 to AGCFG_060: Max Iterations Tests
- AGCFG_061 to AGCFG_090: Tools Configuration Tests
- AGCFG_091 to AGCFG_099: LLM Configuration Tests

Status: Implemented
"""

import pytest
import json
from unittest.mock import MagicMock, patch


class TestAgentMode:
    """
    Agent Mode Configuration Tests.

    Tests for get_agent_mode() function.
    """

    def test_AGCFG_001_get_agent_mode_standard(self, app, app_context):
        """
        [AGCFG-001] Get Agent Mode - Standard (Default)

        Should return 'standard' when agent_mode is 'standard'.
        """
        from services.chatbot.agent_modes.agent_config import get_agent_mode

        settings = MagicMock()
        settings.agent_mode = 'standard'

        result = get_agent_mode(settings)
        assert result == 'standard'

    def test_AGCFG_002_get_agent_mode_act(self, app, app_context):
        """
        [AGCFG-002] Get Agent Mode - ACT

        Should return 'act' when agent_mode is 'act'.
        """
        from services.chatbot.agent_modes.agent_config import get_agent_mode

        settings = MagicMock()
        settings.agent_mode = 'act'

        result = get_agent_mode(settings)
        assert result == 'act'

    def test_AGCFG_003_get_agent_mode_react(self, app, app_context):
        """
        [AGCFG-003] Get Agent Mode - ReAct

        Should return 'react' when agent_mode is 'react'.
        """
        from services.chatbot.agent_modes.agent_config import get_agent_mode

        settings = MagicMock()
        settings.agent_mode = 'react'

        result = get_agent_mode(settings)
        assert result == 'react'

    def test_AGCFG_004_get_agent_mode_reflact(self, app, app_context):
        """
        [AGCFG-004] Get Agent Mode - ReflAct

        Should return 'reflact' when agent_mode is 'reflact'.
        """
        from services.chatbot.agent_modes.agent_config import get_agent_mode

        settings = MagicMock()
        settings.agent_mode = 'reflact'

        result = get_agent_mode(settings)
        assert result == 'reflact'

    def test_AGCFG_005_get_agent_mode_none_settings(self, app, app_context):
        """
        [AGCFG-005] Get Agent Mode - None Settings

        Should return 'standard' when settings is None.
        """
        from services.chatbot.agent_modes.agent_config import get_agent_mode

        result = get_agent_mode(None)
        assert result == 'standard'

    def test_AGCFG_006_get_agent_mode_empty_string(self, app, app_context):
        """
        [AGCFG-006] Get Agent Mode - Empty String

        Should return 'standard' when agent_mode is empty string.
        """
        from services.chatbot.agent_modes.agent_config import get_agent_mode

        settings = MagicMock()
        settings.agent_mode = ''

        result = get_agent_mode(settings)
        assert result == 'standard'

    def test_AGCFG_007_get_agent_mode_none_value(self, app, app_context):
        """
        [AGCFG-007] Get Agent Mode - None Value

        Should return 'standard' when agent_mode is None.
        """
        from services.chatbot.agent_modes.agent_config import get_agent_mode

        settings = MagicMock()
        settings.agent_mode = None

        result = get_agent_mode(settings)
        assert result == 'standard'

    def test_AGCFG_008_get_agent_mode_missing_attribute(self, app, app_context):
        """
        [AGCFG-008] Get Agent Mode - Missing Attribute

        Should return 'standard' when agent_mode attribute doesn't exist.
        """
        from services.chatbot.agent_modes.agent_config import get_agent_mode

        settings = MagicMock(spec=[])  # No attributes

        result = get_agent_mode(settings)
        assert result == 'standard'


class TestTaskType:
    """
    Task Type Configuration Tests.

    Tests for get_task_type() function.
    """

    def test_AGCFG_021_get_task_type_lookup(self, app, app_context):
        """
        [AGCFG-021] Get Task Type - Lookup

        Should return 'lookup' when task_type is 'lookup'.
        """
        from services.chatbot.agent_modes.agent_config import get_task_type

        settings = MagicMock()
        settings.task_type = 'lookup'

        result = get_task_type(settings)
        assert result == 'lookup'

    def test_AGCFG_022_get_task_type_multihop(self, app, app_context):
        """
        [AGCFG-022] Get Task Type - Multihop

        Should return 'multihop' when task_type is 'multihop'.
        """
        from services.chatbot.agent_modes.agent_config import get_task_type

        settings = MagicMock()
        settings.task_type = 'multihop'

        result = get_task_type(settings)
        assert result == 'multihop'

    def test_AGCFG_023_get_task_type_none_settings(self, app, app_context):
        """
        [AGCFG-023] Get Task Type - None Settings

        Should return 'lookup' when settings is None.
        """
        from services.chatbot.agent_modes.agent_config import get_task_type

        result = get_task_type(None)
        assert result == 'lookup'

    def test_AGCFG_024_get_task_type_empty_string(self, app, app_context):
        """
        [AGCFG-024] Get Task Type - Empty String

        Should return 'lookup' when task_type is empty string.
        """
        from services.chatbot.agent_modes.agent_config import get_task_type

        settings = MagicMock()
        settings.task_type = ''

        result = get_task_type(settings)
        assert result == 'lookup'


class TestMaxIterations:
    """
    Max Iterations Configuration Tests.

    Tests for get_max_iterations() function.
    """

    def test_AGCFG_041_get_max_iterations_default(self, app, app_context):
        """
        [AGCFG-041] Get Max Iterations - Default Value

        Should return 5 when no explicit setting.
        """
        from services.chatbot.agent_modes.agent_config import get_max_iterations

        settings = MagicMock()
        settings.agent_max_iterations = None
        settings.task_type = 'lookup'

        result = get_max_iterations(settings)
        assert result == 5

    def test_AGCFG_042_get_max_iterations_custom(self, app, app_context):
        """
        [AGCFG-042] Get Max Iterations - Custom Value

        Should return custom value when set.
        """
        from services.chatbot.agent_modes.agent_config import get_max_iterations

        settings = MagicMock()
        settings.agent_max_iterations = 7
        settings.task_type = 'lookup'

        result = get_max_iterations(settings)
        assert result == 7

    def test_AGCFG_043_get_max_iterations_multihop_bonus(self, app, app_context):
        """
        [AGCFG-043] Get Max Iterations - Multihop Bonus

        Multihop tasks should get +2 iterations (capped at 10).
        """
        from services.chatbot.agent_modes.agent_config import get_max_iterations

        settings = MagicMock()
        settings.agent_max_iterations = 5
        settings.task_type = 'multihop'

        result = get_max_iterations(settings)
        assert result == 7  # 5 + 2

    def test_AGCFG_044_get_max_iterations_multihop_cap(self, app, app_context):
        """
        [AGCFG-044] Get Max Iterations - Multihop Cap at 10

        Multihop bonus should not exceed 10.
        """
        from services.chatbot.agent_modes.agent_config import get_max_iterations

        settings = MagicMock()
        settings.agent_max_iterations = 9
        settings.task_type = 'multihop'

        result = get_max_iterations(settings)
        assert result == 10  # min(9+2, 10)

    def test_AGCFG_045_get_max_iterations_none_settings(self, app, app_context):
        """
        [AGCFG-045] Get Max Iterations - None Settings

        Should return 5 when settings is None.
        """
        from services.chatbot.agent_modes.agent_config import get_max_iterations

        result = get_max_iterations(None)
        assert result == 5


class TestEnabledTools:
    """
    Tools Configuration Tests.

    Tests for get_enabled_tools() and _normalize_tools_value() functions.
    """

    def test_AGCFG_061_get_enabled_tools_default(self, app, app_context):
        """
        [AGCFG-061] Get Enabled Tools - Default

        Should return default tools when not configured.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        result = get_enabled_tools(None)
        assert 'rag_search' in result
        assert 'lexical_search' in result
        assert 'respond' in result

    def test_AGCFG_062_get_enabled_tools_list(self, app, app_context):
        """
        [AGCFG-062] Get Enabled Tools - List Input

        Should parse list of tool names.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        settings = MagicMock()
        settings.tools_enabled = ['rag_search', 'web_search']

        result = get_enabled_tools(settings)
        assert 'rag_search' in result
        assert 'web_search' in result

    def test_AGCFG_063_get_enabled_tools_dict(self, app, app_context):
        """
        [AGCFG-063] Get Enabled Tools - Dict Input

        Should parse dict with boolean values.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        settings = MagicMock()
        settings.tools_enabled = {
            'rag_search': True,
            'lexical_search': False,
            'web_search': True
        }

        result = get_enabled_tools(settings)
        assert 'rag_search' in result
        assert 'web_search' in result
        assert 'lexical_search' not in result

    def test_AGCFG_064_get_enabled_tools_json_list(self, app, app_context):
        """
        [AGCFG-064] Get Enabled Tools - JSON List String

        Should parse JSON list string.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        settings = MagicMock()
        settings.tools_enabled = '["rag_search", "respond"]'

        result = get_enabled_tools(settings)
        assert 'rag_search' in result
        assert 'respond' in result

    def test_AGCFG_065_get_enabled_tools_json_dict(self, app, app_context):
        """
        [AGCFG-065] Get Enabled Tools - JSON Dict String

        Should parse JSON dict string.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        settings = MagicMock()
        settings.tools_enabled = '{"rag_search": true, "web_search": false}'

        result = get_enabled_tools(settings)
        assert 'rag_search' in result
        assert 'web_search' not in result

    def test_AGCFG_066_get_enabled_tools_comma_separated(self, app, app_context):
        """
        [AGCFG-066] Get Enabled Tools - Comma Separated String

        Should parse comma-separated string.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        settings = MagicMock()
        settings.tools_enabled = 'rag_search, lexical_search, respond'

        result = get_enabled_tools(settings)
        assert 'rag_search' in result
        assert 'lexical_search' in result
        assert 'respond' in result

    def test_AGCFG_067_get_enabled_tools_normalizes_case(self, app, app_context):
        """
        [AGCFG-067] Get Enabled Tools - Case Normalization

        Should normalize tool names to lowercase.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        settings = MagicMock()
        settings.tools_enabled = ['RAG_SEARCH', 'Web_Search']

        result = get_enabled_tools(settings)
        assert 'rag_search' in result
        assert 'web_search' in result

    def test_AGCFG_068_get_enabled_tools_empty_list(self, app, app_context):
        """
        [AGCFG-068] Get Enabled Tools - Empty List

        Should return defaults for empty list.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        settings = MagicMock()
        settings.tools_enabled = []

        result = get_enabled_tools(settings)
        # Falls back to defaults
        assert 'rag_search' in result

    def test_AGCFG_069_get_enabled_tools_strips_whitespace(self, app, app_context):
        """
        [AGCFG-069] Get Enabled Tools - Whitespace Stripping

        Should strip whitespace from tool names.
        """
        from services.chatbot.agent_modes.agent_config import get_enabled_tools

        settings = MagicMock()
        settings.tools_enabled = ['  rag_search  ', ' respond ']

        result = get_enabled_tools(settings)
        assert 'rag_search' in result
        assert 'respond' in result


class TestNormalizeToolsValue:
    """
    _normalize_tools_value() Helper Tests.
    """

    def test_AGCFG_071_normalize_list_input(self, app, app_context):
        """
        [AGCFG-071] Normalize Tools - List Input

        Should handle list input directly.
        """
        from services.chatbot.agent_modes.agent_config import _normalize_tools_value

        result = _normalize_tools_value(['tool1', 'tool2'])
        assert result == ['tool1', 'tool2']

    def test_AGCFG_072_normalize_dict_input(self, app, app_context):
        """
        [AGCFG-072] Normalize Tools - Dict Input

        Should extract keys with truthy values.
        """
        from services.chatbot.agent_modes.agent_config import _normalize_tools_value

        result = _normalize_tools_value({'tool1': True, 'tool2': False, 'tool3': 1})
        assert 'tool1' in result
        assert 'tool3' in result
        assert 'tool2' not in result

    def test_AGCFG_073_normalize_json_string(self, app, app_context):
        """
        [AGCFG-073] Normalize Tools - JSON String

        Should parse valid JSON strings.
        """
        from services.chatbot.agent_modes.agent_config import _normalize_tools_value

        result = _normalize_tools_value('["a", "b"]')
        assert result == ['a', 'b']

    def test_AGCFG_074_normalize_invalid_json_falls_back(self, app, app_context):
        """
        [AGCFG-074] Normalize Tools - Invalid JSON Fallback

        Should fall back to comma-split for invalid JSON.
        """
        from services.chatbot.agent_modes.agent_config import _normalize_tools_value

        result = _normalize_tools_value('not json, but comma, separated')
        assert 'not json' in result
        assert 'but comma' in result
        assert 'separated' in result

    def test_AGCFG_075_normalize_single_value(self, app, app_context):
        """
        [AGCFG-075] Normalize Tools - Single Value

        Should handle single non-string value.
        """
        from services.chatbot.agent_modes.agent_config import _normalize_tools_value

        result = _normalize_tools_value(123)
        assert result == ['123']

    def test_AGCFG_076_normalize_filters_empty_strings(self, app, app_context):
        """
        [AGCFG-076] Normalize Tools - Filters Empty Strings

        Should filter out empty strings.
        """
        from services.chatbot.agent_modes.agent_config import _normalize_tools_value

        result = _normalize_tools_value(['tool1', '', '  ', 'tool2'])
        assert 'tool1' in result
        assert 'tool2' in result
        assert '' not in result


class TestWebSearchConfig:
    """
    Web Search Configuration Tests.

    Tests for is_web_search_enabled() and get_tavily_api_key().
    """

    def test_AGCFG_081_is_web_search_enabled_true(self, app, app_context):
        """
        [AGCFG-081] Is Web Search Enabled - True

        Should return True when enabled.
        """
        from services.chatbot.agent_modes.agent_config import is_web_search_enabled

        settings = MagicMock()
        settings.web_search_enabled = True

        result = is_web_search_enabled(settings)
        assert result is True

    def test_AGCFG_082_is_web_search_enabled_false(self, app, app_context):
        """
        [AGCFG-082] Is Web Search Enabled - False

        Should return False when disabled.
        """
        from services.chatbot.agent_modes.agent_config import is_web_search_enabled

        settings = MagicMock()
        settings.web_search_enabled = False

        result = is_web_search_enabled(settings)
        assert result is False

    def test_AGCFG_083_is_web_search_enabled_none_settings(self, app, app_context):
        """
        [AGCFG-083] Is Web Search Enabled - None Settings

        Should return False when settings is None.
        """
        from services.chatbot.agent_modes.agent_config import is_web_search_enabled

        result = is_web_search_enabled(None)
        assert result is False

    def test_AGCFG_084_get_tavily_api_key_from_settings(self, app, app_context):
        """
        [AGCFG-084] Get Tavily API Key - From Settings

        Should return key from settings.
        """
        from services.chatbot.agent_modes.agent_config import get_tavily_api_key

        settings = MagicMock()
        settings.tavily_api_key = 'test-tavily-key'

        result = get_tavily_api_key(settings)
        assert result == 'test-tavily-key'

    def test_AGCFG_085_get_tavily_api_key_from_env(self, app, app_context):
        """
        [AGCFG-085] Get Tavily API Key - From Environment

        Should fall back to environment variable.
        """
        from services.chatbot.agent_modes.agent_config import get_tavily_api_key
        import os

        settings = MagicMock()
        settings.tavily_api_key = None

        with patch.dict(os.environ, {'TAVILY_API_KEY': 'env-tavily-key'}):
            result = get_tavily_api_key(settings)
            assert result == 'env-tavily-key'

    def test_AGCFG_086_get_tavily_api_key_none(self, app, app_context):
        """
        [AGCFG-086] Get Tavily API Key - None

        Should return None when not configured.
        """
        from services.chatbot.agent_modes.agent_config import get_tavily_api_key
        import os

        # Ensure env var is not set
        env_backup = os.environ.pop('TAVILY_API_KEY', None)
        try:
            result = get_tavily_api_key(None)
            assert result is None
        finally:
            if env_backup:
                os.environ['TAVILY_API_KEY'] = env_backup


class TestBuildCompletionKwargs:
    """
    LLM Completion Configuration Tests.

    Tests for build_completion_kwargs() function.
    """

    def test_AGCFG_091_build_completion_kwargs_basic(self, app, app_context):
        """
        [AGCFG-091] Build Completion Kwargs - Basic

        Should include model, messages, temperature, top_p, stream.
        """
        from services.chatbot.agent_modes.agent_config import build_completion_kwargs

        chatbot = MagicMock()
        chatbot.model_name = 'gpt-4'
        chatbot.temperature = 0.7
        chatbot.top_p = 0.9
        chatbot.max_tokens = None

        messages = [{'role': 'user', 'content': 'Hello'}]

        result = build_completion_kwargs(chatbot, messages, stream=True)

        assert result['model'] == 'gpt-4'
        assert result['messages'] == messages
        assert result['temperature'] == 0.7
        assert result['top_p'] == 0.9
        assert result['stream'] is True
        assert 'max_tokens' not in result

    def test_AGCFG_092_build_completion_kwargs_with_max_tokens(self, app, app_context):
        """
        [AGCFG-092] Build Completion Kwargs - With Max Tokens

        Should include max_tokens when set.
        """
        from services.chatbot.agent_modes.agent_config import build_completion_kwargs

        chatbot = MagicMock()
        chatbot.model_name = 'gpt-4'
        chatbot.temperature = 0.7
        chatbot.top_p = 0.9
        chatbot.max_tokens = 2048

        messages = [{'role': 'user', 'content': 'Hello'}]

        result = build_completion_kwargs(chatbot, messages, stream=False)

        assert result['max_tokens'] == 2048
        assert result['stream'] is False

    def test_AGCFG_093_build_completion_kwargs_no_stream(self, app, app_context):
        """
        [AGCFG-093] Build Completion Kwargs - No Stream

        Should set stream=False when specified.
        """
        from services.chatbot.agent_modes.agent_config import build_completion_kwargs

        chatbot = MagicMock()
        chatbot.model_name = 'claude-3'
        chatbot.temperature = 0.5
        chatbot.top_p = 1.0
        chatbot.max_tokens = None

        messages = []

        result = build_completion_kwargs(chatbot, messages, stream=False)

        assert result['stream'] is False
