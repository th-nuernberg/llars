"""
Tests for ComparisonPreferenceStatsService.

Covers:
- `_categorize`: prefix/path matching for all known provenance categories
  plus the parameter-count lookup table.
- `get_user_preference_stats`: aggregator semantics — tie-exclusion,
  applicable-only counting on each axis, A/B ordering by feature_id.

Test IDs: [COMP_PREF_001] through [COMP_PREF_020]
"""

import pytest


# =============================================================================
# _categorize — pure parser
# =============================================================================

class TestCategorize:
    """Unit tests for the model_id → category parser."""

    def test_COMP_PREF_001_human_prefix(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        assert _categorize("human:counsellor")["category"] == "Human"

    def test_COMP_PREF_002_sft_prefix(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        assert _categorize("sft:mis24b-instrprofi")["category"] == "Trained-SFT"

    def test_COMP_PREF_003_base_prefix(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        assert _categorize("base:mis24b")["category"] == "Pre-Base"

    def test_COMP_PREF_004_global_mistral_is_pre_instruct(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        cat = _categorize("Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506")
        assert cat["category"] == "Pre-Instruct"

    def test_COMP_PREF_005_global_openai_is_closed_baseline(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        assert _categorize("Global/OpenAI/gpt-4o-mini")["category"] == "Closed-Baseline"

    def test_COMP_PREF_006_unknown_for_freeform(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        assert _categorize("user-provider:42:steigerwald:my-fancy-model")["category"] == "Unknown"

    def test_COMP_PREF_007_empty_or_none_is_unknown(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        assert _categorize(None)["category"] == "Unknown"
        assert _categorize("")["category"] == "Unknown"

    def test_COMP_PREF_008_params_b_lookup_hit(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        # "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506" → tail family is
        # the full lower-cased model name; should resolve to 24.0.
        cat = _categorize("Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506")
        assert cat["params_b"] == 24.0

    def test_COMP_PREF_009_params_b_lookup_miss(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        # Unknown family — no params info, params_b is None and the axis
        # cannot contribute to "larger vs smaller".
        cat = _categorize("Global/Mistral/Some-Future-Model-XL")
        assert cat["params_b"] is None

    def test_COMP_PREF_010_sft_tail_family_resolves(self):
        from services.evaluation.comparison_preference_stats_service import _categorize
        # "sft:qwen25-72b-instrprofi" → tail "qwen25-72b-instrprofi" → 72.0
        cat = _categorize("sft:qwen25-72b-instrprofi")
        assert cat["category"] == "Trained-SFT"
        assert cat["params_b"] == 72.0


# =============================================================================
# Aggregator — uses real DB models with SQLite via the `db` fixture
# =============================================================================

@pytest.fixture
def comparison_scenario(app, db):
    """Create a minimal comparison scenario with a known item + 2 features."""
    from db import db as _db
    from db.models.scenario import (
        RatingScenarios, FeatureFunctionType, FeatureType,
        EvaluationItem, Feature,
    )
    from db.models.user import User

    # Function type 4 = comparison
    if FeatureFunctionType.query.get(4) is None:
        _db.session.add(FeatureFunctionType(function_type_id=4, name='comparison'))

    feature_type = FeatureType.query.first()
    if feature_type is None:
        feature_type = FeatureType(type_id=1, name='reply')
        _db.session.add(feature_type)

    user = User(username='test_rater', password_hash='test')
    _db.session.add(user)
    _db.session.flush()

    scenario = RatingScenarios(
        scenario_name='Pref Stats Test',
        function_type_id=4,
        config_json={'gamificationEnabled': True},
    )
    _db.session.add(scenario)
    _db.session.flush()

    item = EvaluationItem(subject='item-1')
    _db.session.add(item)
    _db.session.flush()

    # Two features — A=human, B=Mistral pre-instruct (Pre-Instruct, 24B)
    fa = Feature(item_id=item.item_id, type_id=feature_type.type_id,
                 model_id='human:counsellor', content='human reply')
    fb = Feature(item_id=item.item_id, type_id=feature_type.type_id,
                 model_id='Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506',
                 content='llm reply')
    _db.session.add_all([fa, fb])
    _db.session.commit()

    return {'user': user, 'scenario': scenario, 'item': item}


class TestAggregator:
    """Aggregator semantics over real ItemComparisonEvaluation rows."""

    def test_COMP_PREF_011_empty_scenario_returns_zero_payload(self, app, db, comparison_scenario):
        from services.evaluation.comparison_preference_stats_service import (
            get_user_preference_stats,
        )
        ctx = comparison_scenario
        payload = get_user_preference_stats(ctx['scenario'].id, ctx['user'].id)
        assert payload['total_evaluated'] == 0
        assert payload['preferences']['human_vs_llm']['applicable'] == 0
        assert payload['history'] == []

    def test_COMP_PREF_012_human_choice_counts_on_human_vs_llm_axis(
        self, app, db, comparison_scenario
    ):
        from db import db as _db
        from db.models.scenario import ItemComparisonEvaluation
        from services.evaluation.comparison_preference_stats_service import (
            get_user_preference_stats,
        )
        ctx = comparison_scenario
        # Choose A = human
        _db.session.add(ItemComparisonEvaluation(
            user_id=ctx['user'].id,
            item_id=ctx['item'].item_id,
            scenario_id=ctx['scenario'].id,
            choice='A',
        ))
        _db.session.commit()

        payload = get_user_preference_stats(ctx['scenario'].id, ctx['user'].id)
        assert payload['total_evaluated'] == 1
        assert payload['preferences']['human_vs_llm']['applicable'] == 1
        assert payload['preferences']['human_vs_llm']['chose_human'] == 1
        # B was Pre-Instruct (24B), A was Human (no params): larger axis NOT applicable
        assert payload['preferences']['larger_vs_smaller']['applicable'] == 0

    def test_COMP_PREF_013_tie_excluded_from_all_axes(
        self, app, db, comparison_scenario
    ):
        from db import db as _db
        from db.models.scenario import ItemComparisonEvaluation
        from services.evaluation.comparison_preference_stats_service import (
            get_user_preference_stats,
        )
        ctx = comparison_scenario
        _db.session.add(ItemComparisonEvaluation(
            user_id=ctx['user'].id,
            item_id=ctx['item'].item_id,
            scenario_id=ctx['scenario'].id,
            choice='tie',
        ))
        _db.session.commit()

        payload = get_user_preference_stats(ctx['scenario'].id, ctx['user'].id)
        assert payload['total_evaluated'] == 1
        # tie produces a history entry but never a numerator/denominator bump
        assert payload['preferences']['human_vs_llm']['applicable'] == 0
        assert len(payload['history']) == 1
        assert payload['history'][0]['choice'] == 'tie'

    def test_COMP_PREF_014_history_carries_categories(
        self, app, db, comparison_scenario
    ):
        from db import db as _db
        from db.models.scenario import ItemComparisonEvaluation
        from services.evaluation.comparison_preference_stats_service import (
            get_user_preference_stats,
        )
        ctx = comparison_scenario
        _db.session.add(ItemComparisonEvaluation(
            user_id=ctx['user'].id,
            item_id=ctx['item'].item_id,
            scenario_id=ctx['scenario'].id,
            choice='B',
        ))
        _db.session.commit()

        payload = get_user_preference_stats(ctx['scenario'].id, ctx['user'].id)
        entry = payload['history'][0]
        assert entry['option_a']['category'] == 'Human'
        assert entry['option_b']['category'] == 'Pre-Instruct'
        # Choice B wins → human_vs_llm applicable but chose_human stays 0
        assert payload['preferences']['human_vs_llm']['chose_human'] == 0
        assert payload['preferences']['human_vs_llm']['applicable'] == 1
