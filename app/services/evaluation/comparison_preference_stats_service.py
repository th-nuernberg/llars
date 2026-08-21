"""
Comparison Preference Stats Service.

Aggregates a single user's pairwise A/B choices in a Comparison scenario into
preference patterns based on the provenance of each Feature (encoded in
Feature.model_id). Powers the gamification reward popup and the per-user
history drawer.

Design notes:
- Pure parsing of `model_id` strings — no DB migration. Provenance categories
  are inferred from prefixes used by the seeders and the wizard (see
  `app/db/seeders/comparison_demo_data.py`).
- Each comparison contributes to at most one bucket per orthogonal axis:
    * human_vs_llm     — only when one side is Human and the other is an LLM
    * trained_vs_base  — only when one side is `Trained-SFT` and the other is
                         `Pre-Base`
    * larger_vs_smaller — only when both sides have a known parameter count
                          and the counts differ
    * closed_vs_open   — only when one side is `Closed-Baseline` and the
                         other is an open-source category
  Tie-choices are excluded from every numerator/denominator (no signal for
  preference reveal). Items where neither side maps to a known category are
  skipped silently.

The popup hides axes with `applicable == 0` so first-time users don't see a
wall of empty stat cards.
"""

from __future__ import annotations

from typing import Optional

from db import db
from db.models.scenario import Feature, ItemComparisonEvaluation, RatingScenarios


# ---------------------------------------------------------------------------
# Provenance parser
# ---------------------------------------------------------------------------

# Approximate parameter counts (in billions) keyed by the *family* segment
# parsed off the tail of `model_id`. Lower-cased on lookup. Conservative when
# numbers aren't public — only used as a tiebreaker for the "larger" axis,
# never displayed verbatim, so a rough estimate is fine.
_PARAMS_B: dict[str, float] = {
    # Mistral family
    "mistral-small-3.2-24b-instruct-2506": 24.0,
    "mistral-small-24b": 24.0,
    "magistral-small-2509": 24.0,
    "magistral-small": 24.0,
    "mistral-7b": 7.0,
    "mis24b": 24.0,
    "mis24b-base": 24.0,
    "mis24b-instruct": 24.0,
    "mis24b-instruct-c1": 24.0,
    "mis24b-instrprofi": 24.0,
    "mis24b-baseprofi": 24.0,
    "mis119b-instruct": 119.0,
    # MiniMax / Ministral 8B
    "min8b-2410instr": 8.0,
    "min8b-instrprofi": 8.0,
    # Qwen
    "qwen25-72b-base": 72.0,
    "qwen25-72b-instruct": 72.0,
    "qwen25-72b-instrprofi": 72.0,
    # LLäMMlein DE (~7B)
    "llaem-base": 7.0,
    "llaem-v2profi": 7.0,
    "llaemmlein-v2profi": 7.0,
    # Community-finetuned counseling models
    "chatpsychiatrist-vicuna-7b": 7.0,
    "psychocounsel-llama3-8b": 8.0,
    # OpenAI (public estimates; treat as approximate)
    "gpt-5-nano": 1.5,
    "gpt-5-mini": 8.0,
    "gpt-4o-mini": 8.0,
}


# Prefix-less family patterns used by the EMNLP v6 / study seeders.
# Order matters — the first matching pattern wins. Matched against the
# *tail* segment (lower-cased), so this also works for prefixed ids
# falling through the explicit-prefix branch above.
_V6_FAMILY_RULES: list[tuple[str, str]] = [
    # Bare "human" id — used by EMNLP v6, no prefix
    ("human", "Human"),
    # Project-fine-tuned ("Profi") suffixes are always SFT, regardless of family
    ("*profi", "Trained-SFT"),
    # Community-finetuned counseling models = SFT-trained
    ("chatpsychiatrist-*", "Trained-SFT"),
    ("psychocounsel-*", "Trained-SFT"),
    # Bare base models (no instruction tuning)
    ("*-base", "Pre-Base"),
    # Bare instruct-tuned baselines
    ("*-instruct", "Pre-Instruct"),
    ("*-instruct-*", "Pre-Instruct"),
    ("*-2410instr", "Pre-Instruct"),
    ("*instr", "Pre-Instruct"),
]


def _match_v6_family(tail: str) -> Optional[str]:
    """Match the family tail against the v6 glob rules. Returns category or None."""
    import fnmatch
    for pattern, category in _V6_FAMILY_RULES:
        if fnmatch.fnmatchcase(tail, pattern):
            return category
    return None


def _categorize(model_id: Optional[str]) -> dict:
    """
    Map a Feature.model_id to a provenance category and (optionally) a
    parameter-count estimate.

    Returns a dict with keys: ``category``, ``family``, ``params_b``.
    ``params_b`` is None when no entry matches.
    """
    if not model_id:
        return {"category": "Unknown", "family": None, "params_b": None}

    mid = str(model_id).strip()
    lower = mid.lower()

    # Family = the tail segment after the last "/" or ":". Used for params_b
    # and v6 glob-matching (the EMNLP v6 importer stores bare ids without
    # any provenance prefix, e.g. "mis24b-instrprofi" or "human").
    tail = mid.split("/")[-1].split(":")[-1].strip().lower()

    if lower.startswith("human:") or tail == "human":
        category = "Human"
    elif lower.startswith("sft:"):
        category = "Trained-SFT"
    elif lower.startswith("base:"):
        category = "Pre-Base"
    elif lower.startswith("global/openai/"):
        category = "Closed-Baseline"
    elif lower.startswith("global/"):
        # Mistral, Anthropic, etc. — open-weights instruct baselines
        category = "Pre-Instruct"
    else:
        # Fall through to v6 glob rules for bare/unprefixed ids.
        category = _match_v6_family(tail) or "Unknown"

    params_b = _PARAMS_B.get(tail)

    return {"category": category, "family": tail or None, "params_b": params_b}


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

# Categories considered "LLM-side" when pitted against Human.
_LLM_CATEGORIES = {"Trained-SFT", "Pre-Base", "Pre-Instruct", "Closed-Baseline"}
# Categories considered "open-source" when pitted against Closed-Baseline.
_OPEN_CATEGORIES = {"Trained-SFT", "Pre-Base", "Pre-Instruct"}


def _empty_payload(scenario_id: int, user_id: int) -> dict:
    return {
        "scenario_id": scenario_id,
        "user_id": user_id,
        "total_evaluated": 0,
        "preferences": {
            "human_vs_llm":      {"chose_human":   0, "applicable": 0},
            "trained_vs_base":   {"chose_trained": 0, "applicable": 0},
            "larger_vs_smaller": {"chose_larger":  0, "applicable": 0},
            "closed_vs_open":    {"chose_closed":  0, "applicable": 0},
        },
        "history": [],
    }


def get_user_preference_stats(scenario_id: int, user_id: int) -> dict:
    """
    Build the preference-pattern payload consumed by the reward popup and the
    history drawer.

    The two Features per item are sorted by `feature_id` ascending so they map
    to the same A/B labels the assessor saw in the UI (see
    `applyItemData()` in `useComparisonEvaluation.js`, which uses
    `features[0]` as Option A and `features[1]` as Option B in the order
    returned by the threads/features endpoint).
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if scenario is None:
        # Caller turns this into a NotFoundError; service stays focused.
        return _empty_payload(scenario_id, user_id)

    rows: list[ItemComparisonEvaluation] = (
        ItemComparisonEvaluation.query
        .filter_by(scenario_id=scenario_id, user_id=user_id)
        .order_by(ItemComparisonEvaluation.created_at.asc())
        .all()
    )
    if not rows:
        return _empty_payload(scenario_id, user_id)

    # Bulk-load features for all touched items in one query — comparison
    # scenarios with hundreds of items would otherwise N+1.
    item_ids = [r.item_id for r in rows]
    features_by_item: dict[int, list[Feature]] = {}
    if item_ids:
        feats = (
            Feature.query
            .filter(Feature.item_id.in_(item_ids))
            .order_by(Feature.item_id.asc(), Feature.feature_id.asc())
            .all()
        )
        for f in feats:
            features_by_item.setdefault(f.item_id, []).append(f)

    payload = _empty_payload(scenario_id, user_id)
    payload["total_evaluated"] = len(rows)
    prefs = payload["preferences"]
    history: list[dict] = payload["history"]

    for row in rows:
        feats = features_by_item.get(row.item_id, [])
        if len(feats) < 2:
            # Skip items without a clean two-feature shape — they were rated
            # against a fallback layout (e.g. messages-only TEXT_PAIR) where
            # provenance can't be recovered.
            continue

        opt_a, opt_b = feats[0], feats[1]
        cat_a = _categorize(opt_a.model_id)
        cat_b = _categorize(opt_b.model_id)
        choice = row.choice  # 'A' | 'B' | 'tie'

        history.append({
            "item_id": row.item_id,
            "choice": choice,
            "notes": row.notes,
            "option_a": {
                "label": "A",
                "model_id": opt_a.model_id,
                "category": cat_a["category"],
                "params_b": cat_a["params_b"],
            },
            "option_b": {
                "label": "B",
                "model_id": opt_b.model_id,
                "category": cat_b["category"],
                "params_b": cat_b["params_b"],
            },
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

        # Tie-choices contribute no signal to any of the four axes.
        if choice == "tie":
            continue

        chose_a = (choice == "A")
        cat_chosen = cat_a if chose_a else cat_b
        cat_other = cat_b if chose_a else cat_a

        # Axis 1: Human vs LLM
        if cat_a["category"] == "Human" and cat_b["category"] in _LLM_CATEGORIES:
            prefs["human_vs_llm"]["applicable"] += 1
            if chose_a:
                prefs["human_vs_llm"]["chose_human"] += 1
        elif cat_b["category"] == "Human" and cat_a["category"] in _LLM_CATEGORIES:
            prefs["human_vs_llm"]["applicable"] += 1
            if not chose_a:
                prefs["human_vs_llm"]["chose_human"] += 1

        # Axis 2: Trained-SFT vs Pre-Base
        if {cat_a["category"], cat_b["category"]} == {"Trained-SFT", "Pre-Base"}:
            prefs["trained_vs_base"]["applicable"] += 1
            if cat_chosen["category"] == "Trained-SFT":
                prefs["trained_vs_base"]["chose_trained"] += 1

        # Axis 3: Larger vs Smaller (params_b known on both sides, unequal)
        pa, pb = cat_a["params_b"], cat_b["params_b"]
        if pa is not None and pb is not None and pa != pb:
            prefs["larger_vs_smaller"]["applicable"] += 1
            larger = "A" if pa > pb else "B"
            if choice == larger:
                prefs["larger_vs_smaller"]["chose_larger"] += 1

        # Axis 4: Closed vs Open
        if cat_a["category"] == "Closed-Baseline" and cat_b["category"] in _OPEN_CATEGORIES:
            prefs["closed_vs_open"]["applicable"] += 1
            if chose_a:
                prefs["closed_vs_open"]["chose_closed"] += 1
        elif cat_b["category"] == "Closed-Baseline" and cat_a["category"] in _OPEN_CATEGORIES:
            prefs["closed_vs_open"]["applicable"] += 1
            if not chose_a:
                prefs["closed_vs_open"]["chose_closed"] += 1

    return payload
