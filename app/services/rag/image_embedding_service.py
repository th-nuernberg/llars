"""
Image Embedding Service.

Provides VDR-2B Multi embeddings for images stored on disk.

Supports two backends:
1. LiteLLM Proxy (preferred) - Fast cluster-based processing
2. Local SentenceTransformer (fallback) - Slower, higher memory usage

The LiteLLM proxy accepts base64-encoded images as data URLs and returns
1024-dimensional embeddings directly compatible with text embeddings.

IMPORTANT: This module also provides LiteLLMDirectEmbeddings, a langchain-compatible
embedding class that uses direct HTTP requests to ensure consistency between
image embeddings and text query embeddings. This is critical because langchain's
OpenAIEmbeddings produces DIFFERENT embeddings than direct API calls.
"""

import base64
import gc
import math
import os
import logging
import threading
from typing import List, Optional

import requests
from PIL import Image

logger = logging.getLogger(__name__)


class LiteLLMDirectEmbeddings:
    """
    Langchain-compatible embedding class using direct HTTP requests.

    CRITICAL: This class exists because langchain's OpenAIEmbeddings produces
    DIFFERENT embeddings than direct API calls to the same endpoint. Since
    images are embedded using direct API calls, we MUST use the same method
    for text queries to ensure similarity search works correctly.

    Tested: Cosine similarity between OpenAIEmbeddings and direct API = 0.042
    (nearly orthogonal!) for the same input text.
    """

    def __init__(self, model: str = "llamaindex/vdr-2b-multi-v1"):
        self.model = model
        self._api_key = os.environ.get("LITELLM_API_KEY")
        self._base_url = os.environ.get("LITELLM_BASE_URL")

        if not self._api_key or not self._base_url:
            raise ValueError("LITELLM_API_KEY and LITELLM_BASE_URL must be set")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents (for storage)."""
        results = []
        for text in texts:
            embedding = self._embed_single(text)
            results.append(embedding if embedding else [0.0] * 1024)
        return results

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text (for retrieval)."""
        embedding = self._embed_single(text)
        return embedding if embedding else [0.0] * 1024

    def _embed_single(self, text: str) -> Optional[List[float]]:
        """Embed a single text using direct HTTP request."""
        try:
            response = requests.post(
                f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": text
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    embedding = data["data"][0].get("embedding", [])
                    if isinstance(embedding, list) and len(embedding) > 0:
                        return embedding
            else:
                logger.warning(f"[LiteLLMDirectEmbeddings] HTTP {response.status_code}: {response.text[:200]}")

        except Exception as e:
            logger.error(f"[LiteLLMDirectEmbeddings] Embedding failed: {e}")

        return None


def get_litellm_direct_embeddings(model_id: str = "llamaindex/vdr-2b-multi-v1") -> Optional[LiteLLMDirectEmbeddings]:
    """
    Get a LiteLLMDirectEmbeddings instance if LiteLLM is configured.

    This function provides a langchain-compatible embedding that uses the same
    direct API method as image embeddings, ensuring consistency.

    Returns None if LiteLLM is not configured or unavailable.
    """
    api_key = os.environ.get("LITELLM_API_KEY")
    base_url = os.environ.get("LITELLM_BASE_URL")

    if not api_key or not base_url:
        logger.info("[get_litellm_direct_embeddings] LiteLLM not configured")
        return None

    try:
        embeddings = LiteLLMDirectEmbeddings(model=model_id)
        # Test that it works
        test_result = embeddings.embed_query("test")
        if test_result and len(test_result) > 0:
            logger.info(f"[get_litellm_direct_embeddings] Ready ({len(test_result)} dims)")
            return embeddings
    except Exception as e:
        logger.warning(f"[get_litellm_direct_embeddings] Failed: {e}")

    return None


class ImageEmbeddingService:
    """Embed images using VDR-2B-Multi-V1 model.

    Prefers LiteLLM proxy for fast cluster-based embedding.
    Falls back to local SentenceTransformer if proxy unavailable.
    """

    _MODEL_ID = "llamaindex/vdr-2b-multi-v1"
    _model_cache = {}
    _lock = threading.Lock()
    _litellm_available = None  # Cache LiteLLM availability check

    # Target dimensions (LiteLLM returns 1024 directly, local needs truncation)
    TARGET_DIMENSIONS = 1024

    # Image processing settings for LiteLLM proxy context limits
    # The proxy has a ~43KB base64 limit (~32KB raw JPEG)
    MAX_IMAGE_SIZE = (512, 512)  # Max thumbnail dimension
    MAX_BASE64_BYTES = 42000  # ~42KB base64 limit (leaving margin)
    JPEG_QUALITY_START = 75  # Start with high quality
    JPEG_QUALITY_MIN = 25  # Don't go below this for quality
    DEFAULT_BATCH_SIZE = 1

    @classmethod
    def supports_model(cls, model_id: str) -> bool:
        return model_id == cls._MODEL_ID

    @classmethod
    def _check_litellm_available(cls) -> bool:
        """Check if LiteLLM proxy is configured and supports image embeddings."""
        if cls._litellm_available is not None:
            return cls._litellm_available

        try:
            litellm_key = os.environ.get("LITELLM_API_KEY")
            litellm_url = os.environ.get("LITELLM_BASE_URL")

            if not litellm_key or not litellm_url:
                logger.info("[ImageEmbedding] LiteLLM not configured, using local model")
                cls._litellm_available = False
                return False

            # Test with a tiny 1x1 pixel image using OpenAI-compatible API
            import requests
            test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

            response = requests.post(
                f"{litellm_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {litellm_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": cls._MODEL_ID,
                    "input": test_image
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    dims = len(data["data"][0].get("embedding", []))
                    if dims > 0:
                        logger.info(f"[ImageEmbedding] LiteLLM proxy available ({dims} dimensions)")
                        cls._litellm_available = True
                        return True

        except Exception as e:
            logger.warning(f"[ImageEmbedding] LiteLLM proxy test failed: {e}")

        cls._litellm_available = False
        return False

    @classmethod
    def _image_to_base64_url(cls, image_path: str) -> Optional[str]:
        """Convert image file to base64 data URL.

        Resizes to MAX_IMAGE_SIZE and uses dynamic JPEG quality to stay
        within the LiteLLM proxy's context limit (~42KB base64).
        """
        if not image_path or not os.path.exists(image_path):
            return None

        try:
            from io import BytesIO

            resample = getattr(Image, "Resampling", Image).LANCZOS
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                # Resize to fit max dimensions while preserving aspect ratio
                if img.size[0] > cls.MAX_IMAGE_SIZE[0] or img.size[1] > cls.MAX_IMAGE_SIZE[1]:
                    img.thumbnail(cls.MAX_IMAGE_SIZE, resample)

                # Dynamic quality: reduce quality until we fit under the limit
                quality = cls.JPEG_QUALITY_START
                while quality >= cls.JPEG_QUALITY_MIN:
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=quality, optimize=True)
                    b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

                    if len(b64_data) <= cls.MAX_BASE64_BYTES:
                        return f"data:image/jpeg;base64,{b64_data}"

                    # Reduce quality and try again
                    quality -= 10

                # Last resort: reduce image size further
                smaller_size = (cls.MAX_IMAGE_SIZE[0] // 2, cls.MAX_IMAGE_SIZE[1] // 2)
                img.thumbnail(smaller_size, resample)
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=cls.JPEG_QUALITY_MIN, optimize=True)
                b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

                if len(b64_data) > cls.MAX_BASE64_BYTES:
                    logger.warning(f"[ImageEmbedding] Image still too large after compression: {image_path}")
                    return None

                return f"data:image/jpeg;base64,{b64_data}"

        except Exception as e:
            logger.warning(f"[ImageEmbedding] Failed to convert image to base64: {image_path}: {e}")
            return None

    @classmethod
    def _embed_via_litellm(
        cls,
        image_paths: List[str]
    ) -> List[Optional[List[float]]]:
        """Embed images using LiteLLM proxy (fast, cluster-based).

        Uses the OpenAI-compatible /embeddings endpoint with base64 data URLs.
        """
        import requests

        litellm_key = os.environ.get("LITELLM_API_KEY")
        litellm_url = os.environ.get("LITELLM_BASE_URL")

        results: List[Optional[List[float]]] = [None] * len(image_paths)
        logger.info(f"[ImageEmbedding] Embedding {len(image_paths)} images via LiteLLM cluster")

        for idx, path in enumerate(image_paths):
            try:
                data_url = cls._image_to_base64_url(path)
                if not data_url:
                    logger.debug(f"[ImageEmbedding] Skipping invalid image: {path}")
                    continue

                response = requests.post(
                    f"{litellm_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {litellm_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": cls._MODEL_ID,
                        "input": data_url
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("data") and len(data["data"]) > 0:
                        embedding = data["data"][0].get("embedding", [])
                        if isinstance(embedding, list) and len(embedding) > 0:
                            results[idx] = embedding
                        else:
                            logger.warning(f"[ImageEmbedding] Empty embedding for {path}")
                    else:
                        logger.warning(f"[ImageEmbedding] No data in response for {path}: {str(data)[:200]}")
                else:
                    logger.warning(f"[ImageEmbedding] HTTP {response.status_code} for {path}: {response.text[:200]}")

                if (idx + 1) % 10 == 0:
                    embedded_so_far = sum(1 for r in results[:idx+1] if r is not None)
                    logger.info(f"[ImageEmbedding] LiteLLM: Processed {idx + 1}/{len(image_paths)} images ({embedded_so_far} successful)")

            except Exception as e:
                logger.warning(f"[ImageEmbedding] LiteLLM embedding failed for {path}: {e}")

        embedded_count = sum(1 for r in results if r is not None)
        logger.info(f"[ImageEmbedding] LiteLLM completed: {embedded_count}/{len(image_paths)} images")
        return results

    @classmethod
    def _get_local_model(cls, model_id: str):
        """Load local SentenceTransformer model (fallback)."""
        if not cls.supports_model(model_id):
            return None

        with cls._lock:
            cached = cls._model_cache.get(model_id)
            if cached is not None:
                return cached

            try:
                from sentence_transformers import SentenceTransformer
            except Exception as exc:
                logger.warning(f"[ImageEmbedding] sentence-transformers not available: {exc}")
                return None

            try:
                model = SentenceTransformer(model_id, device="cpu", trust_remote_code=True)
                cls._model_cache[model_id] = model
                logger.info(f"[ImageEmbedding] Loaded local multimodal model: {model_id}")
                return model
            except Exception as exc:
                logger.warning(f"[ImageEmbedding] Failed to load model {model_id}: {exc}")
                return None

    @classmethod
    def _embed_via_local(
        cls,
        model_id: str,
        image_paths: List[str]
    ) -> List[Optional[List[float]]]:
        """Embed images using local SentenceTransformer (slower, fallback)."""
        model = cls._get_local_model(model_id)
        if not model:
            return [None] * len(image_paths)

        results: List[Optional[List[float]]] = [None] * len(image_paths)
        resample = getattr(Image, "Resampling", Image).LANCZOS

        logger.info(f"[ImageEmbedding] Embedding {len(image_paths)} images via local model (slow)")

        for idx, path in enumerate(image_paths):
            if not path or not os.path.exists(path):
                continue

            img = None
            try:
                with Image.open(path) as raw_img:
                    img = raw_img.convert("RGB")
                    if img.size[0] > cls.MAX_IMAGE_SIZE[0] or img.size[1] > cls.MAX_IMAGE_SIZE[1]:
                        img.thumbnail(cls.MAX_IMAGE_SIZE, resample)
                    img = img.copy()

                embedding = model.encode([img], batch_size=1, normalize_embeddings=True)

                if hasattr(embedding, "tolist"):
                    embedding = embedding.tolist()

                if embedding and len(embedding) > 0:
                    vec = embedding[0]
                    # Local model returns 1536 dims, truncate to 1024
                    if len(vec) > cls.TARGET_DIMENSIONS:
                        vec = vec[:cls.TARGET_DIMENSIONS]
                        norm = math.sqrt(sum(x * x for x in vec))
                        if norm > 0:
                            vec = [x / norm for x in vec]
                    results[idx] = vec

                if (idx + 1) % 10 == 0:
                    logger.info(f"[ImageEmbedding] Local: Processed {idx + 1}/{len(image_paths)} images")

            except Exception as exc:
                logger.warning(f"[ImageEmbedding] Local embedding failed for {path}: {exc}")

            finally:
                if img is not None:
                    try:
                        img.close()
                    except Exception:
                        pass
                    del img

                if (idx + 1) % 5 == 0:
                    gc.collect()

        gc.collect()
        embedded_count = sum(1 for r in results if r is not None)
        logger.info(f"[ImageEmbedding] Local completed: {embedded_count}/{len(image_paths)} images")
        return results

    @classmethod
    def embed_image_paths(
        cls,
        model_id: str,
        image_paths: List[str],
        batch_size: Optional[int] = None,
        force_local: bool = False
    ) -> List[Optional[List[float]]]:
        """Embed images from file paths.

        Automatically uses LiteLLM proxy if available (fast cluster processing).
        Falls back to local SentenceTransformer if proxy unavailable.

        Args:
            model_id: The model ID to use (must be VDR-2B-Multi-V1)
            image_paths: List of file paths to images
            batch_size: Override batch size (only for local model)
            force_local: Force using local model instead of LiteLLM

        Returns:
            List of embeddings (or None for failed/missing images)
        """
        if not cls.supports_model(model_id):
            logger.warning(f"[ImageEmbedding] Unsupported model: {model_id}")
            return [None] * len(image_paths)

        if not image_paths:
            return []

        # Try LiteLLM first (much faster)
        if not force_local and cls._check_litellm_available():
            return cls._embed_via_litellm(image_paths)

        # Fallback to local processing
        return cls._embed_via_local(model_id, image_paths)
