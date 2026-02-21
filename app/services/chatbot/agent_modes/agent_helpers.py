# agent_helpers.py
"""
Agent Helper Methods Module.

Provides shared helper methods and common patterns used across all agent modes:
- LLM response generation (sync and streaming)
- Conversation finalization and message saving
- Adaptive iteration handling
- Final response generation

These helpers reduce code duplication across mode implementations.

Used by: mode_standard.py, mode_act.py, mode_react.py, mode_reflact.py
Depends on: agent_config.py, agent_prompts.py
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator, TYPE_CHECKING

from llm.openai_utils import extract_delta_text, extract_message_text
from services.llm.llm_execution_service import LLMExecutionService

from .agent_config import build_completion_kwargs

if TYPE_CHECKING:
    from db.models.chatbot import Chatbot, ChatbotConversation, ChatbotMessageRole

logger = logging.getLogger(__name__)


# =============================================================================
# LLM CALLS
# =============================================================================

def call_llm_sync(
    llm_client,
    chatbot: 'Chatbot',
    messages: List[Dict],
    api_model_id: Optional[str] = None,
) -> str:
    """
    Synchronous LLM call.

    Args:
        llm_client: LiteLLM client instance
        chatbot: Chatbot model instance
        messages: List of message dicts

    Returns:
        Response text string, empty string on error
    """
    try:
        kwargs = build_completion_kwargs(
            chatbot,
            messages,
            stream=False,
            model_id=api_model_id,
        )
        response = LLMExecutionService.execute_with_param_fixes(
            llm_client,
            kwargs,
            model_key=api_model_id or chatbot.model_name,
        )

        if response.choices:
            return extract_message_text(response.choices[0].message)
        return ""

    except Exception as e:
        logger.error(f"[AgentChatService] LLM call failed: {e}")
        return ""


def stream_llm_response(
    llm_client,
    chatbot: 'Chatbot',
    messages: List[Dict],
    api_model_id: Optional[str] = None,
) -> Generator[str, None, str]:
    """
    Stream LLM response, yielding delta text.

    Args:
        llm_client: LiteLLM client instance
        chatbot: Chatbot model instance
        messages: List of message dicts

    Yields:
        Delta text chunks as they arrive

    Returns:
        Complete accumulated response text
    """
    accumulated = ""

    try:
        kwargs = build_completion_kwargs(
            chatbot,
            messages,
            stream=True,
            model_id=api_model_id,
        )
        stream = LLMExecutionService.execute_with_param_fixes(
            llm_client,
            kwargs,
            model_key=api_model_id or chatbot.model_name,
        )

        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            delta = getattr(choice, "delta", None) if choice else None
            delta_text = extract_delta_text(delta)
            if delta_text:
                accumulated += delta_text
                yield delta_text

    except Exception as e:
        logger.error(f"[AgentChatService] Streaming failed: {e}")

    return accumulated


# =============================================================================
# CONVERSATION FINALIZATION
# =============================================================================

def finalize_conversation(
    db,
    conversation: 'ChatbotConversation',
    message: str,
    response: str,
    sources: List[Dict],
    include_sources: bool,
    mode: str,
    iterations: int,
    reasoning_steps: List[Dict],
    save_message_func,
    maybe_set_title_func,
    retrieval_time_ms: Optional[int] = None,
    adaptive_exit: bool = False,
    goal: Optional[str] = None
) -> Dict[str, Any]:
    """
    Finalize conversation by saving message and updating conversation state.

    This is a common pattern used at the end of all agent modes to:
    1. Save the assistant response message
    2. Update conversation metadata
    3. Generate a title if needed
    4. Commit database changes

    Args:
        db: SQLAlchemy database instance
        conversation: ChatbotConversation instance
        message: Original user message
        response: Final assistant response
        sources: List of RAG sources
        include_sources: Whether to include sources in saved message
        mode: Agent mode name
        iterations: Number of iterations taken
        reasoning_steps: List of reasoning step dicts
        save_message_func: Function to save messages
        maybe_set_title_func: Function to set conversation title
        retrieval_time_ms: Optional RAG retrieval time
        adaptive_exit: Whether adaptive iteration triggered early exit
        goal: Optional goal string (for reflact mode)

    Returns:
        Dict containing message_id, conversation_id, and title
    """
    from db.models.chatbot import ChatbotMessageRole

    # Build stream metadata
    stream_metadata = {
        "mode": mode,
        "iterations": iterations,
        "sources_count": len(sources)
    }

    if retrieval_time_ms is not None:
        stream_metadata["retrieval_time_ms"] = retrieval_time_ms

    if adaptive_exit:
        stream_metadata["adaptive_exit"] = True

    # Save assistant message
    msg = save_message_func(
        conversation.id,
        ChatbotMessageRole.ASSISTANT,
        response,
        rag_sources=sources if include_sources else [],
        agent_trace=reasoning_steps if reasoning_steps else None,
        stream_metadata=stream_metadata
    )

    # Update conversation metadata
    conversation.message_count += 2  # User + Assistant
    conversation.last_message_at = datetime.now()
    maybe_set_title_func(conversation, message)
    db.session.commit()

    return {
        "message_id": msg.id,
        "conversation_id": conversation.id,
        "title": conversation.title
    }


def build_done_event(
    response: str,
    sources: List[Dict],
    include_sources: bool,
    mode: str,
    iterations: int,
    reasoning_steps: List[Dict],
    conversation_info: Dict[str, Any],
    adaptive_exit: bool = False,
    goal: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build the final 'done' event for agent completion.

    Args:
        response: Final response text
        sources: List of RAG sources
        include_sources: Whether to include sources
        mode: Agent mode name
        iterations: Number of iterations
        reasoning_steps: List of reasoning steps
        conversation_info: Dict with message_id, conversation_id, title
        adaptive_exit: Whether adaptive iteration triggered
        goal: Optional goal (for reflact mode)

    Returns:
        Complete 'done' event dict
    """
    event = {
        "done": True,
        "full_response": response,
        "sources": sources if include_sources else [],
        "mode": mode,
        "iterations": iterations,
        "reasoning_steps": reasoning_steps,
        "conversation_id": conversation_info["conversation_id"],
        "title": conversation_info["title"],
        "message_id": conversation_info["message_id"]
    }

    if adaptive_exit:
        event["adaptive_exit"] = True

    if goal:
        event["goal"] = goal

    return event


# =============================================================================
# ADAPTIVE RESPONSE GENERATION
# =============================================================================

def generate_adaptive_response_stream(
    llm_client,
    chatbot: 'Chatbot',
    prompt_settings,
    message: str,
    sources: List[Dict],
    observation: str,
    api_model_id: Optional[str] = None,
) -> Generator[Dict[str, Any], None, str]:
    """
    Generate a final answer when adaptive iteration triggers early completion.

    Streams the response and yields status events plus delta chunks.

    Args:
        llm_client: LiteLLM client instance
        chatbot: Chatbot model instance
        prompt_settings: ChatbotPromptSettings instance
        message: Original user question
        sources: High-confidence sources that triggered adaptive exit
        observation: The observation text from the tool

    Yields:
        Status events and delta chunks

    Returns:
        Complete response text
    """
    from services.chatbot.agent_prompts import (
        get_act_system_prompt,
        build_adaptive_response_prompt,
        _substitute_project_url,
    )

    yield {"status": "adaptive_response", "reason": "high_confidence_results"}

    system_prompt = get_act_system_prompt(chatbot, prompt_settings)
    # Replace {PROJECT_URL} placeholders before using in prompts
    base_prompt = _substitute_project_url((chatbot.system_prompt or "").strip())

    answer_prompt = build_adaptive_response_prompt(message, observation, base_prompt)

    messages = [{"role": "system", "content": base_prompt or system_prompt}]
    messages.append({"role": "user", "content": answer_prompt})

    final_response = ""
    try:
        kwargs = build_completion_kwargs(
            chatbot,
            messages,
            stream=True,
            model_id=api_model_id,
        )
        stream = LLMExecutionService.execute_with_param_fixes(
            llm_client,
            kwargs,
            model_key=api_model_id or chatbot.model_name,
        )

        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            delta = getattr(choice, "delta", None) if choice else None
            delta_text = extract_delta_text(delta)
            if delta_text:
                final_response += delta_text
                yield {"delta": delta_text}

    except Exception as e:
        logger.error(f"[AgentChatService] Adaptive response streaming failed: {e}")
        final_response = call_llm_sync(
            llm_client,
            chatbot,
            messages,
            api_model_id=api_model_id,
        )

    return final_response


def generate_final_response(
    llm_client,
    chatbot: 'Chatbot',
    question: str,
    steps: List[Dict],
    citation_instructions: str,
    api_model_id: Optional[str] = None,
) -> str:
    """
    Generate final response based on collected information.

    Used when max iterations are reached or when no direct answer was produced.

    Args:
        llm_client: LiteLLM client instance
        chatbot: Chatbot model instance
        question: Original user question
        steps: List of reasoning steps (thoughts, actions, observations)
        citation_instructions: Instructions for citing sources

    Returns:
        Final response text
    """
    from services.chatbot.agent_prompts import build_final_response_prompt, _substitute_project_url

    # Replace {PROJECT_URL} placeholders before using in prompts
    system_prompt = _substitute_project_url(chatbot.system_prompt or "")
    messages = build_final_response_prompt(
        question,
        steps,
        system_prompt,
        citation_instructions
    )
    return call_llm_sync(
        llm_client,
        chatbot,
        messages,
        api_model_id=api_model_id,
    )


# =============================================================================
# SYNC AGENT EXECUTION
# =============================================================================

def run_agent_sync(
    agent_generator: Generator[Dict[str, Any], None, None],
    session_id: str,
    conversation_id: Optional[int],
    mode: str,
    task_type: str,
    files: Optional[List[Dict]] = None,
    unknown_answer: str = ""
) -> Dict[str, Any]:
    """
    Run agent chat synchronously and return the final result.

    Consumes the generator until completion and returns a structured result.

    Args:
        agent_generator: Generator from chat_agent or mode-specific method
        session_id: Session identifier
        conversation_id: Conversation ID
        mode: Agent mode name
        task_type: Task type (lookup/multihop)
        files: Optional list of file attachments
        unknown_answer: Fallback response if agent fails

    Returns:
        Dict with response, sources, metadata, etc.
    """
    start_time = time.time()
    final_event: Optional[Dict[str, Any]] = None

    for event in agent_generator:
        if event.get("done"):
            final_event = event
            break

    response_time_ms = int((time.time() - start_time) * 1000)

    if not final_event:
        return {
            'response': unknown_answer,
            'sources': [],
            'conversation_id': conversation_id,
            'session_id': session_id,
            'title': None,
            'message_id': None,
            'tokens': {'input': 0, 'output': 0},
            'response_time_ms': response_time_ms,
            'mode': mode,
            'task_type': task_type,
            'iterations': 0,
            'reasoning_steps': [],
            'files_processed': len(files) if files else 0
        }

    return {
        'response': final_event.get('full_response', ''),
        'sources': final_event.get('sources', []),
        'conversation_id': final_event.get('conversation_id'),
        'session_id': session_id,
        'title': final_event.get('title'),
        'message_id': final_event.get('message_id'),
        'tokens': {'input': 0, 'output': 0},
        'response_time_ms': response_time_ms,
        'mode': final_event.get('mode'),
        'task_type': task_type,
        'iterations': final_event.get('iterations'),
        'reasoning_steps': final_event.get('reasoning_steps', []),
        'files_processed': len(files) if files else 0
    }
