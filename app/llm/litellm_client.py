"""
LiteLLM Client - OpenAI-compatible interface to LiteLLM Proxy

Provides access to Mistral models via TH Nürnberg's LiteLLM Proxy at
https://kiz1.in.ohmportal.de/llmproxy/v1

Key Features:
- Simple OpenAI client usage
- Support for streaming responses
- Metadata tags for TH Nürnberg / KIA tracking
- JSON mode support
"""

import logging
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from llm.openai_utils import extract_delta_text, extract_message_text
from db.models.llm_model import LLMModel

logger = logging.getLogger(__name__)


class LiteLLMClient:
    """
    LiteLLM Proxy Client - OpenAI-compatible interface to LiteLLM Gateway

    Provides simple access to Mistral models hosted on TH Nürnberg's infrastructure.
    """

    DEFAULT_BASE_URL = "https://kiz1.in.ohmportal.de/llmproxy/v1"
    DEFAULT_MODEL = None
    METADATA_TAGS = ["Technische Hochschule Nürnberg", "prj-llars"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize LiteLLM client.

        Args:
            api_key: API key for authentication (default: from LITELLM_API_KEY env var)
            base_url: Base URL for LiteLLM proxy (default: from LITELLM_BASE_URL env var)
            model: Model to use (default: Mistral-Small-3.2-24B-Instruct-2506)
        """
        self.api_key = api_key or os.getenv("LITELLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LITELLM_API_KEY must be provided or set in environment variables"
            )

        self.base_url = base_url or os.getenv("LITELLM_BASE_URL", self.DEFAULT_BASE_URL)
        if model:
            self.model = model
        else:
            default_model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
            if not default_model_id:
                raise ValueError("No default LLM model configured in llm_models")
            self.model = default_model_id

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        logger.info(f"[LiteLLM] Initialized client with model={self.model}, base_url={self.base_url}")

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Optional[str]:
        """
        Generate a completion (non-streaming).

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API

        Returns:
            Generated text or None on error
        """
        try:
            # Add metadata
            metadata = {"tags": self.METADATA_TAGS}

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"metadata": metadata},
                **kwargs
            )

            if response.choices:
                content = extract_message_text(response.choices[0].message)
                logger.debug(f"[LiteLLM] Generated {len(content)} characters")
                return content

            return None

        except Exception as e:
            logger.error(f"[LiteLLM] Error during completion: {e}")
            return None

    def stream_complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Generate a streaming completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API

        Yields:
            Text deltas from the streaming response
        """
        try:
            # Add metadata
            metadata = {"tags": self.METADATA_TAGS}

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                extra_body={"metadata": metadata},
                **kwargs
            )

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = extract_delta_text(delta)
                if content:
                    yield content

        except Exception as e:
            logger.error(f"[LiteLLM] Error during streaming: {e}")
            return


def create_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None
) -> LiteLLMClient:
    """
    Factory function to create a LiteLLM client.

    Args:
        api_key: API key for authentication
        base_url: Base URL for LiteLLM proxy
        model: Model to use

    Returns:
        Configured LiteLLMClient instance
    """
    return LiteLLMClient(api_key=api_key, base_url=base_url, model=model)
