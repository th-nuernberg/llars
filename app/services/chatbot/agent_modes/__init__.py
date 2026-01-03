# agent_modes/__init__.py
"""
Agent Modes Package.

Contains implementations of different LLM agent reasoning patterns:
- Standard: Single-shot response without reasoning
- ACT: Action-only without explicit reasoning traces
- ReAct: Reasoning + Acting interleaved
- ReflAct: Goal-state reflection before each action

Module Structure:
    - agent_config.py: Configuration access and parsing
        - get_agent_mode, get_task_type, get_max_iterations
        - get_enabled_tools, is_web_search_enabled
        - build_completion_kwargs

    - agent_helpers.py: Shared helper methods
        - call_llm_sync, stream_llm_response
        - finalize_conversation, build_done_event
        - generate_adaptive_response_stream
        - generate_final_response
        - run_agent_sync

    - mode_standard.py: Standard mode implementation
        - chat_standard_stream

    - mode_act.py: ACT mode implementation
        - chat_act

    - mode_react.py: ReAct mode implementation
        - chat_react

    - mode_reflact.py: ReflAct mode implementation
        - chat_reflact

Usage:
    from services.chatbot.agent_modes import (
        get_agent_mode,
        chat_standard_stream,
        chat_act,
        chat_react,
        chat_reflact,
    )

Author: LLARS Team
Date: November 2025 (refactored January 2026)
"""

# Configuration
from .agent_config import (
    get_agent_mode,
    get_task_type,
    get_max_iterations,
    get_enabled_tools,
    is_web_search_enabled,
    get_tavily_api_key,
    build_completion_kwargs,
)

# Helpers
from .agent_helpers import (
    call_llm_sync,
    stream_llm_response,
    finalize_conversation,
    build_done_event,
    generate_adaptive_response_stream,
    generate_final_response,
    run_agent_sync,
)

# Mode implementations
from .mode_standard import chat_standard_stream
from .mode_act import chat_act
from .mode_react import chat_react
from .mode_reflact import chat_reflact

__all__ = [
    # Configuration
    'get_agent_mode',
    'get_task_type',
    'get_max_iterations',
    'get_enabled_tools',
    'is_web_search_enabled',
    'get_tavily_api_key',
    'build_completion_kwargs',

    # Helpers
    'call_llm_sync',
    'stream_llm_response',
    'finalize_conversation',
    'build_done_event',
    'generate_adaptive_response_stream',
    'generate_final_response',
    'run_agent_sync',

    # Mode implementations
    'chat_standard_stream',
    'chat_act',
    'chat_react',
    'chat_reflact',
]
