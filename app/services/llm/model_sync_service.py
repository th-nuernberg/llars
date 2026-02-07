"""
LLM Model Sync Service

Synchronizes available models from a configured OpenAI-compatible endpoint
(typically a LiteLLM proxy) into the llm_models table.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from db.database import db
from db.models.llm_model import LLMModel
from db.models.llm_provider import LLMProvider
from services.llm.secret_encryption import decrypt_api_key


logger = logging.getLogger(__name__)


class LLMModelSyncService:
    @staticmethod
    def infer_model_defaults(model_id: str) -> Dict[str, Any]:
        return _infer_model_defaults(model_id)

    @staticmethod
    def sync_from_litellm(
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        activate_existing: bool = True,
        synced_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Pull model IDs from the configured LiteLLM/OpenAI-compatible `/models` endpoint
        and upsert missing entries into `llm_models`.
        """
        base_url = (base_url or os.environ.get("LITELLM_BASE_URL") or "").rstrip("/")
        api_key = api_key or os.environ.get("LITELLM_API_KEY")

        if not base_url:
            return {"success": False, "error": "LITELLM_BASE_URL is not configured"}

        url = f"{base_url}/models"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {"success": False, "error": "Unexpected /models response format"}

        model_ids: List[str] = []
        for item in items:
            if isinstance(item, dict):
                mid = item.get("id") or item.get("model")
                if mid:
                    model_ids.append(str(mid))

        inserted = 0
        updated = 0
        skipped = 0

        for model_id in sorted(set(model_ids)):
            existing = LLMModel.get_by_model_id(model_id)
            if existing:
                if activate_existing and not existing.is_active:
                    existing.is_active = True
                    if synced_by:
                        existing.updated_by = synced_by
                    updated += 1
                if not existing.color:
                    existing.color = LLMModel.generate_color(existing.model_id)
                else:
                    skipped += 1
                continue

            inferred = _infer_model_defaults(model_id)
            model = LLMModel(
                model_id=model_id,
                display_name=inferred["display_name"],
                provider=inferred["provider"],
                description=None,
                model_type=inferred["model_type"],
                color=LLMModel.generate_color(model_id),
                supports_vision=inferred["supports_vision"],
                supports_reasoning=inferred["supports_reasoning"],
                supports_function_calling=True,
                supports_streaming=True,
                context_window=inferred["context_window"],
                max_output_tokens=inferred["max_output_tokens"],
                input_cost_per_million=0.0,
                output_cost_per_million=0.0,
                is_default=False,
                is_active=True,
                created_by=synced_by,
                updated_by=synced_by,
            )
            db.session.add(model)
            inserted += 1

        db.session.commit()

        return {
            "success": True,
            "source": url,
            "total_remote": len(set(model_ids)),
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
        }

    @staticmethod
    def sync_from_provider(
        provider: LLMProvider,
        *,
        activate_existing: bool = True,
        synced_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not provider:
            return {"success": False, "error": "Provider not found"}

        if not provider.is_openai_compatible:
            return {"success": False, "error": "Provider is not OpenAI-compatible"}

        base_url = (provider.base_url or "").rstrip("/")
        if not base_url:
            return {"success": False, "error": "Provider base_url is not configured"}

        api_key = None
        if provider.api_key_encrypted:
            api_key = decrypt_api_key(provider.api_key_encrypted)

        url = f"{base_url}/models"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {"success": False, "error": "Unexpected /models response format"}

        model_ids: List[str] = []
        for item in items:
            if isinstance(item, dict):
                mid = item.get("id") or item.get("model")
                if mid:
                    model_ids.append(str(mid))

        inserted = 0
        updated = 0
        skipped = 0

        for model_id in sorted(set(model_ids)):
            existing = LLMModel.get_by_model_id(model_id)
            if existing:
                if activate_existing and not existing.is_active:
                    existing.is_active = True
                    if synced_by:
                        existing.updated_by = synced_by
                    updated += 1
                if not existing.color:
                    existing.color = LLMModel.generate_color(existing.model_id)
                if existing.provider_id != provider.id:
                    existing.provider_id = provider.id
                    if synced_by:
                        existing.updated_by = synced_by
                else:
                    skipped += 1
                continue

            inferred = _infer_model_defaults(model_id)
            model = LLMModel(
                model_id=model_id,
                display_name=inferred["display_name"],
                provider=inferred["provider"],
                description=None,
                model_type=inferred["model_type"],
                color=LLMModel.generate_color(model_id),
                supports_vision=inferred["supports_vision"],
                supports_reasoning=inferred["supports_reasoning"],
                supports_function_calling=True,
                supports_streaming=True,
                context_window=inferred["context_window"],
                max_output_tokens=inferred["max_output_tokens"],
                input_cost_per_million=0.0,
                output_cost_per_million=0.0,
                is_default=False,
                is_active=True,
                provider_id=provider.id,
                created_by=synced_by,
                updated_by=synced_by,
            )
            db.session.add(model)
            inserted += 1

        db.session.commit()

        return {
            "success": True,
            "source": url,
            "total_remote": len(set(model_ids)),
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
        }


_VISION_HINTS = (
    "vision",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4.1",
    "pixtral",
    "magistral",
    "claude-3",
)

_REASONING_HINTS = (
    "reasoning",
    "o1",
    "o3",
    "magistral",
)

_EMBEDDING_HINTS = (
    "embedding",
    "embed",
    "e5",
    "bge",
    "vdr",
    "text-embedding",
    "sentence-transformers",
)

_RERANKER_HINTS = (
    "rerank",
    "reranker",
    "cross-encoder",
)


def _infer_model_defaults(model_id: str) -> Dict[str, Any]:
    mid = (model_id or "").strip()
    lower = mid.lower()

    provider = _infer_provider(mid)

    supports_vision = any(h in lower for h in _VISION_HINTS)
    supports_reasoning = any(h in lower for h in _REASONING_HINTS)
    is_embedding = any(h in lower for h in _EMBEDDING_HINTS)
    is_reranker = any(h in lower for h in _RERANKER_HINTS)

    if is_reranker:
        model_type = LLMModel.MODEL_TYPE_RERANKER
    elif is_embedding:
        model_type = LLMModel.MODEL_TYPE_EMBEDDING
    else:
        model_type = LLMModel.MODEL_TYPE_LLM

    # Conservative defaults; can be adjusted in the admin later.
    context_window = 32768
    max_output_tokens = 8192

    display_name = _pretty_model_name(mid)

    return {
        "provider": provider,
        "display_name": display_name,
        "supports_vision": supports_vision,
        "supports_reasoning": supports_reasoning,
        "context_window": context_window,
        "max_output_tokens": max_output_tokens,
        "model_type": model_type,
    }


def _infer_provider(model_id: str) -> str:
    if "/" in model_id:
        return model_id.split("/", 1)[0].lower()

    lower = model_id.lower()
    if lower.startswith(("gpt-", "o1", "o3")):
        return "openai"
    if lower.startswith("claude"):
        return "anthropic"
    return "litellm"


_PRETTY_RE = re.compile(r"[_\-]+")


def _pretty_model_name(model_id: str) -> str:
    # Keep namespace but make it readable
    name = model_id.replace("/", " · ")
    name = _PRETTY_RE.sub(" ", name).strip()
    return name
