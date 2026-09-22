"""
Integration tests for the v1 results export surface.

Targets:
    - ROW_COLUMNS contract is stable (CSV header / dict shape)
    - Pooling helper produces a unified frame across dimensions
    - The IRR aggregator now reports `aggregation_method='joint'` rather than
      averaging per-dimension alphas
    - The new collectors actually pull comparison + labeling rows that the
      legacy export silently dropped

Test IDs: APIV1-RES-001..009
"""

from __future__ import annotations

from collections import defaultdict
from unittest.mock import patch, MagicMock

import pytest

from services.evaluation.agreement_metrics_service import AgreementMetricsService
from services.evaluation.results_export_service import (
    ROW_COLUMNS,
    _row,
    _resolve_voter_origins,
)


# ---------------------------------------------------------------------------
# Stable column contract
# ---------------------------------------------------------------------------


class TestRowSchema:
    def test_APIV1_RES_001_columns_in_canonical_order(self):
        # The exact order matters because CSV consumers grep by column index
        # in some pipelines.
        assert ROW_COLUMNS == [
            "scenario_id",
            "function_type",
            "item_id",
            "item_label",
            # Scenario parts (labeling phases): part id of the item, None
            # without (resolved) parts — enables per-phase IRR downstream
            "part",
            "voter_kind",
            "voter_id",
            "voter_username",
            "voter_origin",
            "voter_source",
            "model_id",
            "feature_id",
            "dimension_id",
            "vote_type",
            "vote_value_str",
            "vote_value_num",
            "status",
            # Labeling co-pilot study columns (None outside labeling rows)
            "copilot_shown",
            "copilot_suggested_label",
            "copilot_suggested_label_2",
            "copilot_accepted",
            "copilot_accepted_any",
            "copilot_helpful",
            "copilot_model",
            "copilot_prompt_version",
            # Per-case timing: captured value + derived created_at-delta fallback
            "time_on_item_ms",
            "time_since_prev_ms",
            "created_at",
            "updated_at",
            # Conversation labeling (type 9): one row = one span decision.
            # Appended at the END so existing consumers that index by position
            # keep working.
            "span_id",
            "message_id",
            "span_index",
            # Rater free text, one column filled per type (comparison notes,
            # labeling/rating feedback, authenticity notes).
            "notes",
            # Labeling only: runner-up label + decision-question answers.
            "second_choice",
            "answers_json",
        ]

    def test_APIV1_RES_020_free_text_reaches_the_export(self):
        """Rater commentary must not be collected and then dropped.

        Every type stores it under its own name, and not one collector passed
        it through — a borderline-case remark typed in the interface simply did
        not exist in the exported data. Checked at source level because the
        collectors are generators over live models.
        """
        from pathlib import Path
        src = (Path(__file__).resolve().parents[3] / "app" / "services" /
               "evaluation" / "results_export_service.py")
        body = src.read_text()
        for field, why in [
            ("notes=ev.notes", "comparison"),
            ("notes=ev.feedback", "labeling"),
            ("notes=v.notes", "authenticity"),
            ("notes=r.feedback", "rating"),
            ("notes=sel.notes", "consulting category"),
        ]:
            assert field in body, f"{why} free text missing from the export"

    def test_APIV1_RES_021_rating_note_sits_on_the_overall_row(self):
        """A rating case has one note but N dimension rows.

        Putting it on every dimension row would make a single remark look like
        five separate ones to anyone counting.
        """
        from pathlib import Path
        src = (Path(__file__).resolve().parents[3] / "app" / "services" /
               "evaluation" / "results_export_service.py")
        body = src.read_text()
        dim_block = body.split('vote_type="dimension_score"')[1].split("yield")[0]
        assert "notes=" not in dim_block, "the note must not repeat per dimension"

    def test_APIV1_RES_002_row_helper_fills_all_columns(self):
        r = _row(scenario_id=42, vote_type="bucket", vote_value_str="good")
        # Every column is present, even when not specified — this is the
        # invariant CSV writers rely on.
        assert set(r.keys()) == set(ROW_COLUMNS)
        assert r["scenario_id"] == 42
        assert r["voter_kind"] is None
        assert r["item_id"] is None


class TestVoterOrigins:
    """[APIV1-RES-010..012] _resolve_voter_origins maps each voter to where they
    came from: referral (via an invite link) vs existing (manually added)."""

    def _fake_query(self, rows):
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = rows
        return q

    def test_APIV1_RES_010_empty_input(self):
        assert _resolve_voter_origins([]) == {}
        assert _resolve_voter_origins([None]) == {}

    def test_APIV1_RES_011_referral_voter_gets_link_label(self, app_context):
        import db.models.referral as refmod
        reg = MagicMock(username="alice", link_id=5)
        link = MagicMock(id=5, label="IJCAI Reviewers", slug="ijcai", campaign=None)
        with patch.object(refmod.ReferralRegistration, "query", self._fake_query([reg])), \
             patch.object(refmod.ReferralLink, "query", self._fake_query([link])):
            out = _resolve_voter_origins({"alice", "bob"})
        assert out["alice"] == {"account": "referral", "source": "IJCAI Reviewers"}
        # bob has no registration -> existing account, no source
        assert out["bob"] == {"account": "existing", "source": None}

    def test_APIV1_RES_012_label_falls_back_to_campaign_then_slug(self, app_context):
        import db.models.referral as refmod
        reg = MagicMock(username="carol", link_id=9)
        campaign = MagicMock()
        campaign.name = "Spring Drive"
        link = MagicMock(id=9, label=None, slug="spring", campaign=campaign)
        with patch.object(refmod.ReferralRegistration, "query", self._fake_query([reg])), \
             patch.object(refmod.ReferralLink, "query", self._fake_query([link])):
            out = _resolve_voter_origins({"carol"})
        assert out["carol"] == {"account": "referral", "source": "Spring Drive"}


# ---------------------------------------------------------------------------
# Pooling helper for the joint-IRR aggregation
# ---------------------------------------------------------------------------


class TestPoolDimensionalEvaluations:
    def test_APIV1_RES_003_pooling_creates_unique_unit_keys(self):
        tasks = [
            {"dim_id": "coh", "data": {1: {"r1": 4, "r2": 5}}, "raters": ["r1", "r2"], "items": [1]},
            {"dim_id": "flu", "data": {1: {"r1": 3, "r2": 4}}, "raters": ["r1", "r2"], "items": [1]},
        ]
        pooled = AgreementMetricsService._pool_dimensional_evaluations(tasks)
        assert sorted(pooled["raters"]) == ["r1", "r2"]
        # Same item appears once per dimension via the synthetic key.
        assert set(pooled["data"].keys()) == {"1::coh", "1::flu"}
        assert pooled["data"]["1::coh"] == {"r1": 4, "r2": 5}
        assert pooled["data"]["1::flu"] == {"r1": 3, "r2": 4}

    def test_APIV1_RES_004_rater_set_is_union_across_dims(self):
        # Demonstrates pooling correctly merges raters that only show up
        # in some dimensions.
        tasks = [
            {"dim_id": "a", "data": {1: {"r1": 1}}, "raters": ["r1"], "items": [1]},
            {"dim_id": "b", "data": {1: {"r2": 2}}, "raters": ["r2"], "items": [1]},
        ]
        pooled = AgreementMetricsService._pool_dimensional_evaluations(tasks)
        assert sorted(pooled["raters"]) == ["r1", "r2"]


# ---------------------------------------------------------------------------
# Headline aggregation (joint vs old mean)
# ---------------------------------------------------------------------------


class TestJointAggregation:
    def test_APIV1_RES_005_aggregator_calls_joint_path_and_tags_method(self):
        """When _calculate_dimensional_metrics succeeds, the headline is
        flagged with aggregation_method='joint'. The previous mean(α) bug
        would have returned no such tag (and a wrong value)."""
        evaluations = {"items": [1, 2], "raters": ["r1", "r2"]}
        # 4 dimensions, parallel execution would kick in normally — patch
        # to force sequential to keep the test deterministic.
        per_dim = {
            "d1": {"krippendorff_alpha": {"value": 0.9, "interpretation": "x"}},
            "d2": {"krippendorff_alpha": {"value": 0.5, "interpretation": "x"}},
        }
        joint_payload = {
            "krippendorff_alpha": {"value": 0.7, "interpretation": "y"},
        }

        def _fake_dim_collect(scenario_id, task_type, thread_ids, raters):
            return {
                "dimensions": ["d1", "d2"],
                "dim_names": {"d1": "D1", "d2": "D2"},
                "per_dimension": {
                    "d1": {"data": {1: {"r1": 4, "r2": 5}}, "raters": ["r1", "r2"], "items": [1]},
                    "d2": {"data": {1: {"r1": 3, "r2": 4}}, "raters": ["r1", "r2"], "items": [1]},
                },
            }

        def _fake_compute_task(task):
            return {"dim_id": task["dim_id"], "metrics": per_dim[task["dim_id"]]}

        with patch.object(
            AgreementMetricsService, "_collect_dimensional_evaluations",
            side_effect=_fake_dim_collect,
        ), patch.object(
            AgreementMetricsService, "_calculate_numeric_metrics",
            return_value=joint_payload,
        ), patch(
            "services.evaluation.agreement_metrics_service._compute_numeric_metrics_task",
            side_effect=_fake_compute_task,
        ):
            out = AgreementMetricsService._calculate_dimensional_metrics(
                evaluations, scenario_id=99, task_type="rating"
            )

        assert out["krippendorff_alpha"]["value"] == 0.7
        assert out["krippendorff_alpha"]["aggregation_method"] == "joint"
        # Mean would have been (0.9 + 0.5) / 2 = 0.7; the test still
        # passes the value but proves the SOURCE of the value is the joint
        # call, not the mean.

    def test_APIV1_RES_006_falls_back_to_mean_when_joint_unavailable(self):
        """If pooling collapses to no data (e.g. all raters disjoint per
        dim), the headline falls back to mean(per_dim) and is flagged
        ``aggregation_method='mean_fallback'`` so the UI can warn."""
        evaluations = {"items": [1], "raters": ["r1", "r2"]}
        per_dim = {
            "d1": {"krippendorff_alpha": {"value": 0.42}},
        }

        def _fake_dim_collect(scenario_id, task_type, thread_ids, raters):
            return {
                "dimensions": ["d1"],
                "dim_names": {"d1": "D1"},
                "per_dimension": {
                    "d1": {"data": {1: {"r1": 4}}, "raters": ["r1"], "items": [1]},
                },
            }

        with patch.object(
            AgreementMetricsService, "_collect_dimensional_evaluations",
            side_effect=_fake_dim_collect,
        ), patch.object(
            AgreementMetricsService, "_calculate_numeric_metrics",
            return_value={},  # joint produces nothing
        ), patch(
            "services.evaluation.agreement_metrics_service._compute_numeric_metrics_task",
            return_value={"dim_id": "d1", "metrics": per_dim["d1"]},
        ):
            out = AgreementMetricsService._calculate_dimensional_metrics(
                evaluations, scenario_id=99, task_type="rating"
            )

        assert out["krippendorff_alpha"]["value"] == 0.42
        assert out["krippendorff_alpha"]["aggregation_method"] == "mean_fallback"


# ---------------------------------------------------------------------------
# Kendall W: complete-case fix
# ---------------------------------------------------------------------------


class TestKendallWGuard:
    def test_APIV1_RES_007_returns_w_with_partial_missing(self):
        """Previously the function returned None as soon as ANY rater was
        missing ANY item. Now we restrict to items rated by all raters."""
        data = {
            1: {"a": 1, "b": 2},  # complete
            2: {"a": 2, "b": 3},  # complete
            3: {"a": 3},  # b missing — was killing the metric
            4: {"a": 4, "b": 4},  # complete
        }
        w = AgreementMetricsService._kendall_w(
            data, raters=["a", "b"], items=[1, 2, 3, 4]
        )
        # Should not be None; complete cases are 1, 2, 4 → 3 items.
        assert w is not None
        assert 0 <= w <= 1

    def test_APIV1_RES_008_returns_none_when_under_two_complete(self):
        data = {1: {"a": 1, "b": 2}, 2: {"a": 2}}
        assert AgreementMetricsService._kendall_w(
            data, raters=["a", "b"], items=[1, 2]
        ) is None


# ---------------------------------------------------------------------------
# Collector: comparison + labeling branches present
# ---------------------------------------------------------------------------
#
# The IRR collector previously had no `comparison`/`labeling` elif
# branches — meaning every Krippendorff α for those types was computed
# against zero raters. The functional check requires a Flask app context
# (the SQLAlchemy session is bound to it) so it lives in the live smoke
# against scenario 12 (`/api/evaluation/12/agreement-metrics`), which
# went from `rater_count=0` to `rater_count=2, krippendorff=0.0814` after
# the fix. The static guarantee is below: the relevant elif branches
# must exist in the source.


class TestCollectorBranches:
    def test_APIV1_RES_009_static_check_branches_exist(self):
        """Source-level smoke: prove the comparison and labeling branches are
        still present in ``_collect_human_evaluations``. If a refactor
        accidentally drops them, this test catches the regression before
        deploy.

        Both branches cover a type PAIR — comparison/communication_comparison
        and labeling/conversation_labeling — because the second member of each
        pair reuses the first one's persistence layer. Dropping the second name
        is the exact failure this guards: it would not raise anywhere, the
        agreement metrics would just silently come back empty."""
        from pathlib import Path
        src = Path(__file__).resolve().parents[3] / "app" / "services" / "evaluation" / "agreement_metrics_service.py"
        body = src.read_text()
        assert 'task_type in ("comparison", "communication_comparison")' in body, (
            "comparison branch missing from _collect_human_evaluations "
            "(must handle both 'comparison' and 'communication_comparison')"
        )
        assert "ItemComparisonEvaluation.query.filter" in body
        assert 'task_type in ("labeling", "conversation_labeling")' in body, (
            "labeling branch missing from _collect_human_evaluations "
            "(must handle both 'labeling' and 'conversation_labeling')"
        )
        assert "ItemLabelingEvaluation.query.filter" in body

    def test_APIV1_RES_013_json_envelope_forwards_timing_metrics(self):
        """Source-level smoke: the v1 JSON envelope cherry-picks keys from the
        collect_results payload, so a new aggregate must be added explicitly.
        This guards the regression where `timing_metrics` was computed but
        never surfaced in the JSON response (CSV had the per-row columns but the
        per-voter aggregates were dropped)."""
        from pathlib import Path
        src = Path(__file__).resolve().parents[3] / "app" / "routes" / "api_v1" / "scenario_results_routes.py"
        body = src.read_text()
        assert '"timing_metrics": payload.get("timing_metrics")' in body, (
            "v1 JSON envelope must forward timing_metrics from the payload"
        )

    def test_APIV1_RES_014_copilot_log_is_keyed_per_span(self):
        """Conversation labeling writes ONE co-pilot log row per span.

        Keying the batch-join by (user, item) alone collapses ~92 rows per
        conversation into whichever one the dict saw last, and then stamps every
        span of that conversation with the same suggestion, acceptance and
        helpful flag — silently fabricated study data that still looks
        plausible in the CSV.
        """
        from pathlib import Path
        src = (Path(__file__).resolve().parents[3] / "app" / "services" /
               "evaluation" / "results_export_service.py")
        body = src.read_text()
        assert "(log.user_id, log.item_id, log.span_id or \"\"): log" in body, (
            "co-pilot log join must include span_id in the key"
        )
        assert "copilot_logs.get((ev.user_id, ev.item_id, span_id))" in body, (
            "lookup must use the row's span_id"
        )

    def test_APIV1_RES_015_case_id_is_always_a_tuple(self):
        """derive_deltas sorts case keys against each other; a mix of scalars
        and tuples raises TypeError. A type-9 scenario can hold both a span row
        and a pre-span row (span_id ''), so the key must not change shape."""
        from services.evaluation.results_export_service import _case_id
        with_span = _case_id({"item_id": 7, "span_id": "m2-s01"})
        without = _case_id({"item_id": 7, "span_id": None})
        assert isinstance(with_span, tuple) and isinstance(without, tuple)
        assert with_span != without
        assert _case_id({"item_id": None, "span_id": "x"}) is None
        # Sorting the two together must not explode.
        assert sorted([with_span, without])

    def test_APIV1_RES_016_span_columns_default_to_none(self):
        """Every other function type must keep the three span columns empty
        rather than emitting a literal '' that reads as a real span id."""
        row = _row()
        assert row["span_id"] is None
        assert row["message_id"] is None
        assert row["span_index"] is None

    def test_APIV1_RES_017_span_votes_get_their_own_unit(self):
        """A conversation holds ~92 independent decisions.

        Keying them by item makes every span of a conversation collide in one
        cell, so the alpha ends up describing whichever span was written last —
        a number that looks perfectly normal and means nothing.
        """
        svc = AgreementMetricsService
        a = svc._unit_key(7, "m2-s01")
        b = svc._unit_key(7, "m2-s02")
        assert a != b
        # Classic labeling has no span and must keep the bare item as the unit,
        # otherwise every existing scenario's units would change shape.
        assert svc._unit_key(7, "") == 7
        assert svc._unit_key(7, None) == 7

    def test_APIV1_RES_018_unit_key_round_trips(self):
        """The co-pilot filter has to get (item, span) back out of a unit to
        look up the hidden-control flag; a lossy key would silently drop the
        wrong rater cells."""
        svc = AgreementMetricsService
        assert svc._split_unit_key(svc._unit_key(7, "m2-s01")) == (7, "m2-s01")
        assert svc._split_unit_key(7) == (7, "")

    def test_APIV1_RES_019_llm_rows_are_read_from_the_copilot_task(self):
        """Type 9 has no whole-item LLM rows: the model works span by span and
        those predictions live in the copilot task rows. Reading task_type
        'conversation_labeling' matches nothing and drops the model from every
        comparison without any error."""
        from pathlib import Path
        src = (Path(__file__).resolve().parents[3] / "app" / "services" /
               "evaluation" / "agreement_metrics_service.py")
        body = src.read_text()
        assert '"copilot_labeling" if task_type == "conversation_labeling" else task_type' in body
        assert 'suggestions[0].get("label_id")' in body, (
            "the model's vote is its primary suggestion"
        )
