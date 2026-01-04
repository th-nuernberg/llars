# mode_act.py
"""
ACT Agent Mode Implementation.

Implements Action-only mode without explicit reasoning traces.
Faster than ReAct but less interpretable.

Features:
    - Tool execution (RAG search, lexical search, web search)
    - Iterative action-observation loop
    - Adaptive iteration (early exit on high confidence)
    - Final response generation

Flow:
    For each iteration:
    1. Generate ACTION
    2. Execute tool and get OBSERVATION
    3. Check for respond action or high confidence
    4. Repeat until done or max iterations

Actions:
    - rag_search(query): Semantic search in RAG collections
    - lexical_search(query): Keyword-based search
    - web_search(query): Tavily web search (if enabled)
    - respond(answer): Provide final answer

Used by: agent_chat_service.py
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Generator, TYPE_CHECKING

from llm.openai_utils import extract_delta_text

from services.chatbot.agent_parsers import parse_action, normalize_action_from_tool_call
from services.chatbot.agent_prompts import (
    get_act_system_prompt,
    build_tool_availability_prompt,
    build_agent_history_messages,
)
from services.chatbot.agent_tools import check_high_confidence, stream_preview_chunks

from .agent_config import build_completion_kwargs
from .agent_helpers import (
    call_llm_sync,
    finalize_conversation,
    build_done_event,
    generate_adaptive_response_stream,
    generate_final_response,
)

if TYPE_CHECKING:
    from services.chatbot.agent_chat_service import AgentChatService

logger = logging.getLogger(__name__)


def chat_act(
    service: 'AgentChatService',
    message: str,
    session_id: str,
    username: Optional[str] = None,
    include_sources: bool = True,
    files: Optional[List[Dict[str, Any]]] = None,
    conversation_id: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    ACT mode - Action-only without explicit reasoning.

    Faster but less interpretable than ReAct. The agent directly
    produces actions without showing its reasoning process.

    Args:
        service: AgentChatService instance
        message: User's input message
        session_id: Session identifier
        username: Optional username
        include_sources: Whether to include RAG sources in response
        files: Optional list of file attachments
        conversation_id: Optional existing conversation ID

    Yields:
        Status events and delta chunks during iteration

    Events Yielded:
        - {"status": "starting", "mode": "act"}
        - {"status": "iteration", "iteration": int, "max": int}
        - {"status": "getting_action", "iteration": int}
        - {"status": "action_delta", "delta": str, "iteration": int}
        - {"status": "action", "action": str, "param": str, "iteration": int}
        - {"status": "observation_delta", "delta": str, "iteration": int}
        - {"status": "observation", "result_preview": str, "iteration": int}
        - {"status": "adaptive_iteration", "iteration": int, "reason": str}
        - {"status": "final_answer"}
        - {"delta": str} (multiple)
        - {"done": True, ...}
    """
    from db.database import db
    from db.models.chatbot import ChatbotMessageRole

    yield {"status": "starting", "mode": "act"}

    # Initialize conversation
    conversation = service._get_or_create_conversation(session_id, username, conversation_id)
    service._save_message(conversation.id, ChatbotMessageRole.USER, message)

    # Setup iteration state
    max_iterations = service.get_max_iterations()
    all_sources = []
    observations = []
    reasoning_steps = []
    enabled_tools = service.get_enabled_tools()

    system_prompt = get_act_system_prompt(service.chatbot, service._prompt_settings)

    for iteration in range(max_iterations):
        yield {"status": "iteration", "iteration": iteration + 1, "max": max_iterations}

        # Build messages for this iteration
        messages = _build_act_messages(
            service, conversation, message, system_prompt,
            observations, enabled_tools
        )

        yield {"status": "getting_action", "iteration": iteration + 1}

        # Stream action generation
        action_text = ""
        try:
            kwargs = build_completion_kwargs(service.chatbot, messages, stream=True)
            stream = service.llm_client.chat.completions.create(**kwargs)

            for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                delta = getattr(choice, "delta", None) if choice else None
                delta_text = extract_delta_text(delta)
                if delta_text:
                    action_text += delta_text
                    yield {"status": "action_delta", "delta": delta_text, "iteration": iteration + 1}

        except Exception as e:
            logger.error(f"[AgentChatService] ACT action streaming failed: {e}")
            action_text = call_llm_sync(service.llm_client, service.chatbot, messages)

        # Parse action
        action, param = parse_action(action_text)
        action, param = normalize_action_from_tool_call(action, param, action_text, enabled_tools)
        yield {"status": "action", "action": action, "param": param, "iteration": iteration + 1}

        # Record action in reasoning steps
        action_content = f'{action}("{param}")' if param else action
        normalized_action_text = f'ACTION: {action_content}'
        reasoning_steps.append({
            "type": "action",
            "action": action,
            "param": param,
            "content": action_content
        })

        # Check for respond action (final answer)
        if action == "respond":
            yield from _handle_respond_action(
                service, db, conversation, message, param,
                all_sources, reasoning_steps, include_sources, iteration
            )
            return

        # Execute tool
        result, sources = service._tool_executor.execute_tool(action, param, message, enabled_tools)
        all_sources.extend(sources)

        # Record observation
        observations.append({
            "action": normalized_action_text,
            "result": result
        })
        reasoning_steps.append({
            "type": "observation",
            "content": result or ""
        })

        # Stream observation preview
        preview = result[:200] if result else ""
        for chunk in stream_preview_chunks(preview):
            yield {"status": "observation_delta", "delta": chunk, "iteration": iteration + 1}
        yield {"status": "observation", "result_preview": preview, "iteration": iteration + 1}

        # Check for adaptive iteration (high confidence early exit)
        if sources and check_high_confidence(sources):
            done_event = yield from _handle_adaptive_exit(
                service, db, conversation, message, result, sources,
                all_sources, reasoning_steps, include_sources, iteration
            )
            if done_event:
                return

    # Max iterations reached - generate final response
    yield from _handle_max_iterations(
        service, db, conversation, message, observations,
        all_sources, reasoning_steps, include_sources, max_iterations
    )


def _build_act_messages(
    service: 'AgentChatService',
    conversation,
    message: str,
    system_prompt: str,
    observations: List[Dict],
    enabled_tools: List[str]
) -> List[Dict]:
    """Build messages for ACT mode iteration."""
    messages = [{"role": "system", "content": system_prompt}]

    # Add tool availability prompt
    tool_prompt = build_tool_availability_prompt(enabled_tools, service.is_web_search_enabled())
    if tool_prompt:
        messages.append({"role": "system", "content": tool_prompt})

    # Add conversation history
    messages.extend(build_agent_history_messages(
        conversation, message, getattr(service.chatbot, "max_context_messages", None)
    ))
    messages.append({"role": "user", "content": message})

    # Add previous action-observation pairs
    for obs in observations:
        messages.append({"role": "assistant", "content": obs["action"]})
        messages.append({"role": "user", "content": f"OBSERVATION: {obs['result']}"})

    return messages


def _handle_respond_action(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    final_response: str,
    all_sources: List[Dict],
    reasoning_steps: List[Dict],
    include_sources: bool,
    iteration: int
) -> Generator[Dict[str, Any], None, None]:
    """Handle respond action - stream final answer and finalize."""
    yield {"status": "final_answer"}

    # Stream the response character by character
    for char in final_response:
        yield {"delta": char}

    # Finalize conversation
    conv_info = finalize_conversation(
        db=db,
        conversation=conversation,
        message=message,
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="act",
        iterations=iteration + 1,
        reasoning_steps=reasoning_steps,
        save_message_func=service._save_message,
        maybe_set_title_func=service._maybe_set_conversation_title
    )

    yield build_done_event(
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="act",
        iterations=iteration + 1,
        reasoning_steps=reasoning_steps,
        conversation_info=conv_info
    )


def _handle_adaptive_exit(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    observation: str,
    sources: List[Dict],
    all_sources: List[Dict],
    reasoning_steps: List[Dict],
    include_sources: bool,
    iteration: int
) -> Generator[Dict[str, Any], None, Optional[Dict]]:
    """Handle adaptive iteration - early exit on high confidence."""
    logger.info(f"[AgentChatService] ACT adaptive iteration: high confidence on iteration {iteration + 1}")
    yield {"status": "adaptive_iteration", "iteration": iteration + 1, "reason": "high_confidence"}

    reasoning_steps.append({
        "type": "adaptive",
        "content": "Hohe Konfidenz erreicht - generiere finale Antwort"
    })

    # Generate adaptive response
    final_response = ""
    response_gen = generate_adaptive_response_stream(
        service.llm_client,
        service.chatbot,
        service._prompt_settings,
        message,
        sources,
        observation
    )
    for event in response_gen:
        if "delta" in event:
            final_response += event["delta"]
        yield event

    # Fallback if streaming failed
    if not final_response:
        final_response = generate_final_response(
            service.llm_client,
            service.chatbot,
            message,
            reasoning_steps,
            service._build_citation_instructions()
        )

    # Finalize conversation
    conv_info = finalize_conversation(
        db=db,
        conversation=conversation,
        message=message,
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="act",
        iterations=iteration + 1,
        reasoning_steps=reasoning_steps,
        save_message_func=service._save_message,
        maybe_set_title_func=service._maybe_set_conversation_title,
        adaptive_exit=True
    )

    yield build_done_event(
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="act",
        iterations=iteration + 1,
        reasoning_steps=reasoning_steps,
        conversation_info=conv_info,
        adaptive_exit=True
    )

    return {"done": True}


def _handle_max_iterations(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    observations: List[Dict],
    all_sources: List[Dict],
    reasoning_steps: List[Dict],
    include_sources: bool,
    max_iterations: int
) -> Generator[Dict[str, Any], None, None]:
    """Handle max iterations reached - generate final response."""
    yield {"status": "max_iterations_reached"}

    final_response = generate_final_response(
        service.llm_client,
        service.chatbot,
        message,
        observations,  # Use observations for context
        service._build_citation_instructions()
    )

    # Finalize conversation
    conv_info = finalize_conversation(
        db=db,
        conversation=conversation,
        message=message,
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="act",
        iterations=max_iterations,
        reasoning_steps=reasoning_steps,
        save_message_func=service._save_message,
        maybe_set_title_func=service._maybe_set_conversation_title
    )

    yield build_done_event(
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="act",
        iterations=max_iterations,
        reasoning_steps=reasoning_steps,
        conversation_info=conv_info
    )
