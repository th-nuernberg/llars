"""
Route Tests for Admin API
==========================

Tests for app/routes/admin/system_settings_routes.py.
Covers: System settings CRUD, admin-only access, non-admin forbidden.

Uses real blueprints with mocked OIDC token validation.
"""

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Get System Settings
# ---------------------------------------------------------------------------

class TestGetSystemSettings:
    """Tests for GET /api/admin/system/settings"""

    def test_ROUTE_ADMIN_GETSYS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/admin/system/settings')
        assert response.status_code == 401

    def test_ROUTE_ADMIN_GETSYS_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/admin/system/settings')
            assert response.status_code == 403

    def test_ROUTE_ADMIN_GETSYS_003_forbidden_researcher(self, auth_researcher, real_app):
        with real_app.app_context():
            response = auth_researcher.get('/api/admin/system/settings')
            assert response.status_code == 403

    def test_ROUTE_ADMIN_GETSYS_004_success_admin(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/system/settings')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'settings' in data


# ---------------------------------------------------------------------------
# Update System Settings
# ---------------------------------------------------------------------------

class TestUpdateSystemSettings:
    """Tests for PATCH /api/admin/system/settings"""

    def test_ROUTE_ADMIN_UPDSYS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.patch('/api/admin/system/settings',
                                 json={'crawl_timeout_seconds': 120})
        assert response.status_code == 401

    def test_ROUTE_ADMIN_UPDSYS_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.patch('/api/admin/system/settings',
                                       json={'crawl_timeout_seconds': 120})
            assert response.status_code == 403

    def test_ROUTE_ADMIN_UPDSYS_003_forbidden_researcher(self, auth_researcher, real_app):
        with real_app.app_context():
            response = auth_researcher.patch('/api/admin/system/settings',
                                             json={'crawl_timeout_seconds': 120})
            assert response.status_code == 403

    def test_ROUTE_ADMIN_UPDSYS_004_update_crawl_timeout(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/system/settings',
                                        json={'crawl_timeout_seconds': 300})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'crawl_timeout_seconds' in data['updated_fields']

    def test_ROUTE_ADMIN_UPDSYS_005_update_bool_field(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/system/settings',
                                        json={'self_registration_enabled': True})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'self_registration_enabled' in data['updated_fields']

    def test_ROUTE_ADMIN_UPDSYS_006_update_string_field(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/system/settings',
                                        json={'default_referral_role': 'evaluator'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'default_referral_role' in data['updated_fields']

    def test_ROUTE_ADMIN_UPDSYS_009_clamp_to_range(self, auth_admin, real_app):
        with real_app.app_context():
            # Send value above max range (86400 for crawl_timeout_seconds)
            response = auth_admin.patch('/api/admin/system/settings',
                                        json={'crawl_timeout_seconds': 999999})
            assert response.status_code == 200
            data = response.get_json()
            # Value should be clamped to 86400
            assert data['settings']['crawl_timeout_seconds'] == 86400

    def test_ROUTE_ADMIN_UPDSYS_010_empty_payload(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/system/settings', json={})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['updated_fields'] == []

    def test_ROUTE_ADMIN_UPDSYS_011_batch_generation_max_parallel(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/system/settings',
                                        json={'batch_generation_max_parallel': 8})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['settings']['batch_generation_max_parallel'] == 8


# ---------------------------------------------------------------------------
# Communication Status (public)
# ---------------------------------------------------------------------------

class TestCommunicationStatus:
    """Tests for GET /api/system/communication-status"""

    def test_ROUTE_ADMIN_COMMSTAT_001_public_access(self, rclient, rdb, rmock_token):
        """Communication status is publicly accessible."""
        response = rclient.get('/api/system/communication-status')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'communication_enabled' in data
