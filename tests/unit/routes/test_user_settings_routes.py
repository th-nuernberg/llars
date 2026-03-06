"""
Route Tests for User Settings API
===================================

Tests for app/routes/user_settings/settings_routes.py and
app/routes/user_settings/user_provider_routes.py.

Covers: Settings CRUD, avatar management, provider CRUD, provider sharing.

Uses real blueprints with mocked OIDC token validation.
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Get Settings
# ---------------------------------------------------------------------------

class TestGetSettings:
    """Tests for GET /api/user/settings"""

    def test_ROUTE_USETTINGS_GET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/user/settings')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_GET_002_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/user/settings')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'settings' in data
            assert 'collab_color' in data['settings']
            assert 'avatar_seed' in data['settings']
            assert 'preferences' in data['settings']

    def test_ROUTE_USETTINGS_GET_003_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/user/settings')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Update Settings
# ---------------------------------------------------------------------------

class TestUpdateSettings:
    """Tests for PUT /api/user/settings"""

    def test_ROUTE_USETTINGS_UPDATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/user/settings',
                               json={'collab_color': '#FF0000'})
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_UPDATE_002_collab_color(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/user/settings',
                                      json={'collab_color': '#FF5733'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['settings']['collab_color'] == '#FF5733'

    def test_ROUTE_USETTINGS_UPDATE_003_invalid_color(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/user/settings',
                                      json={'collab_color': 'not-a-color'})
            assert response.status_code == 400

    def test_ROUTE_USETTINGS_UPDATE_004_avatar_seed(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/user/settings',
                                      json={'avatar_seed': 'new-seed-42'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['settings']['avatar_seed'] == 'new-seed-42'

    def test_ROUTE_USETTINGS_UPDATE_005_preferences(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/user/settings',
                                      json={'preferences': {'theme': 'dark', 'language': 'de'}})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['settings']['preferences']['theme'] == 'dark'

    def test_ROUTE_USETTINGS_UPDATE_006_empty_body(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/user/settings', json={})
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# Upload Avatar
# ---------------------------------------------------------------------------

class TestUploadAvatar:
    """Tests for POST /api/user/settings/avatar"""

    def test_ROUTE_USETTINGS_AVATAR_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/user/settings/avatar')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_AVATAR_002_no_file(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/user/settings/avatar')
            assert response.status_code == 400

    def test_ROUTE_USETTINGS_AVATAR_003_invalid_file_type(self, auth_admin, real_app):
        import io
        with real_app.app_context():
            data = {
                'avatar': (io.BytesIO(b'not an image'), 'test.exe')
            }
            response = auth_admin.post('/api/user/settings/avatar',
                                       data=data,
                                       content_type='multipart/form-data')
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# Delete Avatar
# ---------------------------------------------------------------------------

class TestDeleteAvatar:
    """Tests for DELETE /api/user/settings/avatar"""

    def test_ROUTE_USETTINGS_AVATAR_DEL_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/user/settings/avatar')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_AVATAR_DEL_002_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.delete('/api/user/settings/avatar')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Get Avatar (public)
# ---------------------------------------------------------------------------

class TestGetAvatar:
    """Tests for GET /api/user/settings/avatar/<public_id>"""

    def test_ROUTE_USETTINGS_AVATAR_PUB_001_not_found(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/user/settings/avatar/nonexistent1234')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Provider Types
# ---------------------------------------------------------------------------

class TestProviderTypes:
    """Tests for GET /api/user/providers/types"""

    def test_ROUTE_USETTINGS_PTYPES_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/user/providers/types')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_PTYPES_002_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/user/providers/types')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['types'], list)
            type_ids = [t['id'] for t in data['types']]
            assert 'openai' in type_ids
            assert 'anthropic' in type_ids
            assert 'ollama' in type_ids


# ---------------------------------------------------------------------------
# List Providers
# ---------------------------------------------------------------------------

class TestListProviders:
    """Tests for GET /api/user/providers"""

    def test_ROUTE_USETTINGS_PLIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/user/providers')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_PLIST_002_empty(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/user/providers')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['providers'], list)


# ---------------------------------------------------------------------------
# List Available Providers
# ---------------------------------------------------------------------------

class TestListAvailableProviders:
    """Tests for GET /api/user/providers/available"""

    def test_ROUTE_USETTINGS_PAVAIL_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/user/providers/available')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_PAVAIL_002_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/user/providers/available')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['providers'], list)


# ---------------------------------------------------------------------------
# Create Provider
# ---------------------------------------------------------------------------

class TestCreateProvider:
    """Tests for POST /api/user/providers"""

    def test_ROUTE_USETTINGS_PCREATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/user/providers',
                                json={'provider_type': 'openai', 'name': 'My Key'})
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_PCREATE_002_missing_type(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/user/providers',
                                       json={'name': 'My Key'})
            assert response.status_code == 400

    def test_ROUTE_USETTINGS_PCREATE_003_missing_name(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/user/providers',
                                       json={'provider_type': 'openai'})
            assert response.status_code == 400

    def test_ROUTE_USETTINGS_PCREATE_004_invalid_type(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/user/providers',
                                       json={'provider_type': 'invalid_xyz', 'name': 'Test'})
            assert response.status_code == 400

    def test_ROUTE_USETTINGS_PCREATE_005_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/user/providers', json={
                'provider_type': 'openai',
                'name': 'My OpenAI Key',
                'api_key': 'sk-test123',
                'base_url': 'https://api.openai.com/v1'
            })
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['provider']['name'] == 'My OpenAI Key'


# ---------------------------------------------------------------------------
# Get Provider
# ---------------------------------------------------------------------------

class TestGetProvider:
    """Tests for GET /api/user/providers/<id>"""

    def test_ROUTE_USETTINGS_PGET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/user/providers/1')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_PGET_002_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/user/providers/99999')
            assert response.status_code == 404

    def test_ROUTE_USETTINGS_PGET_003_success(self, auth_admin, real_app):
        with real_app.app_context():
            # Create first
            create_resp = auth_admin.post('/api/user/providers', json={
                'provider_type': 'ollama',
                'name': 'Local Ollama',
                'base_url': 'http://localhost:11434'
            })
            provider_id = create_resp.get_json()['provider']['id']

            response = auth_admin.get(f'/api/user/providers/{provider_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['provider']['name'] == 'Local Ollama'


# ---------------------------------------------------------------------------
# Update Provider
# ---------------------------------------------------------------------------

class TestUpdateProvider:
    """Tests for PUT /api/user/providers/<id>"""

    def test_ROUTE_USETTINGS_PUPDATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/user/providers/1', json={'name': 'New Name'})
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_PUPDATE_002_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/user/providers/99999',
                                      json={'name': 'New Name'})
            assert response.status_code == 404

    def test_ROUTE_USETTINGS_PUPDATE_003_success(self, auth_admin, real_app):
        with real_app.app_context():
            create_resp = auth_admin.post('/api/user/providers', json={
                'provider_type': 'openai',
                'name': 'Update Me',
                'api_key': 'sk-old'
            })
            provider_id = create_resp.get_json()['provider']['id']

            response = auth_admin.put(f'/api/user/providers/{provider_id}',
                                       json={'name': 'Updated Name'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['provider']['name'] == 'Updated Name'


# ---------------------------------------------------------------------------
# Delete Provider
# ---------------------------------------------------------------------------

class TestDeleteProvider:
    """Tests for DELETE /api/user/providers/<id>"""

    def test_ROUTE_USETTINGS_PDELETE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/user/providers/1')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_PDELETE_002_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.delete('/api/user/providers/99999')
            assert response.status_code == 404

    def test_ROUTE_USETTINGS_PDELETE_003_success(self, auth_admin, real_app):
        with real_app.app_context():
            create_resp = auth_admin.post('/api/user/providers', json={
                'provider_type': 'openai',
                'name': 'Delete Me',
                'api_key': 'sk-delete'
            })
            provider_id = create_resp.get_json()['provider']['id']

            response = auth_admin.delete(f'/api/user/providers/{provider_id}')
            assert response.status_code == 200
            assert response.get_json()['success'] is True

            # Verify deleted
            get_resp = auth_admin.get(f'/api/user/providers/{provider_id}')
            assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Admin List All Providers
# ---------------------------------------------------------------------------

class TestAdminListAllProviders:
    """Tests for GET /api/user/providers/admin/all"""

    def test_ROUTE_USETTINGS_PADMIN_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/user/providers/admin/all')
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_PADMIN_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/user/providers/admin/all')
            assert response.status_code == 403

    def test_ROUTE_USETTINGS_PADMIN_003_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/user/providers/admin/all')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['providers'], list)


# ---------------------------------------------------------------------------
# Share-All Toggle
# ---------------------------------------------------------------------------

class TestToggleShareAll:
    """Tests for POST /api/user/providers/<id>/share-all"""

    def test_ROUTE_USETTINGS_SHAREALL_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/user/providers/1/share-all',
                                json={'share_with_all': True})
        assert response.status_code == 401

    def test_ROUTE_USETTINGS_SHAREALL_002_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/user/providers/99999/share-all',
                                       json={'share_with_all': True})
            assert response.status_code == 404

    def test_ROUTE_USETTINGS_SHAREALL_003_success(self, auth_admin, real_app):
        with real_app.app_context():
            create_resp = auth_admin.post('/api/user/providers', json={
                'provider_type': 'openai',
                'name': 'Share All Test',
                'api_key': 'sk-share'
            })
            provider_id = create_resp.get_json()['provider']['id']

            response = auth_admin.post(f'/api/user/providers/{provider_id}/share-all',
                                        json={'share_with_all': True})
            assert response.status_code == 200
            assert response.get_json()['success'] is True
