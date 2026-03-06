"""
Route Tests for System Monitor API
=====================================

Tests for app/routes/system_monitor/system_monitor_routes.py.
Covers: System events list, CI/CD event ingestion, chatbot activity,
        admin-only access enforcement.

Uses real blueprints with mocked OIDC token validation.
Prefix: ROUTE_SYSMON
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# GET /api/admin/system/events (List system events)
# ---------------------------------------------------------------------------

class TestListSystemEvents:
    """Tests for GET /api/admin/system/events"""

    def test_ROUTE_SYSMON_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/admin/system/events')
        assert response.status_code == 401

    def test_ROUTE_SYSMON_LIST_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/admin/system/events')
            assert response.status_code == 403

    def test_ROUTE_SYSMON_LIST_003_forbidden_researcher(self, auth_researcher, real_app):
        with real_app.app_context():
            response = auth_researcher.get('/api/admin/system/events')
            assert response.status_code == 403

    def test_ROUTE_SYSMON_LIST_004_admin_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/system/events')
            assert response.status_code == 200
            data = response.get_json()
            assert 'events' in data
            assert isinstance(data['events'], list)

    def test_ROUTE_SYSMON_LIST_005_with_limit(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/system/events?limit=10')
            assert response.status_code == 200

    def test_ROUTE_SYSMON_LIST_006_with_severity_filter(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/system/events?severity=error')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data['events'], list)

    def test_ROUTE_SYSMON_LIST_007_with_event_type_filter(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/system/events?event_type=admin')
            assert response.status_code == 200

    def test_ROUTE_SYSMON_LIST_008_with_before_id(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/system/events?before_id=1000')
            assert response.status_code == 200

    def test_ROUTE_SYSMON_LIST_009_with_seeded_event(self, auth_admin, real_app):
        """Verify that events appear in the response after creation."""
        with real_app.app_context():
            from db.database import db
            from db.models.system_event import SystemEvent
            from datetime import datetime

            event = SystemEvent(
                event_type='test.event',
                severity='info',
                message='Test event message',
                username='admin',
                created_at=datetime.utcnow()
            )
            db.session.add(event)
            db.session.commit()

            response = auth_admin.get('/api/admin/system/events')
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['events']) >= 1
            event_types = [e['event_type'] for e in data['events']]
            assert 'test.event' in event_types


# ---------------------------------------------------------------------------
# POST /api/admin/system/events/ci-cd (CI/CD event ingestion)
# ---------------------------------------------------------------------------

class TestIngestCiCdEvent:
    """Tests for POST /api/admin/system/events/ci-cd (system API key required)"""

    def test_ROUTE_SYSMON_CICD_001_no_api_key(self, rclient, rdb, rmock_token):
        """Without system API key, should fail."""
        response = rclient.post('/api/admin/system/events/ci-cd',
                                json={'message': 'pipeline started'})
        # system_api_key_required returns 401 or 403
        assert response.status_code in (401, 403)

    def test_ROUTE_SYSMON_CICD_002_wrong_api_key(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/admin/system/events/ci-cd',
                                json={'message': 'test'},
                                headers={'X-API-Key': 'wrong-key'})
        assert response.status_code in (401, 403)

    def test_ROUTE_SYSMON_CICD_003_missing_message(self, rclient, rdb, rmock_token):
        """Valid API key but missing message should return 400."""
        response = rclient.post('/api/admin/system/events/ci-cd',
                                json={'event_type': 'ci_cd.test'},
                                headers={'X-API-Key': 'test-system-api-key-12345'})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    @patch('services.system_event_service.SystemEventService.log_event')
    def test_ROUTE_SYSMON_CICD_004_success(self, mock_log, rclient, rdb, rmock_token):
        """Valid API key and message should succeed."""
        response = rclient.post('/api/admin/system/events/ci-cd',
                                json={
                                    'event_type': 'ci_cd.pipeline',
                                    'message': 'Pipeline #123 started',
                                    'severity': 'ci_cd',
                                    'username': 'gitlab-ci',
                                    'entity_type': 'pipeline',
                                    'entity_id': '123',
                                },
                                headers={'X-API-Key': 'test-system-api-key-12345'})
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        # log_event is called for CI/CD event (may also be called by other
        # background processes, so just verify it was called at least once
        # with the expected event_type)
        ci_cd_calls = [c for c in mock_log.call_args_list
                       if c.kwargs.get('event_type', '') == 'ci_cd.pipeline']
        assert len(ci_cd_calls) == 1

    @patch('services.system_event_service.SystemEventService.log_event')
    def test_ROUTE_SYSMON_CICD_005_minimal_payload(self, mock_log, rclient, rdb, rmock_token):
        """Minimal valid payload with just message."""
        response = rclient.post('/api/admin/system/events/ci-cd',
                                json={'message': 'deployment done'},
                                headers={'X-API-Key': 'test-system-api-key-12345'})
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# GET /api/admin/chatbot-activity (Chatbot activity)
# ---------------------------------------------------------------------------

class TestChatbotActivity:
    """Tests for GET /api/admin/chatbot-activity"""

    def test_ROUTE_SYSMON_ACTIVITY_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/admin/chatbot-activity')
        assert response.status_code == 401

    def test_ROUTE_SYSMON_ACTIVITY_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/admin/chatbot-activity')
            assert response.status_code == 403

    @patch('routes.system_monitor.system_monitor_routes.ChatbotActivityService.get_activities')
    def test_ROUTE_SYSMON_ACTIVITY_003_admin_success(self, mock_act, auth_admin, real_app):
        with real_app.app_context():
            mock_act.return_value = [
                {'id': 1, 'event_type': 'chatbot.created', 'message': 'Bot created'}
            ]
            response = auth_admin.get('/api/admin/chatbot-activity')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'activities' in data
            assert data['count'] == 1

    @patch('routes.system_monitor.system_monitor_routes.ChatbotActivityService.get_activities')
    def test_ROUTE_SYSMON_ACTIVITY_004_with_filters(self, mock_act, auth_admin, real_app):
        with real_app.app_context():
            mock_act.return_value = []
            response = auth_admin.get(
                '/api/admin/chatbot-activity?limit=10&offset=5&period=24h&username=admin&type=chatbot'
            )
            assert response.status_code == 200
            mock_act.assert_called_once()


# ---------------------------------------------------------------------------
# GET /api/admin/chatbot-activity/stats (Activity stats)
# ---------------------------------------------------------------------------

class TestChatbotActivityStats:
    """Tests for GET /api/admin/chatbot-activity/stats"""

    def test_ROUTE_SYSMON_STATS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/admin/chatbot-activity/stats')
        assert response.status_code == 401

    def test_ROUTE_SYSMON_STATS_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/admin/chatbot-activity/stats')
            assert response.status_code == 403

    @patch('routes.system_monitor.system_monitor_routes.ChatbotActivityService.get_activity_stats')
    def test_ROUTE_SYSMON_STATS_003_admin_success(self, mock_stats, auth_admin, real_app):
        with real_app.app_context():
            mock_stats.return_value = {
                'total_events': 42,
                'by_type': {'chatbot.created': 10}
            }
            response = auth_admin.get('/api/admin/chatbot-activity/stats')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'stats' in data

    @patch('routes.system_monitor.system_monitor_routes.ChatbotActivityService.get_activity_stats')
    def test_ROUTE_SYSMON_STATS_004_custom_period(self, mock_stats, auth_admin, real_app):
        with real_app.app_context():
            mock_stats.return_value = {}
            response = auth_admin.get('/api/admin/chatbot-activity/stats?period=168')
            assert response.status_code == 200
            mock_stats.assert_called_once_with(period_hours=168)
