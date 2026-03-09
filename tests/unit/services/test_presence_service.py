"""
Unit tests for PresenceService.

Tests record_seen, record_active, remove_socket, build_user_payload,
list_users, status computation, throttled DB writes, and helper methods.
All Redis interactions are mocked entirely with MagicMock.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call

from services.presence_service import PresenceService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_redis():
    """Provide a fresh MagicMock Redis client for each test."""
    redis = MagicMock()
    # Defaults: no prior scores/values in Redis
    redis.zscore.return_value = None
    redis.zcount.return_value = 0
    redis.get.return_value = None
    return redis


@pytest.fixture
def service(mock_redis):
    """Create a PresenceService with mocked Redis."""
    return PresenceService(mock_redis)


@pytest.fixture
def mock_user():
    """Create a lightweight mock User object."""
    user = MagicMock()
    user.id = 42
    user.username = 'testuser'
    user.last_seen_at = None
    user.last_active_at = None
    return user


# ---------------------------------------------------------------------------
# Tests: _coalesce_timestamp (static)
# ---------------------------------------------------------------------------

class TestCoalesceTimestamp:
    """Tests for PresenceService._coalesce_timestamp()."""

    def test_PRES_001_both_none_returns_none(self):
        """[PRES-001] Returns None when both Redis and DB timestamps are None."""
        assert PresenceService._coalesce_timestamp(None, None) is None

    def test_PRES_002_redis_only(self):
        """[PRES-002] Returns Redis timestamp when DB timestamp is None."""
        result = PresenceService._coalesce_timestamp(1000.0, None)
        assert result == 1000.0

    def test_PRES_003_db_only(self):
        """[PRES-003] Returns DB timestamp when Redis timestamp is None."""
        dt = datetime(2026, 1, 15, 12, 0, 0)
        result = PresenceService._coalesce_timestamp(None, dt)
        assert result == dt.timestamp()

    def test_PRES_004_picks_higher_value(self):
        """[PRES-004] Returns the higher of Redis and DB timestamps."""
        dt = datetime(2026, 1, 15, 12, 0, 0)
        redis_ts = dt.timestamp() + 100
        result = PresenceService._coalesce_timestamp(redis_ts, dt)
        assert result == redis_ts


# ---------------------------------------------------------------------------
# Tests: _format_iso (static)
# ---------------------------------------------------------------------------

class TestFormatIso:
    """Tests for PresenceService._format_iso()."""

    def test_PRES_005_none_returns_none(self):
        """[PRES-005] Returns None for a None/zero timestamp."""
        assert PresenceService._format_iso(None) is None
        assert PresenceService._format_iso(0) is None

    def test_PRES_006_valid_timestamp(self):
        """[PRES-006] Formats a valid timestamp as ISO string with Z suffix."""
        ts = datetime(2026, 1, 15, 10, 30, 0).timestamp()
        result = PresenceService._format_iso(ts)
        assert result.endswith('Z')
        assert '2026-01-15' in result


# ---------------------------------------------------------------------------
# Tests: _compute_status
# ---------------------------------------------------------------------------

class TestComputeStatus:
    """Tests for PresenceService._compute_status()."""

    def test_PRES_010_offline_no_sockets(self, service):
        """[PRES-010] Returns 'offline' when no sockets are connected."""
        now_ts = datetime.utcnow().timestamp()
        assert service._compute_status(0, now_ts, now_ts, now_ts) == 'offline'

    def test_PRES_011_offline_stale_seen(self, service):
        """[PRES-011] Returns 'offline' when last_seen is older than timeout."""
        now_ts = datetime.utcnow().timestamp()
        old_seen = now_ts - service.ONLINE_TIMEOUT_SECONDS - 10
        assert service._compute_status(1, old_seen, now_ts, now_ts) == 'offline'

    def test_PRES_012_offline_no_seen_ts(self, service):
        """[PRES-012] Returns 'offline' when last_seen is None."""
        now_ts = datetime.utcnow().timestamp()
        assert service._compute_status(1, None, now_ts, now_ts) == 'offline'

    def test_PRES_013_active_recent_activity(self, service):
        """[PRES-013] Returns 'active' when user has recent activity."""
        now_ts = datetime.utcnow().timestamp()
        assert service._compute_status(1, now_ts, now_ts, now_ts) == 'active'

    def test_PRES_014_online_no_recent_activity(self, service):
        """[PRES-014] Returns 'online' when seen recently but not active recently."""
        now_ts = datetime.utcnow().timestamp()
        old_active = now_ts - service.ACTIVE_WINDOW_SECONDS - 10
        assert service._compute_status(1, now_ts, old_active, now_ts) == 'online'

    def test_PRES_015_online_no_active_ts(self, service):
        """[PRES-015] Returns 'online' when last_active is None but seen recently."""
        now_ts = datetime.utcnow().timestamp()
        assert service._compute_status(1, now_ts, None, now_ts) == 'online'


# ---------------------------------------------------------------------------
# Tests: record_seen
# ---------------------------------------------------------------------------

class TestRecordSeen:
    """Tests for PresenceService.record_seen()."""

    def test_PRES_020_records_seen_in_redis(self, service, mock_redis, mock_user):
        """[PRES-020] record_seen stores a timestamp in the sorted set."""
        with patch.object(service, '_maybe_update_db'):
            result = service.record_seen(mock_user, 'sock_1')

        mock_redis.zadd.assert_any_call(
            PresenceService.KEY_USER_LAST_SEEN,
            {'42': pytest.approx(datetime.utcnow().timestamp(), abs=5)},
        )
        assert result['username'] == 'testuser'

    def test_PRES_021_registers_socket(self, service, mock_redis, mock_user):
        """[PRES-021] record_seen associates the socket ID with the user."""
        with patch.object(service, '_maybe_update_db'):
            service.record_seen(mock_user, 'sock_1')

        sockets_key = PresenceService.KEY_USER_SOCKETS.format(user_id='42')
        mock_redis.zadd.assert_any_call(
            sockets_key,
            {'sock_1': pytest.approx(datetime.utcnow().timestamp(), abs=5)},
        )
        mock_redis.setex.assert_called()
        mock_redis.expire.assert_called_with(sockets_key, PresenceService.SOCKET_TTL_SECONDS)

    def test_PRES_022_no_socket_skips_registration(self, service, mock_redis, mock_user):
        """[PRES-022] record_seen without socket_id does not register a socket."""
        with patch.object(service, '_maybe_update_db'):
            service.record_seen(mock_user, None)

        # Only one zadd call (the seen set), not the sockets set
        assert mock_redis.zadd.call_count == 1

    def test_PRES_023_purges_stale_sockets(self, service, mock_redis, mock_user):
        """[PRES-023] record_seen calls _purge_stale_sockets."""
        with patch.object(service, '_maybe_update_db'), \
             patch.object(service, '_purge_stale_sockets') as mock_purge:
            service.record_seen(mock_user, 'sock_1')

        mock_purge.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: record_active
# ---------------------------------------------------------------------------

class TestRecordActive:
    """Tests for PresenceService.record_active()."""

    def test_PRES_030_records_both_seen_and_active(self, service, mock_redis, mock_user):
        """[PRES-030] record_active stores timestamps in both sorted sets."""
        with patch.object(service, '_maybe_update_db'):
            result = service.record_active(mock_user, 'sock_1')

        zadd_keys = [c.args[0] for c in mock_redis.zadd.call_args_list]
        assert PresenceService.KEY_USER_LAST_SEEN in zadd_keys
        assert PresenceService.KEY_USER_LAST_ACTIVE in zadd_keys
        assert result['username'] == 'testuser'

    def test_PRES_031_triggers_db_write_for_both_timestamps(self, service, mock_redis, mock_user):
        """[PRES-031] record_active calls _maybe_update_db with both last_seen and last_active."""
        with patch.object(service, '_maybe_update_db') as mock_db:
            service.record_active(mock_user, None)

        mock_db.assert_called_once()
        _, kwargs = mock_db.call_args
        assert 'last_seen_at' in kwargs
        assert 'last_active_at' in kwargs


# ---------------------------------------------------------------------------
# Tests: remove_socket
# ---------------------------------------------------------------------------

class TestRemoveSocket:
    """Tests for PresenceService.remove_socket()."""

    def test_PRES_040_returns_none_for_empty_sid(self, service, mock_redis):
        """[PRES-040] Returns None when socket_id is empty."""
        assert service.remove_socket('') is None
        assert service.remove_socket(None) is None

    def test_PRES_041_returns_none_for_unknown_socket(self, service, mock_redis):
        """[PRES-041] Returns None when socket is not associated with any user."""
        mock_redis.get.return_value = None
        assert service.remove_socket('unknown_sock') is None

    def test_PRES_042_removes_socket_and_updates_seen(self, service, mock_redis):
        """[PRES-042] Removes the socket association and records a final seen timestamp."""
        mock_redis.get.return_value = '42'

        mock_user_obj = MagicMock()
        mock_user_obj.id = 42
        mock_user_obj.username = 'testuser'
        mock_user_obj.last_seen_at = None
        mock_user_obj.last_active_at = None

        with patch('services.presence_service.db') as mock_db, \
             patch.object(service, '_maybe_update_db'):
            mock_db.session.get.return_value = mock_user_obj
            result = service.remove_socket('sock_1')

        sockets_key = PresenceService.KEY_USER_SOCKETS.format(user_id='42')
        mock_redis.zrem.assert_called_once_with(sockets_key, 'sock_1')
        mock_redis.delete.assert_called_once_with(
            PresenceService.KEY_SOCKET_USER.format(sid='sock_1')
        )
        assert result is not None
        assert result['username'] == 'testuser'

    def test_PRES_043_returns_none_when_user_not_in_db(self, service, mock_redis):
        """[PRES-043] Returns None when the user ID from Redis is not in DB."""
        mock_redis.get.return_value = '999'

        with patch('services.presence_service.db') as mock_db, \
             patch.object(service, '_maybe_update_db'):
            mock_db.session.get.return_value = None
            result = service.remove_socket('sock_1')

        assert result is None


# ---------------------------------------------------------------------------
# Tests: build_user_payload
# ---------------------------------------------------------------------------

class TestBuildUserPayload:
    """Tests for PresenceService.build_user_payload()."""

    def test_PRES_050_payload_structure(self, service, mock_redis, mock_user):
        """[PRES-050] Payload contains all required keys."""
        result = service.build_user_payload(mock_user)

        assert 'user_id' in result
        assert 'username' in result
        assert 'status' in result
        assert 'last_seen_at' in result
        assert 'last_active_at' in result
        assert result['user_id'] == 42
        assert result['username'] == 'testuser'

    def test_PRES_051_offline_when_no_data(self, service, mock_redis, mock_user):
        """[PRES-051] Status is 'offline' when no Redis data exists."""
        result = service.build_user_payload(mock_user)
        assert result['status'] == 'offline'

    def test_PRES_052_active_when_sockets_and_recent(self, service, mock_redis, mock_user):
        """[PRES-052] Status is 'active' when sockets exist and activity is recent."""
        now_ts = datetime.utcnow().timestamp()
        mock_redis.zscore.side_effect = lambda key, uid: now_ts
        mock_redis.zcount.return_value = 1

        result = service.build_user_payload(mock_user, now_ts=now_ts)
        assert result['status'] == 'active'

    def test_PRES_053_uses_db_fallback_for_seen(self, service, mock_redis, mock_user):
        """[PRES-053] Falls back to DB last_seen_at when Redis has no score."""
        now = datetime.utcnow()
        mock_user.last_seen_at = now
        mock_redis.zscore.return_value = None
        mock_redis.zcount.return_value = 0

        result = service.build_user_payload(mock_user)
        # Should still be offline (no sockets), but last_seen_at should be populated
        assert result['last_seen_at'] is not None


# ---------------------------------------------------------------------------
# Tests: list_users
# ---------------------------------------------------------------------------

class TestListUsers:
    """Tests for PresenceService.list_users()."""

    def test_PRES_060_returns_list_for_all_active_users(self, service, mock_redis, app, db, app_context):
        """[PRES-060] Returns a list of payloads for all active, non-deleted users."""
        from db.models.user import User

        u1 = User(
            username='alice', password_hash='h', api_key='key-alice-pres',
            is_active=True,
        )
        u2 = User(
            username='bob', password_hash='h', api_key='key-bob-pres',
            is_active=True,
        )
        u3 = User(
            username='inactive', password_hash='h', api_key='key-inactive-pres',
            is_active=False,
        )
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        result = service.list_users()

        usernames = [p['username'] for p in result]
        assert 'alice' in usernames
        assert 'bob' in usernames
        assert 'inactive' not in usernames

    def test_PRES_061_empty_list_when_no_users(self, service, mock_redis, app, db, app_context):
        """[PRES-061] Returns empty list when no active users exist."""
        result = service.list_users()
        assert result == []


# ---------------------------------------------------------------------------
# Tests: _should_write_db (throttling)
# ---------------------------------------------------------------------------

class TestShouldWriteDb:
    """Tests for PresenceService._should_write_db() throttle logic."""

    def test_PRES_070_first_write_allowed(self, service, mock_redis):
        """[PRES-070] First write is allowed when no throttle key exists."""
        mock_redis.get.return_value = None
        assert service._should_write_db('presence:last_db_seen:42') is True
        mock_redis.setex.assert_called_once()

    def test_PRES_071_throttled_within_window(self, service, mock_redis):
        """[PRES-071] Write is throttled when last write was within the throttle window."""
        now_ts = datetime.utcnow().timestamp()
        mock_redis.get.return_value = str(now_ts - 10)  # 10 seconds ago
        assert service._should_write_db('presence:last_db_seen:42') is False

    def test_PRES_072_allowed_after_throttle_expires(self, service, mock_redis):
        """[PRES-072] Write is allowed when throttle window has expired."""
        now_ts = datetime.utcnow().timestamp()
        mock_redis.get.return_value = str(now_ts - service.DB_WRITE_THROTTLE_SECONDS - 10)
        assert service._should_write_db('presence:last_db_seen:42') is True

    def test_PRES_073_handles_corrupt_redis_value(self, service, mock_redis):
        """[PRES-073] Treats corrupt Redis values as 'no prior write'."""
        mock_redis.get.return_value = 'not-a-number'
        assert service._should_write_db('presence:last_db_seen:42') is True


# ---------------------------------------------------------------------------
# Tests: _maybe_update_db
# ---------------------------------------------------------------------------

class TestMaybeUpdateDb:
    """Tests for PresenceService._maybe_update_db()."""

    def test_PRES_080_skips_when_no_timestamps(self, service, mock_redis):
        """[PRES-080] Does not query DB when both timestamps are None."""
        with patch('services.presence_service.db') as mock_db:
            service._maybe_update_db(42)

        # No DB update should happen
        # _should_write_db won't be called either, nothing to update

    def test_PRES_081_writes_when_forced(self, service, mock_redis):
        """[PRES-081] Always writes to DB when force=True."""
        now = datetime.utcnow()
        with patch('services.presence_service.db') as mock_db:
            service._maybe_update_db(42, last_seen_at=now, force=True)

        mock_db.session.query.return_value.filter_by.return_value.update.assert_called_once()
        mock_db.session.commit.assert_called_once()

    def test_PRES_082_rolls_back_on_error(self, service, mock_redis):
        """[PRES-082] Rolls back DB session on exception."""
        now = datetime.utcnow()
        with patch('services.presence_service.db') as mock_db:
            mock_db.session.query.return_value.filter_by.return_value.update.side_effect = Exception('DB error')
            service._maybe_update_db(42, last_seen_at=now, force=True)

        mock_db.session.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: _purge_stale_sockets
# ---------------------------------------------------------------------------

class TestPurgeStale:
    """Tests for PresenceService._purge_stale_sockets()."""

    def test_PRES_090_removes_old_entries(self, service, mock_redis):
        """[PRES-090] Removes socket entries older than 2x the online timeout."""
        now_ts = datetime.utcnow().timestamp()
        service._purge_stale_sockets('presence:user:sockets:42', now_ts)

        expected_threshold = now_ts - (service.ONLINE_TIMEOUT_SECONDS * 2)
        mock_redis.zremrangebyscore.assert_called_once_with(
            'presence:user:sockets:42', 0, expected_threshold
        )

    def test_PRES_091_swallows_redis_error(self, service, mock_redis):
        """[PRES-091] Does not raise when Redis errors during purge."""
        mock_redis.zremrangebyscore.side_effect = ConnectionError('Redis down')
        now_ts = datetime.utcnow().timestamp()
        # Should not raise
        service._purge_stale_sockets('presence:user:sockets:42', now_ts)
