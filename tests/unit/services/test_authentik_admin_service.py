"""
Unit tests for AuthentikAdminService.

Tests user management operations via the Authentik Admin API.
All HTTP calls to Authentik are mocked.
"""

import pytest
import time
from unittest.mock import patch, MagicMock, PropertyMock


class MockResponse:
    """Helper class for mocking requests.Response objects."""

    def __init__(self, json_data=None, status_code=200, text=''):
        self._json_data = json_data or {}
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._json_data


@pytest.fixture(autouse=True)
def reset_authentik_state():
    """Reset class-level state between tests."""
    from services.authentik_admin_service import AuthentikAdminService

    AuthentikAdminService._token = None
    AuthentikAdminService._token_expires = 0
    AuthentikAdminService._session = None
    yield
    AuthentikAdminService._token = None
    AuthentikAdminService._token_expires = 0
    AuthentikAdminService._session = None


class TestGetConfig:
    """Tests for configuration retrieval."""

    def test_AUTH_ADM_001_get_config_defaults(self):
        """[AUTH_ADM-001] Should return default config from environment."""
        from services.authentik_admin_service import AuthentikAdminService

        config = AuthentikAdminService._get_config()

        assert 'base_url' in config
        assert 'api_token' in config
        assert 'admin_email' in config
        assert 'admin_password' in config


class TestGetAdminToken:
    """Tests for admin token acquisition."""

    @patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': 'test-static-token'})
    def test_AUTH_ADM_002_get_token_from_env(self):
        """[AUTH_ADM-002] Should use static API token when available."""
        from services.authentik_admin_service import AuthentikAdminService

        token = AuthentikAdminService._get_admin_token()
        assert token == 'test-static-token'

    @patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': ''})
    def test_AUTH_ADM_003_get_token_cached(self):
        """[AUTH_ADM-003] Should return cached token when still valid."""
        from services.authentik_admin_service import AuthentikAdminService

        AuthentikAdminService._token = 'cached-token'
        AuthentikAdminService._token_expires = time.time() + 3600

        token = AuthentikAdminService._get_admin_token()
        assert token == 'cached-token'

    @patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': ''})
    @patch('services.authentik_admin_service.requests.Session')
    def test_AUTH_ADM_004_get_token_via_flow(self, mock_session_class):
        """[AUTH_ADM-004] Should obtain token via authentication flow."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Stage 1: identification
        mock_session.get.return_value = MockResponse(
            {'component': 'ak-stage-identification'}, 200
        )
        # Stage 2: password, then redirect
        mock_session.post.side_effect = [
            MockResponse({'component': 'ak-stage-password'}, 200),
            MockResponse({'type': 'redirect', 'to': '/'}, 200),
            MockResponse({'key': 'new-api-token'}, 201),  # token creation
        ]

        token = AuthentikAdminService._get_admin_token()
        assert token == 'new-api-token'

    @patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': ''})
    @patch('services.authentik_admin_service.requests.Session')
    def test_AUTH_ADM_005_get_token_flow_failure(self, mock_session_class):
        """[AUTH_ADM-005] Should return None when flow fails."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = MockResponse({}, 500)

        token = AuthentikAdminService._get_admin_token()
        assert token is None

    @patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': ''})
    @patch('services.authentik_admin_service.requests.Session')
    def test_AUTH_ADM_006_get_token_connection_error(self, mock_session_class):
        """[AUTH_ADM-006] Should return None on connection error."""
        import requests
        from services.authentik_admin_service import AuthentikAdminService

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = requests.exceptions.ConnectionError("refused")

        token = AuthentikAdminService._get_admin_token()
        assert token is None


class TestGetAuthHeaders:
    """Tests for authentication header generation."""

    @patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': 'bearer-token'})
    def test_AUTH_ADM_007_auth_headers_bearer(self):
        """[AUTH_ADM-007] Should return Bearer auth headers."""
        from services.authentik_admin_service import AuthentikAdminService

        headers = AuthentikAdminService._get_auth_headers()
        assert headers['Authorization'] == 'Bearer bearer-token'

    @patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': ''})
    def test_AUTH_ADM_008_auth_headers_no_token(self):
        """[AUTH_ADM-008] Should return headers without Authorization when no token."""
        from services.authentik_admin_service import AuthentikAdminService

        # Ensure no cached token
        AuthentikAdminService._token = None
        AuthentikAdminService._token_expires = 0

        with patch.object(AuthentikAdminService, '_get_admin_token', return_value=None):
            headers = AuthentikAdminService._get_auth_headers()
            assert 'Authorization' not in headers


class TestCreateUser:
    """Tests for user creation in Authentik."""

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_009_create_user_success(self, mock_request, mock_token):
        """[AUTH_ADM-009] Should create a user successfully."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.side_effect = [
            MockResponse({'results': []}, 200),  # check existing
            MockResponse({'pk': 123, 'username': 'newuser'}, 201),  # create
            MockResponse({}, 204),  # set password
        ]

        success, error, user_data = AuthentikAdminService.create_user(
            username='newuser',
            email='new@test.com',
            password='secret123',
            name='New User',
        )

        assert success is True
        assert error is None
        assert user_data is not None
        assert user_data['username'] == 'newuser'

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_010_create_user_already_exists(self, mock_request, mock_token):
        """[AUTH_ADM-010] Should fail when user already exists."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.return_value = MockResponse(
            {'results': [{'username': 'existing', 'pk': 1}]}, 200
        )

        success, error, user_data = AuthentikAdminService.create_user(
            username='existing', email='e@test.com', password='pass',
        )

        assert success is False
        assert 'already exists' in error

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value=None,
    )
    def test_AUTH_ADM_011_create_user_no_token(self, mock_token):
        """[AUTH_ADM-011] Should fail when no auth token available."""
        from services.authentik_admin_service import AuthentikAdminService

        success, error, user_data = AuthentikAdminService.create_user(
            username='newuser', email='new@test.com', password='pass',
        )

        assert success is False
        assert 'authenticate' in error.lower()
        assert user_data is None

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_012_create_user_api_error(self, mock_request, mock_token):
        """[AUTH_ADM-012] Should handle API errors during creation."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.side_effect = [
            MockResponse({'results': []}, 200),  # check existing
            MockResponse({'detail': 'Internal error'}, 500),  # create fails
        ]

        success, error, user_data = AuthentikAdminService.create_user(
            username='failuser', email='f@test.com', password='pass',
        )

        assert success is False
        assert user_data is None

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_013_create_user_password_fail(self, mock_request, mock_token):
        """[AUTH_ADM-013] Should report partial success when password setting fails."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.side_effect = [
            MockResponse({'results': []}, 200),
            MockResponse({'pk': 456, 'username': 'pwuser'}, 201),
            MockResponse({}, 500),  # password fails
        ]

        success, error, user_data = AuthentikAdminService.create_user(
            username='pwuser', email='pw@test.com', password='pass',
        )

        assert success is True
        assert 'password could not be set' in error

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_014_create_user_connection_error(self, mock_request, mock_token):
        """[AUTH_ADM-014] Should handle connection errors."""
        import requests
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.side_effect = requests.exceptions.ConnectionError("refused")

        success, error, user_data = AuthentikAdminService.create_user(
            username='nope', email='n@test.com', password='pass',
        )

        assert success is False
        assert 'Connection error' in error


class TestUpdateUserStatus:
    """Tests for updating user active status."""

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_015_update_user_status_success(self, mock_request, mock_token):
        """[AUTH_ADM-015] Should update user status successfully."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.side_effect = [
            MockResponse({'results': [{'username': 'testuser', 'pk': 100}]}, 200),
            MockResponse({}, 200),
        ]

        success, error = AuthentikAdminService.update_user_status('testuser', False)

        assert success is True
        assert error is None

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_016_update_user_not_found(self, mock_request, mock_token):
        """[AUTH_ADM-016] Should fail when user not found."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.return_value = MockResponse({'results': []}, 200)

        success, error = AuthentikAdminService.update_user_status('ghost', True)

        assert success is False
        assert 'not found' in error

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value=None,
    )
    def test_AUTH_ADM_017_update_user_no_token(self, mock_token):
        """[AUTH_ADM-017] Should fail when no auth token available."""
        from services.authentik_admin_service import AuthentikAdminService

        success, error = AuthentikAdminService.update_user_status('any', True)
        assert success is False


class TestSendRecoveryEmail:
    """Tests for sending password recovery emails."""

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_018_send_recovery_success(self, mock_request, mock_token):
        """[AUTH_ADM-018] Should send recovery email successfully."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.side_effect = [
            MockResponse({'results': [{'username': 'user1', 'pk': 10}]}, 200),
            MockResponse({'results': [{'pk': 'stage-pk', 'name': 'recovery-email'}]}, 200),
            MockResponse({}, 200),
        ]

        success, error = AuthentikAdminService.send_recovery_email('user1')

        assert success is True
        assert error is None

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_019_send_recovery_user_not_found(self, mock_request, mock_token):
        """[AUTH_ADM-019] Should fail when user not found."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.return_value = MockResponse({'results': []}, 200)

        success, error = AuthentikAdminService.send_recovery_email('ghost')

        assert success is False
        assert 'not found' in error

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_make_request',
    )
    def test_AUTH_ADM_020_send_recovery_no_email_stage(self, mock_request, mock_token):
        """[AUTH_ADM-020] Should fail when no email stage configured."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_request.side_effect = [
            MockResponse({'results': [{'username': 'user1', 'pk': 10}]}, 200),
            MockResponse({'results': []}, 200),  # no email stages
        ]

        success, error = AuthentikAdminService.send_recovery_email('user1')

        assert success is False
        assert 'email stage' in error.lower()

    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value=None,
    )
    def test_AUTH_ADM_021_send_recovery_no_token(self, mock_token):
        """[AUTH_ADM-021] Should fail when no auth token available."""
        from services.authentik_admin_service import AuthentikAdminService

        success, error = AuthentikAdminService.send_recovery_email('any')
        assert success is False


class TestCheckConnection:
    """Tests for Authentik connectivity checks."""

    @patch('services.authentik_admin_service.requests.get')
    @patch.object(
        __import__('services.authentik_admin_service', fromlist=['AuthentikAdminService']).AuthentikAdminService,
        '_get_admin_token',
        return_value='test-token',
    )
    def test_AUTH_ADM_022_check_connection_success(self, mock_token, mock_get):
        """[AUTH_ADM-022] Should report healthy connection."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_get.return_value = MockResponse({}, 200)

        success, error = AuthentikAdminService.check_connection()

        assert success is True
        assert error is None

    @patch('services.authentik_admin_service.requests.get')
    def test_AUTH_ADM_023_check_connection_health_fail(self, mock_get):
        """[AUTH_ADM-023] Should fail when health check fails."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_get.return_value = MockResponse({}, 503)

        success, error = AuthentikAdminService.check_connection()

        assert success is False
        assert 'health check' in error.lower()

    @patch('services.authentik_admin_service.requests.get')
    def test_AUTH_ADM_024_check_connection_error(self, mock_get):
        """[AUTH_ADM-024] Should handle connection errors."""
        import requests
        from services.authentik_admin_service import AuthentikAdminService

        mock_get.side_effect = requests.exceptions.ConnectionError("refused")

        success, error = AuthentikAdminService.check_connection()

        assert success is False
        assert 'Connection error' in error


class TestMakeRequest:
    """Tests for the _make_request helper method."""

    @patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': 'api-token'})
    @patch('services.authentik_admin_service.requests.get')
    def test_AUTH_ADM_025_make_request_token_auth(self, mock_get):
        """[AUTH_ADM-025] Should use token-based auth for requests."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_get.return_value = MockResponse({'data': 'test'}, 200)

        response = AuthentikAdminService._make_request('GET', 'http://test/api/v3/test')

        assert mock_get.called
        call_kwargs = mock_get.call_args
        assert 'Bearer api-token' in str(call_kwargs)

    def test_AUTH_ADM_026_make_request_session_auth(self):
        """[AUTH_ADM-026] Should use session-based auth when token is SESSION_AUTH."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_session = MagicMock()
        mock_session.get.return_value = MockResponse({'data': 'test'}, 200)

        AuthentikAdminService._token = 'SESSION_AUTH'
        AuthentikAdminService._token_expires = time.time() + 3600
        AuthentikAdminService._session = mock_session

        with patch.dict('os.environ', {'AUTHENTIK_API_TOKEN': ''}):
            response = AuthentikAdminService._make_request('GET', 'http://test/api')

        assert mock_session.get.called
