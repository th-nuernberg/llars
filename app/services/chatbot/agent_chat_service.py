# agent_chat_service.py
"""
Agent Chat Service - Implements advanced LLM agent patterns.

Extends ChatService with support for various agent reasoning modes:
- Standard: Single-shot response (no reasoning)
- ACT: Action-only without explicit reasoning traces
- ReAct: Reasoning + Acting interleaved (Thought → Action → Observation)
- ReflAct: Goal-state reflection before each action

Task Types:
- Lookup: Simple fact retrieval (1-2 iterations)
- Multi-hop: Complex reasoning requiring multiple steps

Architecture:
    This service coordinates the agent modes by delegating to:
    - agent_modes/agent_config.py: Configuration access
    - agent_modes/agent_helpers.py: Shared helper methods
    - agent_modes/mode_standard.py: Standard mode
    - agent_modes/mode_act.py: ACT mode
    - agent_modes/mode_react.py: ReAct mode
    - agent_modes/mode_reflact.py: ReflAct mode

    Additionally uses:
    - agent_tools.py: Tool execution (RAG, lexical, web search)
    - agent_parsers.py: Response parsing (THOUGHT, ACTION, FINAL ANSWER)
    - agent_prompts.py: System prompt builders

Usage:
    from services.chatbot.agent_chat_service import AgentChatService

    service = AgentChatService(chatbot_id=123)
    for event in service.chat_agent(message, session_id):
        if event.get("delta"):
            print(event["delta"], end="")

Author: LLARS Team
Date: November 2025 (refactored January 2026)
"""

import logging
from typing import List, Dict, Any, Optional, Generator

from services.chatbot.chat_service import ChatService
from services.chatbot.agent_tools import AgentToolExecutor

# Import mode implementations
from services.chatbot.agent_modes import (
    # Configuration
    get_agent_mode as _get_agent_mode,
    get_task_type as _get_task_type,
    get_max_iterations as _get_max_iterations,
    get_enabled_tools as _get_enabled_tools,
    is_web_search_enabled as _is_web_search_enabled,
    get_tavily_api_key as _get_tavily_api_key,
    build_completion_kwargs,
    # Helpers
    run_agent_sync,
    # Modes
    chat_standard_stream,
    chat_act,
    chat_react,
    chat_reflact,
)

logger = logging.getLogger(__name__)


class AgentChatService(ChatService):
    """
    Extended ChatService with agent reasoning patterns.

    Supports multiple agent modes (standard, act, react, reflact) for
    different reasoning and tool-use patterns.

    Attributes:
        _prompt_settings: Cached ChatbotPromptSettings instance
        _tool_executor: AgentToolExecutor for tool calls

    Example:
        >>> service = AgentChatService(chatbot_id=123)
        >>> for event in service.chat_agent("What is RAG?", "session-1"):
        ...     if event.get("delta"):
        ...         print(event["delta"], end="")
        ...     elif event.get("done"):
        ...         print(f"\\nSources: {len(event['sources'])}")
    """

    def __init__(self, chatbot_id: int):
        """
        Initialize agent chat service.

        Args:
            chatbot_id: ID of the chatbot to use
        """
        super().__init__(chatbot_id)
        self._prompt_settings = self._get_prompt_settings()
        self._tool_executor = AgentToolExecutor(self)

    # =========================================================================
    # CONFIGURATION ACCESSORS
    # =========================================================================

    def get_agent_mode(self) -> str:
        """
        Get the configured agent mode for this chatbot.

        Returns:
            Agent mode: 'standard', 'act', 'react', or 'reflact'
        """
        return _get_agent_mode(self._prompt_settings)

    def get_task_type(self) -> str:
        """
        Get the configured task type for this chatbot.

        Returns:
            Task type: 'lookup' or 'multihop'
        """
        return _get_task_type(self._prompt_settings)

    def get_max_iterations(self) -> int:
        """
        Get max iterations based on task type.

        Returns:
            Maximum number of agent iterations (5-10)
        """
        return _get_max_iterations(self._prompt_settings)

    def get_enabled_tools(self) -> List[str]:
        """
        Get list of enabled tools for agent modes.

        Returns:
            List of tool names (e.g., ['rag_search', 'lexical_search', 'respond'])
        """
        return _get_enabled_tools(self._prompt_settings)

    def is_web_search_enabled(self) -> bool:
        """
        Check if web search is enabled.

        Returns:
            True if web search is enabled
        """
        return _is_web_search_enabled(self._prompt_settings)

    def get_tavily_api_key(self) -> Optional[str]:
        """
        Get Tavily API key if configured.

        Returns:
            API key string or None
        """
        return _get_tavily_api_key(self._prompt_settings)

    def _build_completion_kwargs(
        self,
        messages: List[Dict],
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Build kwargs for LLM completion.

        Args:
            messages: List of message dicts
            stream: Whether to stream the response

        Returns:
            Kwargs dict for llm_client.chat.completions.create()
        """
        return build_completion_kwargs(self.chatbot, messages, stream)

    # =========================================================================
    # MAIN AGENT METHODS
    # =========================================================================

    def chat_agent(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Main agent chat method - routes to appropriate mode.

        Yields status updates and final response based on the configured
        agent mode (standard, act, react, or reflact).

        Args:
            message: User's input message
            session_id: Session identifier for conversation tracking
            username: Optional username for new conversations
            include_sources: Whether to include RAG sources in response
            files: Optional list of file attachments
            conversation_id: Optional existing conversation ID

        Yields:
            Dict events including:
            - {"status": str}: Status updates during processing
            - {"delta": str}: Response text chunks
            - {"done": True, ...}: Final completion event

        Example:
            >>> for event in service.chat_agent("Hello", "sess-1"):
            ...     if "delta" in event:
            ...         print(event["delta"], end="")
        """
        mode = self.get_agent_mode()

        if mode == 'standard':
            yield from chat_standard_stream(
                self, message, session_id, username,
                include_sources, files, conversation_id
            )
        elif mode == 'act':
            yield from chat_act(
                self, message, session_id, username,
                include_sources, files, conversation_id
            )
        elif mode == 'react':
            yield from chat_react(
                self, message, session_id, username,
                include_sources, files, conversation_id
            )
        elif mode == 'reflact':
            yield from chat_reflact(
                self, message, session_id, username,
                include_sources, files, conversation_id
            )
        else:
            # Default to standard mode
            yield from chat_standard_stream(
                self, message, session_id, username,
                include_sources, files, conversation_id
            )

    def chat_agent_sync(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run agent chat synchronously and return the final result.

        Useful for REST fallback when streaming is not available.

        Args:
            message: User's input message
            session_id: Session identifier
            username: Optional username
            include_sources: Whether to include sources
            files: Optional file attachments
            conversation_id: Optional conversation ID

        Returns:
            Dict containing:
            - response: Final response text
            - sources: List of RAG sources
            - conversation_id: Conversation ID
            - session_id: Session ID
            - title: Conversation title
            - message_id: Message ID
            - tokens: Token usage (input/output)
            - response_time_ms: Response time in milliseconds
            - mode: Agent mode used
            - task_type: Task type
            - iterations: Number of iterations
            - reasoning_steps: List of reasoning steps
            - files_processed: Number of files processed

        Example:
            >>> result = service.chat_agent_sync("What is RAG?", "sess-1")
            >>> print(result["response"])
        """
        generator = self.chat_agent(
            message=message,
            session_id=session_id,
            username=username,
            include_sources=include_sources,
            files=files,
            conversation_id=conversation_id
        )

        return run_agent_sync(
            agent_generator=generator,
            session_id=session_id,
            conversation_id=conversation_id,
            mode=self.get_agent_mode(),
            task_type=self.get_task_type(),
            files=files,
            unknown_answer=self.get_unknown_answer()
        )
