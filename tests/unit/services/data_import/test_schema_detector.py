"""
Tests for SchemaDetector service.

Covers deterministic field-based evaluation type detection,
priority ordering, normalization, CSV header convenience,
field documentation, and singleton factory.
"""

import pytest
from unittest.mock import patch


class TestDetectionResultDataclass:
    """Tests for DetectionResult dataclass."""

    def test_SDET_001_to_dict_with_type(self, app, app_context):
        """[SDET-001] to_dict includes eval_type value."""
        from services.data_import.schema_detector import DetectionResult, EvaluationType
        result = DetectionResult(
            eval_type=EvaluationType.RATING,
            confidence='definite',
            matched_fields=['question', 'response'],
            reason='test',
        )
        d = result.to_dict()
        assert d['eval_type'] == 'rating'
        assert d['confidence'] == 'definite'
        assert d['matched_fields'] == ['question', 'response']
        assert d['all_fields'] == []

    def test_SDET_002_to_dict_none_type(self, app, app_context):
        """[SDET-002] to_dict returns None for eval_type when undetected."""
        from services.data_import.schema_detector import DetectionResult
        result = DetectionResult(
            eval_type=None,
            confidence='uncertain',
            matched_fields=[],
            reason='No match',
            all_fields=['foo', 'bar'],
        )
        d = result.to_dict()
        assert d['eval_type'] is None
        assert d['all_fields'] == ['foo', 'bar']


class TestNormalizeData:
    """Tests for SchemaDetector._normalize_data."""

    def test_SDET_010_normalize_single_dict(self, app, app_context):
        """[SDET-010] Single dict returns itself."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        sample, fields = det._normalize_data({'text': 'hello', 'label': 'pos'})
        assert sample == {'text': 'hello', 'label': 'pos'}
        assert 'text' in fields

    def test_SDET_011_normalize_dict_with_items(self, app, app_context):
        """[SDET-011] Dict with items[] returns first item."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        data = {'items': [{'a': 1}, {'b': 2}]}
        sample, fields = det._normalize_data(data)
        assert sample == {'a': 1}

    def test_SDET_012_normalize_list_of_dicts(self, app, app_context):
        """[SDET-012] List of dicts returns first dict."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        data = [{'question': 'hi', 'answer': 'bye'}, {'question': 'x', 'answer': 'y'}]
        sample, fields = det._normalize_data(data)
        assert sample == {'question': 'hi', 'answer': 'bye'}

    def test_SDET_013_normalize_csv_list_of_lists(self, app, app_context):
        """[SDET-013] List of lists (CSV) uses first row as headers."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        data = [['Text', 'Category'], ['hello', 'pos']]
        sample, fields = det._normalize_data(data)
        assert 'text' in sample
        assert 'category' in sample

    def test_SDET_014_normalize_empty_list(self, app, app_context):
        """[SDET-014] Empty list returns None."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        sample, fields = det._normalize_data([])
        assert sample is None
        assert fields == []

    def test_SDET_015_normalize_none(self, app, app_context):
        """[SDET-015] Non-parseable data returns None."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        sample, fields = det._normalize_data('just a string')
        assert sample is None

    def test_SDET_016_normalize_empty_items(self, app, app_context):
        """[SDET-016] Dict with empty items[] returns the dict itself."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        data = {'items': [], 'metadata': 'test'}
        sample, fields = det._normalize_data(data)
        # Empty items list: falls through to return the dict itself
        assert sample == data
        assert 'items' in fields


class TestCheckAuthenticity:
    """Tests for authenticity detection (Priority 1)."""

    def test_SDET_020_is_human_field(self, app, app_context):
        """[SDET-020] Detects is_human as authenticity."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'text': 'sample', 'is_human': True})
        assert result.eval_type == EvaluationType.AUTHENTICITY
        assert result.confidence == 'definite'
        assert 'is_human' in result.matched_fields

    def test_SDET_021_is_fake_field(self, app, app_context):
        """[SDET-021] Detects is_fake as authenticity."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'content': 'sample', 'is_fake': False})
        assert result.eval_type == EvaluationType.AUTHENTICITY

    def test_SDET_022_synthetic_field(self, app, app_context):
        """[SDET-022] Detects synthetic as authenticity."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'text': 'test', 'synthetic': 1})
        assert result.eval_type == EvaluationType.AUTHENTICITY
        assert 'synthetic' in result.matched_fields

    def test_SDET_023_ai_generated_field(self, app, app_context):
        """[SDET-023] Detects ai_generated as authenticity."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'text': 'x', 'ai_generated': True})
        assert result.eval_type == EvaluationType.AUTHENTICITY

    def test_SDET_024_authenticity_beats_messages(self, app, app_context):
        """[SDET-024] Authenticity wins over mail_rating even with messages[]."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        data = {
            'text': 'sample',
            'is_human': True,
            'messages': [
                {'role': 'user', 'content': 'hi'},
                {'role': 'assistant', 'content': 'hello'}
            ]
        }
        result = det.detect(data)
        assert result.eval_type == EvaluationType.AUTHENTICITY


class TestCheckComparison:
    """Tests for comparison detection (Priority 2)."""

    def test_SDET_030_response_a_b_pair(self, app, app_context):
        """[SDET-030] Detects response_a/response_b as comparison."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'prompt': 'q', 'response_a': 'x', 'response_b': 'y'})
        assert result.eval_type == EvaluationType.COMPARISON
        assert 'response_a' in result.matched_fields
        assert 'response_b' in result.matched_fields

    def test_SDET_031_with_winner_field(self, app, app_context):
        """[SDET-031] Winner field included in matched fields."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'prompt': 'q', 'response_a': 'x', 'response_b': 'y', 'winner': 'a'
        })
        assert result.eval_type == EvaluationType.COMPARISON
        assert 'winner' in result.matched_fields

    def test_SDET_032_conversation_a_b(self, app, app_context):
        """[SDET-032] Detects conversation_a/conversation_b as comparison."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'conversation_a': [{'role': 'user'}],
            'conversation_b': [{'role': 'user'}],
        })
        assert result.eval_type == EvaluationType.COMPARISON

    def test_SDET_033_winner_with_response_fields(self, app, app_context):
        """[SDET-033] Winner + generic response fields trigger comparison."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'winner': 'model_1',
            'response_1': 'text',
            'response_2': 'text',
        })
        assert result.eval_type == EvaluationType.COMPARISON


class TestCheckRanking:
    """Tests for ranking detection (Priority 3)."""

    def test_SDET_040_summary_abc(self, app, app_context):
        """[SDET-040] Detects summary_a/b/c as ranking."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'source': 'original', 'summary_a': 'x', 'summary_b': 'y', 'summary_c': 'z'
        })
        assert result.eval_type == EvaluationType.RANKING
        assert 'summary_a' in result.matched_fields

    def test_SDET_041_two_summary_variants(self, app, app_context):
        """[SDET-041] Two summary variants still detected as ranking."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'source': 'original', 'summary_a': 'x', 'summary_b': 'y'
        })
        assert result.eval_type == EvaluationType.RANKING

    def test_SDET_042_generic_suffix_pattern(self, app, app_context):
        """[SDET-042] Generic _1/_2/_3 pattern detected as ranking."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'text_1': 'v1', 'text_2': 'v2', 'text_3': 'v3'
        })
        assert result.eval_type == EvaluationType.RANKING

    def test_SDET_043_not_enough_variants(self, app, app_context):
        """[SDET-043] Single variant does not trigger ranking."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        fields = {'summary_a'}
        matched = det._check_ranking(fields, {})
        assert matched is None


class TestCheckMailRating:
    """Tests for mail_rating detection (Priority 5)."""

    def test_SDET_050_messages_with_roles(self, app, app_context):
        """[SDET-050] Detects messages[] with role field as mail_rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'subject': 'Help',
            'messages': [
                {'role': 'user', 'content': 'hi'},
                {'role': 'assistant', 'content': 'hello'}
            ]
        })
        assert result.eval_type == EvaluationType.MAIL_RATING
        assert 'messages' in result.matched_fields
        assert 'subject' in result.matched_fields

    def test_SDET_051_messages_with_sender(self, app, app_context):
        """[SDET-051] Detects messages[] with sender field as mail_rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'messages': [
                {'sender': 'Alice', 'text': 'hi'},
                {'sender': 'Bob', 'text': 'hello'}
            ]
        })
        assert result.eval_type == EvaluationType.MAIL_RATING

    def test_SDET_052_single_message_not_mail(self, app, app_context):
        """[SDET-052] Single message does not trigger mail_rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'messages': [{'role': 'user', 'content': 'hi'}]
        })
        assert result.eval_type != EvaluationType.MAIL_RATING

    def test_SDET_053_messages_not_list(self, app, app_context):
        """[SDET-053] Non-list messages field does not trigger mail_rating."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        fields = {'messages', 'text'}
        sample = {'messages': 'not a list', 'text': 'hello'}
        matched = det._check_mail_rating(fields, sample)
        assert matched is None

    def test_SDET_054_messages_without_role_fields(self, app, app_context):
        """[SDET-054] Messages without role/sender fields not detected."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        fields = {'messages'}
        sample = {
            'messages': [
                {'text': 'plain'},
                {'text': 'also plain'}
            ]
        }
        matched = det._check_mail_rating(fields, sample)
        assert matched is None


class TestCheckRating:
    """Tests for rating detection (Priority 6)."""

    def test_SDET_060_question_response_pair(self, app, app_context):
        """[SDET-060] Detects question/response as rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'question': 'What?', 'response': 'Answer.'})
        assert result.eval_type == EvaluationType.RATING
        assert 'question' in result.matched_fields
        assert 'response' in result.matched_fields

    def test_SDET_061_prompt_completion_pair(self, app, app_context):
        """[SDET-061] Detects prompt/completion as rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'prompt': 'Write', 'completion': 'Done'})
        assert result.eval_type == EvaluationType.RATING
        assert 'prompt' in result.matched_fields

    def test_SDET_062_fallback_content_field(self, app, app_context):
        """[SDET-062] Falls back to content field for rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'content': 'Some text to rate', 'id': 1})
        assert result.eval_type == EvaluationType.RATING
        assert 'content' in result.matched_fields

    def test_SDET_063_input_output_pair(self, app, app_context):
        """[SDET-063] Detects input/output as rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'input': 'query', 'output': 'result'})
        assert result.eval_type == EvaluationType.RATING


class TestCheckLabeling:
    """Tests for labeling detection (Priority 4, but checked last)."""

    def test_SDET_070_category_with_document(self, app, app_context):
        """[SDET-070] Detects category + document as labeling."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        # Use 'document' (labeling-only content field, not in RATING_CONTENT_FIELDS)
        result = det.detect({'document': 'review text', 'category': 'positive'})
        assert result.eval_type == EvaluationType.LABELING
        assert 'category' in result.matched_fields
        assert 'document' in result.matched_fields

    def test_SDET_071_sentiment_with_review(self, app, app_context):
        """[SDET-071] Detects sentiment + review as labeling."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({'review': 'Great product!', 'sentiment': 'positive'})
        assert result.eval_type == EvaluationType.LABELING

    def test_SDET_072_label_with_long_text(self, app, app_context):
        """[SDET-072] Label field with long text content in other field triggers labeling."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'label': 'spam',
            'email_body': 'A' * 60  # Long text triggers secondary check
        })
        assert result.eval_type == EvaluationType.LABELING

    def test_SDET_073_label_alone_short_text_no_match(self, app, app_context):
        """[SDET-073] Label field alone with only short text does not trigger labeling."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        fields = {'label', 'id'}
        sample = {'label': 'pos', 'id': 1}
        matched = det._check_labeling(fields, sample)
        assert matched is None


class TestPriorityOrder:
    """Tests for correct priority ordering among types."""

    def test_SDET_080_authenticity_over_comparison(self, app, app_context):
        """[SDET-080] Authenticity beats comparison."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'response_a': 'x', 'response_b': 'y',
            'is_human': True
        })
        assert result.eval_type == EvaluationType.AUTHENTICITY

    def test_SDET_081_comparison_over_rating(self, app, app_context):
        """[SDET-081] Comparison beats rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'question': 'q', 'response_a': 'x', 'response_b': 'y'
        })
        assert result.eval_type == EvaluationType.COMPARISON

    def test_SDET_082_ranking_over_labeling(self, app, app_context):
        """[SDET-082] Ranking beats labeling."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'text': 'content',
            'category': 'pos',
            'summary_a': 'x', 'summary_b': 'y', 'summary_c': 'z'
        })
        assert result.eval_type == EvaluationType.RANKING

    def test_SDET_083_rating_over_labeling(self, app, app_context):
        """[SDET-083] Rating (question/response) beats labeling (category/text)."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        # Has both Q/A (rating) and category/text (labeling)
        result = det.detect({
            'question': 'What?', 'response': 'Answer.',
            'category': 'factual', 'text': 'related'
        })
        # Rating is checked before labeling in priority order
        assert result.eval_type == EvaluationType.RATING

    def test_SDET_084_mail_rating_over_labeling(self, app, app_context):
        """[SDET-084] mail_rating beats labeling."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect({
            'category': 'support',
            'text': 'content',
            'messages': [
                {'role': 'user', 'content': 'hi'},
                {'role': 'agent', 'content': 'hello'}
            ]
        })
        assert result.eval_type == EvaluationType.MAIL_RATING


class TestDetectNoMatch:
    """Tests for cases where no pattern matches."""

    def test_SDET_090_no_recognizable_fields(self, app, app_context):
        """[SDET-090] Completely unknown fields return None type."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        result = det.detect({'foo': 1, 'bar': 2, 'baz': 3})
        assert result.eval_type is None
        assert result.confidence == 'uncertain'

    def test_SDET_091_unparseable_data(self, app, app_context):
        """[SDET-091] Unparseable data returns uncertain."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        result = det.detect(42)
        assert result.eval_type is None
        assert result.confidence == 'uncertain'
        assert 'Could not parse' in result.reason


class TestDetectFromCsvHeaders:
    """Tests for CSV header convenience method."""

    def test_SDET_100_csv_rating_headers(self, app, app_context):
        """[SDET-100] CSV headers with question/answer detected as rating."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect_from_csv_headers(['Question', 'Answer', 'ID'])
        assert result.eval_type == EvaluationType.RATING

    def test_SDET_101_csv_labeling_headers(self, app, app_context):
        """[SDET-101] CSV headers with document/sentiment detected as labeling."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        # Use 'Document' (labeling-only content field, not in RATING_CONTENT_FIELDS)
        result = det.detect_from_csv_headers(['Document', 'Sentiment'])
        assert result.eval_type == EvaluationType.LABELING

    def test_SDET_102_csv_case_insensitive(self, app, app_context):
        """[SDET-102] CSV header detection is case-insensitive."""
        from services.data_import.schema_detector import SchemaDetector, EvaluationType
        det = SchemaDetector()
        result = det.detect_from_csv_headers(['IS_HUMAN', 'TEXT'])
        assert result.eval_type == EvaluationType.AUTHENTICITY


class TestFieldDocumentation:
    """Tests for get_field_documentation."""

    def test_SDET_110_all_types_documented(self, app, app_context):
        """[SDET-110] All 6 evaluation types have documentation."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        docs = det.get_field_documentation()
        assert len(docs) == 6
        for key in ['authenticity', 'comparison', 'ranking', 'labeling', 'mail_rating', 'rating']:
            assert key in docs

    def test_SDET_111_doc_has_required_keys(self, app, app_context):
        """[SDET-111] Each doc entry has priority, fields, description, example."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        docs = det.get_field_documentation()
        for type_name, doc in docs.items():
            assert 'priority' in doc, f'{type_name} missing priority'
            assert 'fields' in doc, f'{type_name} missing fields'
            assert 'description' in doc, f'{type_name} missing description'
            assert 'example' in doc, f'{type_name} missing example'

    def test_SDET_112_priority_ordering(self, app, app_context):
        """[SDET-112] Priorities are correctly ordered 1-6."""
        from services.data_import.schema_detector import SchemaDetector
        det = SchemaDetector()
        docs = det.get_field_documentation()
        assert docs['authenticity']['priority'] == 1
        assert docs['comparison']['priority'] == 2
        assert docs['ranking']['priority'] == 3
        assert docs['labeling']['priority'] == 4
        assert docs['mail_rating']['priority'] == 5
        assert docs['rating']['priority'] == 6


class TestSingletonFactory:
    """Tests for module-level singleton and convenience function."""

    def test_SDET_120_singleton_creation(self, app, app_context):
        """[SDET-120] get_schema_detector returns SchemaDetector instance."""
        from services.data_import import schema_detector
        schema_detector._detector_instance = None

        det = schema_detector.get_schema_detector()
        assert isinstance(det, schema_detector.SchemaDetector)

        schema_detector._detector_instance = None

    def test_SDET_121_singleton_reuse(self, app, app_context):
        """[SDET-121] Repeated calls return same instance."""
        from services.data_import import schema_detector
        schema_detector._detector_instance = None

        d1 = schema_detector.get_schema_detector()
        d2 = schema_detector.get_schema_detector()
        assert d1 is d2

        schema_detector._detector_instance = None

    def test_SDET_122_convenience_function(self, app, app_context):
        """[SDET-122] detect_evaluation_type convenience function works."""
        from services.data_import.schema_detector import detect_evaluation_type, EvaluationType
        result = detect_evaluation_type({'question': 'q', 'response': 'a'})
        assert result.eval_type == EvaluationType.RATING

    def test_SDET_123_convenience_with_filename(self, app, app_context):
        """[SDET-123] detect_evaluation_type accepts filename parameter."""
        from services.data_import.schema_detector import detect_evaluation_type, EvaluationType
        result = detect_evaluation_type(
            {'text': 'sample', 'is_human': True},
            filename='authenticity_data.json'
        )
        assert result.eval_type == EvaluationType.AUTHENTICITY


class TestEvaluationType:
    """Tests for EvaluationType enum."""

    def test_SDET_130_all_types_exist(self, app, app_context):
        """[SDET-130] All 6 evaluation types defined."""
        from services.data_import.schema_detector import EvaluationType
        assert len(EvaluationType) == 6
        values = {e.value for e in EvaluationType}
        assert values == {'authenticity', 'comparison', 'ranking', 'labeling', 'mail_rating', 'rating'}
