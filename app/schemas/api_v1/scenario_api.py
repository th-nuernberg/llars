"""
Request / response schemas for `/api/v1/scenarios`.

These are the external contract for the public v1 API. Changes here are
breaking changes for API clients.

Design choices
--------------
- We REUSE the existing config classes from
  `app/schemas/evaluation_data_schemas.py` (RatingConfig, ComparisonConfig,
  SimpleRankingConfig, MultiGroupRankingConfig, AuthenticityConfig,
  LabelingConfig, MailRatingConfig). That way the v1 API is automatically
  consistent with the items ground truth and the wizard, and a config that
  validates here also imports cleanly through the wizard pipeline.
- `extra='forbid'` everywhere so a typo in a client request fails loudly
  (`"sccenarios"`) instead of silently being dropped.
- `EvaluationType` (string enum) is the user-facing type discriminator;
  internally we still use `function_type_id`, but exposing the enum keeps
  callers decoupled from DB ids.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.evaluation_data_schemas import (
    AuthenticityConfig,
    CommunicationComparisonConfig,
    ComparisonConfig,
    ConversationContent,
    ConversationLabelingConfig,
    ConversationLabelingContent,
    EvaluationType,
    LabelingConfig,
    MailRatingConfig,
    MultiGroupRankingConfig,
    RatingConfig,
    Reference,
    SchemaVersion,
    SimpleRankingConfig,
    Source,
)


# Ordered union: more specific shapes (multi-group, mail) first so Pydantic's
# left-to-right discrimination doesn't silently accept the looser variant.
# `CommunicationComparisonConfig` extends `ComparisonConfig` so it must come
# first — otherwise the parent class swallows the extra fields silently.
EvalConfig = Union[
    MultiGroupRankingConfig,
    SimpleRankingConfig,
    MailRatingConfig,
    RatingConfig,
    CommunicationComparisonConfig,
    ComparisonConfig,
    AuthenticityConfig,
    # ConversationLabelingConfig extends LabelingConfig, so it MUST come first
    # for the same reason CommunicationComparisonConfig does above — otherwise
    # the parent swallows it and the context options are silently dropped.
    ConversationLabelingConfig,
    LabelingConfig,
]


class _ApiModel(BaseModel):
    """Shared base: strict field validation for every public schema.

    ``protected_namespaces=()`` silences Pydantic's noisy default warning
    for legitimate field names that begin with ``model_`` (e.g.
    ``model_name`` on the chatbot schemas — that's an LLM model id, not a
    Pydantic-internal field).
    """

    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        protected_namespaces=(),
    )


# ---------------------------------------------------------------------------
# Sub-payloads
# ---------------------------------------------------------------------------


class EvalConfigEnvelope(_ApiModel):
    """
    The function-type + matching config block for a scenario.

    `type` decides which evaluation flow the scenario runs (it maps 1:1 to
    `feature_function_types.function_type_id`); `config` must be the matching
    Pydantic config class for that type. The cross-validator below rejects
    mismatches like `type=ranking` with a `RatingConfig`.
    """

    type: EvaluationType
    config: EvalConfig

    @field_validator("config")
    @classmethod
    def _config_matches_type(cls, v: EvalConfig, info) -> EvalConfig:
        eval_type = info.data.get("type")
        if eval_type is None:
            return v

        # Normalise: when use_enum_values is on and the value comes through
        # already coerced as a string, lift it back to the enum member.
        if isinstance(eval_type, str):
            try:
                eval_type = EvaluationType(eval_type)
            except ValueError:
                return v  # let the type field's own validator surface this

        expected = {
            EvaluationType.RANKING: (SimpleRankingConfig, MultiGroupRankingConfig),
            EvaluationType.RATING: (RatingConfig,),
            EvaluationType.MAIL_RATING: (MailRatingConfig,),
            # CommunicationComparison inherits from ComparisonConfig so either
            # accepts the same shape; the type discriminator is what tells the
            # frontend which interface to mount.
            EvaluationType.COMPARISON: (ComparisonConfig,),
            EvaluationType.COMMUNICATION_COMPARISON: (ComparisonConfig,),
            EvaluationType.AUTHENTICITY: (AuthenticityConfig,),
            EvaluationType.LABELING: (LabelingConfig,),
            # Conversation labeling accepts its own config only — a plain
            # LabelingConfig would mean "no context settings", which for this
            # type is a client mistake worth surfacing rather than defaulting.
            EvaluationType.CONVERSATION_LABELING: (ConversationLabelingConfig,),
        }.get(eval_type)

        if expected and not isinstance(v, expected):
            raise ValueError(
                f"config type {type(v).__name__} does not match "
                f"evaluation type '{eval_type.value}' "
                f"(expected one of: {[c.__name__ for c in expected]})"
            )
        return v


class NativeFeature(_ApiModel):
    """
    One alternative for an Item.

    Maps 1:1 to a `Feature` row (`type` → `FeatureType.name`, `content` →
    `Feature.content`, `generated_by` → `Feature.model_id`). The provenance
    string in `generated_by` is what the comparison stats parser reads, so
    use values like ``human`` / ``Global/OpenAI/gpt-5-nano`` here.
    """

    type: str = "candidate"
    content: str
    generated_by: Optional[str] = None


class NativeItem(_ApiModel):
    """
    One item in an LLARS-Native envelope.

    This is the v1-specific item shape: identical to
    `evaluation_data_schemas.Item` but ALSO carries an optional `features`
    list, because the importer's `_extract_native_features` reads exactly
    that key for ranking / comparison alternatives.

    ``metadata`` is the public-API counterpart of
    ``EvaluationItem.metadata_json`` (introduced by Eric in commit
    6f2acd61). Arbitrary per-item research metadata — channel of the
    underlying counselling encounter (transcript/chat/mail), persona,
    axis, model-family, claim-id — gets persisted and is surfaced to
    the ComparisonInterface for ``{{variable}}`` template substitution
    in ``itemHeaderTemplate`` / ``taskDescriptionMarkdown``.
    """

    id: str
    label: str
    source: Source
    content: Union[str, ConversationLabelingContent, ConversationContent]
    group: Optional[str] = None
    # SECURITY (H1): hard-cap the metadata dict so an API client can't
    # smuggle an enormous JSON blob into the row (every key roundtrips
    # to the frontend and back into the ChromaDB metadata on indexing).
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    # SECURITY (H1): cap features per item. Each NativeFeature becomes one
    # Feature row (and FeatureType lookup), so an unbounded list multiplies
    # the bulk-import cost beyond the items[] cap below.
    features: List[NativeFeature] = Field(default_factory=list, max_length=50)


class LlarsNativeEnvelope(_ApiModel):
    """
    Items payload in LLARS-Native format.

    This is the same shape the wizard accepts (`schema_version`, optional
    `reference`, list of items). Items are imported as `EvaluationItem`s and
    their `features` are persisted as `Feature` rows. The envelope's `type`
    and `config` are intentionally NOT duplicated here — they come from the
    parent `EvalConfigEnvelope` to avoid the two getting out of sync.
    """

    schema_version: SchemaVersion = SchemaVersion.V1_0
    reference: Optional[Reference] = None
    # SECURITY (H1): cap bulk imports. Without this an API client can POST
    # 10000+ items in one transaction, writing 10000 EvaluationItem +
    # 10000 Message rows and locking the DB on a single transaction. 500
    # is a comfortable headroom over realistic study sizes; if a user
    # genuinely needs more, they should chunk via /scenarios/<id>/items.
    items: List[NativeItem] = Field(default_factory=list, max_length=500)
    # Scenario parts (labeling phases): target part for the items in THIS
    # envelope. REQUIRED on POST /scenarios/<id>/items when the scenario has
    # resolved parts (partition invariant — no silent unassigned items);
    # ignored on the one-shot create, where assignment comes from the parts
    # config itself (item_ids / size specs).
    part_id: Optional[str] = Field(default=None, max_length=100)


class AssessorInvite(_ApiModel):
    """
    One row to create in `scenario_users` when the scenario is created.

    `manager_role` and `evaluation_role` follow the new 2-axis model
    (`ScenarioUsers.manager_role` / `evaluation_role`). Default is "no
    manager access, can submit evaluations" — i.e. a plain assessor.
    """

    username: str
    manager_role: str = Field(default="none", pattern="^(owner|editor|viewer|none)$")
    evaluation_role: str = Field(default="assessor", pattern="^(assessor|viewer|none)$")
    # Pre-set the invitation as accepted by default so API clients don't need
    # a second round-trip; pass "pending" if they want manual accept.
    invitation_status: str = Field(
        default="accepted", pattern="^(accepted|rejected|pending)$"
    )


class ReferralLinkSpec(_ApiModel):
    """
    Optional referral link to (re)point at the new scenario.

    If `slug` already exists, we PATCH it (label + target_scenario_id);
    otherwise we create a new link in the campaign named by
    `campaign_name`. This is the single mechanism external clients use to
    keep a study URL stable across re-seedings.
    """

    slug: str = Field(min_length=2, max_length=100)
    label: Optional[str] = Field(default=None, max_length=255)
    # SECURITY (C1): restrict role_name to scenario-side roles ONLY.
    # Without this regex an API client can pass `"admin"` here and the
    # ReferralRegistration flow will promote anyone who joins via the link
    # straight to global admin — a critical privilege escalation. Keep this
    # whitelist in sync with the scenario-membership role enum.
    role_name: str = Field(default="evaluator", pattern="^(evaluator|assessor|viewer)$")
    campaign_name: Optional[str] = Field(default=None, max_length=255)
    auto_enroll: bool = True
    # Registration-form toggles surfaced to the frontend via
    # `/api/referral/validate/<slug>`. Defaults TRUE so a re-sync without
    # an explicit value keeps the existing field configuration.
    collect_email: bool = True
    collect_display_name: bool = True
    # When `collect_email` is TRUE, whether the email field is optional
    # (shown but skippable). Default FALSE keeps the field required.
    collect_email_optional: bool = False


# ---------------------------------------------------------------------------
# Top-level requests
# ---------------------------------------------------------------------------


class ScenarioCreateRequest(_ApiModel):
    """
    One-shot scenario creation: scenario row + items + assessors + ref-link
    in a single POST. Anything optional (items, assessors, referral_link)
    can be omitted and added later via the dedicated sub-resource routes.
    """

    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    eval_config: EvalConfigEnvelope
    items: Optional[LlarsNativeEnvelope] = None
    # SECURITY (H1): cap assessor invites per request — same DoS class as
    # bulk-imports above (each invite is a User lookup + ScenarioUsers row).
    assessors: List[AssessorInvite] = Field(default_factory=list, max_length=200)
    referral_link: Optional[ReferralLinkSpec] = None

    # Comparison-only: pinning the model pair on the scenario row so the
    # assessor UI labels matches.
    llm1_model: Optional[str] = Field(default=None, max_length=255)
    llm2_model: Optional[str] = Field(default=None, max_length=255)

    # Evaluation window. Optional: when omitted the service defaults to
    # ``begin = now`` and ``end = now + 3 weeks`` so the EvaluationHub
    # status-derivation marks the scenario as actively collecting
    # evaluations (`evaluating`). API clients running longer studies
    # should pass an explicit ``end`` further in the future.
    begin: Optional[datetime] = None
    end: Optional[datetime] = None

    archived: bool = False

    @field_validator("end")
    @classmethod
    def _end_after_begin(cls, end_value, info):
        begin_value = info.data.get("begin")
        if begin_value is not None and end_value is not None and end_value <= begin_value:
            raise ValueError("`end` must be after `begin`")
        return end_value


class ScenarioPatchRequest(_ApiModel):
    """Partial update of an existing scenario row.

    None == "do not touch this field"; pass an explicit value to overwrite.
    `eval_config` is intentionally NOT patchable here — changing function
    type after items already exist breaks evaluations, so callers have to
    delete and re-create instead.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    archived: Optional[bool] = None
    llm1_model: Optional[str] = Field(default=None, max_length=255)
    llm2_model: Optional[str] = Field(default=None, max_length=255)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class AssessorResponse(_ApiModel):
    user_id: int
    username: str
    manager_role: str
    evaluation_role: str
    invitation_status: str


class ReferralLinkResponse(_ApiModel):
    id: int
    slug: Optional[str]
    code: str
    label: Optional[str]
    role_name: str
    target_scenario_id: Optional[int]
    is_active: bool


class ItemImportResponse(_ApiModel):
    """Returned both by the one-shot create and the bulk-import endpoint."""

    items_created: int
    item_ids: List[int]
    features_created: int
    skipped: int = 0


class ScenarioResponse(_ApiModel):
    id: int
    name: str
    description: Optional[str]
    function_type_id: int
    evaluation_type: EvaluationType
    created_by: Optional[str]
    config_json: Dict[str, Any]
    item_count: int
    assessor_count: int
    archived: bool
    created_at: Optional[str]
    llm1_model: Optional[str] = None
    llm2_model: Optional[str] = None
    referral_link: Optional[ReferralLinkResponse] = None
    items_imported: Optional[ItemImportResponse] = None
