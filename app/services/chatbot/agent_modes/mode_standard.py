# mode_standard.py
"""
Standard Agent Mode Implementation.

Implements single-shot streaming response without explicit reasoning.
This is the simplest agent mode - just a direct LLM call with RAG context.

Features:
    - RAG context retrieval (if enabled)
    - Streaming response generation
    - Source attribution

Flow:
    1. Retrieve RAG context if enabled
    2. Build messages with context
    3. Stream LLM response
    4. Save message and finalize conversation

Used by: agent_chat_service.py
"""

from __future__ import annotations

import logging
import time
from typing import List, Dict, Any, Optional, Generator, TYPE_CHECKING

from llm.openai_utils import extract_delta_text

from .agent_config import build_completion_kwargs
from .agent_helpers import finalize_conversation, build_done_event

if TYPE_CHECKING:
    from services.chatbot.agent_chat_service import AgentChatService

logger = logging.getLogger(__name__)


def chat_standard_stream(
    service: 'AgentChatService',
    message: str,
    session_id: str,
    username: Optional[str] = None,
    include_sources: bool = True,
    files: Optional[List[Dict[str, Any]]] = None,
    conversation_id: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Standard single-shot streaming response.

    The simplest agent mode - retrieves RAG context and generates
    a direct response without any reasoning traces.

    Args:
        service: AgentChatService instance
        message: User's input message
        session_id: Session identifier
        username: Optional username
        include_sources: Whether to include RAG sources in response
        files: Optional list of file attachments
        conversation_id: Optional existing conversation ID

    Yields:
        Status events and delta chunks during streaming

    Events Yielded:
        - {"status": "starting", "mode": "standard"}
        - {"status": "context_retrieved", "sources_count": int}
        - {"status": "generating"}
        - {"delta": str} (multiple)
        - {"done": True, "full_response": str, ...}
    """
    from db.db import db
    from db.models.chatbot import ChatbotMessageRole

    yield {"status": "starting", "mode": "standard"}

    # Get or create conversation
    conversation = service._get_or_create_conversation(session_id, username, conversation_id)
    service._save_message(conversation.id, ChatbotMessageRole.USER, message)

    # Get RAG context if enabled
    rag_context = ""
    sources = []
    retrieval_time_ms = None

    if service.chatbot.rag_enabled and service.chatbot.collections:
        retrieval_start = time.time()
        rag_context, sources = service._get_multi_collection_context(message)
        retrieval_time_ms = int((time.time() - retrieval_start) * 1000)

    yield {"status": "context_retrieved", "sources_count": len(sources)}

    # Build messages and generate response
    messages = service._build_messages(conversation, message, rag_context, files, sources=sources)
    yield {"status": "generating"}

    accumulated = ""
    try:
        kwargs = build_completion_kwargs(service.chatbot, messages, stream=True)
        stream = service.llm_client.chat.completions.create(**kwargs)

        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            delta = getattr(choice, "delta", None) if choice else None
            delta_text = extract_delta_text(delta)
            if delta_text:
                accumulated += delta_text
                yield {"delta": delta_text}

    except Exception as e:
        logger.error(f"[AgentChatService] Standard streaming failed: {e}")
        yield {"error": str(e)}
        return

    # Finalize conversation
    conv_info = finalize_conversation(
        db=db,
        conversation=conversation,
        message=message,
        response=accumulated,
        sources=sources,
        include_sources=include_sources,
        mode="standard",
        iterations=1,
        reasoning_steps=[],
        save_message_func=service._save_message,
        maybe_set_title_func=service._maybe_set_conversation_title,
        retrieval_time_ms=retrieval_time_ms
    )

    yield build_done_event(
        response=accumulated,
        sources=sources,
        include_sources=include_sources,
        mode="standard",
        iterations=1,
        reasoning_steps=[],
        conversation_info=conv_info
    )
