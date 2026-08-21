"""
Route Tests for Prompt Engineering API
========================================

Tests for app/routes/prompts/prompt_routes.py (1170 lines).
Covers: CRUD operations, sharing/unsharing, templates, commits, download.

Uses real blueprints with mocked OIDC token validation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Create Prompt
# ---------------------------------------------------------------------------

class TestCreatePrompt:
    """Tests for POST /api/prompts"""

    def test_PROMPT_CREATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/prompts',
                                json={'name': 'Test', 'content': 'Hello'})
        assert response.status_code == 401

    def test_PROMPT_CREATE_002_missing_name(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/prompts',
                                      json={'content': 'Hello'})
            assert response.status_code == 400

    def test_PROMPT_CREATE_003_missing_content(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/prompts',
                                      json={'name': 'Test'})
            assert response.status_code == 400

    def test_PROMPT_CREATE_004_success(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/prompts', json={
                'name': 'My Prompt',
                'content': 'Summarize the following: {{text}}'
            })
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['data']['name'] == 'My Prompt'
            assert 'id' in data['data']

    def test_PROMPT_CREATE_005_duplicate_name(self, auth_user, real_app):
        with real_app.app_context():
            # Create first
            auth_user.post('/api/prompts', json={
                'name': 'Unique Name',
                'content': 'Content 1'
            })
            # Attempt duplicate
            response = auth_user.post('/api/prompts', json={
                'name': 'Unique Name',
                'content': 'Content 2'
            })
            assert response.status_code == 409


# ---------------------------------------------------------------------------
# List Prompts
# ---------------------------------------------------------------------------

class TestListPrompts:
    """Tests for GET /api/prompts"""

    def test_PROMPT_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/prompts')
        assert response.status_code == 401

    def test_PROMPT_LIST_002_empty(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/prompts')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['data'], list)

    def test_PROMPT_LIST_003_returns_own_prompts(self, auth_user, real_app):
        with real_app.app_context():
            # Create a prompt
            auth_user.post('/api/prompts', json={
                'name': 'Listed Prompt',
                'content': 'Content here'
            })

            response = auth_user.get('/api/prompts')
            assert response.status_code == 200
            data = response.get_json()
            names = [p['name'] for p in data['data']]
            assert 'Listed Prompt' in names


# ---------------------------------------------------------------------------
# Get Single Prompt
# ---------------------------------------------------------------------------

class TestGetPrompt:
    """Tests for GET /api/prompts/<id>"""

    def test_PROMPT_GET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/prompts/1')
        assert response.status_code == 401

    def test_PROMPT_GET_002_not_found(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/prompts/99999')
            assert response.status_code == 404

    def test_PROMPT_GET_003_own_prompt(self, auth_user, real_app):
        with real_app.app_context():
            # Create a prompt
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Get Test',
                'content': 'Get content'
            })
            prompt_id = create_resp.get_json()['data']['id']

            response = auth_user.get(f'/api/prompts/{prompt_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['data']['name'] == 'Get Test'


# ---------------------------------------------------------------------------
# Update Prompt
# ---------------------------------------------------------------------------

class TestUpdatePrompt:
    """Tests for PUT /api/prompts/<id>"""

    def test_PROMPT_UPDATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/prompts/1',
                               json={'content': {'blocks': []}})
        assert response.status_code == 401

    def test_PROMPT_UPDATE_002_not_found(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.put('/api/prompts/99999',
                                     json={'content': {'blocks': []}})
            assert response.status_code == 404

    def test_PROMPT_UPDATE_003_invalid_content(self, auth_user, real_app):
        with real_app.app_context():
            # Create a prompt
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Update Invalid',
                'content': 'Old content'
            })
            prompt_id = create_resp.get_json()['data']['id']

            # Update with non-dict content (should fail validation)
            response = auth_user.put(f'/api/prompts/{prompt_id}',
                                     json={'content': 'just a string'})
            assert response.status_code == 400

    def test_PROMPT_UPDATE_004_success(self, auth_user, real_app):
        with real_app.app_context():
            # Create a prompt
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Update Me',
                'content': 'Old content'
            })
            prompt_id = create_resp.get_json()['data']['id']

            response = auth_user.put(f'/api/prompts/{prompt_id}',
                                     json={'content': {'blocks': [{'text': 'new'}]}})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Delete Prompt
# ---------------------------------------------------------------------------

class TestDeletePrompt:
    """Tests for DELETE /api/prompts/<id>"""

    def test_PROMPT_DELETE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/prompts/1')
        assert response.status_code == 401

    def test_PROMPT_DELETE_002_not_found(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.delete('/api/prompts/99999')
            assert response.status_code == 404

    def test_PROMPT_DELETE_003_success(self, auth_user, real_app):
        with real_app.app_context():
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Delete Me',
                'content': 'Bye'
            })
            prompt_id = create_resp.get_json()['data']['id']

            response = auth_user.delete(f'/api/prompts/{prompt_id}')
            assert response.status_code == 200

            # Verify deleted
            get_resp = auth_user.get(f'/api/prompts/{prompt_id}')
            assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Share Prompt
# ---------------------------------------------------------------------------

class TestSharePrompt:
    """Tests for POST /api/prompts/<id>/share"""

    def test_PROMPT_SHARE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/prompts/1/share',
                                json={'shared_with': 'admin'})
        assert response.status_code == 401

    def test_PROMPT_SHARE_002_missing_username(self, auth_user, real_app):
        with real_app.app_context():
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Share Test',
                'content': 'Content'
            })
            prompt_id = create_resp.get_json()['data']['id']

            response = auth_user.post(f'/api/prompts/{prompt_id}/share',
                                      json={})
            assert response.status_code == 400

    def test_PROMPT_SHARE_003_self_share_denied(self, auth_user, real_app):
        with real_app.app_context():
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Self Share',
                'content': 'Content'
            })
            prompt_id = create_resp.get_json()['data']['id']

            response = auth_user.post(f'/api/prompts/{prompt_id}/share',
                                      json={'shared_with': 'testuser'})
            assert response.status_code == 400

    def test_PROMPT_SHARE_004_user_not_found(self, auth_user, real_app):
        with real_app.app_context():
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Share Missing',
                'content': 'Content'
            })
            prompt_id = create_resp.get_json()['data']['id']

            response = auth_user.post(f'/api/prompts/{prompt_id}/share',
                                      json={'shared_with': 'nonexistent_user'})
            assert response.status_code == 404

    def test_PROMPT_SHARE_005_success(self, auth_user, real_app, radmin):
        with real_app.app_context():
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Share Success',
                'content': 'Content'
            })
            prompt_id = create_resp.get_json()['data']['id']

            response = auth_user.post(f'/api/prompts/{prompt_id}/share',
                                      json={'shared_with': 'admin'})
            assert response.status_code == 201


# ---------------------------------------------------------------------------
# Unshare Prompt
# ---------------------------------------------------------------------------

class TestUnsharePrompt:
    """Tests for POST /api/prompts/<id>/unshare"""

    def test_PROMPT_UNSHARE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/prompts/1/unshare',
                                json={'unshare_with': 'admin'})
        assert response.status_code == 401

    def test_PROMPT_UNSHARE_002_missing_username(self, auth_user, real_app):
        with real_app.app_context():
            create_resp = auth_user.post('/api/prompts', json={
                'name': 'Unshare Test',
                'content': 'Content'
            })
            prompt_id = create_resp.get_json()['data']['id']

            response = auth_user.post(f'/api/prompts/{prompt_id}/unshare',
                                      json={})
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# Rename Prompt
# ---------------------------------------------------------------------------

class TestRenamePrompt:
    """Tests for PUT /api/prompts/<id>/rename"""

    def test_PROMPT_RENAME_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/prompts/1/rename',
                               json={'name': 'New Name'})
        assert response.status_code == 401

    def test_PROMPT_RENAME_002_not_found(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.put('/api/prompts/99999/rename',
                                     json={'name': 'New Name'})
            assert response.status_code == 404


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class TestPromptTemplates:
    """Tests for GET /api/prompts/templates"""

    def test_PROMPT_TEMPLATES_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/prompts/templates')
        assert response.status_code == 401

    def test_PROMPT_TEMPLATES_002_success(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/prompts/templates')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Shared Prompts
# ---------------------------------------------------------------------------

class TestSharedPrompts:
    """Tests for GET /api/prompts/shared"""

    def test_PROMPT_SHARED_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/prompts/shared')
        assert response.status_code == 401

    def test_PROMPT_SHARED_002_success(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/prompts/shared')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['data'], list)


# ---------------------------------------------------------------------------
# Download Prompt
# ---------------------------------------------------------------------------

class TestDownloadPrompt:
    """Tests for GET /api/prompts/<id>/download"""

    def test_PROMPT_DOWNLOAD_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/prompts/1/download')
        assert response.status_code == 401

    def test_PROMPT_DOWNLOAD_002_not_found(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/prompts/99999/download')
            assert response.status_code == 404
