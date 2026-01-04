# mode_react.py
"""
ReAct Agent Mode Implementation.

Implements Reasoning and Acting interleaved pattern.
Shows explicit reasoning traces: THOUGHT → ACTION → OBSERVATION cycle.

Features:
    - Explicit reasoning (THOUGHT) before each action
    - Tool execution (ACTION)
    - Observation feedback (OBSERVATION)
    - Final answer detection (FINAL ANSWER)
    - Adaptive iteration (early exit on high confidence)
    - Fallback search when no action generated

Flow:
    For each iteration:
    1. Generate THOUGHT (reasoning about what to do)
    2. Generate ACTION (tool call or respond)
    3. Execute tool and get OBSERVATION
    4. Repeat until FINAL ANSWER or max iterations

Reference:
    Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models"
    https://arxiv.org/abs/2210.03629

Used by: agent_chat_service.py
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Generator, TYPE_CHECKING

from llm.openai_utils import extract_delta_text

from services.chatbot.agent_parsers import (
    parse_action,
    normalize_action_from_tool_call,
    parse_react_response,
)
from services.chatbot.agent_prompts import (
    get_react_system_prompt,
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


def chat_react(
    service: 'AgentChatService',
    message: str,
    session_id: str,
    username: Optional[str] = None,
    include_sources: bool = True,
    files: Optional[List[Dict[str, Any]]] = None,
    conversation_id: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    ReAct mode - Reasoning and Acting interleaved.

    THOUGHT → ACTION → OBSERVATION cycle with explicit reasoning.

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
        - {"status": "starting", "mode": "react"}
        - {"status": "iteration", "iteration": int, "max": int, "steps": list}
        - {"status": "thinking", "iteration": int}
        - {"status": "thought_delta", "delta": str, "iteration": int}
        - {"status": "thought", "thought": str, "iteration": int}
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

    yield {"status": "starting", "mode": "react"}

    # Initialize conversation
    conversation = service._get_or_create_conversation(session_id, username, conversation_id)
    service._save_message(conversation.id, ChatbotMessageRole.USER, message)

    # Setup iteration state
    max_iterations = service.get_max_iterations()
    all_sources = []
    steps = []
    enabled_tools = service.get_enabled_tools()

    system_prompt = get_react_system_prompt(service.chatbot, service._prompt_settings)

    for iteration in range(max_iterations):
        yield {
            "status": "iteration",
            "iteration": iteration + 1,
            "max": max_iterations,
            "steps": steps
        }

        # Build messages for this iteration
        messages = _build_react_messages(
            service, conversation, message, system_prompt,
            steps, enabled_tools
        )

        yield {"status": "thinking", "iteration": iteration + 1}

        # Stream thought and action generation
        response_text, thought, action, final_answer = yield from _stream_react_response(
            service, messages, iteration, steps
        )

        # Check source requirements
        requires_sources = service._requires_sources()
        has_observation = any(step.get("type") == "observation" for step in steps)

        # Reject final answer if sources required but no observation yet
        if final_answer and requires_sources and not has_observation:
            final_answer = None

        # Handle final answer
        if final_answer:
            yield from _handle_final_answer(
                service, db, conversation, message, final_answer,
                all_sources, steps, include_sources, iteration
            )
            return

        # Handle respond action
        if action:
            action_name, action_param = parse_action(f"ACTION: {action}")
            action_name, action_param = normalize_action_from_tool_call(
                action_name, action_param, action, enabled_tools
            )

            if action_name == "respond":
                if action_param and (not requires_sources or has_observation):
                    yield from _handle_respond_action(
                        service, db, conversation, message, action_param,
                        all_sources, steps, include_sources, iteration,
                        action_name
                    )
                    return
                action = None
                action_name = None
                action_param = None

            if not action_name:
                action = None

        # Execute action if present
        if action:
            done = yield from _execute_action(
                service, db, conversation, message, action_name, action_param,
                all_sources, steps, include_sources, iteration, enabled_tools
            )
            if done:
                return

        # Fallback search if no action and sources required
        elif not final_answer and requires_sources:
            if not any(step.get("type") == "action" for step in steps):
                done = yield from _execute_fallback_search(
                    service, db, conversation, message,
                    all_sources, steps, include_sources, iteration, enabled_tools
                )
                if done:
                    return

    # Max iterations reached
    yield from _handle_max_iterations(
        service, db, conversation, message,
        all_sources, steps, include_sources, max_iterations
    )


def _build_react_messages(
    service: 'AgentChatService',
    conversation,
    message: str,
    system_prompt: str,
    steps: List[Dict],
    enabled_tools: List[str]
) -> List[Dict]:
    """Build messages for ReAct mode iteration."""
    messages = [{"role": "system", "content": system_prompt}]

    # Add tool availability prompt
    tool_prompt = build_tool_availability_prompt(enabled_tools, service.is_web_search_enabled())
    if tool_prompt:
        messages.append({"role": "system", "content": tool_prompt})

    # Add conversation history
    messages.extend(build_agent_history_messages(
        conversation, message, getattr(service.chatbot, "max_context_messages", None)
    ))
    messages.append({"role": "user", "content": f"Frage: {message}"})

    # Add previous steps
    for step in steps:
        if step["type"] == "thought":
            messages.append({"role": "assistant", "content": f"THOUGHT: {step['content']}"})
        elif step["type"] == "action":
            messages.append({"role": "assistant", "content": f"ACTION: {step['content']}"})
        elif step["type"] == "observation":
            messages.append({"role": "user", "content": f"OBSERVATION: {step['content']}"})

    return messages


def _stream_react_response(
    service: 'AgentChatService',
    messages: List[Dict],
    iteration: int,
    steps: List[Dict]
) -> Generator[Dict[str, Any], None, tuple]:
    """
    Stream ReAct response and parse thought/action/final_answer.

    Returns tuple of (response_text, thought, action, final_answer)
    """
    response_text = ""
    last_thought = ""
    last_action = ""
    thought_finalized = False

    try:
        kwargs = build_completion_kwargs(service.chatbot, messages, stream=True)
        stream = service.llm_client.chat.completions.create(**kwargs)

        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            delta = getattr(choice, "delta", None) if choice else None
            delta_text = extract_delta_text(delta)
            if not delta_text:
                continue

            response_text += delta_text
            thought_partial, action_partial, _ = parse_react_response(response_text)

            # Stream thought delta
            if thought_partial and len(thought_partial) > len(last_thought):
                delta_chunk = thought_partial[len(last_thought):]
                last_thought = thought_partial
                yield {"status": "thought_delta", "delta": delta_chunk, "iteration": iteration + 1}

            # Handle action parsing
            if action_partial:
                if not thought_finalized and last_thought:
                    yield {"status": "thought", "thought": last_thought, "iteration": iteration + 1}
                    thought_finalized = True

                if len(action_partial) > len(last_action):
                    delta_chunk = action_partial[len(last_action):]
                    last_action = action_partial
                    yield {"status": "action_delta", "delta": delta_chunk, "iteration": iteration + 1}

    except Exception as e:
        logger.error(f"[AgentChatService] ReAct streaming failed: {e}")
        response_text = call_llm_sync(service.llm_client, service.chatbot, messages)

    # Parse final response
    thought, action, final_answer = parse_react_response(response_text)

    # Record thought if not already done
    if thought and not thought_finalized:
        steps.append({"type": "thought", "content": thought})
        yield {"status": "thought", "thought": thought, "iteration": iteration + 1}
    elif thought and thought_finalized:
        steps.append({"type": "thought", "content": thought})

    return (response_text, thought, action, final_answer)


def _handle_final_answer(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    final_answer: str,
    all_sources: List[Dict],
    steps: List[Dict],
    include_sources: bool,
    iteration: int
) -> Generator[Dict[str, Any], None, None]:
    """Handle FINAL ANSWER detection."""
    yield {"status": "final_answer"}

    for char in final_answer:
        yield {"delta": char}

    conv_info = finalize_conversation(
        db=db,
        conversation=conversation,
        message=message,
        response=final_answer,
        sources=all_sources,
        include_sources=include_sources,
        mode="react",
        iterations=iteration + 1,
        reasoning_steps=steps,
        save_message_func=service._save_message,
        maybe_set_title_func=service._maybe_set_conversation_title
    )

    yield build_done_event(
        response=final_answer,
        sources=all_sources,
        include_sources=include_sources,
        mode="react",
        iterations=iteration + 1,
        reasoning_steps=steps,
        conversation_info=conv_info
    )


def _handle_respond_action(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    response: str,
    all_sources: List[Dict],
    steps: List[Dict],
    include_sources: bool,
    iteration: int,
    action_name: str
) -> Generator[Dict[str, Any], None, None]:
    """Handle respond action as final answer."""
    normalized_action_content = f'{action_name}("{response}")'
    steps.append({
        "type": "action",
        "content": normalized_action_content,
        "action_name": action_name,
        "action_param": response
    })
    yield {"status": "action", "action": action_name, "param": response, "iteration": iteration + 1}
    yield {"status": "final_answer"}

    for char in response:
        yield {"delta": char}

    conv_info = finalize_conversation(
        db=db,
        conversation=conversation,
        message=message,
        response=response,
        sources=all_sources,
        include_sources=include_sources,
        mode="react",
        iterations=iteration + 1,
        reasoning_steps=steps,
        save_message_func=service._save_message,
        maybe_set_title_func=service._maybe_set_conversation_title
    )

    yield build_done_event(
        response=response,
        sources=all_sources,
        include_sources=include_sources,
        mode="react",
        iterations=iteration + 1,
        reasoning_steps=steps,
        conversation_info=conv_info
    )


def _execute_action(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    action_name: str,
    action_param: str,
    all_sources: List[Dict],
    steps: List[Dict],
    include_sources: bool,
    iteration: int,
    enabled_tools: List[str]
) -> Generator[Dict[str, Any], None, bool]:
    """Execute action and handle observation. Returns True if done."""
    normalized_action_content = f'{action_name}("{action_param}")' if action_param else action_name
    steps.append({
        "type": "action",
        "content": normalized_action_content,
        "action_name": action_name,
        "action_param": action_param
    })
    yield {"status": "action", "action": action_name, "param": action_param, "iteration": iteration + 1}

    # Execute tool
    result, sources = service._tool_executor.execute_tool(action_name, action_param, message, enabled_tools)
    all_sources.extend(sources)

    # Record observation
    steps.append({"type": "observation", "content": result, "sources_found": len(sources)})
    preview = result[:300] if result else ""
    for chunk in stream_preview_chunks(preview):
        yield {"status": "observation_delta", "delta": chunk, "iteration": iteration + 1}
    yield {"status": "observation", "result_preview": preview, "iteration": iteration + 1}

    # Check for adaptive exit
    if sources and check_high_confidence(sources):
        done = yield from _handle_adaptive_exit(
            service, db, conversation, message, result, sources,
            all_sources, steps, include_sources, iteration
        )
        return done

    return False


def _execute_fallback_search(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    all_sources: List[Dict],
    steps: List[Dict],
    include_sources: bool,
    iteration: int,
    enabled_tools: List[str]
) -> Generator[Dict[str, Any], None, bool]:
    """Execute fallback search when no action generated. Returns True if done."""
    fallback_action = None
    if "rag_search" in enabled_tools:
        fallback_action = "rag_search"
    elif "lexical_search" in enabled_tools:
        fallback_action = "lexical_search"

    if not fallback_action:
        return False

    action_param = message
    steps.append({
        "type": "action",
        "content": fallback_action,
        "action_name": fallback_action,
        "action_param": action_param,
        "auto": True
    })
    yield {"status": "action", "action": fallback_action, "param": action_param, "iteration": iteration + 1}

    # Execute tool
    result, sources = service._tool_executor.execute_tool(fallback_action, action_param, message, enabled_tools)
    all_sources.extend(sources)

    # Record observation
    steps.append({
        "type": "observation",
        "content": result,
        "sources_found": len(sources),
        "auto": True
    })
    preview = result[:300] if result else ""
    for chunk in stream_preview_chunks(preview):
        yield {"status": "observation_delta", "delta": chunk, "iteration": iteration + 1}
    yield {"status": "observation", "result_preview": preview, "iteration": iteration + 1}

    # Check for adaptive exit
    if sources and check_high_confidence(sources):
        done = yield from _handle_adaptive_exit(
            service, db, conversation, message, result, sources,
            all_sources, steps, include_sources, iteration
        )
        return done

    return False


def _handle_adaptive_exit(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    observation: str,
    sources: List[Dict],
    all_sources: List[Dict],
    steps: List[Dict],
    include_sources: bool,
    iteration: int
) -> Generator[Dict[str, Any], None, bool]:
    """Handle adaptive iteration - early exit on high confidence."""
    logger.info(f"[AgentChatService] ReAct adaptive iteration: high confidence on iteration {iteration + 1}")
    yield {"status": "adaptive_iteration", "iteration": iteration + 1, "reason": "high_confidence"}

    steps.append({
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
            steps,
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
        mode="react",
        iterations=iteration + 1,
        reasoning_steps=steps,
        save_message_func=service._save_message,
        maybe_set_title_func=service._maybe_set_conversation_title,
        adaptive_exit=True
    )

    yield build_done_event(
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="react",
        iterations=iteration + 1,
        reasoning_steps=steps,
        conversation_info=conv_info,
        adaptive_exit=True
    )

    return True


def _handle_max_iterations(
    service: 'AgentChatService',
    db,
    conversation,
    message: str,
    all_sources: List[Dict],
    steps: List[Dict],
    include_sources: bool,
    max_iterations: int
) -> Generator[Dict[str, Any], None, None]:
    """Handle max iterations reached."""
    yield {"status": "max_iterations_reached"}

    final_response = generate_final_response(
        service.llm_client,
        service.chatbot,
        message,
        steps,
        service._build_citation_instructions()
    )

    conv_info = finalize_conversation(
        db=db,
        conversation=conversation,
        message=message,
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="react",
        iterations=max_iterations,
        reasoning_steps=steps,
        save_message_func=service._save_message,
        maybe_set_title_func=service._maybe_set_conversation_title
    )

    yield build_done_event(
        response=final_response,
        sources=all_sources,
        include_sources=include_sources,
        mode="react",
        iterations=max_iterations,
        reasoning_steps=steps,
        conversation_info=conv_info
    )
