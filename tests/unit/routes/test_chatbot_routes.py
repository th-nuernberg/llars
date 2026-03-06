"""
Route Tests for Chatbot API
=============================

Tests for app/routes/chatbot/chatbot_crud_routes.py.
Covers: CRUD operations, auth checks (401, 403), validation (400).

Uses real blueprints with mocked OIDC token validation.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


def _create_chatbot_in_db(db_instance, name='test-bot', display_name='Test Bot',
                          created_by='admin', is_active=True, is_public=False):
    """Helper: insert a chatbot directly into the DB."""
    from db.models.chatbot import Chatbot

    bot = Chatbot(
        name=name,
        display_name=display_name,
        description='A test chatbot',
        system_prompt='You are a helpful assistant.',
        model_name='test-model',
        created_by=created_by,
        is_active=is_active,
        is_public=is_public,
    )
    db_instance.session.add(bot)
    db_instance.session.commit()
    return bot


# ---------------------------------------------------------------------------
# List Chatbots
# ---------------------------------------------------------------------------

class TestListChatbots:
    """Tests for GET /api/chatbots"""

    def test_ROUTE_CHAT_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/chatbots')
        assert response.status_code == 401

    def test_ROUTE_CHAT_LIST_002_success_admin(self, auth_admin, real_app):
        with real_app.app_context():
            _create_chatbot_in_db(real_app.db, name='list-bot-1',
                                  display_name='List Bot 1', created_by='admin')

            response = auth_admin.get('/api/chatbots')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['chatbots'], list)
            assert data['count'] >= 1

    def test_ROUTE_CHAT_LIST_003_success_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            _create_chatbot_in_db(real_app.db, name='list-bot-eval',
                                  display_name='Eval Bot', created_by='admin',
                                  is_public=True)

            response = auth_user.get('/api/chatbots')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Get Single Chatbot
# ---------------------------------------------------------------------------

class TestGetChatbot:
    """Tests for GET /api/chatbots/<id>"""

    def test_ROUTE_CHAT_GET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/chatbots/1')
        assert response.status_code == 401

    def test_ROUTE_CHAT_GET_002_not_found_returns_403(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/chatbots/99999')
            # Access check runs first: Chatbot.query.get(99999) returns None,
            # so user_can_access_chatbot(username, None) returns False -> 403
            assert response.status_code == 403

    def test_ROUTE_CHAT_GET_003_success_admin(self, auth_admin, real_app):
        with real_app.app_context():
            bot = _create_chatbot_in_db(real_app.db, name='get-bot',
                                        display_name='Get Bot', created_by='admin')
            response = auth_admin.get(f'/api/chatbots/{bot.id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['chatbot']['display_name'] == 'Get Bot'

    def test_ROUTE_CHAT_GET_004_forbidden_evaluator_private(self, auth_user, real_app):
        with real_app.app_context():
            bot = _create_chatbot_in_db(real_app.db, name='private-bot',
                                        display_name='Private Bot',
                                        created_by='admin', is_public=False)
            response = auth_user.get(f'/api/chatbots/{bot.id}')
            assert response.status_code == 403


# ---------------------------------------------------------------------------
# Create Chatbot
# ---------------------------------------------------------------------------

class TestCreateChatbot:
    """Tests for POST /api/chatbots"""

    def test_ROUTE_CHAT_CREATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/chatbots', json={
            'name': 'new-bot', 'display_name': 'New Bot',
            'system_prompt': 'Hello'
        })
        assert response.status_code == 401

    def test_ROUTE_CHAT_CREATE_002_forbidden_evaluator(self, auth_user, real_app):
        """Evaluator lacks feature:chatbots:edit permission."""
        with real_app.app_context():
            response = auth_user.post('/api/chatbots', json={
                'name': 'eval-bot', 'display_name': 'Eval Bot',
                'system_prompt': 'Hello'
            })
            assert response.status_code == 403

    def test_ROUTE_CHAT_CREATE_003_no_data(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/chatbots',
                                       data='',
                                       content_type='application/json')
            assert response.status_code in [400, 500]

    @patch('services.chatbot.chatbot_service.ChatbotService.create_chatbot')
    @patch('services.chatbot_activity_service.ChatbotActivityService.log_chatbot_created')
    def test_ROUTE_CHAT_CREATE_004_success(self, mock_log, mock_create, auth_admin, real_app):
        mock_create.return_value = {
            'id': 1, 'name': 'new-bot', 'display_name': 'New Bot',
            'description': '', 'system_prompt': 'Hello'
        }
        with real_app.app_context():
            response = auth_admin.post('/api/chatbots', json={
                'name': 'new-bot', 'display_name': 'New Bot',
                'system_prompt': 'Hello'
            })
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['chatbot']['name'] == 'new-bot'

    @patch('services.chatbot.chatbot_service.ChatbotService.create_chatbot')
    def test_ROUTE_CHAT_CREATE_005_missing_required(self, mock_create, auth_admin, real_app):
        mock_create.side_effect = ValueError("Missing required field: name")
        with real_app.app_context():
            response = auth_admin.post('/api/chatbots', json={
                'display_name': 'No Name Bot',
                'system_prompt': 'Hello'
            })
            assert response.status_code == 400

    @patch('services.chatbot.chatbot_service.ChatbotService.create_chatbot')
    def test_ROUTE_CHAT_CREATE_006_duplicate_name(self, mock_create, auth_admin, real_app):
        mock_create.side_effect = ValueError("Chatbot with name 'dup' already exists")
        with real_app.app_context():
            response = auth_admin.post('/api/chatbots', json={
                'name': 'dup', 'display_name': 'Dup Bot',
                'system_prompt': 'Hello'
            })
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# Update Chatbot
# ---------------------------------------------------------------------------

class TestUpdateChatbot:
    """Tests for PUT /api/chatbots/<id>"""

    def test_ROUTE_CHAT_UPDATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/chatbots/1',
                               json={'display_name': 'Updated'})
        assert response.status_code == 401

    def test_ROUTE_CHAT_UPDATE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.put('/api/chatbots/1',
                                     json={'display_name': 'Updated'})
            assert response.status_code == 403

    def test_ROUTE_CHAT_UPDATE_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/chatbots/99999',
                                      json={'display_name': 'Updated'})
            assert response.status_code == 404

    @patch('services.chatbot.chatbot_service.ChatbotService.update_chatbot')
    @patch('services.chatbot_activity_service.ChatbotActivityService.log_chatbot_updated')
    def test_ROUTE_CHAT_UPDATE_004_success(self, mock_log, mock_update, auth_admin, real_app):
        with real_app.app_context():
            bot = _create_chatbot_in_db(real_app.db, name='update-bot',
                                        display_name='Update Bot', created_by='admin')
            mock_update.return_value = {
                'id': bot.id, 'display_name': 'Updated Bot',
                'name': 'update-bot'
            }
            response = auth_admin.put(f'/api/chatbots/{bot.id}',
                                       json={'display_name': 'Updated Bot'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_ROUTE_CHAT_UPDATE_005_no_data(self, auth_admin, real_app):
        with real_app.app_context():
            bot = _create_chatbot_in_db(real_app.db, name='update-nodata',
                                        display_name='No Data Bot', created_by='admin')
            response = auth_admin.put(f'/api/chatbots/{bot.id}',
                                       data='', content_type='application/json')
            assert response.status_code in [400, 500]


# ---------------------------------------------------------------------------
# Delete Chatbot
# ---------------------------------------------------------------------------

class TestDeleteChatbot:
    """Tests for DELETE /api/chatbots/<id>"""

    def test_ROUTE_CHAT_DELETE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/chatbots/1')
        assert response.status_code == 401

    def test_ROUTE_CHAT_DELETE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.delete('/api/chatbots/1')
            assert response.status_code == 403

    def test_ROUTE_CHAT_DELETE_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.delete('/api/chatbots/99999')
            assert response.status_code == 404

    @patch('services.chatbot.chatbot_service.ChatbotService.delete_chatbot')
    @patch('services.chatbot_activity_service.ChatbotActivityService.log_chatbot_deleted')
    def test_ROUTE_CHAT_DELETE_004_success(self, mock_log, mock_delete, auth_admin, real_app):
        with real_app.app_context():
            bot = _create_chatbot_in_db(real_app.db, name='delete-bot',
                                        display_name='Delete Bot', created_by='admin')
            mock_delete.return_value = True
            response = auth_admin.delete(f'/api/chatbots/{bot.id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Duplicate Chatbot
# ---------------------------------------------------------------------------

class TestDuplicateChatbot:
    """Tests for POST /api/chatbots/<id>/duplicate"""

    def test_ROUTE_CHAT_DUP_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/chatbots/1/duplicate')
        assert response.status_code == 401

    def test_ROUTE_CHAT_DUP_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/chatbots/1/duplicate')
            assert response.status_code == 403

    def test_ROUTE_CHAT_DUP_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/chatbots/99999/duplicate')
            assert response.status_code == 404

    @patch('services.chatbot.chatbot_service.ChatbotService.duplicate_chatbot')
    @patch('services.chatbot_activity_service.ChatbotActivityService.log_chatbot_duplicated')
    def test_ROUTE_CHAT_DUP_004_success(self, mock_log, mock_dup, auth_admin, real_app):
        with real_app.app_context():
            bot = _create_chatbot_in_db(real_app.db, name='dup-source',
                                        display_name='Dup Source', created_by='admin')
            mock_dup.return_value = {
                'id': 999, 'display_name': 'Dup Source (Copy)',
                'name': 'dup-source-copy'
            }
            response = auth_admin.post(f'/api/chatbots/{bot.id}/duplicate')
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert 'Copy' in data['chatbot']['display_name']


# ---------------------------------------------------------------------------
# Chatbot Access Overview (Admin)
# ---------------------------------------------------------------------------

class TestChatbotAccessOverview:
    """Tests for GET /api/chatbots/access/overview"""

    def test_ROUTE_CHAT_ACCESS_OV_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/chatbots/access/overview')
        assert response.status_code == 401

    def test_ROUTE_CHAT_ACCESS_OV_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/chatbots/access/overview')
            assert response.status_code == 403

    def test_ROUTE_CHAT_ACCESS_OV_003_success_admin(self, auth_admin, real_app):
        with real_app.app_context():
            _create_chatbot_in_db(real_app.db, name='access-ov-bot',
                                  display_name='Access OV Bot', created_by='admin')
            response = auth_admin.get('/api/chatbots/access/overview')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['chatbots'], list)
            assert data['count'] >= 1


# ---------------------------------------------------------------------------
# Chatbot Access Get/Set
# ---------------------------------------------------------------------------

class TestChatbotAccess:
    """Tests for GET/PUT /api/chatbots/<id>/access"""

    def test_ROUTE_CHAT_ACCESS_001_get_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/chatbots/1/access')
        assert response.status_code == 401

    def test_ROUTE_CHAT_ACCESS_002_get_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/chatbots/99999/access')
            assert response.status_code == 404

    def test_ROUTE_CHAT_ACCESS_003_get_success(self, auth_admin, real_app):
        with real_app.app_context():
            bot = _create_chatbot_in_db(real_app.db, name='access-get-bot',
                                        display_name='Access Get Bot', created_by='admin')
            response = auth_admin.get(f'/api/chatbots/{bot.id}/access')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'allowed_usernames' in data

    def test_ROUTE_CHAT_ACCESS_004_set_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/chatbots/1/access',
                               json={'usernames': ['testuser']})
        assert response.status_code == 401

    def test_ROUTE_CHAT_ACCESS_005_set_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/chatbots/99999/access',
                                      json={'usernames': ['testuser']})
            assert response.status_code == 404

    def test_ROUTE_CHAT_ACCESS_006_set_success(self, auth_admin, real_app, ruser):
        with real_app.app_context():
            bot = _create_chatbot_in_db(real_app.db, name='access-set-bot',
                                        display_name='Access Set Bot', created_by='admin')
            response = auth_admin.put(f'/api/chatbots/{bot.id}/access',
                                       json={'usernames': ['testuser']})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
