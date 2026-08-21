"""
Tests for ChatbotCreator service.

Covers wizard chatbot creation, finalization, build status updates,
cancellation, resume, and tweaking.
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


class TestCreateWizardChatbot:
    """Tests for ChatbotCreator.create_wizard_chatbot."""

    @patch('services.chatbot.chatbot_creator.LLMAccessService')
    def test_CCRT_001_create_from_valid_url(self, mock_access, app, db, app_context):
        """[CCRT-001] Creates draft chatbot from valid URL."""
        from services.chatbot.chatbot_creator import ChatbotCreator

        mock_model = MagicMock()
        mock_model.model_id = 'test-model'
        mock_model.is_default = True
        mock_access.get_accessible_models.return_value = [mock_model]

        result = ChatbotCreator.create_wizard_chatbot('https://example.com', 'admin')

        assert result['success'] is True
        assert result['chatbot_id'] is not None
        assert result['chatbot']['build_status'] == 'draft'
        assert result['chatbot']['source_url'] == 'https://example.com'

    def test_CCRT_002_invalid_url_raises(self, app, db, app_context):
        """[CCRT-002] Invalid URL raises ValueError."""
        from services.chatbot.chatbot_creator import ChatbotCreator

        with pytest.raises(ValueError, match='Invalid URL format'):
            ChatbotCreator.create_wizard_chatbot('not-a-url', 'admin')

    def test_CCRT_003_empty_url_raises(self, app, db, app_context):
        """[CCRT-003] Empty URL raises ValueError."""
        from services.chatbot.chatbot_creator import ChatbotCreator

        with pytest.raises(ValueError, match='Invalid URL format'):
            ChatbotCreator.create_wizard_chatbot('', 'admin')

    @patch('services.chatbot.chatbot_creator.LLMAccessService')
    def test_CCRT_004_no_model_raises(self, mock_access, app, db, app_context):
        """[CCRT-004] No accessible model raises ValueError."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        mock_access.get_accessible_models.return_value = []

        with pytest.raises(ValueError, match='No accessible LLM model'):
            ChatbotCreator.create_wizard_chatbot('https://example.com', 'admin')

    @patch('services.chatbot.chatbot_creator.LLMAccessService')
    def test_CCRT_005_unique_name_generation(self, mock_access, app, db, app_context):
        """[CCRT-005] Generates unique name when conflict exists."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        mock_model = MagicMock()
        mock_model.model_id = 'test-model'
        mock_model.is_default = True
        mock_access.get_accessible_models.return_value = [mock_model]

        # Create first bot
        result1 = ChatbotCreator.create_wizard_chatbot('https://example.com', 'admin')
        name1 = result1['chatbot']['name']

        # Create second bot from same URL
        result2 = ChatbotCreator.create_wizard_chatbot('https://example.com', 'admin')
        name2 = result2['chatbot']['name']

        assert name1 != name2
        assert name2.endswith('_1') or name2.endswith('_2')


class TestFinalizeChatbot:
    """Tests for ChatbotCreator.finalize_chatbot."""

    def test_CCRT_010_finalize_success(self, app, db, app_context):
        """[CCRT-010] Finalize chatbot with configuration data."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_fin', display_name='Test', system_prompt='test',
            model_name='test', build_status='configuring', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotCreator.finalize_chatbot(bot.id, {
            'display_name': 'My Bot',
            'system_prompt': 'Be helpful',
            'icon': 'mdi-school',
            'color': '#FF0000',
            'welcome_message': 'Hi!'
        })

        assert result['success'] is True
        assert result['build_status'] == 'ready'

        refreshed = Chatbot.query.get(bot.id)
        assert refreshed.display_name == 'My Bot'
        assert refreshed.is_active is True

    def test_CCRT_011_finalize_not_found(self, app, db, app_context):
        """[CCRT-011] Finalize nonexistent chatbot raises."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        with pytest.raises(ValueError, match='Chatbot not found'):
            ChatbotCreator.finalize_chatbot(99999, {})

    def test_CCRT_012_finalize_name_conflict(self, app, db, app_context):
        """[CCRT-012] Finalize with conflicting name raises."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        existing = Chatbot(
            name='taken_name', display_name='Existing', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(existing)

        bot = Chatbot(
            name='test_fin2', display_name='Test', system_prompt='test',
            model_name='test', build_status='configuring', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with pytest.raises(ValueError, match='Name already exists'):
            ChatbotCreator.finalize_chatbot(bot.id, {'name': 'taken_name'})

    def test_CCRT_013_finalize_with_embedding_in_progress(self, app, db, app_context):
        """[CCRT-013] Finalize during embedding returns progress flag."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot, RAGCollection

        collection = RAGCollection(
            name='test_emb', display_name='Test', created_by='admin',
            embedding_status='processing', embedding_progress=42
        )
        db.session.add(collection)
        db.session.flush()

        bot = Chatbot(
            name='test_fin3', display_name='Test', system_prompt='test',
            model_name='test', build_status='configuring', created_by='admin',
            primary_collection_id=collection.id
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotCreator.finalize_chatbot(bot.id, {})
        assert result['embedding_in_progress'] is True
        assert result['embedding_progress'] == 42


class TestUpdateBuildStatus:
    """Tests for ChatbotCreator.update_build_status."""

    def test_CCRT_020_update_status_valid(self, app, db, app_context):
        """[CCRT-020] Updates to valid status."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_stat', display_name='Test', system_prompt='test',
            model_name='test', build_status='draft', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotCreator.update_build_status(bot.id, 'crawling')
        assert result['build_status'] == 'crawling'

    def test_CCRT_021_update_status_invalid(self, app, db, app_context):
        """[CCRT-021] Invalid status raises ValueError."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_stat2', display_name='Test', system_prompt='test',
            model_name='test', build_status='draft', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with pytest.raises(ValueError, match='Invalid status'):
            ChatbotCreator.update_build_status(bot.id, 'invalid_status')

    def test_CCRT_022_update_status_not_found(self, app, db, app_context):
        """[CCRT-022] Nonexistent chatbot raises."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        with pytest.raises(ValueError, match='Chatbot not found'):
            ChatbotCreator.update_build_status(99999, 'draft')

    def test_CCRT_023_update_ready_activates(self, app, db, app_context):
        """[CCRT-023] Setting ready status activates chatbot."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_stat3', display_name='Test', system_prompt='test',
            model_name='test', build_status='configuring', is_active=False,
            created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        ChatbotCreator.update_build_status(bot.id, 'ready')
        refreshed = Chatbot.query.get(bot.id)
        assert refreshed.is_active is True
        assert refreshed.build_error is None

    def test_CCRT_024_update_error_status_with_message(self, app, db, app_context):
        """[CCRT-024] Error status stores error message."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_stat4', display_name='Test', system_prompt='test',
            model_name='test', build_status='crawling', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        ChatbotCreator.update_build_status(bot.id, 'error', error='Crawl failed')
        refreshed = Chatbot.query.get(bot.id)
        assert refreshed.build_error == 'Crawl failed'


class TestCancelBuild:
    """Tests for ChatbotCreator.cancel_build."""

    def test_CCRT_030_cancel_crawling(self, app, db, app_context):
        """[CCRT-030] Cancel during crawling sets paused status."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_cancel', display_name='Test', system_prompt='test',
            model_name='test', build_status='crawling', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotCreator.cancel_build(bot.id)
        assert result['success'] is True
        assert result['build_status'] == 'paused'
        assert 'cleanup' in result

    def test_CCRT_031_cancel_invalid_status(self, app, db, app_context):
        """[CCRT-031] Cannot cancel in draft or ready status."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_cancel2', display_name='Test', system_prompt='test',
            model_name='test', build_status='draft', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with pytest.raises(ValueError, match='Cannot cancel'):
            ChatbotCreator.cancel_build(bot.id)

    def test_CCRT_032_cancel_not_found(self, app, db, app_context):
        """[CCRT-032] Cancel nonexistent chatbot raises."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        with pytest.raises(ValueError, match='Chatbot not found'):
            ChatbotCreator.cancel_build(99999)


class TestTweakChatbot:
    """Tests for ChatbotCreator.tweak_chatbot."""

    def test_CCRT_040_tweak_temperature(self, app, db, app_context):
        """[CCRT-040] Tweaks temperature parameter."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_tweak', display_name='Test', system_prompt='test',
            model_name='test', temperature=0.7, created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotCreator.tweak_chatbot(bot.id, {'temperature': 0.3})
        assert result['success'] is True
        assert 'temperature' in result['updated_fields']

        refreshed = Chatbot.query.get(bot.id)
        assert refreshed.temperature == 0.3

    def test_CCRT_041_tweak_no_valid_fields(self, app, db, app_context):
        """[CCRT-041] No valid fields raises ValueError."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_tweak2', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with pytest.raises(ValueError, match='No valid fields'):
            ChatbotCreator.tweak_chatbot(bot.id, {'invalid_field': 'value'})

    def test_CCRT_042_tweak_not_found(self, app, db, app_context):
        """[CCRT-042] Tweak nonexistent chatbot raises."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        with pytest.raises(ValueError, match='Chatbot not found'):
            ChatbotCreator.tweak_chatbot(99999, {'temperature': 0.5})

    def test_CCRT_043_tweak_multiple_fields(self, app, db, app_context):
        """[CCRT-043] Tweaks multiple fields at once."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_tweak3', display_name='Test', system_prompt='old prompt',
            model_name='test', temperature=0.7, max_tokens=1024, created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotCreator.tweak_chatbot(bot.id, {
            'temperature': 0.5,
            'max_tokens': 2048,
            'system_prompt': 'new prompt'
        })
        assert len(result['updated_fields']) == 3

    def test_CCRT_044_tweak_updates_timestamp(self, app, db, app_context):
        """[CCRT-044] Tweak updates the updated_at timestamp."""
        from services.chatbot.chatbot_creator import ChatbotCreator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_tweak4', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotCreator.tweak_chatbot(bot.id, {'temperature': 0.1})
        assert 'updated_at' in result
