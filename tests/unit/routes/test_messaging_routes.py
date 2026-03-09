"""
Route Tests for Messaging API
================================

Tests for app/routes/messaging/ (conversation_routes.py, message_routes.py,
encryption_routes.py, ai_routes.py).
Covers: Conversation CRUD, message send/edit/delete, read receipts,
        encryption keys, AI access.

Uses real blueprints with mocked OIDC token validation.
Prefix: ROUTE_MSG

NOTE: All messaging endpoints are gated by the `_check_communication_enabled`
before_request hook. The `enable_communication` fixture patches that check.
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_messaging_perms(rdb, real_app):
    """Seed communication permissions needed by messaging routes."""
    from db.models.permission import Permission, Role, RolePermission

    with real_app.app_context():
        perms_data = [
            ('feature:communication:access', 'Access Communication', 'feature'),
            ('feature:communication:chat', 'Chat Communication', 'feature'),
            ('feature:communication:ai', 'AI Communication', 'feature'),
        ]
        for perm_key, display, category in perms_data:
            perm = Permission.query.filter_by(permission_key=perm_key).first()
            if not perm:
                perm = Permission(
                    permission_key=perm_key,
                    display_name=display,
                    category=category,
                    description=display
                )
                rdb.session.add(perm)
        rdb.session.commit()

        # Grant to admin
        admin_role = Role.query.filter_by(role_name='admin').first()
        if admin_role:
            for perm_key in perms_data:
                perm = Permission.query.filter_by(permission_key=perm_key[0]).first()
                existing = RolePermission.query.filter_by(
                    role_id=admin_role.id, permission_id=perm.id
                ).first()
                if not existing:
                    rdb.session.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
        rdb.session.commit()


@pytest.fixture
def enable_communication():
    """Patch is_communication_enabled to return True for messaging tests."""
    with patch('services.system_settings_service.is_communication_enabled', return_value=True):
        yield


# ---------------------------------------------------------------------------
# Communication disabled gate
# ---------------------------------------------------------------------------

class TestCommunicationGate:
    """Tests for messaging global before_request gate."""

    def test_ROUTE_MSG_GATE_001_disabled(self, auth_admin, real_app, seed_messaging_perms):
        """All messaging endpoints return 403 when communication is disabled."""
        with real_app.app_context():
            with patch('services.system_settings_service.is_communication_enabled', return_value=False):
                response = auth_admin.get('/api/messaging/conversations')
                assert response.status_code == 403
                data = response.get_json()
                assert data['success'] is False


# ---------------------------------------------------------------------------
# GET /api/messaging/conversations (List conversations)
# ---------------------------------------------------------------------------

class TestListConversations:
    """Tests for GET /api/messaging/conversations"""

    def test_ROUTE_MSG_LISTCONV_001_unauthenticated(self, rclient, rdb, rmock_token,
                                                     enable_communication):
        response = rclient.get('/api/messaging/conversations')
        assert response.status_code in (401, 403)

    @patch('services.messaging_service.MessagingService.get_conversations')
    def test_ROUTE_MSG_LISTCONV_002_success(self, mock_get, auth_admin, real_app,
                                             seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_get.return_value = []
            response = auth_admin.get('/api/messaging/conversations')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'conversations' in data

    @patch('services.messaging_service.MessagingService.get_conversations')
    def test_ROUTE_MSG_LISTCONV_003_with_pagination(self, mock_get, auth_admin, real_app,
                                                     seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_get.return_value = []
            response = auth_admin.get('/api/messaging/conversations?limit=10&offset=5')
            assert response.status_code == 200
            mock_get.assert_called_once_with('admin', 10, 5)


# ---------------------------------------------------------------------------
# GET /api/messaging/conversations/<id> (Get conversation)
# ---------------------------------------------------------------------------

class TestGetConversation:
    """Tests for GET /api/messaging/conversations/<conversation_id>"""

    def test_ROUTE_MSG_GETCONV_001_unauthenticated(self, rclient, rdb, rmock_token,
                                                    enable_communication):
        response = rclient.get('/api/messaging/conversations/1')
        assert response.status_code in (401, 403)

    @patch('services.messaging_service.MessagingService.get_conversation')
    def test_ROUTE_MSG_GETCONV_002_not_found(self, mock_get, auth_admin, real_app,
                                              seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_get.return_value = None
            response = auth_admin.get('/api/messaging/conversations/999')
            assert response.status_code == 404

    @patch('services.messaging_service.MessagingService.get_conversation')
    def test_ROUTE_MSG_GETCONV_003_success(self, mock_get, auth_admin, real_app,
                                            seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_get.return_value = {'id': 1, 'type': 'direct', 'name': 'Test'}
            response = auth_admin.get('/api/messaging/conversations/1')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['conversation']['id'] == 1


# ---------------------------------------------------------------------------
# POST /api/messaging/conversations/direct (Create direct conversation)
# ---------------------------------------------------------------------------

class TestCreateDirectConversation:
    """Tests for POST /api/messaging/conversations/direct"""

    def test_ROUTE_MSG_DIRECT_001_unauthenticated(self, rclient, rdb, rmock_token,
                                                    enable_communication):
        response = rclient.post('/api/messaging/conversations/direct',
                                json={'username': 'other'})
        assert response.status_code in (401, 403)

    def test_ROUTE_MSG_DIRECT_002_missing_username(self, auth_admin, real_app,
                                                    seed_messaging_perms, enable_communication):
        with real_app.app_context():
            response = auth_admin.post('/api/messaging/conversations/direct', json={})
            assert response.status_code == 400

    @patch('services.messaging_service.MessagingService.create_direct_conversation')
    def test_ROUTE_MSG_DIRECT_003_success(self, mock_create, auth_admin, real_app,
                                           seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_create.return_value = {'id': 1, 'type': 'direct'}
            response = auth_admin.post('/api/messaging/conversations/direct',
                                        json={'username': 'testuser'})
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# POST /api/messaging/conversations/group (Create group conversation)
# ---------------------------------------------------------------------------

class TestCreateGroupConversation:
    """Tests for POST /api/messaging/conversations/group"""

    def test_ROUTE_MSG_GROUP_001_missing_name(self, auth_admin, real_app,
                                               seed_messaging_perms, enable_communication):
        with real_app.app_context():
            response = auth_admin.post('/api/messaging/conversations/group',
                                        json={'members': ['user1']})
            assert response.status_code == 400

    def test_ROUTE_MSG_GROUP_002_missing_members(self, auth_admin, real_app,
                                                  seed_messaging_perms, enable_communication):
        with real_app.app_context():
            response = auth_admin.post('/api/messaging/conversations/group',
                                        json={'name': 'Test Group'})
            assert response.status_code == 400

    @patch('services.messaging_service.MessagingService.create_group_conversation')
    def test_ROUTE_MSG_GROUP_003_success(self, mock_create, auth_admin, real_app,
                                          seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_create.return_value = {'id': 2, 'type': 'group', 'name': 'Test Group'}
            response = auth_admin.post('/api/messaging/conversations/group',
                                        json={'name': 'Test Group', 'members': ['user1']})
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# POST /api/messaging/conversations/<id>/messages (Send message)
# ---------------------------------------------------------------------------

class TestSendMessage:
    """Tests for POST /api/messaging/conversations/<id>/messages"""

    def test_ROUTE_MSG_SEND_001_unauthenticated(self, rclient, rdb, rmock_token,
                                                  enable_communication):
        response = rclient.post('/api/messaging/conversations/1/messages',
                                json={'content': 'hello'})
        assert response.status_code in (401, 403)

    def test_ROUTE_MSG_SEND_002_missing_content(self, auth_admin, real_app,
                                                 seed_messaging_perms, enable_communication):
        with real_app.app_context():
            response = auth_admin.post('/api/messaging/conversations/1/messages',
                                        json={})
            assert response.status_code == 400

    @patch('services.messaging_service.MessagingService.send_message')
    def test_ROUTE_MSG_SEND_003_conv_not_found(self, mock_send, auth_admin, real_app,
                                                seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_send.return_value = None
            response = auth_admin.post('/api/messaging/conversations/999/messages',
                                        json={'content': 'hello'})
            assert response.status_code == 404

    @patch('services.messaging_service.MessagingService.send_message')
    def test_ROUTE_MSG_SEND_004_success(self, mock_send, auth_admin, real_app,
                                         seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_send.return_value = {'id': 1, 'content': 'hello', 'is_encrypted': False}
            response = auth_admin.post('/api/messaging/conversations/1/messages',
                                        json={'content': 'hello'})
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['message']['content'] == 'hello'


# ---------------------------------------------------------------------------
# PUT /api/messaging/messages/<id> (Edit message)
# ---------------------------------------------------------------------------

class TestEditMessage:
    """Tests for PUT /api/messaging/messages/<message_id>"""

    def test_ROUTE_MSG_EDIT_001_missing_content(self, auth_admin, real_app,
                                                 seed_messaging_perms, enable_communication):
        with real_app.app_context():
            response = auth_admin.put('/api/messaging/messages/1', json={})
            assert response.status_code == 400

    @patch('services.messaging_service.MessagingService.edit_message')
    def test_ROUTE_MSG_EDIT_002_not_found(self, mock_edit, auth_admin, real_app,
                                           seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_edit.return_value = None
            response = auth_admin.put('/api/messaging/messages/999',
                                       json={'content': 'edited'})
            assert response.status_code == 404

    @patch('services.messaging_service.MessagingService.edit_message')
    def test_ROUTE_MSG_EDIT_003_success(self, mock_edit, auth_admin, real_app,
                                         seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_edit.return_value = {'id': 1, 'content': 'edited'}
            response = auth_admin.put('/api/messaging/messages/1',
                                       json={'content': 'edited'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# DELETE /api/messaging/messages/<id> (Delete message)
# ---------------------------------------------------------------------------

class TestDeleteMessage:
    """Tests for DELETE /api/messaging/messages/<message_id>"""

    @patch('services.messaging_service.MessagingService.delete_message')
    def test_ROUTE_MSG_DEL_001_not_found(self, mock_del, auth_admin, real_app,
                                          seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_del.return_value = False
            response = auth_admin.delete('/api/messaging/messages/999')
            assert response.status_code == 404

    @patch('services.messaging_service.MessagingService.delete_message')
    def test_ROUTE_MSG_DEL_002_success(self, mock_del, auth_admin, real_app,
                                        seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_del.return_value = True
            response = auth_admin.delete('/api/messaging/messages/1')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# POST /api/messaging/conversations/<id>/read (Mark as read)
# ---------------------------------------------------------------------------

class TestMarkAsRead:
    """Tests for POST /api/messaging/conversations/<id>/read"""

    def test_ROUTE_MSG_READ_001_missing_message_id(self, auth_admin, real_app,
                                                    seed_messaging_perms, enable_communication):
        with real_app.app_context():
            response = auth_admin.post('/api/messaging/conversations/1/read', json={})
            assert response.status_code == 400

    @patch('services.messaging_service.MessagingService.mark_as_read')
    def test_ROUTE_MSG_READ_002_not_found(self, mock_read, auth_admin, real_app,
                                           seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_read.return_value = False
            response = auth_admin.post('/api/messaging/conversations/999/read',
                                        json={'up_to_message_id': 5})
            assert response.status_code == 404

    @patch('services.messaging_service.MessagingService.mark_as_read')
    def test_ROUTE_MSG_READ_003_success(self, mock_read, auth_admin, real_app,
                                         seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_read.return_value = True
            response = auth_admin.post('/api/messaging/conversations/1/read',
                                        json={'up_to_message_id': 10})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# GET /api/messaging/unread (Unread counts)
# ---------------------------------------------------------------------------

class TestUnreadCounts:
    """Tests for GET /api/messaging/unread"""

    @patch('services.messaging_service.MessagingService.get_unread_counts')
    def test_ROUTE_MSG_UNREAD_001_success(self, mock_counts, auth_admin, real_app,
                                           seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_counts.return_value = {'total': 5, 'conversations': {}}
            response = auth_admin.get('/api/messaging/unread')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['total'] == 5


# ---------------------------------------------------------------------------
# POST /api/messaging/conversations/<id>/mute (Mute conversation)
# ---------------------------------------------------------------------------

class TestMuteConversation:
    """Tests for POST /api/messaging/conversations/<id>/mute"""

    @patch('services.messaging_service.MessagingService.mute_conversation')
    def test_ROUTE_MSG_MUTE_001_not_found(self, mock_mute, auth_admin, real_app,
                                           seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_mute.return_value = False
            response = auth_admin.post('/api/messaging/conversations/999/mute',
                                        json={'mute': True})
            assert response.status_code == 404

    @patch('services.messaging_service.MessagingService.mute_conversation')
    def test_ROUTE_MSG_MUTE_002_success(self, mock_mute, auth_admin, real_app,
                                         seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_mute.return_value = True
            response = auth_admin.post('/api/messaging/conversations/1/mute',
                                        json={'mute': True})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['is_muted'] is True


# ---------------------------------------------------------------------------
# POST /api/messaging/keys (Store key bundle)
# ---------------------------------------------------------------------------

class TestStoreKeyBundle:
    """Tests for POST /api/messaging/keys"""

    def test_ROUTE_MSG_KEY_001_missing_body(self, auth_admin, real_app,
                                             seed_messaging_perms, enable_communication):
        with real_app.app_context():
            response = auth_admin.post('/api/messaging/keys', json={})
            assert response.status_code == 400

    def test_ROUTE_MSG_KEY_002_missing_fields(self, auth_admin, real_app,
                                               seed_messaging_perms, enable_communication):
        with real_app.app_context():
            response = auth_admin.post('/api/messaging/keys',
                                        json={'identity_public_key': 'abc'})
            assert response.status_code == 400

    @patch('services.messaging_service.MessagingService.store_key_bundle')
    def test_ROUTE_MSG_KEY_003_success(self, mock_store, auth_admin, real_app,
                                        seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_store.return_value = {'id': 1}
            response = auth_admin.post('/api/messaging/keys', json={
                'identity_public_key': 'abc',
                'signed_prekey_public': 'xyz'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# GET /api/messaging/keys/<username> (Get key bundle)
# ---------------------------------------------------------------------------

class TestGetKeyBundle:
    """Tests for GET /api/messaging/keys/<target_username>"""

    @patch('services.messaging_service.MessagingService.get_key_bundle')
    def test_ROUTE_MSG_KEYBUNDLE_001_not_found(self, mock_get, auth_admin, real_app,
                                                seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_get.return_value = None
            response = auth_admin.get('/api/messaging/keys/nonexistent')
            assert response.status_code == 404

    @patch('services.messaging_service.MessagingService.get_key_bundle')
    def test_ROUTE_MSG_KEYBUNDLE_002_success(self, mock_get, auth_admin, real_app,
                                              seed_messaging_perms, enable_communication):
        with real_app.app_context():
            mock_get.return_value = {'identity_public_key': 'abc'}
            response = auth_admin.get('/api/messaging/keys/someuser')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'key_bundle' in data
