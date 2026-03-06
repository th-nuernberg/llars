"""
Route Tests for Users API (Admin + Self-Service)
===================================================

Tests for app/routes/users/ (user_admin_routes.py, user_settings_routes.py).
Covers: Admin user management (CRUD), user self-service settings,
        avatar management, RBAC enforcement.

Uses real blueprints with mocked OIDC token validation.
Prefix: ROUTE_USERS
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# GET /api/admin/users (Admin list users)
# ---------------------------------------------------------------------------

class TestAdminListUsers:
    """Tests for GET /api/admin/users"""

    def test_ROUTE_USERS_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/admin/users')
        assert response.status_code == 401

    def test_ROUTE_USERS_LIST_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/admin/users')
            assert response.status_code == 403

    def test_ROUTE_USERS_LIST_003_forbidden_researcher(self, auth_researcher, real_app):
        with real_app.app_context():
            response = auth_researcher.get('/api/admin/users')
            assert response.status_code == 403

    def test_ROUTE_USERS_LIST_004_admin_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/users')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'users' in data
            assert isinstance(data['users'], list)
            # At least the admin user should be in the list
            usernames = [u['username'] for u in data['users']]
            assert 'admin' in usernames

    def test_ROUTE_USERS_LIST_005_with_search_query(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/users?q=admin')
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['users']) >= 1

    def test_ROUTE_USERS_LIST_006_no_results(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/admin/users?q=nonexistent_user_xyz')
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['users']) == 0


# ---------------------------------------------------------------------------
# POST /api/admin/users (Admin create user)
# ---------------------------------------------------------------------------

class TestAdminCreateUser:
    """Tests for POST /api/admin/users"""

    def test_ROUTE_USERS_CREATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/admin/users',
                                json={'username': 'newuser'})
        assert response.status_code == 401

    def test_ROUTE_USERS_CREATE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/admin/users',
                                       json={'username': 'newuser'})
            assert response.status_code == 403

    def test_ROUTE_USERS_CREATE_003_missing_username(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/admin/users', json={})
            assert response.status_code == 400

    def test_ROUTE_USERS_CREATE_004_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/admin/users', json={
                'username': 'newuser',
                'first_name': 'New',
                'last_name': 'User',
                'create_in_authentik': False,
            })
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['user']['username'] == 'newuser'

    def test_ROUTE_USERS_CREATE_005_duplicate_user(self, auth_admin, real_app):
        with real_app.app_context():
            # First creation
            auth_admin.post('/api/admin/users', json={
                'username': 'dupuser',
                'create_in_authentik': False,
            })
            # Duplicate
            response = auth_admin.post('/api/admin/users', json={
                'username': 'dupuser',
                'create_in_authentik': False,
            })
            assert response.status_code == 409

    def test_ROUTE_USERS_CREATE_006_with_roles(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/admin/users', json={
                'username': 'roleuser',
                'role_names': ['evaluator'],
                'create_in_authentik': False,
            })
            assert response.status_code == 201
            data = response.get_json()
            assert any(r['role_name'] == 'evaluator' for r in data['user']['roles'])

    def test_ROUTE_USERS_CREATE_007_invalid_collab_color(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/admin/users', json={
                'username': 'coloruser',
                'collab_color': 'not-a-color',
                'create_in_authentik': False,
            })
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# PATCH /api/admin/users/<username> (Admin update user)
# ---------------------------------------------------------------------------

class TestAdminUpdateUser:
    """Tests for PATCH /api/admin/users/<username>"""

    def test_ROUTE_USERS_UPDATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.patch('/api/admin/users/someuser',
                                 json={'is_active': False})
        assert response.status_code == 401

    def test_ROUTE_USERS_UPDATE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.patch('/api/admin/users/admin',
                                        json={'is_active': False})
            assert response.status_code == 403

    def test_ROUTE_USERS_UPDATE_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/users/nonexistent',
                                         json={'is_active': False})
            assert response.status_code == 404

    def test_ROUTE_USERS_UPDATE_004_cannot_modify_admin(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/users/admin',
                                         json={'is_active': False})
            assert response.status_code == 403

    def test_ROUTE_USERS_UPDATE_005_success(self, auth_admin, real_app):
        with real_app.app_context():
            # Create a user to update
            auth_admin.post('/api/admin/users', json={
                'username': 'updateuser',
                'create_in_authentik': False,
            })
            response = auth_admin.patch('/api/admin/users/updateuser',
                                         json={'first_name': 'Updated'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_ROUTE_USERS_UPDATE_006_lock_user(self, auth_admin, real_app):
        with real_app.app_context():
            auth_admin.post('/api/admin/users', json={
                'username': 'lockme',
                'create_in_authentik': False,
            })
            response = auth_admin.patch('/api/admin/users/lockme',
                                         json={'is_active': False})
            assert response.status_code == 200
            data = response.get_json()
            assert data['user']['is_active'] is False


# ---------------------------------------------------------------------------
# DELETE /api/admin/users/<username> (Admin delete user)
# ---------------------------------------------------------------------------

class TestAdminDeleteUser:
    """Tests for DELETE /api/admin/users/<username>"""

    def test_ROUTE_USERS_DEL_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/admin/users/someuser')
        assert response.status_code == 401

    def test_ROUTE_USERS_DEL_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.delete('/api/admin/users/someuser')
            assert response.status_code == 403

    def test_ROUTE_USERS_DEL_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.delete('/api/admin/users/nonexistent')
            assert response.status_code == 404

    def test_ROUTE_USERS_DEL_004_cannot_delete_admin(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.delete('/api/admin/users/admin')
            assert response.status_code == 403

    def test_ROUTE_USERS_DEL_005_cannot_delete_self(self, auth_admin, real_app):
        """Admin cannot delete their own account."""
        with real_app.app_context():
            response = auth_admin.delete('/api/admin/users/admin')
            assert response.status_code == 403

    def test_ROUTE_USERS_DEL_006_success(self, auth_admin, real_app):
        with real_app.app_context():
            auth_admin.post('/api/admin/users', json={
                'username': 'deleteme',
                'create_in_authentik': False,
            })
            response = auth_admin.delete('/api/admin/users/deleteme')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# PATCH /api/admin/users/<username>/console-logs (Toggle console logs)
# ---------------------------------------------------------------------------

class TestToggleConsoleLogs:
    """Tests for PATCH /api/admin/users/<username>/console-logs"""

    def test_ROUTE_USERS_CONSOLE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.patch('/api/admin/users/admin/console-logs',
                                 json={'enabled': True})
        assert response.status_code == 401

    def test_ROUTE_USERS_CONSOLE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.patch('/api/admin/users/admin/console-logs',
                                        json={'enabled': True})
            assert response.status_code == 403

    def test_ROUTE_USERS_CONSOLE_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/admin/users/nonexistent/console-logs',
                                         json={'enabled': True})
            assert response.status_code == 404

    def test_ROUTE_USERS_CONSOLE_004_enable(self, auth_admin, real_app):
        with real_app.app_context():
            auth_admin.post('/api/admin/users', json={
                'username': 'consoleuser',
                'create_in_authentik': False,
            })
            response = auth_admin.patch('/api/admin/users/consoleuser/console-logs',
                                         json={'enabled': True})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['user']['console_logs_enabled'] is True


# ---------------------------------------------------------------------------
# GET /api/users/me/settings (Self-service settings)
# ---------------------------------------------------------------------------

class TestGetUserSelfSettings:
    """Tests for GET /api/users/me/settings"""

    def test_ROUTE_USERS_SELFGET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/users/me/settings')
        assert response.status_code == 401

    def test_ROUTE_USERS_SELFGET_002_admin_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/users/me/settings')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'collab_color' in data
            assert 'avatar_url' in data

    def test_ROUTE_USERS_SELFGET_003_evaluator_success(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/users/me/settings')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# PATCH /api/users/me/settings (Update own settings)
# ---------------------------------------------------------------------------

class TestUpdateUserSelfSettings:
    """Tests for PATCH /api/users/me/settings"""

    def test_ROUTE_USERS_SELFPATCH_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.patch('/api/users/me/settings',
                                 json={'collab_color': '#FF0000'})
        assert response.status_code == 401

    def test_ROUTE_USERS_SELFPATCH_002_valid_color(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/users/me/settings',
                                         json={'collab_color': '#FF5733'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['collab_color'] == '#FF5733'

    def test_ROUTE_USERS_SELFPATCH_003_invalid_color(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/users/me/settings',
                                         json={'collab_color': 'not-hex'})
            assert response.status_code == 400

    def test_ROUTE_USERS_SELFPATCH_004_empty_color_picks_random(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/users/me/settings',
                                         json={'collab_color': ''})
            assert response.status_code == 200
            data = response.get_json()
            # Should have gotten a random color
            assert data['collab_color'] is not None
            assert data['collab_color'].startswith('#')


# ---------------------------------------------------------------------------
# PATCH /api/users/me/avatar (Regenerate avatar)
# ---------------------------------------------------------------------------

class TestRegenerateAvatar:
    """Tests for PATCH /api/users/me/avatar"""

    def test_ROUTE_USERS_AVATAR_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.patch('/api/users/me/avatar', json={})
        assert response.status_code == 401

    def test_ROUTE_USERS_AVATAR_002_regenerate(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/users/me/avatar', json={})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'avatar_seed' in data

    def test_ROUTE_USERS_AVATAR_003_custom_seed(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/users/me/avatar',
                                         json={'avatar_seed': 'customseed'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['avatar_seed'] == 'customseed'

    def test_ROUTE_USERS_AVATAR_004_seed_too_long(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.patch('/api/users/me/avatar',
                                         json={'avatar_seed': 'a' * 33})
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /api/users/me/avatar (Reset avatar)
# ---------------------------------------------------------------------------

class TestResetAvatar:
    """Tests for DELETE /api/users/me/avatar"""

    def test_ROUTE_USERS_RSTAVA_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/users/me/avatar')
        assert response.status_code == 401

    def test_ROUTE_USERS_RSTAVA_002_no_custom_avatar(self, auth_admin, real_app):
        """Reset when no custom avatar is set should return success."""
        with real_app.app_context():
            response = auth_admin.delete('/api/users/me/avatar')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# GET /api/users/avatar/<avatar_id> (Public avatar)
# ---------------------------------------------------------------------------

class TestGetPublicAvatar:
    """Tests for GET /api/users/avatar/<avatar_id> (public endpoint)"""

    def test_ROUTE_USERS_PUBAVA_001_not_found(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/users/avatar/nonexistent')
        assert response.status_code == 404
