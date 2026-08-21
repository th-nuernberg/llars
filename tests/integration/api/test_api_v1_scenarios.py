"""
Integration Tests: /api/v1/scenarios schemas
=============================================

The full HTTP surface lives behind a fairly heavy dependency tree (the wizard
import path, RBAC, referral campaigns), so we end-to-end test it via the
container smoke (curl). What we test here is the contract layer that's most
likely to drift silently if someone refactors the Pydantic schemas:

  - ScenarioCreateRequest accepts the canonical one-shot envelope
  - EvalConfigEnvelope rejects type/config mismatches loudly
  - LlarsNativeEnvelope round-trips features (where the wizard regression
    happened in the past — features were silently dropped)
  - AssessorInvite enforces the role enums
  - ReferralLinkSpec defaults match the docs

Test IDs: APIV1-001..APIV1-016.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.api_v1.scenario_api import (
    AssessorInvite,
    EvalConfigEnvelope,
    LlarsNativeEnvelope,
    NativeFeature,
    NativeItem,
    ReferralLinkSpec,
    ScenarioCreateRequest,
)
from schemas.evaluation_data_schemas import (
    Bucket,
    ComparisonConfig,
    Dimension,
    EvaluationType,
    LocalizedString,
    RatingConfig,
    Scale,
    SimpleRankingConfig,
    Source,
    SourceType,
)


# ---------------------------------------------------------------------------
# EvalConfigEnvelope — the workhorse that protects against type/config drift
# ---------------------------------------------------------------------------


class TestEvalConfigEnvelope:
    def test_APIV1_001_comparison_with_comparison_config(self):
        env = EvalConfigEnvelope(
            type="comparison",
            config=ComparisonConfig(
                question=LocalizedString(de="?", en="?")
            ),
        )
        assert env.type == "comparison"

    def test_APIV1_002_rating_with_rating_config(self):
        env = EvalConfigEnvelope(
            type="rating",
            config=RatingConfig(
                scale=Scale(min=1, max=5, step=1),
                dimensions=[
                    Dimension(
                        id="overall",
                        label=LocalizedString(de="Gesamt", en="Overall"),
                        weight=1.0,
                    )
                ],
            ),
        )
        assert env.type == "rating"

    def test_APIV1_002b_rating_keeps_item_header_template(self):
        """Regression: the v1 API used to silently drop `item_header_template`
        on rating configs because the field only existed on ComparisonConfig.
        Rating scenarios now carry a per-item header just like comparisons."""
        env = EvalConfigEnvelope(
            type="rating",
            config=RatingConfig(
                scale=Scale(min=1, max=5, step=1),
                dimensions=[
                    Dimension(
                        id="overall",
                        label=LocalizedString(de="Gesamt", en="Overall"),
                        weight=1.0,
                    )
                ],
                item_header_template=LocalizedString(
                    de="Fall {{case_id}}", en="Case {{case_id}}"
                ),
            ),
        )
        # Survives validation AND round-trips through model_dump (the exact
        # path _build_config_json uses to persist config_json).
        dumped = env.config.model_dump(mode="json")
        assert dumped["item_header_template"] == {
            "de": "Fall {{case_id}}",
            "en": "Case {{case_id}}",
        }

    def test_APIV1_003_ranking_with_ranking_config(self):
        env = EvalConfigEnvelope(
            type="ranking",
            config=SimpleRankingConfig(
                buckets=[
                    Bucket(
                        id="good",
                        label=LocalizedString(de="Gut", en="Good"),
                        color="#0f0",
                        order=1,
                    )
                ]
            ),
        )
        assert env.type == "ranking"

    def test_APIV1_004_rating_with_ranking_config_rejected(self):
        """The cross-validator catches type/config drift — this is the main
        failure mode users hit when copy-pasting a wizard config without
        updating `type`."""
        with pytest.raises(ValidationError) as exc:
            EvalConfigEnvelope(
                type="rating",
                config=SimpleRankingConfig(
                    buckets=[
                        Bucket(
                            id="g",
                            label=LocalizedString(de="g", en="g"),
                            color="#0f0",
                            order=1,
                        )
                    ]
                ),
            )
        assert "does not match" in str(exc.value)

    def test_APIV1_005_comparison_with_rating_config_rejected(self):
        with pytest.raises(ValidationError):
            EvalConfigEnvelope(
                type="comparison",
                config=RatingConfig(
                    scale=Scale(min=1, max=5, step=1),
                    dimensions=[
                        Dimension(
                            id="d",
                            label=LocalizedString(de="d", en="d"),
                            weight=1.0,
                        )
                    ],
                ),
            )


# ---------------------------------------------------------------------------
# Strict-mode boundary — extra fields at the API contract layer are a typo
# ---------------------------------------------------------------------------


class TestStrictMode:
    def test_APIV1_010_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ScenarioCreateRequest.model_validate(
                {
                    "name": "x",
                    "eval_config": {
                        "type": "comparison",
                        "config": {"question": {"de": "?", "en": "?"}},
                    },
                    "TYPO_FIELD": "should fail",
                }
            )

    def test_APIV1_011_minimal_payload_accepts(self):
        req = ScenarioCreateRequest.model_validate(
            {
                "name": "Minimal",
                "eval_config": {
                    "type": "comparison",
                    "config": {"question": {"de": "?", "en": "?"}},
                },
            }
        )
        assert req.name == "Minimal"
        assert req.assessors == []
        assert req.items is None
        assert req.referral_link is None


# ---------------------------------------------------------------------------
# Items envelope — guard against the historical "features silently dropped"
# regression that bit the Turing-Test pipeline.
# ---------------------------------------------------------------------------


class TestNativeItems:
    def test_APIV1_012_features_round_trip(self):
        env = LlarsNativeEnvelope(
            items=[
                NativeItem(
                    id="x1",
                    label="X1",
                    source=Source(type=SourceType.HUMAN),
                    content="hello",
                    features=[
                        NativeFeature(
                            content="A",
                            generated_by="human",
                        ),
                        NativeFeature(
                            content="B",
                            generated_by="Global/OpenAI/gpt-5-nano",
                        ),
                    ],
                )
            ]
        )
        assert len(env.items[0].features) == 2
        assert env.items[0].features[1].generated_by == (
            "Global/OpenAI/gpt-5-nano"
        )

    def test_APIV1_013_default_feature_type_is_candidate(self):
        f = NativeFeature(content="hi")
        assert f.type == "candidate"
        assert f.generated_by is None


# ---------------------------------------------------------------------------
# Sub-payloads — defaults / enum guards
# ---------------------------------------------------------------------------


class TestAssessorInvite:
    def test_APIV1_014_default_role_is_plain_assessor(self):
        a = AssessorInvite(username="evaluator")
        assert a.manager_role == "none"
        assert a.evaluation_role == "assessor"
        assert a.invitation_status == "accepted"

    def test_APIV1_015_unknown_role_rejected(self):
        with pytest.raises(ValidationError):
            AssessorInvite(username="x", manager_role="superuser")


class TestReferralLinkSpec:
    def test_APIV1_016_defaults(self):
        spec = ReferralLinkSpec(slug="emnlp-pilot")
        assert spec.role_name == "evaluator"
        assert spec.auto_enroll is True
        assert spec.label is None
        assert spec.campaign_name is None
