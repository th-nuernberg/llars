"""
Unit tests for DebugLogService.

Tests enable/disable user debug, checking debug status,
getting all debug users, TTL limits, and Redis error handling.
All Redis interactions are mocked entirely with MagicMock.
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_redis():
    """Provide a fresh MagicMock Redis client for each test."""
    return MagicMock()


@pytest.fixture
def _patch_redis(mock_redis):
    """Patch _get_redis() so that every service call uses mock_redis."""
    with patch('services.debug_log_service._get_redis', return_value=mock_redis):
        yield


# ---------------------------------------------------------------------------
# Tests: is_user_debug_enabled
# ---------------------------------------------------------------------------

class TestIsUserDebugEnabled:
    """Tests for is_user_debug_enabled()."""

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_001_returns_true_when_key_exists(self, mock_redis):
        """[DEBUG-001] Returns True when the Redis key is present."""
        from services.debug_log_service import is_user_debug_enabled

        mock_redis.exists.return_value = 1
        assert is_user_debug_enabled('evaluator') is True
        mock_redis.exists.assert_called_once_with('debug:user:evaluator')

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_002_returns_false_when_key_missing(self, mock_redis):
        """[DEBUG-002] Returns False when the Redis key does not exist."""
        from services.debug_log_service import is_user_debug_enabled

        mock_redis.exists.return_value = 0
        assert is_user_debug_enabled('evaluator') is False

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_003_returns_false_for_empty_username(self, mock_redis):
        """[DEBUG-003] Returns False when username is empty or None."""
        from services.debug_log_service import is_user_debug_enabled

        assert is_user_debug_enabled('') is False
        assert is_user_debug_enabled(None) is False
        mock_redis.exists.assert_not_called()

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_004_returns_false_on_redis_error(self, mock_redis):
        """[DEBUG-004] Returns False when Redis raises an exception."""
        from services.debug_log_service import is_user_debug_enabled

        mock_redis.exists.side_effect = ConnectionError('Redis down')
        assert is_user_debug_enabled('evaluator') is False


# ---------------------------------------------------------------------------
# Tests: enable_user_debug
# ---------------------------------------------------------------------------

class TestEnableUserDebug:
    """Tests for enable_user_debug()."""

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_010_enable_with_default_ttl(self, mock_redis):
        """[DEBUG-010] Enabling debug without TTL uses the 30-minute default."""
        from services.debug_log_service import enable_user_debug, DEFAULT_DEBUG_TTL_SECONDS

        result = enable_user_debug('evaluator')

        mock_redis.setex.assert_called_once_with(
            'debug:user:evaluator', DEFAULT_DEBUG_TTL_SECONDS, '1'
        )
        assert result['username'] == 'evaluator'
        assert result['debug_enabled'] is True
        assert result['ttl_seconds'] == DEFAULT_DEBUG_TTL_SECONDS

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_011_enable_with_custom_ttl(self, mock_redis):
        """[DEBUG-011] Enabling debug with a custom TTL uses that value."""
        from services.debug_log_service import enable_user_debug

        result = enable_user_debug('evaluator', ttl_seconds=600)

        mock_redis.setex.assert_called_once_with('debug:user:evaluator', 600, '1')
        assert result['ttl_seconds'] == 600
        assert result['ttl_minutes'] == 10.0

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_012_ttl_clamped_to_max_24h(self, mock_redis):
        """[DEBUG-012] TTL above 24 hours is clamped to the maximum."""
        from services.debug_log_service import enable_user_debug, MAX_DEBUG_TTL_SECONDS

        result = enable_user_debug('evaluator', ttl_seconds=100_000)

        assert result['ttl_seconds'] == MAX_DEBUG_TTL_SECONDS
        mock_redis.setex.assert_called_once_with(
            'debug:user:evaluator', MAX_DEBUG_TTL_SECONDS, '1'
        )

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_013_ttl_clamped_to_min_60s(self, mock_redis):
        """[DEBUG-013] TTL below 60 seconds is clamped to the minimum."""
        from services.debug_log_service import enable_user_debug

        result = enable_user_debug('evaluator', ttl_seconds=10)

        assert result['ttl_seconds'] == 60

    def test_DEBUG_014_raises_for_empty_username(self):
        """[DEBUG-014] Raises ValueError when username is empty."""
        from services.debug_log_service import enable_user_debug

        with pytest.raises(ValueError, match='Username is required'):
            enable_user_debug('')

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_015_raises_on_redis_error(self, mock_redis):
        """[DEBUG-015] Raises when Redis is unreachable during enable."""
        from services.debug_log_service import enable_user_debug

        mock_redis.setex.side_effect = ConnectionError('Redis down')
        with pytest.raises(ConnectionError):
            enable_user_debug('evaluator')


# ---------------------------------------------------------------------------
# Tests: disable_user_debug
# ---------------------------------------------------------------------------

class TestDisableUserDebug:
    """Tests for disable_user_debug()."""

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_020_disable_deletes_key(self, mock_redis):
        """[DEBUG-020] Disabling debug deletes the Redis key."""
        from services.debug_log_service import disable_user_debug

        result = disable_user_debug('evaluator')

        mock_redis.delete.assert_called_once_with('debug:user:evaluator')
        assert result['username'] == 'evaluator'
        assert result['debug_enabled'] is False

    def test_DEBUG_021_raises_for_empty_username(self):
        """[DEBUG-021] Raises ValueError when username is empty."""
        from services.debug_log_service import disable_user_debug

        with pytest.raises(ValueError, match='Username is required'):
            disable_user_debug('')

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_022_raises_on_redis_error(self, mock_redis):
        """[DEBUG-022] Raises when Redis is unreachable during disable."""
        from services.debug_log_service import disable_user_debug

        mock_redis.delete.side_effect = ConnectionError('Redis down')
        with pytest.raises(ConnectionError):
            disable_user_debug('evaluator')


# ---------------------------------------------------------------------------
# Tests: get_user_debug_status
# ---------------------------------------------------------------------------

class TestGetUserDebugStatus:
    """Tests for get_user_debug_status()."""

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_030_status_enabled_with_remaining_ttl(self, mock_redis):
        """[DEBUG-030] Returns enabled=True and remaining TTL when key exists."""
        from services.debug_log_service import get_user_debug_status

        mock_redis.ttl.return_value = 900  # 15 minutes remaining
        result = get_user_debug_status('evaluator')

        assert result['debug_enabled'] is True
        assert result['ttl_remaining'] == 900
        assert result['ttl_remaining_minutes'] == 15.0

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_031_status_disabled_when_key_missing(self, mock_redis):
        """[DEBUG-031] Returns enabled=False when the key does not exist."""
        from services.debug_log_service import get_user_debug_status

        mock_redis.ttl.return_value = -2  # key does not exist
        result = get_user_debug_status('evaluator')

        assert result['debug_enabled'] is False
        assert result['ttl_remaining'] == 0

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_032_status_disabled_when_no_expiry(self, mock_redis):
        """[DEBUG-032] Returns enabled=False when TTL is -1 (no expiry)."""
        from services.debug_log_service import get_user_debug_status

        mock_redis.ttl.return_value = -1
        result = get_user_debug_status('evaluator')

        assert result['debug_enabled'] is False
        assert result['ttl_remaining'] == 0

    def test_DEBUG_033_status_for_empty_username(self):
        """[DEBUG-033] Returns disabled status for empty username."""
        from services.debug_log_service import get_user_debug_status

        result = get_user_debug_status('')
        assert result['debug_enabled'] is False

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_034_status_returns_safe_defaults_on_error(self, mock_redis):
        """[DEBUG-034] Returns safe defaults when Redis errors out."""
        from services.debug_log_service import get_user_debug_status

        mock_redis.ttl.side_effect = ConnectionError('Redis down')
        result = get_user_debug_status('evaluator')

        assert result['debug_enabled'] is False
        assert result['ttl_remaining'] == 0


# ---------------------------------------------------------------------------
# Tests: get_all_debug_users
# ---------------------------------------------------------------------------

class TestGetAllDebugUsers:
    """Tests for get_all_debug_users()."""

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_040_returns_sorted_user_list(self, mock_redis):
        """[DEBUG-040] Returns all debug users sorted alphabetically."""
        from services.debug_log_service import get_all_debug_users

        mock_redis.keys.return_value = [
            'debug:user:zara',
            'debug:user:alice',
        ]
        mock_redis.ttl.side_effect = [300, 600]

        result = get_all_debug_users()

        assert len(result) == 2
        assert result[0]['username'] == 'alice'
        assert result[0]['ttl_remaining'] == 600
        assert result[1]['username'] == 'zara'
        assert result[1]['ttl_remaining'] == 300

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_041_excludes_expired_keys(self, mock_redis):
        """[DEBUG-041] Excludes keys whose TTL is zero or negative."""
        from services.debug_log_service import get_all_debug_users

        mock_redis.keys.return_value = [
            'debug:user:active',
            'debug:user:expired',
        ]
        mock_redis.ttl.side_effect = [600, -2]

        result = get_all_debug_users()

        assert len(result) == 1
        assert result[0]['username'] == 'active'

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_042_returns_empty_list_when_no_keys(self, mock_redis):
        """[DEBUG-042] Returns empty list when no debug keys exist."""
        from services.debug_log_service import get_all_debug_users

        mock_redis.keys.return_value = []
        result = get_all_debug_users()

        assert result == []

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_043_returns_empty_list_on_redis_error(self, mock_redis):
        """[DEBUG-043] Returns empty list when Redis is unreachable."""
        from services.debug_log_service import get_all_debug_users

        mock_redis.keys.side_effect = ConnectionError('Redis down')
        result = get_all_debug_users()

        assert result == []

    @pytest.mark.usefixtures('_patch_redis')
    def test_DEBUG_044_ttl_remaining_minutes_calculated(self, mock_redis):
        """[DEBUG-044] Each user entry includes correctly calculated ttl_remaining_minutes."""
        from services.debug_log_service import get_all_debug_users

        mock_redis.keys.return_value = ['debug:user:bob']
        mock_redis.ttl.return_value = 1800  # 30 minutes

        result = get_all_debug_users()

        assert len(result) == 1
        assert result[0]['ttl_remaining_minutes'] == 30.0
