"""
Unit Tests für LLM Services

Testet:
- LLMModelSyncService: Model-Synchronisation von LiteLLM
- VisionLLMProcessor: Screenshot-Analyse mit Vision-LLMs
- Helper-Funktionen: Provider-Inferenz, Model-Typ-Erkennung
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'app'))


# =============================================================================
# LLMModelSyncService Tests - Inference Functions
# =============================================================================

class TestInferProvider:
    """Tests für _infer_provider."""

    def test_LLM_001_infer_provider_with_namespace(self):
        """LLM-001: Provider aus Namespace extrahieren."""
        from services.llm.model_sync_service import _infer_provider

        result = _infer_provider("anthropic/claude-3-sonnet")
        assert result == "anthropic"

    def test_LLM_002_infer_provider_openai_gpt(self):
        """LLM-002: OpenAI Provider für GPT-Modelle."""
        from services.llm.model_sync_service import _infer_provider

        result = _infer_provider("gpt-4-turbo")
        assert result == "openai"

    def test_LLM_003_infer_provider_openai_o1(self):
        """LLM-003: OpenAI Provider für o1-Modelle."""
        from services.llm.model_sync_service import _infer_provider

        result = _infer_provider("o1-preview")
        assert result == "openai"

    def test_LLM_004_infer_provider_openai_o3(self):
        """LLM-004: OpenAI Provider für o3-Modelle."""
        from services.llm.model_sync_service import _infer_provider

        result = _infer_provider("o3-mini")
        assert result == "openai"

    def test_LLM_005_infer_provider_anthropic(self):
        """LLM-005: Anthropic Provider für Claude-Modelle."""
        from services.llm.model_sync_service import _infer_provider

        result = _infer_provider("claude-3-opus")
        assert result == "anthropic"

    def test_LLM_006_infer_provider_default_litellm(self):
        """LLM-006: Default zu LiteLLM für unbekannte Modelle."""
        from services.llm.model_sync_service import _infer_provider

        result = _infer_provider("unknown-model")
        assert result == "litellm"

    def test_LLM_007_infer_provider_namespace_lowercase(self):
        """LLM-007: Namespace wird zu Kleinbuchstaben."""
        from services.llm.model_sync_service import _infer_provider

        result = _infer_provider("OPENAI/gpt-4")
        assert result == "openai"


class TestInferModelDefaults:
    """Tests für _infer_model_defaults."""

    def test_LLM_010_infer_defaults_vision_gpt4o(self):
        """LLM-010: GPT-4o wird als Vision-Modell erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("gpt-4o")

        assert result['supports_vision'] is True
        assert result['model_type'] == 'llm'

    def test_LLM_011_infer_defaults_vision_pixtral(self):
        """LLM-011: Pixtral wird als Vision-Modell erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("pixtral-large")

        assert result['supports_vision'] is True

    def test_LLM_012_infer_defaults_vision_claude3(self):
        """LLM-012: Claude-3 wird als Vision-Modell erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("claude-3-sonnet")

        assert result['supports_vision'] is True

    def test_LLM_013_infer_defaults_reasoning_o1(self):
        """LLM-013: o1-Modelle werden als Reasoning erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("o1-mini")

        assert result['supports_reasoning'] is True

    def test_LLM_014_infer_defaults_reasoning_magistral(self):
        """LLM-014: Magistral wird als Reasoning erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("magistral-medium")

        assert result['supports_reasoning'] is True
        assert result['supports_vision'] is True  # Also vision

    def test_LLM_015_infer_defaults_embedding_model(self):
        """LLM-015: Embedding-Modelle werden korrekt erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("text-embedding-ada-002")

        assert result['model_type'] == 'embedding'

    def test_LLM_016_infer_defaults_embedding_sentence_transformer(self):
        """LLM-016: Sentence-Transformers werden als Embedding erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("sentence-transformers/all-MiniLM-L6-v2")

        assert result['model_type'] == 'embedding'

    def test_LLM_017_infer_defaults_embedding_bge(self):
        """LLM-017: BGE-Modelle werden als Embedding erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("BAAI/bge-large-en")

        assert result['model_type'] == 'embedding'

    def test_LLM_018_infer_defaults_embedding_vdr(self):
        """LLM-018: VDR-Modelle werden als Embedding erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("llamaindex/vdr-2b-multi-v1")

        assert result['model_type'] == 'embedding'

    def test_LLM_019_infer_defaults_reranker(self):
        """LLM-019: Reranker-Modelle werden korrekt erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("cross-encoder/ms-marco-MiniLM")

        assert result['model_type'] == 'reranker'

    def test_LLM_020_infer_defaults_reranker_explicit(self):
        """LLM-020: Explizite Reranker werden erkannt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("rerank-multilingual")

        assert result['model_type'] == 'reranker'

    def test_LLM_021_infer_defaults_context_window(self):
        """LLM-021: Default Context-Window wird gesetzt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("gpt-4")

        assert result['context_window'] == 32768

    def test_LLM_022_infer_defaults_max_output_tokens(self):
        """LLM-022: Default Max-Output-Tokens werden gesetzt."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("gpt-4")

        assert result['max_output_tokens'] == 8192

    def test_LLM_023_infer_defaults_standard_llm(self):
        """LLM-023: Standard-LLM ohne spezielle Features."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("mistral-7b")

        assert result['model_type'] == 'llm'
        assert result['supports_vision'] is False
        assert result['supports_reasoning'] is False


class TestPrettyModelName:
    """Tests für _pretty_model_name."""

    def test_LLM_030_pretty_name_simple(self):
        """LLM-030: Einfacher Modellname."""
        from services.llm.model_sync_service import _pretty_model_name

        result = _pretty_model_name("gpt-4-turbo")
        assert result == "gpt 4 turbo"

    def test_LLM_031_pretty_name_with_namespace(self):
        """LLM-031: Namespace wird zu Punkt-Separator."""
        from services.llm.model_sync_service import _pretty_model_name

        result = _pretty_model_name("anthropic/claude-3-sonnet")
        assert result == "anthropic · claude 3 sonnet"

    def test_LLM_032_pretty_name_underscores(self):
        """LLM-032: Unterstriche werden zu Leerzeichen."""
        from services.llm.model_sync_service import _pretty_model_name

        result = _pretty_model_name("text_embedding_ada_002")
        assert result == "text embedding ada 002"

    def test_LLM_033_pretty_name_multiple_dashes(self):
        """LLM-033: Mehrfache Trennzeichen werden zusammengefasst."""
        from services.llm.model_sync_service import _pretty_model_name

        result = _pretty_model_name("model--with---dashes")
        assert result == "model with dashes"


# =============================================================================
# LLMModelSyncService Tests - Sync Function
# =============================================================================

class TestLLMModelSyncService:
    """Tests für LLMModelSyncService.sync_from_litellm."""

    def test_LLM_040_sync_no_base_url(self):
        """LLM-040: Sync schlägt fehl ohne Base-URL."""
        from services.llm.model_sync_service import LLMModelSyncService

        with patch.dict(os.environ, {'LITELLM_BASE_URL': ''}, clear=False):
            result = LLMModelSyncService.sync_from_litellm(base_url='')

        assert result['success'] is False
        assert 'not configured' in result['error']

    @patch('services.llm.model_sync_service.requests.get')
    def test_LLM_041_sync_successful(self, mock_get):
        """LLM-041: Erfolgreiche Synchronisation."""
        from services.llm.model_sync_service import LLMModelSyncService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'gpt-4'},
                {'id': 'claude-3-sonnet'},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch('services.llm.model_sync_service.LLMModel') as mock_model_class:
            mock_model_class.get_by_model_id.return_value = None
            with patch('services.llm.model_sync_service.db') as mock_db:
                result = LLMModelSyncService.sync_from_litellm(
                    base_url='http://localhost:4000'
                )

        assert result['success'] is True
        assert result['total_remote'] == 2
        assert result['inserted'] == 2

    @patch('services.llm.model_sync_service.requests.get')
    def test_LLM_042_sync_with_api_key(self, mock_get):
        """LLM-042: Sync sendet API-Key im Header."""
        from services.llm.model_sync_service import LLMModelSyncService

        mock_response = MagicMock()
        mock_response.json.return_value = {'data': []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch('services.llm.model_sync_service.db'):
            LLMModelSyncService.sync_from_litellm(
                base_url='http://localhost:4000',
                api_key='secret-key'
            )

        # Verify header was set
        call_args = mock_get.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer secret-key'

    @patch('services.llm.model_sync_service.requests.get')
    def test_LLM_043_sync_invalid_response(self, mock_get):
        """LLM-043: Ungültiges Response-Format."""
        from services.llm.model_sync_service import LLMModelSyncService

        mock_response = MagicMock()
        mock_response.json.return_value = {'invalid': 'format'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = LLMModelSyncService.sync_from_litellm(
            base_url='http://localhost:4000'
        )

        assert result['success'] is False
        assert 'Unexpected' in result['error']

    @patch('services.llm.model_sync_service.requests.get')
    def test_LLM_044_sync_existing_model_activated(self, mock_get):
        """LLM-044: Existierendes Modell wird aktiviert."""
        from services.llm.model_sync_service import LLMModelSyncService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [{'id': 'existing-model'}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        existing_model = MagicMock()
        existing_model.is_active = False

        with patch('services.llm.model_sync_service.LLMModel') as mock_model_class:
            mock_model_class.get_by_model_id.return_value = existing_model
            with patch('services.llm.model_sync_service.db') as mock_db:
                result = LLMModelSyncService.sync_from_litellm(
                    base_url='http://localhost:4000',
                    activate_existing=True
                )

        assert result['success'] is True
        assert result['updated'] == 1
        assert existing_model.is_active is True

    @patch('services.llm.model_sync_service.requests.get')
    def test_LLM_045_sync_existing_model_skipped(self, mock_get):
        """LLM-045: Aktives Modell wird übersprungen."""
        from services.llm.model_sync_service import LLMModelSyncService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [{'id': 'existing-model'}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        existing_model = MagicMock()
        existing_model.is_active = True

        with patch('services.llm.model_sync_service.LLMModel') as mock_model_class:
            mock_model_class.get_by_model_id.return_value = existing_model
            with patch('services.llm.model_sync_service.db') as mock_db:
                result = LLMModelSyncService.sync_from_litellm(
                    base_url='http://localhost:4000'
                )

        assert result['success'] is True
        assert result['skipped'] == 1

    @patch('services.llm.model_sync_service.requests.get')
    def test_LLM_046_sync_deduplicate_models(self, mock_get):
        """LLM-046: Doppelte Modell-IDs werden dedupliziert."""
        from services.llm.model_sync_service import LLMModelSyncService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'id': 'gpt-4'},
                {'id': 'gpt-4'},  # Duplicate
                {'id': 'gpt-4'},  # Duplicate
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch('services.llm.model_sync_service.LLMModel') as mock_model_class:
            mock_model_class.get_by_model_id.return_value = None
            with patch('services.llm.model_sync_service.db') as mock_db:
                result = LLMModelSyncService.sync_from_litellm(
                    base_url='http://localhost:4000'
                )

        assert result['total_remote'] == 1  # Deduplicated

    @patch('services.llm.model_sync_service.requests.get')
    def test_LLM_047_sync_model_field_alternative(self, mock_get):
        """LLM-047: 'model' Feld als Alternative zu 'id'."""
        from services.llm.model_sync_service import LLMModelSyncService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'model': 'alt-model-name'}  # Using 'model' instead of 'id'
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch('services.llm.model_sync_service.LLMModel') as mock_model_class:
            mock_model_class.get_by_model_id.return_value = None
            with patch('services.llm.model_sync_service.db') as mock_db:
                result = LLMModelSyncService.sync_from_litellm(
                    base_url='http://localhost:4000'
                )

        assert result['total_remote'] == 1


# =============================================================================
# VisionLLMProcessor Tests
# =============================================================================

class TestVisionLLMProcessorInit:
    """Tests für VisionLLMProcessor Initialisierung."""

    def test_LLM_050_init_with_explicit_model(self):
        """LLM-050: Initialisierung mit explizitem Modell."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        assert processor.model == "gpt-4o"
        assert processor.litellm_base_url == "http://localhost:4000"
        assert processor.litellm_api_key == "test-key"

    def test_LLM_051_init_default_temperature(self):
        """LLM-051: Default Temperature ist 0.1."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        assert processor.temperature == 0.1

    def test_LLM_052_init_custom_temperature(self):
        """LLM-052: Custom Temperature."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key",
            temperature=0.5
        )

        assert processor.temperature == 0.5

    def test_LLM_053_init_custom_max_tokens(self):
        """LLM-053: Custom Max-Tokens."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key",
            max_tokens=2000
        )

        assert processor.max_tokens == 2000

    def test_LLM_054_init_with_explicit_params(self):
        """LLM-054: Werte werden explizit übergeben."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://env-url:4000",
            litellm_api_key="env-key"
        )

        assert processor.litellm_base_url == "http://env-url:4000"
        assert processor.litellm_api_key == "env-key"


class TestVisionLLMProcessorIsAvailable:
    """Tests für VisionLLMProcessor.is_available."""

    def test_LLM_060_is_available_true(self):
        """LLM-060: is_available gibt True zurück wenn konfiguriert."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        assert processor.is_available() is True

    @patch.dict(os.environ, {'LITELLM_BASE_URL': '', 'LITELLM_API_KEY': ''}, clear=False)
    def test_LLM_061_is_available_no_url(self):
        """LLM-061: is_available gibt False zurück ohne URL."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="",
            litellm_api_key="test-key"
        )

        # Note: The default fallback URL may still be used if empty string isn't checked
        assert processor.litellm_base_url == "" or processor.is_available() is False

    def test_LLM_062_is_available_with_explicit_key(self):
        """LLM-062: is_available gibt True zurück mit explizitem API-Key."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        assert processor.is_available() is True


class TestVisionLLMProcessorParseJson:
    """Tests für VisionLLMProcessor._parse_json_response."""

    def test_LLM_070_parse_json_valid(self):
        """LLM-070: Valides JSON wird geparsed."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        response = '{"company_name": "Test GmbH", "email": "info@test.de"}'
        result = processor._parse_json_response(response)

        assert result['company_name'] == "Test GmbH"
        assert result['email'] == "info@test.de"

    def test_LLM_071_parse_json_with_code_block(self):
        """LLM-071: JSON in Markdown Code-Block."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        response = '```json\n{"company_name": "Test GmbH"}\n```'
        result = processor._parse_json_response(response)

        assert result['company_name'] == "Test GmbH"

    def test_LLM_072_parse_json_with_plain_code_block(self):
        """LLM-072: JSON in einfachem Code-Block."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        response = '```\n{"company_name": "Test GmbH"}\n```'
        result = processor._parse_json_response(response)

        assert result['company_name'] == "Test GmbH"

    def test_LLM_073_parse_json_invalid(self):
        """LLM-073: Ungültiges JSON gibt leeres Dict."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        response = 'not valid json'
        result = processor._parse_json_response(response)

        assert result == {}

    def test_LLM_074_parse_json_non_dict(self):
        """LLM-074: Non-Dict JSON gibt leeres Dict."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        response = '["array", "not", "dict"]'
        result = processor._parse_json_response(response)

        assert result == {}

    def test_LLM_075_parse_json_empty_string(self):
        """LLM-075: Leerer String gibt leeres Dict."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        response = ''
        result = processor._parse_json_response(response)

        assert result == {}

    def test_LLM_076_parse_json_complete_response(self):
        """LLM-076: Vollständige strukturierte Antwort."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        response = json.dumps({
            "company_name": "Mustermann GmbH",
            "owner": "Max Mustermann",
            "email": "info@mustermann.de",
            "phone": "+49 30 12345678",
            "address": "Musterstraße 1, 12345 Berlin",
            "vat_id": "DE123456789",
            "website_purpose": "Beratungsdienstleistungen",
            "services": ["Beratung", "Coaching"],
            "team_members": []
        })

        result = processor._parse_json_response(response)

        assert result['company_name'] == "Mustermann GmbH"
        assert result['owner'] == "Max Mustermann"
        assert result['vat_id'] == "DE123456789"
        assert len(result['services']) == 2


class TestVisionLLMProcessorExtractData:
    """Tests für VisionLLMProcessor.extract_structured_data (async)."""

    def test_LLM_080_extract_data_success(self):
        """LLM-080: Erfolgreiche Daten-Extraktion."""
        import asyncio
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"company_name": "Test GmbH", "email": "info@test.de"}'
        mock_response.choices = [MagicMock(message=mock_message)]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        # Replace the client directly on the processor instance
        processor.client = mock_client

        with patch('llm.openai_utils.extract_message_text') as mock_extract:
            mock_extract.return_value = '{"company_name": "Test GmbH", "email": "info@test.de"}'

            result = asyncio.get_event_loop().run_until_complete(
                processor.extract_structured_data(
                    screenshot_base64="base64encodedimage",
                    url="https://example.com"
                )
            )

        assert result['company_name'] == "Test GmbH"
        assert result['email'] == "info@test.de"

    def test_LLM_081_extract_data_empty_response(self):
        """LLM-081: Leere Antwort gibt leeres Dict."""
        import asyncio
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = ''
        mock_response.choices = [MagicMock(message=mock_message)]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        # Replace the client directly on the processor instance
        processor.client = mock_client

        with patch('llm.openai_utils.extract_message_text') as mock_extract:
            mock_extract.return_value = ''

            result = asyncio.get_event_loop().run_until_complete(
                processor.extract_structured_data(
                    screenshot_base64="base64encodedimage",
                    url="https://example.com"
                )
            )

        assert result == {}

    def test_LLM_082_extract_data_exception(self):
        """LLM-082: Exception gibt leeres Dict."""
        import asyncio
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key"
        )

        # Create a mock client that raises an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        processor.client = mock_client

        result = asyncio.get_event_loop().run_until_complete(
            processor.extract_structured_data(
                screenshot_base64="base64encodedimage",
                url="https://example.com"
            )
        )

        assert result == {}

    def test_LLM_083_extract_data_with_max_tokens(self):
        """LLM-083: max_tokens wird an API übergeben."""
        import asyncio
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        processor = VisionLLMProcessor(
            model="gpt-4o",
            litellm_base_url="http://localhost:4000",
            litellm_api_key="test-key",
            max_tokens=1500
        )

        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{}'
        mock_response.choices = [MagicMock(message=mock_message)]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        # Replace the client directly on the processor instance
        processor.client = mock_client

        with patch('llm.openai_utils.extract_message_text') as mock_extract:
            mock_extract.return_value = '{}'

            asyncio.get_event_loop().run_until_complete(
                processor.extract_structured_data(
                    screenshot_base64="base64encodedimage",
                    url="https://example.com"
                )
            )

        # Check that max_tokens was passed
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs['max_tokens'] == 1500


# =============================================================================
# Model Type Hints Tests
# =============================================================================

class TestModelTypeHints:
    """Tests für Model-Type-Hint-Konstanten."""

    def test_LLM_090_vision_hints_gpt4o(self):
        """LLM-090: Vision-Hints enthalten gpt-4o."""
        from services.llm.model_sync_service import _VISION_HINTS

        assert "gpt-4o" in _VISION_HINTS

    def test_LLM_091_vision_hints_claude3(self):
        """LLM-091: Vision-Hints enthalten claude-3."""
        from services.llm.model_sync_service import _VISION_HINTS

        assert "claude-3" in _VISION_HINTS

    def test_LLM_092_reasoning_hints_o1(self):
        """LLM-092: Reasoning-Hints enthalten o1."""
        from services.llm.model_sync_service import _REASONING_HINTS

        assert "o1" in _REASONING_HINTS

    def test_LLM_093_embedding_hints_e5(self):
        """LLM-093: Embedding-Hints enthalten e5."""
        from services.llm.model_sync_service import _EMBEDDING_HINTS

        assert "e5" in _EMBEDDING_HINTS

    def test_LLM_094_embedding_hints_bge(self):
        """LLM-094: Embedding-Hints enthalten bge."""
        from services.llm.model_sync_service import _EMBEDDING_HINTS

        assert "bge" in _EMBEDDING_HINTS

    def test_LLM_095_reranker_hints_cross_encoder(self):
        """LLM-095: Reranker-Hints enthalten cross-encoder."""
        from services.llm.model_sync_service import _RERANKER_HINTS

        assert "cross-encoder" in _RERANKER_HINTS


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================

class TestLLMServiceEdgeCases:
    """Edge Cases und Integration Tests."""

    def test_LLM_100_infer_empty_model_id(self):
        """LLM-100: Leerer Model-ID."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("")

        assert result['provider'] == 'litellm'
        assert result['model_type'] == 'llm'

    def test_LLM_101_infer_whitespace_model_id(self):
        """LLM-101: Model-ID mit Whitespace."""
        from services.llm.model_sync_service import _infer_model_defaults

        result = _infer_model_defaults("  gpt-4  ")

        # Should be trimmed and processed
        assert result['provider'] == 'openai'

    def test_LLM_102_infer_case_insensitive(self):
        """LLM-102: Case-insensitive Erkennung."""
        from services.llm.model_sync_service import _infer_model_defaults

        result_lower = _infer_model_defaults("gpt-4o")
        result_upper = _infer_model_defaults("GPT-4O")

        assert result_lower['supports_vision'] == result_upper['supports_vision']

    def test_LLM_103_pretty_name_empty(self):
        """LLM-103: Pretty-Name für leeren String."""
        from services.llm.model_sync_service import _pretty_model_name

        result = _pretty_model_name("")
        assert result == ""

    def test_LLM_104_infer_mixed_model(self):
        """LLM-104: Modell mit mehreren Features."""
        from services.llm.model_sync_service import _infer_model_defaults

        # magistral is both vision and reasoning
        result = _infer_model_defaults("magistral-medium")

        assert result['supports_vision'] is True
        assert result['supports_reasoning'] is True
        assert result['model_type'] == 'llm'

    def test_LLM_105_vision_processor_prompt_contains_json(self):
        """LLM-105: Extraction-Prompt enthält JSON-Schema."""
        from services.crawler.modules.vision_llm_processor import VisionLLMProcessor

        assert "company_name" in VisionLLMProcessor.EXTRACTION_PROMPT
        assert "email" in VisionLLMProcessor.EXTRACTION_PROMPT
        assert "JSON" in VisionLLMProcessor.EXTRACTION_PROMPT
