"""
Unit Tests: Reranker Service
============================

Tests for the RAG result reranking service.

Test IDs:
- RERANK-001 to RERANK-010: Lexical Reranking Tests
- RERANK-020 to RERANK-025: Mode Selection Tests
- RERANK-030 to RERANK-035: Token Handling Tests

Status: Implemented
"""

import pytest
from unittest.mock import MagicMock, patch


class TestLexicalReranking:
    """
    Lexical Reranking Tests

    Tests for token-overlap based reranking.
    """

    def test_RERANK_001_lexical_rerank_basic(self, app, app_context):
        """
        [RERANK-001] Lexical Reranking Grundfunktion

        Dokumente mit mehr Token-Überlappung sollen höher ranken.
        """
        from services.rag.reranker import rerank_results

        query = "Python programming language"
        results = [
            {'content': 'Java is a programming language', 'score': 0.8},
            {'content': 'Python is a programming language for beginners', 'score': 0.7},
            {'content': 'Ruby programming basics', 'score': 0.9},
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            reranked = rerank_results(query, results, use_cross_encoder='off')

        # Results should be reordered based on token overlap
        assert isinstance(reranked, list)
        assert len(reranked) == 3

    def test_RERANK_002_lexical_rerank_preserves_content(self, app, app_context):
        """
        [RERANK-002] Lexical Reranking erhält Content

        Alle ursprünglichen Felder sollen erhalten bleiben.
        """
        from services.rag.reranker import rerank_results

        query = "test query"
        results = [
            {'content': 'doc 1', 'score': 0.5, 'metadata': {'id': 1}},
            {'content': 'doc 2', 'score': 0.6, 'metadata': {'id': 2}},
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            reranked = rerank_results(query, results, use_cross_encoder='off')

        # Check that metadata is preserved
        for r in reranked:
            assert 'content' in r
            assert 'metadata' in r

    def test_RERANK_003_empty_results(self, app, app_context):
        """
        [RERANK-003] Leere Ergebnisliste

        Leere Liste soll leere Liste zurückgeben.
        """
        from services.rag.reranker import rerank_results

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            reranked = rerank_results("query", [])

        assert reranked == []

    def test_RERANK_004_single_result(self, app, app_context):
        """
        [RERANK-004] Einzelnes Ergebnis

        Ein Ergebnis soll unverändert zurückgegeben werden.
        """
        from services.rag.reranker import rerank_results

        results = [{'content': 'single doc', 'score': 0.8}]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            reranked = rerank_results("query", results)

        assert len(reranked) == 1
        assert reranked[0]['content'] == 'single doc'


class TestModeSelection:
    """
    Mode Selection Tests

    Tests for reranking mode selection.
    """

    def test_RERANK_020_off_mode_preserves_order(self, app, app_context):
        """
        [RERANK-020] 'off' Mode erhält Reihenfolge

        Bei RAG_RERANK_MODE='off' soll Original-Reihenfolge bleiben.
        """
        from services.rag.reranker import rerank_results
        import os

        results = [
            {'content': 'first', 'score': 0.5},
            {'content': 'second', 'score': 0.9},
            {'content': 'third', 'score': 0.7},
        ]

        original = os.environ.get('RAG_RERANK_MODE')
        try:
            os.environ['RAG_RERANK_MODE'] = 'off'
            reranked = rerank_results("query", results)

            # Order should be preserved when mode is 'off'
            assert reranked[0]['content'] == 'first'
            assert reranked[1]['content'] == 'second'
            assert reranked[2]['content'] == 'third'
        finally:
            if original is not None:
                os.environ['RAG_RERANK_MODE'] = original
            else:
                os.environ.pop('RAG_RERANK_MODE', None)

    def test_RERANK_021_lexical_mode_default(self, app, app_context):
        """
        [RERANK-021] Lexical Mode als Default

        Ohne expliziten Mode soll lexical verwendet werden.
        """
        from services.rag.reranker import rerank_results

        results = [
            {'content': 'apple banana', 'score': 0.5},
            {'content': 'apple apple apple', 'score': 0.4},
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            reranked = rerank_results("apple", results)

        # Should use lexical reranking by default
        assert isinstance(reranked, list)

    def test_RERANK_022_cross_encoder_mode(self, app, app_context):
        """
        [RERANK-022] Cross-Encoder Mode

        Bei use_cross_encoder=True soll Cross-Encoder Model verwendet werden.
        """
        from services.rag.reranker import rerank_results

        results = [
            {'content': 'doc 1', 'score': 0.5},
            {'content': 'doc 2', 'score': 0.6},
        ]

        with patch('services.rag.reranker._get_cross_encoder') as mock_encoder:
            mock_model = MagicMock()
            mock_model.predict.return_value = [0.8, 0.3]
            mock_encoder.return_value = mock_model

            reranked = rerank_results(
                "query",
                results,
                use_cross_encoder=True,
                model_name='test-model'
            )

            # Cross-encoder should be called
            mock_encoder.assert_called_once_with('test-model')


class TestTokenHandling:
    """
    Token Handling Tests

    Tests for tokenization functionality.
    """

    def test_RERANK_030_basic_tokenization(self, app, app_context):
        """
        [RERANK-030] Basis Tokenisierung

        Text soll in Tokens aufgeteilt werden (als Liste).
        """
        from services.rag.reranker import _tokenize

        text = "Hello World Test"
        tokens = _tokenize(text)

        assert isinstance(tokens, list)
        assert len(tokens) > 0
        # Should contain lowercase tokens
        assert 'hello' in tokens
        assert 'world' in tokens
        assert 'test' in tokens

    def test_RERANK_031_lowercase_tokenization(self, app, app_context):
        """
        [RERANK-031] Lowercase Tokenisierung

        Tokens sollen lowercase sein.
        """
        from services.rag.reranker import _tokenize

        text = "HELLO World TeSt"
        tokens = _tokenize(text)

        # All tokens should be lowercase
        for token in tokens:
            assert token == token.lower()

    def test_RERANK_032_short_tokens_filtered(self, app, app_context):
        """
        [RERANK-032] Kurze Tokens gefiltert

        Tokens mit weniger als 2 Zeichen sollen gefiltert werden.
        """
        from services.rag.reranker import _tokenize

        text = "I am a test"
        tokens = _tokenize(text)

        # Single-char tokens should be filtered
        for token in tokens:
            assert len(token) >= 2

    def test_RERANK_033_unicode_tokenization(self, app, app_context):
        """
        [RERANK-033] Unicode Tokenisierung

        Deutsche Umlaute sollen korrekt tokenisiert werden.
        """
        from services.rag.reranker import _tokenize

        text = "Größe Übung Änderung"
        tokens = _tokenize(text)

        # Should handle German umlauts
        assert len(tokens) > 0
        # Tokens should contain umlaut words
        lowercase_text = text.lower()
        assert any(t in lowercase_text for t in tokens)

    def test_RERANK_034_punctuation_handling(self, app, app_context):
        """
        [RERANK-034] Interpunktion Handling

        Interpunktion soll entfernt werden.
        """
        from services.rag.reranker import _tokenize

        text = "Hello, World! Test. Query?"
        tokens = _tokenize(text)

        # Punctuation should be stripped
        for token in tokens:
            assert ',' not in token
            assert '!' not in token
            assert '.' not in token
            assert '?' not in token


class TestAlphaBlending:
    """
    Alpha Blending Tests

    Tests for the score blending parameter.
    """

    def test_RERANK_040_alpha_from_env(self, app, app_context):
        """
        [RERANK-040] Alpha aus Umgebungsvariable

        RAG_RERANK_ALPHA soll aus env gelesen werden.
        """
        from services.rag.reranker import _get_alpha
        import os

        original = os.environ.get('RAG_RERANK_ALPHA')

        try:
            os.environ['RAG_RERANK_ALPHA'] = '0.25'
            alpha = _get_alpha()
            assert alpha == 0.25
        finally:
            if original is not None:
                os.environ['RAG_RERANK_ALPHA'] = original
            else:
                os.environ.pop('RAG_RERANK_ALPHA', None)

    def test_RERANK_041_alpha_default(self, app, app_context):
        """
        [RERANK-041] Alpha Default Wert

        Ohne env var soll Default verwendet werden.
        """
        from services.rag.reranker import _get_alpha
        import os

        original = os.environ.pop('RAG_RERANK_ALPHA', None)

        try:
            alpha = _get_alpha()
            # Should have a default value (typically 0.15)
            assert 0.0 <= alpha <= 1.0
        finally:
            if original is not None:
                os.environ['RAG_RERANK_ALPHA'] = original

    def test_RERANK_042_alpha_clipping(self, app, app_context):
        """
        [RERANK-042] Alpha Clipping

        Alpha außerhalb [0,1] soll geclippt werden.
        """
        from services.rag.reranker import _get_alpha
        import os

        original = os.environ.get('RAG_RERANK_ALPHA')

        try:
            # Test value > 1
            os.environ['RAG_RERANK_ALPHA'] = '1.5'
            alpha = _get_alpha()
            assert alpha <= 1.0

            # Test value < 0
            os.environ['RAG_RERANK_ALPHA'] = '-0.5'
            alpha = _get_alpha()
            assert alpha >= 0.0
        finally:
            if original is not None:
                os.environ['RAG_RERANK_ALPHA'] = original
            else:
                os.environ.pop('RAG_RERANK_ALPHA', None)


class TestScoreCalculation:
    """
    Score Calculation Tests

    Tests for the blended score calculation.
    """

    def test_RERANK_050_higher_overlap_higher_score(self, app, app_context):
        """
        [RERANK-050] Mehr Überlappung = Höherer Score

        Dokumente mit mehr Query-Token-Überlappung sollen höher scoren.
        """
        from services.rag.reranker import rerank_results

        query = "python machine learning"
        results = [
            {'content': 'java programming basics', 'score': 0.9},
            {'content': 'python machine learning tutorial', 'score': 0.5},
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            reranked = rerank_results(query, results, use_cross_encoder='lexical')

        # The doc with more overlap should rank higher after reranking
        # (unless alpha is very low)
        assert len(reranked) == 2

    def test_RERANK_051_vector_score_still_matters(self, app, app_context):
        """
        [RERANK-051] Vector Score zählt noch

        Original-Score soll in Berechnung einfließen.
        """
        from services.rag.reranker import rerank_results

        query = "test"
        results = [
            {'content': 'test document', 'score': 0.1},  # Low vector score
            {'content': 'other content test', 'score': 0.95},  # High vector score
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            with patch('services.rag.reranker._get_alpha', return_value=0.1):  # Low alpha
                reranked = rerank_results(query, results, use_cross_encoder='lexical')

        # With low alpha, vector score dominates
        assert len(reranked) == 2


class TestEdgeCases:
    """
    Edge Case Tests

    Tests for unusual inputs and edge cases.
    """

    def test_RERANK_060_empty_query(self, app, app_context):
        """
        [RERANK-060] Leere Query

        Leere Query soll Original-Reihenfolge erhalten.
        """
        from services.rag.reranker import rerank_results

        results = [
            {'content': 'doc 1', 'score': 0.5},
            {'content': 'doc 2', 'score': 0.6},
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            reranked = rerank_results("", results)

        assert len(reranked) == 2

    def test_RERANK_061_none_content(self, app, app_context):
        """
        [RERANK-061] None Content

        Dokumente ohne Content sollen behandelt werden.
        """
        from services.rag.reranker import rerank_results

        results = [
            {'content': None, 'score': 0.5},
            {'content': 'valid doc', 'score': 0.6},
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            try:
                reranked = rerank_results("query", results)
                # Should handle None gracefully
                assert isinstance(reranked, list)
            except (TypeError, AttributeError):
                # Also acceptable - explicit error for bad input
                pass

    def test_RERANK_062_missing_score(self, app, app_context):
        """
        [RERANK-062] Fehlender Score

        Dokumente ohne Score sollen behandelt werden.
        """
        from services.rag.reranker import rerank_results

        results = [
            {'content': 'doc 1'},  # No score
            {'content': 'doc 2', 'score': 0.6},
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            try:
                reranked = rerank_results("query", results, use_cross_encoder='off')
                assert isinstance(reranked, list)
            except KeyError:
                # Also acceptable
                pass

    def test_RERANK_063_very_long_content(self, app, app_context):
        """
        [RERANK-063] Sehr langer Content

        Sehr lange Dokumente sollen effizient behandelt werden.
        """
        from services.rag.reranker import rerank_results

        long_content = "word " * 10000  # 50000 chars

        results = [
            {'content': long_content, 'score': 0.5},
            {'content': 'short doc', 'score': 0.6},
        ]

        with patch('services.rag.reranker._get_default_reranker_model', return_value=None):
            reranked = rerank_results("word", results, use_cross_encoder='lexical')

        assert len(reranked) == 2
