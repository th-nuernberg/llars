"""
Shared LLM execution helpers.

Centralizes completion parameter handling and provider-specific retries/fixes
for all chat.completions.create() call sites.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class LLMExecutionService:
    """Shared execution layer for provider-aware completion calls."""

    MAX_PARAM_FIX_RETRIES = 3

    # Model-specific hints learned from previous unsupported-parameter errors.
    _param_fix_hints: Dict[str, Set[str]] = {}
    _hints_lock = threading.Lock()

    @staticmethod
    def supports_sampling_params(api_model_id: str) -> bool:
        """
        Heuristic for models that reject temperature/top_p.

        GPT-5 and OpenAI o-series often reject custom sampling params.
        """
        model = (api_model_id or "").strip().lower()
        return not (
            model.startswith("gpt-5")
            or model.startswith("o1")
            or model.startswith("o3")
            or model.startswith("o4")
        )

    @classmethod
    def clear_param_fix_hints(cls) -> None:
        """Clear learned parameter-fix hints (mainly useful for tests)."""
        with cls._hints_lock:
            cls._param_fix_hints.clear()

    @classmethod
    def build_chat_completion_params(
        cls,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        extra_body: Optional[Dict[str, Any]] = None,
        request_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build normalized chat completion params.

        Applies preflight model heuristics to avoid known unsupported params.
        """
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if stream:
            params["stream"] = True

        if cls.supports_sampling_params(model):
            if temperature is not None:
                params["temperature"] = temperature
            if top_p is not None:
                params["top_p"] = top_p

        if max_tokens is not None and int(max_tokens) > 0:
            params["max_tokens"] = int(max_tokens)

        if extra_body:
            params["extra_body"] = extra_body
        if request_kwargs:
            for key, value in request_kwargs.items():
                params.setdefault(key, value)

        return params

    @classmethod
    def execute_chat_completion(
        cls,
        client,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        extra_body: Optional[Dict[str, Any]] = None,
        request_kwargs: Optional[Dict[str, Any]] = None,
        model_key: Optional[str] = None,
        max_param_fix_retries: int = MAX_PARAM_FIX_RETRIES,
    ):
        """Build params and execute completion with provider-specific retries."""
        params = cls.build_chat_completion_params(
            model=model,
            messages=messages,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            extra_body=extra_body,
            request_kwargs=request_kwargs,
        )
        return cls.execute_with_param_fixes(
            client,
            params,
            model_key=model_key or model,
            max_param_fix_retries=max_param_fix_retries,
        )

    @classmethod
    def execute_with_param_fixes(
        cls,
        client,
        params: Dict[str, Any],
        *,
        model_key: Optional[str] = None,
        max_param_fix_retries: int = MAX_PARAM_FIX_RETRIES,
    ):
        """
        Execute chat completion and retry with safe parameter fixes on 400-style errors.
        """
        request_params = dict(params)
        key = cls._normalize_model_key(model_key or str(request_params.get("model") or ""))
        cls._apply_known_param_fixes(key, request_params)

        retries = max(1, int(max_param_fix_retries))
        for _ in range(retries):
            try:
                return client.chat.completions.create(**request_params)
            except Exception as exc:
                err_text = str(exc)
                if not cls._apply_fix_from_error(key, request_params, err_text):
                    raise

        return client.chat.completions.create(**request_params)

    @staticmethod
    def _normalize_model_key(model_key: Optional[str]) -> Optional[str]:
        normalized = (model_key or "").strip()
        return normalized or None

    @classmethod
    def _apply_known_param_fixes(cls, model_key: Optional[str], params: Dict[str, Any]) -> None:
        if not model_key:
            return
        with cls._hints_lock:
            hints = set(cls._param_fix_hints.get(model_key, set()))
        if not hints:
            return
        if "drop_temperature" in hints:
            params.pop("temperature", None)
        if "drop_top_p" in hints:
            params.pop("top_p", None)
        if "drop_max_tokens" in hints:
            params.pop("max_tokens", None)
            params.pop("max_completion_tokens", None)

    @classmethod
    def _remember_fix(cls, model_key: Optional[str], fix_name: str) -> None:
        if not model_key:
            return
        with cls._hints_lock:
            hints = cls._param_fix_hints.setdefault(model_key, set())
            hints.add(fix_name)

    @classmethod
    def _apply_fix_from_error(
        cls,
        model_key: Optional[str],
        params: Dict[str, Any],
        error_text: str,
    ) -> bool:
        err = (error_text or "").lower()

        if "temperature" in params and "temperature" in err and (
            "unsupported" in err or "not support" in err or "only the default" in err
        ):
            params.pop("temperature", None)
            cls._remember_fix(model_key, "drop_temperature")
            logger.info("[LLMExec] Dropping unsupported temperature for model=%s", model_key)
            return True

        if "top_p" in params and "top_p" in err and (
            "unsupported" in err or "not support" in err
        ):
            params.pop("top_p", None)
            cls._remember_fix(model_key, "drop_top_p")
            logger.info("[LLMExec] Dropping unsupported top_p for model=%s", model_key)
            return True

        if "max_tokens" in params and "max_tokens" in err and (
            "unsupported" in err or "not support" in err or "max_completion_tokens" in err
        ):
            params.pop("max_tokens", None)
            cls._remember_fix(model_key, "drop_max_tokens")
            logger.info("[LLMExec] Dropping unsupported max_tokens for model=%s", model_key)
            return True

        if "max_completion_tokens" in params and "max_completion_tokens" in err and (
            "unsupported" in err or "not support" in err
        ):
            params.pop("max_completion_tokens", None)
            cls._remember_fix(model_key, "drop_max_tokens")
            logger.info("[LLMExec] Dropping unsupported max_completion_tokens for model=%s", model_key)
            return True

        return False
