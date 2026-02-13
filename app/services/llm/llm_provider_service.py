"""
LLM Provider Service

CRUD and utility helpers for provider registry.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from db.database import db
from db.models.llm_model import LLMModel
from db.models.llm_provider import LLMProvider
from services.llm.secret_encryption import encrypt_api_key, decrypt_api_key
from services.llm.model_sync_service import LLMModelSyncService

logger = logging.getLogger(__name__)

OPENAI_COMPATIBLE_TYPES = {
    "openai",
    "litellm",
    "ollama",
    "vllm",
    "openai_compatible",
}

KNOWN_PROVIDER_TYPES = OPENAI_COMPATIBLE_TYPES | {"anthropic", "gemini", "custom"}


class LLMProviderService:
    """Provider registry management."""

    @staticmethod
    def get_default_provider() -> Optional[LLMProvider]:
        return (
            LLMProvider.query
            .filter_by(is_default=True, is_active=True)
            .order_by(LLMProvider.id.asc())
            .first()
        )

    @staticmethod
    def list_providers(include_inactive: bool = True) -> List[LLMProvider]:
        LLMProviderService.ensure_env_providers()
        query = LLMProvider.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(LLMProvider.created_at.desc()).all()

    @staticmethod
    def _collect_litellm_env_configs() -> List[Dict[str, Any]]:
        configs: List[Dict[str, Any]] = []
        for key, value in os.environ.items():
            if not key.startswith("LITELLM_BASE_URL"):
                continue
            base_url = (value or "").strip()
            if not base_url:
                continue
            suffix = key[len("LITELLM_BASE_URL"):]
            api_key = (os.environ.get(f"LITELLM_API_KEY{suffix}") or "").strip() or None
            label = suffix.lstrip("_").replace("_", " ").strip()
            parsed = urlparse(base_url)
            host_label = parsed.netloc or base_url
            if parsed.path and parsed.path not in ("", "/"):
                host_label = f"{host_label}{parsed.path}"
            if label:
                name = f"LiteLLM Proxy {label}"
            elif host_label:
                name = f"LiteLLM Proxy ({host_label})"
            else:
                name = "LiteLLM Proxy"
            configs.append({
                "name": name,
                "base_url": base_url,
                "api_key": api_key,
                "is_primary": suffix == "",
            })
        return configs

    @staticmethod
    def ensure_env_providers() -> int:
        configs = LLMProviderService._collect_litellm_env_configs()

        # Also collect OpenAI provider from OPENAI_API_KEY env var
        openai_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
        if openai_key:
            configs.append({
                "provider_type": "openai",
                "name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "api_key": openai_key,
                "is_primary": False,
            })

        if not configs:
            return 0

        existing = LLMProvider.query.all()
        existing_urls = {((p.base_url or "").rstrip("/")) for p in existing if p.base_url}
        default_exists = any(p.is_default and p.is_active for p in existing)

        created = 0
        new_providers = []
        for cfg in sorted(configs, key=lambda c: not c.get("is_primary", False)):
            base_url = (cfg.get("base_url") or "").rstrip("/")
            if not base_url or base_url in existing_urls:
                continue
            provider_type = cfg.get("provider_type", "litellm")
            provider = LLMProvider(
                provider_type=provider_type,
                name=cfg["name"],
                base_url=base_url,
                api_key_encrypted=encrypt_api_key(cfg["api_key"]) if cfg.get("api_key") else None,
                config_json={"source": "env"},
                is_active=True,
                is_default=False,
                is_openai_compatible=True,
            )
            if not default_exists and cfg.get("is_primary", False):
                provider.is_default = True
                default_exists = True
            db.session.add(provider)
            new_providers.append(provider)
            existing_urls.add(base_url)
            created += 1

        if created:
            db.session.commit()
            # Link orphaned models to the newly created default provider
            LLMProviderService._link_orphaned_models()

        return created

    @staticmethod
    def _link_orphaned_models():
        """Link models without provider_id to the default provider."""
        default_provider = LLMProviderService.get_default_provider()
        if not default_provider:
            return
        orphaned = LLMModel.query.filter(
            LLMModel.provider_id.is_(None),
            LLMModel.is_active.is_(True),
        ).all()
        for model in orphaned:
            model.provider_id = default_provider.id
            logger.info("Linked model '%s' to provider '%s'", model.model_id, default_provider.name)
        if orphaned:
            db.session.commit()

    @staticmethod
    def create_provider(data: Dict[str, Any]) -> LLMProvider:
        provider_type = (data.get("provider_type") or data.get("type") or "").strip().lower()
        if not provider_type or provider_type not in KNOWN_PROVIDER_TYPES:
            raise ValueError("provider_type is required and must be a known type")

        name = (data.get("name") or provider_type.upper()).strip()
        if not name:
            raise ValueError("name is required")

        base_url = (data.get("base_url") or "").strip() or None
        is_active = bool(data.get("is_active", True))
        is_default = bool(data.get("is_default", False))

        is_openai_compatible = bool(data.get("is_openai_compatible", provider_type in OPENAI_COMPATIBLE_TYPES))

        api_key = data.get("api_key")
        api_key_encrypted = encrypt_api_key(api_key) if api_key else None

        provider = LLMProvider(
            provider_type=provider_type,
            name=name,
            base_url=base_url,
            api_key_encrypted=api_key_encrypted,
            config_json=data.get("config") or {},
            is_active=is_active,
            is_default=is_default,
            is_openai_compatible=is_openai_compatible,
        )

        if provider.is_default:
            LLMProvider.query.update({"is_default": False})

        db.session.add(provider)
        db.session.commit()
        return provider

    @staticmethod
    def update_provider(provider_id: int, data: Dict[str, Any]) -> LLMProvider:
        provider = LLMProvider.query.get(provider_id)
        if not provider:
            raise ValueError("Provider not found")

        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                raise ValueError("name is required")
            provider.name = name

        if "base_url" in data:
            base_url = (data.get("base_url") or "").strip() or None
            provider.base_url = base_url

        if "is_active" in data:
            provider.is_active = bool(data.get("is_active"))

        if "is_default" in data:
            provider.is_default = bool(data.get("is_default"))
            if provider.is_default:
                LLMProvider.query.filter(LLMProvider.id != provider.id).update({"is_default": False})

        if "is_openai_compatible" in data:
            provider.is_openai_compatible = bool(data.get("is_openai_compatible"))

        if "provider_type" in data:
            provider_type = (data.get("provider_type") or "").strip().lower()
            if not provider_type or provider_type not in KNOWN_PROVIDER_TYPES:
                raise ValueError("provider_type must be a known type")
            provider.provider_type = provider_type

        if "api_key" in data:
            api_key = data.get("api_key")
            if api_key == "":
                provider.api_key_encrypted = None
            elif api_key:
                provider.api_key_encrypted = encrypt_api_key(api_key)

        if "config" in data:
            provider.config_json = data.get("config") or {}

        db.session.commit()
        return provider

    @staticmethod
    def _get_api_key(provider: LLMProvider) -> Optional[str]:
        if not provider or not provider.api_key_encrypted:
            return None
        return decrypt_api_key(provider.api_key_encrypted)

    @staticmethod
    def test_connection(
        provider_type: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Test a provider connection without saving.

        Args:
            provider_type: Type of provider (openai, anthropic, ollama, etc.)
            base_url: Base URL for the provider API
            api_key: API key (optional for some providers like Ollama)
            config: Additional configuration options

        Returns:
            Dict with 'success' bool and 'error' or 'message'
        """
        provider_type = (provider_type or "").lower().strip()
        if not provider_type:
            return {"success": False, "error": "provider_type is required"}

        base_url = (base_url or "").rstrip("/")
        config = config or {}
        is_openai_compatible = provider_type in OPENAI_COMPATIBLE_TYPES

        try:
            if is_openai_compatible:
                if not base_url:
                    return {"success": False, "error": "base_url is required for OpenAI-compatible providers"}
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                resp = requests.get(f"{base_url}/models", headers=headers, timeout=10)
                if resp.status_code >= 400:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
                return {"success": True, "message": "Connection OK"}

            if provider_type == "anthropic":
                url = f"{base_url or 'https://api.anthropic.com'}/v1/models"
                headers = {
                    "x-api-key": api_key or "",
                    "anthropic-version": config.get("api_version", "2023-06-01"),
                }
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code >= 400:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
                return {"success": True, "message": "Connection OK"}

            if provider_type == "gemini":
                version = config.get("api_version", "v1beta")
                url = f"{base_url or 'https://generativelanguage.googleapis.com'}/{version}/models"
                resp = requests.get(url, params={"key": api_key or ""}, timeout=10)
                if resp.status_code >= 400:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
                return {"success": True, "message": "Connection OK"}

            return {"success": False, "error": "Provider type not supported for connection tests"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection refused - is the server running?"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Connection timed out"}
        except Exception as exc:
            logger.warning(f"[LLMProviderService] Connection test failed: {exc}")
            return {"success": False, "error": str(exc)}

    @staticmethod
    def test_provider(provider: LLMProvider) -> Dict[str, Any]:
        if not provider:
            raise ValueError("Provider not found")

        provider_type = (provider.provider_type or "").lower()
        base_url = (provider.base_url or "").rstrip("/")
        api_key = LLMProviderService._get_api_key(provider)

        try:
            if provider.is_openai_compatible:
                if not base_url:
                    return {"success": False, "error": "base_url is required for OpenAI-compatible providers"}
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                resp = requests.get(f"{base_url}/models", headers=headers, timeout=10)
                if resp.status_code >= 400:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
                return {"success": True, "message": "Connection OK"}

            if provider_type == "anthropic":
                url = f"{base_url or 'https://api.anthropic.com'}/v1/models"
                headers = {
                    "x-api-key": api_key or "",
                    "anthropic-version": (provider.config_json or {}).get("api_version", "2023-06-01"),
                }
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code >= 400:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
                return {"success": True, "message": "Connection OK"}

            if provider_type == "gemini":
                version = (provider.config_json or {}).get("api_version", "v1beta")
                url = f"{base_url or 'https://generativelanguage.googleapis.com'}/{version}/models"
                resp = requests.get(url, params={"key": api_key or ""}, timeout=10)
                if resp.status_code >= 400:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
                return {"success": True, "message": "Connection OK"}

            return {"success": False, "error": "Provider type not supported for tests"}
        except Exception as exc:
            logger.warning(f"[LLMProviderService] Test failed: {exc}")
            return {"success": False, "error": str(exc)}

    @staticmethod
    def sync_models(
        provider: LLMProvider,
        *,
        model_ids: Optional[List[str]] = None,
        model_metadata: Optional[Dict[str, Any]] = None,
        activate_existing: bool = True,
        synced_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not provider:
            raise ValueError("Provider not found")

        if model_ids:
            return LLMProviderService.register_models(
                provider,
                model_ids,
                model_metadata=model_metadata,
                activate_existing=activate_existing,
                synced_by=synced_by,
            )

        if not provider.is_openai_compatible:
            return {
                "success": False,
                "error": "Model sync is only supported for OpenAI-compatible providers without explicit model list",
            }

        return LLMModelSyncService.sync_from_provider(
            provider,
            activate_existing=activate_existing,
            synced_by=synced_by,
        )

    @staticmethod
    def register_models(
        provider: LLMProvider,
        model_ids: List[str],
        *,
        model_metadata: Optional[Dict[str, Any]] = None,
        activate_existing: bool = True,
        synced_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not provider:
            raise ValueError("Provider not found")

        clean_ids = sorted({m.strip() for m in model_ids if isinstance(m, str) and m.strip()})
        if not clean_ids:
            return {"success": False, "error": "No model_ids provided"}

        metadata = model_metadata or {}
        inserted = 0
        updated = 0
        skipped = 0

        for model_id in clean_ids:
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
                continue

            # Use frontend-provided metadata if available, otherwise infer
            meta = metadata.get(model_id) or {}
            inferred = LLMModelSyncService.infer_model_defaults(model_id)
            model = LLMModel(
                model_id=model_id,
                display_name=meta.get("display_name") or inferred["display_name"],
                provider=inferred["provider"],
                description=None,
                model_type=inferred["model_type"],
                color=LLMModel.generate_color(model_id),
                supports_vision=meta.get("supports_vision", inferred["supports_vision"]),
                supports_reasoning=meta.get("supports_reasoning", inferred["supports_reasoning"]),
                supports_function_calling=True,
                supports_streaming=True,
                context_window=meta.get("context_window") or inferred["context_window"],
                max_output_tokens=meta.get("max_output_tokens") or inferred["max_output_tokens"],
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
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
        }
