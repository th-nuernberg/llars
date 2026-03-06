"""
Tests for ChatbotFieldGenerator service.

Covers icon generation, color generation, field generation,
name cleaning, color cleaning, icon cleaning, collection context,
and streaming field generation.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from uuid import uuid4


class TestCleanIcon:
    """Tests for ChatbotFieldGenerator._clean_icon static method."""

    def test_CBFG_001_clean_icon_exact_match(self, app, app_context):
        """[CBFG-001] Exact icon match returns as-is."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_icon('mdi-robot')
        assert result == 'mdi-robot'

    def test_CBFG_002_clean_icon_empty_returns_default(self, app, app_context):
        """[CBFG-002] Empty input returns mdi-robot default."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        assert ChatbotFieldGenerator._clean_icon('') == 'mdi-robot'
        assert ChatbotFieldGenerator._clean_icon(None) == 'mdi-robot'

    def test_CBFG_003_clean_icon_strips_quotes(self, app, app_context):
        """[CBFG-003] Strips quotes and whitespace."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_icon('"mdi-robot"')
        assert result == 'mdi-robot'

    def test_CBFG_004_clean_icon_adds_prefix(self, app, app_context):
        """[CBFG-004] Adds mdi- prefix if missing."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_icon('robot')
        assert result == 'mdi-robot'

    def test_CBFG_005_clean_icon_takes_first_line(self, app, app_context):
        """[CBFG-005] Takes only first line from multi-line response."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_icon('mdi-school\nDieses Icon passt gut')
        assert result == 'mdi-school'

    def test_CBFG_006_clean_icon_takes_first_word(self, app, app_context):
        """[CBFG-006] Takes only first word from multi-word response."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_icon('mdi-school because education')
        assert result == 'mdi-school'

    def test_CBFG_007_clean_icon_removes_trailing_punctuation(self, app, app_context):
        """[CBFG-007] Removes trailing punctuation."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_icon('mdi-school.')
        assert result == 'mdi-school'

    def test_CBFG_008_clean_icon_partial_match(self, app, app_context):
        """[CBFG-008] Falls back to partial match if no exact match."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        # 'mdi-chat-outline' is in ALL_CHATBOT_ICONS, 'chat' is in it
        result = ChatbotFieldGenerator._clean_icon('chat')
        assert result.startswith('mdi-')
        assert 'chat' in result

    def test_CBFG_009_clean_icon_no_match_returns_default(self, app, app_context):
        """[CBFG-009] No match returns default mdi-robot."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_icon('mdi-xyznonexistent1234')
        assert result == 'mdi-robot'

    def test_CBFG_010_clean_icon_case_insensitive(self, app, app_context):
        """[CBFG-010] Matching is case-insensitive."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_icon('MDI-ROBOT')
        assert result == 'mdi-robot'


class TestCleanColor:
    """Tests for ChatbotFieldGenerator._clean_color static method."""

    def test_CBFG_020_clean_color_valid_hex(self, app, app_context):
        """[CBFG-020] Valid hex color passes through."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        assert ChatbotFieldGenerator._clean_color('#3498db') == '#3498db'

    def test_CBFG_021_clean_color_without_hash(self, app, app_context):
        """[CBFG-021] Hex without # prefix gets it added."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        assert ChatbotFieldGenerator._clean_color('3498db') == '#3498db'

    def test_CBFG_022_clean_color_3_digit_expanded(self, app, app_context):
        """[CBFG-022] 3-digit hex expanded to 6-digit."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        assert ChatbotFieldGenerator._clean_color('#abc') == '#aabbcc'

    def test_CBFG_023_clean_color_empty_returns_default(self, app, app_context):
        """[CBFG-023] Empty input returns default color."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        default = ChatbotFieldGenerator.INDUSTRY_COLORS['default']
        assert ChatbotFieldGenerator._clean_color('') == default
        assert ChatbotFieldGenerator._clean_color(None) == default

    def test_CBFG_024_clean_color_strips_quotes(self, app, app_context):
        """[CBFG-024] Strips quotes from LLM output."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        assert ChatbotFieldGenerator._clean_color('"#3498db"') == '#3498db'

    def test_CBFG_025_clean_color_extracts_from_text(self, app, app_context):
        """[CBFG-025] Extracts hex from surrounding text."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_color('The color is #4CAF50 for health')
        assert result == '#4CAF50'

    def test_CBFG_026_clean_color_invalid_returns_default(self, app, app_context):
        """[CBFG-026] Invalid color returns default."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        default = ChatbotFieldGenerator.INDUSTRY_COLORS['default']
        assert ChatbotFieldGenerator._clean_color('no color here') == default


class TestCleanName:
    """Tests for ChatbotFieldGenerator._clean_name static method."""

    def test_CBFG_030_clean_name_basic(self, app, app_context):
        """[CBFG-030] Basic name cleaning works."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        assert ChatbotFieldGenerator._clean_name('My Bot Name') == 'my_bot_name'

    def test_CBFG_031_clean_name_max_length(self, app, app_context):
        """[CBFG-031] Name is truncated to 50 chars."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        long_name = 'a' * 100
        result = ChatbotFieldGenerator._clean_name(long_name)
        assert len(result) == 50

    def test_CBFG_032_clean_name_special_chars(self, app, app_context):
        """[CBFG-032] Special characters replaced with underscore."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        result = ChatbotFieldGenerator._clean_name('Bot-Name (v2)')
        assert result == 'bot_name__v2_'


class TestGetCollectionContext:
    """Tests for ChatbotFieldGenerator._get_collection_context."""

    def test_CBFG_040_no_collection_returns_empty(self, app, db, app_context):
        """[CBFG-040] No primary collection returns default message."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_ctx', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator._get_collection_context(bot)
        assert 'keine Dokumente' in result

    def test_CBFG_041_collection_with_no_documents(self, app, db, app_context):
        """[CBFG-041] Empty collection returns default message."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot, RAGCollection

        collection = RAGCollection(
            name='test_coll', display_name='Test', created_by='admin'
        )
        db.session.add(collection)
        db.session.flush()

        bot = Chatbot(
            name='test_ctx2', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin',
            primary_collection_id=collection.id
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator._get_collection_context(bot)
        assert 'keine Dokumente' in result


class TestGenerateField:
    """Tests for ChatbotFieldGenerator.generate_field."""

    def test_CBFG_050_unknown_field_raises(self, app, db, app_context):
        """[CBFG-050] Unknown field name raises ValueError."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_field', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with pytest.raises(ValueError, match='Unknown field'):
            ChatbotFieldGenerator.generate_field(bot.id, 'nonexistent_field')

    def test_CBFG_051_chatbot_not_found_raises(self, app, db, app_context):
        """[CBFG-051] Nonexistent chatbot raises ValueError."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator

        with pytest.raises(ValueError, match='Chatbot not found'):
            ChatbotFieldGenerator.generate_field(99999, 'name')

    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_with_llm')
    def test_CBFG_052_generate_name_field(self, mock_llm, app, db, app_context):
        """[CBFG-052] Generate name field calls LLM and cleans result."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        mock_llm.return_value = 'My Cool Bot'

        bot = Chatbot(
            name='test_gen', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator.generate_field(bot.id, 'name')
        assert result['success'] is True
        assert result['field'] == 'name'
        assert result['value'] == 'my_cool_bot'
        mock_llm.assert_called_once()

    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_with_llm')
    def test_CBFG_053_generate_description_field(self, mock_llm, app, db, app_context):
        """[CBFG-053] Generate description field returns raw LLM output."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        mock_llm.return_value = 'A helpful assistant for medical questions.'

        bot = Chatbot(
            name='test_desc', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator.generate_field(bot.id, 'description')
        assert result['success'] is True
        assert result['value'] == 'A helpful assistant for medical questions.'

    def test_CBFG_054_generate_icon_delegates(self, app, db, app_context):
        """[CBFG-054] Icon field delegates to generate_icon method."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_icon', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with patch.object(ChatbotFieldGenerator, 'generate_icon', return_value={'success': True, 'field': 'icon', 'value': 'mdi-school'}) as mock_icon:
            result = ChatbotFieldGenerator.generate_field(bot.id, 'icon')
            mock_icon.assert_called_once_with(bot.id, None)
            assert result['value'] == 'mdi-school'

    def test_CBFG_055_generate_color_delegates(self, app, db, app_context):
        """[CBFG-055] Color field delegates to generate_color method."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_color', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with patch.object(ChatbotFieldGenerator, 'generate_color', return_value={'success': True, 'field': 'color', 'value': '#FF0000'}) as mock_color:
            result = ChatbotFieldGenerator.generate_field(bot.id, 'color')
            mock_color.assert_called_once_with(bot.id, None, force_llm=False)
            assert result['value'] == '#FF0000'


class TestGenerateIcon:
    """Tests for ChatbotFieldGenerator.generate_icon."""

    def test_CBFG_060_generate_icon_not_found(self, app, db, app_context):
        """[CBFG-060] Nonexistent chatbot raises ValueError."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        with pytest.raises(ValueError, match='Chatbot not found'):
            ChatbotFieldGenerator.generate_icon(99999)

    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_with_llm')
    def test_CBFG_061_generate_icon_success(self, mock_llm, app, db, app_context):
        """[CBFG-061] Successful icon generation."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        mock_llm.return_value = 'mdi-school'

        bot = Chatbot(
            name='test_icgen', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator.generate_icon(bot.id)
        assert result['success'] is True
        assert result['field'] == 'icon'
        assert result['value'] == 'mdi-school'

    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_with_llm')
    def test_CBFG_062_generate_icon_error_returns_default(self, mock_llm, app, db, app_context):
        """[CBFG-062] LLM error returns default icon."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        mock_llm.side_effect = Exception('LLM unavailable')

        bot = Chatbot(
            name='test_icerr', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator.generate_icon(bot.id)
        assert result['success'] is True
        assert result['value'] == 'mdi-robot'


class TestGenerateColor:
    """Tests for ChatbotFieldGenerator.generate_color."""

    def test_CBFG_070_generate_color_not_found(self, app, db, app_context):
        """[CBFG-070] Nonexistent chatbot raises ValueError."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        with pytest.raises(ValueError, match='Chatbot not found'):
            ChatbotFieldGenerator.generate_color(99999)

    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_color_from_screenshot')
    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_with_llm')
    def test_CBFG_071_color_from_screenshot(self, mock_llm, mock_screenshot, app, db, app_context):
        """[CBFG-071] Color from screenshot takes priority."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        mock_screenshot.return_value = '#FF5733'

        bot = Chatbot(
            name='test_clr_sc', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin', source_url='https://example.com'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator.generate_color(bot.id)
        assert result['success'] is True
        assert result['value'] == '#FF5733'
        assert result['source'] == 'vision'
        mock_llm.assert_not_called()

    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_color_from_screenshot')
    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_with_llm')
    def test_CBFG_072_color_llm_fallback(self, mock_llm, mock_screenshot, app, db, app_context):
        """[CBFG-072] Falls back to LLM when screenshot fails."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        mock_screenshot.return_value = None
        mock_llm.return_value = '#4CAF50'

        bot = Chatbot(
            name='test_clr_fb', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator.generate_color(bot.id)
        assert result['success'] is True
        assert result['value'] == '#4CAF50'
        assert result['source'] == 'llm'

    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_color_from_screenshot')
    @patch('services.chatbot.chatbot_field_generator.ChatbotFieldGenerator._generate_with_llm')
    def test_CBFG_073_color_error_returns_default(self, mock_llm, mock_screenshot, app, db, app_context):
        """[CBFG-073] Error returns default color."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        mock_screenshot.return_value = None
        mock_llm.side_effect = Exception('LLM error')

        bot = Chatbot(
            name='test_clr_err', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotFieldGenerator.generate_color(bot.id)
        assert result['success'] is True
        assert result['source'] == 'fallback'


class TestStreamFieldGeneration:
    """Tests for ChatbotFieldGenerator.stream_field_generation."""

    def test_CBFG_080_stream_icon_yields_done(self, app, db, app_context):
        """[CBFG-080] Streaming icon yields a single done event."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_stream', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with patch.object(ChatbotFieldGenerator, 'generate_icon', return_value={'value': 'mdi-school'}):
            events = list(ChatbotFieldGenerator.stream_field_generation(bot.id, 'icon'))
            assert len(events) == 1
            assert events[0]['done'] is True
            assert events[0]['value'] == 'mdi-school'

    def test_CBFG_081_stream_color_yields_done(self, app, db, app_context):
        """[CBFG-081] Streaming color yields a single done event."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_stream2', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with patch.object(ChatbotFieldGenerator, 'generate_color', return_value={'value': '#FF0000'}):
            events = list(ChatbotFieldGenerator.stream_field_generation(bot.id, 'color'))
            assert len(events) == 1
            assert events[0]['done'] is True

    def test_CBFG_082_stream_unknown_field_raises(self, app, db, app_context):
        """[CBFG-082] Streaming unknown field raises ValueError."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        from db.tables import Chatbot

        bot = Chatbot(
            name='test_stream3', display_name='Test', system_prompt='test',
            model_name='test', created_by='admin'
        )
        db.session.add(bot)
        db.session.commit()

        with pytest.raises(ValueError, match='Unknown field'):
            list(ChatbotFieldGenerator.stream_field_generation(bot.id, 'nonexistent'))

    def test_CBFG_083_stream_not_found_raises(self, app, db, app_context):
        """[CBFG-083] Streaming for nonexistent chatbot raises."""
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        with pytest.raises(ValueError, match='Chatbot not found'):
            list(ChatbotFieldGenerator.stream_field_generation(99999, 'name'))


class TestIconCategories:
    """Tests for icon constants."""

    def test_CBFG_090_all_icons_list_populated(self, app, app_context):
        """[CBFG-090] ALL_CHATBOT_ICONS is populated from all categories."""
        from services.chatbot.chatbot_field_generator import CHATBOT_ICONS, ALL_CHATBOT_ICONS
        total = sum(len(icons) for icons in CHATBOT_ICONS.values())
        assert len(ALL_CHATBOT_ICONS) == total
        assert len(ALL_CHATBOT_ICONS) > 50

    def test_CBFG_091_all_icons_start_with_mdi(self, app, app_context):
        """[CBFG-091] All icons start with mdi- prefix."""
        from services.chatbot.chatbot_field_generator import ALL_CHATBOT_ICONS
        for icon in ALL_CHATBOT_ICONS:
            assert icon.startswith('mdi-'), f"Icon {icon} missing mdi- prefix"

    def test_CBFG_092_industry_colors_valid_hex(self, app, app_context):
        """[CBFG-092] All industry colors are valid hex codes."""
        import re
        from services.chatbot.chatbot_field_generator import ChatbotFieldGenerator
        for name, color in ChatbotFieldGenerator.INDUSTRY_COLORS.items():
            assert re.match(r'^#[0-9A-Fa-f]{6}$', color), f"Invalid color for {name}: {color}"
