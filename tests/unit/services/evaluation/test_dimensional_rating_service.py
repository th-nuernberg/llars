"""
Tests for DimensionalRatingService.

Comprehensive unit tests covering the multi-dimensional rating system:
- Rating initialization from config
- Score computation (weighted, normalized)
- Progress tracking
- Validation
- Content building
- Scenario config resolution
- Save and update workflows

Test IDs: [DIM_RATE_SVC_001] through [DIM_RATE_SVC_045]
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime


# =============================================================================
# Constants / Defaults
# =============================================================================

class TestDefaultConstants:
    """Tests for module-level constants."""

    def test_DIM_RATE_SVC_001_default_dimensions_exist(self):
        """Default dimensions should include LLM-as-Judge standard metrics."""
        from services.evaluation.dimensional_rating_service import DEFAULT_DIMENSIONS

        assert len(DEFAULT_DIMENSIONS) == 4
        dimension_ids = [d['id'] for d in DEFAULT_DIMENSIONS]
        assert 'coherence' in dimension_ids
        assert 'fluency' in dimension_ids
        assert 'relevance' in dimension_ids
        assert 'consistency' in dimension_ids

    def test_DIM_RATE_SVC_002_default_dimensions_have_localization(self):
        """Default dimensions should have German and English translations."""
        from services.evaluation.dimensional_rating_service import DEFAULT_DIMENSIONS

        for dim in DEFAULT_DIMENSIONS:
            assert 'name' in dim
            assert 'de' in dim['name']
            assert 'en' in dim['name']
            assert 'description' in dim
            assert 'de' in dim['description']
            assert 'en' in dim['description']

    def test_DIM_RATE_SVC_003_default_weights_sum_to_one(self):
        """Default dimension weights should sum to 1.0."""
        from services.evaluation.dimensional_rating_service import DEFAULT_DIMENSIONS

        total_weight = sum(d.get('weight', 0) for d in DEFAULT_DIMENSIONS)
        assert total_weight == pytest.approx(1.0, abs=0.01)

    def test_DIM_RATE_SVC_004_mail_rating_dimensions_exist(self):
        """Mail rating should have LLARS-specific dimensions."""
        from services.evaluation.dimensional_rating_service import MAIL_RATING_DIMENSIONS

        assert len(MAIL_RATING_DIMENSIONS) == 4
        ids = [d['id'] for d in MAIL_RATING_DIMENSIONS]
        assert 'counsellor_coherence' in ids
        assert 'client_coherence' in ids
        assert 'quality' in ids
        assert 'overall' in ids

    def test_DIM_RATE_SVC_005_mail_rating_weights_sum_to_one(self):
        """Mail rating dimension weights should sum to 1.0."""
        from services.evaluation.dimensional_rating_service import MAIL_RATING_DIMENSIONS

        total_weight = sum(d.get('weight', 0) for d in MAIL_RATING_DIMENSIONS)
        assert total_weight == pytest.approx(1.0, abs=0.01)

    def test_DIM_RATE_SVC_006_default_labels_cover_1_to_5(self):
        """Default labels should cover scale values 1 through 5."""
        from services.evaluation.dimensional_rating_service import DEFAULT_LABELS

        for key in ['1', '2', '3', '4', '5']:
            assert key in DEFAULT_LABELS
            assert 'de' in DEFAULT_LABELS[key]
            assert 'en' in DEFAULT_LABELS[key]

    def test_DIM_RATE_SVC_007_mail_rating_labels_cover_1_to_5(self):
        """Mail rating labels should cover scale values 1 through 5."""
        from services.evaluation.dimensional_rating_service import MAIL_RATING_LABELS

        for key in ['1', '2', '3', '4', '5']:
            assert key in MAIL_RATING_LABELS


# =============================================================================
# Weighted Score Calculation (_calculate_weighted_score)
# =============================================================================

class TestCalculateWeightedScore:
    """Tests for _calculate_weighted_score static method."""

    def test_DIM_RATE_SVC_008_weighted_score_basic(self):
        """Weighted score should be correctly calculated."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'dim1': 5, 'dim2': 3}
        weights = {'dim1': 0.6, 'dim2': 0.4}
        result = DimensionalRatingService._calculate_weighted_score(ratings, weights)
        # 5 * 0.6 + 3 * 0.4 = 4.2
        assert result == pytest.approx(4.2)

    def test_DIM_RATE_SVC_009_weighted_score_equal_weights(self):
        """Equal weights should produce simple average."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 4, 'b': 4, 'c': 4, 'd': 4}
        weights = {'a': 0.25, 'b': 0.25, 'c': 0.25, 'd': 0.25}
        result = DimensionalRatingService._calculate_weighted_score(ratings, weights)
        assert result == pytest.approx(4.0)

    def test_DIM_RATE_SVC_010_weighted_score_empty_ratings(self):
        """Empty ratings should return 0.0."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        result = DimensionalRatingService._calculate_weighted_score({}, {'a': 1.0})
        assert result == 0.0

    def test_DIM_RATE_SVC_011_weighted_score_none_values_skipped(self):
        """None values in ratings should be skipped."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 5, 'b': None}
        weights = {'a': 0.5, 'b': 0.5}
        result = DimensionalRatingService._calculate_weighted_score(ratings, weights)
        # Only 'a' is counted: 5 * 0.5 / 0.5 = 5.0
        assert result == pytest.approx(5.0)

    def test_DIM_RATE_SVC_012_weighted_score_missing_weight_defaults_to_one(self):
        """Missing weight for a dimension should default to 1.0."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 4, 'b': 2}
        weights = {'a': 1.0}  # 'b' missing from weights
        result = DimensionalRatingService._calculate_weighted_score(ratings, weights)
        # 4 * 1.0 + 2 * 1.0 = 6.0 / 2.0 = 3.0
        assert result == pytest.approx(3.0)

    def test_DIM_RATE_SVC_013_weighted_score_single_dimension(self):
        """Single dimension should return that score."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'only': 3}
        weights = {'only': 1.0}
        result = DimensionalRatingService._calculate_weighted_score(ratings, weights)
        assert result == pytest.approx(3.0)

    def test_DIM_RATE_SVC_014_weighted_score_rounding(self):
        """Result should be rounded to 2 decimal places."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 3, 'b': 4, 'c': 5}
        weights = {'a': 0.333, 'b': 0.333, 'c': 0.334}
        result = DimensionalRatingService._calculate_weighted_score(ratings, weights)
        assert isinstance(result, float)
        # Check that it has at most 2 decimal places
        assert result == round(result, 2)


# =============================================================================
# Normalized Score Calculation (calculate_normalized_score)
# =============================================================================

class TestCalculateNormalizedScore:
    """Tests for calculate_normalized_score static method."""

    def test_DIM_RATE_SVC_015_normalized_basic_1_5_scale(self):
        """Normalized score on 1-5 scale should be (score - 1) / 4."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 3}
        weights = {'a': 1.0}
        result = DimensionalRatingService.calculate_normalized_score(
            ratings, weights, scale_min=1, scale_max=5
        )
        # raw = 3.0, normalized = (3 - 1) / (5 - 1) = 0.5
        assert result == pytest.approx(0.5)

    def test_DIM_RATE_SVC_016_normalized_0_1_scale(self):
        """Normalized score on 0-1 binary scale."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 1}
        weights = {'a': 1.0}
        result = DimensionalRatingService.calculate_normalized_score(
            ratings, weights, scale_min=0, scale_max=1
        )
        assert result == pytest.approx(1.0)

    def test_DIM_RATE_SVC_017_normalized_empty_returns_none(self):
        """Empty ratings should return None."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        result = DimensionalRatingService.calculate_normalized_score(
            {}, {'a': 1.0}, scale_min=1, scale_max=5
        )
        assert result is None

    def test_DIM_RATE_SVC_018_normalized_equal_min_max(self):
        """When min equals max, return 1.0 if score > 0, else 0.0."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 5}
        weights = {'a': 1.0}
        result = DimensionalRatingService.calculate_normalized_score(
            ratings, weights, scale_min=5, scale_max=5
        )
        assert result == 1.0

    def test_DIM_RATE_SVC_019_normalized_clamped_to_0_1(self):
        """Normalized score should be clamped between 0.0 and 1.0."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        # Score above max
        ratings = {'a': 7}
        weights = {'a': 1.0}
        result = DimensionalRatingService.calculate_normalized_score(
            ratings, weights, scale_min=1, scale_max=5
        )
        assert result <= 1.0
        assert result >= 0.0

    def test_DIM_RATE_SVC_020_normalized_0_9_scale(self):
        """Normalized score on 0-9 scale."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 4.5, 'b': 4.5}
        weights = {'a': 0.5, 'b': 0.5}
        result = DimensionalRatingService.calculate_normalized_score(
            ratings, weights, scale_min=0, scale_max=9
        )
        # raw = 4.5, normalized = 4.5 / 9 = 0.5
        assert result == pytest.approx(0.5)


# =============================================================================
# Content Building (_build_content_text)
# =============================================================================

class TestBuildContentText:
    """Tests for _build_content_text static method."""

    def test_DIM_RATE_SVC_021_build_content_basic(self):
        """Should format messages as [sender]\\ncontent."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        messages = [
            {'sender': 'Alice', 'content': 'Hello'},
            {'sender': 'Bob', 'content': 'Hi there'},
        ]
        result = DimensionalRatingService._build_content_text(messages)
        assert '[Alice]' in result
        assert 'Hello' in result
        assert '[Bob]' in result
        assert 'Hi there' in result

    def test_DIM_RATE_SVC_022_build_content_empty(self):
        """Empty messages list should return empty string."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        result = DimensionalRatingService._build_content_text([])
        assert result == ''

    def test_DIM_RATE_SVC_023_build_content_missing_sender(self):
        """Missing sender should default to 'Unknown'."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        messages = [{'content': 'Hello'}]
        result = DimensionalRatingService._build_content_text(messages)
        assert '[Unknown]' in result

    def test_DIM_RATE_SVC_024_build_content_separator(self):
        """Messages should be separated by double newline."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        messages = [
            {'sender': 'A', 'content': 'First'},
            {'sender': 'B', 'content': 'Second'},
        ]
        result = DimensionalRatingService._build_content_text(messages)
        assert '\n\n' in result


# =============================================================================
# Scenario Config (get_scenario_config) - requires DB
# =============================================================================

class TestGetScenarioConfig:
    """Tests for get_scenario_config that require database."""

    def test_DIM_RATE_SVC_025_config_not_found(self, app, db):
        """Non-existent scenario should return error."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        with app.app_context():
            result = DimensionalRatingService.get_scenario_config(99999)
            assert 'error' in result

    def test_DIM_RATE_SVC_026_config_defaults_for_rating(self, app, db):
        """Rating scenario without config should get default dimensions."""
        from services.evaluation.dimensional_rating_service import (
            DimensionalRatingService, DEFAULT_DIMENSIONS
        )
        from db.models.scenario import RatingScenarios, FeatureFunctionType

        with app.app_context():
            ftype = FeatureFunctionType(function_type_id=2, name='rating')
            db.session.add(ftype)
            db.session.flush()

            scenario = RatingScenarios(
                scenario_name='Test Rating',
                function_type_id=2,
                config_json={}
            )
            db.session.add(scenario)
            db.session.commit()

            config = DimensionalRatingService.get_scenario_config(scenario.id)
            assert 'error' not in config
            assert config['dimensions'] == DEFAULT_DIMENSIONS
            assert config['min'] == 1
            assert config['max'] == 5
            assert config['step'] == 1
            assert config['showOverallScore'] is True
            assert config['allowFeedback'] is True

    def test_DIM_RATE_SVC_027_config_defaults_for_mail_rating(self, app, db):
        """Mail rating scenario should get mail-specific dimensions."""
        from services.evaluation.dimensional_rating_service import (
            DimensionalRatingService, MAIL_RATING_DIMENSIONS, MAIL_RATING_LABELS
        )
        from db.models.scenario import RatingScenarios, FeatureFunctionType

        with app.app_context():
            ftype = FeatureFunctionType(function_type_id=3, name='mail_rating')
            db.session.add(ftype)
            db.session.flush()

            scenario = RatingScenarios(
                scenario_name='Test Mail Rating',
                function_type_id=3,
                config_json={}
            )
            db.session.add(scenario)
            db.session.commit()

            config = DimensionalRatingService.get_scenario_config(scenario.id)
            assert config['dimensions'] == MAIL_RATING_DIMENSIONS
            assert config['labels'] == MAIL_RATING_LABELS

    def test_DIM_RATE_SVC_028_config_preserves_custom_settings(self, app, db):
        """Custom config values should not be overridden."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService
        from db.models.scenario import RatingScenarios, FeatureFunctionType

        with app.app_context():
            ftype = FeatureFunctionType(function_type_id=2, name='rating')
            db.session.add(ftype)
            db.session.flush()

            custom_dims = [{'id': 'custom', 'name': {'de': 'Eigen'}, 'weight': 1.0}]
            custom_labels = {'1': {'de': 'Min'}, '7': {'de': 'Max'}}
            scenario = RatingScenarios(
                scenario_name='Custom',
                function_type_id=2,
                config_json={
                    'dimensions': custom_dims,
                    'min': 1,
                    'max': 7,
                    'step': 1,
                    'labels': custom_labels
                }
            )
            db.session.add(scenario)
            db.session.commit()

            config = DimensionalRatingService.get_scenario_config(scenario.id)
            assert config['dimensions'] == custom_dims
            assert config['min'] == 1
            assert config['max'] == 7
            assert config['labels'] == custom_labels


# =============================================================================
# Save Dimensional Rating (save_dimensional_rating) - requires DB
# =============================================================================

class TestSaveDimensionalRating:
    """Tests for save_dimensional_rating that require database."""

    def _create_scenario_with_item(self, db_session):
        """Helper to create scenario with one item."""
        from db.models.scenario import (
            RatingScenarios, FeatureFunctionType, EvaluationItem,
            ScenarioItems, ScenarioUsers, ScenarioRoles
        )
        from db.models.user import User

        ftype = FeatureFunctionType(function_type_id=2, name='rating')
        db_session.session.add(ftype)
        db_session.session.flush()

        user = User(username='rater', password_hash='x', api_key='test-api-key-rater', is_active=True)
        db_session.session.add(user)
        db_session.session.flush()

        scenario = RatingScenarios(
            scenario_name='Save Test',
            function_type_id=2,
            config_json={
                'dimensions': [
                    {'id': 'coherence', 'weight': 0.5},
                    {'id': 'fluency', 'weight': 0.5},
                ],
                'min': 1, 'max': 5, 'step': 1
            },
            created_by='rater'
        )
        db_session.session.add(scenario)
        db_session.session.flush()

        item = EvaluationItem(subject='Test Item', chat_id=1)
        db_session.session.add(item)
        db_session.session.flush()

        si = ScenarioItems(scenario_id=scenario.id, item_id=item.item_id)
        db_session.session.add(si)

        su = ScenarioUsers(scenario_id=scenario.id, user_id=user.id, role=ScenarioRoles.ASSESSOR)
        db_session.session.add(su)
        db_session.session.commit()

        return scenario, item, user

    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._emit_rating_update')
    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._log_completion_event')
    def test_DIM_RATE_SVC_029_save_new_rating(self, mock_log, mock_emit, app, db):
        """Should create new ItemDimensionRating record."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService
        from db.models.scenario import ItemDimensionRating

        with app.app_context():
            scenario, item, user = self._create_scenario_with_item(db)

            result = DimensionalRatingService.save_dimensional_rating(
                scenario_id=scenario.id,
                item_id=item.item_id,
                user_id=user.id,
                dimension_ratings={'coherence': 4, 'fluency': 5},
                feedback='Good quality'
            )

            assert result['success'] is True
            assert result['became_done'] is True

            saved = ItemDimensionRating.query.filter_by(
                user_id=user.id, item_id=item.item_id
            ).first()
            assert saved is not None
            assert saved.overall_score == pytest.approx(4.5)
            assert saved.feedback == 'Good quality'

    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._emit_rating_update')
    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._log_completion_event')
    def test_DIM_RATE_SVC_030_save_partial_rating(self, mock_log, mock_emit, app, db):
        """Partial rating should be marked as PROGRESSING."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService
        from db.models.scenario import ItemDimensionRating, ProgressionStatus

        with app.app_context():
            scenario, item, user = self._create_scenario_with_item(db)

            result = DimensionalRatingService.save_dimensional_rating(
                scenario_id=scenario.id,
                item_id=item.item_id,
                user_id=user.id,
                dimension_ratings={'coherence': 4},  # Missing 'fluency'
            )

            assert result['success'] is True
            assert result['became_done'] is False

            saved = ItemDimensionRating.query.filter_by(
                user_id=user.id, item_id=item.item_id
            ).first()
            assert saved.status == ProgressionStatus.PROGRESSING

    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._emit_rating_update')
    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._log_completion_event')
    def test_DIM_RATE_SVC_031_save_updates_existing(self, mock_log, mock_emit, app, db):
        """Updating an existing rating should modify the same record."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService
        from db.models.scenario import ItemDimensionRating

        with app.app_context():
            scenario, item, user = self._create_scenario_with_item(db)

            # First save
            DimensionalRatingService.save_dimensional_rating(
                scenario_id=scenario.id,
                item_id=item.item_id,
                user_id=user.id,
                dimension_ratings={'coherence': 3, 'fluency': 3},
            )

            # Update
            result = DimensionalRatingService.save_dimensional_rating(
                scenario_id=scenario.id,
                item_id=item.item_id,
                user_id=user.id,
                dimension_ratings={'coherence': 5, 'fluency': 5},
                feedback='Updated'
            )

            assert result['success'] is True
            count = ItemDimensionRating.query.filter_by(
                user_id=user.id, item_id=item.item_id
            ).count()
            assert count == 1

            saved = ItemDimensionRating.query.filter_by(
                user_id=user.id, item_id=item.item_id
            ).first()
            assert saved.overall_score == pytest.approx(5.0)
            assert saved.feedback == 'Updated'

    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._emit_rating_update')
    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._log_completion_event')
    def test_DIM_RATE_SVC_032_save_nonexistent_item(self, mock_log, mock_emit, app, db):
        """Saving rating for nonexistent item should return error."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        with app.app_context():
            result = DimensionalRatingService.save_dimensional_rating(
                scenario_id=1,
                item_id=99999,
                user_id=1,
                dimension_ratings={'coherence': 4}
            )
            assert 'error' in result

    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._emit_rating_update')
    @patch('services.evaluation.dimensional_rating_service.DimensionalRatingService._log_completion_event')
    def test_DIM_RATE_SVC_033_save_auto_complete_false(self, mock_log, mock_emit, app, db):
        """With auto_complete=False, status should be PROGRESSING even if all dimensions rated."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService
        from db.models.scenario import ItemDimensionRating, ProgressionStatus

        with app.app_context():
            scenario, item, user = self._create_scenario_with_item(db)

            result = DimensionalRatingService.save_dimensional_rating(
                scenario_id=scenario.id,
                item_id=item.item_id,
                user_id=user.id,
                dimension_ratings={'coherence': 4, 'fluency': 5},
                auto_complete=False
            )

            assert result['success'] is True
            saved = ItemDimensionRating.query.filter_by(
                user_id=user.id, item_id=item.item_id
            ).first()
            assert saved.status == ProgressionStatus.PROGRESSING


# =============================================================================
# Scenario Statistics (get_scenario_statistics) - requires DB
# =============================================================================

class TestGetScenarioStatistics:
    """Tests for get_scenario_statistics."""

    def test_DIM_RATE_SVC_034_stats_nonexistent_scenario(self, app, db):
        """Non-existent scenario should return error."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        with app.app_context():
            result = DimensionalRatingService.get_scenario_statistics(99999)
            assert 'error' in result

    def test_DIM_RATE_SVC_035_stats_empty_scenario(self, app, db):
        """Scenario with no ratings should return zeros."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService
        from db.models.scenario import RatingScenarios, FeatureFunctionType

        with app.app_context():
            ftype = FeatureFunctionType(function_type_id=2, name='rating')
            db.session.add(ftype)
            db.session.flush()

            scenario = RatingScenarios(
                scenario_name='Empty',
                function_type_id=2,
                config_json={}
            )
            db.session.add(scenario)
            db.session.commit()

            result = DimensionalRatingService.get_scenario_statistics(scenario.id)
            assert result['total_ratings'] == 0
            assert result['unique_users'] == 0
            assert result['unique_items'] == 0
            assert result['average_overall_score'] is None

    def test_DIM_RATE_SVC_036_stats_with_completed_ratings(self, app, db):
        """Statistics should aggregate completed ratings correctly."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService
        from db.models.scenario import (
            RatingScenarios, FeatureFunctionType, EvaluationItem,
            ItemDimensionRating, ProgressionStatus
        )
        from db.models.user import User

        with app.app_context():
            ftype = FeatureFunctionType(function_type_id=2, name='rating')
            db.session.add(ftype)
            db.session.flush()

            scenario = RatingScenarios(
                scenario_name='Stats Test',
                function_type_id=2,
                config_json={
                    'dimensions': [
                        {'id': 'coherence', 'weight': 0.5},
                        {'id': 'fluency', 'weight': 0.5},
                    ]
                }
            )
            db.session.add(scenario)

            user1 = User(username='stats_u1', password_hash='x', api_key='test-api-key-stats-u1', is_active=True)
            user2 = User(username='stats_u2', password_hash='x', api_key='test-api-key-stats-u2', is_active=True)
            db.session.add_all([user1, user2])

            item = EvaluationItem(subject='Stats Item', chat_id=100)
            db.session.add(item)
            db.session.flush()

            r1 = ItemDimensionRating(
                user_id=user1.id, item_id=item.item_id, scenario_id=scenario.id,
                dimension_ratings={'coherence': 4, 'fluency': 5},
                overall_score=4.5, status=ProgressionStatus.DONE
            )
            r2 = ItemDimensionRating(
                user_id=user2.id, item_id=item.item_id, scenario_id=scenario.id,
                dimension_ratings={'coherence': 3, 'fluency': 3},
                overall_score=3.0, status=ProgressionStatus.DONE
            )
            db.session.add_all([r1, r2])
            db.session.commit()

            result = DimensionalRatingService.get_scenario_statistics(scenario.id)
            assert result['total_ratings'] == 2
            assert result['unique_users'] == 2
            assert result['unique_items'] == 1
            assert result['average_overall_score'] == pytest.approx(3.75)
            assert result['dimension_averages']['coherence'] == pytest.approx(3.5)
            assert result['dimension_averages']['fluency'] == pytest.approx(4.0)


# =============================================================================
# User Progress (get_user_progress)
# =============================================================================

class TestGetUserProgress:
    """Tests for get_user_progress."""

    def test_DIM_RATE_SVC_037_progress_empty(self, app, db):
        """Empty scenario should return zero progress."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        with app.app_context():
            # Will return empty items -> 0 total
            result = DimensionalRatingService.get_user_progress(99999, 1)
            assert result['total'] == 0
            assert result['percent'] == 0

    def test_DIM_RATE_SVC_038_progress_calculation(self, app, db):
        """Progress should correctly report completed/in_progress/not_started."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService
        from db.models.scenario import (
            RatingScenarios, FeatureFunctionType, EvaluationItem,
            ScenarioItems, ScenarioUsers, ScenarioRoles,
            ItemDimensionRating, ProgressionStatus
        )
        from db.models.user import User

        with app.app_context():
            ftype = FeatureFunctionType(function_type_id=2, name='rating')
            db.session.add(ftype)
            db.session.flush()

            user = User(username='progress_u', password_hash='x', api_key='test-api-key-progress-u', is_active=True)
            db.session.add(user)
            db.session.flush()

            scenario = RatingScenarios(
                scenario_name='Progress Test',
                function_type_id=2,
                config_json={}
            )
            db.session.add(scenario)
            db.session.flush()

            # Create 3 items
            items = []
            for i in range(3):
                item = EvaluationItem(subject=f'Item {i}', chat_id=200 + i)
                db.session.add(item)
                db.session.flush()
                si = ScenarioItems(scenario_id=scenario.id, item_id=item.item_id)
                db.session.add(si)
                items.append(item)

            su = ScenarioUsers(scenario_id=scenario.id, user_id=user.id, role=ScenarioRoles.ASSESSOR)
            db.session.add(su)

            # Rate first item as done
            r1 = ItemDimensionRating(
                user_id=user.id, item_id=items[0].item_id, scenario_id=scenario.id,
                dimension_ratings={'coherence': 4}, overall_score=4.0,
                status=ProgressionStatus.DONE
            )
            # Rate second item as in-progress
            r2 = ItemDimensionRating(
                user_id=user.id, item_id=items[1].item_id, scenario_id=scenario.id,
                dimension_ratings={'coherence': 3}, overall_score=3.0,
                status=ProgressionStatus.PROGRESSING
            )
            db.session.add_all([r1, r2])
            db.session.commit()

            result = DimensionalRatingService.get_user_progress(scenario.id, user.id)
            assert result['total'] == 3
            assert result['completed'] == 1
            assert result['in_progress'] == 1
            assert result['not_started'] == 1
            assert result['percent'] == pytest.approx(33.3, abs=0.1)


# =============================================================================
# Edge Cases / Miscellaneous
# =============================================================================

class TestEdgeCases:
    """Edge case tests for DimensionalRatingService."""

    def test_DIM_RATE_SVC_039_all_none_ratings_return_zero_weight(self):
        """If all ratings are None, weighted score should be 0.0."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': None, 'b': None}
        weights = {'a': 0.5, 'b': 0.5}
        result = DimensionalRatingService._calculate_weighted_score(ratings, weights)
        assert result == 0.0

    def test_DIM_RATE_SVC_040_normalized_score_all_at_min(self):
        """All scores at minimum should normalize to 0.0."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 1, 'b': 1}
        weights = {'a': 0.5, 'b': 0.5}
        result = DimensionalRatingService.calculate_normalized_score(
            ratings, weights, scale_min=1, scale_max=5
        )
        assert result == pytest.approx(0.0)

    def test_DIM_RATE_SVC_041_normalized_score_all_at_max(self):
        """All scores at maximum should normalize to 1.0."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        ratings = {'a': 5, 'b': 5}
        weights = {'a': 0.5, 'b': 0.5}
        result = DimensionalRatingService.calculate_normalized_score(
            ratings, weights, scale_min=1, scale_max=5
        )
        assert result == pytest.approx(1.0)

    def test_DIM_RATE_SVC_042_emit_rating_update_no_socketio(self, app, db):
        """Emit should not crash when socketio is not available."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        with app.app_context():
            # Should not raise
            DimensionalRatingService._emit_rating_update(1, 1, 1, 'done')

    def test_DIM_RATE_SVC_043_log_completion_event_no_user(self, app, db):
        """Log completion should handle missing user gracefully."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        with app.app_context():
            with patch('services.system_event_service.SystemEventService') as mock_svc:
                mock_svc.log_event = MagicMock()
                # Should not raise even with nonexistent user
                DimensionalRatingService._log_completion_event(1, 1, 99999)

    def test_DIM_RATE_SVC_044_get_items_no_scenario(self, app, db):
        """get_items_for_user with no scenario should return empty list."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        with app.app_context():
            result = DimensionalRatingService.get_items_for_user(99999, 1)
            assert result == []

    def test_DIM_RATE_SVC_045_get_item_with_content_no_item(self, app, db):
        """get_item_with_content with nonexistent item should return error."""
        from services.evaluation.dimensional_rating_service import DimensionalRatingService

        with app.app_context():
            result = DimensionalRatingService.get_item_with_content(1, 99999, 1)
            assert 'error' in result
