"""
Real-DB scaling benchmark for the ranking IRR / agreement-metrics pipeline.

Seeds a ranking scenario with N features (the unit of analysis) and R raters and
times the production AgreementMetricsService.calculate_all_metrics() — the same
code the /agreement endpoint runs. Answers: does Krippendorff's alpha still
compute correctly AND fast at 1k / 10k rankings, and where is the cost?

Skipped in CI (it seeds tens of thousands of rows). Run explicitly:
    RUN_BENCH=1 python3 -m pytest -s tests/unit/services/test_stats_10k_bench.py
"""

import os
import time

import pytest

from tests.unit.services.test_scenario_stats_service import (
    _sss,
    _create_function_type,
    _create_scenario,
    _create_user,
    _add_scenario_user,
)

# Fully load scenario_stats_service up front so the lazy import inside
# AgreementMetricsService._collect_ranking_evaluations resolves cleanly (in
# production the module is fully loaded at app startup before any request).
_sss()

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_BENCH"), reason="perf benchmark; set RUN_BENCH=1 to run"
)

_BUCKETS = ["gut", "mittel", "neutral", "schlecht"]
_BUCKET_CONFIG = {"buckets": [
    {"id": "gut", "name": {"de": "Gut"}},
    {"id": "mittel", "name": {"de": "Mittel"}},
    {"id": "neutral", "name": {"de": "Neutral"}},
    {"id": "schlecht", "name": {"de": "Schlecht"}},
]}


def _seed_ranking(db, n_features, n_raters):
    """Bulk-seed a ranking scenario: n_features features, each ranked by n_raters."""
    from db.models.scenario import (
        EvaluationItem, Feature, UserFeatureRanking, ScenarioItems,
    )
    fft = _create_function_type(db, "ranking")
    scenario = _create_scenario(db, "Bench", fft.function_type_id, config_json=_BUCKET_CONFIG)

    users = [_create_user(db, f"bench_u{i}") for i in range(n_raters)]
    for u in users:
        _add_scenario_user(db, scenario.id, u.id, role_str="Assessor")

    # One item per feature keeps the link table simple; bulk insert for speed.
    items = [EvaluationItem(chat_id=i + 1, institut_id=1, subject=f"i{i}",
                            function_type_id=fft.function_type_id) for i in range(n_features)]
    db.session.add_all(items)
    db.session.commit()
    db.session.add_all([ScenarioItems(scenario_id=scenario.id, item_id=it.item_id) for it in items])
    features = [Feature(item_id=it.item_id, content="c") for it in items]
    db.session.add_all(features)
    db.session.commit()

    rankings = []
    for idx, f in enumerate(features):
        base = idx % len(_BUCKETS)  # correlated buckets -> non-degenerate alpha
        for j, u in enumerate(users):
            bucket = _BUCKETS[min(len(_BUCKETS) - 1, max(0, base + ((j % 3) - 1)))]
            rankings.append(UserFeatureRanking(user_id=u.id, feature_id=f.feature_id, bucket=bucket))
    db.session.add_all(rankings)
    db.session.commit()
    return scenario


@pytest.mark.parametrize("n_features", [1000, 10000])
def test_BENCH_ranking_agreement_scale(app, db, app_context, n_features):
    from services.evaluation.agreement_metrics_service import AgreementMetricsService

    n_raters = 5
    t_seed = time.time()
    scenario = _seed_ranking(db, n_features, n_raters)
    seed_s = time.time() - t_seed

    t0 = time.time()
    metrics = AgreementMetricsService.calculate_all_metrics(
        scenario_id=scenario.id, include_llm=False, include_human=True
    )
    elapsed = time.time() - t0

    inner = metrics.get("metrics", {}) if isinstance(metrics, dict) else {}
    alpha = inner.get("krippendorff_alpha")
    alpha_val = alpha.get("value") if isinstance(alpha, dict) else alpha
    print(f"\n[BENCH] features={n_features} raters={n_raters} "
          f"seed={seed_s:.2f}s  calculate_all_metrics={elapsed*1000:.0f}ms  "
          f"alpha={alpha_val}  rankings={n_features * n_raters}")

    assert "error" not in metrics
    assert alpha_val is not None
