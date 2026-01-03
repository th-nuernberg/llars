# agent_prompts.py
"""
Agent Prompt Builder Module.

Provides system prompt builders for agent chat modes (ACT, ReAct, ReflAct).
"""

from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.chatbot import Chatbot, ChatbotPromptSettings, ChatbotConversation


def get_act_system_prompt(
    chatbot: "Chatbot",
    prompt_settings: Optional["ChatbotPromptSettings"]
) -> str:
    """
    Get ACT system prompt.

    Args:
        chatbot: The chatbot configuration
        prompt_settings: Optional prompt settings

    Returns:
        Complete ACT system prompt
    """
    base_prompt = (chatbot.system_prompt or "").strip()

    if prompt_settings and hasattr(prompt_settings, 'act_system_prompt'):
        custom = prompt_settings.act_system_prompt
        if custom and custom.strip():
            act_prompt = custom
        else:
            act_prompt = None
    else:
        act_prompt = None

    from db.models.chatbot import DEFAULT_ACT_SYSTEM_PROMPT
    if not act_prompt:
        act_prompt = DEFAULT_ACT_SYSTEM_PROMPT

    if base_prompt:
        return f"{base_prompt}\n\n{act_prompt}"
    return act_prompt


def get_react_system_prompt(
    chatbot: "Chatbot",
    prompt_settings: Optional["ChatbotPromptSettings"]
) -> str:
    """
    Get ReAct system prompt.

    Args:
        chatbot: The chatbot configuration
        prompt_settings: Optional prompt settings

    Returns:
        Complete ReAct system prompt
    """
    base_prompt = (chatbot.system_prompt or "").strip()

    if prompt_settings and hasattr(prompt_settings, 'react_system_prompt'):
        custom = prompt_settings.react_system_prompt
        if custom and custom.strip():
            react_prompt = custom
        else:
            react_prompt = None
    else:
        react_prompt = None

    if not react_prompt:
        from db.models.chatbot import DEFAULT_REACT_SYSTEM_PROMPT
        react_prompt = DEFAULT_REACT_SYSTEM_PROMPT

    if base_prompt:
        return f"{base_prompt}\n\n{react_prompt}"
    return react_prompt


def get_reflact_system_prompt(
    chatbot: "Chatbot",
    prompt_settings: Optional["ChatbotPromptSettings"]
) -> str:
    """
    Get ReflAct system prompt.

    Args:
        chatbot: The chatbot configuration
        prompt_settings: Optional prompt settings

    Returns:
        Complete ReflAct system prompt
    """
    base_prompt = (chatbot.system_prompt or "").strip()

    if prompt_settings and hasattr(prompt_settings, 'reflact_system_prompt'):
        custom = prompt_settings.reflact_system_prompt
        if custom and custom.strip():
            reflact_prompt = custom
        else:
            reflact_prompt = None
    else:
        reflact_prompt = None

    if not reflact_prompt:
        from db.models.chatbot import DEFAULT_REFLACT_SYSTEM_PROMPT
        reflact_prompt = DEFAULT_REFLACT_SYSTEM_PROMPT

    if base_prompt:
        return f"{base_prompt}\n\n{reflact_prompt}"
    return reflact_prompt


def build_tool_availability_prompt(
    enabled_tools: List[str],
    web_search_enabled: bool
) -> str:
    """
    Provide tool availability and query guidance for agent modes.

    Args:
        enabled_tools: List of enabled tool names
        web_search_enabled: Whether web search is enabled

    Returns:
        Tool availability prompt string
    """
    tools = [t for t in enabled_tools if t]
    if not web_search_enabled:
        tools = [t for t in tools if t != "web_search"]
    if not tools:
        return ""

    tool_list = ", ".join(tools)
    return (
        f"Verfuegbare Tools fuer diese Session: {tool_list}.\n"
        "Nutze nur diese Tools.\n"
        "Nutze Suchbegriffe aus der aktuellen Nutzerfrage oder dem Verlauf.\n"
        "Wenn die Frage ohne Kontext unklar ist, stelle eine Rueckfrage mit respond.\n"
        "Keine [TOOL_CALLS]-Marker oder JSON-Toolcalls, nur das ACTION-Format."
    )


def build_agent_history_messages(
    conversation: "ChatbotConversation",
    current_message: str,
    max_context_messages: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Return recent chat history for agent modes, excluding the current message.

    Args:
        conversation: The conversation object
        current_message: Current user message to exclude
        max_context_messages: Maximum number of message pairs to include

    Returns:
        List of message dicts with 'role' and 'content'
    """
    from db.models.chatbot import ChatbotMessage, ChatbotMessageRole

    max_context = max_context_messages or 6
    limit = max_context * 2
    history = ChatbotMessage.query.filter_by(
        conversation_id=conversation.id
    ).order_by(ChatbotMessage.created_at.desc()).limit(limit).all()

    history.reverse()
    if history and history[-1].role == ChatbotMessageRole.USER and history[-1].content == current_message:
        history = history[:-1]

    messages: List[Dict[str, str]] = []
    for msg in history:
        role = "user" if msg.role == ChatbotMessageRole.USER else "assistant"
        messages.append({"role": role, "content": msg.content})
    return messages


def build_adaptive_response_prompt(
    message: str,
    observation: str,
    base_prompt: str
) -> str:
    """
    Build prompt for generating adaptive response when high-confidence results found.

    Args:
        message: Original user message
        observation: Search observation/results
        base_prompt: Base system prompt

    Returns:
        Formatted prompt for response generation
    """
    return f"""Basierend auf den folgenden Suchergebnissen, beantworte die Nutzerfrage.
Nutze die Quellenverweise [1], [2], etc. für deine Antwort.

SUCHERGEBNISSE:
{observation}

NUTZERFRAGE: {message}

Gib eine vollständige, gut strukturierte Antwort mit Quellenverweisen."""


def build_final_response_prompt(
    question: str,
    steps: List[Dict],
    system_prompt: str,
    citation_instructions: str
) -> List[Dict[str, str]]:
    """
    Build messages for final response generation.

    Args:
        question: Original user question
        steps: List of agent reasoning steps
        system_prompt: Base system prompt
        citation_instructions: Citation formatting instructions

    Returns:
        List of message dicts for LLM call
    """
    # Build context from observations
    context_parts = []
    for step in steps:
        if step.get("type") == "observation":
            context_parts.append(step.get("content", ""))

    context = "\n\n".join(context_parts)

    return [
        {"role": "system", "content": system_prompt + citation_instructions},
        {"role": "system", "content": f"Kontext aus der Recherche:\n\n{context}"},
        {"role": "user", "content": f"Basierend auf der obigen Recherche, beantworte folgende Frage:\n\n{question}"}
    ]
