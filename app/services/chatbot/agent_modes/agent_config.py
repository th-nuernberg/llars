# agent_config.py
"""
Agent Configuration Module.

Provides configuration access and parsing for agent chat service.
Handles extraction and normalization of agent settings from chatbot
and prompt configuration.

Configuration Sources:
    - ChatbotPromptSettings: Agent mode, task type, max iterations, tools
    - Chatbot: Model settings, temperature, max_tokens
    - Environment: API keys (Tavily)

Supported Agent Modes:
    - standard: Single-shot response without reasoning
    - act: Action-only without explicit reasoning traces
    - react: Reasoning + Acting interleaved (Thought → Action → Observation)
    - reflact: Goal-state reflection before each action

Used by: agent_chat_service.py, mode_*.py
"""

from __future__ import annotations

import json
import logging
import os
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from services.llm.llm_execution_service import LLMExecutionService

if TYPE_CHECKING:
    from db.models.chatbot import Chatbot, ChatbotPromptSettings

logger = logging.getLogger(__name__)


# =============================================================================
# AGENT MODE CONFIGURATION
# =============================================================================

def get_agent_mode(prompt_settings: Optional['ChatbotPromptSettings']) -> str:
    """
    Get the configured agent mode for this chatbot.

    Args:
        prompt_settings: ChatbotPromptSettings instance or None

    Returns:
        Agent mode string: 'standard', 'act', 'react', or 'reflact'

    Example:
        >>> mode = get_agent_mode(chatbot.prompt_settings)
        >>> print(mode)
        'react'
    """
    if prompt_settings:
        return getattr(prompt_settings, 'agent_mode', 'standard') or 'standard'
    return 'standard'


def get_task_type(prompt_settings: Optional['ChatbotPromptSettings']) -> str:
    """
    Get the configured task type for this chatbot.

    Task types influence the number of iterations allowed:
    - lookup: Simple fact retrieval (fewer iterations)
    - multihop: Complex reasoning requiring multiple steps (more iterations)

    Args:
        prompt_settings: ChatbotPromptSettings instance or None

    Returns:
        Task type string: 'lookup' or 'multihop'
    """
    if prompt_settings:
        return getattr(prompt_settings, 'task_type', 'lookup') or 'lookup'
    return 'lookup'


def get_max_iterations(prompt_settings: Optional['ChatbotPromptSettings']) -> int:
    """
    Get max iterations based on task type.

    Multi-hop tasks are allowed additional iterations (up to 10 max).

    Args:
        prompt_settings: ChatbotPromptSettings instance or None

    Returns:
        Maximum number of agent iterations (5-10)

    Example:
        >>> # Lookup task
        >>> get_max_iterations(lookup_settings)
        5
        >>> # Multihop task
        >>> get_max_iterations(multihop_settings)
        7
    """
    if prompt_settings:
        base = getattr(prompt_settings, 'agent_max_iterations', 5) or 5
    else:
        base = 5

    # Multi-hop tasks allow more iterations
    task_type = get_task_type(prompt_settings)
    if task_type == 'multihop':
        return min(base + 2, 10)
    return base


# =============================================================================
# TOOL CONFIGURATION
# =============================================================================

def get_enabled_tools(prompt_settings: Optional['ChatbotPromptSettings']) -> List[str]:
    """
    Get list of enabled tools for agent modes.

    Parses the tools_enabled field which can be:
    - List of tool names
    - Dict with tool names as keys and boolean values
    - JSON string encoding a list or dict
    - Comma-separated string

    Args:
        prompt_settings: ChatbotPromptSettings instance or None

    Returns:
        List of normalized (lowercase) tool names

    Default Tools:
        ['rag_search', 'lexical_search', 'respond']

    Example:
        >>> get_enabled_tools(settings)
        ['rag_search', 'lexical_search', 'web_search', 'respond']
    """
    if not prompt_settings:
        return ['rag_search', 'lexical_search', 'respond']

    tools = getattr(prompt_settings, 'tools_enabled', None)
    if not tools:
        return ['rag_search', 'lexical_search', 'respond']

    normalized = _normalize_tools_value(tools)
    if normalized:
        return [t.lower() for t in normalized]

    return ['rag_search', 'lexical_search', 'respond']


def _normalize_tools_value(tools: Any) -> List[str]:
    """
    Normalize tools configuration value to a list of strings.

    Handles various input formats:
    - List: ['rag_search', 'lexical_search']
    - Dict: {'rag_search': True, 'lexical_search': False}
    - JSON string: '["rag_search"]' or '{"rag_search": true}'
    - Comma-separated string: 'rag_search, lexical_search'

    Args:
        tools: Raw tools configuration value

    Returns:
        List of tool name strings
    """
    if isinstance(tools, list):
        return [str(t).strip() for t in tools if str(t).strip()]

    if isinstance(tools, dict):
        return [str(k).strip() for k, v in tools.items() if v and str(k).strip()]

    if isinstance(tools, str):
        # Try JSON parsing first
        try:
            decoded = json.loads(tools)
            if isinstance(decoded, list):
                return [str(t).strip() for t in decoded if str(t).strip()]
            if isinstance(decoded, dict):
                return [str(k).strip() for k, v in decoded.items() if v and str(k).strip()]
        except (json.JSONDecodeError, TypeError):
            pass

        # Fall back to comma-separated
        return [t.strip() for t in tools.split(",") if t.strip()]

    # Single value
    single = str(tools).strip()
    return [single] if single else []


# =============================================================================
# WEB SEARCH CONFIGURATION
# =============================================================================

def is_web_search_enabled(prompt_settings: Optional['ChatbotPromptSettings']) -> bool:
    """
    Check if web search is enabled.

    Args:
        prompt_settings: ChatbotPromptSettings instance or None

    Returns:
        True if web search is enabled
    """
    if prompt_settings:
        return bool(getattr(prompt_settings, 'web_search_enabled', False))
    return False


def get_tavily_api_key(prompt_settings: Optional['ChatbotPromptSettings']) -> Optional[str]:
    """
    Get Tavily API key if configured.

    First checks the prompt settings, then falls back to environment variable.

    Args:
        prompt_settings: ChatbotPromptSettings instance or None

    Returns:
        Tavily API key string or None if not configured
    """
    if prompt_settings:
        key = getattr(prompt_settings, 'tavily_api_key', None)
        if key:
            return key
    return os.environ.get('TAVILY_API_KEY')


# =============================================================================
# LLM CONFIGURATION
# =============================================================================

def build_completion_kwargs(
    chatbot: 'Chatbot',
    messages: List[Dict],
    stream: bool = True,
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build kwargs for LLM completion.

    Only includes max_tokens if explicitly set on the chatbot
    to avoid overriding model defaults.

    Args:
        chatbot: Chatbot model instance
        messages: List of message dicts for the completion
        stream: Whether to stream the response

    Returns:
        Dict of kwargs for llm_client.chat.completions.create()

    Example:
        >>> kwargs = build_completion_kwargs(chatbot, messages, stream=True)
        >>> response = llm_client.chat.completions.create(**kwargs)
    """
    return LLMExecutionService.build_chat_completion_params(
        model=model_id or chatbot.model_name,
        messages=messages,
        stream=stream,
        temperature=chatbot.temperature,
        top_p=chatbot.top_p,
        max_tokens=chatbot.max_tokens,
    )
