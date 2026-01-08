"""
System Settings Service.

Provides cached access to system-wide settings stored in the database.
Settings are cached in memory and refreshed periodically or on update.
"""

import logging
import threading
import time
from typing import Optional

from db.database import db
from db.models.system_settings import SystemSettings

logger = logging.getLogger(__name__)

# Cache settings
_settings_cache: Optional[dict] = None
_cache_lock = threading.Lock()
_cache_timestamp: float = 0
CACHE_TTL_SECONDS = 60  # Refresh cache every 60 seconds


def _get_or_create_settings() -> SystemSettings:
    """Get or create the singleton settings row."""
    settings = SystemSettings.query.get(1)
    if settings is None:
        settings = SystemSettings(id=1)
        db.session.add(settings)
        db.session.commit()
        logger.info("[SystemSettings] Created default system settings")
    return settings


def _load_settings_to_cache() -> dict:
    """Load settings from database into cache."""
    global _settings_cache, _cache_timestamp

    settings = _get_or_create_settings()
    cached = {
        'crawl_timeout_seconds': settings.crawl_timeout_seconds,
        'embedding_timeout_seconds': settings.embedding_timeout_seconds,
        'crawler_default_max_pages': settings.crawler_default_max_pages,
        'crawler_default_max_depth': settings.crawler_default_max_depth,
        'rag_default_chunk_size': settings.rag_default_chunk_size,
        'rag_default_chunk_overlap': settings.rag_default_chunk_overlap,
        'llm_ai_log_responses': settings.llm_ai_log_responses,
        'llm_ai_log_tasks': settings.llm_ai_log_tasks,
        'llm_ai_log_response_max': settings.llm_ai_log_response_max,
        'llm_ai_log_prompts': settings.llm_ai_log_prompts,
        'llm_ai_log_prompt_max': settings.llm_ai_log_prompt_max,
    }

    with _cache_lock:
        _settings_cache = cached
        _cache_timestamp = time.time()

    return cached


def get_system_settings() -> dict:
    """
    Get system settings with caching.

    Returns cached settings if available and not stale,
    otherwise loads from database.
    """
    global _settings_cache, _cache_timestamp

    with _cache_lock:
        if _settings_cache is not None:
            age = time.time() - _cache_timestamp
            if age < CACHE_TTL_SECONDS:
                return _settings_cache.copy()

    # Cache miss or stale - reload from DB
    return _load_settings_to_cache()


def get_setting(key: str, default=None):
    """
    Get a single setting value.

    Args:
        key: Setting key name
        default: Default value if key not found
    """
    settings = get_system_settings()
    return settings.get(key, default)


def invalidate_cache():
    """Force cache invalidation (call after updates)."""
    global _settings_cache, _cache_timestamp

    with _cache_lock:
        _settings_cache = None
        _cache_timestamp = 0


# Convenience functions for commonly used settings
def get_crawl_timeout() -> int:
    """Get crawl timeout in seconds (default: 3600 = 1 hour)."""
    return get_setting('crawl_timeout_seconds', 3600)


def get_embedding_timeout() -> int:
    """Get embedding timeout in seconds (default: 7200 = 2 hours)."""
    return get_setting('embedding_timeout_seconds', 7200)


def get_default_max_pages() -> int:
    """Get default max pages for crawler (default: 500)."""
    return get_setting('crawler_default_max_pages', 500)


def get_default_max_depth() -> int:
    """Get default max depth for crawler (default: 3)."""
    return get_setting('crawler_default_max_depth', 3)


def get_default_chunk_size() -> int:
    """Get default chunk size for RAG (default: 1000)."""
    return get_setting('rag_default_chunk_size', 1000)


def get_default_chunk_overlap() -> int:
    """Get default chunk overlap for RAG (default: 200)."""
    return get_setting('rag_default_chunk_overlap', 200)
