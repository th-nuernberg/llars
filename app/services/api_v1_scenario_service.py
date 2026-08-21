"""
Service orchestrator for the public LLARS v1 scenario API.

Scope
-----
Translates a validated ``ScenarioCreateRequest`` (Pydantic) into the
underlying DB rows needed for a complete, useable scenario:

    RatingScenarios   (the scenario row + config_json)
        ├── ScenarioItems → EvaluationItem + Message + Feature   (items[] payload)
        ├── ScenarioUsers (one row per assessor; owner gets manager_role='owner')
        └── ReferralLink.target_scenario_id (optional)

Why not reuse the wizard?
-------------------------
The wizard pipeline (`ScenarioWizardService.create_scenario`) goes through
``ImportService.create_session_from_data → transform_with_ai → execute_import``.
That path is built around format auto-detection and AI-guided field mapping,
which we don't need here — v1 callers send already-validated Pydantic items in
LLARS-Native shape, so we write to the DB directly. This keeps the contract
deterministic (no fuzzy matching) and avoids dragging the AI analyser into the
hot path of an external API call.

Concurrency
-----------
The orchestrator does the entire create in one transaction (single
``db.session.commit()`` at the end). On error we ``rollback()`` so the caller
never sees a half-built scenario — matters because the v1 API is meant to be
idempotent at the slug level (re-POST a referral link with the same slug).
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta

# Default evaluation window for new scenarios when the API caller doesn't
# provide explicit dates. Three weeks is the sweet spot for student/rater
# studies — long enough to absorb holidays, short enough that the
# EvaluationHub doesn't keep stale scenarios visible forever. Override by
# passing `begin` / `end` in the create payload.
_DEFAULT_EVAL_WINDOW = timedelta(weeks=3)
from typing import List, Optional, Tuple

from db import db
from db.models import (
    EvaluationItem,
    Feature,
    FeatureType,
    Message,
    RatingScenarios,
    ReferralCampaign,
    ScenarioItems,
    ScenarioUsers,
    User,
)
from db.models.scenario import (
    InvitationStatus,
    ManagerRole,
    MembershipStatus,
    ScenarioRoles,
)
from schemas.api_v1.scenario_api import (
    AssessorInvite,
    LlarsNativeEnvelope,
    NativeFeature,
    NativeItem,
    ReferralLinkSpec,
    ScenarioCreateRequest,
)
from services.evaluation.labeling_types import (
    CONVERSATION_LABELING_FUNCTION_TYPE_ID,
)
from schemas.evaluation_data_schemas import (
    ConversationContent,
    ConversationLabelingContent,
    EvaluationType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type → function_type_id mapping (mirrors EvaluationType.to_function_type_id)
# Kept as a local table because the v1 service is a strict boundary; if we
# ever rename the enum the API contract should fail loudly here, not silently.
# ---------------------------------------------------------------------------
_TYPE_TO_FUNCTION_ID = {
    EvaluationType.RANKING: 1,
    EvaluationType.RATING: 2,
    EvaluationType.MAIL_RATING: 3,
    EvaluationType.COMPARISON: 4,
    EvaluationType.AUTHENTICITY: 5,
    EvaluationType.LABELING: 7,
    EvaluationType.COMMUNICATION_COMPARISON: 8,
    EvaluationType.CONVERSATION_LABELING: 9,
}


class ApiV1Error(Exception):
    """Raised on validation/business-rule failures inside the orchestrator.

    The route layer catches this and turns it into a 400 / 409. We don't reach
    for `ValidationError` from `decorators.error_handler` here because the
    service is tested in isolation and shouldn't depend on the Flask error
    machinery."""


class ApiV1NotFound(ApiV1Error):
    """Raised when a referenced entity (user, scenario, link) doesn't exist."""


# ===========================================================================
# Public entrypoint
# ===========================================================================


def create_scenario_one_shot(
    payload: ScenarioCreateRequest,
    requesting_username: str,
) -> RatingScenarios:
    """
    Create a scenario + items + assessors + (optional) referral link in a
    single transaction.

    The owner is the requesting user — i.e. the API key's owner. They are
    auto-added with ``manager_role='owner'`` so they can manage the scenario
    afterwards via either the v1 API or the regular UI.
    """
    eval_type = _coerce_eval_type(payload.eval_config.type)
    function_type_id = _TYPE_TO_FUNCTION_ID[eval_type]

    config_json = _build_config_json(payload)

    # Labeling co-pilot: stamp hidden-control salt + prompt version 1 so
    # v1-API-created scenarios behave identically to wizard-created ones.
    from services.evaluation.labeling_copilot_service import LabelingCopilotService
    config_json = LabelingCopilotService.normalize_config_on_write(config_json)

    # Scenario parts (labeling phases): normalize ids/flags up front and
    # require the items in the SAME request — the size/external-id specs are
    # resolved into internal item ids in this very transaction, so a
    # parts-enabled scenario can never exist in a half-assigned state.
    from services.evaluation.scenario_parts_service import (
        PartsConfigError,
        ScenarioPartsService,
    )
    try:
        config_json = ScenarioPartsService.normalize_config_on_write(config_json)
    except PartsConfigError as exc:
        raise ApiV1Error(str(exc))
    if ScenarioPartsService.get_parts_config(config_json) and not (
        payload.items and payload.items.items
    ):
        raise ApiV1Error(
            "parts.enabled requires the items in the same create request "
            "(part specs are resolved against the imported items)"
        )

    # The `RatingScenarios` model defaults both `begin` and `end` to
    # `datetime.utcnow`, which would make the status-derivation logic in
    # `_serialize_scenario` flip to "completed" one second after creation
    # and hide the scenario from every non-owner in the EvaluationHub.
    # Always set an explicit window: caller-provided values win,
    # otherwise default to a 3-week evaluation window starting now.
    now = datetime.utcnow()
    begin_value = payload.begin if payload.begin is not None else now
    end_value = payload.end if payload.end is not None else (begin_value + _DEFAULT_EVAL_WINDOW)

    try:
        scenario = RatingScenarios(
            scenario_name=payload.name,
            function_type_id=function_type_id,
            created_by=requesting_username,
            config_json=config_json,
            llm1_model=payload.llm1_model,
            llm2_model=payload.llm2_model,
            begin=begin_value,
            end=end_value,
        )
        db.session.add(scenario)
        db.session.flush()  # need scenario.id for the dependent rows below

        items_imported = (0, 0)
        if payload.items and payload.items.items:
            items_imported = _import_native_items(
                scenario, payload.items, function_type_id
            )

        # Resolve parts specs (size / external ids) against the just-imported
        # items — same transaction, so create either yields a fully
        # partitioned scenario or fails as a whole.
        try:
            ScenarioPartsService.resolve_specs(scenario)
        except PartsConfigError as exc:
            raise ApiV1Error(f"parts: {exc}")

        _assign_owner(scenario, requesting_username)
        _assign_assessors(scenario, payload.assessors, requesting_username)

        if payload.referral_link is not None:
            _sync_referral_link(scenario, payload.referral_link, requesting_username)

        db.session.commit()
        logger.info(
            "[api_v1] Created scenario %s (id=%s) with %s items, %s features, "
            "%s assessors",
            payload.name,
            scenario.id,
            items_imported[0],
            items_imported[1],
            len(payload.assessors),
        )
        # Stash the import counts on the scenario object so the route layer
        # can lift them into the response without a second query.
        scenario._api_v1_items_imported = items_imported  # type: ignore[attr-defined]

        # Auto-start co-pilot suggestion generation (mirrors the wizard path).
        if LabelingCopilotService.get_copilot_config(scenario):
            LabelingCopilotService.start_generation(scenario, clear_errors=False)

        return scenario
    except Exception:
        db.session.rollback()
        raise


# ===========================================================================
# Helpers
# ===========================================================================


def _coerce_eval_type(value) -> EvaluationType:
    """Lift an enum-or-string back to a real EvaluationType member.

    `EvalConfigEnvelope` has `use_enum_values=True` (set on `_ApiModel`), so
    by the time we see it the value is the raw string. The to-function-id
    map is keyed on enum members, so we coerce here.
    """
    if isinstance(value, EvaluationType):
        return value
    return EvaluationType(value)


def _build_config_json(payload: ScenarioCreateRequest) -> dict:
    """Persist the config block + descriptive metadata on the scenario row.

    We store the full Pydantic config plus a few extras (description,
    archived flag, schema_version) so the rest of LLARS — which already
    reads ``config_json`` — sees a self-describing object.

    Compatibility surface (kept deliberately wide so v1-API-created
    scenarios behave identically to wizard-created ones):
      - ``config.*``                — original v1 placement
      - ``eval_config.config.*``    — wizard placement; the comparison
        evaluation page reads gamification_* and several other fields
        from this exact path (``EvaluationItemsOverview.vue:280``)
      - top-level hoists for the keys frontend services peek at without
        walking the nested object: dimensions/buckets/labels/scale/groups
        (legacy) plus the gamification trio so milestone trophies show up
        on the overview grid for v1-imported comparison scenarios
    """
    type_value = _coerce_eval_type(payload.eval_config.type).value
    cfg = payload.eval_config.config.model_dump(mode="json")

    # Top-level hoists: the keys here are read by services that don't know
    # about the wizard's `eval_config.config.*` nesting.
    hoist_keys = (
        "dimensions",
        "buckets",
        "labels",
        "scale",
        "groups",
        # Comparison gamification — frontend's read-path falls back to
        # top-level when `eval_config.config` is missing, so hoisting these
        # makes v1 + wizard configs interchangeable.
        "gamification_enabled",
        "gamification_first_milestone",
        "gamification_recurring_milestone",
        "progressive_reveal",
        "allow_tie",
        "show_source",
    )

    out = {
        "type": type_value,
        "config": cfg,
        # Mirror the wizard-style nesting so the comparison evaluation
        # page's primary read-path (`config_json.eval_config.config.*`)
        # finds gamification + tie/source flags without duplication elsewhere.
        "eval_config": {
            "type": type_value,
            "config": cfg,
        },
        **{k: cfg[k] for k in hoist_keys if k in cfg},
        "description": payload.description,
        "archived": payload.archived,
        "source": "api_v1",
        "schema_version": "1.0",
    }
    return out


def _generate_chat_id(item_id: str) -> int:
    """Mirror ImportService._generate_chat_id so v1-imported items collide
    with wizard-imported items only when the user IDs actually match —
    keeps the existing dedup invariant working for downstream consumers."""
    h = int(hashlib.md5(item_id.encode()).hexdigest()[:8], 16)
    return h % 2147483647


def _ensure_feature_type(name: str, cache: dict[str, FeatureType]) -> FeatureType:
    """Look up or create a FeatureType row, with per-import cache to avoid
    one round-trip per feature."""
    if name in cache:
        return cache[name]
    ft = FeatureType.query.filter_by(name=name).first()
    if not ft:
        ft = FeatureType(name=name)
        db.session.add(ft)
        db.session.flush()
    cache[name] = ft
    return ft


def _import_native_items(
    scenario: RatingScenarios,
    envelope: LlarsNativeEnvelope,
    function_type_id: int,
) -> Tuple[int, int]:
    """
    Persist the LLARS-Native items into EvaluationItem + Message + Feature
    rows and link them to ``scenario`` via ScenarioItems.

    Returns ``(items_created, features_created)`` for the response.
    """
    type_cache: dict[str, FeatureType] = {}
    items_created = 0
    features_created = 0

    expects_spans = function_type_id == CONVERSATION_LABELING_FUNCTION_TYPE_ID

    for native in envelope.items:
        # Fail loudly rather than importing a conversation-labeling scenario
        # whose items carry nothing to label — that would only surface later as
        # an empty rater screen with no indication of what went wrong.
        if expects_spans and not isinstance(native.content, ConversationLabelingContent):
            raise ApiV1Error(
                f"item '{native.id}': conversation_labeling scenarios require "
                f"content.type = 'conversation_labeling' with spans"
            )

        chat_id = _generate_chat_id(native.id)
        if native.source:
            # source.type may still be the SourceType ENUM here — take .value,
            # otherwise str() leaks "SourceType.HUMAN" into Message.sender and
            # the rater UI shows the raw Python enum text.
            source_type = getattr(native.source.type, "value", native.source.type)
            sender = native.source.name or source_type
        else:
            sender = "system"

        item = EvaluationItem(
            chat_id=chat_id,
            institut_id=scenario.id,  # use scenario id as institut bucket so
                                      # items from different v1 scenarios
                                      # don't collide on the unique
                                      # (chat_id, institut_id, function_type)
                                      # constraint.
            subject=native.label,
            sender=str(sender),
            function_type_id=function_type_id,
            # Eric's metadata_json column (commit 6f2acd61). Arbitrary
            # research metadata (channel, persona, axis, model-family,
            # claim-id, …) gets persisted here so ComparisonInterface
            # can substitute {{variable}} placeholders in the
            # itemHeaderTemplate / taskDescriptionMarkdown per item.
            metadata_json=native.metadata if native.metadata else None,
        )
        db.session.add(item)
        db.session.flush()  # need item_id for messages + features

        _persist_content(item, native, sender)
        features_created += _persist_features(item, native.features, type_cache)

        db.session.add(ScenarioItems(scenario_id=scenario.id, item_id=item.item_id))
        items_created += 1

    return items_created, features_created


# Reserved key under EvaluationItem.metadata_json that carries the span index
# of a conversation-labeling item. Namespaced so it can never collide with the
# study's own research metadata (channel, persona, axis, …), which lives in the
# same JSON blob and must survive untouched.
CONVERSATION_LABELING_META_KEY = "conversation_labeling"


def _persist_conversation_labeling(
    item: EvaluationItem, content: ConversationLabelingContent
) -> int:
    """Write the conversation as Message rows + index its spans on the item.

    The message text is stored EXACTLY ONCE (as a Message row); spans only
    reference character offsets into it. Duplicating the text per span would
    turn ~1 MB of study data into ~100 MB at the sizes this type is built for
    (8.307 spans over 86 conversations).

    The span index goes into ``metadata_json`` rather than its own table: spans
    are immutable import artefacts (the unitizing is frozen and deliberately
    not editable in the UI), there is no write path and no query against a
    single span — only ever "all spans of this item". A JSON array is cheaper
    than a join and saves a second migration.

    ``message_index`` is the join key to the rendered message list;
    ``message_id`` is the importer's own id, carried along because the export
    has to report it.

    Returns the number of spans indexed.
    """
    spans: List[dict] = []
    labelable_indexes: List[int] = []

    for idx, msg in enumerate(content.messages):
        db.session.add(
            Message(
                item_id=item.item_id,
                sender=msg.role,
                content=msg.content,
                timestamp=_parse_timestamp(msg.timestamp),
                generated_by="Human",
            )
        )
        if msg.labelable:
            labelable_indexes.append(idx)
        for span_idx, span in enumerate(msg.spans):
            spans.append(
                {
                    "span_id": span.span_id,
                    "message_index": idx,
                    "message_id": msg.message_id if msg.message_id is not None else idx + 1,
                    "span_index": span_idx,
                    "start": span.start,
                    "end": span.end,
                }
            )

    # Reassign instead of mutating: SQLAlchemy does not track in-place changes
    # to a JSON column, so an .update() on the existing dict would never be
    # written back.
    meta = dict(item.metadata_json or {})
    meta[CONVERSATION_LABELING_META_KEY] = {
        "spans": spans,
        "labelable_messages": labelable_indexes,
    }
    item.metadata_json = meta

    return len(spans)


def _persist_content(item: EvaluationItem, native: NativeItem, sender: str) -> None:
    """Materialise an Item's content block.

    A ConversationLabelingContent becomes Message rows plus a span index on the
    item (see _persist_conversation_labeling). A ConversationContent becomes one
    Message row per turn. A plain string is left only on
    `EvaluationItem.subject` (which already holds the label) plus a single
    Message so the evaluator UI has something to render — keeps
    comparison/rating/labeling flows that read messages consistent with
    wizard-imported items.
    """
    if isinstance(native.content, ConversationLabelingContent):
        _persist_conversation_labeling(item, native.content)
        return

    if isinstance(native.content, ConversationContent):
        for idx, msg in enumerate(native.content.messages):
            db.session.add(
                Message(
                    item_id=item.item_id,
                    sender=msg.role,
                    content=msg.content,
                    timestamp=_parse_timestamp(msg.timestamp),
                    generated_by="Human",
                )
            )
        return

    # Plain string content: keep both label (already on .subject) and a
    # single message so UIs that paginate over messages still work.
    if native.content:
        db.session.add(
            Message(
                item_id=item.item_id,
                sender=str(sender),
                content=str(native.content),
                timestamp=datetime.utcnow(),
                generated_by="Human",
            )
        )


def _persist_features(
    item: EvaluationItem,
    features: List[NativeFeature],
    type_cache: dict[str, FeatureType],
) -> int:
    """Write each NativeFeature as one Feature row. Returns count for stats."""
    count = 0
    for feat in features:
        ft = _ensure_feature_type(feat.type, type_cache)
        db.session.add(
            Feature(
                item_id=item.item_id,
                type_id=ft.type_id,
                model_id=feat.generated_by,
                content=feat.content,
            )
        )
        count += 1
    return count


def _parse_timestamp(raw: Optional[str]) -> datetime:
    """Best-effort ISO-8601 parsing; falls back to now() so DB NOT NULL holds."""
    if not raw:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return datetime.utcnow()


# ---------------------------------------------------------------------------
# Assessor / owner assignment
# ---------------------------------------------------------------------------


def _assign_owner(scenario: RatingScenarios, owner_username: str) -> None:
    """The API key owner becomes scenario owner with full management rights."""
    user = User.query.filter_by(username=owner_username).first()
    if not user:
        # Should never happen — the requesting user is already authenticated
        # against the User table by the time we reach here.
        raise ApiV1Error(f"Authenticated user '{owner_username}' not found in DB")

    db.session.add(
        ScenarioUsers(
            scenario_id=scenario.id,
            user_id=user.id,
            role=ScenarioRoles.OWNER,
            access_level="OWNER",
            manager_role=ManagerRole.OWNER.value,
            evaluation_role="none",
            invitation_status=InvitationStatus.ACCEPTED,
            membership_status=MembershipStatus.ACTIVE,
            invited_at=datetime.utcnow(),
            invited_by=owner_username,
        )
    )


def _assign_assessors(
    scenario: RatingScenarios,
    invites: List[AssessorInvite],
    invited_by: str,
) -> None:
    """Bulk-create ScenarioUsers rows for the invited assessors.

    Skips the owner (already added by `_assign_owner`) so a caller can list
    themselves in `assessors` without producing a unique-constraint error.
    Unknown usernames raise ApiV1NotFound — partial failure would leave the
    scenario in a half-built state, and the route layer surfaces this as a
    422 with the failing username.
    """
    seen: set[int] = set()
    for invite in invites:
        if invite.username == invited_by:
            continue  # already added as owner
        user = User.query.filter_by(username=invite.username).first()
        if not user:
            raise ApiV1NotFound(f"User '{invite.username}' not found")
        if user.id in seen:
            continue
        seen.add(user.id)

        db.session.add(
            ScenarioUsers(
                scenario_id=scenario.id,
                user_id=user.id,
                role=ScenarioRoles.EVALUATOR,
                access_level="MEMBER",
                manager_role=invite.manager_role,
                evaluation_role=invite.evaluation_role,
                is_assessor=invite.evaluation_role == "assessor",
                is_viewer=invite.evaluation_role == "viewer",
                invitation_status=InvitationStatus(invite.invitation_status),
                membership_status=MembershipStatus.ACTIVE,
                invited_at=datetime.utcnow(),
                invited_by=invited_by,
            )
        )


# ---------------------------------------------------------------------------
# Referral link
# ---------------------------------------------------------------------------


def _sync_referral_link(
    scenario: RatingScenarios,
    spec: ReferralLinkSpec,
    requesting_username: str,
):
    """Make the slug point at this scenario.

    Behaviour:
        - slug exists  → patch label / role / target_scenario_id (idempotent)
        - slug missing → ensure a campaign exists (find by name, else create
          a campaign owned by the requester), then create a new link
    """
    from services.referral_service import ReferralService
    from services.permission_service import PermissionService

    existing = ReferralService.get_link_by_slug(spec.slug)
    if existing:
        # SECURITY (C2): slug-squatting guard.
        # Without this check any user holding `scenario:write` could re-target
        # someone else's slug at their own scenario (and rewrite label /
        # role_name in the process). We allow re-syncing only when the
        # requester is either the original creator OR a global admin.
        if (
            existing.created_by != requesting_username
            and not PermissionService.user_has_role(requesting_username, "admin")
        ):
            raise ApiV1Error(
                f"Slug '{spec.slug}' is owned by another user"
            )

        target = scenario.id if spec.auto_enroll else None
        ReferralService.update_link(
            existing.id,
            role_name=spec.role_name,
            label=spec.label,
            target_scenario_id=target,
            collect_email=spec.collect_email,
            collect_display_name=spec.collect_display_name,
            collect_email_optional=spec.collect_email_optional,
        )
        return existing

    # No link yet — pick / create a campaign and add a fresh link to it.
    campaign = _ensure_campaign(spec.campaign_name, requesting_username)
    return ReferralService.create_link(
        campaign_id=campaign.id,
        created_by=requesting_username,
        role_name=spec.role_name,
        slug=spec.slug,
        label=spec.label,
        target_scenario_id=scenario.id if spec.auto_enroll else None,
        collect_email=spec.collect_email,
        collect_display_name=spec.collect_display_name,
        collect_email_optional=spec.collect_email_optional,
    )


def _ensure_campaign(
    campaign_name: Optional[str],
    requesting_username: str,
) -> ReferralCampaign:
    """Look up a campaign by name (case-insensitive); fall back to creating
    one named after the requester if the caller didn't pass `campaign_name`.

    We don't expose campaign management on v1 yet — this is a "JIT" so a
    minimal client can do everything via `POST /api/v1/scenarios` without
    needing to know the campaign concept exists.
    """
    name = (campaign_name or f"{requesting_username}'s API Campaign").strip()
    existing = (
        ReferralCampaign.query
        .filter(db.func.lower(ReferralCampaign.name) == name.lower())
        .first()
    )
    if existing:
        return existing

    campaign = ReferralCampaign(
        name=name,
        description=f"Auto-created by {requesting_username} via /api/v1",
        status="active",
        created_by=requesting_username,
    )
    db.session.add(campaign)
    db.session.flush()
    return campaign
