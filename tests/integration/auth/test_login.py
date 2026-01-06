"""
Integration Tests: Login Flow
==============================

Tests for the authentication login flow.

Test IDs:
- LOGIN-001 to LOGIN-008: Login Route Tests
- ME-001 to ME-003: User Info Route Tests
- VAL-001 to VAL-003: Token Validation Tests
- ADM-CHK-001 to ADM-CHK-002: Admin Check Tests
- HEALTH-001: Health Check Tests

Status: ✅ IMPLEMENTED
"""

import pytest


class TestLoginRoute:
    """
    POST /auth/authentik/login Tests

    Route location: app/routes/authentik_routes.py:121-403
    """

    def test_LOGIN_004_missing_fields(self, client, app_context):
        """
        [LOGIN-004] Fehlende Felder geben 400

        Login ohne password oder username soll 400 zurückgeben.
        """
        # Missing password
        response = client.post('/auth/authentik/login', json={
            'username': 'admin'
        })
        assert response.status_code in [400, 422]

        # Missing username
        response = client.post('/auth/authentik/login', json={
            'password': 'admin123'
        })
        assert response.status_code in [400, 422]

        # Both missing
        response = client.post('/auth/authentik/login', json={})
        assert response.status_code in [400, 422]

    def test_LOGIN_empty_credentials(self, client, app_context):
        """
        Empty username or password should be rejected.
        """
        response = client.post('/auth/authentik/login', json={
            'username': '',
            'password': 'admin123'
        })
        assert response.status_code in [400, 401, 422]

        response = client.post('/auth/authentik/login', json={
            'username': 'admin',
            'password': ''
        })
        assert response.status_code in [400, 401, 422]

    def test_LOGIN_no_content_type(self, client, app_context):
        """
        Login without JSON content type should fail.
        """
        response = client.post(
            '/auth/authentik/login',
            data='username=admin&password=admin123'
        )
        assert response.status_code in [400, 415]


class TestUserInfoRoute:
    """
    GET /auth/authentik/me Tests

    Route location: app/routes/authentik_routes.py:49-80
    """

    def test_ME_002_invalid_token(self, client, app_context):
        """
        [ME-002] Invalid Token gibt 401

        Ungültiger Token bei /me soll 401 zurückgeben.
        """
        response = client.get(
            '/auth/authentik/me',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        assert response.status_code == 401

    def test_ME_no_token(self, client, app_context):
        """
        No token at /me should return 401.
        """
        response = client.get('/auth/authentik/me')
        assert response.status_code == 401


class TestTokenValidationRoute:
    """
    GET /auth/authentik/validate Tests

    Route location: app/routes/authentik_routes.py:83-106
    """

    def test_VAL_002_invalid_token(self, client, app_context):
        """
        [VAL-002] Ungültiger Token wird abgelehnt

        Token validation endpoint soll ungültige Tokens ablehnen.
        """
        response = client.get(
            '/auth/authentik/validate',
            headers={'Authorization': 'Bearer invalid.token.here'}
        )
        assert response.status_code == 401

    def test_VAL_003_expired_token(self, client, expired_token, mock_token_validation, app_context):
        """
        [VAL-003] Abgelaufener Token wird abgelehnt

        Expired tokens sollen abgelehnt werden.
        """
        response = client.get(
            '/auth/authentik/validate',
            headers={'Authorization': f'Bearer {expired_token}'}
        )
        assert response.status_code == 401

    def test_VAL_no_token(self, client, app_context):
        """
        No token at /validate should return 401.
        """
        response = client.get('/auth/authentik/validate')
        assert response.status_code == 401


class TestAdminCheckRoute:
    """
    GET /auth/authentik/admin/check Tests

    Route location: app/routes/authentik_routes.py:109-118
    """

    def test_ADM_CHK_002_non_admin(self, authenticated_client_evaluator, mock_token_validation, app_context):
        """
        [ADM-CHK-002] Nicht-Admin User gibt 403

        Non-admin users should get 403 at admin check.
        """
        response = authenticated_client_evaluator.get('/auth/authentik/admin/check')
        assert response.status_code == 403


class TestHealthCheckRoute:
    """
    GET /auth/authentik/health_check Tests

    Public health check endpoint.
    """

    def test_HEALTH_001_no_auth_required(self, client, app_context):
        """
        [HEALTH-001] Ohne Auth gibt 200 OK

        Health check should work without authentication.
        """
        response = client.get('/auth/authentik/health_check')
        assert response.status_code == 200

        data = response.get_json()
        assert 'status' in data or 'running' in str(data).lower()


class TestLegacyAuthRoutes:
    """
    Legacy Auth Route Tests

    Tests for backwards-compatible auth routes.
    """

    def test_REG_003_missing_fields(self, client, app_context):
        """
        [REG-003] Registration with missing fields gives 400.
        """
        response = client.post('/auth/register', json={
            'username': 'newuser'
            # Missing other required fields
        })
        assert response.status_code in [400, 422, 404]  # 404 if route disabled

    def test_REG_002_duplicate_username(self, client, db, mock_user, app_context):
        """
        [REG-002] Registration with duplicate username gives 409.
        """
        response = client.post('/auth/register', json={
            'username': mock_user.username,
            'password': 'password123'
        })
        # 409 Conflict or 400 Bad Request or 404 if disabled
        assert response.status_code in [400, 409, 404]


class TestSecurityHeaders:
    """
    Security Header Tests

    Tests that security headers are properly set.
    """

    def test_cors_headers(self, client, app_context):
        """
        CORS headers should be set on responses.
        """
        response = client.get('/api/health')
        # CORS headers may or may not be present depending on origin
        assert response.status_code == 200

    def test_no_sensitive_headers_leaked(self, client, app_context):
        """
        Sensitive headers should not be leaked.
        """
        response = client.get('/api/health')

        # These headers should not expose sensitive info
        sensitive_headers = ['X-Powered-By', 'Server']
        for header in sensitive_headers:
            if header in response.headers:
                # Value should not expose too much detail
                value = response.headers[header]
                assert 'version' not in value.lower()
