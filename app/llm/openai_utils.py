"""
OpenAI-compatible response helpers.

Several LiteLLM-backed models return text in `reasoning_content` (e.g. Magistral)
or as content blocks. These helpers normalize both streaming deltas and final
messages into plain text.
"""

from __future__ import annotations

from typing import Any


def _extract_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        preferred: list[str] = []
        fallback: list[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    item_type = item.get("type")
                    if item_type in ("output_text", "text"):
                        preferred.append(text)
                    else:
                        fallback.append(text)
                    continue
            if isinstance(item, str):
                fallback.append(item)
                continue
            if hasattr(item, "text"):
                fallback.append(getattr(item, "text") or "")
                continue
            fallback.append(str(item))
        return "".join(preferred or fallback)

    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            return text
        content = value.get("content")
        if isinstance(content, str):
            return content

    if hasattr(value, "text"):
        return getattr(value, "text") or ""

    return str(value)


def extract_message_text(message: Any) -> str:
    """
    Extract assistant text from a chat completion message.

    Prefers `content`, falls back to `reasoning_content`, then `refusal`.
    """
    if message is None:
        return ""

    if isinstance(message, dict):
        content = message.get("content")
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        refusal = message.get("refusal")
    else:
        content = getattr(message, "content", None)
        reasoning = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None)
        refusal = getattr(message, "refusal", None)

    text = _extract_text(content)
    if not text.strip():
        text = _extract_text(reasoning)
    if not text.strip():
        text = _extract_text(refusal)
    return text


def extract_delta_text(delta: Any) -> str:
    """
    Extract token delta text from a streaming chunk delta.

    Prefers `content`, falls back to `reasoning_content`.
    """
    if delta is None:
        return ""

    if isinstance(delta, dict):
        content = delta.get("content")
        reasoning = delta.get("reasoning_content") or delta.get("reasoning")
    else:
        content = getattr(delta, "content", None)
        reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)

    text = _extract_text(content)
    if not text:
        text = _extract_text(reasoning)
    return text
