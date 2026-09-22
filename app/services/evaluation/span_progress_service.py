"""
Span-level progress for conversation-labeling scenarios.

Classic labeling (type 7) asks one question per item, so "did this user finish
this item?" is a single row lookup. Conversation labeling (type 9) asks one
question per SPAN of a conversation, so the same question becomes
"has this user voted on every span of this item?".

That comparison needs the item's span inventory, which the importer indexes on
``EvaluationItem.metadata_json['conversation_labeling']['spans']``
(see api_v1_scenario_service._persist_conversation_labeling for why it lives
there rather than in its own table).

This module exists because "done" is computed in FOUR independent places in
LLARS — the session batch view, the single-item lookup, the progression states
in the stats service and the per-part assessor progress. They already agreed on
the classic rule by coincidence of three separate implementations; for the span
rule they agree because they all call in here.
"""

from typing import Dict, Iterable, List, Optional

CONVERSATION_LABELING_META_KEY = "conversation_labeling"


def span_ids_for_items(item_ids: Iterable[int]) -> Dict[int, List[str]]:
    """Return ``{item_id: [span_id, ...]}`` for the given conversation items.

    Items with no span index (wrong type, or an import that predates the span
    structure) map to an empty list — callers treat that as "nothing to do"
    rather than crashing.
    """
    from db.models import EvaluationItem

    ids = [int(i) for i in item_ids if i is not None]
    if not ids:
        return {}

    rows = (
        EvaluationItem.query
        .with_entities(EvaluationItem.item_id, EvaluationItem.metadata_json)
        .filter(EvaluationItem.item_id.in_(ids))
        .all()
    )

    result: Dict[int, List[str]] = {}
    for item_id, meta in rows:
        result[item_id] = span_ids_from_metadata(meta)
    return result


def span_ids_from_metadata(metadata_json: Optional[dict]) -> List[str]:
    """Extract the ordered span ids out of one item's metadata blob."""
    if not isinstance(metadata_json, dict):
        return []
    block = metadata_json.get(CONVERSATION_LABELING_META_KEY)
    if not isinstance(block, dict):
        return []
    spans = block.get("spans")
    if not isinstance(spans, list):
        return []
    return [
        str(s.get("span_id"))
        for s in spans
        if isinstance(s, dict) and s.get("span_id")
    ]


def span_progress_sets(
    scenario_id: int, user_id: int, item_ids: Iterable[int]
) -> Dict[int, Dict[str, set]]:
    """Return ``{item_id: {"decided": {span_id}, "started": {span_id}}}``.

    Both sets come out of ONE query because every caller needs both and this
    runs per item list on every overview render.

    "Decided" mirrors the classic labeling rule: a category was chosen OR the
    rater explicitly marked the span unsure. "Started" is the question-first
    middle ground — the rater answered decision questions (or left feedback)
    for that span but has not committed to a label yet. Both classifications
    come from ``labeling_types.labeling_row_status`` so the span rule cannot
    drift away from the item rule.
    """
    from db.models.scenario import ItemLabelingEvaluation
    from services.evaluation.labeling_types import (
        LABELING_STATUS_DONE,
        LABELING_STATUS_IN_PROGRESS,
        labeling_row_status,
    )

    ids = [int(i) for i in item_ids if i is not None]
    if not ids:
        return {}

    rows = (
        ItemLabelingEvaluation.query
        .filter(
            ItemLabelingEvaluation.user_id == user_id,
            ItemLabelingEvaluation.scenario_id == scenario_id,
            ItemLabelingEvaluation.item_id.in_(ids),
        )
        .all()
    )

    progress: Dict[int, Dict[str, set]] = {}
    for row in rows:
        status = labeling_row_status(row)
        if status == LABELING_STATUS_DONE:
            bucket = "decided"
        elif status == LABELING_STATUS_IN_PROGRESS:
            bucket = "started"
        else:
            continue
        entry = progress.setdefault(row.item_id, {"decided": set(), "started": set()})
        entry[bucket].add(row.span_id or "")
    return progress


def voted_span_ids(
    scenario_id: int, user_id: int, item_ids: Iterable[int]
) -> Dict[int, set]:
    """Return ``{item_id: {span_id that this user has DECIDED}}``.

    Thin view on :func:`span_progress_sets` — kept because "which spans are
    finished" is what the counting callers actually mean.
    """
    return {
        item_id: entry["decided"]
        for item_id, entry in span_progress_sets(
            scenario_id, user_id, item_ids
        ).items()
    }


def item_status_map(
    scenario_id: int, user_id: int, item_ids: Iterable[int]
) -> Dict[int, str]:
    """Per-item ``'done' | 'in_progress' | 'pending'`` for conversation labeling.

    Unlike classic labeling — which is binary, because one item is one decision
    — a conversation genuinely has a middle state: 40 of 92 spans done. Raters
    spend ~20 minutes inside a single item, so surfacing that is the difference
    between a usable overview and one that shows "pending" for most of a
    working day.
    """
    ids = [int(i) for i in item_ids if i is not None]
    if not ids:
        return {}

    inventory = span_ids_for_items(ids)
    progress = span_progress_sets(scenario_id, user_id, ids)

    status: Dict[int, str] = {}
    for item_id in ids:
        total = inventory.get(item_id) or []
        entry = progress.get(item_id) or {}
        done = entry.get("decided") or set()
        started = entry.get("started") or set()
        if not total:
            # No spans indexed: nothing can be completed, so don't claim it is.
            status[item_id] = "pending"
            continue
        done_count = sum(1 for span_id in total if span_id in done)
        if done_count >= len(total):
            status[item_id] = "done"
        elif done_count > 0 or any(span_id in started for span_id in total):
            # Answering the decision questions of a single span is already work
            # the rater must be able to see again — with question-first
            # labeling the first click lands here, not on a label.
            status[item_id] = "in_progress"
        else:
            status[item_id] = "pending"
    return status


def split_span(item, span_id: str, offset: int) -> dict:
    """Split one span into two at an absolute character offset.

    Why this exists
    ---------------
    The unitizing is frozen at import time and deliberately not editable — a
    wrong boundary is normally REPORTED through a label card, not re-cut,
    because silently re-segmenting mid-study would make the units incomparable
    between raters. This is the sanctioned exception: a span that plainly
    carries two intents can be cut, and the cut is recorded in the item's own
    span index so both raters see the same units from then on.

    Rules that keep the data honest:

    * The cut must fall strictly INSIDE the span. Cutting at either edge would
      produce a zero-length unit.
    * The two halves get suffixed ids derived from the original (``x`` ->
      ``x+a`` / ``x+b``). Derived rather than renumbered, so an export from
      before the split still joins onto the conversation, and re-running a
      split is idempotent in shape.
    * Any EXISTING vote on the original span is dropped by the caller — a
      decision made about the whole span is not a decision about either half,
      and silently carrying it over would fabricate data.

    Returns ``{'spans': [...], 'new_ids': (a, b)}`` — the caller persists.
    """
    spans = list(span_ids_and_records(item))
    idx = next((i for i, s in enumerate(spans) if s.get("span_id") == span_id), -1)
    if idx < 0:
        raise ValueError(f"span '{span_id}' not found on this item")

    original = spans[idx]
    start = int(original.get("start", 0))
    end = int(original.get("end", 0))
    offset = int(offset)

    if not (start < offset < end):
        raise ValueError(
            f"split offset {offset} must lie strictly inside the span "
            f"[{start}, {end}]"
        )

    left = dict(original)
    right = dict(original)
    left["span_id"] = f"{span_id}+a"
    left["end"] = offset
    right["span_id"] = f"{span_id}+b"
    right["start"] = offset

    spans[idx:idx + 1] = [left, right]

    # Renumber span_index within the affected message so the reading order
    # stays a dense sequence — the interface walks it positionally.
    msg_index = original.get("message_index")
    counter = 0
    for s in spans:
        if s.get("message_index") == msg_index:
            s["span_index"] = counter
            counter += 1

    return {"spans": spans, "new_ids": (left["span_id"], right["span_id"])}


def merge_spans(item, span_ids, message_text: Optional[str] = None) -> dict:
    """Merge two or more CONSECUTIVE spans of the same message into one.

    The inverse of :func:`split_span`, and it exists for the same reason: the
    unitizing is frozen, but a boundary that is plainly wrong should be fixable
    rather than only reportable. A rater who cut by mistake — or who finds
    neighbouring units that are really one speech act — can put them back
    together.

    Takes a LIST because the rater picks the spans themselves (ctrl/cmd-click);
    letting them mark three and then merging only two would silently do
    something other than what they selected.

    Rules, mirroring split:

    * The spans must form an unbroken run in reading order and belong to the
      SAME message. A union across a message boundary would produce a unit whose
      text does not exist anywhere as a contiguous string.
    * Only WHITESPACE may sit between consecutive spans. Real segmentations
      leave the separator out of every span — sentence spans are typically one
      space apart — so demanding exact contiguity would make merging impossible
      on actual data. Absorbing a space is harmless; absorbing words is not,
      because nobody decided about them. Without ``message_text`` the check
      falls back to exact contiguity, which is the conservative reading.
    * The merged id is derived, not renumbered. Undoing a split gives back the
      original id (``x+a`` + ``x+b`` -> ``x``), so a study that split and merged
      again ends up exactly where it started; otherwise the id is the first
      span's with a ``+m`` marker so an older export still joins.
    * ALL original votes are dropped by the caller — decisions about the parts
      are not a decision about the whole, and picking one of them would be
      inventing a rater's opinion.

    Returns ``{'spans': [...], 'new_id': str, 'removed_ids': (...)}``.
    """
    wanted = [str(sid) for sid in (span_ids or [])]
    if len(set(wanted)) < 2:
        raise ValueError("merging needs at least two distinct spans")

    spans = list(span_ids_and_records(item))
    positions = []
    for sid in dict.fromkeys(wanted):          # de-dupe, keep first order
        idx = next((k for k, s in enumerate(spans) if s.get("span_id") == sid), -1)
        if idx < 0:
            raise ValueError(f"span '{sid}' not found on this item")
        positions.append(idx)
    positions.sort()

    lo, hi = positions[0], positions[-1]
    if positions != list(range(lo, hi + 1)):
        raise ValueError("only consecutive spans can be merged")

    run = spans[lo:hi + 1]
    message_index = run[0].get("message_index")
    for part in run[1:]:
        if part.get("message_index") != message_index:
            raise ValueError("spans belong to different messages")
    for left, right in zip(run, run[1:]):
        gap_start, gap_end = int(left.get("end", 0)), int(right.get("start", 0))
        if gap_start == gap_end:
            continue
        between = (
            message_text[gap_start:gap_end] if message_text is not None else None
        )
        if between is None or between.strip():
            raise ValueError(
                "spans are not adjacent - merging them would swallow the text "
                "between them without a decision"
            )

    merged = dict(run[0])
    merged["end"] = int(run[-1].get("end", 0))
    merged["span_id"] = _merged_span_id([str(s.get("span_id")) for s in run])
    # `text` is a redundant import convenience; a stale fragment would now lie
    # about the span, and the offsets are the truth anyway.
    merged.pop("text", None)

    removed_ids = tuple(str(s.get("span_id")) for s in run)
    spans[lo:hi + 1] = [merged]

    msg_index = merged.get("message_index")
    counter = 0
    for s in spans:
        if s.get("message_index") == msg_index:
            s["span_index"] = counter
            counter += 1

    return {"spans": spans, "new_id": merged["span_id"], "removed_ids": removed_ids}


def _merged_span_id(ids) -> str:
    """Id for the union of a run of spans.

    Undoing a split is the common case, so recognise it: ``x+a`` merged with
    ``x+b`` gives back plain ``x``. A study that split and merged again then
    holds exactly the ids it started with, instead of accumulating markers.
    """
    if len(ids) == 2 and ids[0].endswith("+a") and ids[1].endswith("+b"):
        stem = ids[0][:-2]
        if stem == ids[1][:-2]:
            return stem
    return f"{ids[0]}+m"


def span_ids_and_records(item) -> list:
    """Full span records of an item (not just the ids)."""
    meta = getattr(item, "metadata_json", None) or {}
    block = meta.get(CONVERSATION_LABELING_META_KEY)
    if not isinstance(block, dict):
        return []
    spans = block.get("spans")
    return [dict(s) for s in spans] if isinstance(spans, list) else []


def span_counts(
    scenario_id: int, user_id: int, item_ids: Iterable[int]
) -> Dict[str, int]:
    """Aggregate ``{'total': N, 'done': M}`` over the given items.

    This is the number the assessor-progress and parts views need: progress is
    counted in SPANS, not items, because an item here is 20 minutes of work.
    """
    ids = [int(i) for i in item_ids if i is not None]
    inventory = span_ids_for_items(ids)
    voted = voted_span_ids(scenario_id, user_id, ids)

    total = 0
    done = 0
    for item_id in ids:
        spans = inventory.get(item_id) or []
        decided = voted.get(item_id) or set()
        total += len(spans)
        done += sum(1 for span_id in spans if span_id in decided)
    return {"total": total, "done": done}
