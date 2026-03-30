"""
Unit tests for system_settings_service.

Tests cached system settings access including:
- Getting settings with cache
- Cache TTL expiration
- Convenience functions (crawl_timeout, embedding_timeout, etc.)
- Cache invalidation
"""

import time
import pytest
from unittest.mock import patch, MagicMock

import services.system_settings_service as sss
from services.system_settings_service import (
    get_system_settings,
    get_setting,
    invalidate_cache,
    get_crawl_timeout,
    get_embedding_timeout,
    get_default_max_pages,
    get_default_max_depth,
    get_default_chunk_size,
    get_default_chunk_overlap,
    get_batch_generation_max_parallel,
    is_communication_enabled,
    CACHE_TTL_SECONDS,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset module-level cache between tests."""
    invalidate_cache()
    yield
    invalidate_cache()


class TestGetSystemSettings:
    """Tests for get_system_settings with caching."""

    def test_SYS_SET_001_returns_settings_dict(self, app, db, app_context):
        """[SYS_SET-001] Should return a dictionary of system settings."""
        settings = get_system_settings()

        assert isinstance(settings, dict)
        assert 'crawl_timeout_seconds' in settings
        assert 'embedding_timeout_seconds' in settings
        assert 'crawler_default_max_pages' in settings
        assert 'rag_default_chunk_size' in settings

    def test_SYS_SET_002_creates_default_settings_when_none_exist(self, app, db, app_context):
        """[SYS_SET-002] Should auto-create default settings row if missing."""
        from db.models.system_settings import SystemSettings

        # Verify no settings exist yet
        assert SystemSettings.query.get(1) is None

        settings = get_system_settings()

        # Should have created the row
        row = SystemSettings.query.get(1)
        assert row is not None
        # Default values
        assert settings['crawl_timeout_seconds'] == 3600
        assert settings['embedding_timeout_seconds'] == 7200

    def test_SYS_SET_003_returns_cached_data_on_second_call(self, app, db, app_context):
        """[SYS_SET-003] Should return cached data on subsequent calls within TTL."""
        settings1 = get_system_settings()
        settings2 = get_system_settings()

        # Both calls should return equivalent dicts
        assert settings1 == settings2

        # The second call returns a copy (via _settings_cache.copy()),
        # so mutating settings2 should not affect a fresh fetch
        settings2['crawl_timeout_seconds'] = 999999
        settings3 = get_system_settings()
        assert settings3['crawl_timeout_seconds'] != 999999

    def test_SYS_SET_004_returns_updated_settings_from_db(self, app, db, app_context):
        """[SYS_SET-004] Should pick up DB changes after cache is invalidated."""
        from db.models.system_settings import SystemSettings

        # Initial load
        get_system_settings()

        # Modify DB directly
        row = SystemSettings.query.get(1)
        row.crawl_timeout_seconds = 9999
        db.session.commit()

        # Cache still has old value
        cached = get_system_settings()
        assert cached['crawl_timeout_seconds'] == 3600  # cached

        # Invalidate and re-fetch
        invalidate_cache()
        refreshed = get_system_settings()
        assert refreshed['crawl_timeout_seconds'] == 9999


class TestCacheTTL:
    """Tests for cache TTL expiration."""

    def test_SYS_SET_005_cache_expires_after_ttl(self, app, db, app_context):
        """[SYS_SET-005] Should reload from DB after cache TTL expires."""
        from db.models.system_settings import SystemSettings

        # Initial load
        get_system_settings()

        # Modify DB directly
        row = SystemSettings.query.get(1)
        row.crawler_default_max_pages = 42
        db.session.commit()

        # Simulate cache expiry by backdating the timestamp
        sss._cache_timestamp = time.time() - CACHE_TTL_SECONDS - 1

        settings = get_system_settings()
        assert settings['crawler_default_max_pages'] == 42

    def test_SYS_SET_006_cache_valid_within_ttl(self, app, db, app_context):
        """[SYS_SET-006] Should serve cached data within TTL window."""
        from db.models.system_settings import SystemSettings

        settings = get_system_settings()
        original_pages = settings['crawler_default_max_pages']

        # Modify DB -- but cache is still fresh
        row = SystemSettings.query.get(1)
        row.crawler_default_max_pages = 12345
        db.session.commit()

        cached = get_system_settings()
        assert cached['crawler_default_max_pages'] == original_pages


class TestCacheInvalidation:
    """Tests for explicit cache invalidation."""

    def test_SYS_SET_007_invalidate_clears_cache(self, app, db, app_context):
        """[SYS_SET-007] Should clear cache so next call reloads from DB."""
        from db.models.system_settings import SystemSettings

        get_system_settings()

        row = SystemSettings.query.get(1)
        row.rag_default_chunk_overlap = 777
        db.session.commit()

        invalidate_cache()
        settings = get_system_settings()
        assert settings['rag_default_chunk_overlap'] == 777

    def test_SYS_SET_008_invalidate_is_idempotent(self, app, db, app_context):
        """[SYS_SET-008] Multiple invalidations should not cause errors."""
        invalidate_cache()
        invalidate_cache()
        invalidate_cache()

        settings = get_system_settings()
        assert isinstance(settings, dict)


class TestGetSetting:
    """Tests for the get_setting helper."""

    def test_SYS_SET_009_returns_known_setting(self, app, db, app_context):
        """[SYS_SET-009] Should return value for a known setting key."""
        value = get_setting('crawl_timeout_seconds')
        assert value == 3600

    def test_SYS_SET_010_returns_default_for_unknown_key(self, app, db, app_context):
        """[SYS_SET-010] Should return default value for an unknown key."""
        value = get_setting('nonexistent_key', default='fallback')
        assert value == 'fallback'

    def test_SYS_SET_011_returns_none_for_unknown_key_no_default(self, app, db, app_context):
        """[SYS_SET-011] Should return None for unknown key when no default specified."""
        value = get_setting('nonexistent_key')
        assert value is None


class TestConvenienceFunctions:
    """Tests for convenience getter functions."""

    def test_SYS_SET_012_get_crawl_timeout(self, app, db, app_context):
        """[SYS_SET-012] get_crawl_timeout should return crawl_timeout_seconds."""
        assert get_crawl_timeout() == 3600

    def test_SYS_SET_013_get_embedding_timeout(self, app, db, app_context):
        """[SYS_SET-013] get_embedding_timeout should return embedding_timeout_seconds."""
        assert get_embedding_timeout() == 7200

    def test_SYS_SET_014_get_default_max_pages(self, app, db, app_context):
        """[SYS_SET-014] get_default_max_pages should return crawler_default_max_pages."""
        assert get_default_max_pages() == 500

    def test_SYS_SET_015_get_default_max_depth(self, app, db, app_context):
        """[SYS_SET-015] get_default_max_depth should return crawler_default_max_depth."""
        assert get_default_max_depth() == 3

    def test_SYS_SET_016_get_default_chunk_size(self, app, db, app_context):
        """[SYS_SET-016] get_default_chunk_size should return rag_default_chunk_size."""
        assert get_default_chunk_size() == 1000

    def test_SYS_SET_017_get_default_chunk_overlap(self, app, db, app_context):
        """[SYS_SET-017] get_default_chunk_overlap should return rag_default_chunk_overlap."""
        assert get_default_chunk_overlap() == 200

    def test_SYS_SET_018_get_batch_generation_max_parallel(self, app, db, app_context):
        """[SYS_SET-018] get_batch_generation_max_parallel should return default value."""
        assert get_batch_generation_max_parallel() == 4

    def test_SYS_SET_019_is_communication_enabled(self, app, db, app_context):
        """[SYS_SET-019] is_communication_enabled should return False by default."""
        assert is_communication_enabled() is False

    def test_SYS_SET_020_convenience_reflects_db_changes(self, app, db, app_context):
        """[SYS_SET-020] Convenience functions should reflect DB changes after cache invalidation."""
        from db.models.system_settings import SystemSettings

        # Load initial settings
        get_system_settings()

        row = SystemSettings.query.get(1)
        row.crawl_timeout_seconds = 1234
        row.communication_enabled = True
        db.session.commit()

        invalidate_cache()

        assert get_crawl_timeout() == 1234
        assert is_communication_enabled() is True


class TestSettingsCacheKeys:
    """Tests to ensure all expected keys are present in cached settings."""

    def test_SYS_SET_021_all_expected_keys_present(self, app, db, app_context):
        """[SYS_SET-021] Cached settings dict should contain all expected keys."""
        settings = get_system_settings()

        expected_keys = [
            'crawl_timeout_seconds',
            'embedding_timeout_seconds',
            'crawler_default_max_pages',
            'crawler_default_max_depth',
            'rag_default_chunk_size',
            'rag_default_chunk_overlap',
            'llm_ai_log_responses',
            'llm_ai_log_tasks',
            'llm_ai_log_response_max',
            'llm_ai_log_prompts',
            'llm_ai_log_prompt_max',
            'batch_generation_max_parallel',
            'referral_system_enabled',
            'self_registration_enabled',
            'default_referral_role',
            'communication_enabled',
        ]

        for key in expected_keys:
            assert key in settings, f"Missing expected key: {key}"
