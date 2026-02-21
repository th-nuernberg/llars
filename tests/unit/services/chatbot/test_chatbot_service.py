"""
Unit Tests: Chatbot Service
============================

Tests for the ChatbotService CRUD and collection management.

Test IDs:
- CBOT-001 to CBOT-015: Helper Methods Tests
- CBOT-020 to CBOT-035: CRUD Operations Tests
- CBOT-040 to CBOT-055: Collection Management Tests
- CBOT-060 to CBOT-070: Statistics Tests
- CBOT-080 to CBOT-090: Edge Cases Tests

Status: Implemented
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHelperMethods:
    """
    Helper Methods Tests

    Tests for private helper methods.
    """

    def test_CBOT_001_resolve_llm_model_id_valid(self, app, db, app_context):
        """
        [CBOT-001] Resolve LLM Model ID - Gültiges Model

        Sollte model_id für ein aktives LLM Model zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.models.llm_model import LLMModel

        # Create active LLM model
        model = LLMModel(
            model_id='test/llm-model',
            provider='test',
            display_name='Test LLM',
            model_type='llm',
            is_active=True,
            context_window=8192,
            max_output_tokens=4096
        )
        db.session.add(model)
        db.session.commit()

        result = ChatbotService._resolve_llm_model_id('test/llm-model')
        assert result == 'test/llm-model'

    def test_CBOT_002_resolve_llm_model_id_inactive(self, app, db, app_context):
        """
        [CBOT-002] Resolve LLM Model ID - Inaktives Model

        Sollte ValueError für inaktives Model werfen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.models.llm_model import LLMModel

        model = LLMModel(
            model_id='test/inactive-model',
            provider='test',
            display_name='Test Inactive',
            model_type='llm',
            is_active=False,
            context_window=8192,
            max_output_tokens=4096
        )
        db.session.add(model)
        db.session.commit()

        with pytest.raises(ValueError, match="not an active LLM model"):
            ChatbotService._resolve_llm_model_id('test/inactive-model')

    def test_CBOT_003_resolve_llm_model_id_wrong_type(self, app, db, app_context):
        """
        [CBOT-003] Resolve LLM Model ID - Falscher Typ

        Sollte ValueError für Embedding Model werfen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.models.llm_model import LLMModel

        model = LLMModel(
            model_id='test/embedding-model',
            provider='test',
            display_name='Test Embedding',
            model_type='embedding',
            is_active=True,
            context_window=512,
            max_output_tokens=512
        )
        db.session.add(model)
        db.session.commit()

        with pytest.raises(ValueError, match="not an active LLM model"):
            ChatbotService._resolve_llm_model_id('test/embedding-model')

    def test_CBOT_004_resolve_llm_model_id_none(self, app, db, app_context):
        """
        [CBOT-004] Resolve LLM Model ID - None Input

        Sollte None für None zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService._resolve_llm_model_id(None)
        assert result is None

    def test_CBOT_005_coerce_model_name_string(self, app, app_context):
        """
        [CBOT-005] Coerce Model Name - String Input

        Sollte String unverändert zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService._coerce_model_name('gpt-4')
        assert result == 'gpt-4'

    def test_CBOT_006_coerce_model_name_dict(self, app, app_context):
        """
        [CBOT-006] Coerce Model Name - Dict Input

        Sollte model_id aus Dict extrahieren.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService._coerce_model_name({'model_id': 'gpt-4', 'name': 'GPT-4'})
        assert result == 'gpt-4'

    def test_CBOT_007_coerce_model_name_dict_value_key(self, app, app_context):
        """
        [CBOT-007] Coerce Model Name - Dict mit value Key

        Sollte value aus Dict extrahieren.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService._coerce_model_name({'value': 'claude-3'})
        assert result == 'claude-3'

    def test_CBOT_008_coerce_model_name_empty(self, app, app_context):
        """
        [CBOT-008] Coerce Model Name - Leerer String

        Sollte None für leeren String zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService._coerce_model_name('   ')
        assert result is None

    def test_CBOT_009_coerce_model_name_none(self, app, app_context):
        """
        [CBOT-009] Coerce Model Name - None Input

        Sollte None für None zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService._coerce_model_name(None)
        assert result is None

    def test_CBOT_010_serialize_prompt_settings_none(self, app, db, app_context):
        """
        [CBOT-010] Serialize Prompt Settings - Keine Settings

        Sollte None zurückgeben wenn keine Settings vorhanden.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_serialize_none',
            display_name='Test Bot',
            system_prompt='Test prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotService._serialize_prompt_settings(bot)
        assert result is None

    def test_CBOT_011_serialize_prompt_settings_exists(self, app, db, app_context):
        """
        [CBOT-011] Serialize Prompt Settings - Settings vorhanden

        Sollte Settings als Dict zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, ChatbotPromptSettings

        bot = Chatbot(
            name='test_serialize_exists',
            display_name='Test Bot',
            system_prompt='Test prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.flush()

        settings = ChatbotPromptSettings(
            chatbot_id=bot.id,
            rag_require_citations=True,
            rag_unknown_answer='Ich weiß es nicht.'
        )
        db.session.add(settings)
        db.session.commit()

        result = ChatbotService._serialize_prompt_settings(bot)
        assert result is not None
        assert result.get('rag_require_citations') is True

    def test_CBOT_012_upsert_prompt_settings_create(self, app, db, app_context):
        """
        [CBOT-012] Upsert Prompt Settings - Neue Settings

        Sollte neue Settings erstellen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, ChatbotPromptSettings

        bot = Chatbot(
            name='test_upsert_create',
            display_name='Test Bot',
            system_prompt='Test prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.flush()

        data = {
            'prompt_settings': {
                'rag_require_citations': True
            }
        }
        ChatbotService._upsert_prompt_settings(bot, data)
        db.session.commit()

        settings = ChatbotPromptSettings.query.filter_by(chatbot_id=bot.id).first()
        assert settings is not None
        assert settings.rag_require_citations is True

    def test_CBOT_013_upsert_prompt_settings_update(self, app, db, app_context):
        """
        [CBOT-013] Upsert Prompt Settings - Existierende Settings

        Sollte existierende Settings aktualisieren.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, ChatbotPromptSettings

        bot = Chatbot(
            name='test_upsert_update',
            display_name='Test Bot',
            system_prompt='Test prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.flush()

        settings = ChatbotPromptSettings(chatbot_id=bot.id, rag_require_citations=False)
        db.session.add(settings)
        db.session.commit()

        data = {'prompt_settings': {'rag_require_citations': True}}
        ChatbotService._upsert_prompt_settings(bot, data)
        db.session.commit()

        updated = ChatbotPromptSettings.query.filter_by(chatbot_id=bot.id).first()
        assert updated.rag_require_citations is True

    def test_CBOT_014_upsert_prompt_settings_flat_keys(self, app, db, app_context):
        """
        [CBOT-014] Upsert Prompt Settings - Flat Keys

        Sollte auch flat keys akzeptieren.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, ChatbotPromptSettings

        bot = Chatbot(
            name='test_upsert_flat',
            display_name='Test Bot',
            system_prompt='Test prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.flush()

        data = {'rag_require_citations': True}
        ChatbotService._upsert_prompt_settings(bot, data)
        db.session.commit()

        settings = ChatbotPromptSettings.query.filter_by(chatbot_id=bot.id).first()
        assert settings is not None
        assert settings.rag_require_citations is True

    def test_CBOT_015_upsert_sets_include_sources(self, app, db, app_context):
        """
        [CBOT-015] Upsert Prompt Settings - Include Sources

        Citations benötigen Sources - sollte automatisch gesetzt werden.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_upsert_sources',
            display_name='Test Bot',
            system_prompt='Test prompt',
            created_by='test',
            rag_include_sources=False
        )
        db.session.add(bot)
        db.session.flush()

        data = {'prompt_settings': {'rag_require_citations': True}}
        ChatbotService._upsert_prompt_settings(bot, data)
        db.session.commit()

        assert bot.rag_include_sources is True


class TestCRUDOperations:
    """
    CRUD Operations Tests

    Tests for create, read, update, delete operations.
    """

    def test_CBOT_020_get_all_chatbots_empty(self, app, db, app_context):
        """
        [CBOT-020] Get All Chatbots - Leere Liste

        Sollte leere Liste zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.get_all_chatbots()
        assert isinstance(result, list)

    def test_CBOT_021_get_all_chatbots_with_data(self, app, db, app_context):
        """
        [CBOT-021] Get All Chatbots - Mit Daten

        Sollte alle aktiven Chatbots zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot1 = Chatbot(
            name='test_get_all_1',
            display_name='Test Bot 1',
            system_prompt='Prompt 1',
            created_by='test',
            is_active=True
        )
        bot2 = Chatbot(
            name='test_get_all_2',
            display_name='Test Bot 2',
            system_prompt='Prompt 2',
            created_by='test',
            is_active=False
        )
        db.session.add_all([bot1, bot2])
        db.session.commit()

        result = ChatbotService.get_all_chatbots(include_inactive=False)
        names = [b['name'] for b in result]
        assert 'test_get_all_1' in names
        assert 'test_get_all_2' not in names

    def test_CBOT_022_get_all_chatbots_include_inactive(self, app, db, app_context):
        """
        [CBOT-022] Get All Chatbots - Include Inactive

        Sollte auch inaktive Chatbots zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_get_all_inactive',
            display_name='Test Inactive',
            system_prompt='Prompt',
            created_by='test',
            is_active=False
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotService.get_all_chatbots(include_inactive=True)
        names = [b['name'] for b in result]
        assert 'test_get_all_inactive' in names

    def test_CBOT_023_get_chatbot_exists(self, app, db, app_context):
        """
        [CBOT-023] Get Chatbot - Existiert

        Sollte Chatbot mit allen Details zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_get_single',
            display_name='Test Single',
            system_prompt='Prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotService.get_chatbot(bot.id)
        assert result is not None
        assert result['name'] == 'test_get_single'
        assert result['display_name'] == 'Test Single'
        assert 'collections' in result
        assert 'conversation_count' in result

    def test_CBOT_024_get_chatbot_not_found(self, app, db, app_context):
        """
        [CBOT-024] Get Chatbot - Nicht gefunden

        Sollte None zurückgeben für nicht existierenden Chatbot.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.get_chatbot(99999)
        assert result is None

    def test_CBOT_025_create_chatbot_success(self, app, db, app_context):
        """
        [CBOT-025] Create Chatbot - Erfolgreich

        Sollte neuen Chatbot erstellen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.models.llm_model import LLMModel

        # Create default LLM model
        model = LLMModel(
            model_id='test/default-llm',
            provider='test',
            display_name='Default LLM',
            model_type='llm',
            is_active=True,
            is_default=True,
            context_window=8192,
            max_output_tokens=4096
        )
        db.session.add(model)
        db.session.commit()

        data = {
            'name': 'new_chatbot',
            'display_name': 'New Chatbot',
            'system_prompt': 'You are a helpful assistant.'
        }

        result = ChatbotService.create_chatbot(data, 'test_user')

        assert result is not None
        assert result['name'] == 'new_chatbot'
        assert result['created_by'] == 'test_user'

    def test_CBOT_026_create_chatbot_missing_field(self, app, db, app_context):
        """
        [CBOT-026] Create Chatbot - Fehlendes Feld

        Sollte ValueError für fehlendes Feld werfen.
        """
        from services.chatbot.chatbot_service import ChatbotService

        data = {
            'name': 'incomplete_bot'
            # Missing display_name and system_prompt
        }

        with pytest.raises(ValueError, match="Missing required field"):
            ChatbotService.create_chatbot(data, 'test_user')

    def test_CBOT_027_create_chatbot_duplicate_name(self, app, db, app_context):
        """
        [CBOT-027] Create Chatbot - Doppelter Name

        Sollte ValueError für doppelten Namen werfen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        existing = Chatbot(
            name='duplicate_name',
            display_name='Existing Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        db.session.add(existing)
        db.session.commit()

        data = {
            'name': 'duplicate_name',
            'display_name': 'New Bot',
            'system_prompt': 'New prompt'
        }

        with pytest.raises(ValueError, match="already exists"):
            ChatbotService.create_chatbot(data, 'test_user')

    def test_CBOT_028_create_chatbot_with_collections(self, app, db, app_context):
        """
        [CBOT-028] Create Chatbot - Mit Collections

        Sollte Chatbot mit Collections erstellen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import RAGCollection, ChatbotCollection
        from db.models.llm_model import LLMModel

        model = LLMModel(
            model_id='test/llm-collections',
            provider='test',
            display_name='LLM',
            model_type='llm',
            is_active=True,
            is_default=True,
            context_window=8192,
            max_output_tokens=4096
        )
        db.session.add(model)

        coll = RAGCollection(
            name='test_coll_for_chatbot',
            display_name='Test Collection',
            created_by='test'
        )
        db.session.add(coll)
        db.session.commit()

        data = {
            'name': 'bot_with_collections',
            'display_name': 'Bot with Collections',
            'system_prompt': 'Prompt',
            'collection_ids': [coll.id]
        }

        result = ChatbotService.create_chatbot(data, 'test_user')

        assert len(result['collections']) == 1
        assert result['collections'][0]['name'] == 'test_coll_for_chatbot'

    def test_CBOT_029_update_chatbot_success(self, app, db, app_context):
        """
        [CBOT-029] Update Chatbot - Erfolgreich

        Sollte Chatbot aktualisieren.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_update',
            display_name='Original Name',
            system_prompt='Original prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.commit()

        data = {'display_name': 'Updated Name', 'temperature': 0.5}
        result = ChatbotService.update_chatbot(bot.id, data)

        assert result['display_name'] == 'Updated Name'
        assert result['temperature'] == 0.5

    def test_CBOT_030_update_chatbot_not_found(self, app, db, app_context):
        """
        [CBOT-030] Update Chatbot - Nicht gefunden

        Sollte None für nicht existierenden Chatbot zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.update_chatbot(99999, {'display_name': 'Test'})
        assert result is None

    def test_CBOT_031_update_chatbot_name_conflict(self, app, db, app_context):
        """
        [CBOT-031] Update Chatbot - Name Konflikt

        Sollte ValueError bei Name-Konflikt werfen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot1 = Chatbot(name='bot_one', display_name='Bot 1', system_prompt='P1', created_by='test')
        bot2 = Chatbot(name='bot_two', display_name='Bot 2', system_prompt='P2', created_by='test')
        db.session.add_all([bot1, bot2])
        db.session.commit()

        with pytest.raises(ValueError, match="already exists"):
            ChatbotService.update_chatbot(bot2.id, {'name': 'bot_one'})

    def test_CBOT_032_delete_chatbot_success(self, app, db, app_context):
        """
        [CBOT-032] Delete Chatbot - Erfolgreich

        Sollte Chatbot löschen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_delete',
            display_name='Delete Me',
            system_prompt='Prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.commit()
        bot_id = bot.id

        result = ChatbotService.delete_chatbot(bot_id)
        assert result is True

        # Verify deleted
        assert Chatbot.query.get(bot_id) is None

    def test_CBOT_033_delete_chatbot_not_found(self, app, db, app_context):
        """
        [CBOT-033] Delete Chatbot - Nicht gefunden

        Sollte False zurückgeben für nicht existierenden Chatbot.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.delete_chatbot(99999)
        assert result is False

    def test_CBOT_034_duplicate_chatbot_success(self, app, db, app_context):
        """
        [CBOT-034] Duplicate Chatbot - Erfolgreich

        Sollte Kopie des Chatbots erstellen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot
        from db.models.llm_model import LLMModel

        model = LLMModel(
            model_id='test/llm-dup',
            provider='test',
            display_name='LLM',
            model_type='llm',
            is_active=True,
            is_default=True,
            context_window=8192,
            max_output_tokens=4096
        )
        db.session.add(model)

        original = Chatbot(
            name='original_bot',
            display_name='Original Bot',
            system_prompt='Original prompt',
            model_name='test/llm-dup',
            temperature=0.8,
            created_by='test'
        )
        db.session.add(original)
        db.session.commit()

        result = ChatbotService.duplicate_chatbot(original.id, 'copy_user')

        assert result is not None
        assert result['name'] == 'original_bot-copy'
        assert 'Kopie' in result['display_name']
        assert result['temperature'] == 0.8
        assert result['is_active'] is False
        assert result['created_by'] == 'copy_user'

    def test_CBOT_035_duplicate_chatbot_not_found(self, app, db, app_context):
        """
        [CBOT-035] Duplicate Chatbot - Nicht gefunden

        Sollte None für nicht existierenden Chatbot zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.duplicate_chatbot(99999, 'test_user')
        assert result is None


class TestCollectionManagement:
    """
    Collection Management Tests

    Tests for collection assignment operations.
    """

    def test_CBOT_040_get_collections_empty(self, app, db, app_context):
        """
        [CBOT-040] Get Collections - Keine Collections

        Sollte leere Liste zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='bot_no_collections',
            display_name='No Collections',
            system_prompt='Prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotService.get_collections(bot.id)
        assert result == []

    def test_CBOT_041_get_collections_with_data(self, app, db, app_context):
        """
        [CBOT-041] Get Collections - Mit Daten

        Sollte Collections zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection

        bot = Chatbot(
            name='bot_with_colls',
            display_name='With Collections',
            system_prompt='Prompt',
            created_by='test'
        )
        coll = RAGCollection(
            name='coll_for_get',
            display_name='Collection for Get',
            created_by='test'
        )
        db.session.add_all([bot, coll])
        db.session.flush()

        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            priority=1,
            is_primary=True,
            assigned_by='test'
        )
        db.session.add(cc)
        db.session.commit()

        result = ChatbotService.get_collections(bot.id)
        assert len(result) == 1
        assert result[0]['name'] == 'coll_for_get'
        assert result[0]['is_primary'] is True

    def test_CBOT_042_get_collections_not_found(self, app, db, app_context):
        """
        [CBOT-042] Get Collections - Bot nicht gefunden

        Sollte leere Liste für nicht existierenden Bot zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.get_collections(99999)
        assert result == []

    def test_CBOT_043_assign_collection_success(self, app, db, app_context):
        """
        [CBOT-043] Assign Collection - Erfolgreich

        Sollte Collection zuweisen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, RAGCollection

        bot = Chatbot(
            name='bot_assign',
            display_name='Bot Assign',
            system_prompt='Prompt',
            created_by='test'
        )
        coll = RAGCollection(
            name='coll_assign',
            display_name='Collection Assign',
            created_by='test'
        )
        db.session.add_all([bot, coll])
        db.session.commit()

        result = ChatbotService.assign_collection(
            bot.id, coll.id, 'test_user',
            priority=1, weight=1.5, is_primary=True
        )

        assert result is not None
        assert result['name'] == 'coll_assign'
        assert result['priority'] == 1
        assert result['weight'] == 1.5
        assert result['is_primary'] is True

    def test_CBOT_044_assign_collection_not_found(self, app, db, app_context):
        """
        [CBOT-044] Assign Collection - Nicht gefunden

        Sollte None für nicht existierenden Bot/Collection zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='bot_assign_nf',
            display_name='Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotService.assign_collection(bot.id, 99999, 'test_user')
        assert result is None

    def test_CBOT_045_assign_collection_already_assigned(self, app, db, app_context):
        """
        [CBOT-045] Assign Collection - Bereits zugewiesen

        Sollte ValueError werfen wenn bereits zugewiesen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection

        bot = Chatbot(
            name='bot_assign_dup',
            display_name='Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        coll = RAGCollection(
            name='coll_assign_dup',
            display_name='Collection',
            created_by='test'
        )
        db.session.add_all([bot, coll])
        db.session.flush()

        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='test'
        )
        db.session.add(cc)
        db.session.commit()

        with pytest.raises(ValueError, match="already assigned"):
            ChatbotService.assign_collection(bot.id, coll.id, 'test_user')

    def test_CBOT_046_assign_collection_primary_unsets_others(self, app, db, app_context):
        """
        [CBOT-046] Assign Collection - Primary unsetzt andere

        Bei Primary sollten andere Primary-Flags entfernt werden.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection

        bot = Chatbot(
            name='bot_primary',
            display_name='Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        coll1 = RAGCollection(name='coll_p1', display_name='Coll 1', created_by='test')
        coll2 = RAGCollection(name='coll_p2', display_name='Coll 2', created_by='test')
        db.session.add_all([bot, coll1, coll2])
        db.session.flush()

        # First collection is primary
        cc1 = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll1.id,
            is_primary=True,
            assigned_by='test'
        )
        db.session.add(cc1)
        db.session.commit()

        # Assign second as primary
        ChatbotService.assign_collection(bot.id, coll2.id, 'test', is_primary=True)

        # First should no longer be primary
        updated_cc1 = ChatbotCollection.query.filter_by(
            chatbot_id=bot.id,
            collection_id=coll1.id
        ).first()
        assert updated_cc1.is_primary is False

    def test_CBOT_047_update_collection_assignment_success(self, app, db, app_context):
        """
        [CBOT-047] Update Collection Assignment - Erfolgreich

        Sollte Assignment aktualisieren.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection

        bot = Chatbot(
            name='bot_update_assign',
            display_name='Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        coll = RAGCollection(
            name='coll_update_assign',
            display_name='Collection',
            created_by='test'
        )
        db.session.add_all([bot, coll])
        db.session.flush()

        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            priority=0,
            weight=1.0,
            assigned_by='test'
        )
        db.session.add(cc)
        db.session.commit()

        result = ChatbotService.update_collection_assignment(
            bot.id, coll.id,
            priority=5, weight=2.0
        )

        assert result is not None
        assert result['priority'] == 5
        assert result['weight'] == 2.0

    def test_CBOT_048_update_collection_assignment_not_found(self, app, db, app_context):
        """
        [CBOT-048] Update Collection Assignment - Nicht gefunden

        Sollte None für nicht existierendes Assignment zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.update_collection_assignment(99999, 99999, priority=1)
        assert result is None

    def test_CBOT_049_remove_collection_success(self, app, db, app_context):
        """
        [CBOT-049] Remove Collection - Erfolgreich

        Sollte Collection entfernen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection

        bot = Chatbot(
            name='bot_remove',
            display_name='Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        coll = RAGCollection(
            name='coll_remove',
            display_name='Collection',
            created_by='test'
        )
        db.session.add_all([bot, coll])
        db.session.flush()

        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='test'
        )
        db.session.add(cc)
        db.session.commit()

        result = ChatbotService.remove_collection(bot.id, coll.id)
        assert result is True

        # Verify removed
        assert ChatbotCollection.query.filter_by(
            chatbot_id=bot.id,
            collection_id=coll.id
        ).first() is None

    def test_CBOT_050_remove_collection_not_found(self, app, db, app_context):
        """
        [CBOT-050] Remove Collection - Nicht gefunden

        Sollte False für nicht existierendes Assignment zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.remove_collection(99999, 99999)
        assert result is False


class TestStatistics:
    """
    Statistics Tests

    Tests for statistics methods.
    """

    def test_CBOT_060_get_stats_success(self, app, db, app_context):
        """
        [CBOT-060] Get Stats - Erfolgreich

        Sollte Statistiken für Chatbot zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='bot_stats',
            display_name='Stats Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotService.get_stats(bot.id)

        assert result is not None
        assert result['chatbot_id'] == bot.id
        assert result['chatbot_name'] == 'Stats Bot'
        assert 'total_conversations' in result
        assert 'total_messages' in result
        assert 'avg_response_time_ms' in result
        assert 'collection_count' in result

    def test_CBOT_061_get_stats_not_found(self, app, db, app_context):
        """
        [CBOT-061] Get Stats - Nicht gefunden

        Sollte None für nicht existierenden Chatbot zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService

        result = ChatbotService.get_stats(99999)
        assert result is None

    def test_CBOT_062_get_overview_stats(self, app, db, app_context):
        """
        [CBOT-062] Get Overview Stats

        Sollte globale Statistiken zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='bot_overview',
            display_name='Overview Bot',
            system_prompt='Prompt',
            created_by='test',
            is_active=True
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotService.get_overview_stats()

        assert 'total_chatbots' in result
        assert 'active_chatbots' in result
        assert 'total_conversations' in result
        assert 'total_messages' in result
        assert 'top_chatbots' in result
        assert result['total_chatbots'] >= 1
        assert result['active_chatbots'] >= 1


class TestEdgeCases:
    """
    Edge Cases Tests

    Tests for unusual inputs and edge cases.
    """

    def test_CBOT_080_create_chatbot_no_default_model(self, app, db, app_context):
        """
        [CBOT-080] Create Chatbot - Kein Default Model

        Sollte ValueError werfen wenn kein Default Model konfiguriert.
        """
        from services.chatbot.chatbot_service import ChatbotService

        # Ensure no default model exists
        from db.models.llm_model import LLMModel
        LLMModel.query.filter_by(is_default=True, model_type='llm').update({'is_default': False})
        db.session.commit()

        data = {
            'name': 'no_default_model',
            'display_name': 'No Default Model',
            'system_prompt': 'Prompt'
        }

        with pytest.raises(ValueError, match="No accessible LLM model"):
            ChatbotService.create_chatbot(data, 'test_user')

    def test_CBOT_081_duplicate_chatbot_increments_counter(self, app, db, app_context):
        """
        [CBOT-081] Duplicate Chatbot - Counter Increment

        Bei mehrfachen Kopien sollte Counter inkrementieren.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot
        from db.models.llm_model import LLMModel

        model = LLMModel(
            model_id='test/llm-dup-inc',
            provider='test',
            display_name='LLM',
            model_type='llm',
            is_active=True,
            is_default=True,
            context_window=8192,
            max_output_tokens=4096
        )
        db.session.add(model)

        original = Chatbot(
            name='dup_counter_orig',
            display_name='Original',
            system_prompt='Prompt',
            model_name='test/llm-dup-inc',
            created_by='test'
        )
        db.session.add(original)
        db.session.commit()

        # First copy
        copy1 = ChatbotService.duplicate_chatbot(original.id, 'user')
        assert copy1['name'] == 'dup_counter_orig-copy'

        # Second copy
        copy2 = ChatbotService.duplicate_chatbot(original.id, 'user')
        assert copy2['name'] == 'dup_counter_orig-copy-1'

        # Third copy
        copy3 = ChatbotService.duplicate_chatbot(original.id, 'user')
        assert copy3['name'] == 'dup_counter_orig-copy-2'

    def test_CBOT_082_get_all_with_username_filter(self, app, db, app_context):
        """
        [CBOT-082] Get All Chatbots - Mit Username Filter

        Sollte nur accessible Chatbots für User zurückgeben.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        # Create chatbot
        bot = Chatbot(
            name='user_filter_bot',
            display_name='User Filter Bot',
            system_prompt='Prompt',
            created_by='owner_user',
            is_public=True
        )
        db.session.add(bot)
        db.session.commit()

        # Mock ChatbotAccessService
        with patch('services.chatbot.chatbot_access_service.ChatbotAccessService.get_accessible_chatbots') as mock:
            mock.return_value = [bot]
            result = ChatbotService.get_all_chatbots(username='test_user')
            mock.assert_called_once()

    def test_CBOT_083_delete_chatbot_with_collections(self, app, db, app_context):
        """
        [CBOT-083] Delete Chatbot - Mit Collection Deletion

        Sollte auch Collections löschen wenn gewünscht.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection

        coll = RAGCollection(
            name='coll_for_delete',
            display_name='Collection for Delete',
            created_by='test'
        )
        db.session.add(coll)
        db.session.flush()

        bot = Chatbot(
            name='bot_delete_coll',
            display_name='Bot Delete Coll',
            system_prompt='Prompt',
            created_by='test',
            primary_collection_id=coll.id
        )
        db.session.add(bot)
        db.session.flush()

        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='test'
        )
        db.session.add(cc)
        db.session.commit()

        coll_id = coll.id
        result = ChatbotService.delete_chatbot(bot.id, delete_collections=True)
        assert result is True

        # Collection should be deleted
        assert RAGCollection.query.get(coll_id) is None

    def test_CBOT_084_update_model_with_invalid(self, app, db, app_context):
        """
        [CBOT-084] Update Chatbot - Ungültiges Model

        Sollte ValueError für ungültiges Model werfen.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot

        bot = Chatbot(
            name='bot_invalid_model',
            display_name='Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        db.session.add(bot)
        db.session.commit()

        with pytest.raises(ValueError, match="not an active LLM model"):
            ChatbotService.update_chatbot(bot.id, {'model_name': 'nonexistent/model'})

    def test_CBOT_085_collections_sorted_by_priority(self, app, db, app_context):
        """
        [CBOT-085] Get Collections - Sortiert nach Priority

        Collections sollten nach Priority sortiert sein.
        """
        from services.chatbot.chatbot_service import ChatbotService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection

        bot = Chatbot(
            name='bot_sort',
            display_name='Bot',
            system_prompt='Prompt',
            created_by='test'
        )
        coll1 = RAGCollection(name='coll_sort_1', display_name='Coll 1', created_by='test')
        coll2 = RAGCollection(name='coll_sort_2', display_name='Coll 2', created_by='test')
        coll3 = RAGCollection(name='coll_sort_3', display_name='Coll 3', created_by='test')
        db.session.add_all([bot, coll1, coll2, coll3])
        db.session.flush()

        # Add in non-sorted order
        cc2 = ChatbotCollection(chatbot_id=bot.id, collection_id=coll2.id, priority=2, assigned_by='test')
        cc1 = ChatbotCollection(chatbot_id=bot.id, collection_id=coll1.id, priority=1, assigned_by='test')
        cc3 = ChatbotCollection(chatbot_id=bot.id, collection_id=coll3.id, priority=3, assigned_by='test')
        db.session.add_all([cc2, cc1, cc3])
        db.session.commit()

        result = ChatbotService.get_collections(bot.id)

        priorities = [c['priority'] for c in result]
        assert priorities == [1, 2, 3]
