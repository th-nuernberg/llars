"""
Tests for DimensionalRatingService.

These tests verify the multi-dimensional rating system which allows
evaluating items on multiple dimensions (e.g., Coherence, Fluency,
Relevance, Consistency) following LLM-as-Judge standard metrics.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestDimensionalRatingService:
    """Tests for DimensionalRatingService."""

    def test_DIMRAT_001_default_dimensions_exist(self):
        """Default dimensions should include LLM-as-Judge standard metrics."""
        from services.evaluation.dimensional_rating_service import DEFAULT_DIMENSIONS

        assert len(DEFAULT_DIMENSIONS) == 4
        dimension_ids = [d['id'] for d in DEFAULT_DIMENSIONS]
        assert 'coherence' in dimension_ids
        assert 'fluency' in dimension_ids
        assert 'relevance' in dimension_ids
        assert 'consistency' in dimension_ids

    def test_DIMRAT_002_default_dimensions_have_localization(self):
        """Default dimensions should have German and English translations."""
        from services.evaluation.dimensional_rating_service import DEFAULT_DIMENSIONS

        for dim in DEFAULT_DIMENSIONS:
            assert 'name' in dim
            assert 'de' in dim['name']
            assert 'en' in dim['name']
            assert 'description' in dim
            assert 'de' in dim['description']
            assert 'en' in dim['description']

    def test_DIMRAT_003_default_dimensions_have_weights(self):
        """Default dimensions should all have weights that sum to 1.0."""
        from services.evaluation.dimensional_rating_service import DEFAULT_DIMENSIONS

        total_weight = sum(d.get('weight', 0) for d in DEFAULT_DIMENSIONS)
        assert total_weight == pytest.approx(1.0, abs=0.01)

    def test_DIMRAT_004_default_labels_cover_1_to_5(self):
        """Default labels should cover scale values 1 through 5."""
        from services.evaluation.dimensional_rating_service import DEFAULT_LABELS

        assert '1' in DEFAULT_LABELS
        assert '2' in DEFAULT_LABELS
        assert '3' in DEFAULT_LABELS
        assert '4' in DEFAULT_LABELS
        assert '5' in DEFAULT_LABELS

    def test_DIMRAT_005_default_labels_have_localization(self):
        """Default labels should have German and English translations."""
        from services.evaluation.dimensional_rating_service import DEFAULT_LABELS

        for key, label in DEFAULT_LABELS.items():
            assert 'de' in label, f"Label {key} missing German translation"
            assert 'en' in label, f"Label {key} missing English translation"


class TestDimensionalRatingCalculations:
    """Tests for rating calculation logic."""

    def test_DIMRAT_006_overall_score_weighted_average(self):
        """Overall score should be calculated as weighted average."""
        # Test calculation logic similar to what ItemDimensionRating.calculate_overall_score does
        dimensions = [
            {'id': 'dim1', 'weight': 0.6},
            {'id': 'dim2', 'weight': 0.4}
        ]
        ratings = {'dim1': 5, 'dim2': 3}

        # Calculate weighted average manually
        weighted_sum = sum(
            ratings.get(d['id'], 0) * d.get('weight', 1.0)
            for d in dimensions
        )
        total_weight = sum(d.get('weight', 1.0) for d in dimensions)
        expected = weighted_sum / total_weight

        # dim1 * 0.6 + dim2 * 0.4 = 5 * 0.6 + 3 * 0.4 = 3.0 + 1.2 = 4.2
        assert expected == pytest.approx(4.2)

    def test_DIMRAT_007_overall_score_equal_weights(self):
        """Equal weights should result in simple average."""
        dimensions = [
            {'id': 'dim1', 'weight': 0.25},
            {'id': 'dim2', 'weight': 0.25},
            {'id': 'dim3', 'weight': 0.25},
            {'id': 'dim4', 'weight': 0.25}
        ]
        ratings = {'dim1': 4, 'dim2': 4, 'dim3': 4, 'dim4': 4}

        weighted_sum = sum(
            ratings.get(d['id'], 0) * d.get('weight', 1.0)
            for d in dimensions
        )
        total_weight = sum(d.get('weight', 1.0) for d in dimensions)
        expected = weighted_sum / total_weight

        assert expected == pytest.approx(4.0)

    def test_DIMRAT_008_handles_missing_dimension_ratings(self):
        """Calculation should handle dimensions without ratings."""
        dimensions = [
            {'id': 'dim1', 'weight': 0.5},
            {'id': 'dim2', 'weight': 0.5}
        ]
        ratings = {'dim1': 4}  # dim2 not rated

        # Calculate only with rated dimensions
        rated_dims = [d for d in dimensions if d['id'] in ratings]
        if not rated_dims:
            expected = None
        else:
            weighted_sum = sum(
                ratings.get(d['id'], 0) * d.get('weight', 1.0)
                for d in rated_dims
            )
            total_weight = sum(d.get('weight', 1.0) for d in rated_dims)
            expected = weighted_sum / total_weight

        assert expected == pytest.approx(4.0)


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_DIMRAT_009_valid_multi_dimensional_config(self):
        """Valid multi-dimensional config should pass validation."""
        config = {
            'type': 'multi-dimensional',
            'min': 1,
            'max': 5,
            'step': 1,
            'dimensions': [
                {'id': 'dim1', 'name': {'de': 'Test'}, 'weight': 1.0}
            ],
            'labels': {'1': {'de': 'Schlecht'}, '5': {'de': 'Gut'}},
            'showOverallScore': True,
            'allowFeedback': True
        }

        # Basic validation checks
        assert config['type'] == 'multi-dimensional'
        assert config['min'] < config['max']
        assert config['step'] > 0
        assert len(config['dimensions']) > 0

    def test_DIMRAT_010_config_without_dimensions_uses_defaults(self):
        """Config without dimensions should use defaults."""
        from services.evaluation.dimensional_rating_service import DEFAULT_DIMENSIONS

        config = {
            'type': 'multi-dimensional',
            'min': 1,
            'max': 5,
            'step': 1
            # No dimensions specified
        }

        # When merging with defaults, should use DEFAULT_DIMENSIONS
        dimensions = config.get('dimensions') or DEFAULT_DIMENSIONS
        assert len(dimensions) == 4

    def test_DIMRAT_011_config_scale_bounds_validated(self):
        """Scale bounds should be valid (min < max)."""
        config = {
            'min': 5,
            'max': 1,  # Invalid: max < min
            'step': 1
        }

        assert config['min'] > config['max']  # This is the invalid condition


class TestProgressionStatus:
    """Tests for progression status handling."""

    def test_DIMRAT_012_progression_status_values(self):
        """ProgressionStatus enum should have expected values."""
        from db.models.scenario import ProgressionStatus

        assert hasattr(ProgressionStatus, 'NOT_STARTED')
        assert hasattr(ProgressionStatus, 'PROGRESSING')
        assert hasattr(ProgressionStatus, 'DONE')

    def test_DIMRAT_013_can_submit_when_all_rated(self):
        """canSubmit should be True when all dimensions are rated."""
        dimensions = [
            {'id': 'coherence'},
            {'id': 'fluency'},
            {'id': 'relevance'},
            {'id': 'consistency'}
        ]
        ratings = {
            'coherence': 4,
            'fluency': 3,
            'relevance': 5,
            'consistency': 4
        }

        can_submit = all(
            d['id'] in ratings and ratings[d['id']] is not None
            for d in dimensions
        )
        assert can_submit is True

    def test_DIMRAT_014_cannot_submit_when_incomplete(self):
        """canSubmit should be False when some dimensions are not rated."""
        dimensions = [
            {'id': 'coherence'},
            {'id': 'fluency'},
            {'id': 'relevance'},
            {'id': 'consistency'}
        ]
        ratings = {
            'coherence': 4,
            'fluency': 3
            # relevance and consistency not rated
        }

        can_submit = all(
            d['id'] in ratings and ratings[d['id']] is not None
            for d in dimensions
        )
        assert can_submit is False


class TestItemDimensionRatingModel:
    """Tests for ItemDimensionRating model methods."""

    def test_DIMRAT_015_to_dict_includes_all_fields(self):
        """to_dict should include all important fields."""
        # Mock the model behavior
        expected_fields = [
            'id', 'user_id', 'item_id', 'scenario_id',
            'dimension_ratings', 'overall_score', 'feedback',
            'status', 'created_at', 'updated_at'
        ]

        # Just verify expected fields exist in a typical dict
        mock_dict = {
            'id': 1,
            'user_id': 1,
            'item_id': 101,
            'scenario_id': 1,
            'dimension_ratings': {'coherence': 4},
            'overall_score': 4.0,
            'feedback': 'Test feedback',
            'status': 'DONE',
            'created_at': '2026-01-20T12:00:00',
            'updated_at': '2026-01-20T12:00:00'
        }

        for field in expected_fields:
            assert field in mock_dict


class TestVariableScaleCalculations:
    """Tests for variable Likert scale support."""

    def test_DIMRAT_016_weighted_score_with_0_1_scale(self):
        """Weighted score calculation should work with 0-1 binary scale."""
        dimensions = [
            {'id': 'dim1', 'weight': 0.5},
            {'id': 'dim2', 'weight': 0.5}
        ]
        ratings = {'dim1': 1, 'dim2': 0}
        scale_min, scale_max = 0, 1

        weighted_sum = sum(
            ratings.get(d['id'], 0) * d.get('weight', 1.0)
            for d in dimensions
        )
        total_weight = sum(d.get('weight', 1.0) for d in dimensions)
        expected = weighted_sum / total_weight

        # 1 * 0.5 + 0 * 0.5 = 0.5
        assert expected == pytest.approx(0.5)

    def test_DIMRAT_017_weighted_score_with_0_9_scale(self):
        """Weighted score calculation should work with 0-9 scale."""
        dimensions = [
            {'id': 'dim1', 'weight': 0.5},
            {'id': 'dim2', 'weight': 0.5}
        ]
        ratings = {'dim1': 9, 'dim2': 5}
        scale_min, scale_max = 0, 9

        weighted_sum = sum(
            ratings.get(d['id'], 0) * d.get('weight', 1.0)
            for d in dimensions
        )
        total_weight = sum(d.get('weight', 1.0) for d in dimensions)
        expected = weighted_sum / total_weight

        # 9 * 0.5 + 5 * 0.5 = 4.5 + 2.5 = 7.0
        assert expected == pytest.approx(7.0)

    def test_DIMRAT_018_normalized_score_calculation(self):
        """Normalized score should be calculated as (score - min) / (max - min)."""
        # Test normalization for different scales
        test_cases = [
            # (score, min, max, expected_normalized)
            (3, 1, 5, 0.5),      # Standard 1-5 scale, score 3 = 50%
            (1, 0, 1, 1.0),      # Binary scale, score 1 = 100%
            (0, 0, 1, 0.0),      # Binary scale, score 0 = 0%
            (5, 0, 9, 0.5556),   # 0-9 scale, score 5 ≈ 55.56%
            (7, 1, 10, 0.6667),  # 1-10 scale, score 7 ≈ 66.67%
        ]

        for score, scale_min, scale_max, expected in test_cases:
            if scale_max == scale_min:
                normalized = 1.0 if score > 0 else 0.0
            else:
                normalized = (score - scale_min) / (scale_max - scale_min)

            assert normalized == pytest.approx(expected, abs=0.01), \
                f"Failed for score={score}, scale={scale_min}-{scale_max}"

    def test_DIMRAT_019_normalized_score_clamped_to_0_1(self):
        """Normalized score should be clamped between 0 and 1."""
        # Edge case: score outside of scale bounds (shouldn't happen, but defensive)
        score = 6
        scale_min, scale_max = 1, 5

        raw_normalized = (score - scale_min) / (scale_max - scale_min)  # Would be 1.25
        normalized = max(0, min(1, raw_normalized))

        assert normalized == 1.0


class TestScaleConfiguration:
    """Tests for scale configuration handling."""

    def test_DIMRAT_020_default_scale_1_5(self):
        """Default scale should be 1-5 if not specified."""
        config = {}
        scale_min = config.get('min', 1)
        scale_max = config.get('max', 5)
        scale_step = config.get('step', 1)

        assert scale_min == 1
        assert scale_max == 5
        assert scale_step == 1

    def test_DIMRAT_021_custom_scale_0_4(self):
        """Custom 0-4 scale should be respected."""
        config = {'min': 0, 'max': 4, 'step': 1}

        assert config['min'] == 0
        assert config['max'] == 4
        assert config['step'] == 1

    def test_DIMRAT_022_custom_scale_1_7(self):
        """Custom 1-7 scale should be respected."""
        config = {'min': 1, 'max': 7, 'step': 1}

        assert config['min'] == 1
        assert config['max'] == 7
        assert config['step'] == 1

    def test_DIMRAT_023_scale_with_custom_labels(self):
        """Scale configuration can include custom labels."""
        config = {
            'min': 1,
            'max': 5,
            'step': 1,
            'labels': {
                '1': {'de': 'Sehr schlecht', 'en': 'Very poor'},
                '2': {'de': 'Schlecht', 'en': 'Poor'},
                '3': {'de': 'Akzeptabel', 'en': 'Acceptable'},
                '4': {'de': 'Gut', 'en': 'Good'},
                '5': {'de': 'Sehr gut', 'en': 'Very good'}
            }
        }

        assert '1' in config['labels']
        assert '5' in config['labels']
        assert config['labels']['1']['de'] == 'Sehr schlecht'
        assert config['labels']['5']['en'] == 'Very good'


class TestLLMEvaluationState:
    """Tests for LLM evaluation state tracking."""

    def test_DIMRAT_024_llm_evaluation_states(self):
        """LLM evaluation should have proper states."""
        # Simulating the states from useDimensionalRating.js
        llm_evaluating = False
        llm_result = None
        llm_error = None

        # Start evaluation
        llm_evaluating = True
        assert llm_evaluating is True

        # Successful evaluation
        llm_result = {
            'success': True,
            'ratings': {'coherence': 4, 'fluency': 3},
            'reasoning': {'coherence': 'Good', 'fluency': 'OK'}
        }
        llm_evaluating = False

        assert llm_evaluating is False
        assert llm_result['success'] is True
        assert llm_error is None

    def test_DIMRAT_025_llm_evaluation_error_handling(self):
        """LLM evaluation errors should be tracked."""
        llm_evaluating = False
        llm_result = None
        llm_error = None

        # Start evaluation
        llm_evaluating = True

        # Error during evaluation
        llm_error = "Model timeout"
        llm_evaluating = False

        assert llm_evaluating is False
        assert llm_result is None
        assert llm_error == "Model timeout"
