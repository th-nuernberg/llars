# anonymize_llm_detection.py
"""
LLM-based entity detection for the anonymize service.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Optional

from .anonymize_constants import (
    EntityOccurrence,
    LLM_ALLOWED_LABELS,
    LLM_LABEL_ALIASES,
    LLM_DETECTION_PROMPT,
)
from services.llm.llm_provider_service import LLMProviderService
from services.llm.llm_client_factory import LLMClientFactory

logger = logging.getLogger(__name__)


def llm_quick_status() -> dict[str, Any]:
    """Check if LLM is configured and ready."""
    litellm_key = os.environ.get("LITELLM_API_KEY") or ""
    litellm_base_url = os.environ.get("LITELLM_BASE_URL") or ""
    openai_key = os.environ.get("OPENAI_API_KEY") or ""

    default_model_id = None
    try:
        from db.models.llm_model import LLMModel
        default_model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
    except Exception:
        default_model_id = None

    provider = LLMProviderService.get_default_provider()
    if provider:
        return {
            "ready": bool(provider.is_active),
            "provider": provider.provider_type,
            "base_url": provider.base_url,
            "default_model": default_model_id,
        }

    if litellm_key.strip():
        return {
            "ready": bool(litellm_base_url.strip()),
            "provider": "litellm",
            "base_url": litellm_base_url.strip() or None,
            "default_model": default_model_id,
        }

    return {
        "ready": bool(openai_key.strip()),
        "provider": "openai" if openai_key.strip() else None,
        "default_model": default_model_id,
    }


def _resolve_llm_model_id(model: Optional[str] = None) -> str:
    """Resolve and validate the LLM model ID."""
    from db.models.llm_model import LLMModel

    if model:
        model_id = str(model).strip()
        db_model = LLMModel.get_by_model_id(model_id)
        if not db_model or not db_model.is_active or db_model.model_type != LLMModel.MODEL_TYPE_LLM:
            raise RuntimeError(f"LLM model '{model_id}' is not available in llm_models")
        return db_model.model_id

    default_model = LLMModel.get_default_model(model_type=LLMModel.MODEL_TYPE_LLM)
    if not default_model:
        raise RuntimeError("No default LLM model configured in llm_models")
    return default_model.model_id


def _parse_llm_json(response_text: str) -> dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    raw = (response_text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def _normalize_llm_label(label: str) -> Optional[str]:
    """Normalize entity label from LLM response."""
    if not isinstance(label, str):
        return None
    key = label.strip().upper()
    key = LLM_LABEL_ALIASES.get(key, key)
    return key if key in LLM_ALLOWED_LABELS else None


def _resolve_llm_span(
    text: str,
    start: Any,
    end: Any,
    span_text: Optional[str],
) -> Optional[tuple[int, int]]:
    """Resolve entity span from LLM response, validating against text."""
    if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text):
        if span_text is None or text[start:end] == span_text:
            return start, end

    if isinstance(span_text, str) and span_text:
        matches = [m.start() for m in re.finditer(re.escape(span_text), text)]
        if len(matches) == 1:
            s = int(matches[0])
            return s, s + len(span_text)
    return None


def find_llm_entities(text: str, model: Optional[str] = None, max_entities: int = 250) -> list[EntityOccurrence]:
    """Find entities using LLM-based detection."""
    from llm.openai_utils import extract_message_text

    status = llm_quick_status()
    if not status.get("ready"):
        raise RuntimeError("LLM is not configured (missing API key/base URL)")

    model_id = _resolve_llm_model_id(model)
    client = LLMClientFactory.get_client_for_model(model_id)

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": LLM_DETECTION_PROMPT},
            {"role": "user", "content": f"ORIGINALTEXT:\n{text}"},
        ],
        temperature=0.0,
        max_tokens=2000,
    )

    response_text = extract_message_text(response.choices[0].message).strip() if response.choices else ""
    if not response_text:
        return []

    try:
        parsed = _parse_llm_json(response_text)
    except Exception as e:
        logger.warning(f"[Anonymize/LLM] Failed to parse JSON: {e}")
        return []

    entities = parsed.get("entities") if isinstance(parsed, dict) else None
    if not isinstance(entities, list):
        return []

    occurrences: list[EntityOccurrence] = []
    seen: set[tuple[str, int, int]] = set()

    for item in entities[:max_entities]:
        if not isinstance(item, dict):
            continue

        label = _normalize_llm_label(item.get("label"))
        if not label:
            continue

        resolved = _resolve_llm_span(
            text=text,
            start=item.get("start"),
            end=item.get("end"),
            span_text=item.get("text") if isinstance(item.get("text"), str) else None,
        )
        if resolved is None:
            continue
        start, end = resolved

        key = (label, start, end)
        if key in seen:
            continue
        seen.add(key)

        occurrences.append(EntityOccurrence(label=label, start=start, end=end, text=text[start:end]))

    return occurrences
