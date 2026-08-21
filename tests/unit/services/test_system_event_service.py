"""
Unit tests for SystemEventService.

Tests system event logging including:
- Persisting events to DB
- Throttling repeated events within a window
- Deduplication of identical events
- Best-effort behavior (never raises)
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from services.system_event_service import SystemEventService, _THROTTLE_STATE


@pytest.fixture(autouse=True)
def _clear_throttle_state():
    """Clear throttle state between tests to ensure isolation."""
    _THROTTLE_STATE.clear()
    yield
    _THROTTLE_STATE.clear()


class TestLogEventBasic:
    """Tests for basic event logging."""

    def test_SYS_EVT_001_persists_event_to_db(self, app, db, app_context):
        """[SYS_EVT-001] Should persist a valid event to the database."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(
            event_type='user.login',
            message='User alice logged in',
            severity='info',
            username='alice',
        )

        events = SystemEvent.query.all()
        assert len(events) == 1
        evt = events[0]
        assert evt.event_type == 'user.login'
        assert evt.message == 'User alice logged in'
        assert evt.severity == 'info'
        assert evt.username == 'alice'

    def test_SYS_EVT_002_normalizes_severity(self, app, db, app_context):
        """[SYS_EVT-002] Should normalize severity to lowercase and strip whitespace."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(
            event_type='test.severity',
            message='Test',
            severity='  WARNING  ',
        )

        evt = SystemEvent.query.first()
        assert evt.severity == 'warning'

    def test_SYS_EVT_003_defaults_invalid_severity_to_info(self, app, db, app_context):
        """[SYS_EVT-003] Should default to 'info' when severity is unrecognized."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(
            event_type='test.bad_sev',
            message='Bad severity',
            severity='catastrophe',
        )

        evt = SystemEvent.query.first()
        assert evt.severity == 'info'

    def test_SYS_EVT_004_accepts_all_valid_severities(self, app, db, app_context):
        """[SYS_EVT-004] Should accept all recognized severity values."""
        from db.models.system_event import SystemEvent

        valid = ['debug', 'info', 'warning', 'error', 'critical', 'success', 'ci_cd']
        for sev in valid:
            SystemEventService.log_event(
                event_type=f'test.{sev}',
                message=f'Test {sev}',
                severity=sev,
            )

        events = SystemEvent.query.all()
        assert len(events) == len(valid)
        for evt, sev in zip(events, valid):
            assert evt.severity == sev

    def test_SYS_EVT_005_skips_empty_event_type(self, app, db, app_context):
        """[SYS_EVT-005] Should silently skip when event_type is empty."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(event_type='', message='Should be skipped')

        assert SystemEvent.query.count() == 0

    def test_SYS_EVT_006_skips_empty_message(self, app, db, app_context):
        """[SYS_EVT-006] Should silently skip when message is empty."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(event_type='test.skip', message='')

        assert SystemEvent.query.count() == 0

    def test_SYS_EVT_007_stores_entity_info(self, app, db, app_context):
        """[SYS_EVT-007] Should store entity_type and entity_id."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(
            event_type='scenario.created',
            message='Created scenario',
            entity_type='scenario',
            entity_id=42,
        )

        evt = SystemEvent.query.first()
        assert evt.entity_type == 'scenario'
        assert evt.entity_id == '42'  # Converted to str

    def test_SYS_EVT_008_stores_details_json(self, app, db, app_context):
        """[SYS_EVT-008] Should store details dict as JSON."""
        from db.models.system_event import SystemEvent

        details = {'ip': '192.168.1.1', 'action': 'bulk_delete'}
        SystemEventService.log_event(
            event_type='admin.action',
            message='Admin performed action',
            details=details,
        )

        evt = SystemEvent.query.first()
        assert evt.details == details


class TestThrottling:
    """Tests for event throttling."""

    def test_SYS_EVT_009_throttles_within_window(self, app, db, app_context):
        """[SYS_EVT-009] Should suppress duplicate events within throttle window."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(
            event_type='rate.limited',
            message='First call',
            throttle_key='test_key',
            throttle_seconds=60,
        )
        SystemEventService.log_event(
            event_type='rate.limited',
            message='Second call (should be throttled)',
            throttle_key='test_key',
            throttle_seconds=60,
        )

        events = SystemEvent.query.all()
        assert len(events) == 1
        assert events[0].message == 'First call'

    def test_SYS_EVT_010_allows_after_throttle_expires(self, app, db, app_context):
        """[SYS_EVT-010] Should allow event after throttle window expires."""
        from db.models.system_event import SystemEvent

        # First event
        SystemEventService.log_event(
            event_type='rate.limited',
            message='First call',
            throttle_key='expire_key',
            throttle_seconds=1,
        )

        # Simulate expiry by manipulating the throttle state timestamp
        _THROTTLE_STATE['expire_key'] = time.monotonic() - 2.0

        SystemEventService.log_event(
            event_type='rate.limited',
            message='After expiry',
            throttle_key='expire_key',
            throttle_seconds=1,
        )

        events = SystemEvent.query.all()
        assert len(events) == 2

    def test_SYS_EVT_011_different_throttle_keys_independent(self, app, db, app_context):
        """[SYS_EVT-011] Events with different throttle keys should not interfere."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(
            event_type='rate.a',
            message='Key A',
            throttle_key='key_a',
            throttle_seconds=60,
        )
        SystemEventService.log_event(
            event_type='rate.b',
            message='Key B',
            throttle_key='key_b',
            throttle_seconds=60,
        )

        events = SystemEvent.query.all()
        assert len(events) == 2


class TestDeduplication:
    """Tests for event deduplication."""

    def test_SYS_EVT_012_deduplicates_existing_event(self, app, db, app_context):
        """[SYS_EVT-012] Should skip event when dedupe=True and matching event exists."""
        from db.models.system_event import SystemEvent

        SystemEventService.log_event(
            event_type='setup.complete',
            message='Setup done',
            username='admin',
            entity_type='system',
            entity_id='1',
            dedupe=True,
        )
        SystemEventService.log_event(
            event_type='setup.complete',
            message='Setup done again',
            username='admin',
            entity_type='system',
            entity_id='1',
            dedupe=True,
        )

        events = SystemEvent.query.all()
        assert len(events) == 1

    def test_SYS_EVT_013_no_dedupe_allows_duplicates(self, app, db, app_context):
        """[SYS_EVT-013] Should allow duplicate events when dedupe is False (default)."""
        from db.models.system_event import SystemEvent

        for _ in range(3):
            SystemEventService.log_event(
                event_type='repeated.event',
                message='Repeated',
            )

        events = SystemEvent.query.all()
        assert len(events) == 3


class TestExceptionSwallowing:
    """Tests that log_event never raises exceptions."""

    def test_SYS_EVT_014_swallows_db_errors(self, app, db, app_context):
        """[SYS_EVT-014] Should swallow database errors without raising."""
        # The service imports db lazily inside the try block.
        # Patch the db.session.commit to simulate a DB failure.
        with patch('db.database.db.session') as mock_session:
            mock_session.add.side_effect = RuntimeError('DB is down')

            # Should not raise despite the DB error
            SystemEventService.log_event(
                event_type='test.error',
                message='Should not crash',
            )

    def test_SYS_EVT_015_swallows_import_errors(self, app, db, app_context):
        """[SYS_EVT-015] Should swallow errors even if internal imports fail."""
        # The service does lazy imports inside the try block,
        # so if they fail, the exception handler should catch it.
        with patch.dict('sys.modules', {'db.models.system_event': None}):
            # This should NOT raise
            SystemEventService.log_event(
                event_type='test.import_fail',
                message='Import should be swallowed',
            )

    def test_SYS_EVT_016_captures_request_context_when_available(self, app, db, app_context):
        """[SYS_EVT-016] Should capture request path and remote addr from request context."""
        from db.models.system_event import SystemEvent

        with app.test_request_context(
            '/api/test/endpoint',
            headers={'X-Real-IP': '10.0.0.1', 'User-Agent': 'TestBot/1.0'},
        ):
            SystemEventService.log_event(
                event_type='test.request',
                message='With request context',
            )

        evt = SystemEvent.query.first()
        assert evt is not None
        assert evt.request_path == '/api/test/endpoint'
        assert evt.remote_addr == '10.0.0.1'
        assert evt.user_agent == 'TestBot/1.0'

    def test_SYS_EVT_017_works_without_request_context(self, app, db, app_context):
        """[SYS_EVT-017] Should work fine outside of a request context."""
        from db.models.system_event import SystemEvent

        # Patch has_request_context to simulate being called outside any request
        with patch('services.system_event_service.has_request_context', return_value=False):
            SystemEventService.log_event(
                event_type='test.no_request',
                message='No request context',
            )

        evt = SystemEvent.query.first()
        assert evt is not None
        assert evt.request_path is None
        assert evt.remote_addr is None
        assert evt.user_agent is None
