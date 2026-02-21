# app/workers/embedding/embedding_resolver.py
"""
Embedding Model Resolver for the Embedding Worker.

This module handles resolving and loading embedding models with a multi-strategy
approach: LiteLLM API first, then local HuggingFace fallback.

Strategy:
    1. Models available via LiteLLM/KIZ (e.g., VDR-2B) -> try API first, fallback to local
    2. Local-only models (sentence-transformers) -> use HuggingFace directly
    3. Other models -> try LiteLLM, fallback to local

Important:
    For VDR-2B multimodal model, we use LiteLLMDirectEmbeddings instead of
    langchain's OpenAIEmbeddings. This is critical because langchain's
    OpenAIEmbeddings produces DIFFERENT embeddings than direct API calls.
    Query embeddings use LiteLLMDirectEmbeddings, so document embeddings must match.

Author: LLARS Team
Date: January 2026
"""

import logging
import os
import sys
from typing import Dict, Any, Optional

from workers.embedding.constants import LITELLM_EMBEDDING_MODELS

logger = logging.getLogger(__name__)


class EmbeddingResolver:
    """
    Resolves and caches embedding models for document processing.

    Supports multiple embedding strategies with automatic fallback:
    - LiteLLM API (for KIZ-hosted models like VDR-2B)
    - Local HuggingFace (for sentence-transformers and fallback)

    Attributes:
        _cache: Dict mapping model_id to loaded embeddings
        _pipeline: Reference to RAGPipeline for default embeddings

    Example:
        >>> resolver = EmbeddingResolver(pipeline)
        >>> embeddings = resolver.get_embeddings("llamaindex/vdr-2b-multi-v1")
        >>> vectors = embeddings.embed_documents(["text1", "text2"])
    """

    def __init__(self, pipeline):
        """
        Initialize the embedding resolver.

        Args:
            pipeline: RAGPipeline instance providing default embeddings
                     and model directory configuration
        """
        self._cache: Dict[str, Any] = {}
        self._pipeline = pipeline

    def get_embeddings(self, model_id: str) -> Any:
        """
        Get embeddings for a specific model with caching.

        Implements a multi-strategy approach:
        1. Check cache first
        2. If same as pipeline model, use pipeline's embeddings
        3. For local-only models, use HuggingFace directly
        4. For LiteLLM models, try API first, fallback to local
        5. Ultimate fallback to pipeline's embeddings

        Args:
            model_id: The model identifier (e.g., "llamaindex/vdr-2b-multi-v1")

        Returns:
            Embedding model instance (LangChain compatible)

        Note:
            Results are cached per model_id for efficiency
        """
        # Check cache first
        if model_id in self._cache:
            return self._cache[model_id]

        # If it's the same model as pipeline, use pipeline's embeddings
        if model_id == self._pipeline.model_name:
            self._cache[model_id] = self._pipeline.embeddings
            return self._pipeline.embeddings

        # Determine strategy based on model type
        is_local_only = self._is_local_only_model(model_id)

        # Strategy 1: Local-only models -> HuggingFace directly
        if is_local_only:
            embeddings = self._try_huggingface_local(model_id)
            if embeddings:
                return embeddings

        # Strategy 2: Models available via LiteLLM -> try API first, then local
        elif model_id in LITELLM_EMBEDDING_MODELS:
            embeddings = self._try_litellm(model_id)
            if embeddings:
                return embeddings
            logger.info(f"[EmbeddingResolver] LiteLLM unavailable for {model_id}, trying local")
            embeddings = self._try_huggingface_local(model_id)
            if embeddings:
                return embeddings

        # Strategy 3: Other models -> try LiteLLM, then local
        else:
            embeddings = self._try_litellm(model_id)
            if embeddings:
                return embeddings
            embeddings = self._try_huggingface_local(model_id)
            if embeddings:
                return embeddings

        # Ultimate fallback to pipeline's embeddings
        logger.warning(f"[EmbeddingResolver] Using pipeline fallback for {model_id}")
        return self._pipeline.embeddings

    def _is_local_only_model(self, model_id: str) -> bool:
        """
        Check if a model should only be loaded locally.

        Args:
            model_id: The model identifier

        Returns:
            True if the model is local-only (no API available)
        """
        return (
            model_id.startswith("sentence-transformers/") or
            "sentence-transformers" in model_id
        )

    def _try_litellm(self, model_id: str) -> Optional[Any]:
        """
        Try loading model via LiteLLM/KIZ API.

        For VDR-2B multimodal model, uses LiteLLMDirectEmbeddings to ensure
        consistency with query embeddings.

        Args:
            model_id: The model identifier

        Returns:
            Embedding model instance or None if unavailable

        Environment:
            LITELLM_API_KEY: API key for LiteLLM
            LITELLM_BASE_URL: Base URL for LiteLLM API
        """
        litellm_api_key = os.environ.get("LITELLM_API_KEY")
        litellm_base_url = os.environ.get("LITELLM_BASE_URL")

        if not litellm_api_key or not litellm_base_url:
            return None

        # For VDR-2B multimodal model, use LiteLLMDirectEmbeddings
        if model_id == "llamaindex/vdr-2b-multi-v1":
            embeddings = self._try_litellm_direct(model_id)
            if embeddings:
                return embeddings

        # For other models, use langchain's OpenAIEmbeddings
        return self._try_litellm_openai(model_id, litellm_api_key, litellm_base_url)

    def _try_litellm_direct(self, model_id: str) -> Optional[Any]:
        """
        Try loading VDR-2B via LiteLLMDirectEmbeddings.

        This method ensures consistency between document and query embeddings
        by using the same embedding class.

        Args:
            model_id: The model identifier

        Returns:
            LiteLLMDirectEmbeddings instance or None
        """
        try:
            from services.rag.image_embedding_service import LiteLLMDirectEmbeddings

            logger.info(f"[EmbeddingResolver] Using LiteLLMDirectEmbeddings for: {model_id}")
            embeddings = LiteLLMDirectEmbeddings(model=model_id)

            # Test the connection
            test_result = embeddings.embed_query("test")
            if test_result and len(test_result) > 0:
                self._cache[model_id] = embeddings
                logger.info(
                    f"[EmbeddingResolver] LiteLLMDirectEmbeddings ready: {model_id} "
                    f"(dims={len(test_result)})"
                )
                return embeddings
            return None

        except Exception as e:
            logger.warning(f"[EmbeddingResolver] LiteLLMDirectEmbeddings failed: {e}")
            return None

    def _try_litellm_openai(
        self,
        model_id: str,
        api_key: str,
        base_url: str
    ) -> Optional[Any]:
        """
        Try loading model via LangChain's OpenAIEmbeddings.

        Args:
            model_id: The model identifier
            api_key: LiteLLM API key
            base_url: LiteLLM base URL

        Returns:
            OpenAIEmbeddings instance or None
        """
        try:
            from langchain_openai import OpenAIEmbeddings

            logger.info(f"[EmbeddingResolver] Trying LiteLLM OpenAI for: {model_id}")
            embeddings = OpenAIEmbeddings(
                model=model_id,
                openai_api_key=api_key,
                openai_api_base=base_url
            )

            # Test the connection
            test_result = embeddings.embed_query("test")
            if test_result and len(test_result) > 0:
                self._cache[model_id] = embeddings
                logger.info(
                    f"[EmbeddingResolver] LiteLLM OpenAI ready: {model_id} "
                    f"(dims={len(test_result)})"
                )
                return embeddings
            return None

        except Exception as e:
            logger.warning(f"[EmbeddingResolver] LiteLLM OpenAI failed: {e}")
            return None

    def _try_huggingface_local(self, model_id: str) -> Optional[Any]:
        """
        Try loading model locally via HuggingFace.

        Handles models with custom code by adding model cache directories
        to sys.path for custom module imports.

        Args:
            model_id: The model identifier

        Returns:
            HuggingFaceEmbeddings instance or None
        """
        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            logger.info(f"[EmbeddingResolver] Loading local HuggingFace: {model_id}")

            # Add custom module paths for models with custom code
            self._add_custom_module_paths()

            embeddings = HuggingFaceEmbeddings(
                model_name=model_id,
                model_kwargs={"device": "cpu", "trust_remote_code": True},
                encode_kwargs={"normalize_embeddings": True},
                cache_folder=self._pipeline.model_dir
            )

            self._cache[model_id] = embeddings
            logger.info(f"[EmbeddingResolver] Local HuggingFace ready: {model_id}")
            return embeddings

        except Exception as e:
            logger.error(f"[EmbeddingResolver] Local HuggingFace failed: {e}")
            return None

    def _add_custom_module_paths(self) -> None:
        """
        Add model cache directories to sys.path for custom module imports.

        Some models (like llamaindex/vdr-2b-multi-v1) require custom Python
        modules that are downloaded with the model files.
        """
        cache_dirs = [
            os.path.expanduser("~/.cache/huggingface/hub"),
            self._pipeline.model_dir,
            "/app/storage/models"
        ]

        for cache_dir in cache_dirs:
            if not os.path.exists(cache_dir):
                continue

            for root, dirs, files in os.walk(cache_dir):
                if 'custom_st.py' in files and root not in sys.path:
                    logger.info(f"[EmbeddingResolver] Adding custom module path: {root}")
                    sys.path.insert(0, root)

    def clear_cache(self) -> None:
        """
        Clear the embedding model cache.

        Useful for testing or when models need to be reloaded.
        """
        self._cache.clear()
        logger.info("[EmbeddingResolver] Cache cleared")
