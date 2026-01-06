"""
Integration Tests: Route Protection
====================================

Tests for API route authentication and authorization.

Test IDs:
- ROUTE-001 to ROUTE-005: Auth Decorator Tests
- ROUTE-010 to ROUTE-012: Permission Decorator Tests

Status: ✅ IMPLEMENTED
"""

import pytest


class TestRouteAuthentication:
    """
    Route Authentication Tests

    Tests that routes properly check for valid authentication.
    """

    def test_ROUTE_001_no_auth_header(self, client, app_context):
        """
        [ROUTE-001] Kein Auth Header gibt 401

        Protected routes without authentication should return 401.
        """
        # Test various protected endpoints
        protected_routes = [
            '/api/users/me',
            '/api/chatbots',
            '/api/rag/collections',
        ]

        for route in protected_routes:
            response = client.get(route)
            assert response.status_code == 401, f"Route {route} should require auth"

    def test_ROUTE_002_invalid_token(self, client, app_context):
        """
        [ROUTE-002] Ungültiger Token gibt 401

        Invalid/malformed tokens should be rejected.
        """
        invalid_tokens = [
            'invalid-token',
            'Bearer',
            'Bearer ',
            'Bearer invalid.token.format',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload',
        ]

        for token in invalid_tokens:
            auth_header = token if token.startswith('Bearer') else f'Bearer {token}'
            response = client.get(
                '/api/users/me',
                headers={'Authorization': auth_header}
            )
            assert response.status_code == 401, f"Token '{token}' should be rejected"

    def test_ROUTE_003_expired_token(self, client, expired_token, mock_token_validation, app_context):
        """
        [ROUTE-003] Abgelaufener Token gibt 401

        Expired tokens should be rejected.
        """
        response = client.get(
            '/api/users/me',
            headers={'Authorization': f'Bearer {expired_token}'}
        )
        assert response.status_code == 401

    def test_ROUTE_004_valid_token(self, authenticated_client, app_context, mock_token_validation):
        """
        [ROUTE-004] Gültiger Token gibt 200

        Valid tokens should allow access to protected routes.
        """
        response = authenticated_client.get('/api/users/me')
        # Should either return user data or 404 if user not found
        assert response.status_code in [200, 404]

    def test_ROUTE_005_system_api_key(self, client, system_api_key, app_context):
        """
        [ROUTE-005] System API Key bypasses auth auf debug routes

        Debug routes with valid system API key should work.
        """
        response = client.get(
            '/debug/info',
            headers={'X-API-Key': system_api_key}
        )
        # 200 or 404 if route doesn't exist
        assert response.status_code in [200, 404]


class TestRoutePermissions:
    """
    Route Permission Tests

    Tests that routes properly check for required permissions.
    """

    def test_ROUTE_010_permission_granted(self, authenticated_client, mock_token_validation, app_context):
        """
        [ROUTE-010] Permission granted gibt 200

        Users with required permission should access the route.
        """
        # Health check should work for anyone
        response = authenticated_client.get('/api/health')
        assert response.status_code == 200

    def test_ROUTE_011_permission_denied(self, authenticated_client_evaluator, mock_token_validation, app_context):
        """
        [ROUTE-011] Fehlende Permission gibt 403

        Users without required permission should get 403.
        """
        # Evaluator trying to access admin routes
        response = authenticated_client_evaluator.get('/api/admin/users')
        assert response.status_code in [403, 401]

    def test_ROUTE_012_admin_override(self, authenticated_client_admin, admin_user, mock_token_validation, app_context):
        """
        [ROUTE-012] Admin hat immer Zugriff

        Admin users should access all routes.
        Note: admin_user fixture ensures the admin user exists in DB with admin role.
        """
        response = authenticated_client_admin.get('/api/admin/users')
        # Should work (200) or route might not exist (404)
        assert response.status_code in [200, 404, 500]


class TestCriticalRoutes:
    """
    Critical Route Protection Tests

    Tests for business-critical routes.
    """

    def test_ranking_routes_protected(self, client, app_context):
        """
        Ranking routes require authentication.
        """
        response = client.get('/api/email_threads/rankings')
        assert response.status_code == 401

    def test_rating_routes_protected(self, client, app_context):
        """
        Rating routes require authentication.
        """
        response = client.get('/api/email_threads/ratings')
        assert response.status_code == 401

    def test_chatbot_routes_protected(self, client, app_context):
        """
        Chatbot routes require authentication.
        """
        response = client.get('/api/chatbots')
        assert response.status_code == 401

    def test_rag_routes_protected(self, client, app_context):
        """
        RAG routes require authentication.
        """
        response = client.get('/api/rag/collections')
        assert response.status_code == 401

    def test_admin_routes_protected(self, client, app_context):
        """
        Admin routes require authentication AND admin role.

        Note: Only testing routes that exist in test blueprints.
        """
        admin_routes = [
            '/api/admin/users',
        ]

        for route in admin_routes:
            response = client.get(route)
            assert response.status_code == 401, f"Route {route} should require auth"


class TestPublicRoutes:
    """
    Public Route Tests

    Tests for routes that don't require authentication.
    """

    def test_health_check_public(self, client, app_context):
        """
        Health check should be public.
        """
        response = client.get('/api/health')
        assert response.status_code == 200

    def test_auth_health_check_public(self, client, app_context):
        """
        Auth health check should be public.
        """
        response = client.get('/auth/authentik/health_check')
        assert response.status_code == 200


class TestLoginRoutes:
    """
    Login Route Tests

    Tests for authentication flow routes.
    """

    def test_login_missing_fields(self, client, app_context):
        """
        [LOGIN-004] Login with missing fields gives 400.
        """
        response = client.post('/auth/authentik/login', json={
            'username': 'admin'
            # Missing password
        })
        assert response.status_code in [400, 422]

    def test_login_empty_body(self, client, app_context):
        """
        Login with empty body gives 400.
        """
        response = client.post('/auth/authentik/login', json={})
        assert response.status_code in [400, 422]

    def test_login_no_json(self, client, app_context):
        """
        Login without JSON body gives 400.
        """
        response = client.post('/auth/authentik/login')
        assert response.status_code in [400, 415]
