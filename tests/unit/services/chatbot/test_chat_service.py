"""
Tests for ChatService - the main chat orchestration service.

Covers initialization, URL placeholder replacement, system prompt building,
message building, vision content building, and static conversation methods.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from uuid import uuid4


def _make_chatbot(db, **overrides):
    """Helper to create a chatbot in the DB."""
    from db.tables import Chatbot
    defaults = dict(
        name=f'test_{uuid4().hex[:8]}', display_name='Test Bot',
        system_prompt='Du bist ein Assistent.', model_name='test-model',
        created_by='admin', rag_enabled=False, temperature=0.7,
        max_tokens=1024, top_p=0.9, max_context_messages=10,
    )
    defaults.update(overrides)
    bot = Chatbot(**defaults)
    db.session.add(bot)
    db.session.commit()
    return bot


class TestChatServiceInit:
    """Tests for ChatService.__init__."""

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_001_init_rag_disabled(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-001] RAG pipeline not created when rag_enabled=False."""
        from services.chatbot.chat_service import ChatService

        mock_client = MagicMock()
        mock_factory.resolve_for_chat.return_value = (mock_client, 'test-api-model')

        bot = _make_chatbot(db, rag_enabled=False)
        service = ChatService(bot.id)

        assert service.rag_pipeline is None
        assert service.chatbot.id == bot.id

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_002_init_rag_enabled(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-002] RAG pipeline created when rag_enabled=True."""
        from services.chatbot.chat_service import ChatService

        mock_client = MagicMock()
        mock_factory.resolve_for_chat.return_value = (mock_client, 'test-api-model')

        bot = _make_chatbot(db, rag_enabled=True)
        service = ChatService(bot.id)

        assert service.rag_pipeline is not None

    def test_CSVC_003_init_nonexistent_chatbot(self, app, db, app_context):
        """[CSVC-003] Nonexistent chatbot raises ValueError."""
        from services.chatbot.chat_service import ChatService
        with pytest.raises(ValueError, match='not found'):
            ChatService(99999)

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_004_init_fallback_client(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-004] Falls back to resolve_client_and_model_id when resolve_for_chat returns None."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (None, None)
        mock_client = MagicMock()
        mock_factory.resolve_client_and_model_id.return_value = (mock_client, 'fallback-model')

        bot = _make_chatbot(db, rag_enabled=False)
        service = ChatService(bot.id)

        assert service.llm_client == mock_client
        assert service.api_model_id == 'fallback-model'


class TestReplaceUrlPlaceholders:
    """Tests for ChatService._replace_url_placeholders."""

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_010_replace_simple_placeholder(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-010] Replaces {PROJECT_URL} placeholder."""
        from services.chatbot.chat_service import ChatService
        import os

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        bot = _make_chatbot(db)
        service = ChatService(bot.id)

        result = service._replace_url_placeholders('Visit {PROJECT_URL}/docs')
        project_url = os.environ.get('PROJECT_URL', 'http://localhost:55080')
        assert project_url in result
        assert '{PROJECT_URL}' not in result

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_011_replace_shell_placeholder(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-011] Replaces ${PROJECT_URL} shell-style placeholder."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        bot = _make_chatbot(db)
        service = ChatService(bot.id)

        result = service._replace_url_placeholders('Link: ${PROJECT_URL}')
        assert '${PROJECT_URL}' not in result

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_012_replace_empty_text(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-012] Empty text returns empty."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        bot = _make_chatbot(db)
        service = ChatService(bot.id)

        assert service._replace_url_placeholders('') == ''
        assert service._replace_url_placeholders(None) is None


class TestSystemPromptWithUrls:
    """Tests for ChatService._get_system_prompt_with_urls."""

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_020_prompt_with_placeholder(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-020] System prompt with placeholder gets substituted."""
        from services.chatbot.chat_service import ChatService
        import os

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        bot = _make_chatbot(db, system_prompt='Visit {PROJECT_URL}/api')
        service = ChatService(bot.id)

        result = service._get_system_prompt_with_urls()
        project_url = os.environ.get('PROJECT_URL', 'http://localhost:55080')
        assert f'{project_url}/api' in result

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_021_prompt_without_placeholder(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-021] System prompt without placeholder passes through."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        bot = _make_chatbot(db, system_prompt='Simple prompt')
        service = ChatService(bot.id)

        assert service._get_system_prompt_with_urls() == 'Simple prompt'


class TestBuildVisionContent:
    """Tests for ChatService._build_vision_content."""

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_030_vision_with_rag_images(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-030] Builds vision content with RAG images."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        bot = _make_chatbot(db)
        service = ChatService(bot.id)

        rag_images = [{'image_data': 'base64data', 'mime_type': 'image/png'}]
        content = service._build_vision_content('What is this?', rag_images, [])

        assert len(content) >= 3  # text header + image + user message
        assert content[0]['type'] == 'text'
        assert 'Kontextbilder' in content[0]['text']
        assert content[-1]['text'] == 'What is this?'

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_031_vision_with_user_images(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-031] Builds vision content with user images."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        bot = _make_chatbot(db)
        service = ChatService(bot.id)

        user_images = [{'image_data': 'userbase64', 'mime_type': 'image/jpeg'}]
        content = service._build_vision_content('Describe this', [], user_images)

        assert content[-1]['text'] == 'Describe this'
        # Should have image_url entry
        has_image = any(c.get('type') == 'image_url' for c in content)
        assert has_image

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_032_vision_both_image_types(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-032] Builds vision content with both RAG and user images."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        bot = _make_chatbot(db)
        service = ChatService(bot.id)

        rag_images = [{'image_data': 'ragdata', 'mime_type': 'image/png'}]
        user_images = [{'image_data': 'userdata', 'mime_type': 'image/jpeg'}]
        content = service._build_vision_content('Analyze', rag_images, user_images)

        text_items = [c for c in content if c.get('type') == 'text']
        # Should have context header, user header, and user message
        assert any('Kontextbilder' in t['text'] for t in text_items)
        assert any('hochgeladene' in t['text'] for t in text_items)


class TestStaticConversationMethods:
    """Tests for static conversation delegation methods."""

    @patch('services.chatbot.chat_service.ChatConversationService')
    def test_CSVC_040_get_conversations_delegates(self, mock_conv_svc, app, app_context):
        """[CSVC-040] get_conversations delegates to ChatConversationService."""
        from services.chatbot.chat_service import ChatService
        mock_conv_svc.get_conversations.return_value = []

        ChatService.get_conversations(1, 'user', 10)
        mock_conv_svc.get_conversations.assert_called_once_with(1, 'user', 10)

    @patch('services.chatbot.chat_service.ChatConversationService')
    def test_CSVC_041_get_conversation_delegates(self, mock_conv_svc, app, app_context):
        """[CSVC-041] get_conversation delegates to ChatConversationService."""
        from services.chatbot.chat_service import ChatService
        mock_conv_svc.get_conversation.return_value = None

        ChatService.get_conversation(1, 'user', 5)
        mock_conv_svc.get_conversation.assert_called_once_with(1, 'user', 5)

    @patch('services.chatbot.chat_service.ChatConversationService')
    def test_CSVC_042_delete_conversation_delegates(self, mock_conv_svc, app, app_context):
        """[CSVC-042] delete_conversation delegates to ChatConversationService."""
        from services.chatbot.chat_service import ChatService
        mock_conv_svc.delete_conversation.return_value = True

        result = ChatService.delete_conversation(1, 'user')
        assert result is True

    @patch('services.chatbot.chat_service.ChatConversationService')
    def test_CSVC_043_rate_message_delegates(self, mock_conv_svc, app, app_context):
        """[CSVC-043] rate_message delegates to ChatConversationService."""
        from services.chatbot.chat_service import ChatService
        mock_conv_svc.rate_message.return_value = True

        result = ChatService.rate_message(1, 'helpful', 'good')
        assert result is True
        mock_conv_svc.rate_message.assert_called_once_with(1, 'helpful', 'good')

    @patch('services.chatbot.chat_service.ChatConversationService')
    def test_CSVC_044_create_conversation_delegates(self, mock_conv_svc, app, app_context):
        """[CSVC-044] create_conversation delegates to ChatConversationService."""
        from services.chatbot.chat_service import ChatService
        mock_conv_svc.create_conversation.return_value = {'id': 1}

        result = ChatService.create_conversation(1, 'user', 'My Title')
        assert result == {'id': 1}


class TestTestChat:
    """Tests for ChatService.test_chat."""

    @patch('services.chatbot.chat_service.LLMExecutionService')
    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_050_test_chat_no_rag(self, mock_rag, mock_factory, mock_exec, app, db, app_context):
        """[CSVC-050] Test chat without RAG returns LLM response."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 30

        mock_exec.execute_chat_completion.return_value = mock_response

        with patch('services.chatbot.chat_service.extract_message_text', return_value='Test response'):
            bot = _make_chatbot(db, rag_enabled=False)
            service = ChatService(bot.id)
            result = service.test_chat('Hello')

            assert result['test_mode'] is True
            assert result['response'] == 'Test response'
            assert 'tokens' in result

    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_051_test_chat_requires_sources_no_results(self, mock_rag, mock_factory, app, db, app_context):
        """[CSVC-051] Test chat with required sources but no results returns unknown answer."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')

        bot = _make_chatbot(db, rag_enabled=True)
        service = ChatService(bot.id)

        with patch.object(service, '_requires_sources', return_value=True):
            with patch.object(service, '_get_multi_collection_context', return_value=('', [])):
                with patch.object(service, 'get_unknown_answer', return_value='Keine Antwort'):
                    result = service.test_chat('Hello')

                    assert result['test_mode'] is True
                    assert result['response'] == 'Keine Antwort'
                    assert result['sources'] == []


class TestSupportsVision:
    """Tests for ChatService.supports_vision."""

    @patch('services.chatbot.chat_service.FileProcessor')
    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_060_supports_vision_true(self, mock_rag, mock_factory, mock_fp, app, db, app_context):
        """[CSVC-060] supports_vision returns True for vision model."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        mock_fp.is_vision_model.return_value = True

        bot = _make_chatbot(db)
        service = ChatService(bot.id)
        assert service.supports_vision() is True

    @patch('services.chatbot.chat_service.FileProcessor')
    @patch('services.chatbot.chat_service.LLMClientFactory')
    @patch('services.chatbot.chat_service.RAGPipeline')
    def test_CSVC_061_supports_vision_false(self, mock_rag, mock_factory, mock_fp, app, db, app_context):
        """[CSVC-061] supports_vision returns False for non-vision model."""
        from services.chatbot.chat_service import ChatService

        mock_factory.resolve_for_chat.return_value = (MagicMock(), 'model')
        mock_fp.is_vision_model.return_value = False

        bot = _make_chatbot(db)
        service = ChatService(bot.id)
        assert service.supports_vision() is False
