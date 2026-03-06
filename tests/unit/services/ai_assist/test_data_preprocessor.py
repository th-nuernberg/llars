"""
Tests for DataPreprocessor - AI-powered data analysis preprocessing.

Covers:
- preprocess() main entry point
- Schema extraction (recursive, nested objects, arrays)
- Pattern detection (comparison, conversation, labels, scores, etc.)
- Representative sample selection
- Complexity scoring
- Intelligent truncation
- Statistics computation
- Prompt formatting
"""

import json

import pytest

from services.ai_assist.data_preprocessor import DataPreprocessor


class TestPreprocess:
    """Test main preprocess entry point."""

    def test_AI_ASSIST_001_empty_items_returns_empty_structure(self):
        """AI_ASSIST_001: Empty items list returns empty structure."""
        result = DataPreprocessor.preprocess([], filename="empty.csv")

        assert result['item_count'] == 0
        assert result['schema'] == {}
        assert result['samples'] == []
        assert result['statistics'] == {}
        assert result['detected_patterns'] == []

    def test_AI_ASSIST_002_preprocess_returns_all_keys(self):
        """AI_ASSIST_002: Preprocess returns expected keys."""
        items = [{"text": "Hello", "score": 5}]
        result = DataPreprocessor.preprocess(items, filename="test.json")

        assert 'item_count' in result
        assert 'filename' in result
        assert 'schema' in result
        assert 'samples' in result
        assert 'statistics' in result
        assert 'detected_patterns' in result
        assert result['item_count'] == 1
        assert result['filename'] == "test.json"

    def test_AI_ASSIST_003_preprocess_with_many_items(self):
        """AI_ASSIST_003: Preprocess handles large datasets efficiently."""
        items = [{"id": i, "text": f"Text {i}", "score": i % 5} for i in range(100)]
        result = DataPreprocessor.preprocess(items)

        assert result['item_count'] == 100
        assert len(result['samples']) <= DataPreprocessor.MAX_SAMPLE_ITEMS


class TestExtractSchema:
    """Test schema extraction."""

    def test_AI_ASSIST_010_schema_string_field(self):
        """AI_ASSIST_010: Detects string type correctly."""
        items = [{"name": "Alice"}, {"name": "Bob"}]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['name']['type'] == 'string'
        assert schema['name']['completeness'] == 1.0
        assert schema['name']['nullable'] is False

    def test_AI_ASSIST_011_schema_number_field(self):
        """AI_ASSIST_011: Detects number type with min/max."""
        items = [{"score": 3}, {"score": 7}, {"score": 5}]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['score']['type'] == 'number'
        assert schema['score']['min'] == 3
        assert schema['score']['max'] == 7
        assert schema['score']['is_integer'] is True

    def test_AI_ASSIST_012_schema_boolean_field(self):
        """AI_ASSIST_012: Detects boolean type."""
        items = [{"is_human": True}, {"is_human": False}]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['is_human']['type'] == 'boolean'
        assert set(schema['is_human']['values']) == {True, False}

    def test_AI_ASSIST_013_schema_nullable_field(self):
        """AI_ASSIST_013: Handles nullable fields with completeness."""
        items = [{"name": "Alice"}, {"name": None}, {"name": "Bob"}]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['name']['nullable'] is True
        assert schema['name']['completeness'] == pytest.approx(0.67, abs=0.01)

    def test_AI_ASSIST_014_schema_all_null_field(self):
        """AI_ASSIST_014: All-null field detected as null type."""
        items = [{"x": None}, {"x": None}]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['x']['type'] == 'null'
        assert schema['x']['completeness'] == 0.0

    def test_AI_ASSIST_015_schema_mixed_type_field(self):
        """AI_ASSIST_015: Mixed types detected as mixed."""
        items = [{"val": "hello"}, {"val": 42}]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['val']['type'] == 'mixed'

    def test_AI_ASSIST_016_schema_array_field(self):
        """AI_ASSIST_016: Array fields with nested object schema."""
        items = [
            {"messages": [{"role": "user", "content": "Hi"}]},
            {"messages": [{"role": "assistant", "content": "Hello"}]}
        ]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['messages']['type'] == 'array'
        assert 'items_schema' in schema['messages']
        assert 'role' in schema['messages']['items_schema']
        assert 'content' in schema['messages']['items_schema']

    def test_AI_ASSIST_017_schema_nested_object_field(self):
        """AI_ASSIST_017: Nested object fields have children schema."""
        items = [
            {"meta": {"source": "web", "count": 5}},
            {"meta": {"source": "api", "count": 10}}
        ]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['meta']['type'] == 'object'
        assert 'children' in schema['meta']
        assert 'source' in schema['meta']['children']

    def test_AI_ASSIST_018_schema_string_enum_detection(self):
        """AI_ASSIST_018: Detects enum pattern for few unique string values."""
        items = [{"status": "open"}, {"status": "closed"}, {"status": "open"},
                 {"status": "pending"}, {"status": "open"}, {"status": "closed"},
                 {"status": "open"}, {"status": "closed"}, {"status": "pending"},
                 {"status": "open"}, {"status": "closed"}, {"status": "pending"}]
        schema = DataPreprocessor.extract_schema(items)

        assert 'enum_values' in schema['status']
        assert set(schema['status']['enum_values']) == {'open', 'closed', 'pending'}

    def test_AI_ASSIST_019_schema_string_avg_length(self):
        """AI_ASSIST_019: Computes average string length."""
        items = [{"text": "ab"}, {"text": "abcd"}, {"text": "abcdef"}]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['text']['avg_length'] == 4  # (2+4+6)/3 = 4
        assert schema['text']['min_length'] == 2
        assert schema['text']['max_length'] == 6

    def test_AI_ASSIST_020_schema_empty_items(self):
        """AI_ASSIST_020: Empty items returns empty schema."""
        assert DataPreprocessor.extract_schema([]) == {}

    def test_AI_ASSIST_021_schema_array_primitive_items(self):
        """AI_ASSIST_021: Array with primitive items detects items_type."""
        items = [{"tags": ["a", "b"]}, {"tags": ["c"]}]
        schema = DataPreprocessor.extract_schema(items)

        assert schema['tags']['type'] == 'array'
        assert schema['tags'].get('items_type') == 'string'


class TestDetectPatterns:
    """Test data pattern detection."""

    def test_AI_ASSIST_030_detects_comparison_pairs(self):
        """AI_ASSIST_030: Detects answer_a/answer_b comparison pattern."""
        items = [{"answer_a": "X", "answer_b": "Y"}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert any('comparison_pairs' in p for p in patterns)

    def test_AI_ASSIST_031_detects_conversation_pattern(self):
        """AI_ASSIST_031: Detects conversation pattern with role/content."""
        items = [{"messages": [{"role": "user", "content": "Hi"}]}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert any('conversation' in p for p in patterns)

    def test_AI_ASSIST_032_detects_label_fields(self):
        """AI_ASSIST_032: Detects label/category fields."""
        items = [{"text": "abc", "label": "positive"}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert any('labels' in p for p in patterns)

    def test_AI_ASSIST_033_detects_authenticity_labels(self):
        """AI_ASSIST_033: Detects is_human authenticity pattern."""
        items = [{"text": "abc", "is_human": True}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert 'authenticity_labels' in patterns

    def test_AI_ASSIST_034_detects_score_fields(self):
        """AI_ASSIST_034: Detects numeric score fields."""
        items = [{"text": "abc", "quality_score": 4.5}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert any('scores' in p for p in patterns)

    def test_AI_ASSIST_035_detects_winner_field(self):
        """AI_ASSIST_035: Detects winner/preference field."""
        items = [{"answer_a": "X", "answer_b": "Y", "winner": "A"}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert 'winner_field' in patterns

    def test_AI_ASSIST_036_detects_email_structure(self):
        """AI_ASSIST_036: Detects email/thread structure."""
        items = [{"subject": "Hello", "thread_id": "t1", "body": "text"}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert 'email_structure' in patterns

    def test_AI_ASSIST_037_detects_is_prefix_labels(self):
        """AI_ASSIST_037: Detects is_ prefixed label fields."""
        items = [{"text": "abc", "is_spam": True}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert any('labels' in p for p in patterns)

    def test_AI_ASSIST_038_no_patterns_for_plain_text(self):
        """AI_ASSIST_038: No special patterns for plain text data."""
        items = [{"text": "Some text content here"}]
        schema = DataPreprocessor.extract_schema(items)
        patterns = DataPreprocessor.detect_patterns(items, schema)

        assert 'comparison_pairs' not in str(patterns)
        assert 'authenticity_labels' not in patterns


class TestSelectRepresentativeSamples:
    """Test representative sample selection."""

    def test_AI_ASSIST_040_few_items_returns_all(self):
        """AI_ASSIST_040: Returns all items when count <= MAX_SAMPLE_ITEMS."""
        items = [{"a": 1}, {"a": 2}]
        schema = DataPreprocessor.extract_schema(items)

        samples = DataPreprocessor.select_representative_samples(items, schema)
        assert len(samples) == 2

    def test_AI_ASSIST_041_selects_diverse_samples(self):
        """AI_ASSIST_041: Selects min, median, and max complexity samples."""
        items = [
            {"text": "a"},
            {"text": "ab" * 50, "extra": "field"},
            {"text": "medium length text"},
            {"text": "x" * 500, "a": 1, "b": 2, "c": 3},
        ]
        schema = DataPreprocessor.extract_schema(items)

        samples = DataPreprocessor.select_representative_samples(items, schema)
        assert len(samples) == 3

    def test_AI_ASSIST_042_empty_items_returns_empty(self):
        """AI_ASSIST_042: Empty items returns empty samples."""
        samples = DataPreprocessor.select_representative_samples([], {})
        assert samples == []


class TestCalculateComplexity:
    """Test complexity scoring."""

    def test_AI_ASSIST_050_simple_item_low_score(self):
        """AI_ASSIST_050: Simple item has low complexity."""
        score = DataPreprocessor._calculate_complexity({"a": 1})
        assert score >= 1

    def test_AI_ASSIST_051_complex_item_higher_score(self):
        """AI_ASSIST_051: Complex item has higher complexity."""
        simple = DataPreprocessor._calculate_complexity({"a": 1})
        complex_item = DataPreprocessor._calculate_complexity({
            "text": "x" * 500,
            "messages": [{"role": "user", "content": "hi"}, {"role": "bot", "content": "hello"}],
            "meta": {"a": 1, "b": 2}
        })
        assert complex_item > simple

    def test_AI_ASSIST_052_non_dict_returns_zero(self):
        """AI_ASSIST_052: Non-dict value returns 0."""
        assert DataPreprocessor._calculate_complexity("not a dict") == 0


class TestTruncateItem:
    """Test intelligent truncation."""

    def test_AI_ASSIST_060_truncates_long_strings(self):
        """AI_ASSIST_060: Long strings are truncated with marker."""
        item = {"text": "x" * 500}
        schema = DataPreprocessor.extract_schema([item])

        truncated = DataPreprocessor.truncate_item(item, schema)
        assert len(truncated['text']) < 500
        assert 'mehr Zeichen' in truncated['text']

    def test_AI_ASSIST_061_preserves_short_strings(self):
        """AI_ASSIST_061: Short strings are not truncated."""
        item = {"text": "Hello"}
        schema = DataPreprocessor.extract_schema([item])

        truncated = DataPreprocessor.truncate_item(item, schema)
        assert truncated['text'] == "Hello"

    def test_AI_ASSIST_062_truncates_long_arrays(self):
        """AI_ASSIST_062: Arrays with many items are truncated."""
        item = {"items": list(range(10))}
        schema = DataPreprocessor.extract_schema([item])

        truncated = DataPreprocessor.truncate_item(item, schema)
        assert len(truncated['items']) == 4  # 3 items + "... (+7 weitere)"
        assert 'weitere' in truncated['items'][-1]

    def test_AI_ASSIST_063_preserves_numbers_and_bools(self):
        """AI_ASSIST_063: Numbers and booleans preserved exactly."""
        item = {"score": 4.5, "active": True, "count": 42}
        schema = DataPreprocessor.extract_schema([item])

        truncated = DataPreprocessor.truncate_item(item, schema)
        assert truncated['score'] == 4.5
        assert truncated['active'] is True
        assert truncated['count'] == 42

    def test_AI_ASSIST_064_truncates_nested_dicts(self):
        """AI_ASSIST_064: Nested dicts are recursively truncated."""
        item = {"meta": {"text": "x" * 500}}
        schema = DataPreprocessor.extract_schema([item])

        truncated = DataPreprocessor.truncate_item(item, schema)
        assert 'mehr Zeichen' in truncated['meta']['text']

    def test_AI_ASSIST_065_handles_none_values(self):
        """AI_ASSIST_065: None values are preserved."""
        item = {"field": None}
        schema = DataPreprocessor.extract_schema([item])

        truncated = DataPreprocessor.truncate_item(item, schema)
        assert truncated['field'] is None

    def test_AI_ASSIST_066_depth_limit_prevents_recursion(self):
        """AI_ASSIST_066: Deep nesting stops at depth 5."""
        result = DataPreprocessor._truncate_value("deep", None, depth=6)
        assert result == "..."


class TestComputeStatistics:
    """Test statistics computation."""

    def test_AI_ASSIST_070_empty_items_returns_empty(self):
        """AI_ASSIST_070: Empty items returns empty stats."""
        assert DataPreprocessor.compute_statistics([], {}) == {}

    def test_AI_ASSIST_071_categorizes_fields_by_completeness(self):
        """AI_ASSIST_071: Fields categorized as always/sometimes/rarely present."""
        schema = {
            "id": {"completeness": 1.0},
            "name": {"completeness": 0.96},
            "email": {"completeness": 0.7},
            "phone": {"completeness": 0.3},
        }
        items = [{"id": 1}]  # Just need non-empty

        stats = DataPreprocessor.compute_statistics(items, schema)

        assert "id" in stats['fields_always_present']
        assert "name" in stats['fields_always_present']
        assert "email" in stats['fields_sometimes_present']
        assert "phone" in stats['fields_rarely_present']

    def test_AI_ASSIST_072_detects_content_fields(self):
        """AI_ASSIST_072: Detects long text content fields."""
        schema = {
            "id": {"type": "number"},
            "body": {"type": "string", "avg_length": 500, "completeness": 1.0},
            "title": {"type": "string", "avg_length": 20, "completeness": 1.0},
        }
        items = [{"id": 1}]

        stats = DataPreprocessor.compute_statistics(items, schema)

        assert 'content_fields' in stats
        assert stats['content_fields'][0]['field'] == 'body'


class TestFormatForPrompt:
    """Test prompt formatting."""

    def test_AI_ASSIST_080_format_includes_header(self):
        """AI_ASSIST_080: Formatted output includes data analysis header."""
        preprocessed = {
            'item_count': 5,
            'filename': 'test.csv',
            'detected_patterns': ['comparison_pairs:answer_a/answer_b'],
            'schema': {'text': {'type': 'string'}},
            'statistics': {
                'fields_always_present': ['text'],
                'fields_sometimes_present': [],
                'fields_rarely_present': [],
            },
            'samples': [{'text': 'hello'}],
        }

        result = DataPreprocessor.format_for_prompt(preprocessed)

        assert '## DATENANALYSE' in result
        assert '**Datensätze:** 5' in result
        assert 'test.csv' in result

    def test_AI_ASSIST_081_format_includes_patterns(self):
        """AI_ASSIST_081: Includes detected patterns section."""
        preprocessed = {
            'item_count': 1,
            'filename': 'test.json',
            'detected_patterns': ['authenticity_labels', 'labels:is_human'],
            'schema': {},
            'statistics': {},
            'samples': [],
        }

        result = DataPreprocessor.format_for_prompt(preprocessed)

        assert 'Erkannte Muster' in result
        assert 'authenticity_labels' in result

    def test_AI_ASSIST_082_format_includes_schema_as_json(self):
        """AI_ASSIST_082: Schema is included as JSON code block."""
        preprocessed = {
            'item_count': 1,
            'filename': 'test.json',
            'detected_patterns': [],
            'schema': {'text': {'type': 'string', 'avg_length': 50}},
            'statistics': {},
            'samples': [],
        }

        result = DataPreprocessor.format_for_prompt(preprocessed)

        assert '```json' in result
        assert '"text"' in result

    def test_AI_ASSIST_083_format_no_patterns_skips_section(self):
        """AI_ASSIST_083: No patterns section when list is empty."""
        preprocessed = {
            'item_count': 1,
            'filename': 'test.json',
            'detected_patterns': [],
            'schema': {},
            'statistics': {},
            'samples': [],
        }

        result = DataPreprocessor.format_for_prompt(preprocessed)
        assert 'Erkannte Muster' not in result
