"""
Embedding Model Service.

Centralized service for:
- Checking embedding model availability (LiteLLM vs local HuggingFace)
- Loading embeddings with proper fallback chains
- Finding best available embedding for a collection

Fallback chain priority:
1. VDR-2B via LiteLLM/KIZ (1024 dims) - preferred
2. VDR-2B local HuggingFace (1024 dims) - fallback if KIZ unavailable
3. MiniLM local (384 dims) - last resort fallback
"""

import os
import logging
import threading
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelSource(Enum):
    """Source where the embedding model is loaded from."""
    LITELLM = "litellm"
    LOCAL = "local"
    UNKNOWN = "unknown"


@dataclass
class ModelInfo:
    """Information about an embedding model."""
    model_id: str
    source: ModelSource
    dimensions: int
    is_available: bool
    error: Optional[str] = None


# Embedding model priorities (higher = preferred)
MODEL_PRIORITIES = {
    "llamaindex/vdr-2b-multi-v1": 100,  # Best quality, preferred
    "sentence-transformers/all-MiniLM-L6-v2": 50,  # Good fallback
}

# Models that should try LiteLLM/KIZ first
LITELLM_PREFERRED_MODELS = [
    "llamaindex/vdr-2b-multi-v1",
]

# Models that are local-only (no API available)
LOCAL_ONLY_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",
]

# Default fallback model
DEFAULT_FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingModelService:
    """
    Service for managing embedding models with robust fallback chains.

    Thread-safe singleton with caching of loaded embeddings.
    """

    _instance = None
    _lock = threading.Lock()

    # Cache for loaded embeddings
    _embeddings_cache: Dict[str, Any] = {}
    _model_info_cache: Dict[str, ModelInfo] = {}
    _cache_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'EmbeddingModelService':
        """Get singleton instance."""
        return cls()

    def check_model_availability(self, model_id: str, force_refresh: bool = False) -> ModelInfo:
        """
        Check if an embedding model is available.

        Args:
            model_id: The model ID to check
            force_refresh: If True, bypass cache and re-check

        Returns:
            ModelInfo with availability status
        """
        cache_key = model_id

        if not force_refresh:
            with self._cache_lock:
                if cache_key in self._model_info_cache:
                    return self._model_info_cache[cache_key]

        # Check availability
        embeddings, source, dims, error = self._try_load_model(model_id)

        info = ModelInfo(
            model_id=model_id,
            source=source,
            dimensions=dims or 0,
            is_available=embeddings is not None,
            error=error
        )

        with self._cache_lock:
            self._model_info_cache[cache_key] = info
            if embeddings is not None:
                self._embeddings_cache[model_id] = embeddings

        return info

    def get_embeddings(self, model_id: str) -> Optional[Any]:
        """
        Get embeddings for a specific model.

        Returns None if model is not available.
        """
        with self._cache_lock:
            if model_id in self._embeddings_cache:
                return self._embeddings_cache[model_id]

        # Try to load
        embeddings, source, dims, error = self._try_load_model(model_id)

        if embeddings is not None:
            with self._cache_lock:
                self._embeddings_cache[model_id] = embeddings
                self._model_info_cache[model_id] = ModelInfo(
                    model_id=model_id,
                    source=source,
                    dimensions=dims,
                    is_available=True
                )

        return embeddings

    def get_best_available_embedding(
        self,
        collection_id: int,
        preferred_model: Optional[str] = None
    ) -> Tuple[Optional[Any], Optional[str], Optional[str], Optional[int]]:
        """
        Get the best available embedding for a collection.

        This checks:
        1. Collection's configured embedding model
        2. Collection's stored embeddings (from collection_embeddings table)
        3. Falls back through the priority chain

        Args:
            collection_id: The collection ID
            preferred_model: Optional preferred model to try first

        Returns:
            Tuple of (embeddings, model_id, chroma_collection_name, dimensions) or (None, None, None, None)
        """
        from db.models.rag import RAGCollection, CollectionEmbedding

        try:
            collection = RAGCollection.query.get(collection_id)
            if not collection:
                logger.error(f"[EmbeddingModelService] Collection {collection_id} not found")
                return None, None, None, None

            # Strategy 1: Check collection_embeddings table for available embeddings
            available_embeddings = (
                CollectionEmbedding.query
                .filter_by(collection_id=collection_id, status='completed')
                .order_by(CollectionEmbedding.priority.desc())
                .all()
            )

            for coll_emb in available_embeddings:
                # Try to load the model
                embeddings = self.get_embeddings(coll_emb.model_id)
                if embeddings is not None:
                    logger.info(
                        f"[EmbeddingModelService] Using stored embedding {coll_emb.model_id} "
                        f"for collection {collection_id}"
                    )
                    return (
                        embeddings,
                        coll_emb.model_id,
                        coll_emb.chroma_collection_name,
                        coll_emb.embedding_dimensions
                    )
                else:
                    logger.warning(
                        f"[EmbeddingModelService] Model {coll_emb.model_id} is stored but not available"
                    )

            # Strategy 2: Try the collection's configured embedding_model
            if collection.embedding_model:
                embeddings = self.get_embeddings(collection.embedding_model)
                if embeddings is not None:
                    info = self._model_info_cache.get(collection.embedding_model)
                    dims = info.dimensions if info else None
                    return (
                        embeddings,
                        collection.embedding_model,
                        collection.chroma_collection_name,
                        dims
                    )

            # Strategy 3: Try preferred model if specified
            if preferred_model:
                embeddings = self.get_embeddings(preferred_model)
                if embeddings is not None:
                    info = self._model_info_cache.get(preferred_model)
                    dims = info.dimensions if info else None
                    return embeddings, preferred_model, None, dims

            logger.error(
                f"[EmbeddingModelService] No available embedding model for collection {collection_id}. "
                f"Stored embeddings: {[e.model_id for e in available_embeddings]}, "
                f"Configured model: {collection.embedding_model}"
            )
            return None, None, None, None

        except Exception as e:
            logger.error(f"[EmbeddingModelService] Error getting embedding for collection {collection_id}: {e}")
            return None, None, None, None

    def get_all_available_models(self) -> List[ModelInfo]:
        """
        Get all available embedding models.

        Returns list of ModelInfo for all models that can be loaded.
        """
        models_to_check = list(MODEL_PRIORITIES.keys())
        available = []

        for model_id in models_to_check:
            info = self.check_model_availability(model_id)
            if info.is_available:
                available.append(info)

        # Sort by priority
        available.sort(key=lambda x: MODEL_PRIORITIES.get(x.model_id, 0), reverse=True)
        return available

    def _try_load_model(self, model_id: str) -> Tuple[Optional[Any], ModelSource, Optional[int], Optional[str]]:
        """
        Try to load an embedding model.

        Returns:
            Tuple of (embeddings, source, dimensions, error_message)
        """
        # Check if local-only
        is_local_only = (
            model_id in LOCAL_ONLY_MODELS or
            model_id.startswith("sentence-transformers/")
        )

        # Check if LiteLLM-preferred
        is_litellm_preferred = model_id in LITELLM_PREFERRED_MODELS

        # Strategy 1: Local-only models -> HuggingFace directly
        if is_local_only:
            return self._try_huggingface(model_id)

        # Strategy 2: LiteLLM-preferred models -> try API first, then local
        if is_litellm_preferred:
            embeddings, source, dims, error = self._try_litellm(model_id)
            if embeddings is not None:
                return embeddings, source, dims, None
            logger.info(f"[EmbeddingModelService] LiteLLM unavailable for {model_id}, trying local HuggingFace")
            return self._try_huggingface(model_id)

        # Strategy 3: Other models -> try LiteLLM, then local
        embeddings, source, dims, error = self._try_litellm(model_id)
        if embeddings is not None:
            return embeddings, source, dims, None
        return self._try_huggingface(model_id)

    def _try_litellm(self, model_id: str) -> Tuple[Optional[Any], ModelSource, Optional[int], Optional[str]]:
        """Try loading model via LiteLLM/KIZ API."""
        litellm_api_key = os.environ.get("LITELLM_API_KEY")
        litellm_base_url = os.environ.get("LITELLM_BASE_URL")

        if not litellm_api_key or not litellm_base_url:
            return None, ModelSource.UNKNOWN, None, "LiteLLM not configured"

        try:
            from langchain_openai import OpenAIEmbeddings

            logger.info(f"[EmbeddingModelService] Attempting LiteLLM for {model_id}")
            embeddings = OpenAIEmbeddings(
                model=model_id,
                openai_api_key=litellm_api_key,
                openai_api_base=litellm_base_url
            )

            # Test that it works
            test_result = embeddings.embed_query("test")
            if test_result and len(test_result) > 0:
                dims = len(test_result)
                logger.info(f"[EmbeddingModelService] LiteLLM ready for {model_id} ({dims} dims)")
                return embeddings, ModelSource.LITELLM, dims, None
            else:
                return None, ModelSource.UNKNOWN, None, "LiteLLM returned empty embeddings"

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"[EmbeddingModelService] LiteLLM failed for {model_id}: {error_msg}")
            return None, ModelSource.UNKNOWN, None, error_msg

    def _try_huggingface(self, model_id: str) -> Tuple[Optional[Any], ModelSource, Optional[int], Optional[str]]:
        """Try loading model via local HuggingFace."""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            logger.info(f"[EmbeddingModelService] Attempting HuggingFace for {model_id}")

            # Set up model cache directory
            model_dir = os.environ.get("HF_HOME", "/app/storage/models")

            embeddings = HuggingFaceEmbeddings(
                model_name=model_id,
                model_kwargs={"device": "cpu", "trust_remote_code": True},
                encode_kwargs={"normalize_embeddings": True},
                cache_folder=model_dir
            )

            # Test that it works
            test_result = embeddings.embed_query("test")
            if test_result and len(test_result) > 0:
                dims = len(test_result)
                logger.info(f"[EmbeddingModelService] HuggingFace ready for {model_id} ({dims} dims)")
                return embeddings, ModelSource.LOCAL, dims, None
            else:
                return None, ModelSource.UNKNOWN, None, "HuggingFace returned empty embeddings"

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"[EmbeddingModelService] HuggingFace failed for {model_id}: {error_msg}")
            return None, ModelSource.UNKNOWN, None, error_msg

    def clear_cache(self):
        """Clear all caches (useful for testing or after config changes)."""
        with self._cache_lock:
            self._embeddings_cache.clear()
            self._model_info_cache.clear()
        logger.info("[EmbeddingModelService] Cache cleared")


# Convenience functions
def get_embedding_model_service() -> EmbeddingModelService:
    """Get the singleton embedding model service."""
    return EmbeddingModelService.get_instance()


def check_model_availability(model_id: str) -> ModelInfo:
    """Check if an embedding model is available."""
    return get_embedding_model_service().check_model_availability(model_id)


def get_embeddings_for_model(model_id: str) -> Optional[Any]:
    """Get embeddings for a specific model."""
    return get_embedding_model_service().get_embeddings(model_id)


def get_best_embedding_for_collection(
    collection_id: int,
    preferred_model: Optional[str] = None
) -> Tuple[Optional[Any], Optional[str], Optional[str], Optional[int]]:
    """Get the best available embedding for a collection."""
    return get_embedding_model_service().get_best_available_embedding(
        collection_id, preferred_model
    )
