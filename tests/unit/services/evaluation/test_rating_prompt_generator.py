"""
Tests for RatingPromptGenerator service.

These tests verify the dynamic LLM prompt generation for multi-dimensional
rating evaluation with variable Likert scales.
"""

import pytest
import json


class TestRatingPromptGeneratorSystemPrompt:
    """Tests for system prompt generation."""

    def test_RPGEN_001_generate_system_prompt_german(self):
        """System prompt should be generated in German by default."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [
            {'id': 'coherence', 'name': {'de': 'Kohärenz', 'en': 'Coherence'}, 'weight': 0.5},
            {'id': 'fluency', 'name': {'de': 'Flüssigkeit', 'en': 'Fluency'}, 'weight': 0.5}
        ]
        scale_config = {'min': 1, 'max': 5, 'step': 1}

        prompt = RatingPromptGenerator.generate_system_prompt(
            dimensions, scale_config, locale='de'
        )

        assert 'Kohärenz' in prompt
        assert 'Flüssigkeit' in prompt
        assert '1' in prompt
        assert '5' in prompt
        assert 'mehrdimensionale Bewertung' in prompt

    def test_RPGEN_002_generate_system_prompt_english(self):
        """System prompt should be generated in English when specified."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [
            {'id': 'coherence', 'name': {'de': 'Kohärenz', 'en': 'Coherence'}, 'weight': 1.0}
        ]
        scale_config = {'min': 1, 'max': 5, 'step': 1}

        prompt = RatingPromptGenerator.generate_system_prompt(
            dimensions, scale_config, locale='en'
        )

        assert 'Coherence' in prompt
        assert 'multi-dimensional evaluation' in prompt

    def test_RPGEN_003_system_prompt_includes_scale_range(self):
        """System prompt should include the scale range."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [{'id': 'test', 'name': 'Test', 'weight': 1.0}]
        scale_config = {'min': 0, 'max': 9, 'step': 1}

        prompt = RatingPromptGenerator.generate_system_prompt(
            dimensions, scale_config, locale='de'
        )

        assert '0' in prompt
        assert '9' in prompt

    def test_RPGEN_004_system_prompt_includes_dimension_weights(self):
        """System prompt should include dimension weights."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [
            {'id': 'dim1', 'name': 'Dim 1', 'weight': 0.6},
            {'id': 'dim2', 'name': 'Dim 2', 'weight': 0.4}
        ]
        scale_config = {'min': 1, 'max': 5}

        prompt = RatingPromptGenerator.generate_system_prompt(
            dimensions, scale_config, locale='de'
        )

        assert '60%' in prompt
        assert '40%' in prompt


class TestRatingPromptGeneratorUserPrompt:
    """Tests for user prompt generation."""

    def test_RPGEN_005_generate_user_prompt_includes_content(self):
        """User prompt should include the content to be evaluated."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [{'id': 'quality', 'name': 'Quality', 'weight': 1.0}]
        scale_config = {'min': 1, 'max': 5}
        content = "This is the test content to evaluate."

        prompt = RatingPromptGenerator.generate_user_prompt(
            dimensions, content, scale_config, locale='de'
        )

        assert content in prompt

    def test_RPGEN_006_user_prompt_includes_dimension_schema(self):
        """User prompt should include JSON schema for dimensions."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [
            {'id': 'coherence', 'name': 'Coherence', 'weight': 0.5},
            {'id': 'fluency', 'name': 'Fluency', 'weight': 0.5}
        ]
        scale_config = {'min': 1, 'max': 5}

        prompt = RatingPromptGenerator.generate_user_prompt(
            dimensions, "Test content", scale_config, locale='de'
        )

        assert '"coherence"' in prompt
        assert '"fluency"' in prompt


class TestRatingPromptGeneratorOutputSchema:
    """Tests for JSON output schema generation."""

    def test_RPGEN_007_output_schema_has_ratings(self):
        """Output schema should have ratings property."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [{'id': 'quality', 'name': 'Quality', 'weight': 1.0}]
        scale_config = {'min': 1, 'max': 5}

        schema = RatingPromptGenerator.generate_output_schema(dimensions, scale_config)

        assert 'ratings' in schema['properties']
        assert 'quality' in schema['properties']['ratings']['properties']

    def test_RPGEN_008_output_schema_respects_scale_bounds(self):
        """Output schema should include correct min/max values."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [{'id': 'test', 'name': 'Test', 'weight': 1.0}]
        scale_config = {'min': 0, 'max': 4}

        schema = RatingPromptGenerator.generate_output_schema(dimensions, scale_config)

        rating_schema = schema['properties']['ratings']['properties']['test']
        assert rating_schema['minimum'] == 0
        assert rating_schema['maximum'] == 4

    def test_RPGEN_009_output_schema_required_fields(self):
        """Output schema should list required fields."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [
            {'id': 'dim1', 'name': 'Dim 1', 'weight': 0.5},
            {'id': 'dim2', 'name': 'Dim 2', 'weight': 0.5}
        ]
        scale_config = {'min': 1, 'max': 5}

        schema = RatingPromptGenerator.generate_output_schema(dimensions, scale_config)

        assert 'ratings' in schema['required']
        assert 'reasoning' in schema['required']
        assert 'overall_score' in schema['required']
        assert 'confidence' in schema['required']


class TestRatingPromptGeneratorParsing:
    """Tests for LLM response parsing."""

    def test_RPGEN_010_parse_valid_json_response(self):
        """Parser should extract ratings from valid JSON response."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [
            {'id': 'coherence', 'name': 'Coherence', 'weight': 0.5},
            {'id': 'fluency', 'name': 'Fluency', 'weight': 0.5}
        ]
        scale_config = {'min': 1, 'max': 5}

        response = json.dumps({
            "ratings": {"coherence": 4, "fluency": 3},
            "reasoning": {"coherence": "Good", "fluency": "Acceptable"},
            "overall_score": 3.5,
            "summary": "Test summary",
            "confidence": 0.85
        })

        result = RatingPromptGenerator.parse_llm_rating_response(
            response, dimensions, scale_config
        )

        assert result['success'] is True
        assert result['ratings']['coherence'] == 4
        assert result['ratings']['fluency'] == 3
        assert result['overall_score'] == 3.5
        assert result['confidence'] == 0.85

    def test_RPGEN_011_parse_json_in_markdown_codeblock(self):
        """Parser should extract JSON from markdown code blocks."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [{'id': 'quality', 'name': 'Quality', 'weight': 1.0}]
        scale_config = {'min': 1, 'max': 5}

        response = '''Here is my evaluation:

```json
{
  "ratings": {"quality": 4},
  "reasoning": {"quality": "Well done"},
  "overall_score": 4.0,
  "summary": "Good quality",
  "confidence": 0.9
}
```
'''

        result = RatingPromptGenerator.parse_llm_rating_response(
            response, dimensions, scale_config
        )

        assert result['success'] is True
        assert result['ratings']['quality'] == 4

    def test_RPGEN_012_parse_rejects_out_of_range_values(self):
        """Parser should reject ratings outside the scale range."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [{'id': 'quality', 'name': 'Quality', 'weight': 1.0}]
        scale_config = {'min': 1, 'max': 5}

        response = json.dumps({
            "ratings": {"quality": 10},  # Out of range
            "reasoning": {"quality": "Test"},
            "overall_score": 5.0,
            "confidence": 0.5
        })

        result = RatingPromptGenerator.parse_llm_rating_response(
            response, dimensions, scale_config
        )

        assert result['success'] is False
        assert len(result['errors']) > 0
        assert 'quality' not in result['ratings']

    def test_RPGEN_013_parse_handles_missing_dimensions(self):
        """Parser should report missing dimension ratings."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [
            {'id': 'dim1', 'name': 'Dim 1', 'weight': 0.5},
            {'id': 'dim2', 'name': 'Dim 2', 'weight': 0.5}
        ]
        scale_config = {'min': 1, 'max': 5}

        response = json.dumps({
            "ratings": {"dim1": 4},  # dim2 missing
            "reasoning": {"dim1": "OK"},
            "overall_score": 4.0,
            "confidence": 0.8
        })

        result = RatingPromptGenerator.parse_llm_rating_response(
            response, dimensions, scale_config
        )

        assert result['success'] is False
        assert 'Missing rating for dimension: dim2' in result['errors']

    def test_RPGEN_014_parse_handles_invalid_json(self):
        """Parser should handle invalid JSON gracefully."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [{'id': 'test', 'name': 'Test', 'weight': 1.0}]
        scale_config = {'min': 1, 'max': 5}

        response = "This is not valid JSON { broken"

        result = RatingPromptGenerator.parse_llm_rating_response(
            response, dimensions, scale_config
        )

        assert result['success'] is False
        assert len(result['errors']) > 0


class TestRatingPromptGeneratorScalePresets:
    """Tests for scale label presets."""

    def test_RPGEN_015_scale_preset_0_1_exists(self):
        """Binary scale 0-1 preset should exist."""
        from services.evaluation.rating_prompt_generator import SCALE_LABEL_PRESETS

        assert '0-1' in SCALE_LABEL_PRESETS
        assert 0 in SCALE_LABEL_PRESETS['0-1']['de']
        assert 1 in SCALE_LABEL_PRESETS['0-1']['de']

    def test_RPGEN_016_scale_preset_1_5_exists(self):
        """Standard Likert 1-5 preset should exist."""
        from services.evaluation.rating_prompt_generator import SCALE_LABEL_PRESETS

        assert '1-5' in SCALE_LABEL_PRESETS
        for i in range(1, 6):
            assert i in SCALE_LABEL_PRESETS['1-5']['de']

    def test_RPGEN_017_scale_preset_0_4_exists(self):
        """Four-point 0-4 scale preset should exist."""
        from services.evaluation.rating_prompt_generator import SCALE_LABEL_PRESETS

        assert '0-4' in SCALE_LABEL_PRESETS
        for i in range(0, 5):
            assert i in SCALE_LABEL_PRESETS['0-4']['de']

    def test_RPGEN_018_scale_preset_1_7_exists(self):
        """Extended Likert 1-7 preset should exist."""
        from services.evaluation.rating_prompt_generator import SCALE_LABEL_PRESETS

        assert '1-7' in SCALE_LABEL_PRESETS
        for i in range(1, 8):
            assert i in SCALE_LABEL_PRESETS['1-7']['de']

    def test_RPGEN_019_scale_preset_0_9_exists(self):
        """Ten-point 0-9 scale preset should exist."""
        from services.evaluation.rating_prompt_generator import SCALE_LABEL_PRESETS

        assert '0-9' in SCALE_LABEL_PRESETS
        # Check key points exist
        assert 0 in SCALE_LABEL_PRESETS['0-9']['de']
        assert 9 in SCALE_LABEL_PRESETS['0-9']['de']

    def test_RPGEN_020_scale_preset_1_10_exists(self):
        """Ten-point 1-10 scale preset should exist."""
        from services.evaluation.rating_prompt_generator import SCALE_LABEL_PRESETS

        assert '1-10' in SCALE_LABEL_PRESETS
        assert 1 in SCALE_LABEL_PRESETS['1-10']['de']
        assert 10 in SCALE_LABEL_PRESETS['1-10']['de']


class TestGetScaleLabelsForRange:
    """Tests for get_scale_labels_for_range function."""

    def test_RPGEN_021_get_labels_for_known_range(self):
        """Should return preset labels for known scale ranges."""
        from services.evaluation.rating_prompt_generator import get_scale_labels_for_range

        labels = get_scale_labels_for_range(1, 5, 'de')

        assert 1 in labels
        assert 5 in labels
        assert labels[1] == 'Sehr schlecht'
        assert labels[5] == 'Sehr gut'

    def test_RPGEN_022_get_labels_for_unknown_range_generates_defaults(self):
        """Should generate default labels for unknown scale ranges."""
        from services.evaluation.rating_prompt_generator import get_scale_labels_for_range

        labels = get_scale_labels_for_range(1, 100, 'de')

        assert 1 in labels
        assert 100 in labels
        # Middle point for large scales
        assert 50 in labels

    def test_RPGEN_023_get_labels_respects_locale(self):
        """Should return labels in the requested locale."""
        from services.evaluation.rating_prompt_generator import get_scale_labels_for_range

        labels_de = get_scale_labels_for_range(1, 5, 'de')
        labels_en = get_scale_labels_for_range(1, 5, 'en')

        assert labels_de[1] == 'Sehr schlecht'
        assert labels_en[1] == 'Very poor'


class TestGenerateRatingPrompt:
    """Tests for the convenience generate_rating_prompt method."""

    def test_RPGEN_024_generate_rating_prompt_returns_both_prompts(self):
        """Convenience method should return both system and user prompts."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [{'id': 'quality', 'name': 'Quality', 'weight': 1.0}]
        scale_config = {'min': 1, 'max': 5}
        content = "Test content"

        result = RatingPromptGenerator.generate_rating_prompt(
            dimensions, scale_config, content, locale='de'
        )

        assert 'system_prompt' in result
        assert 'user_prompt' in result
        assert len(result['system_prompt']) > 0
        assert len(result['user_prompt']) > 0
        assert content in result['user_prompt']


class TestPromptHintIntegration:
    """Tests for prompt_hint field integration."""

    def test_RPGEN_025_prompt_hint_included_in_system_prompt(self):
        """Prompt hints should be included in the system prompt."""
        from services.evaluation.rating_prompt_generator import RatingPromptGenerator

        dimensions = [
            {
                'id': 'coherence',
                'name': {'de': 'Kohärenz'},
                'weight': 1.0,
                'prompt_hint': 'Achte besonders auf logischen Zusammenhang'
            }
        ]
        scale_config = {'min': 1, 'max': 5}

        prompt = RatingPromptGenerator.generate_system_prompt(
            dimensions, scale_config, locale='de'
        )

        assert 'Achte besonders auf logischen Zusammenhang' in prompt
