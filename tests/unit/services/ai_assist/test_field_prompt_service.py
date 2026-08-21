"""
Tests for FieldPromptService - AI-assisted form field prompt management.

Covers:
- seed_defaults: seeding default prompts
- reseed_defaults: updating existing prompts
- CRUD operations (get, create, update, delete)
- render_prompt: template rendering with context
- DEFAULT_FIELD_PROMPTS structure validation
"""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestDefaultFieldPrompts:
    """Test the DEFAULT_FIELD_PROMPTS constant."""

    def test_AI_ASSIST_100_defaults_contain_required_keys(self):
        """AI_ASSIST_100: All default prompts have required fields."""
        from services.ai_assist.field_prompt_service import DEFAULT_FIELD_PROMPTS

        required_keys = {'display_name', 'system_prompt', 'user_prompt_template'}

        for field_key, config in DEFAULT_FIELD_PROMPTS.items():
            for req in required_keys:
                assert req in config, f"Missing '{req}' in {field_key}"

    def test_AI_ASSIST_101_defaults_have_valid_temperatures(self):
        """AI_ASSIST_101: All temperatures are between 0 and 1."""
        from services.ai_assist.field_prompt_service import DEFAULT_FIELD_PROMPTS

        for field_key, config in DEFAULT_FIELD_PROMPTS.items():
            temp = config.get('temperature', 0.7)
            assert 0.0 <= temp <= 1.0, f"Invalid temperature {temp} in {field_key}"

    def test_AI_ASSIST_102_defaults_have_positive_max_tokens(self):
        """AI_ASSIST_102: All max_tokens are positive integers."""
        from services.ai_assist.field_prompt_service import DEFAULT_FIELD_PROMPTS

        for field_key, config in DEFAULT_FIELD_PROMPTS.items():
            max_tokens = config.get('max_tokens', 200)
            assert isinstance(max_tokens, int) and max_tokens > 0

    def test_AI_ASSIST_103_scenario_analysis_prompt_exists(self):
        """AI_ASSIST_103: scenario.analysis prompt exists with full config."""
        from services.ai_assist.field_prompt_service import DEFAULT_FIELD_PROMPTS

        assert 'scenario.analysis' in DEFAULT_FIELD_PROMPTS
        analysis = DEFAULT_FIELD_PROMPTS['scenario.analysis']
        assert analysis['max_tokens'] == 2000
        assert 'preprocessed_data' in analysis['context_variables']

    def test_AI_ASSIST_104_all_keys_follow_naming_convention(self):
        """AI_ASSIST_104: All field_keys follow module.entity.field convention."""
        from services.ai_assist.field_prompt_service import DEFAULT_FIELD_PROMPTS

        for field_key in DEFAULT_FIELD_PROMPTS:
            parts = field_key.split('.')
            assert len(parts) >= 2, f"Key {field_key} doesn't follow convention"


class TestFieldPromptServiceSeedDefaults:
    """Test seed_defaults method."""

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_110_seed_creates_missing_prompts(self, mock_db, mock_fpt):
        """AI_ASSIST_110: seed_defaults creates prompts that don't exist."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_fpt.query.filter_by.return_value.first.return_value = None

        count = FieldPromptService.seed_defaults()

        assert count > 0
        assert mock_db.session.add.call_count == count
        mock_db.session.commit.assert_called_once()

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_111_seed_skips_existing_prompts(self, mock_db, mock_fpt):
        """AI_ASSIST_111: seed_defaults skips already existing prompts."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_fpt.query.filter_by.return_value.first.return_value = MagicMock()

        count = FieldPromptService.seed_defaults()

        assert count == 0
        mock_db.session.add.assert_not_called()


class TestFieldPromptServiceReseedDefaults:
    """Test reseed_defaults method."""

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_120_reseed_updates_existing(self, mock_db, mock_fpt):
        """AI_ASSIST_120: reseed_defaults updates existing prompts."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        existing = MagicMock()
        mock_fpt.query.filter_by.return_value.first.return_value = existing

        result = FieldPromptService.reseed_defaults(
            field_keys=['scenario.settings.name']
        )

        assert result['updated'] == 1
        assert result['created'] == 0

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_121_reseed_creates_new(self, mock_db, mock_fpt):
        """AI_ASSIST_121: reseed_defaults creates prompts that don't exist."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_fpt.query.filter_by.return_value.first.return_value = None

        result = FieldPromptService.reseed_defaults(
            field_keys=['scenario.settings.name']
        )

        assert result['created'] == 1
        assert result['updated'] == 0

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_122_reseed_skips_unknown_keys(self, mock_db, mock_fpt):
        """AI_ASSIST_122: Skips field keys not in DEFAULT_FIELD_PROMPTS."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        result = FieldPromptService.reseed_defaults(
            field_keys=['nonexistent.key.here']
        )

        assert result['created'] == 0
        assert result['updated'] == 0

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_123_reseed_all_when_no_keys_specified(self, mock_db, mock_fpt):
        """AI_ASSIST_123: Reseeds all defaults when no keys specified."""
        from services.ai_assist.field_prompt_service import (
            FieldPromptService, DEFAULT_FIELD_PROMPTS
        )

        mock_fpt.query.filter_by.return_value.first.return_value = None

        result = FieldPromptService.reseed_defaults(field_keys=None)

        assert result['created'] == len(DEFAULT_FIELD_PROMPTS)


class TestFieldPromptServiceCRUD:
    """Test CRUD operations."""

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    def test_AI_ASSIST_130_get_by_field_key_delegates(self, mock_fpt):
        """AI_ASSIST_130: get_by_field_key delegates to model."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_template = MagicMock()
        mock_fpt.get_by_field_key.return_value = mock_template

        result = FieldPromptService.get_by_field_key('scenario.settings.name')

        mock_fpt.get_by_field_key.assert_called_once_with('scenario.settings.name')
        assert result is mock_template

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    def test_AI_ASSIST_131_get_all_returns_ordered(self, mock_fpt):
        """AI_ASSIST_131: get_all returns ordered by field_key."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_fpt.query.order_by.return_value.all.return_value = [MagicMock(), MagicMock()]

        result = FieldPromptService.get_all()
        assert len(result) == 2

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    def test_AI_ASSIST_132_get_all_active_delegates(self, mock_fpt):
        """AI_ASSIST_132: get_all_active delegates to model class method."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_fpt.get_all_active.return_value = [MagicMock()]

        result = FieldPromptService.get_all_active()
        assert len(result) == 1

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_133_create_adds_and_commits(self, mock_db, mock_fpt):
        """AI_ASSIST_133: create adds template and commits."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        result = FieldPromptService.create(
            field_key='test.field',
            display_name='Test Field',
            system_prompt='System prompt',
            user_prompt_template='Hello {name}',
            context_variables=['name'],
            max_tokens=100,
            temperature=0.5,
        )

        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_134_update_modifies_allowed_fields(self, mock_db, mock_fpt):
        """AI_ASSIST_134: update modifies only allowed fields."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_template = MagicMock()
        mock_template.field_key = 'test.field'
        mock_fpt.query.get.return_value = mock_template

        result = FieldPromptService.update(
            template_id=1,
            display_name='Updated Name',
            max_tokens=300,
        )

        assert result is mock_template
        mock_db.session.commit.assert_called_once()

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_135_update_returns_none_for_missing(self, mock_db, mock_fpt):
        """AI_ASSIST_135: update returns None when template not found."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_fpt.query.get.return_value = None

        result = FieldPromptService.update(template_id=999, display_name='X')
        assert result is None

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_136_delete_removes_and_commits(self, mock_db, mock_fpt):
        """AI_ASSIST_136: delete removes template and returns True."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_template = MagicMock()
        mock_template.field_key = 'test.field'
        mock_fpt.query.get.return_value = mock_template

        result = FieldPromptService.delete(template_id=1)

        assert result is True
        mock_db.session.delete.assert_called_once_with(mock_template)
        mock_db.session.commit.assert_called_once()

    @patch('services.ai_assist.field_prompt_service.FieldPromptTemplate')
    @patch('services.ai_assist.field_prompt_service.db')
    def test_AI_ASSIST_137_delete_returns_false_for_missing(self, mock_db, mock_fpt):
        """AI_ASSIST_137: delete returns False when template not found."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_fpt.query.get.return_value = None

        result = FieldPromptService.delete(template_id=999)
        assert result is False


class TestFieldPromptServiceRender:
    """Test prompt rendering."""

    def test_AI_ASSIST_140_render_prompt_delegates_to_model(self):
        """AI_ASSIST_140: render_prompt calls template.render_user_prompt."""
        from services.ai_assist.field_prompt_service import FieldPromptService

        mock_template = MagicMock()
        mock_template.render_user_prompt.return_value = "Rendered prompt"

        context = {'name': 'Test'}
        result = FieldPromptService.render_prompt(mock_template, context)

        mock_template.render_user_prompt.assert_called_once_with(context)
        assert result == "Rendered prompt"
