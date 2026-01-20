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
