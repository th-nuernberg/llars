"""
Redis-based caching for NER results in the anonymize service.

Caches the expensive NER detection results to speed up repeated requests.
The cache key is based on text hash + engine, since NER results only depend on these.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL_SECONDS = int(os.environ.get("ANONYMIZE_CACHE_TTL", "3600"))  # 1 hour default
CACHE_PREFIX = "anonymize:ner:"
CACHE_ENABLED = os.environ.get("ANONYMIZE_CACHE_ENABLED", "true").lower() == "true"


def _get_redis_client():
    """Get Redis client from main app (lazy import to avoid circular imports)."""
    try:
        from app.main import redis_client
        return redis_client
    except ImportError:
        logger.warning("Could not import redis_client from app.main")
        return None


def _compute_cache_key(text: str, engine: str) -> str:
    """
    Compute cache key from text and engine.

    We hash the text to keep keys short and avoid special characters.
    """
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
    return f"{CACHE_PREFIX}{engine}:{text_hash}"


def get_cached_ner_result(text: str, engine: str) -> Optional[dict[str, Any]]:
    """
    Get cached NER result if available.

    Args:
        text: Input text
        engine: Detection engine ("offline", "llm", "hybrid")

    Returns:
        Cached result dict or None if not found
    """
    if not CACHE_ENABLED:
        return None

    redis_client = _get_redis_client()
    if not redis_client:
        return None

    try:
        key = _compute_cache_key(text, engine)
        cached = redis_client.get(key)
        if cached:
            result = json.loads(cached)
            logger.debug(f"Cache hit for anonymize NER (key={key[:50]}...)")
            return result
    except Exception as e:
        logger.warning(f"Error reading anonymize cache: {e}")

    return None


def set_cached_ner_result(
    text: str,
    engine: str,
    entities: list[dict[str, Any]],
    raw_candidates: Optional[list[dict[str, Any]]] = None,
) -> bool:
    """
    Cache NER detection result.

    We cache:
    - entities: The detected entities with positions and labels
    - raw_candidates: The raw entity candidates before grouping (optional)

    Args:
        text: Input text
        engine: Detection engine
        entities: List of detected entities
        raw_candidates: Optional raw candidates for full reconstruction

    Returns:
        True if cached successfully, False otherwise
    """
    if not CACHE_ENABLED:
        return False

    redis_client = _get_redis_client()
    if not redis_client:
        return False

    try:
        key = _compute_cache_key(text, engine)
        data = {
            "entities": entities,
            "raw_candidates": raw_candidates,
            "text_length": len(text),
        }
        redis_client.setex(key, CACHE_TTL_SECONDS, json.dumps(data))
        logger.debug(f"Cached anonymize NER result (key={key[:50]}..., ttl={CACHE_TTL_SECONDS}s)")
        return True
    except Exception as e:
        logger.warning(f"Error writing anonymize cache: {e}")
        return False


def invalidate_cache(text: str, engine: str) -> bool:
    """
    Invalidate cached result for specific text+engine.

    Args:
        text: Input text
        engine: Detection engine

    Returns:
        True if invalidated, False otherwise
    """
    if not CACHE_ENABLED:
        return False

    redis_client = _get_redis_client()
    if not redis_client:
        return False

    try:
        key = _compute_cache_key(text, engine)
        redis_client.delete(key)
        logger.debug(f"Invalidated anonymize cache (key={key[:50]}...)")
        return True
    except Exception as e:
        logger.warning(f"Error invalidating anonymize cache: {e}")
        return False


def clear_all_cache() -> int:
    """
    Clear all anonymize NER cache entries.

    Returns:
        Number of entries cleared
    """
    redis_client = _get_redis_client()
    if not redis_client:
        return 0

    try:
        pattern = f"{CACHE_PREFIX}*"
        keys = list(redis_client.scan_iter(match=pattern))
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} anonymize cache entries")
            return len(keys)
    except Exception as e:
        logger.warning(f"Error clearing anonymize cache: {e}")

    return 0


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dict with cache stats (count, memory estimate, etc.)
    """
    redis_client = _get_redis_client()
    if not redis_client:
        return {"enabled": False, "error": "Redis not available"}

    try:
        pattern = f"{CACHE_PREFIX}*"
        keys = list(redis_client.scan_iter(match=pattern))
        return {
            "enabled": CACHE_ENABLED,
            "count": len(keys),
            "ttl_seconds": CACHE_TTL_SECONDS,
            "prefix": CACHE_PREFIX,
        }
    except Exception as e:
        return {"enabled": CACHE_ENABLED, "error": str(e)}
