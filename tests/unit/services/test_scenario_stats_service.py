"""
Unit tests for scenario_stats_service.py.

Tests the largest backend service (4,356 lines, ~7% of codebase).
Covers: progress stats, evaluator stats, IRR calculations, bucket/rating
distribution, caching, helper functions, and edge cases.

All imports from app/ are deferred to function scope to avoid circular imports
triggered by routes/__init__.py -> socketio_handlers -> scenario_stats_service.

Test IDs: [STATS-001] through [STATS-105]
"""

import json
import sys
import time
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


# =============================================================================
# Lazy import helper -- breaks the circular import chain:
# scenario_stats_service -> routes.HelperFunctions -> routes/__init__
# -> routes.oncoco -> socketio_handlers -> events_scenarios
# -> scenario_stats_service  (BOOM)
#
# Fix: before the first import we inject stubs for the modules that cause
# the cycle, then import the actual HelperFunctions, then import the service.
# =============================================================================

_sss_mod = None


def _sss():
    """Return the scenario_stats_service module, breaking the circular import."""
    global _sss_mod
    if _sss_mod is not None:
        return _sss_mod

    # Pre-inject a stub for socketio_handlers so that
    # routes.oncoco -> socketio_handlers does NOT try to import
    # events_scenarios which in turn would import this service again.
    _socketio_stub = MagicMock()
    _saved = {}
    keys_to_stub = [
        'socketio_handlers',
        'socketio_handlers.events_scenarios',
        'socketio_handlers.events_oncoco',
    ]
    for k in keys_to_stub:
        if k not in sys.modules:
            _saved[k] = None
            sys.modules[k] = _socketio_stub
        else:
            _saved[k] = sys.modules[k]

    try:
        import services.scenario_stats_service as mod
        _sss_mod = mod
    finally:
        # Restore original modules (or remove stubs)
        for k, orig in _saved.items():
            if orig is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = orig

    return _sss_mod


# =============================================================================
# Helper: Create test data in DB
# =============================================================================

def _create_function_type(db_session, name, ftype_id=None):
    from db.models.scenario import FeatureFunctionType
    fft = FeatureFunctionType(name=name)
    if ftype_id:
        fft.function_type_id = ftype_id
    db_session.session.add(fft)
    db_session.session.commit()
    return fft


def _create_user(db_session, username, **kwargs):
    from db.models.user import User
    user = User(
        username=username,
        password_hash=kwargs.get('password_hash', 'hash'),
        api_key=kwargs.get('api_key', f'key-{username}'),
        is_active=kwargs.get('is_active', True),
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


def _create_scenario(db_session, name, function_type_id, config_json=None):
    from db.models.scenario import RatingScenarios
    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=function_type_id,
        config_json=config_json or {},
    )
    db_session.session.add(scenario)
    db_session.session.commit()
    return scenario


def _create_item(db_session, function_type_id, subject='Test item', chat_id=None, institut_id=None):
    from db.models.scenario import EvaluationItem
    item = EvaluationItem(
        chat_id=chat_id or 1,
        institut_id=institut_id or 1,
        subject=subject,
        function_type_id=function_type_id,
    )
    db_session.session.add(item)
    db_session.session.commit()
    return item


def _add_scenario_item(db_session, scenario_id, item_id):
    from db.models.scenario import ScenarioItems
    si = ScenarioItems(scenario_id=scenario_id, item_id=item_id)
    db_session.session.add(si)
    db_session.session.commit()
    return si


def _add_scenario_user(db_session, scenario_id, user_id, role_str='Assessor'):
    from db.models.scenario import ScenarioUsers, ScenarioRoles, MembershipStatus
    role = ScenarioRoles.EVALUATOR if role_str == 'Assessor' else ScenarioRoles.OWNER
    is_assessor = role_str == 'Assessor'
    is_owner = role_str == 'Owner'
    su = ScenarioUsers(
        scenario_id=scenario_id,
        user_id=user_id,
        role=role,
        access_level='OWNER' if is_owner else 'MEMBER',
        is_assessor=is_assessor,
        is_viewer=is_owner or (not is_assessor),
        membership_status=MembershipStatus.ACTIVE,
        manager_role='owner' if is_owner else 'none',
        evaluation_role='assessor' if is_assessor else 'none',
    )
    db_session.session.add(su)
    db_session.session.commit()
    return su


def _create_feature(db_session, item_id, content='feature content', model_id=None):
    from db.models.scenario import Feature
    f = Feature(item_id=item_id, content=content, model_id=model_id)
    db_session.session.add(f)
    db_session.session.commit()
    return f


def _create_ranking(db_session, user_id, feature_id, bucket='gut'):
    from db.models.scenario import UserFeatureRanking
    r = UserFeatureRanking(user_id=user_id, feature_id=feature_id, bucket=bucket)
    db_session.session.add(r)
    db_session.session.commit()
    return r


def _create_dimension_rating(db_session, user_id, item_id, scenario_id,
                              dimension_ratings, overall_score=None, status='Done'):
    from db.models.scenario import ItemDimensionRating, ProgressionStatus
    ps = ProgressionStatus.DONE if status == 'Done' else ProgressionStatus.NOT_STARTED
    r = ItemDimensionRating(
        user_id=user_id, item_id=item_id, scenario_id=scenario_id,
        dimension_ratings=dimension_ratings, overall_score=overall_score, status=ps,
    )
    db_session.session.add(r)
    db_session.session.commit()
    return r


def _create_llm_task_result(db_session, scenario_id, item_id, model_id,
                             task_type, payload_json=None, error=None):
    from db.models.llm_task_result import LLMTaskResult
    r = LLMTaskResult(
        scenario_id=scenario_id, item_id=item_id, model_id=model_id,
        task_type=task_type, payload_json=payload_json, error=error,
    )
    db_session.session.add(r)
    db_session.session.commit()
    return r


def _create_llm_model(db_session, model_id, display_name=None):
    from db.models.llm_model import LLMModel
    m = LLMModel(model_id=model_id, display_name=display_name or model_id,
                 model_type='llm', provider='test', context_window=4096,
                 max_output_tokens=2048)
    db_session.session.add(m)
    db_session.session.commit()
    return m


def _create_authenticity_vote(db_session, user_id, item_id, vote='real', confidence=3):
    from db.models.authenticity import UserAuthenticityVote
    v = UserAuthenticityVote(user_id=user_id, item_id=item_id, vote=vote, confidence=confidence)
    db_session.session.add(v)
    db_session.session.commit()
    return v


def _create_mail_rating(db_session, user_id, item_id, overall_rating=4, status='Done'):
    from db.models.scenario import UserMailHistoryRating, ProgressionStatus
    ps = ProgressionStatus.DONE if status == 'Done' else ProgressionStatus.NOT_STARTED
    r = UserMailHistoryRating(user_id=user_id, item_id=item_id, overall_rating=overall_rating, status=ps)
    db_session.session.add(r)
    db_session.session.commit()
    return r


# =============================================================================
# TESTS: Pure helper / utility functions (no DB needed)
# =============================================================================

class TestNormalizeBucketLookupKey:
    def test_STATS_001_none_returns_empty(self, app, db, app_context):
        """[STATS-001] None input returns empty string."""
        assert _sss()._normalize_bucket_lookup_key(None) == ""

    def test_STATS_002_empty_string_returns_empty(self, app, db, app_context):
        """[STATS-002] Empty / whitespace returns empty string."""
        m = _sss()
        assert m._normalize_bucket_lookup_key("") == ""
        assert m._normalize_bucket_lookup_key("   ") == ""

    def test_STATS_003_normalizes_whitespace_and_case(self, app, db, app_context):
        """[STATS-003] Normalizes whitespace, hyphens, case."""
        m = _sss()
        assert m._normalize_bucket_lookup_key("Very Good") == "very_good"
        assert m._normalize_bucket_lookup_key("VERY-GOOD") == "very_good"
        assert m._normalize_bucket_lookup_key("  gut  ") == "gut"

    def test_STATS_004_collapses_multiple_spaces(self, app, db, app_context):
        """[STATS-004] Collapses multiple spaces into single underscore."""
        assert _sss()._normalize_bucket_lookup_key("very   good") == "very_good"


class TestHumanizeBucketIdentifier:
    def test_STATS_005_empty_returns_bucket(self, app, db, app_context):
        """[STATS-005] Empty value returns 'Bucket'."""
        m = _sss()
        assert m._humanize_bucket_identifier("") == "Bucket"
        assert m._humanize_bucket_identifier(None) == "Bucket"

    def test_STATS_006_capitalizes_words(self, app, db, app_context):
        """[STATS-006] Capitalizes each word."""
        m = _sss()
        assert m._humanize_bucket_identifier("very_good") == "Very Good"
        assert m._humanize_bucket_identifier("gut") == "Gut"


class TestNormalizeProvenanceText:
    def test_STATS_007_none_returns_empty(self, app, db, app_context):
        """[STATS-007] None returns empty string."""
        assert _sss()._normalize_provenance_text(None) == ""

    def test_STATS_008_collapses_whitespace(self, app, db, app_context):
        """[STATS-008] Collapses all whitespace to single spaces."""
        assert _sss()._normalize_provenance_text("hello  \n world") == "hello world"


class TestNormalizeModelIdentity:
    def test_STATS_009_none_returns_empty(self, app, db, app_context):
        """[STATS-009] None returns empty string."""
        assert _sss()._normalize_model_identity(None) == ""

    def test_STATS_010_strips_non_alnum(self, app, db, app_context):
        """[STATS-010] Strips non-alphanumeric characters."""
        m = _sss()
        assert m._normalize_model_identity("GPT-4o-mini") == "gpt4omini"
        assert m._normalize_model_identity("  Model/Name  ") == "modelname"


class TestInterpretAlpha:
    def test_STATS_011_none_returns_nicht_berechenbar(self, app, db, app_context):
        """[STATS-011] None alpha returns 'Nicht berechenbar'."""
        assert _sss()._interpret_alpha(None) == "Nicht berechenbar"

    def test_STATS_012_high_alpha(self, app, db, app_context):
        """[STATS-012] Alpha >= 0.8 returns 'Sehr gut'."""
        m = _sss()
        assert m._interpret_alpha(0.85) == "Sehr gut"
        assert m._interpret_alpha(1.0) == "Sehr gut"

    def test_STATS_013_acceptable_alpha(self, app, db, app_context):
        """[STATS-013] Alpha >= 0.667 returns 'Akzeptabel'."""
        assert _sss()._interpret_alpha(0.7) == "Akzeptabel"

    def test_STATS_014_moderate_alpha(self, app, db, app_context):
        """[STATS-014] Alpha >= 0.4 returns 'Moderat'."""
        assert _sss()._interpret_alpha(0.5) == "Moderat"

    def test_STATS_015_low_alpha(self, app, db, app_context):
        """[STATS-015] Alpha < 0.4 returns 'Gering'."""
        m = _sss()
        assert m._interpret_alpha(0.2) == "Gering"
        assert m._interpret_alpha(0.0) == "Gering"


class TestExtractRatingScaleBounds:
    def test_STATS_016_defaults_to_1_5(self, app, db, app_context):
        """[STATS-016] Empty config defaults to min=1, max=5."""
        assert _sss()._extract_rating_scale_bounds({}) == {"min": 1.0, "max": 5.0}

    def test_STATS_017_reads_from_top_level(self, app, db, app_context):
        """[STATS-017] Reads min/max from top-level config."""
        assert _sss()._extract_rating_scale_bounds({"min": 0, "max": 10}) == {"min": 0.0, "max": 10.0}

    def test_STATS_018_reads_from_eval_config(self, app, db, app_context):
        """[STATS-018] Reads from eval_config nesting."""
        r = _sss()._extract_rating_scale_bounds({"eval_config": {"min": 1, "max": 7}})
        assert r == {"min": 1.0, "max": 7.0}

    def test_STATS_019_reads_from_nested_eval_config(self, app, db, app_context):
        """[STATS-019] Reads from eval_config.config nesting."""
        r = _sss()._extract_rating_scale_bounds({"eval_config": {"config": {"min": 2, "max": 8}}})
        assert r == {"min": 2.0, "max": 8.0}

    def test_STATS_020_invalid_bounds_reset(self, app, db, app_context):
        """[STATS-020] If max <= min, resets to default 1-5."""
        assert _sss()._extract_rating_scale_bounds({"min": 5, "max": 3}) == {"min": 1.0, "max": 5.0}

    def test_STATS_021_non_dict_returns_defaults(self, app, db, app_context):
        """[STATS-021] Non-dict config returns defaults."""
        assert _sss()._extract_rating_scale_bounds(None) == {"min": 1.0, "max": 5.0}

    def test_STATS_022_invalid_types_fallback(self, app, db, app_context):
        """[STATS-022] Non-numeric values fall back to defaults."""
        assert _sss()._extract_rating_scale_bounds({"min": "abc", "max": "xyz"}) == {"min": 1.0, "max": 5.0}


class TestExtractOverallRatingFromPayload:
    def test_STATS_023_none_returns_none(self, app, db, app_context):
        """[STATS-023] None payload returns None."""
        assert _sss()._extract_overall_rating_from_payload(None) is None

    def test_STATS_024_dimensional_format(self, app, db, app_context):
        """[STATS-024] Dimensional format extracts overall_rating."""
        r = _sss()._extract_overall_rating_from_payload({"type": "dimensional", "overall_rating": 4.5})
        assert r == 4.5

    def test_STATS_025_overall_rating_field(self, app, db, app_context):
        """[STATS-025] Direct overall_rating field."""
        assert _sss()._extract_overall_rating_from_payload({"overall_rating": 3}) == 3.0

    def test_STATS_026_rating_field_fallback(self, app, db, app_context):
        """[STATS-026] Falls back to 'rating' field."""
        assert _sss()._extract_overall_rating_from_payload({"rating": 2}) == 2.0

    def test_STATS_027_json_string_payload(self, app, db, app_context):
        """[STATS-027] JSON string payload is parsed."""
        assert _sss()._extract_overall_rating_from_payload(json.dumps({"overall_rating": 4.0})) == 4.0

    def test_STATS_028_invalid_json_returns_none(self, app, db, app_context):
        """[STATS-028] Invalid JSON string returns None."""
        assert _sss()._extract_overall_rating_from_payload("not-json") is None

    def test_STATS_029_non_numeric_returns_none(self, app, db, app_context):
        """[STATS-029] Non-numeric overall_rating returns None."""
        assert _sss()._extract_overall_rating_from_payload({"overall_rating": "bad"}) is None


class TestExtractRankingBucketConfig:
    def test_STATS_030_empty_config_returns_default_buckets(self, app, db, app_context):
        """[STATS-030] Empty config returns default 3 buckets."""
        result = _sss()._extract_ranking_bucket_config({})
        assert len(result) == 3
        assert result[0]["id"] == "gut"
        assert result[1]["id"] == "mittel"
        assert result[2]["id"] == "schlecht"

    def test_STATS_031_top_level_buckets(self, app, db, app_context):
        """[STATS-031] Reads buckets from top-level config."""
        config = {"buckets": [
            {"id": "excellent", "name": {"de": "Exzellent", "en": "Excellent"}, "color": "#00ff00"},
            {"id": "poor", "name": {"de": "Schlecht", "en": "Poor"}, "color": "#ff0000"},
        ]}
        result = _sss()._extract_ranking_bucket_config(config)
        assert len(result) == 2
        assert result[0]["id"] == "excellent"

    def test_STATS_032_eval_config_buckets(self, app, db, app_context):
        """[STATS-032] Reads buckets from eval_config nesting."""
        config = {"eval_config": {"buckets": [{"id": "a"}, {"id": "b"}]}}
        assert len(_sss()._extract_ranking_bucket_config(config)) == 2

    def test_STATS_033_string_buckets(self, app, db, app_context):
        """[STATS-033] String bucket values are supported."""
        result = _sss()._extract_ranking_bucket_config({"buckets": ["Good", "Bad"]})
        assert len(result) == 2
        assert result[0]["id"] == "good"

    def test_STATS_034_deduplicates_bucket_ids(self, app, db, app_context):
        """[STATS-034] Duplicate bucket IDs are skipped."""
        assert len(_sss()._extract_ranking_bucket_config({"buckets": [{"id": "a"}, {"id": "a"}]})) == 1


class TestBuildBucketIdResolver:
    def test_STATS_035_resolves_exact_id(self, app, db, app_context):
        """[STATS-035] Resolves exact bucket id."""
        bo = [{"id": "gut", "label": "Gut", "label_de": "Gut", "label_en": "Good"}]
        assert _sss()._build_bucket_id_resolver(bo)("gut") == "gut"

    def test_STATS_036_resolves_label(self, app, db, app_context):
        """[STATS-036] Resolves by label (case-insensitive)."""
        bo = [{"id": "gut", "label": "Gut", "label_de": "Gut", "label_en": "Good"}]
        resolve = _sss()._build_bucket_id_resolver(bo)
        assert resolve("Good") == "gut"
        assert resolve("GUT") == "gut"

    def test_STATS_037_resolves_legacy_alias(self, app, db, app_context):
        """[STATS-037] Resolves legacy aliases like 'good' -> 'gut'."""
        bo = [{"id": "gut", "label": "Gut", "label_de": "Gut", "label_en": "Good"}]
        assert _sss()._build_bucket_id_resolver(bo)("good") == "gut"

    def test_STATS_038_unresolvable_returns_none(self, app, db, app_context):
        """[STATS-038] Unresolvable value returns None."""
        bo = [{"id": "gut", "label": "Gut", "label_de": "Gut", "label_en": "Good"}]
        assert _sss()._build_bucket_id_resolver(bo)("nonexistent") is None

    def test_STATS_039_none_returns_none(self, app, db, app_context):
        """[STATS-039] None input returns None."""
        assert _sss()._build_bucket_id_resolver([])( None) is None


class TestKrippendorffAlpha:
    def test_STATS_040_perfect_agreement(self, app, db, app_context):
        """[STATS-040] Perfect agreement yields alpha=1.0."""
        matrix = np.array([[0, 1, 0], [0, 1, 0]], dtype=float)
        assert _sss()._calculate_krippendorff_alpha(matrix) == 1.0

    def test_STATS_041_empty_matrix_returns_none(self, app, db, app_context):
        """[STATS-041] Empty matrix returns None."""
        assert _sss()._calculate_krippendorff_alpha(np.array([], dtype=float).reshape(0, 0)) is None

    def test_STATS_042_all_nan_returns_none(self, app, db, app_context):
        """[STATS-042] All-NaN matrix returns None."""
        assert _sss()._calculate_krippendorff_alpha(np.full((2, 3), np.nan)) is None

    def test_STATS_043_single_column_returns_none(self, app, db, app_context):
        """[STATS-043] Single column (< 2 items) returns None."""
        assert _sss()._calculate_krippendorff_alpha(np.array([[0], [1]], dtype=float)) is None

    def test_STATS_044_total_disagreement(self, app, db, app_context):
        """[STATS-044] Complete disagreement yields negative alpha."""
        matrix = np.array([[0, 1, 0, 1], [1, 0, 1, 0]], dtype=float)
        alpha = _sss()._calculate_krippendorff_alpha(matrix)
        assert alpha is not None and alpha < 0.0

    def test_STATS_045_with_nan_values(self, app, db, app_context):
        """[STATS-045] NaN values (missing ratings) are handled."""
        matrix = np.array([[0, 1, np.nan], [0, 1, 0]], dtype=float)
        assert _sss()._calculate_krippendorff_alpha(matrix) == 1.0

    def test_STATS_046_uniform_ratings(self, app, db, app_context):
        """[STATS-046] All same rating -> alpha = 1.0."""
        matrix = np.array([[0, 0, 0], [0, 0, 0]], dtype=float)
        assert _sss()._calculate_krippendorff_alpha(matrix) == 1.0


# =============================================================================
# TESTS: Caching
# =============================================================================

class TestStatsCache:
    def test_STATS_047_cache_miss_returns_none(self, app, db, app_context):
        """[STATS-047] Cache miss returns None."""
        assert _sss()._get_cached_stats(999999) is None

    def test_STATS_048_set_and_get_cache(self, app, db, app_context):
        """[STATS-048] Set then get returns cached data."""
        m = _sss()
        test_data = {"test": "value"}
        m._set_cached_stats(888888, test_data)
        assert m._get_cached_stats(888888) == test_data
        m.invalidate_stats_cache(888888)

    def test_STATS_049_invalidate_cache(self, app, db, app_context):
        """[STATS-049] Invalidate removes cached entry."""
        m = _sss()
        m._set_cached_stats(777777, {"foo": "bar"})
        m.invalidate_stats_cache(777777)
        assert m._get_cached_stats(777777) is None

    def test_STATS_050_expired_cache_returns_none(self, app, db, app_context):
        """[STATS-050] Expired cache entry returns None."""
        m = _sss()
        m._stats_cache[666666] = (time.time() - 200, {"old": "data"})
        assert m._get_cached_stats(666666) is None
        m._stats_cache.pop(666666, None)


# =============================================================================
# TESTS: DB-backed lookups
# =============================================================================

class TestGetScenarioOrRaise:
    def test_STATS_051_missing_id_raises_validation_error(self, app, db, app_context):
        """[STATS-051] Missing scenario_id raises ValidationError."""
        from decorators.error_handler import ValidationError
        with pytest.raises(ValidationError, match="missing"):
            _sss()._get_scenario_or_raise(None)

    def test_STATS_052_nonexistent_scenario_raises_not_found(self, app, db, app_context):
        """[STATS-052] Nonexistent scenario raises NotFoundError."""
        from decorators.error_handler import NotFoundError
        with pytest.raises(NotFoundError, match="not found"):
            _sss()._get_scenario_or_raise(99999)

    def test_STATS_053_existing_scenario_returned(self, app, db, app_context):
        """[STATS-053] Existing scenario is returned."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'Test', fft.function_type_id)
        assert _sss()._get_scenario_or_raise(scenario.id).id == scenario.id


class TestGetFunctionTypeOrRaise:
    def test_STATS_054_nonexistent_raises_not_found(self, app, db, app_context):
        """[STATS-054] Nonexistent function_type_id raises NotFoundError."""
        from decorators.error_handler import NotFoundError
        with pytest.raises(NotFoundError, match="does not exist"):
            _sss()._get_function_type_or_raise(99999)

    def test_STATS_055_existing_returns_type(self, app, db, app_context):
        """[STATS-055] Existing function type is returned."""
        fft = _create_function_type(db, 'ranking')
        assert _sss()._get_function_type_or_raise(fft.function_type_id).name == 'ranking'


class TestGetScenarioIdsForThread:
    def test_STATS_056_no_thread_returns_empty(self, app, db, app_context):
        """[STATS-056] No thread_id returns empty list."""
        m = _sss()
        assert m.get_scenario_ids_for_thread(None) == []
        assert m.get_scenario_ids_for_thread(0) == []

    def test_STATS_057_returns_scenario_ids(self, app, db, app_context):
        """[STATS-057] Returns sorted scenario IDs for a thread."""
        fft = _create_function_type(db, 'ranking')
        item = _create_item(db, fft.function_type_id, chat_id=10, institut_id=10)
        s1 = _create_scenario(db, 'S1', fft.function_type_id)
        s2 = _create_scenario(db, 'S2', fft.function_type_id)
        _add_scenario_item(db, s1.id, item.item_id)
        _add_scenario_item(db, s2.id, item.item_id)
        result = _sss().get_scenario_ids_for_thread(item.item_id)
        assert result == sorted([s1.id, s2.id])


# =============================================================================
# TESTS: _batch_get_progression_states
# =============================================================================

class TestBatchGetProgressionStates:
    def test_STATS_058_empty_inputs_returns_empty(self, app, db, app_context):
        """[STATS-058] Empty thread/user IDs return empty dict."""
        m = _sss()
        assert m._batch_get_progression_states([], [], 1, 1) == {}
        assert m._batch_get_progression_states([1], [], 1, 1) == {}
        assert m._batch_get_progression_states([], [1], 1, 1) == {}

    def test_STATS_059_ranking_no_rankings_not_started(self, app, db, app_context):
        """[STATS-059] Ranking items with no rankings -> NOT_STARTED."""
        from db.models.scenario import ProgressionStatus
        fft = _create_function_type(db, 'ranking')
        user = _create_user(db, 'user_rank_1')
        item = _create_item(db, fft.function_type_id, chat_id=20, institut_id=20)
        _create_feature(db, item.item_id, content='feature1')
        r = _sss()._batch_get_progression_states([item.item_id], [user.id], 1, 1)
        assert r[(item.item_id, user.id)] == ProgressionStatus.NOT_STARTED

    def test_STATS_060_ranking_partial_progressing(self, app, db, app_context):
        """[STATS-060] Ranking with partial rankings -> PROGRESSING."""
        from db.models.scenario import ProgressionStatus
        fft = _create_function_type(db, 'ranking')
        user = _create_user(db, 'user_rank_2')
        item = _create_item(db, fft.function_type_id, chat_id=21, institut_id=21)
        f1 = _create_feature(db, item.item_id, content='f1')
        _create_feature(db, item.item_id, content='f2')
        _create_ranking(db, user.id, f1.feature_id, bucket='gut')
        r = _sss()._batch_get_progression_states([item.item_id], [user.id], 1, 1)
        assert r[(item.item_id, user.id)] == ProgressionStatus.PROGRESSING

    def test_STATS_061_ranking_all_done(self, app, db, app_context):
        """[STATS-061] Ranking with all features ranked -> DONE."""
        from db.models.scenario import ProgressionStatus
        fft = _create_function_type(db, 'ranking')
        user = _create_user(db, 'user_rank_3')
        item = _create_item(db, fft.function_type_id, chat_id=22, institut_id=22)
        f1 = _create_feature(db, item.item_id, content='f1')
        f2 = _create_feature(db, item.item_id, content='f2')
        _create_ranking(db, user.id, f1.feature_id, bucket='gut')
        _create_ranking(db, user.id, f2.feature_id, bucket='mittel')
        r = _sss()._batch_get_progression_states([item.item_id], [user.id], 1, 1)
        assert r[(item.item_id, user.id)] == ProgressionStatus.DONE

    def test_STATS_062_rating_with_dimension_rating_done(self, app, db, app_context):
        """[STATS-062] Rating with ItemDimensionRating status=DONE -> DONE."""
        from db.models.scenario import ProgressionStatus
        fft = _create_function_type(db, 'rating')
        user = _create_user(db, 'user_rate_1')
        scenario = _create_scenario(db, 'RatingTest', fft.function_type_id)
        item = _create_item(db, fft.function_type_id, chat_id=30, institut_id=30)
        _create_dimension_rating(db, user.id, item.item_id, scenario.id, {"coherence": 4}, overall_score=4.5)
        r = _sss()._batch_get_progression_states([item.item_id], [user.id], 2, scenario.id)
        assert r[(item.item_id, user.id)] == ProgressionStatus.DONE

    def test_STATS_063_authenticity_voted_is_done(self, app, db, app_context):
        """[STATS-063] Authenticity vote exists -> DONE."""
        from db.models.scenario import ProgressionStatus
        fft = _create_function_type(db, 'authenticity')
        user = _create_user(db, 'user_auth_1')
        item = _create_item(db, fft.function_type_id, chat_id=40, institut_id=40)
        _create_authenticity_vote(db, user.id, item.item_id, vote='fake')
        r = _sss()._batch_get_progression_states([item.item_id], [user.id], 5, 1)
        assert r[(item.item_id, user.id)] == ProgressionStatus.DONE

    def test_STATS_064_authenticity_no_vote_not_started(self, app, db, app_context):
        """[STATS-064] No authenticity vote -> NOT_STARTED."""
        from db.models.scenario import ProgressionStatus
        fft = _create_function_type(db, 'authenticity')
        user = _create_user(db, 'user_auth_2')
        item = _create_item(db, fft.function_type_id, chat_id=41, institut_id=41)
        r = _sss()._batch_get_progression_states([item.item_id], [user.id], 5, 1)
        assert r[(item.item_id, user.id)] == ProgressionStatus.NOT_STARTED

    def test_STATS_065_mail_rating_done(self, app, db, app_context):
        """[STATS-065] Mail rating with status=DONE -> DONE."""
        from db.models.scenario import ProgressionStatus
        fft = _create_function_type(db, 'mail_rating')
        user = _create_user(db, 'user_mail_1')
        item = _create_item(db, fft.function_type_id, chat_id=50, institut_id=50)
        _create_mail_rating(db, user.id, item.item_id, overall_rating=4, status='Done')
        r = _sss()._batch_get_progression_states([item.item_id], [user.id], 3, 1)
        assert r[(item.item_id, user.id)] == ProgressionStatus.DONE

    def test_STATS_066_mail_rating_no_rating_not_started(self, app, db, app_context):
        """[STATS-066] No mail rating -> NOT_STARTED."""
        from db.models.scenario import ProgressionStatus
        fft = _create_function_type(db, 'mail_rating')
        user = _create_user(db, 'user_mail_2')
        item = _create_item(db, fft.function_type_id, chat_id=51, institut_id=51)
        r = _sss()._batch_get_progression_states([item.item_id], [user.id], 3, 1)
        assert r[(item.item_id, user.id)] == ProgressionStatus.NOT_STARTED


# =============================================================================
# TESTS: _build_llm_progress_entries
# =============================================================================

class TestBuildLlmProgressEntries:
    def test_STATS_067_empty_threads_returns_empty(self, app, db, app_context):
        """[STATS-067] Empty thread list returns empty."""
        r = _sss()._build_llm_progress_entries(scenario_id=1, thread_ids=[], task_type='ranking')
        assert r == []

    def test_STATS_068_no_results_with_model_ids(self, app, db, app_context):
        """[STATS-068] Configured model IDs with no results show as not_started."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'LLM Test', fft.function_type_id)
        item = _create_item(db, fft.function_type_id, chat_id=60, institut_id=60)
        _create_llm_model(db, 'test/model-1', 'Test Model 1')
        r = _sss()._build_llm_progress_entries(
            scenario_id=scenario.id, thread_ids=[item.item_id],
            task_type='ranking', model_ids=['test/model-1'],
        )
        assert len(r) == 1
        assert r[0]['is_llm'] is True
        assert r[0]['done_threads'] == 0
        assert r[0]['not_started_threads'] == 1

    def test_STATS_069_completed_results(self, app, db, app_context):
        """[STATS-069] Completed LLM results counted as done."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'LLM Done', fft.function_type_id)
        item = _create_item(db, fft.function_type_id, chat_id=61, institut_id=61)
        _create_llm_model(db, 'test/model-2', 'Test Model 2')
        _create_llm_task_result(db, scenario.id, item.item_id, 'test/model-2', 'ranking', payload_json={"gut": [1]})
        r = _sss()._build_llm_progress_entries(
            scenario_id=scenario.id, thread_ids=[item.item_id],
            task_type='ranking', model_ids=['test/model-2'],
        )
        assert r[0]['done_threads'] == 1

    def test_STATS_070_error_results(self, app, db, app_context):
        """[STATS-070] Errored LLM results counted as error_threads."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'LLM Err', fft.function_type_id)
        item = _create_item(db, fft.function_type_id, chat_id=62, institut_id=62)
        _create_llm_model(db, 'test/model-err', 'Err Model')
        _create_llm_task_result(db, scenario.id, item.item_id, 'test/model-err', 'ranking', error='timeout')
        r = _sss()._build_llm_progress_entries(
            scenario_id=scenario.id, thread_ids=[item.item_id],
            task_type='ranking', model_ids=['test/model-err'],
        )
        assert r[0]['error_threads'] == 1
        assert r[0]['done_threads'] == 0


# =============================================================================
# TESTS: get_user_progress_counts
# =============================================================================

class TestGetUserProgressCounts:
    def test_STATS_071_empty_scenario(self, app, db, app_context):
        """[STATS-071] Empty scenario returns empty dict."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'Empty', fft.function_type_id)
        assert _sss().get_user_progress_counts(scenario.id) == {}

    def test_STATS_072_user_with_all_done(self, app, db, app_context):
        """[STATS-072] User with all items done."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'Progress', fft.function_type_id, config_json={"distribution_mode": "all"})
        user = _create_user(db, 'progress_user')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        item = _create_item(db, fft.function_type_id, chat_id=70, institut_id=70)
        _add_scenario_item(db, scenario.id, item.item_id)
        f1 = _create_feature(db, item.item_id, content='f1')
        _create_ranking(db, user.id, f1.feature_id, bucket='gut')
        r = _sss().get_user_progress_counts(scenario.id)
        assert r['progress_user']['done'] == 1
        assert r['progress_user']['total'] == 1

    def test_STATS_073_comparison_returns_empty(self, app, db, app_context):
        """[STATS-073] Comparison scenario returns empty dict."""
        fft = _create_function_type(db, 'comparison')
        scenario = _create_scenario(db, 'Comp', fft.function_type_id)
        assert _sss().get_user_progress_counts(scenario.id) == {}


# =============================================================================
# TESTS: get_progress_stats (main orchestration)
# =============================================================================

class TestGetProgressStats:
    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.resolve_model_registry')
    def test_STATS_074_ranking_scenario_basic(self, mock_registry, mock_brief, app, db, app_context):
        """[STATS-074] Basic ranking scenario returns expected structure."""
        mock_brief.return_value = {"username": "eval_user", "avatar_seed": None, "avatar_url": None}
        mock_registry.return_value = {}
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'Stats', fft.function_type_id, config_json={"distribution_mode": "all"})
        user = _create_user(db, 'eval_user')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        item = _create_item(db, fft.function_type_id, chat_id=80, institut_id=80)
        _add_scenario_item(db, scenario.id, item.item_id)
        f1 = _create_feature(db, item.item_id, content='summary1')
        _create_ranking(db, user.id, f1.feature_id, bucket='gut')
        result = _sss().get_progress_stats(scenario.id, skip_provenance=True)
        assert 'rater_stats' in result
        assert 'evaluator_stats' in result
        assert 'krippendorff_alpha' in result
        assert 'bucket_distribution' in result
        assert len(result['rater_stats']) == 1
        assert result['rater_stats'][0]['done_threads'] == 1

    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.resolve_model_registry')
    def test_STATS_075_empty_ranking_scenario(self, mock_registry, mock_brief, app, db, app_context):
        """[STATS-075] Ranking scenario with no items returns zeros."""
        mock_brief.return_value = {"username": "empty_user", "avatar_seed": None, "avatar_url": None}
        mock_registry.return_value = {}
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'Empty Stats', fft.function_type_id)
        user = _create_user(db, 'empty_user')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        result = _sss().get_progress_stats(scenario.id)
        assert result['rater_stats'][0]['total_threads'] == 0
        assert result['rater_stats'][0]['done_threads'] == 0

    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.DimensionalRatingService')
    @patch('services.scenario_stats_service.resolve_model_registry')
    def test_STATS_076_rating_scenario_has_distribution(self, mock_registry, mock_dim_svc,
                                                          mock_brief, app, db, app_context):
        """[STATS-076] Rating scenario returns rating_distribution and dimension_averages."""
        mock_brief.return_value = {"username": "rater_user", "avatar_seed": None, "avatar_url": None}
        mock_registry.return_value = {}
        mock_dim_svc.get_scenario_config.return_value = {
            "min": 1, "max": 5,
            "dimensions": [{"id": "coherence", "name": {"en": "Coherence"}}],
            "labels": {},
        }
        fft = _create_function_type(db, 'rating')
        scenario = _create_scenario(db, 'Rating Stats', fft.function_type_id, config_json={"distribution_mode": "all"})
        user = _create_user(db, 'rater_user')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        item = _create_item(db, fft.function_type_id, chat_id=81, institut_id=81)
        _add_scenario_item(db, scenario.id, item.item_id)
        _create_dimension_rating(db, user.id, item.item_id, scenario.id, {"coherence": 4}, overall_score=4.5)
        result = _sss().get_progress_stats(scenario.id, skip_provenance=True)
        assert result['rating_distribution'] is not None
        assert result['dimension_averages'] is not None

    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.resolve_model_registry')
    def test_STATS_078_owner_in_evaluator_stats(self, mock_registry, mock_brief, app, db, app_context):
        """[STATS-078] OWNER users appear in evaluator_stats, not rater_stats."""
        mock_brief.return_value = {"username": "owner_user", "avatar_seed": None, "avatar_url": None}
        mock_registry.return_value = {}
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'Owner', fft.function_type_id, config_json={"distribution_mode": "all"})
        user = _create_user(db, 'owner_user')
        _add_scenario_user(db, scenario.id, user.id, 'Owner')
        result = _sss().get_progress_stats(scenario.id, skip_provenance=True)
        owner_entries = [e for e in result['evaluator_stats'] if e.get('username') == 'owner_user']
        assert len(owner_entries) == 1


# =============================================================================
# TESTS: _calculate_unified_pairwise_agreement dispatcher
# =============================================================================

class TestUnifiedPairwiseAgreement:
    def test_STATS_079_unknown_type_returns_empty(self, app, db, app_context):
        """[STATS-079] Unknown function type returns empty agreement."""
        r = _sss()._calculate_unified_pairwise_agreement(1, "unknown_type")
        assert r == {"evaluators": [], "agreements": {}}

    def test_STATS_080_ranking_dispatches(self, app, db, app_context):
        """[STATS-080] Ranking type dispatches to ranking agreement."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'Pairwise', fft.function_type_id)
        r = _sss()._calculate_unified_pairwise_agreement(scenario.id, "ranking")
        assert "evaluators" in r
        assert "agreements" in r


# =============================================================================
# TESTS: Rating distribution
# =============================================================================

class TestCalculateRatingDistribution:
    @patch('services.scenario_stats_service.DimensionalRatingService')
    def test_STATS_081_empty_scenario_returns_empty_distribution(self, mock_dim_svc, app, db, app_context):
        """[STATS-081] Empty scenario returns zero-count distribution."""
        mock_dim_svc.get_scenario_config.return_value = {
            "min": 1, "max": 5,
            "dimensions": [{"id": "coherence", "name": {"en": "Coherence"}}],
            "labels": {},
        }
        fft = _create_function_type(db, 'rating')
        scenario = _create_scenario(db, 'Empty Rating', fft.function_type_id)
        result = _sss()._calculate_rating_distribution(scenario.id)
        assert 'all' in result
        assert 'humans' in result
        assert 'llms' in result
        for entry in result['all']:
            assert entry['count'] == 0


# =============================================================================
# TESTS: Bucket distribution
# =============================================================================

class TestCalculateBucketDistribution:
    def test_STATS_082_empty_scenario_returns_empty(self, app, db, app_context):
        """[STATS-082] Scenario with no items returns empty list."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'EmptyBucket', fft.function_type_id)
        assert _sss()._calculate_bucket_distribution(scenario.id) == []

    def test_STATS_083_distribution_with_human_rankings(self, app, db, app_context):
        """[STATS-083] Human rankings produce correct bucket counts.

        The user must be an active scenario member because bucket distribution
        only counts rankings from active members.
        """
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'BucketTest', fft.function_type_id, config_json={
            "buckets": [
                {"id": "gut", "name": {"de": "Gut", "en": "Good"}, "color": "#00ff00"},
                {"id": "schlecht", "name": {"de": "Schlecht", "en": "Bad"}, "color": "#ff0000"},
            ]
        })
        user = _create_user(db, 'bucket_user')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        item1 = _create_item(db, fft.function_type_id, chat_id=90, institut_id=90)
        item2 = _create_item(db, fft.function_type_id, chat_id=91, institut_id=91)
        _add_scenario_item(db, scenario.id, item1.item_id)
        _add_scenario_item(db, scenario.id, item2.item_id)
        f1 = _create_feature(db, item1.item_id, content='f1')
        f2 = _create_feature(db, item2.item_id, content='f2')
        _create_ranking(db, user.id, f1.feature_id, bucket='gut')
        _create_ranking(db, user.id, f2.feature_id, bucket='schlecht')
        result = _sss()._calculate_bucket_distribution(scenario.id)
        assert len(result) == 2
        gut = [b for b in result if b['bucket'] == 'gut'][0]
        schlecht = [b for b in result if b['bucket'] == 'schlecht'][0]
        assert gut['count'] == 1
        assert schlecht['count'] == 1
        assert gut['percentage'] == 50

    def test_STATS_084_distribution_with_llm_rankings(self, app, db, app_context):
        """[STATS-084] LLM rankings are included in bucket distribution."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'LLMBucket', fft.function_type_id, config_json={
            "buckets": [
                {"id": "gut", "name": {"de": "Gut", "en": "Good"}},
                {"id": "schlecht", "name": {"de": "Schlecht", "en": "Bad"}},
            ]
        })
        item = _create_item(db, fft.function_type_id, chat_id=92, institut_id=92)
        _add_scenario_item(db, scenario.id, item.item_id)
        f1 = _create_feature(db, item.item_id, content='llm_f')
        _create_llm_task_result(db, scenario.id, item.item_id, 'test/llm-b', 'ranking',
                                payload_json={"gut": [f1.feature_id], "schlecht": []})
        result = _sss()._calculate_bucket_distribution(scenario.id)
        gut = [b for b in result if b['bucket'] == 'gut'][0]
        assert gut['count'] == 1


# =============================================================================
# TESTS: Labeling distribution
# =============================================================================

class TestCalculateLabelingDistribution:
    def test_STATS_085_empty_returns_empty(self, app, db, app_context):
        """[STATS-085] No categories returns empty dict."""
        fft = _create_function_type(db, 'labeling')
        scenario = _create_scenario(db, 'LabelEmpty', fft.function_type_id)
        assert _sss()._calculate_labeling_distribution(scenario.id) == {}

    def test_STATS_086_with_categories_zero_counts(self, app, db, app_context):
        """[STATS-086] Categories with no evaluations return zero counts."""
        fft = _create_function_type(db, 'labeling')
        scenario = _create_scenario(db, 'LabelCats', fft.function_type_id, config_json={
            "categories": [{"id": "positive", "name": "Positive"}, {"id": "negative", "name": "Negative"}]
        })
        result = _sss()._calculate_labeling_distribution(scenario.id)
        assert 'all' in result
        assert len(result['all']) == 2
        assert result['all'][0]['count'] == 0


# =============================================================================
# TESTS: Rating Krippendorff Alpha
# =============================================================================

class TestRatingKrippendorffAlpha:
    def test_STATS_087_too_few_threads_returns_none(self, app, db, app_context):
        """[STATS-087] Less than 2 threads returns all None."""
        fft = _create_function_type(db, 'rating')
        scenario = _create_scenario(db, 'Alpha1', fft.function_type_id)
        item = _create_item(db, fft.function_type_id, chat_id=100, institut_id=100)
        _add_scenario_item(db, scenario.id, item.item_id)
        r = _sss()._calculate_rating_krippendorff_alpha(scenario.id)
        assert r == {"all": None, "humans": None, "llms": None}

    def test_STATS_088_two_human_raters_perfect_agreement(self, app, db, app_context):
        """[STATS-088] Two human raters with identical scores -> alpha = 1.0."""
        fft = _create_function_type(db, 'rating')
        scenario = _create_scenario(db, 'Alpha2', fft.function_type_id)
        u1 = _create_user(db, 'alpha_user1')
        u2 = _create_user(db, 'alpha_user2')
        items = []
        for i in range(3):
            item = _create_item(db, fft.function_type_id, chat_id=110+i, institut_id=110+i)
            _add_scenario_item(db, scenario.id, item.item_id)
            items.append(item)
        for item in items:
            _create_dimension_rating(db, u1.id, item.item_id, scenario.id, {"c": 4}, overall_score=4.0)
            _create_dimension_rating(db, u2.id, item.item_id, scenario.id, {"c": 4}, overall_score=4.0)
        r = _sss()._calculate_rating_krippendorff_alpha(scenario.id)
        assert r['humans'] == 1.0

    def test_STATS_089_varying_scores_produces_alpha(self, app, db, app_context):
        """[STATS-089] Varying scores produce a numeric alpha."""
        fft = _create_function_type(db, 'rating')
        scenario = _create_scenario(db, 'Alpha3', fft.function_type_id)
        u1 = _create_user(db, 'var_user1')
        u2 = _create_user(db, 'var_user2')
        items = []
        for i in range(4):
            item = _create_item(db, fft.function_type_id, chat_id=120+i, institut_id=120+i)
            _add_scenario_item(db, scenario.id, item.item_id)
            items.append(item)
        scores = [(1, 1), (2, 2), (3, 3), (4, 5)]
        for item, (s1, s2) in zip(items, scores):
            _create_dimension_rating(db, u1.id, item.item_id, scenario.id, {"c": s1}, overall_score=float(s1))
            _create_dimension_rating(db, u2.id, item.item_id, scenario.id, {"c": s2}, overall_score=float(s2))
        r = _sss()._calculate_rating_krippendorff_alpha(scenario.id)
        assert r['humans'] is not None
        assert 0.5 < r['humans'] < 1.0


# =============================================================================
# TESTS: Pairwise agreement
# =============================================================================

class TestCalculatePairwiseAgreement:
    def test_STATS_090_empty_returns_empty(self, app, db, app_context):
        """[STATS-090] No ratings returns empty evaluators/agreements."""
        fft = _create_function_type(db, 'rating')
        scenario = _create_scenario(db, 'PairEmpty', fft.function_type_id)
        r = _sss()._calculate_pairwise_agreement(scenario.id)
        assert r == {"evaluators": [], "agreements": {}}

    def test_STATS_091_two_raters_agreement(self, app, db, app_context):
        """[STATS-091] Two raters with some agreement produces correct score."""
        fft = _create_function_type(db, 'rating')
        scenario = _create_scenario(db, 'Pair2', fft.function_type_id)
        u1 = _create_user(db, 'pair_user1')
        u2 = _create_user(db, 'pair_user2')
        items = []
        for i in range(4):
            item = _create_item(db, fft.function_type_id, chat_id=130+i, institut_id=130+i)
            _add_scenario_item(db, scenario.id, item.item_id)
            items.append(item)
        u1_scores = [3.0, 4.0, 3.0, 5.0]
        u2_scores = [3.0, 4.0, 2.0, 5.0]
        for item, s1, s2 in zip(items, u1_scores, u2_scores):
            _create_dimension_rating(db, u1.id, item.item_id, scenario.id, {"c": s1}, overall_score=s1)
            _create_dimension_rating(db, u2.id, item.item_id, scenario.id, {"c": s2}, overall_score=s2)
        r = _sss()._calculate_pairwise_agreement(scenario.id)
        assert len(r['evaluators']) == 2
        assert len(r['agreements']) == 1
        assert list(r['agreements'].values())[0] == 0.75


# =============================================================================
# TESTS: get_scenario_stats_payload
# =============================================================================

class TestGetScenarioStatsPayload:
    @patch('services.scenario_stats_service.get_authenticity_stats')
    def test_STATS_092_authenticity_returns_authenticity_kind(self, mock_auth, app, db, app_context):
        """[STATS-092] Authenticity scenario returns kind='authenticity'."""
        mock_auth.return_value = {"scenario_id": 1}
        fft = _create_function_type(db, 'authenticity')
        scenario = _create_scenario(db, 'AuthPayload', fft.function_type_id)
        r = _sss().get_scenario_stats_payload(scenario.id)
        assert r['kind'] == 'authenticity'
        assert r['function_type'] == 'authenticity'

    def test_STATS_093_non_authenticity_returns_progress_kind(self, app, db, app_context):
        """[STATS-093] Non-authenticity scenario returns kind='progress'."""
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'RankPayload', fft.function_type_id)
        with patch('services.scenario_stats_cache_service.get_cached_stats') as mc:
            mc.return_value = {"rater_stats": []}
            r = _sss().get_scenario_stats_payload(scenario.id)
            assert r['kind'] == 'progress'
            assert r['function_type'] == 'ranking'


# =============================================================================
# TESTS: Edge cases
# =============================================================================

class TestEdgeCases:
    def test_STATS_094_empty_bucket_list_fallback(self, app, db, app_context):
        """[STATS-094] Empty bucket list falls back to default."""
        r = _sss()._extract_ranking_bucket_config({"buckets": []})
        assert len(r) == 3

    def test_STATS_095_config_dot_config_dot_buckets(self, app, db, app_context):
        """[STATS-095] config.config.buckets path is supported."""
        config = {"config": {"buckets": [{"id": "x", "name": "X"}]}}
        assert len(_sss()._extract_ranking_bucket_config(config)) == 1

    def test_STATS_096_non_dict_bucket_entries_skipped(self, app, db, app_context):
        """[STATS-096] Non-string/non-dict bucket entries are skipped."""
        r = _sss()._extract_ranking_bucket_config({"buckets": [42, None, {"id": "valid"}]})
        assert len(r) == 1

    def test_STATS_097_equal_min_max_resets(self, app, db, app_context):
        """[STATS-097] Equal min/max resets to defaults."""
        assert _sss()._extract_rating_scale_bounds({"min": 3, "max": 3}) == {"min": 1.0, "max": 5.0}

    def test_STATS_098_normalize_bucket_with_integer(self, app, db, app_context):
        """[STATS-098] Integer value is converted to string."""
        assert _sss()._normalize_bucket_lookup_key(42) == "42"

    def test_STATS_099_humanize_multiple_underscores(self, app, db, app_context):
        """[STATS-099] Multiple underscored words are all capitalized."""
        assert _sss()._humanize_bucket_identifier("very_very_good") == "Very Very Good"

    def test_STATS_100_normalize_model_identity_special(self, app, db, app_context):
        """[STATS-100] Special characters stripped from model identity."""
        assert _sss()._normalize_model_identity("claude-3.5-sonnet@2024") == "claude35sonnet2024"


# =============================================================================
# TESTS: Authenticity stats
# =============================================================================

class TestGetAuthenticityStats:
    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.get_scenario_distribution_mode')
    def test_STATS_101_empty_scenario(self, mock_dist, mock_brief, app, db, app_context):
        """[STATS-101] Empty authenticity scenario returns zeros."""
        mock_brief.return_value = {"username": "auth_test", "avatar_seed": None, "avatar_url": None}
        mock_dist.return_value = "all"
        fft = _create_function_type(db, 'authenticity')
        scenario = _create_scenario(db, 'AuthEmpty', fft.function_type_id)
        user = _create_user(db, 'auth_test')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        r = _sss().get_authenticity_stats(scenario.id)
        assert r['total_threads'] == 0
        assert r['krippendorff_alpha'] is None

    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.get_scenario_distribution_mode')
    def test_STATS_102_with_votes_computes_accuracy(self, mock_dist, mock_brief, app, db, app_context):
        """[STATS-102] Authenticity with votes computes accuracy."""
        from db.models.authenticity import AuthenticityConversation
        mock_brief.return_value = {"username": "auth_voter", "avatar_seed": None, "avatar_url": None}
        mock_dist.return_value = "all"
        fft = _create_function_type(db, 'authenticity')
        scenario = _create_scenario(db, 'AuthVotes', fft.function_type_id)
        user = _create_user(db, 'auth_voter')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        item_real = _create_item(db, fft.function_type_id, chat_id=200, institut_id=200)
        item_fake = _create_item(db, fft.function_type_id, chat_id=201, institut_id=201)
        _add_scenario_item(db, scenario.id, item_real.item_id)
        _add_scenario_item(db, scenario.id, item_fake.item_id)
        db.session.add_all([
            AuthenticityConversation(item_id=item_real.item_id, sample_key='real_1', is_fake=False),
            AuthenticityConversation(item_id=item_fake.item_id, sample_key='fake_1', is_fake=True, model='GPT-4'),
        ])
        db.session.commit()
        _create_authenticity_vote(db, user.id, item_real.item_id, vote='real')
        _create_authenticity_vote(db, user.id, item_fake.item_id, vote='fake')
        r = _sss().get_authenticity_stats(scenario.id)
        assert r['total_threads'] == 2
        human = [u for u in r['user_stats'] if not u.get('is_llm')]
        assert human[0]['accuracy_percent'] == 100.0


# =============================================================================
# TESTS: Multiple users
# =============================================================================

class TestMultiUserScenario:
    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.resolve_model_registry')
    def test_STATS_103_multiple_evaluators_different_progress(self, mock_reg, mock_brief, app, db, app_context):
        """[STATS-103] Multiple users show individual progress counts."""
        mock_brief.side_effect = lambda u: {"username": u.username, "avatar_seed": None, "avatar_url": None}
        mock_reg.return_value = {}
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'Multi', fft.function_type_id, config_json={"distribution_mode": "all"})
        u1 = _create_user(db, 'multi_u1')
        u2 = _create_user(db, 'multi_u2')
        _add_scenario_user(db, scenario.id, u1.id, 'Assessor')
        _add_scenario_user(db, scenario.id, u2.id, 'Assessor')
        item = _create_item(db, fft.function_type_id, chat_id=300, institut_id=300)
        _add_scenario_item(db, scenario.id, item.item_id)
        f1 = _create_feature(db, item.item_id, content='multi_f1')
        _create_ranking(db, u1.id, f1.feature_id, bucket='gut')
        result = _sss().get_progress_stats(scenario.id, skip_provenance=True)
        u1_s = [r for r in result['rater_stats'] if r['username'] == 'multi_u1'][0]
        u2_s = [r for r in result['rater_stats'] if r['username'] == 'multi_u2'][0]
        assert u1_s['done_threads'] == 1
        assert u2_s['done_threads'] == 0


# =============================================================================
# TESTS: LLM evaluator in progress stats
# =============================================================================

class TestLlmEvaluatorInProgressStats:
    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.resolve_model_registry')
    def test_STATS_104_llm_evaluator_in_stats(self, mock_reg, mock_brief, app, db, app_context):
        """[STATS-104] Configured LLM evaluators appear in evaluator_stats."""
        mock_brief.return_value = {"username": "llm_test_user", "avatar_seed": None, "avatar_url": None}
        mock_reg.return_value = {}
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'LLMEval', fft.function_type_id, config_json={
            "distribution_mode": "all", "llm_evaluators": ["test/llm-eval-1"]
        })
        user = _create_user(db, 'llm_test_user')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        item = _create_item(db, fft.function_type_id, chat_id=400, institut_id=400)
        _add_scenario_item(db, scenario.id, item.item_id)
        _create_llm_model(db, 'test/llm-eval-1', 'LLM Eval')
        _create_llm_task_result(db, scenario.id, item.item_id, 'test/llm-eval-1', 'ranking', payload_json={"gut": [1]})
        result = _sss().get_progress_stats(scenario.id, skip_provenance=True)
        llm = [e for e in result['evaluator_stats'] if e.get('is_llm')]
        assert len(llm) >= 1
        assert llm[0]['done_threads'] == 1


class TestConfigJsonStringParsing:
    @patch('services.scenario_stats_service.serialize_user_brief')
    @patch('services.scenario_stats_service.resolve_model_registry')
    def test_STATS_105_string_config_json(self, mock_reg, mock_brief, app, db, app_context):
        """[STATS-105] config_json as dict is handled without crashing."""
        mock_brief.return_value = {"username": "str_cfg_user", "avatar_seed": None, "avatar_url": None}
        mock_reg.return_value = {}
        fft = _create_function_type(db, 'ranking')
        scenario = _create_scenario(db, 'StrCfg', fft.function_type_id, config_json={"distribution_mode": "all"})
        user = _create_user(db, 'str_cfg_user')
        _add_scenario_user(db, scenario.id, user.id, 'Assessor')
        result = _sss().get_progress_stats(scenario.id, skip_provenance=True)
        assert 'rater_stats' in result


class TestRankingAgreementRegression:
    def test_STATS_106_ranking_progress_stats_handles_feature_primary_key_names(
        self, app, db, app_context
    ):
        """[STATS-106] Ranking stats use Feature.feature_id/item_id and do not crash."""
        service = _sss()

        with patch.object(service, 'serialize_user_brief') as mock_brief, patch.object(service, 'resolve_model_registry') as mock_reg:
            mock_brief.side_effect = lambda u: {"username": u.username, "avatar_seed": None, "avatar_url": None}
            mock_reg.return_value = {}

            fft = _create_function_type(db, 'ranking')
            scenario = _create_scenario(db, 'Ranking Alpha Regression', fft.function_type_id, config_json={
                "distribution_mode": "all",
                "buckets": [
                    {"id": "gut", "name": {"de": "Gut", "en": "Good"}},
                    {"id": "mittel", "name": {"de": "Mittel", "en": "Medium"}},
                ],
            })

            u1 = _create_user(db, 'alpha_u1')
            u2 = _create_user(db, 'alpha_u2')
            _add_scenario_user(db, scenario.id, u1.id, 'Assessor')
            _add_scenario_user(db, scenario.id, u2.id, 'Assessor')

            item1 = _create_item(db, fft.function_type_id, chat_id=500, institut_id=500)
            item2 = _create_item(db, fft.function_type_id, chat_id=501, institut_id=501)
            _add_scenario_item(db, scenario.id, item1.item_id)
            _add_scenario_item(db, scenario.id, item2.item_id)

            feature1 = _create_feature(db, item1.item_id, content='alpha_f1')
            feature2 = _create_feature(db, item2.item_id, content='alpha_f2')

            for user in (u1, u2):
                _create_ranking(db, user.id, feature1.feature_id, bucket='gut')
                _create_ranking(db, user.id, feature2.feature_id, bucket='mittel')

            result = service.get_progress_stats(scenario.id, skip_provenance=True)

        assert len(result['rater_stats']) == 2
        assert result['krippendorff_alpha'] == 1.0
        assert all(entry['done_threads'] == 2 for entry in result['rater_stats'])
