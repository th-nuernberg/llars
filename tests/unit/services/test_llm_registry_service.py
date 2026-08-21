"""
Unit tests for llm_registry_service.

Tests the central model registry resolver including:
- Resolving Global (seeded) model metadata from DB
- Resolving user-provider model metadata with batch provider lookup
- Handling unknown model IDs with fallback colors
"""

import pytest
from unittest.mock import patch, MagicMock

from services.llm_registry_service import resolve_model_registry
from db.models.llm_model import LLMModel


class TestResolveModelRegistryEmpty:
    """Tests for edge cases with empty or missing inputs."""

    def test_LLM_REG_001_returns_empty_dict_for_empty_list(self, app, db, app_context):
        """[LLM_REG-001] Should return empty dict when no model IDs provided."""
        result = resolve_model_registry([])
        assert result == {}

    def test_LLM_REG_002_returns_empty_dict_for_none_coerced(self, app, db, app_context):
        """[LLM_REG-002] Should return empty dict for falsy input."""
        result = resolve_model_registry([])
        assert result == {}


class TestResolveGlobalModels:
    """Tests for resolving Global (seeded) LLM models from the DB."""

    def test_LLM_REG_003_resolves_global_model_from_db(self, app, db, app_context):
        """[LLM_REG-003] Should resolve display_name and color from DB for known models."""
        model = LLMModel(
            model_id='Global/OpenAI/gpt-5-nano',
            display_name='GPT-5 Nano',
            provider='openai',
            model_type=LLMModel.MODEL_TYPE_LLM,
            color='#1E88E5',
            context_window=4096,
            max_output_tokens=1024,
            input_cost_per_million=0.0,
            output_cost_per_million=0.0,
            is_default=False,
            is_active=True,
        )
        db.session.add(model)
        db.session.commit()

        registry = resolve_model_registry(['Global/OpenAI/gpt-5-nano'])

        assert 'Global/OpenAI/gpt-5-nano' in registry
        entry = registry['Global/OpenAI/gpt-5-nano']
        assert entry['display_name'] == 'GPT-5 Nano'
        assert entry['color'] == '#1E88E5'
        assert entry['user_provider_name'] is None

    def test_LLM_REG_004_uses_generated_color_when_db_color_is_none(self, app, db, app_context):
        """[LLM_REG-004] Should fall back to generated color when model has no stored color."""
        model = LLMModel(
            model_id='Global/Mistral/test-model',
            display_name='Test Model',
            provider='litellm',
            model_type=LLMModel.MODEL_TYPE_LLM,
            color=None,
            context_window=4096,
            max_output_tokens=1024,
            input_cost_per_million=0.0,
            output_cost_per_million=0.0,
            is_default=False,
            is_active=True,
        )
        db.session.add(model)
        db.session.commit()

        registry = resolve_model_registry(['Global/Mistral/test-model'])
        entry = registry['Global/Mistral/test-model']

        # Should have a generated color (non-None hex string)
        assert entry['color'] is not None
        assert entry['color'].startswith('#')
        assert len(entry['color']) == 7

    def test_LLM_REG_005_deduplicates_model_ids(self, app, db, app_context):
        """[LLM_REG-005] Should handle duplicate model IDs without duplicate entries."""
        model = LLMModel(
            model_id='Global/OpenAI/gpt-5-mini',
            display_name='GPT-5 Mini',
            provider='openai',
            model_type=LLMModel.MODEL_TYPE_LLM,
            color='#FB8C00',
            context_window=4096,
            max_output_tokens=1024,
            input_cost_per_million=0.0,
            output_cost_per_million=0.0,
            is_default=False,
            is_active=True,
        )
        db.session.add(model)
        db.session.commit()

        registry = resolve_model_registry([
            'Global/OpenAI/gpt-5-mini',
            'Global/OpenAI/gpt-5-mini',
            'Global/OpenAI/gpt-5-mini',
        ])

        assert len(registry) == 1
        assert 'Global/OpenAI/gpt-5-mini' in registry


class TestResolveUserProviderModels:
    """Tests for resolving user-provider model IDs."""

    def test_LLM_REG_006_resolves_user_provider_with_db_lookup(self, app, db, app_context):
        """[LLM_REG-006] Should resolve user_provider_name from UserLLMProvider table."""
        from db.models.user import User
        from db.models.user_llm_provider import UserLLMProvider

        user = User(username='provider_owner', password_hash='x', api_key='prov_key')
        db.session.add(user)
        db.session.commit()

        provider = UserLLMProvider(
            user_id=user.id,
            provider_type='openai_compatible',
            name='My IONOS',
        )
        db.session.add(provider)
        db.session.commit()

        model_id = f'user-provider:{provider.id}:provider_owner:llama3'
        registry = resolve_model_registry([model_id])

        assert model_id in registry
        entry = registry[model_id]
        assert entry['user_provider_name'] == 'My IONOS'
        assert entry['display_name'] == model_id
        assert entry['color'].startswith('#')

    def test_LLM_REG_007_handles_missing_user_provider(self, app, db, app_context):
        """[LLM_REG-007] Should set user_provider_name to None for non-existent provider ID."""
        model_id = 'user-provider:99999:unknown_user:some-model'
        registry = resolve_model_registry([model_id])

        assert model_id in registry
        entry = registry[model_id]
        assert entry['user_provider_name'] is None
        assert entry['display_name'] == model_id

    def test_LLM_REG_008_handles_malformed_user_provider_id(self, app, db, app_context):
        """[LLM_REG-008] Should handle user-provider ID with non-numeric provider part."""
        model_id = 'user-provider:notanumber:user:model'
        registry = resolve_model_registry([model_id])

        assert model_id in registry
        entry = registry[model_id]
        assert entry['user_provider_name'] is None


class TestResolveUnknownModels:
    """Tests for unknown model IDs that are neither in DB nor user-provider."""

    def test_LLM_REG_009_returns_fallback_for_unknown_model(self, app, db, app_context):
        """[LLM_REG-009] Should return model_id as display_name with generated color."""
        registry = resolve_model_registry(['some/unknown/model'])

        assert 'some/unknown/model' in registry
        entry = registry['some/unknown/model']
        assert entry['display_name'] == 'some/unknown/model'
        assert entry['color'].startswith('#')
        assert entry['user_provider_name'] is None

    def test_LLM_REG_010_resolves_mixed_model_types(self, app, db, app_context):
        """[LLM_REG-010] Should batch-resolve a mix of Global, user-provider, and unknown models."""
        from db.models.user import User
        from db.models.user_llm_provider import UserLLMProvider

        # Global model in DB
        global_model = LLMModel(
            model_id='Global/OpenAI/gpt-5-nano',
            display_name='GPT-5 Nano',
            provider='openai',
            model_type=LLMModel.MODEL_TYPE_LLM,
            color='#1E88E5',
            context_window=4096,
            max_output_tokens=1024,
            input_cost_per_million=0.0,
            output_cost_per_million=0.0,
            is_default=False,
            is_active=True,
        )
        db.session.add(global_model)
        db.session.commit()

        # User provider
        user = User(username='mix_user', password_hash='x', api_key='mix_key')
        db.session.add(user)
        db.session.commit()

        provider = UserLLMProvider(
            user_id=user.id,
            provider_type='ollama',
            name='Local Ollama',
        )
        db.session.add(provider)
        db.session.commit()

        user_model_id = f'user-provider:{provider.id}:mix_user:mistral'

        registry = resolve_model_registry([
            'Global/OpenAI/gpt-5-nano',
            user_model_id,
            'totally/unknown',
        ])

        assert len(registry) == 3
        assert registry['Global/OpenAI/gpt-5-nano']['display_name'] == 'GPT-5 Nano'
        assert registry[user_model_id]['user_provider_name'] == 'Local Ollama'
        assert registry['totally/unknown']['display_name'] == 'totally/unknown'
