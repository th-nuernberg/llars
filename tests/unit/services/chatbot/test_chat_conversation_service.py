"""
Tests for ChatConversationService.

Covers get_or_create_conversation, save_message, get_conversations,
get_conversation, create_conversation, delete_conversation, and rate_message.
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


class TestGetOrCreateConversation:
    """Tests for ChatConversationService.get_or_create_conversation."""

    def test_CCONV_001_creates_new_conversation(self, app, db, app_context):
        """[CCONV-001] Creates new conversation when none exists."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_conv', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        conv = ChatConversationService.get_or_create_conversation(
            bot.id, 'session-123', 'testuser'
        )
        db.session.commit()

        assert conv is not None
        assert conv.chatbot_id == bot.id
        assert conv.session_id == 'session-123'
        assert conv.username == 'testuser'
        assert conv.is_active is True

    def test_CCONV_002_returns_existing_conversation(self, app, db, app_context):
        """[CCONV-002] Returns existing conversation for same session."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_conv2', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        existing = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-exist', username='testuser', is_active=True
        )
        db.session.add(existing)
        db.session.commit()

        conv = ChatConversationService.get_or_create_conversation(
            bot.id, 'sess-exist', 'testuser'
        )
        assert conv.id == existing.id

    def test_CCONV_003_explicit_conversation_id(self, app, db, app_context):
        """[CCONV-003] Explicit conversation_id takes priority."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_conv3', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        existing = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-3', username='testuser', is_active=True
        )
        db.session.add(existing)
        db.session.commit()

        conv = ChatConversationService.get_or_create_conversation(
            bot.id, 'different-sess', 'testuser', conversation_id=existing.id
        )
        assert conv.id == existing.id

    def test_CCONV_004_different_session_creates_new(self, app, db, app_context):
        """[CCONV-004] Different session_id creates new conversation."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_conv4', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        existing = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-4a', username='user_a', is_active=True
        )
        db.session.add(existing)
        db.session.commit()

        # Different session_id creates a new conversation
        conv = ChatConversationService.get_or_create_conversation(
            bot.id, 'sess-4b', 'user_b'
        )
        db.session.commit()
        assert conv.id != existing.id
        assert conv.username == 'user_b'

    def test_CCONV_005_wrong_user_explicit_id_returns_none(self, app, db, app_context):
        """[CCONV-005] Explicit ID with wrong user falls back to session lookup."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_conv5', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        existing = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-5', username='owner', is_active=True
        )
        db.session.add(existing)
        db.session.commit()

        conv = ChatConversationService.get_or_create_conversation(
            bot.id, 'new-sess', 'intruder', conversation_id=existing.id
        )
        db.session.commit()
        # Should create a new one since user mismatch
        assert conv.id != existing.id


class TestSaveMessage:
    """Tests for ChatConversationService.save_message."""

    def test_CCONV_010_save_user_message(self, app, db, app_context):
        """[CCONV-010] Save user message to conversation."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation, ChatbotMessageRole

        bot = Chatbot(
            name='test_msg', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        conv = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-msg', is_active=True
        )
        db.session.add(conv)
        db.session.commit()

        msg = ChatConversationService.save_message(
            conv.id, ChatbotMessageRole.USER, 'Hello!'
        )
        db.session.commit()

        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.role == ChatbotMessageRole.USER
        assert msg.content == 'Hello!'

    def test_CCONV_011_save_assistant_message_with_metadata(self, app, db, app_context):
        """[CCONV-011] Save assistant message with full metadata."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation, ChatbotMessageRole

        bot = Chatbot(
            name='test_msg2', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        conv = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-msg2', is_active=True
        )
        db.session.add(conv)
        db.session.commit()

        msg = ChatConversationService.save_message(
            conv.id, ChatbotMessageRole.ASSISTANT, 'Response!',
            rag_context='some context',
            rag_sources=[{'url': 'http://example.com'}],
            tokens_input=100,
            tokens_output=50,
            response_time_ms=250,
            stream_metadata={'mode': 'standard'}
        )
        db.session.commit()

        assert msg.tokens_input == 100
        assert msg.tokens_output == 50
        assert msg.response_time_ms == 250


class TestGetConversations:
    """Tests for ChatConversationService.get_conversations."""

    def test_CCONV_020_empty_list(self, app, db, app_context):
        """[CCONV-020] Returns empty list when no conversations."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        result = ChatConversationService.get_conversations(99999)
        assert result == []

    def test_CCONV_021_filters_by_username(self, app, db, app_context):
        """[CCONV-021] Filters conversations by username."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_list', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        for user in ['user_a', 'user_b', 'user_a']:
            db.session.add(ChatbotConversation(
                chatbot_id=bot.id, session_id=f'sess-{uuid4()}', username=user, is_active=True
            ))
        db.session.commit()

        result = ChatConversationService.get_conversations(bot.id, 'user_a')
        assert len(result) == 2
        for conv in result:
            assert conv['username'] == 'user_a'

    def test_CCONV_022_respects_limit(self, app, db, app_context):
        """[CCONV-022] Respects limit parameter."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_limit', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        for i in range(10):
            db.session.add(ChatbotConversation(
                chatbot_id=bot.id, session_id=f'sess-{i}', is_active=True
            ))
        db.session.commit()

        result = ChatConversationService.get_conversations(bot.id, limit=3)
        assert len(result) == 3


class TestGetConversation:
    """Tests for ChatConversationService.get_conversation."""

    def test_CCONV_030_not_found(self, app, db, app_context):
        """[CCONV-030] Returns None for nonexistent conversation."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        assert ChatConversationService.get_conversation(99999) is None

    def test_CCONV_031_returns_with_messages(self, app, db, app_context):
        """[CCONV-031] Returns conversation with messages."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation, ChatbotMessage, ChatbotMessageRole

        bot = Chatbot(
            name='test_get', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        conv = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-get', username='testuser', is_active=True
        )
        db.session.add(conv)
        db.session.flush()

        msg = ChatbotMessage(
            conversation_id=conv.id, role=ChatbotMessageRole.USER, content='Hello'
        )
        db.session.add(msg)
        db.session.commit()

        result = ChatConversationService.get_conversation(conv.id)
        assert result is not None
        assert result['id'] == conv.id
        assert len(result['messages']) == 1
        assert result['messages'][0]['content'] == 'Hello'

    def test_CCONV_032_security_wrong_user(self, app, db, app_context):
        """[CCONV-032] Returns None when username doesn't match."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_sec', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        conv = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-sec', username='owner', is_active=True
        )
        db.session.add(conv)
        db.session.commit()

        result = ChatConversationService.get_conversation(conv.id, username='intruder')
        assert result is None


class TestCreateConversation:
    """Tests for ChatConversationService.create_conversation."""

    def test_CCONV_040_create_with_defaults(self, app, db, app_context):
        """[CCONV-040] Creates conversation with auto-generated session_id."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_create', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatConversationService.create_conversation(bot.id, 'testuser')
        assert result['chatbot_id'] == bot.id
        assert result['username'] == 'testuser'
        assert result['session_id'] is not None
        assert result['is_active'] is True

    def test_CCONV_041_create_with_title(self, app, db, app_context):
        """[CCONV-041] Creates conversation with specified title."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_create2', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatConversationService.create_conversation(
            bot.id, 'testuser', title='My Chat'
        )
        assert result['title'] == 'My Chat'


class TestDeleteConversation:
    """Tests for ChatConversationService.delete_conversation."""

    def test_CCONV_050_delete_success(self, app, db, app_context):
        """[CCONV-050] Deletes conversation and returns True."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_del', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        conv = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-del', username='testuser', is_active=True
        )
        db.session.add(conv)
        db.session.commit()

        result = ChatConversationService.delete_conversation(conv.id, 'testuser')
        assert result is True

        # Verify deleted
        assert ChatbotConversation.query.get(conv.id) is None

    def test_CCONV_051_delete_not_found(self, app, db, app_context):
        """[CCONV-051] Returns False for nonexistent conversation."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        assert ChatConversationService.delete_conversation(99999) is False

    def test_CCONV_052_delete_wrong_user(self, app, db, app_context):
        """[CCONV-052] Returns False when username doesn't match."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation

        bot = Chatbot(
            name='test_del2', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        conv = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-del2', username='owner', is_active=True
        )
        db.session.add(conv)
        db.session.commit()

        result = ChatConversationService.delete_conversation(conv.id, 'intruder')
        assert result is False


class TestRateMessage:
    """Tests for ChatConversationService.rate_message."""

    def test_CCONV_060_rate_success(self, app, db, app_context):
        """[CCONV-060] Rates message successfully."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        from db.tables import Chatbot, ChatbotConversation, ChatbotMessage, ChatbotMessageRole

        bot = Chatbot(
            name='test_rate', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.flush()

        conv = ChatbotConversation(
            chatbot_id=bot.id, session_id='sess-rate', is_active=True
        )
        db.session.add(conv)
        db.session.flush()

        msg = ChatbotMessage(
            conversation_id=conv.id, role=ChatbotMessageRole.ASSISTANT, content='Hi'
        )
        db.session.add(msg)
        db.session.commit()

        result = ChatConversationService.rate_message(msg.id, 'helpful', 'Great response')
        assert result is True

        refreshed = ChatbotMessage.query.get(msg.id)
        assert refreshed.user_rating == 'helpful'
        assert refreshed.user_feedback == 'Great response'

    def test_CCONV_061_rate_not_found(self, app, db, app_context):
        """[CCONV-061] Returns False for nonexistent message."""
        from services.chatbot.chat_conversation_service import ChatConversationService
        assert ChatConversationService.rate_message(99999, 'helpful') is False
