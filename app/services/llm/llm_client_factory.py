"""
LLM Client Factory

Builds OpenAI-compatible clients for configured providers and routes per model.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import httpx
import requests
from openai import OpenAI

# Timeout for LLM requests (in seconds)
# Streaming requests need longer timeouts as the model generates tokens
LLM_TIMEOUT = httpx.Timeout(
    connect=30.0,    # Connection timeout
    read=300.0,      # Read timeout (5 minutes for streaming)
    write=30.0,      # Write timeout
    pool=30.0        # Pool timeout
)

from db.models.llm_model import LLMModel
from db.models.llm_provider import LLMProvider
from services.llm.llm_provider_service import LLMProviderService
from services.llm.secret_encryption import decrypt_api_key
from services.user_llm_provider_service import UserLLMProviderService

USER_PROVIDER_PREFIX = "user-provider:"

# Meta-prefix for globally seeded models (e.g. "Global/OpenAI/gpt-5-nano")
GLOBAL_PREFIX = "Global/"

# Manufacturer → provider type mapping for Global/ prefix routing
MANUFACTURER_TO_PROVIDER = {
    "openai": "openai",
    "mistral": "litellm",
    "anthropic": "anthropic",
    "gemini": "gemini",
}

# Manufacturer → API model prefix (for LiteLLM-style routing)
MANUFACTURER_API_PREFIX = {
    "mistral": "mistralai/",
}

# Known provider prefixes for model ID routing (e.g. "OpenAI/gpt-5-nano")
KNOWN_PROVIDER_PREFIXES = {"openai", "litellm", "anthropic", "gemini", "ollama", "custom"}


class LLMClientFactory:
    """Create LLM clients routed by model or provider."""

    # Module-level client cache: avoids repeated DB queries, key decryption,
    # and TCP connection setup. Keyed by a stable identifier per provider.
    _client_cache: dict[str, OpenAI] = {}

    @classmethod
    def _get_or_create_client(cls, cache_key: str, factory_fn) -> OpenAI:
        """Get a cached client or create one via factory_fn."""
        client = cls._client_cache.get(cache_key)
        if client is None:
            client = factory_fn()
            cls._client_cache[cache_key] = client
        return client

    @classmethod
    def clear_cache(cls):
        """Clear the client cache (e.g. after provider config changes)."""
        cls._client_cache.clear()

    @staticmethod
    def _parse_user_provider_model_id(model_id: Optional[str]) -> tuple[Optional[int], Optional[str]]:
        """Parse user-provider model IDs.

        Supports two formats:
        - New: user-provider:<providerId>:<username>:<model>
        - Old: user-provider:<providerId>:<model>
        """
        if not model_id or not isinstance(model_id, str):
            return None, None
        if not model_id.startswith(USER_PROVIDER_PREFIX):
            return None, None
        rest = model_id[len(USER_PROVIDER_PREFIX):]
        parts = rest.split(":", 2)
        if len(parts) < 2:
            return None, None
        try:
            provider_id = int(parts[0])
        except (TypeError, ValueError):
            return None, None
        # New format: provider_id:username:model (3 parts)
        # Old format: provider_id:model (2 parts)
        if len(parts) == 3:
            actual_model = parts[2]
        else:
            actual_model = parts[1]
        return provider_id, actual_model.strip() or None

    @staticmethod
    def _parse_provider_prefix(model_id: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """
        Parse a provider prefix from a model ID.

        'Global/OpenAI/gpt-5-nano' -> ('openai', 'gpt-5-nano')
        'Global/Mistral/Mistral-Small-3.2' -> ('litellm', 'mistralai/Mistral-Small-3.2')
        'OpenAI/gpt-5-nano' -> ('openai', 'gpt-5-nano')
        'LiteLLM/mistralai/Mistral-Small-3.2' -> ('litellm', 'mistralai/Mistral-Small-3.2')
        'llamaindex/vdr-2b-multi-v1' -> (None, None)  # Not a known provider prefix
        """
        if not model_id or not isinstance(model_id, str) or '/' not in model_id:
            return None, None

        # Handle Global/ meta-prefix: Global/Manufacturer/model-name
        if model_id.startswith(GLOBAL_PREFIX):
            rest_after_global = model_id[len(GLOBAL_PREFIX):]
            if '/' not in rest_after_global:
                return None, None
            slash_idx = rest_after_global.index('/')
            manufacturer = rest_after_global[:slash_idx].strip().lower()
            api_model = rest_after_global[slash_idx + 1:].strip()
            if not manufacturer or not api_model:
                return None, None
            provider_type = MANUFACTURER_TO_PROVIDER.get(manufacturer)
            if not provider_type:
                return None, None
            api_prefix = MANUFACTURER_API_PREFIX.get(manufacturer, "")
            return provider_type, f"{api_prefix}{api_model}"

        # Legacy direct provider prefix (e.g. "OpenAI/gpt-5-nano", "LiteLLM/mistralai/...")
        first_slash = model_id.index('/')
        prefix = model_id[:first_slash].strip().lower()
        if prefix not in KNOWN_PROVIDER_PREFIXES:
            return None, None
        rest = model_id[first_slash + 1:].strip()
        if not rest:
            return None, None
        return prefix, rest

    @staticmethod
    def resolve_client_and_model_id(model_id: Optional[str]):
        """
        Resolve a client + effective model_id for API calls.

        Routing priority:
        1. user-provider:<provider_id>:<model_id> → user's personal provider
        2. Provider prefix (e.g. OpenAI/gpt-5-nano) → find admin provider by type, strip prefix
        3. Legacy FK-based routing via llm_models.provider_id
        """
        # 1. User-provider prefix
        provider_id, actual_model_id = LLMClientFactory._parse_user_provider_model_id(model_id)
        if provider_id and actual_model_id:
            cache_key = f"user-provider:{provider_id}"
            client = LLMClientFactory._client_cache.get(cache_key)
            if client is None:
                provider, api_key = UserLLMProviderService.get_provider_with_key(provider_id)
                if provider and provider.provider_type in {"openai", "litellm", "ollama", "custom"}:
                    base_url = (provider.base_url or "").strip() or None
                    client = OpenAI(api_key=api_key or "EMPTY", base_url=base_url, timeout=LLM_TIMEOUT)
                    LLMClientFactory._client_cache[cache_key] = client
            if client:
                return client, actual_model_id

        # 2. Provider prefix routing (e.g. "OpenAI/gpt-5-nano" → OpenAI provider + "gpt-5-nano")
        prefix, stripped_model_id = LLMClientFactory._parse_provider_prefix(model_id)
        if prefix and stripped_model_id:
            cache_key = f"provider-type:{prefix}"
            client = LLMClientFactory._client_cache.get(cache_key)
            if client is None:
                provider = LLMProviderService.get_provider_by_type(prefix)
                if provider and provider.is_active:
                    client = LLMClientFactory.get_client_for_provider(provider)
                    LLMClientFactory._client_cache[cache_key] = client
            if client:
                return client, stripped_model_id

        # 3. Legacy FK-based routing (still strip prefix for API calls)
        effective_id = stripped_model_id if (prefix and stripped_model_id) else model_id
        cache_key = f"legacy:{model_id}"
        client = LLMClientFactory._client_cache.get(cache_key)
        if client is None:
            client = LLMClientFactory.get_client_for_model(model_id)
            LLMClientFactory._client_cache[cache_key] = client
        return client, effective_id

    @staticmethod
    def get_default_model_id() -> Optional[str]:
        """
        Get the default model ID.

        Returns the model_id of the first matching:
        1. Model with is_default=True and is_active=True
        2. First active model of the default provider
        3. None if no models are configured
        """
        # First try explicit default model
        default_model = (
            LLMModel.query
            .filter_by(is_default=True, is_active=True, model_type=LLMModel.MODEL_TYPE_LLM)
            .first()
        )
        if default_model:
            return default_model.model_id

        # Fallback: first model of default provider
        default_provider = LLMProviderService.get_default_provider()
        if default_provider:
            first_model = (
                LLMModel.query
                .filter_by(provider_id=default_provider.id, is_active=True, model_type=LLMModel.MODEL_TYPE_LLM)
                .first()
            )
            if first_model:
                return first_model.model_id

        # Fallback: any active LLM model
        any_model = (
            LLMModel.query
            .filter_by(is_active=True, model_type=LLMModel.MODEL_TYPE_LLM)
            .first()
        )
        if any_model:
            return any_model.model_id

        return None

    @staticmethod
    def get_client_for_model(model_id: Optional[str]):
        provider = LLMClientFactory._resolve_provider(model_id)
        return LLMClientFactory.get_client_for_provider(provider)

    @staticmethod
    def get_client_for_provider(provider: Optional[LLMProvider]):
        if provider and provider.is_openai_compatible:
            return LLMClientFactory._build_openai_client(provider)

        if provider and provider.provider_type == "anthropic":
            return _AdapterClient(AnthropicChatHandler(provider))

        if provider and provider.provider_type == "gemini":
            return _AdapterClient(GeminiChatHandler(provider))

        # Fallback to env-configured OpenAI/LiteLLM
        return LLMClientFactory._build_env_openai_client()

    @staticmethod
    def _resolve_provider(model_id: Optional[str]) -> Optional[LLMProvider]:
        if model_id:
            model = LLMModel.get_by_model_id(str(model_id).strip())
            if model and model.provider_id:
                provider = LLMProvider.query.get(model.provider_id)
                if provider and provider.is_active:
                    return provider
        return LLMProviderService.get_default_provider()

    @staticmethod
    def _build_openai_client(provider: LLMProvider) -> OpenAI:
        api_key = None
        if provider.api_key_encrypted:
            api_key = decrypt_api_key(provider.api_key_encrypted)

        base_url = (provider.base_url or "").strip() or None
        return OpenAI(
            api_key=api_key or "EMPTY",
            base_url=base_url,
            timeout=LLM_TIMEOUT,
        )

    @staticmethod
    def _build_env_openai_client() -> OpenAI:
        base_url = (os.environ.get("LITELLM_BASE_URL") or "").strip() or None
        api_key = (
            (os.environ.get("LITELLM_API_KEY") or "").strip()
            or (os.environ.get("OPENAI_API_KEY") or "").strip()
            or "EMPTY"
        )
        return OpenAI(api_key=api_key, base_url=base_url, timeout=LLM_TIMEOUT)


class _AdapterClient:
    """Expose OpenAI-like chat.completions.create for non-OpenAI providers."""

    def __init__(self, handler):
        self.chat = SimpleNamespace(completions=_CompletionAdapter(handler))


class _CompletionAdapter:
    def __init__(self, handler):
        self._handler = handler

    def create(self, **kwargs):
        return self._handler.create(**kwargs)


class _BaseHandler:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def _build_openai_like_response(self, text: str):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])

    def _build_openai_like_stream(self, text: str):
        chunk = SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason="stop")]
        )
        return iter([chunk])

    def _split_system_messages(self, messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
        system_parts: List[str] = []
        remaining: List[Dict[str, Any]] = []
        for msg in messages or []:
            role = msg.get("role")
            if role == "system":
                content = msg.get("content")
                if isinstance(content, str):
                    system_parts.append(content)
                continue
            remaining.append(msg)
        return "\n\n".join(system_parts), remaining


class AnthropicChatHandler(_BaseHandler):
    def create(self, **kwargs):
        model = kwargs.get("model")
        messages = kwargs.get("messages") or []
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens") or kwargs.get("maxTokens") or 1024
        stream = bool(kwargs.get("stream"))

        system_text, remaining = self._split_system_messages(messages)
        payload = {
            "model": model,
            "messages": [
                {"role": msg.get("role"), "content": msg.get("content")}
                for msg in remaining
                if msg.get("role") in {"user", "assistant"}
            ],
            "max_tokens": max_tokens,
        }
        if system_text:
            payload["system"] = system_text
        if temperature is not None:
            payload["temperature"] = float(temperature)

        api_key = decrypt_api_key(self.provider.api_key_encrypted) if self.provider.api_key_encrypted else None
        if not api_key:
            raise ValueError("Anthropic API key is missing")

        base_url = (self.provider.base_url or "https://api.anthropic.com").rstrip("/")
        api_version = (self.provider.config_json or {}).get("api_version", "2023-06-01")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": api_version,
            "content-type": "application/json",
        }

        resp = requests.post(f"{base_url}/v1/messages", headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        content_blocks = data.get("content") or []
        text = "".join([block.get("text", "") for block in content_blocks if isinstance(block, dict)])

        if stream:
            return self._build_openai_like_stream(text)
        return self._build_openai_like_response(text)


class GeminiChatHandler(_BaseHandler):
    def create(self, **kwargs):
        model = kwargs.get("model") or ""
        messages = kwargs.get("messages") or []
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens") or kwargs.get("maxTokens")
        stream = bool(kwargs.get("stream"))

        system_text, remaining = self._split_system_messages(messages)
        contents = []
        for msg in remaining:
            role = msg.get("role")
            if role not in {"user", "assistant"}:
                continue
            parts = [{"text": msg.get("content") or ""}]
            contents.append({"role": "user" if role == "user" else "model", "parts": parts})

        api_key = decrypt_api_key(self.provider.api_key_encrypted) if self.provider.api_key_encrypted else None
        if not api_key:
            raise ValueError("Gemini API key is missing")

        version = (self.provider.config_json or {}).get("api_version", "v1beta")
        base_url = (self.provider.base_url or "https://generativelanguage.googleapis.com").rstrip("/")

        model_path = model.strip()
        if model_path and not model_path.startswith("models/"):
            model_path = f"models/{model_path}"

        payload: Dict[str, Any] = {"contents": contents}
        if system_text:
            payload["system_instruction"] = {"parts": [{"text": system_text}]}
        if temperature is not None:
            payload.setdefault("generationConfig", {})["temperature"] = float(temperature)
        if max_tokens is not None:
            payload.setdefault("generationConfig", {})["maxOutputTokens"] = int(max_tokens)

        url = f"{base_url}/{version}/{model_path}:generateContent"
        resp = requests.post(url, params={"key": api_key}, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        text_parts: List[str] = []
        for candidate in data.get("candidates", []):
            content = candidate.get("content") or {}
            for part in content.get("parts", []) or []:
                text_parts.append(part.get("text") or "")
        text = "".join(text_parts)

        if stream:
            return self._build_openai_like_stream(text)
        return self._build_openai_like_response(text)
