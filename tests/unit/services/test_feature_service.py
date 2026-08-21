"""
Unit tests for FeatureService.

Tests feature function types (by name, ID, all), feature types (get, create),
feature queries (by ID, by thread, by attributes), counting, and filtering.
Uses the SQLite in-memory test DB from conftest.py.
"""

import pytest
from db.models.scenario import (
    FeatureFunctionType, FeatureType, Feature, EvaluationItem,
)
from services.feature_service import FeatureService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_function_types(app, db, app_context):
    """Seed the standard feature function types."""
    types = []
    for name in ('ranking', 'rating', 'mail_rating', 'comparison', 'authenticity'):
        fft = FeatureFunctionType(name=name)
        db.session.add(fft)
        types.append(fft)
    db.session.commit()
    return types


@pytest.fixture
def seed_feature_types(app, db, app_context):
    """Seed a few feature types."""
    types = []
    for name in ('situation_summary', 'narrative_summary', 'structured_summary'):
        ft = FeatureType(name=name)
        db.session.add(ft)
        types.append(ft)
    db.session.commit()
    return types


@pytest.fixture
def seed_evaluation_item(app, db, app_context, seed_function_types):
    """Create an evaluation item for feature tests."""
    fft_ranking = seed_function_types[0]
    item = EvaluationItem(
        chat_id=100,
        institut_id=1,
        subject='Test item',
        sender='tester',
        function_type_id=fft_ranking.function_type_id,
    )
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture
def seed_features(app, db, app_context, seed_evaluation_item, seed_feature_types):
    """Create features attached to the evaluation item."""
    item = seed_evaluation_item
    ft_situation = seed_feature_types[0]
    ft_narrative = seed_feature_types[1]

    features = [
        Feature(
            item_id=item.item_id,
            type_id=ft_situation.type_id,
            model_id='Global/OpenAI/gpt-5-nano',
            content='Summary A',
        ),
        Feature(
            item_id=item.item_id,
            type_id=ft_situation.type_id,
            model_id='Global/Mistral/Mistral-Small',
            content='Summary B',
        ),
        Feature(
            item_id=item.item_id,
            type_id=ft_narrative.type_id,
            model_id='Global/OpenAI/gpt-5-nano',
            content='Narrative C',
        ),
    ]
    db.session.add_all(features)
    db.session.commit()
    return features


# ---------------------------------------------------------------------------
# Tests: Function type lookups
# ---------------------------------------------------------------------------

class TestFunctionTypeLookups:
    """Tests for FeatureService function type methods."""

    def test_FEAT_001_get_function_type_by_name_found(
        self, app, db, app_context, seed_function_types
    ):
        """[FEAT-001] Returns the function type when searched by name."""
        result = FeatureService.get_function_type_by_name('ranking')
        assert result is not None
        assert result.name == 'ranking'

    def test_FEAT_002_get_function_type_by_name_not_found(
        self, app, db, app_context, seed_function_types
    ):
        """[FEAT-002] Returns None when function type name does not exist."""
        result = FeatureService.get_function_type_by_name('nonexistent')
        assert result is None

    def test_FEAT_003_get_function_type_by_id_found(
        self, app, db, app_context, seed_function_types
    ):
        """[FEAT-003] Returns the function type when searched by ID."""
        fft = seed_function_types[0]
        result = FeatureService.get_function_type_by_id(fft.function_type_id)
        assert result is not None
        assert result.name == fft.name

    def test_FEAT_004_get_function_type_by_id_not_found(
        self, app, db, app_context, seed_function_types
    ):
        """[FEAT-004] Returns None when function type ID does not exist."""
        result = FeatureService.get_function_type_by_id(99999)
        assert result is None

    def test_FEAT_005_get_all_function_types(
        self, app, db, app_context, seed_function_types
    ):
        """[FEAT-005] Returns all seeded function types."""
        result = FeatureService.get_all_function_types()
        assert len(result) == len(seed_function_types)
        names = {ft.name for ft in result}
        assert 'ranking' in names
        assert 'rating' in names


# ---------------------------------------------------------------------------
# Tests: Feature type lookups
# ---------------------------------------------------------------------------

class TestFeatureTypeLookups:
    """Tests for FeatureService feature type methods."""

    def test_FEAT_010_get_feature_type_by_name_found(
        self, app, db, app_context, seed_feature_types
    ):
        """[FEAT-010] Returns the feature type when searched by name."""
        result = FeatureService.get_feature_type_by_name('situation_summary')
        assert result is not None
        assert result.name == 'situation_summary'

    def test_FEAT_011_get_feature_type_by_name_not_found(
        self, app, db, app_context, seed_feature_types
    ):
        """[FEAT-011] Returns None when feature type name does not exist."""
        result = FeatureService.get_feature_type_by_name('nonexistent_type')
        assert result is None

    def test_FEAT_012_get_all_feature_types(
        self, app, db, app_context, seed_feature_types
    ):
        """[FEAT-012] Returns all seeded feature types."""
        result = FeatureService.get_all_feature_types()
        assert len(result) == len(seed_feature_types)

    def test_FEAT_013_get_or_create_existing(
        self, app, db, app_context, seed_feature_types
    ):
        """[FEAT-013] get_or_create returns existing feature type without creating a new one."""
        before_count = len(FeatureService.get_all_feature_types())
        result = FeatureService.get_or_create_feature_type('situation_summary')
        after_count = len(FeatureService.get_all_feature_types())

        assert result.name == 'situation_summary'
        assert before_count == after_count

    def test_FEAT_014_get_or_create_new(
        self, app, db, app_context, seed_feature_types
    ):
        """[FEAT-014] get_or_create creates a new feature type when it does not exist."""
        before_count = len(FeatureService.get_all_feature_types())
        result = FeatureService.get_or_create_feature_type('brand_new_type')
        after_count = len(FeatureService.get_all_feature_types())

        assert result.name == 'brand_new_type'
        assert after_count == before_count + 1


# ---------------------------------------------------------------------------
# Tests: Feature queries
# ---------------------------------------------------------------------------

class TestFeatureQueries:
    """Tests for FeatureService feature query methods."""

    def test_FEAT_020_get_feature_by_id_found(
        self, app, db, app_context, seed_features
    ):
        """[FEAT-020] Returns a feature when searched by its ID."""
        feature = seed_features[0]
        result = FeatureService.get_feature_by_id(feature.feature_id)
        assert result is not None
        assert result.content == 'Summary A'

    def test_FEAT_021_get_feature_by_id_not_found(
        self, app, db, app_context, seed_features
    ):
        """[FEAT-021] Returns None when feature ID does not exist."""
        result = FeatureService.get_feature_by_id(99999)
        assert result is None

    def test_FEAT_022_get_features_by_thread(
        self, app, db, app_context, seed_features, seed_evaluation_item
    ):
        """[FEAT-022] Returns all features for a given thread/item ID."""
        result = FeatureService.get_features_by_thread(seed_evaluation_item.item_id)
        assert len(result) == 3

    def test_FEAT_023_get_features_by_thread_empty(
        self, app, db, app_context, seed_features
    ):
        """[FEAT-023] Returns empty list for a thread with no features."""
        result = FeatureService.get_features_by_thread(99999)
        assert result == []

    def test_FEAT_024_get_feature_by_attributes_found(
        self, app, db, app_context, seed_features, seed_evaluation_item, seed_feature_types
    ):
        """[FEAT-024] Returns a feature matching thread, type, and model."""
        item = seed_evaluation_item
        ft = seed_feature_types[0]
        result = FeatureService.get_feature_by_attributes(
            thread_id=item.item_id,
            type_id=ft.type_id,
            model_id='Global/OpenAI/gpt-5-nano',
        )
        assert result is not None
        assert result.content == 'Summary A'

    def test_FEAT_025_get_feature_by_attributes_with_content_match(
        self, app, db, app_context, seed_features, seed_evaluation_item, seed_feature_types
    ):
        """[FEAT-025] Returns a feature when content also matches."""
        item = seed_evaluation_item
        ft = seed_feature_types[0]
        result = FeatureService.get_feature_by_attributes(
            thread_id=item.item_id,
            type_id=ft.type_id,
            model_id='Global/OpenAI/gpt-5-nano',
            content='Summary A',
        )
        assert result is not None

    def test_FEAT_026_get_feature_by_attributes_content_mismatch(
        self, app, db, app_context, seed_features, seed_evaluation_item, seed_feature_types
    ):
        """[FEAT-026] Returns None when content does not match."""
        item = seed_evaluation_item
        ft = seed_feature_types[0]
        result = FeatureService.get_feature_by_attributes(
            thread_id=item.item_id,
            type_id=ft.type_id,
            model_id='Global/OpenAI/gpt-5-nano',
            content='Nonexistent content',
        )
        assert result is None

    def test_FEAT_027_get_feature_by_attributes_not_found(
        self, app, db, app_context, seed_features, seed_evaluation_item, seed_feature_types
    ):
        """[FEAT-027] Returns None when no feature matches the attributes."""
        item = seed_evaluation_item
        result = FeatureService.get_feature_by_attributes(
            thread_id=item.item_id,
            type_id=99999,
            model_id='nonexistent_model',
        )
        assert result is None


# ---------------------------------------------------------------------------
# Tests: Feature counting and filtering
# ---------------------------------------------------------------------------

class TestFeatureCountingFiltering:
    """Tests for counting and type/model filtering."""

    def test_FEAT_030_count_features_by_thread(
        self, app, db, app_context, seed_features, seed_evaluation_item
    ):
        """[FEAT-030] Returns correct count of features for a thread."""
        count = FeatureService.get_features_count_by_thread(seed_evaluation_item.item_id)
        assert count == 3

    def test_FEAT_031_count_features_for_empty_thread(
        self, app, db, app_context, seed_features
    ):
        """[FEAT-031] Returns 0 for a thread with no features."""
        count = FeatureService.get_features_count_by_thread(99999)
        assert count == 0

    def test_FEAT_032_get_features_by_type_found(
        self, app, db, app_context, seed_features, seed_evaluation_item
    ):
        """[FEAT-032] Returns features filtered by feature type name."""
        result = FeatureService.get_features_by_type(
            seed_evaluation_item.item_id, 'situation_summary'
        )
        assert len(result) == 2
        assert all(f.content.startswith('Summary') for f in result)

    def test_FEAT_033_get_features_by_type_not_found(
        self, app, db, app_context, seed_features, seed_evaluation_item
    ):
        """[FEAT-033] Returns empty list when feature type name does not exist."""
        result = FeatureService.get_features_by_type(
            seed_evaluation_item.item_id, 'nonexistent_type'
        )
        assert result == []

    def test_FEAT_034_get_features_by_model_found(
        self, app, db, app_context, seed_features, seed_evaluation_item
    ):
        """[FEAT-034] Returns features filtered by model ID."""
        result = FeatureService.get_features_by_model(
            seed_evaluation_item.item_id, 'Global/OpenAI/gpt-5-nano'
        )
        assert len(result) == 2

    def test_FEAT_035_get_features_by_model_not_found(
        self, app, db, app_context, seed_features, seed_evaluation_item
    ):
        """[FEAT-035] Returns empty list when model ID does not match."""
        result = FeatureService.get_features_by_model(
            seed_evaluation_item.item_id, 'nonexistent_model'
        )
        assert result == []
