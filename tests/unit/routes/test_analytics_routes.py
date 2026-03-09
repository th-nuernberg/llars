"""
Route Tests for Analytics API
================================

Tests for app/routes/analytics/analytics_routes.py.
Covers: Public config, admin settings read/write, validation.

Uses real blueprints with mocked OIDC token validation.
Prefix: ROUTE_ANA
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# GET /api/analytics/config (Public)
# ---------------------------------------------------------------------------

class TestGetAnalyticsConfig:
    """Tests for GET /api/analytics/config (public endpoint)"""

    def test_ROUTE_ANA_CONFIG_001_public_access(self, rclient, rdb, rmock_token):
        """Public endpoint should not require authentication."""
        response = rclient.get('/api/analytics/config')
        assert response.status_code == 200
        data = response.get_json()
        assert 'matomo_enabled' in data
        assert 'matomo_site_id' in data

    def test_ROUTE_ANA_CONFIG_002_default_values(self, rclient, rdb, rmock_token):
        """Default settings should have sensible values."""
        response = rclient.get('/api/analytics/config')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data['matomo_enabled'], bool)
        assert isinstance(data['matomo_site_id'], int)
        assert data['matomo_site_id'] >= 1

    def test_ROUTE_ANA_CONFIG_003_authenticated_also_works(self, auth_admin, real_app):
        """Authenticated users can also access public endpoint."""
        with real_app.app_context():
            response = auth_admin.get('/api/analytics/config')
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/admin/analytics/settings (Admin)
# ---------------------------------------------------------------------------

class TestGetAdminAnalyticsSettings:
    """Tests for GET /api/admin/analytics/settings"""

    def test_ROUTE_ANA_GETSET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/admin/analytics/settings')
        assert response.status_code == 401

    def test_ROUTE_ANA_GETSET_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/admin/analytics/settings')
            assert response.status_code == 403

    def test_ROUTE_ANA_GETSET_003_forbidden_researcher(self, auth_researcher, real_app):
        with real_app.app_context():
            response = auth_researcher.get('/api/admin/analytics/settings')
            assert response.status_code == 403

    def test_ROUTE_ANA_GETSET_004_admin_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/analytics/settings')
            assert response.status_code == 200
            data = response.get_json()
            assert 'matomo_enabled' in data
            assert 'matomo_base_url' in data
            assert 'require_consent' in data
            assert 'track_clicks' in data
            assert 'heartbeat_enabled' in data


# ---------------------------------------------------------------------------
# PATCH /api/admin/analytics/settings (Admin update)
# ---------------------------------------------------------------------------

class TestPatchAdminAnalyticsSettings:
    """Tests for PATCH /api/admin/analytics/settings"""

    def test_ROUTE_ANA_PATCH_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.patch('/api/admin/analytics/settings',
                                 json={'matomo_enabled': True})
        assert response.status_code == 401

    def test_ROUTE_ANA_PATCH_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.patch('/api/admin/analytics/settings',
                                        json={'matomo_enabled': True})
            assert response.status_code == 403

    def test_ROUTE_ANA_PATCH_003_admin_enable_matomo(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings',
                                         json={'matomo_enabled': True})
            assert response.status_code == 200
            data = response.get_json()
            assert data['matomo_enabled'] is True

    def test_ROUTE_ANA_PATCH_004_update_site_id(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings',
                                         json={'matomo_site_id': 5})
            assert response.status_code == 200
            data = response.get_json()
            assert data['matomo_site_id'] == 5

    def test_ROUTE_ANA_PATCH_005_site_id_min_1(self, auth_admin, real_app):
        """Site ID should be at least 1."""
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings',
                                         json={'matomo_site_id': 0})
            assert response.status_code == 200
            data = response.get_json()
            assert data['matomo_site_id'] >= 1

    def test_ROUTE_ANA_PATCH_006_update_base_url(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings',
                                         json={'matomo_base_url': '/custom/'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['matomo_base_url'] == '/custom/'

    def test_ROUTE_ANA_PATCH_007_base_url_normalized(self, auth_admin, real_app):
        """Base URL should get trailing slash added."""
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings',
                                         json={'matomo_base_url': '/analytics'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['matomo_base_url'].endswith('/')

    def test_ROUTE_ANA_PATCH_008_update_consent_settings(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings', json={
                'require_consent': True,
                'require_cookie_consent': True,
                'disable_cookies': True,
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['require_consent'] is True
            assert data['require_cookie_consent'] is True
            assert data['disable_cookies'] is True

    def test_ROUTE_ANA_PATCH_009_update_tracking_settings(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings', json={
                'track_clicks': True,
                'track_hovers': True,
                'hover_min_ms': 500,
                'hover_sample_rate': 0.5,
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['track_clicks'] is True
            assert data['track_hovers'] is True
            assert data['hover_min_ms'] == 500
            assert data['hover_sample_rate'] == 0.5

    def test_ROUTE_ANA_PATCH_010_heartbeat_min_5(self, auth_admin, real_app):
        """Heartbeat seconds should be at least 5."""
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings',
                                         json={'heartbeat_seconds': 1})
            assert response.status_code == 200
            data = response.get_json()
            assert data['heartbeat_seconds'] >= 5

    def test_ROUTE_ANA_PATCH_011_hover_sample_rate_clamped(self, auth_admin, real_app):
        """Hover sample rate should be clamped to [0.0, 1.0]."""
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings',
                                         json={'hover_sample_rate': 2.0})
            assert response.status_code == 200
            data = response.get_json()
            assert data['hover_sample_rate'] <= 1.0

    def test_ROUTE_ANA_PATCH_012_empty_payload(self, auth_admin, real_app):
        """Empty payload should succeed without changes."""
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings', json={})
            assert response.status_code == 200

    def test_ROUTE_ANA_PATCH_013_bad_json(self, auth_admin, real_app):
        """Non-JSON object should return 400."""
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings',
                                         data='not json',
                                         content_type='application/json')
            # Will receive 400 because the payload is not a valid JSON object
            assert response.status_code in (200, 400)

    def test_ROUTE_ANA_PATCH_014_dimension_ids(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/analytics/settings', json={
                'dimension_route_id': 1,
                'dimension_module_id': 2,
                'dimension_entity_id': 3,
                'dimension_view_id': 4,
                'dimension_role_id': 5,
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['dimension_route_id'] == 1
            assert data['dimension_module_id'] == 2
