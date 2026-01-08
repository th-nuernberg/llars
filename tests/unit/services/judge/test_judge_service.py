"""
Unit Tests: Judge Service
=========================

Tests for the LLM-as-Judge evaluation service.

Test IDs:
- JUDGE-001 to JUDGE-010: Initialization Tests
- JUDGE-020 to JUDGE-030: Format/Parse Tests
- JUDGE-040 to JUDGE-055: Transform Response Tests
- JUDGE-060 to JUDGE-070: Evaluation Tests (mocked)
- JUDGE-080 to JUDGE-090: Schema Tests
- JUDGE-100 to JUDGE-110: Edge Cases

Status: Implemented
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock


class TestJudgeServiceInitialization:
    """
    Initialization Tests

    Tests for JudgeService constructor and configuration.
    """

    def test_JUDGE_001_init_with_explicit_api_key(self, app, app_context):
        """
        [JUDGE-001] Initialisierung mit explizitem API Key

        Service sollte explizit übergebenen API Key verwenden.
        """
        with patch('services.judge.judge_service.OpenAI'):
            from services.judge.judge_service import JudgeService
            from db.models.llm_model import LLMModel

            with patch.object(LLMModel, 'get_default_model_id', return_value='test/model'):
                service = JudgeService(api_key='test-key-123', base_url='http://test.local/v1')
                assert service.api_key == 'test-key-123'

    def test_JUDGE_002_init_with_explicit_params(self, app, app_context):
        """
        [JUDGE-002] Initialisierung mit expliziten Parametern

        Explizite Parameter sollten env vars überschreiben.
        """
        with patch('services.judge.judge_service.OpenAI'):
            from services.judge.judge_service import JudgeService

            service = JudgeService(
                api_key='explicit-key',
                base_url='http://test.local/v1',
                model='test/explicit-model'
            )
            assert service.api_key == 'explicit-key'
            assert service.base_url == 'http://test.local/v1'
            assert service.model == 'test/explicit-model'

    def test_JUDGE_003_init_no_default_model_raises(self, app, app_context):
        """
        [JUDGE-003] Initialisierung ohne Default-Modell

        Sollte ValueError werfen wenn kein Default LLM-Modell konfiguriert.
        """
        from services.judge.judge_service import JudgeService
        from db.models.llm_model import LLMModel

        with patch.object(LLMModel, 'get_default_model_id', return_value=None):
            with pytest.raises(ValueError, match="No default LLM model"):
                JudgeService()

    def test_JUDGE_004_init_with_provider_client(self, app, app_context):
        """
        [JUDGE-004] Initialisierung mit Provider Client

        Sollte LLMClientFactory verwenden wenn keine expliziten Parameter.
        """
        from services.judge.judge_service import JudgeService
        from services.judge.judge_service import LLMClientFactory
        from db.models.llm_model import LLMModel

        mock_client = MagicMock()
        with patch.object(LLMModel, 'get_default_model_id', return_value='test/model'):
            with patch.object(LLMClientFactory, 'get_client_for_model', return_value=mock_client):
                service = JudgeService()
                assert service.client == mock_client
                assert service.model == 'test/model'

    def test_JUDGE_005_init_no_default_model_raises(self, app, db, app_context):
        """
        [JUDGE-005] Initialisierung ohne Default Model

        Sollte ValueError werfen wenn kein Default Model.
        """
        from db.models.llm_model import LLMModel

        # Ensure no default model
        LLMModel.query.filter_by(is_default=True, model_type='llm').update({'is_default': False})
        db.session.commit()

        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                with pytest.raises(ValueError, match="No default LLM model"):
                    JudgeService()


class TestFormatAndParse:
    """
    Format and Parse Tests

    Tests for thread formatting and response parsing.
    """

    def test_JUDGE_020_format_thread_basic(self, app, app_context):
        """
        [JUDGE-020] Format Thread - Basis

        Sollte Thread korrekt formatieren.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                messages = [
                    {'content': 'Hallo, ich brauche Hilfe.', 'is_counsellor': False},
                    {'content': 'Guten Tag, wie kann ich helfen?', 'is_counsellor': True}
                ]

                result = service.format_thread_for_prompt(messages)

                assert 'RATSUCHENDE' in result
                assert 'BERATER' in result
                assert 'ich brauche Hilfe' in result
                assert 'wie kann ich helfen' in result

    def test_JUDGE_021_format_thread_long_message_truncated(self, app, app_context):
        """
        [JUDGE-021] Format Thread - Lange Nachricht gekürzt

        Sehr lange Nachrichten sollten gekürzt werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                messages = [
                    {'content': 'x' * 3000, 'is_counsellor': False}
                ]

                result = service.format_thread_for_prompt(messages)

                assert '[gekürzt]' in result
                assert len(result) < 3000

    def test_JUDGE_022_format_thread_empty(self, app, app_context):
        """
        [JUDGE-022] Format Thread - Leer

        Leere Nachrichtenliste sollte leeren String ergeben.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')
                result = service.format_thread_for_prompt([])

                assert result == ''

    def test_JUDGE_023_parse_response_valid_json(self, app, app_context):
        """
        [JUDGE-023] Parse Response - Valides JSON

        Valide JSON Response sollte geparsed werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                response = json.dumps({
                    "chain_of_thought": {
                        "step_1_overview": "x" * 50,
                        "step_2_strengths_a": "x" * 30,
                        "step_3_strengths_b": "x" * 30,
                        "step_4_weaknesses_a": "x" * 20,
                        "step_5_weaknesses_b": "x" * 20,
                        "step_6_comparison": "x" * 50
                    },
                    "criteria_scores": {
                        "counsellor_coherence": {"score_a": 4.0, "score_b": 3.5, "reasoning": "Test reasoning"},
                        "client_coherence": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning"},
                        "quality": {"score_a": 3.5, "score_b": 4.0, "reasoning": "Test reasoning"},
                        "empathy": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning"},
                        "authenticity": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning"},
                        "solution_orientation": {"score_a": 3.5, "score_b": 4.5, "reasoning": "Test reasoning"}
                    },
                    "winner": "A",
                    "confidence": 0.75,
                    "final_justification": "x" * 60
                })

                result = service._parse_response(response)

                assert result.winner == "A"
                assert result.confidence == 0.75

    def test_JUDGE_024_parse_response_markdown_code_block(self, app, app_context):
        """
        [JUDGE-024] Parse Response - Markdown Code Block

        JSON in Markdown Code Block sollte geparsed werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                # Use step_X format which will be transformed
                response = '''```json
{
    "step_1": "Overview text that is long enough for validation here",
    "step_2": "Strengths A text here",
    "step_3": "Strengths B text here",
    "step_4": "Weaknesses A text",
    "step_5": "Weaknesses B text",
    "step_6": "Comparison text that is long enough for validation",
    "scores": {
        "A": {"counsellor_coherence": 4, "client_coherence": 4, "quality": 4, "empathy": 4, "authenticity": 4, "solution_orientation": 4},
        "B": {"counsellor_coherence": 3, "client_coherence": 3, "quality": 3, "empathy": 3, "authenticity": 3, "solution_orientation": 3}
    },
    "winner": "A",
    "confidence": 0.8,
    "final_justification": "A was better overall because of many reasons and good things."
}
```'''

                result = service._parse_response(response)
                assert result.winner == "A"

    def test_JUDGE_025_parse_response_invalid_json(self, app, app_context):
        """
        [JUDGE-025] Parse Response - Ungültiges JSON

        Ungültiges JSON sollte ValueError werfen.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                with pytest.raises(ValueError, match="Failed to parse"):
                    service._parse_response("not valid json {{{")


class TestTransformResponse:
    """
    Transform Response Tests

    Tests for LLM response transformation.
    """

    def test_JUDGE_040_transform_step_format(self, app, app_context):
        """
        [JUDGE-040] Transform - Step Format

        step_1 bis step_6 Format sollte transformiert werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                data = {
                    "step_1": "Overview " * 10,
                    "step_2": "Strengths A " * 5,
                    "step_3": "Strengths B " * 5,
                    "step_4": "Weaknesses A " * 3,
                    "step_5": "Weaknesses B " * 3,
                    "step_6": "Comparison " * 10,
                    "scores": {
                        "A": {"counsellor_coherence": 4, "client_coherence": 4, "quality": 4, "empathy": 4, "authenticity": 4, "solution_orientation": 4},
                        "B": {"counsellor_coherence": 3, "client_coherence": 3, "quality": 3, "empathy": 3, "authenticity": 3, "solution_orientation": 3}
                    },
                    "winner": "A",
                    "confidence": 0.8,
                    "final_justification": "A is better because of multiple factors considered."
                }

                result = service._transform_llm_response(data)

                assert "chain_of_thought" in result
                assert "criteria_scores" in result
                assert result["winner"] == "A"

    def test_JUDGE_041_transform_already_correct_format(self, app, app_context):
        """
        [JUDGE-041] Transform - Bereits korrektes Format

        Korrekt formatierte Daten sollten unverändert bleiben.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                data = {
                    "chain_of_thought": {
                        "step_1_overview": "x" * 60,
                        "step_2_strengths_a": "x" * 35,
                        "step_3_strengths_b": "x" * 35,
                        "step_4_weaknesses_a": "x" * 25,
                        "step_5_weaknesses_b": "x" * 25,
                        "step_6_comparison": "x" * 60
                    },
                    "criteria_scores": {
                        "counsellor_coherence": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"},
                        "client_coherence": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"},
                        "quality": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"},
                        "empathy": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"},
                        "authenticity": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"},
                        "solution_orientation": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"}
                    },
                    "winner": "B",
                    "confidence": 0.9,
                    "final_justification": "B is better for these reasons which are explained here."
                }

                result = service._transform_llm_response(data)
                assert result == data

    def test_JUDGE_042_transform_invalid_winner(self, app, app_context):
        """
        [JUDGE-042] Transform - Ungültiger Winner

        Ungültiger Winner sollte zu TIE werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                data = {
                    "step_1": "Test " * 20,
                    "scores": {"A": {}, "B": {}},
                    "winner": "INVALID",
                    "confidence": 0.5
                }

                result = service._transform_llm_response(data)
                assert result["winner"] == "TIE"

    def test_JUDGE_043_transform_clamps_confidence(self, app, app_context):
        """
        [JUDGE-043] Transform - Confidence Clipping

        Confidence außerhalb [0,1] sollte geclippt werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                # Test > 1
                data1 = {"step_1": "Test " * 20, "scores": {"A": {}, "B": {}}, "winner": "A", "confidence": 1.5}
                result1 = service._transform_llm_response(data1)
                assert result1["confidence"] == 1.0

                # Test < 0
                data2 = {"step_1": "Test " * 20, "scores": {"A": {}, "B": {}}, "winner": "A", "confidence": -0.5}
                result2 = service._transform_llm_response(data2)
                assert result2["confidence"] == 0.0

    def test_JUDGE_044_transform_builds_justification(self, app, app_context):
        """
        [JUDGE-044] Transform - Justification Build

        Fehlende Justification sollte gebaut werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                data = {
                    "step_1": "First analysis point for the comparison here",
                    "step_2": "Second analysis point here",
                    "scores": {"A": {}, "B": {}},
                    "winner": "A",
                    "confidence": 0.7
                }

                result = service._transform_llm_response(data)
                assert len(result["final_justification"]) >= 50


class TestEvaluationMocked:
    """
    Evaluation Tests (Mocked)

    Tests for evaluation methods with mocked API calls.
    """

    def test_JUDGE_060_evaluate_pair_success(self, app, app_context):
        """
        [JUDGE-060] Evaluate Pair - Erfolgreich

        Evaluation sollte Result zurückgeben.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI') as MockOpenAI:
                from services.judge.judge_service import JudgeService

                # Mock response
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps({
                    "chain_of_thought": {
                        "step_1_overview": "x" * 60,
                        "step_2_strengths_a": "x" * 35,
                        "step_3_strengths_b": "x" * 35,
                        "step_4_weaknesses_a": "x" * 25,
                        "step_5_weaknesses_b": "x" * 25,
                        "step_6_comparison": "x" * 60
                    },
                    "criteria_scores": {
                        "counsellor_coherence": {"score_a": 4.0, "score_b": 3.5, "reasoning": "Test reasoning"},
                        "client_coherence": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning"},
                        "quality": {"score_a": 3.5, "score_b": 4.0, "reasoning": "Test reasoning"},
                        "empathy": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning"},
                        "authenticity": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning"},
                        "solution_orientation": {"score_a": 3.5, "score_b": 4.5, "reasoning": "Test reasoning"}
                    },
                    "winner": "A",
                    "confidence": 0.75,
                    "final_justification": "A won because of better overall quality in multiple areas."
                })
                mock_response.usage = MagicMock(total_tokens=1000)

                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                MockOpenAI.return_value = mock_client

                service = JudgeService(api_key='test', model='test/model')

                thread_a = [{'content': 'Hallo', 'is_counsellor': False}]
                thread_b = [{'content': 'Hi', 'is_counsellor': False}]

                result, metadata = service.evaluate_pair(
                    thread_a, thread_b,
                    pillar_a=1, pillar_b=2
                )

                assert result.winner == "A"
                assert result.confidence == 0.75
                assert "latency_ms" in metadata
                assert "aggregate_scores" in metadata

    def test_JUDGE_061_evaluate_pair_with_streaming(self, app, app_context):
        """
        [JUDGE-061] Evaluate Pair - Mit Streaming

        Streaming Callback sollte aufgerufen werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI') as MockOpenAI:
                from services.judge.judge_service import JudgeService

                # Mock streaming response
                response_json = json.dumps({
                    "chain_of_thought": {
                        "step_1_overview": "x" * 60,
                        "step_2_strengths_a": "x" * 35,
                        "step_3_strengths_b": "x" * 35,
                        "step_4_weaknesses_a": "x" * 25,
                        "step_5_weaknesses_b": "x" * 25,
                        "step_6_comparison": "x" * 60
                    },
                    "criteria_scores": {
                        "counsellor_coherence": {"score_a": 4.0, "score_b": 3.5, "reasoning": "Test reasoning text"},
                        "client_coherence": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning text"},
                        "quality": {"score_a": 3.5, "score_b": 4.0, "reasoning": "Test reasoning text"},
                        "empathy": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"},
                        "authenticity": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning text"},
                        "solution_orientation": {"score_a": 3.5, "score_b": 4.5, "reasoning": "Test reasoning text"}
                    },
                    "winner": "B",
                    "confidence": 0.8,
                    "final_justification": "B won because of the better solution orientation shown."
                })

                # Split into chunks
                chunks = []
                for char in response_json:
                    mock_chunk = MagicMock()
                    mock_chunk.choices = [MagicMock()]
                    mock_chunk.choices[0].delta.content = char
                    chunks.append(mock_chunk)

                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = iter(chunks)
                MockOpenAI.return_value = mock_client

                service = JudgeService(api_key='test', model='test/model')

                received_chunks = []
                def callback(chunk):
                    received_chunks.append(chunk)

                thread_a = [{'content': 'Test', 'is_counsellor': False}]
                thread_b = [{'content': 'Test', 'is_counsellor': False}]

                result, _ = service.evaluate_pair(
                    thread_a, thread_b,
                    pillar_a=1, pillar_b=2,
                    stream_callback=callback
                )

                assert result.winner == "B"
                assert len(received_chunks) > 0

    def test_JUDGE_062_evaluate_with_position_swap(self, app, app_context):
        """
        [JUDGE-062] Evaluate with Position Swap - Agreement

        Position-swap mit Agreement sollte gleichen Winner zurückgeben.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI') as MockOpenAI:
                from services.judge.judge_service import JudgeService

                def create_mock_response(winner):
                    mock_response = MagicMock()
                    mock_response.choices = [MagicMock()]
                    mock_response.choices[0].message.content = json.dumps({
                        "chain_of_thought": {
                            "step_1_overview": "x" * 60,
                            "step_2_strengths_a": "x" * 35,
                            "step_3_strengths_b": "x" * 35,
                            "step_4_weaknesses_a": "x" * 25,
                            "step_5_weaknesses_b": "x" * 25,
                            "step_6_comparison": "x" * 60
                        },
                        "criteria_scores": {
                            "counsellor_coherence": {"score_a": 4.0, "score_b": 3.5, "reasoning": "Test reasoning text"},
                            "client_coherence": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning text"},
                            "quality": {"score_a": 3.5, "score_b": 4.0, "reasoning": "Test reasoning text"},
                            "empathy": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"},
                            "authenticity": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning text"},
                            "solution_orientation": {"score_a": 3.5, "score_b": 4.5, "reasoning": "Test reasoning text"}
                        },
                        "winner": winner,
                        "confidence": 0.8,
                        "final_justification": f"{winner} won for multiple reasons explained here in detail with comprehensive analysis."
                    })
                    mock_response.usage = MagicMock(total_tokens=1000)
                    return mock_response

                mock_client = MagicMock()
                # First call: A wins, Second call: B wins (which means A wins in original order)
                mock_client.chat.completions.create.side_effect = [
                    create_mock_response("A"),
                    create_mock_response("B")  # In swapped order, B means A in original
                ]
                MockOpenAI.return_value = mock_client

                service = JudgeService(api_key='test', model='test/model')

                thread_a = [{'content': 'Test A', 'is_counsellor': False}]
                thread_b = [{'content': 'Test B', 'is_counsellor': False}]

                result_ab, result_ba, final_winner, swap_meta = service.evaluate_with_position_swap(
                    thread_a, thread_b, pillar_a=1, pillar_b=2
                )

                assert final_winner == "A"
                assert swap_meta["agreement"] is True

    def test_JUDGE_063_evaluate_with_position_swap_bias_detected(self, app, app_context):
        """
        [JUDGE-063] Evaluate with Position Swap - Bias Detected

        Bei unterschiedlichen Ergebnissen sollte TIE zurückgegeben werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI') as MockOpenAI:
                from services.judge.judge_service import JudgeService

                def create_mock_response(winner):
                    mock_response = MagicMock()
                    mock_response.choices = [MagicMock()]
                    mock_response.choices[0].message.content = json.dumps({
                        "chain_of_thought": {
                            "step_1_overview": "x" * 60,
                            "step_2_strengths_a": "x" * 35,
                            "step_3_strengths_b": "x" * 35,
                            "step_4_weaknesses_a": "x" * 25,
                            "step_5_weaknesses_b": "x" * 25,
                            "step_6_comparison": "x" * 60
                        },
                        "criteria_scores": {
                            "counsellor_coherence": {"score_a": 4.0, "score_b": 3.5, "reasoning": "Test reasoning text"},
                            "client_coherence": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning text"},
                            "quality": {"score_a": 3.5, "score_b": 4.0, "reasoning": "Test reasoning text"},
                            "empathy": {"score_a": 4.0, "score_b": 3.0, "reasoning": "Test reasoning text"},
                            "authenticity": {"score_a": 4.0, "score_b": 4.0, "reasoning": "Test reasoning text"},
                            "solution_orientation": {"score_a": 3.5, "score_b": 4.5, "reasoning": "Test reasoning text"}
                        },
                        "winner": winner,
                        "confidence": 0.6,
                        "final_justification": f"{winner} won but with uncertainty in the decision and multiple factors considered."
                    })
                    mock_response.usage = MagicMock(total_tokens=1000)
                    return mock_response

                mock_client = MagicMock()
                # Both calls say A wins - position bias!
                mock_client.chat.completions.create.side_effect = [
                    create_mock_response("A"),
                    create_mock_response("A")  # Should be B if consistent
                ]
                MockOpenAI.return_value = mock_client

                service = JudgeService(api_key='test', model='test/model')

                thread_a = [{'content': 'Test A', 'is_counsellor': False}]
                thread_b = [{'content': 'Test B', 'is_counsellor': False}]

                result_ab, result_ba, final_winner, swap_meta = service.evaluate_with_position_swap(
                    thread_a, thread_b, pillar_a=1, pillar_b=2
                )

                assert final_winner == "TIE"
                assert swap_meta["position_bias_detected"] is True


class TestJudgeSchema:
    """
    Schema Tests

    Tests for Pydantic schema validation.
    """

    def test_JUDGE_080_metric_score_validation(self, app, app_context):
        """
        [JUDGE-080] MetricScore Validation

        Score muss zwischen 1 und 5 sein.
        """
        from services.judge.judge_schema import MetricScore

        # Valid
        score = MetricScore(score_a=4.0, score_b=3.5, reasoning="Test reasoning")
        assert score.score_a == 4.0

        # Invalid - out of range
        with pytest.raises(Exception):
            MetricScore(score_a=0.5, score_b=3.5, reasoning="Test")

        with pytest.raises(Exception):
            MetricScore(score_a=4.0, score_b=5.5, reasoning="Test")

    def test_JUDGE_081_winner_choice_enum(self, app, app_context):
        """
        [JUDGE-081] WinnerChoice Enum

        Winner muss A, B oder TIE sein.
        """
        from services.judge.judge_schema import WinnerChoice

        assert WinnerChoice.A.value == "A"
        assert WinnerChoice.B.value == "B"
        assert WinnerChoice.TIE.value == "TIE"

    def test_JUDGE_082_calculate_aggregate_scores(self, app, app_context):
        """
        [JUDGE-082] Calculate Aggregate Scores

        Aggregate Scores sollten korrekt berechnet werden.
        """
        from services.judge.judge_schema import (
            JudgeEvaluationResult, ChainOfThought, EvaluationCriteria,
            MetricScore, calculate_aggregate_scores
        )

        cot = ChainOfThought(
            step_1_overview="x" * 60,
            step_2_strengths_a="x" * 35,
            step_3_strengths_b="x" * 35,
            step_4_weaknesses_a="x" * 25,
            step_5_weaknesses_b="x" * 25,
            step_6_comparison="x" * 60
        )

        criteria = EvaluationCriteria(
            counsellor_coherence=MetricScore(score_a=5.0, score_b=3.0, reasoning="Test reasoning text"),
            client_coherence=MetricScore(score_a=4.0, score_b=3.0, reasoning="Test reasoning text"),
            quality=MetricScore(score_a=4.0, score_b=3.0, reasoning="Test reasoning text"),
            empathy=MetricScore(score_a=4.0, score_b=3.0, reasoning="Test reasoning text"),
            authenticity=MetricScore(score_a=4.0, score_b=3.0, reasoning="Test reasoning text"),
            solution_orientation=MetricScore(score_a=4.0, score_b=3.0, reasoning="Test reasoning text")
        )

        result = JudgeEvaluationResult(
            chain_of_thought=cot,
            criteria_scores=criteria,
            winner="A",
            confidence=0.9,
            final_justification="x" * 60
        )

        agg = calculate_aggregate_scores(result)

        assert agg["total_a"] == 25.0
        assert agg["total_b"] == 18.0
        assert agg["avg_a"] == 25.0 / 6
        assert agg["avg_b"] == 18.0 / 6
        assert agg["winner_by_score"] == "A"

    def test_JUDGE_083_aggregate_scores_tie(self, app, app_context):
        """
        [JUDGE-083] Aggregate Scores - TIE

        Bei nahezu gleichen Scores sollte TIE sein.
        """
        from services.judge.judge_schema import (
            JudgeEvaluationResult, ChainOfThought, EvaluationCriteria,
            MetricScore, calculate_aggregate_scores
        )

        cot = ChainOfThought(
            step_1_overview="x" * 60,
            step_2_strengths_a="x" * 35,
            step_3_strengths_b="x" * 35,
            step_4_weaknesses_a="x" * 25,
            step_5_weaknesses_b="x" * 25,
            step_6_comparison="x" * 60
        )

        # Nearly equal scores
        criteria = EvaluationCriteria(
            counsellor_coherence=MetricScore(score_a=4.0, score_b=4.0, reasoning="Test reasoning text"),
            client_coherence=MetricScore(score_a=4.0, score_b=4.1, reasoning="Test reasoning text"),
            quality=MetricScore(score_a=4.0, score_b=4.0, reasoning="Test reasoning text"),
            empathy=MetricScore(score_a=4.0, score_b=3.9, reasoning="Test reasoning text"),
            authenticity=MetricScore(score_a=4.0, score_b=4.0, reasoning="Test reasoning text"),
            solution_orientation=MetricScore(score_a=4.0, score_b=4.0, reasoning="Test reasoning text")
        )

        result = JudgeEvaluationResult(
            chain_of_thought=cot,
            criteria_scores=criteria,
            winner="TIE",
            confidence=0.6,
            final_justification="x" * 60
        )

        agg = calculate_aggregate_scores(result)

        # Difference is 0.0, within 0.5 threshold
        assert agg["winner_by_score"] == "TIE"


class TestFactoryFunction:
    """
    Factory Function Tests

    Tests for create_judge_service function.
    """

    def test_JUDGE_090_create_judge_service(self, app, app_context):
        """
        [JUDGE-090] Create Judge Service

        Factory sollte Service erstellen.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import create_judge_service

                service = create_judge_service(
                    api_key='test-key',
                    model='test/model'
                )

                assert service is not None
                assert service.api_key == 'test-key'
                assert service.model == 'test/model'


class TestEdgeCases:
    """
    Edge Cases Tests

    Tests for unusual inputs and edge cases.
    """

    def test_JUDGE_100_pillar_names_mapping(self, app, app_context):
        """
        [JUDGE-100] Pillar Names Mapping

        Pillar Namen sollten korrekt gemappt werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                assert service.PILLAR_NAMES[1] == "Rollenspiele"
                assert service.PILLAR_NAMES[2] == "Feature aus Säule 1"
                assert service.PILLAR_NAMES[3] == "Anonymisierte Daten"
                assert service.PILLAR_NAMES[4] == "Synthetisch generiert"
                assert service.PILLAR_NAMES[5] == "Live-Testungen"

    def test_JUDGE_101_format_thread_missing_fields(self, app, app_context):
        """
        [JUDGE-101] Format Thread - Fehlende Felder

        Fehlende Felder sollten mit Defaults behandelt werden.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                messages = [
                    {'content': 'Test'},  # Missing is_counsellor
                    {}  # Empty dict
                ]

                result = service.format_thread_for_prompt(messages)
                # Should handle gracefully
                assert 'RATSUCHENDE' in result  # Default role

    def test_JUDGE_102_transform_missing_scores(self, app, app_context):
        """
        [JUDGE-102] Transform - Fehlende Scores

        Fehlende Scores sollten Default 3 bekommen.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')

                data = {
                    "step_1": "Test " * 20,
                    "scores": {},  # Empty scores
                    "winner": "A",
                    "confidence": 0.5
                }

                result = service._transform_llm_response(data)

                # Should have default scores
                assert result["criteria_scores"]["counsellor_coherence"]["score_a"] == 3.0

    def test_JUDGE_103_get_json_schema(self, app, app_context):
        """
        [JUDGE-103] Get JSON Schema

        Schema sollte valide sein.
        """
        with patch.dict(os.environ, {'LITELLM_API_KEY': 'test-key'}):
            with patch('services.judge.judge_service.OpenAI'):
                from services.judge.judge_service import JudgeService

                service = JudgeService(api_key='test', model='test/model')
                schema = service._get_json_schema()

                assert isinstance(schema, dict)
                assert 'properties' in schema
                assert 'chain_of_thought' in schema['properties']
                assert 'criteria_scores' in schema['properties']
                assert 'winner' in schema['properties']
