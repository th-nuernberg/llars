"""
Results export service for the public ``/api/v1/scenarios/{id}/results`` API.

Goals
-----
Produce a defensible, complete per-vote audit trail for any of LLARS's six
evaluation types in a single, stable schema. One row per vote event — never
pivoted summaries — so external tooling (R, pandas, statistical packages)
can ingest the file without guessing at column semantics.

Why a separate service
----------------------
The legacy ``GET /api/scenarios/{id}/export`` route in ``scenario_manager_api``
mixes per-type row shapes (``ranking_value`` for one type, ``rating`` for
another, ``vote`` for a third) and silently drops human votes for the
function types that have no ``elif`` branch. Rather than further bolting
onto that route, the v1 API gets a long-format export with a stable
columns list that works across types.

Stable columns
--------------
Every row carries: ``scenario_id``, ``function_type``, ``item_id``,
``item_label``, ``voter_kind`` (``human``/``llm``), ``voter_id``,
``voter_username``, ``model_id``, ``vote_type``, ``vote_value_str``,
``vote_value_num``, ``feature_id`` (where applicable), ``dimension_id``
(rating only), ``payload_json`` (raw for debug), ``status``,
``created_at``, ``updated_at``.

The headline IRR block (Krippendorff α, Cohen's κ, Fleiss' κ, percent
agreement, Kendall W) is bundled in the response envelope under
``metrics`` — same numbers the Evaluation tab shows, sourced from
``AgreementMetricsService`` so there's a single place where the math
lives.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from db import db
from db.models import (
    EvaluationItem,
    Feature,
    ItemDimensionRating,
    LLMTaskResult,
    RatingScenarios,
    ScenarioItems,
    ScenarioUsers,
    User,
    UserAuthenticityVote,
    UserConsultingCategorySelection,
    UserFeatureRanking,
    UserMailHistoryRating,
)
from db.models.scenario import ItemComparisonEvaluation, ItemLabelingEvaluation

logger = logging.getLogger(__name__)


_FUNCTION_TYPE_NAME = {
    1: "ranking",
    2: "rating",
    3: "mail_rating",
    4: "comparison",
    5: "authenticity",
    7: "labeling",
    9: "conversation_labeling",
    # communication_comparison shares comparison's data layout (single
    # A/B choice + optional notes), so results export iterates the same
    # ItemComparisonEvaluation rows. The discriminator only flips which
    # rater interface gets mounted in the frontend.
    8: "communication_comparison",
}


# ---------------------------------------------------------------------------
# Citation block (JSON envelopes only)
# ---------------------------------------------------------------------------
#
# LLARS is licensed under the PolyForm Noncommercial License 1.0.0 with an
# additional citation requirement: academic work that uses LLARS — or data
# produced with it — must cite the LLARS paper. Shipping the reference inside
# every JSON export means a researcher who only ever sees the exported file
# still has the citation at hand.
#
# Deliberately NOT added to CSV/JSONL exports: a comment/preamble line would
# break strict CSV parsers (pandas.read_csv, R read.csv) and JSONL consumers
# that expect one homogeneous record per line.
#
# Single source of truth — also consumed by the v1 API route
# (app/routes/api_v1/scenario_results_routes.py) and the GUI export route
# (app/routes/scenarios/scenario_manager_api.py). Keep in sync with the root
# CITATION.cff / README.md when the paper reference is updated.
#
# Stand 2026-09: die Proceedings-Version (IJCAI-26 Demo Track,
# doi:10.24963/ijcai.2026/995) ersetzt den arXiv-Preprint als Zitat. Der
# Preprint bleibt in CITATION.cff als identifier erhalten, taucht hier aber
# nicht mehr auf — wer einen Export zitiert, soll die publizierte Fassung
# nennen.
CITATION_BLOCK = {
    "message": (
        "If you use data produced with LLARS in academic work, "
        "please cite the LLARS paper."
    ),
    "paper": (
        "Steigerwald et al. (2026). LLARS: Enabling Domain Expert & Developer "
        "Collaboration for LLM Prompting, Generation and Evaluation. "
        "In Proceedings of IJCAI-26 (Demo Track), pages 8526-8529. "
        "doi:10.24963/ijcai.2026/995"
    ),
    "doi": "10.24963/ijcai.2026/995",
    "url": "https://doi.org/10.24963/ijcai.2026/995",
    "bibtex_url": "https://github.com/th-nuernberg/llars/blob/main/CITATION.cff",
}


def citation_block() -> Dict[str, str]:
    """Return a fresh copy of :data:`CITATION_BLOCK`.

    Callers embed the result in a JSON response envelope; handing out a copy
    stops an accidental downstream mutation from poisoning the module-level
    constant for every subsequent export in the same worker process.
    """
    return dict(CITATION_BLOCK)


# ---------------------------------------------------------------------------
# Stable column ordering (CSV header / row keys)
# ---------------------------------------------------------------------------

ROW_COLUMNS = [
    "scenario_id",
    "function_type",
    "item_id",
    "item_label",
    # Scenario parts (labeling phases): part id the item belongs to — the
    # audit column that lets IRR be computed per calibration phase. None for
    # scenarios without (resolved) parts.
    "part",
    "voter_kind",
    "voter_id",
    "voter_username",
    # Where the human voter came from. ``voter_origin`` = how they joined LLARS
    # ("referral" via an invite link vs "existing" account manually added);
    # ``voter_source`` = the referral link they arrived through (label/slug), or
    # the campaign — empty for existing accounts and LLM voters. Mirrors the
    # team view's per-member origin so exports carry the same provenance.
    "voter_origin",
    "voter_source",
    "model_id",
    "feature_id",
    "dimension_id",
    "vote_type",
    "vote_value_str",
    "vote_value_num",
    "status",
    # Labeling co-pilot study columns (labeling rows only, from
    # LabelingCopilotLog). copilot_shown=False marks the hidden control
    # subset — the flag is export-only and never reaches raters.
    "copilot_shown",
    "copilot_suggested_label",
    "copilot_suggested_label_2",
    "copilot_accepted",
    "copilot_accepted_any",
    "copilot_helpful",
    "copilot_model",
    "copilot_prompt_version",
    # Per-case rater timing. ``time_on_item_ms`` = client-measured time from
    # item display to first save (all types; populated from EvaluationItemTiming,
    # falling back to the labeling co-pilot log). ``time_since_prev_ms`` = a
    # DERIVED fallback: the gap between this voter's consecutive item timestamps
    # (created_at), so studies that predate real timing capture still get an
    # approximate per-case duration. Caveats: the first case per voter is null
    # (no predecessor) and idle gaps/breaks inflate the value — it is raw, not
    # gap-filtered. Prefer ``time_on_item_ms`` when present.
    "time_on_item_ms",
    "time_since_prev_ms",
    "created_at",
    "updated_at",
    # Conversation labeling (function_type 9): one row = one SPAN decision, so
    # the item id alone no longer identifies a case. ``span_id`` is the join key
    # back to the imported unitizing; ``message_id``/``span_index`` let an
    # analysis reconstruct turn order without re-reading the item payload.
    # Appended at the END on purpose — the column order is asserted
    # (APIV1_RES_001) and every other type keeps these empty.
    "span_id",
    "message_id",
    "span_index",
    # Free-text the rater wrote alongside their judgement. Every type stores it
    # under its own name (comparison `notes`, labeling/rating `feedback`,
    # authenticity `notes`), and NONE of them reached the v1 export — a
    # borderline-case remark or a rationale was collected in the interface and
    # then silently dropped on the way out. One column, filled per type.
    "notes",
]


def _row(**kw) -> Dict[str, Any]:
    """Stable dict with all known columns; missing values default to None.

    Keeps every row's shape identical so CSV writers don't dance around
    sparse keys."""
    out = {k: None for k in ROW_COLUMNS}
    out.update(kw)
    return out


def _to_iso(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return value.isoformat()
    except AttributeError:
        return None


def _resolve_voter_origins(usernames: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """Map each username to where they came from, mirroring the scenario team
    view's ``origin`` (see ``_resolve_source_links`` in scenario_manager_api).

    Returns ``{username: {'account': 'referral'|'existing', 'source': str|None}}``.
    A user with a ``ReferralRegistration`` arrived through an invite link
    (``account='referral'``, ``source`` = link label/slug or campaign); no
    registration means a pre-existing/manually-added account (``'existing'``,
    no source). Batched (two queries) to avoid N+1 over the voter set.

    Kept self-contained here (instead of importing the route helper) to avoid a
    service→route import cycle; the shape is intentionally narrower (export only
    needs account + a human-readable source label).
    """
    names = {u for u in usernames if u}
    origins: Dict[str, Dict[str, Any]] = {
        u: {"account": "existing", "source": None} for u in names
    }
    if not names:
        return origins

    from db.models.referral import ReferralRegistration, ReferralLink

    registrations = ReferralRegistration.query.filter(
        ReferralRegistration.username.in_(list(names))
    ).all()
    link_ids = {r.link_id for r in registrations if r.link_id is not None}
    links_by_id = {
        link.id: link
        for link in ReferralLink.query.filter(ReferralLink.id.in_(link_ids)).all()
    } if link_ids else {}

    for reg in registrations:
        link = links_by_id.get(reg.link_id) if reg.link_id is not None else None
        if link is None:
            continue
        campaign_name = link.campaign.name if link.campaign else None
        origins[reg.username] = {
            "account": "referral",
            # Prefer the link's own label; fall back to the campaign, then slug,
            # so the column is never an opaque blank for a referral voter.
            "source": link.label or campaign_name or link.slug,
        }
    return origins


def _case_id(row: Dict[str, Any]) -> Any:
    """Identity of the thing that was timed, as seen from an export row.

    For every type except conversation labeling this is effectively the item. A
    conversation, though, holds ~92 independent decisions, so the unit a rater
    spends time on is the SPAN — timing the whole conversation as one case would
    be a different measurement entirely.

    Always a 2-tuple, never sometimes-scalar: derive_deltas sorts these keys
    against each other, and a mix of ints and tuples raises TypeError. A type-9
    scenario can legitimately hold both (a pre-span row carries '').
    """
    item_id = row.get("item_id")
    if item_id is None:
        return None
    return (item_id, row.get("span_id") or "")


def _timing_key(row: Dict[str, Any]):
    """Key into ItemTimingService.timings_for_scenario for this row."""
    return (row.get("voter_id"), row.get("item_id"), row.get("span_id") or "")


def _stamp_timing(rows: List[Dict[str, Any]], scenario: RatingScenarios) -> None:
    """Stamp per-case timing onto the human rows in place.

    ``time_on_item_ms`` — the real captured value from EvaluationItemTiming,
    keyed by ``(voter_id, item_id)``. Coalesces: an existing value (e.g. the
    labeling co-pilot log, already set by the labeling collector) is overwritten
    only by a real generic value, never nulled.

    ``time_since_prev_ms`` — DERIVED fallback = the gap between a voter's
    consecutive item ``created_at`` timestamps, so studies predating real timing
    capture still get an approximate per-case duration. The first case per voter
    is None (no predecessor); the value is raw (idle gaps not filtered). Ranking
    rows carry no created_at, so their derived value stays None.
    """
    from services.evaluation.item_timing_service import ItemTimingService

    timing_map = ItemTimingService.timings_for_scenario(scenario.id)
    if timing_map:
        for r in rows:
            if r.get("voter_kind") != "human":
                continue
            t = timing_map.get(_timing_key(r))
            if t is not None:
                r["time_on_item_ms"] = t

    # Derived created_at-delta fallback (shared with the legacy export), computed
    # at CASE granularity so rating/ranking's multiple rows per case share one
    # per-case duration — and so conversation labeling gets one duration per
    # span rather than one per conversation.
    delta_ms = ItemTimingService.derive_deltas([
        (r.get("voter_id"), _case_id(r), r.get("created_at"))
        for r in rows
        if r.get("voter_kind") == "human"
    ])
    if delta_ms:
        for r in rows:
            if r.get("voter_kind") != "human":
                continue
            r["time_since_prev_ms"] = delta_ms.get((r.get("voter_id"), _case_id(r)))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def collect_results(
    scenario: RatingScenarios,
    *,
    include_humans: bool = True,
    include_llms: bool = True,
    include_payload: bool = False,
) -> Dict[str, Any]:
    """
    Materialise the full result set for a scenario.

    Args:
        scenario: the loaded RatingScenarios row
        include_humans: include rows from human votes (default True)
        include_llms:   include rows from LLMTaskResult (default True)
        include_payload: attach the raw ``payload_json`` to each LLM row.
            Off by default to keep CSV exports human-readable; turn on for
            debugging or when a downstream consumer needs the unstructured
            blob.

    Returns:
        ``{
            "scenario_id": int,
            "scenario_name": str,
            "function_type": str,
            "item_count": int,
            "voter_count": int,
            "row_count": int,
            "rows": [...],
            "exported_at": str (iso),
            "citation": {"message": ..., "paper": ..., "bibtex_url": ...},
        }``
    """
    func_type = _FUNCTION_TYPE_NAME.get(scenario.function_type_id, "unknown")

    item_ids = [
        si.item_id
        for si in ScenarioItems.query.filter_by(scenario_id=scenario.id).all()
    ]
    items_by_id: Dict[int, EvaluationItem] = {
        it.item_id: it
        for it in EvaluationItem.query.filter(
            EvaluationItem.item_id.in_(item_ids)
        ).all()
    } if item_ids else {}

    user_ids = [
        su.user_id
        for su in ScenarioUsers.query.filter_by(scenario_id=scenario.id).all()
    ]
    users_by_id: Dict[int, User] = {
        u.id: u
        for u in (User.query.filter(User.id.in_(user_ids)).all() if user_ids else [])
    }

    rows: List[Dict[str, Any]] = []
    voters: set = set()

    if include_humans and item_ids:
        rows.extend(_collect_human_rows(
            scenario, func_type, item_ids, items_by_id, users_by_id, voters
        ))
    if include_llms and item_ids:
        rows.extend(_collect_llm_rows(
            scenario, func_type, item_ids, items_by_id, voters,
            include_payload=include_payload,
        ))

    # Stamp each human row with the voter's provenance (where they came from).
    # Done as a single post-pass over all already-built rows so every vote type
    # (comparison, rating, labeling, …) gets the columns uniformly without each
    # per-type collector needing to know about referrals. LLM rows keep None.
    human_usernames = {
        r["voter_username"]
        for r in rows
        if r.get("voter_kind") == "human" and r.get("voter_username")
    }
    if human_usernames:
        origins = _resolve_voter_origins(human_usernames)
        for r in rows:
            if r.get("voter_kind") != "human":
                continue
            origin = origins.get(r.get("voter_username"))
            if origin:
                r["voter_origin"] = origin["account"]
                r["voter_source"] = origin["source"]

    # Scenario parts: stamp each row with the item's part id. Same post-pass
    # pattern as the provenance columns — per-type collectors stay agnostic.
    # Empty map (parts inactive) leaves the column None everywhere.
    from services.evaluation.scenario_parts_service import ScenarioPartsService
    part_map = ScenarioPartsService.item_part_map(scenario)
    if part_map:
        for r in rows:
            r["part"] = part_map.get(r.get("item_id"))

    # Per-case timing: real (captured) value + derived created_at-delta fallback.
    # Same agnostic post-pass so every function type gets the columns uniformly.
    _stamp_timing(rows, scenario)

    result = {
        "scenario_id": scenario.id,
        "scenario_name": scenario.scenario_name,
        "function_type": func_type,
        "item_count": len(item_ids),
        "voter_count": len(voters),
        "row_count": len(rows),
        "rows": rows,
        "exported_at": datetime.utcnow().isoformat(),
        # Citation requirement of the PolyForm Noncommercial license — see
        # CITATION_BLOCK above. Envelope only; never written to CSV/JSONL.
        "citation": citation_block(),
    }

    # Per-voter timing aggregates (n / mean / median / min / max / std / total per
    # rater + an overall block), computed from the per-case times just stamped on
    # the rows. Deduped to one time per CASE inside summarize_cases so rating's
    # multi-dimension rows don't inflate the stats — and so a conversation counts
    # as ~92 cases rather than one. Only attached when at least one case has a
    # time.
    from services.evaluation.item_timing_service import ItemTimingService
    timing_metrics = ItemTimingService.summarize_cases(
        (r["voter_id"], r["voter_username"], _case_id(r),
         r["time_on_item_ms"], r["time_since_prev_ms"])
        for r in rows if r.get("voter_kind") == "human"
    )
    if timing_metrics["per_voter"]:
        result["timing_metrics"] = timing_metrics

    # Labeling co-pilot aggregates (acceptance/helpful rates per annotator and
    # per label, mean time with/without suggestion) - only present when the
    # scenario ever logged co-pilot data.
    if func_type in ("labeling", "conversation_labeling"):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        copilot_metrics = LabelingCopilotService.get_copilot_metrics(scenario.id)
        if copilot_metrics.get("available"):
            result["copilot_metrics"] = copilot_metrics

    return result


# ---------------------------------------------------------------------------
# Human-vote collectors (one per function type)
# ---------------------------------------------------------------------------


def _collect_human_rows(
    scenario: RatingScenarios,
    func_type: str,
    item_ids: List[int],
    items_by_id: Dict[int, EvaluationItem],
    users_by_id: Dict[int, User],
    voters: set,
) -> Iterable[Dict[str, Any]]:
    """Dispatch to the per-type human-vote collector."""
    handler = {
        "ranking": _human_ranking_rows,
        "rating": _human_rating_rows,
        "mail_rating": _human_mail_rating_rows,
        "comparison": _human_comparison_rows,
        # communication_comparison (function_type_id=8) is a UI variant of
        # comparison and stores votes in the SAME ItemComparisonEvaluation
        # table — export it via the same collector (was silently dropping ALL
        # human A/B votes for the live study scenario 492).
        "communication_comparison": _human_comparison_rows,
        "authenticity": _human_authenticity_rows,
        "labeling": _human_labeling_rows,
        # Same collector: a conversation-labeling vote is an
        # ItemLabelingEvaluation row too, it just carries a span_id.
        "conversation_labeling": _human_labeling_rows,
    }.get(func_type)
    if handler is None:
        return []
    return handler(scenario, item_ids, items_by_id, users_by_id, voters)


def _row_for(item, scenario, voter_id, voter_username, **kw) -> Dict[str, Any]:
    """Convenience wrapper that fills the common envelope columns."""
    return _row(
        scenario_id=scenario.id,
        function_type=_FUNCTION_TYPE_NAME.get(scenario.function_type_id, "unknown"),
        item_id=item.item_id if item else kw.pop("item_id", None),
        item_label=(item.subject if item else None) or kw.pop("item_label", None),
        voter_kind="human",
        voter_id=voter_id,
        voter_username=voter_username,
        **kw,
    )


def _human_ranking_rows(scenario, item_ids, items_by_id, users_by_id, voters):
    """Each row = one (user, feature) ranking vote with bucket + score."""
    feats = Feature.query.filter(Feature.item_id.in_(item_ids)).all()
    feats_by_id = {f.feature_id: f for f in feats}
    feature_ids = list(feats_by_id.keys())
    if not feature_ids:
        return

    rankings = UserFeatureRanking.query.filter(
        UserFeatureRanking.feature_id.in_(feature_ids)
    ).all()
    for r in rankings:
        feat = feats_by_id.get(r.feature_id)
        if feat is None:
            continue
        item = items_by_id.get(feat.item_id)
        user = users_by_id.get(r.user_id)
        voters.add(("human", r.user_id))
        yield _row_for(
            item, scenario,
            voter_id=r.user_id,
            voter_username=user.username if user else None,
            model_id=feat.model_id,
            feature_id=r.feature_id,
            vote_type="bucket",
            vote_value_str=r.bucket,
            vote_value_num=r.ranking_content,
        )


def _human_rating_rows(scenario, item_ids, items_by_id, users_by_id, voters):
    """One row per (user, item, dimension) — pivoting the dimension JSON
    into a long-format. Plus one extra row per (user, item) for the
    ``overall_score`` so consumers can pick either format."""
    ratings = ItemDimensionRating.query.filter(
        ItemDimensionRating.scenario_id == scenario.id
    ).all()
    for r in ratings:
        item = items_by_id.get(r.item_id)
        user = users_by_id.get(r.user_id)
        voters.add(("human", r.user_id))
        # One row per dimension
        for dim_id, dim_score in (r.dimension_ratings or {}).items():
            yield _row_for(
                item, scenario,
                voter_id=r.user_id,
                voter_username=user.username if user else None,
                dimension_id=dim_id,
                vote_type="dimension_score",
                vote_value_num=float(dim_score) if dim_score is not None else None,
                status=r.status.value if r.status else None,
                created_at=_to_iso(r.created_at),
                updated_at=_to_iso(r.updated_at),
            )
        # Plus the overall row
        if r.overall_score is not None:
            yield _row_for(
                item, scenario,
                voter_id=r.user_id,
                voter_username=user.username if user else None,
                vote_type="overall_score",
                vote_value_num=float(r.overall_score),
                status=r.status.value if r.status else None,
                # The note belongs to the CASE, not to a dimension. Repeating it
                # on every dimension row would make one remark look like five.
                notes=r.feedback,
                created_at=_to_iso(r.created_at),
                updated_at=_to_iso(r.updated_at),
            )


def _human_mail_rating_rows(scenario, item_ids, items_by_id, users_by_id, voters):
    """Mail-rating votes + consulting categories + (legacy) per-message ratings."""
    mail_ratings = UserMailHistoryRating.query.filter(
        UserMailHistoryRating.item_id.in_(item_ids)
    ).all()
    for mr in mail_ratings:
        item = items_by_id.get(mr.item_id)
        user = users_by_id.get(mr.user_id)
        voters.add(("human", mr.user_id))
        # Pivot the four sub-scores into one row per (user, item, dimension)
        for dim_id, val in [
            ("counsellor_coherence", mr.counsellor_coherence_rating),
            ("client_coherence", mr.client_coherence_rating),
            ("quality", mr.quality_rating),
            ("overall", mr.overall_rating),
        ]:
            if val is None:
                continue
            yield _row_for(
                item, scenario,
                voter_id=mr.user_id,
                voter_username=user.username if user else None,
                dimension_id=dim_id,
                vote_type="dimension_score",
                vote_value_num=float(val),
                status=mr.status.value if mr.status else None,
                created_at=_to_iso(mr.timestamp),
            )

    # Consulting category selections — separate vote_type so they don't
    # mingle with the dimensional rows in downstream pivots.
    cat_selections = UserConsultingCategorySelection.query.filter(
        UserConsultingCategorySelection.item_id.in_(item_ids)
    ).all()
    for sel in cat_selections:
        item = items_by_id.get(sel.item_id)
        user = users_by_id.get(sel.user_id)
        voters.add(("human", sel.user_id))
        yield _row_for(
            item, scenario,
            voter_id=sel.user_id,
            voter_username=user.username if user else None,
            vote_type="consulting_category",
            vote_value_str=str(sel.consulting_category_type_id) if sel.consulting_category_type_id else None,
            notes=sel.notes,
            created_at=_to_iso(sel.timestamp),
        )


def _human_comparison_rows(scenario, item_ids, items_by_id, users_by_id, voters):
    """One row per A/B/tie choice."""
    rows = ItemComparisonEvaluation.query.filter(
        ItemComparisonEvaluation.scenario_id == scenario.id,
        ItemComparisonEvaluation.item_id.in_(item_ids),
    ).all()
    for ev in rows:
        item = items_by_id.get(ev.item_id)
        user = users_by_id.get(ev.user_id)
        voters.add(("human", ev.user_id))
        yield _row_for(
            item, scenario,
            voter_id=ev.user_id,
            voter_username=user.username if user else None,
            vote_type="comparison_choice",
            vote_value_str=ev.choice,
            notes=ev.notes,
            created_at=_to_iso(ev.created_at),
            updated_at=_to_iso(ev.updated_at),
        )


def _human_authenticity_rows(scenario, item_ids, items_by_id, users_by_id, voters):
    """Filter via ``item_id`` (the canonical column) — the legacy export
    still uses ``thread_id`` via the synonym, which works but is confusing
    and fragile when reading the model later."""
    rows = UserAuthenticityVote.query.filter(
        UserAuthenticityVote.item_id.in_(item_ids)
    ).all()
    for v in rows:
        item = items_by_id.get(v.item_id)
        user = users_by_id.get(v.user_id)
        voters.add(("human", v.user_id))
        yield _row_for(
            item, scenario,
            voter_id=v.user_id,
            voter_username=user.username if user else None,
            vote_type="authenticity_vote",
            vote_value_str=v.vote,
            vote_value_num=float(v.confidence) if v.confidence is not None else None,
            notes=v.notes,
            created_at=_to_iso(getattr(v, "created_at", None) or getattr(v, "timestamp", None)),
        )


def _human_labeling_rows(scenario, item_ids, items_by_id, users_by_id, voters):
    rows = ItemLabelingEvaluation.query.filter(
        ItemLabelingEvaluation.scenario_id == scenario.id,
        ItemLabelingEvaluation.item_id.in_(item_ids),
    ).all()

    # Batch-join the co-pilot log so labeling rows carry the study columns
    # (shown/accepted/helpful/time). Empty map when the co-pilot was off.
    #
    # The key MUST include span_id: conversation labeling writes one log row per
    # span, so keying by (user, item) alone would collapse ~92 rows into one and
    # stamp every span of a conversation with the same suggestion and helpful
    # flag. Classic labeling stores '' there, so the key degrades cleanly.
    from db.models import LabelingCopilotLog
    copilot_logs = {
        (log.user_id, log.item_id, log.span_id or ""): log
        for log in LabelingCopilotLog.query.filter(
            LabelingCopilotLog.scenario_id == scenario.id,
            LabelingCopilotLog.item_id.in_(item_ids),
        ).all()
    }

    # span_id -> (message_id, span_index) per item, so a span row can carry its
    # position without the consumer re-reading the item payload.
    span_meta_by_item = {}
    for item_id, item in items_by_id.items():
        block = ((getattr(item, "metadata_json", None) or {})
                 .get("conversation_labeling") or {})
        span_meta_by_item[item_id] = {
            s.get("span_id"): (s.get("message_id"), s.get("span_index"))
            for s in (block.get("spans") or [])
            if s.get("span_id")
        }

    for ev in rows:
        item = items_by_id.get(ev.item_id)
        user = users_by_id.get(ev.user_id)
        voters.add(("human", ev.user_id))
        span_id = ev.span_id or ""
        log = copilot_logs.get((ev.user_id, ev.item_id, span_id))
        message_id, span_index = span_meta_by_item.get(ev.item_id, {}).get(
            span_id, (None, None)
        )
        copilot_columns = {}
        if log is not None:
            copilot_columns = {
                "copilot_shown": log.shown,
                "copilot_suggested_label": log.suggested_label,
                "copilot_suggested_label_2": log.suggested_label_2,
                "copilot_accepted": log.accepted,
                "copilot_accepted_any": log.accepted_any,
                "copilot_helpful": log.helpful,
                "copilot_model": log.model_id,
                "copilot_prompt_version": log.prompt_version,
                "time_on_item_ms": log.time_on_item_ms,
            }
        yield _row_for(
            item, scenario,
            voter_id=ev.user_id,
            voter_username=user.username if user else None,
            vote_type="label_choice",
            vote_value_str=ev.category_id,
            status="unsure" if ev.is_unsure else None,
            notes=ev.feedback,
            created_at=_to_iso(ev.created_at),
            updated_at=_to_iso(ev.updated_at),
            # None for classic labeling, where '' is the sentinel for "whole
            # item" — an empty CSV cell reads correctly as "no span dimension",
            # whereas a literal '' would look like a real, blank span id.
            span_id=span_id or None,
            message_id=message_id,
            span_index=span_index,
            **copilot_columns,
        )


# ---------------------------------------------------------------------------
# LLM-vote collector (one shape across all task types — payload differs)
# ---------------------------------------------------------------------------


def _collect_llm_rows(
    scenario: RatingScenarios,
    func_type: str,
    item_ids: List[int],
    items_by_id: Dict[int, EvaluationItem],
    voters: set,
    *,
    include_payload: bool = False,
) -> Iterable[Dict[str, Any]]:
    """Pull LLMTaskResult rows for this scenario, render one row per
    `(model_id, item, dimension)` for rating-shaped payloads or one row
    per `(model_id, item)` for everything else."""
    results = LLMTaskResult.query.filter(
        LLMTaskResult.scenario_id == scenario.id,
        LLMTaskResult.thread_id.in_(item_ids),
        # Co-pilot suggestions are pre-annotations, not evaluator votes -
        # they ride along on the HUMAN labeling rows (copilot_* columns)
        # instead of appearing as an LLM voter of their own.
        LLMTaskResult.task_type != "copilot_labeling",
    ).all()

    for r in results:
        item = items_by_id.get(r.thread_id)
        payload = r.payload_json or {}
        voters.add(("llm", r.model_id))

        # Dimensional rating payloads — pivot like the human rating path.
        if r.task_type in ("rating", "mail_rating") and isinstance(payload, dict) \
                and payload.get("type") == "dimensional":
            for dr in payload.get("dimensional_ratings", []) or []:
                dim_id = dr.get("dimension")
                rating_val = dr.get("rating")
                if not dim_id or rating_val is None:
                    continue
                yield _row(
                    scenario_id=scenario.id,
                    function_type=func_type,
                    item_id=r.thread_id,
                    item_label=item.subject if item else None,
                    voter_kind="llm",
                    model_id=r.model_id,
                    dimension_id=dim_id,
                    vote_type="dimension_score",
                    vote_value_num=float(rating_val),
                    status="error" if r.error else "ok",
                    created_at=_to_iso(r.created_at),
                )
            overall = payload.get("overall_rating") or payload.get("average_rating")
            if overall is not None:
                yield _row(
                    scenario_id=scenario.id,
                    function_type=func_type,
                    item_id=r.thread_id,
                    item_label=item.subject if item else None,
                    voter_kind="llm",
                    model_id=r.model_id,
                    vote_type="overall_score",
                    vote_value_num=float(overall),
                    status="error" if r.error else "ok",
                    created_at=_to_iso(r.created_at),
                )
            continue

        # Generic single-value payload — one row, vote_type comes from
        # task_type so consumers can group by type without reading payload.
        vote_value_str = None
        vote_value_num = None
        if r.task_type in ("comparison", "communication_comparison"):
            # LLM comparison stores the pick under "winner" — item-based:
            # {"winner": "A"|"B"|"tie"}; session-based: {"results": [{"winner": ...}]}.
            # The old code read "choice"/"selection" (which don't exist), so LLM
            # comparison votes exported as null and session results were dropped.
            if isinstance(payload, dict):
                results = payload.get("results")
                if isinstance(results, list) and results:
                    for sub in results:
                        sw = sub.get("winner") if isinstance(sub, dict) else None
                        if sw is None:
                            continue
                        yield _row(
                            scenario_id=scenario.id,
                            function_type=func_type,
                            item_id=r.thread_id,
                            item_label=item.subject if item else None,
                            voter_kind="llm",
                            model_id=r.model_id,
                            vote_type="comparison_winner",
                            vote_value_str=str(sw),
                            status="error" if r.error else "ok",
                            created_at=_to_iso(r.created_at),
                        )
                    continue
                winner = payload.get("winner") or payload.get("choice") or payload.get("selection")
                vote_value_str = str(winner) if winner is not None else None
        elif r.task_type == "authenticity":
            vote_value_str = payload.get("vote") if isinstance(payload, dict) else None
            cv = payload.get("confidence") if isinstance(payload, dict) else None
            try:
                vote_value_num = float(cv) if cv is not None else None
            except (TypeError, ValueError):
                vote_value_num = None
        elif r.task_type == "labeling":
            vote_value_str = (
                payload.get("category_id") or payload.get("label")
            ) if isinstance(payload, dict) else None
        elif r.task_type == "ranking":
            # Ranking LLM payloads carry {bucket_name: [feature_ids]} for ANY
            # bucket scheme — emit one row per (feature, bucket) using the
            # payload's OWN keys. The old hardcoded ("gut","mittel","neutral",
            # "schlecht") list silently dropped English / custom-bucket scenarios.
            if isinstance(payload, dict):
                for bucket_id, feats in payload.items():
                    if not isinstance(feats, list):
                        continue
                    for feat_id in feats:
                        yield _row(
                            scenario_id=scenario.id,
                            function_type=func_type,
                            item_id=r.thread_id,
                            item_label=item.subject if item else None,
                            voter_kind="llm",
                            model_id=r.model_id,
                            feature_id=feat_id,
                            vote_type="bucket",
                            vote_value_str=str(bucket_id),
                            status="error" if r.error else "ok",
                            created_at=_to_iso(r.created_at),
                        )
            continue

        out = _row(
            scenario_id=scenario.id,
            function_type=func_type,
            item_id=r.thread_id,
            item_label=item.subject if item else None,
            voter_kind="llm",
            model_id=r.model_id,
            vote_type=f"{r.task_type}_choice" if r.task_type else "llm_payload",
            vote_value_str=vote_value_str,
            vote_value_num=vote_value_num,
            status="error" if r.error else "ok",
            created_at=_to_iso(r.created_at),
        )
        if include_payload:
            out["payload_json"] = payload
        yield out


# ---------------------------------------------------------------------------
# IRR bundle (cached call into AgreementMetricsService)
# ---------------------------------------------------------------------------


def collect_metrics(
    scenario: RatingScenarios,
    *,
    copilot_filter: Optional[str] = None,
    part_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call AgreementMetricsService and condense the result into a small
    `{metric_key: {value, interpretation, aggregation_method}}` block
    suitable for embedding in the export envelope.

    copilot_filter / part_filter (labeling only) restrict the underlying
    cells the same way the agreement endpoint does — this is how a study
    fetches the IRR of one calibration phase headlessly.

    Returns ``{}`` (not None) when no metrics could be computed — caller
    should then signal "no IRR available" to the user, not fall back.
    """
    from services.evaluation.agreement_metrics_service import AgreementMetricsService

    raw = AgreementMetricsService.calculate_all_metrics(
        scenario_id=scenario.id,
        include_llm=True,
        include_human=True,
        copilot_filter=copilot_filter,
        part_filter=part_filter,
    )
    if raw and raw.get("error"):
        # Informational only (e.g. "No evaluations found" on a fresh
        # scenario) — HTTP semantics stay with the caller; the v1 metrics
        # route returns this as 200 so pollers don't break pre-first-label.
        return {
            "scenario_id": scenario.id,
            "error": raw["error"],
            "metrics": {},
            **({"copilot_filter": copilot_filter} if copilot_filter else {}),
            **({"part_filter": part_filter} if part_filter else {}),
        }
    metrics = (raw or {}).get("metrics") or {}
    summary = {}
    for key, m in metrics.items():
        if not isinstance(m, dict):
            continue
        summary[key] = {
            "value": m.get("value"),
            "interpretation": m.get("interpretation"),
            "aggregation_method": m.get("aggregation_method"),
        }
    return {
        "scenario_id": scenario.id,
        "task_type": (raw or {}).get("task_type"),
        "rater_count": (raw or {}).get("rater_count"),
        "item_count": (raw or {}).get("item_count"),
        "metrics": summary,
        **({"copilot_filter": copilot_filter} if copilot_filter else {}),
        **({"part_filter": part_filter} if part_filter else {}),
    }
