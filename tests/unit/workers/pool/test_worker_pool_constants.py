"""
Tests for worker_pool_constants - configuration and global registry.

Covers:
- Constant values verification
- Thread-safe pool registry operations (get, register, unregister)
- get_all_pool_ids
"""

import threading
from unittest.mock import MagicMock

import pytest


class TestConstants:
    """Test constant definitions."""

    def test_WPC_001_max_workers_is_5(self):
        """WPC_001: MAX_WORKERS is set to 5."""
        from workers.pool.worker_pool_constants import MAX_WORKERS
        assert MAX_WORKERS == 5

    def test_WPC_002_max_attempts_is_3(self):
        """WPC_002: MAX_ATTEMPTS is set to 3."""
        from workers.pool.worker_pool_constants import MAX_ATTEMPTS
        assert MAX_ATTEMPTS == 3

    def test_WPC_003_backoff_base_is_2(self):
        """WPC_003: BACKOFF_BASE is set to 2."""
        from workers.pool.worker_pool_constants import BACKOFF_BASE
        assert BACKOFF_BASE == 2

    def test_WPC_004_heartbeat_interval_is_30(self):
        """WPC_004: HEARTBEAT_INTERVAL is set to 30 seconds."""
        from workers.pool.worker_pool_constants import HEARTBEAT_INTERVAL
        assert HEARTBEAT_INTERVAL == 30

    def test_WPC_005_stale_timeout_is_120(self):
        """WPC_005: STALE_TIMEOUT is set to 120 seconds."""
        from workers.pool.worker_pool_constants import STALE_TIMEOUT
        assert STALE_TIMEOUT == 120

    def test_WPC_006_pool_lock_is_threading_lock(self):
        """WPC_006: _pool_lock is a threading.Lock."""
        from workers.pool.worker_pool_constants import _pool_lock
        assert isinstance(_pool_lock, type(threading.Lock()))

    def test_WPC_007_pools_is_dict(self):
        """WPC_007: _pools is a dict."""
        from workers.pool.worker_pool_constants import _pools
        assert isinstance(_pools, dict)


class TestGetPool:
    """Test get_pool function."""

    def test_WPC_010_get_pool_returns_existing(self):
        """WPC_010: get_pool returns pool for existing session_id."""
        from workers.pool.worker_pool_constants import get_pool, _pools

        mock_pool = MagicMock()
        _pools[42] = mock_pool

        result = get_pool(42)
        assert result is mock_pool

        _pools.clear()

    def test_WPC_011_get_pool_returns_none_for_missing(self):
        """WPC_011: get_pool returns None for non-existent session_id."""
        from workers.pool.worker_pool_constants import get_pool, _pools

        _pools.clear()
        assert get_pool(999) is None


class TestRegisterPool:
    """Test register_pool function."""

    def test_WPC_020_register_pool_adds_to_registry(self):
        """WPC_020: register_pool adds pool to _pools dict."""
        from workers.pool.worker_pool_constants import register_pool, _pools

        _pools.clear()
        mock_pool = MagicMock()

        register_pool(42, mock_pool)

        assert _pools[42] is mock_pool
        _pools.clear()

    def test_WPC_021_register_pool_stops_existing(self):
        """WPC_021: register_pool stops existing pool before replacing."""
        from workers.pool.worker_pool_constants import register_pool, _pools

        old_pool = MagicMock()
        _pools[42] = old_pool

        new_pool = MagicMock()
        register_pool(42, new_pool)

        old_pool.stop.assert_called_once()
        assert _pools[42] is new_pool

        _pools.clear()


class TestUnregisterPool:
    """Test unregister_pool function."""

    def test_WPC_030_unregister_existing_returns_true(self):
        """WPC_030: unregister_pool removes pool and returns True."""
        from workers.pool.worker_pool_constants import unregister_pool, _pools

        _pools[42] = MagicMock()

        result = unregister_pool(42)

        assert result is True
        assert 42 not in _pools

    def test_WPC_031_unregister_missing_returns_false(self):
        """WPC_031: unregister_pool returns False for non-existent session."""
        from workers.pool.worker_pool_constants import unregister_pool, _pools

        _pools.clear()
        result = unregister_pool(999)
        assert result is False


class TestGetAllPoolIds:
    """Test get_all_pool_ids function."""

    def test_WPC_040_returns_all_session_ids(self):
        """WPC_040: Returns list of all active pool session IDs."""
        from workers.pool.worker_pool_constants import get_all_pool_ids, _pools

        _pools.clear()
        _pools[1] = MagicMock()
        _pools[5] = MagicMock()
        _pools[10] = MagicMock()

        ids = get_all_pool_ids()

        assert sorted(ids) == [1, 5, 10]
        _pools.clear()

    def test_WPC_041_returns_empty_when_no_pools(self):
        """WPC_041: Returns empty list when no pools active."""
        from workers.pool.worker_pool_constants import get_all_pool_ids, _pools

        _pools.clear()
        assert get_all_pool_ids() == []
