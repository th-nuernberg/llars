# anonymize_privacy_filter_detection.py
"""
privacy-filter based entity detection for the anonymize service.

Wraps OpenAI's `openai/privacy-filter` model (a 1.5B-param, 50M-active
bidirectional token classifier, Apache-2.0) as a *fourth detection engine*
alongside regex, Flair and LLM.

Architecture decisions (see also PRIVACY_FILTER_LABEL_MAP in
anonymize_constants.py):

- **Detector only.** The model marks spans; it does NOT do consistent
  pseudonymous replacement. That is intentional - LLARS already owns the
  replacement/grouping logic (anonymize_service.py), so we only need spans here,
  exactly like `find_flair_ner()`.
- **English-centric.** The model card warns of degraded quality on non-English
  text. For German counselling data it should therefore be benchmarked against
  Flair (scripts/anonymize/benchmark_privacy_filter_vs_flair.py) before relying
  on it, and is best used as a second opinion in addition to Flair, not as a
  drop-in replacement.
- **Offline-friendly.** Defaults to the HF hub id but honours a local path via
  `ANONYMIZE_PRIVACY_FILTER_MODEL` so it can run air-gapped once cached.
- **CPU by default** (mirrors the Flair loader) to avoid surprise GPU usage on
  shared servers; set `ANONYMIZE_PRIVACY_FILTER_DEVICE=cuda` to opt in.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

from .anonymize_constants import (
    EntityOccurrence,
    PRIVACY_FILTER_MODEL_ID,
    PRIVACY_FILTER_LABEL_MAP,
)

logger = logging.getLogger(__name__)


def _model_ref() -> str:
    """Resolve the model reference (local path wins over the hub id)."""
    return (os.environ.get("ANONYMIZE_PRIVACY_FILTER_MODEL") or PRIVACY_FILTER_MODEL_ID).strip()


def privacy_filter_quick_status() -> dict[str, Any]:
    """
    Fast readiness probe without loading the model.

    We only confirm that the `transformers` stack is importable and report the
    configured model reference. The (potentially expensive) first load - which
    may download weights from HuggingFace - happens lazily in _load_pipeline().
    A `loaded` flag tells callers whether that has already happened in-process.
    """
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
    except Exception as e:  # pragma: no cover - depends on backend image
        return {"ready": False, "error": f"transformers/torch not available: {e}", "model": _model_ref()}

    return {
        "ready": True,
        "model": _model_ref(),
        "device": os.environ.get("ANONYMIZE_PRIVACY_FILTER_DEVICE", "cpu"),
        "loaded": _load_pipeline.cache_info().currsize > 0,
    }


@lru_cache(maxsize=1)
def _load_pipeline():
    """
    Load the privacy-filter token-classification pipeline (cached per process).

    Uses aggregation_strategy="simple" so the pipeline returns merged spans with
    character offsets (start/end) - matching what the rest of the pipeline
    expects from an EntityOccurrence. trust_remote_code=True is required because
    the model ships a custom bidirectional classification head / Viterbi decoder.
    """
    try:
        import torch
        from transformers import pipeline
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "transformers/torch not installed - cannot use the privacy-filter engine."
        ) from e

    model_ref = _model_ref()
    device_env = os.environ.get("ANONYMIZE_PRIVACY_FILTER_DEVICE", "cpu").strip().lower()
    device = 0 if (device_env == "cuda" and torch.cuda.is_available()) else -1

    logger.info(f"[Anonymize/PF] Loading privacy-filter pipeline: {model_ref} (device={'cuda' if device == 0 else 'cpu'})")
    return pipeline(
        task="token-classification",
        model=model_ref,
        aggregation_strategy="simple",
        trust_remote_code=True,
        device=device,
    )


def _merge_and_trim(text: str, spans: list[tuple[str, int, int]]) -> list[EntityOccurrence]:
    """
    Repair the two systematic artefacts of the stock HF pipeline on this model.

    1. **Fragmentation.** The model emits BIOES tags; HF's
       aggregation_strategy="simple" understands B-/I- but not E-/S-, so it
       breaks a single entity at the E-/S- boundary ("Sandra Hof" + "mann",
       "0176 123456" + "78"). We re-join consecutive spans of the same mapped
       label when the gap between them is empty or whitespace-only. Same-label
       multi-word names ("John Smith") merge correctly; distinct adjacent
       entities of the same label are rare and would be merged by Flair too.
    2. **Leading/trailing whitespace** in offsets (GPT-style tokenizers fold a
       leading space into the token, yielding " Sandra Hof"). We trim it so the
       offsets align to the actual entity text - critical because the service
       groups by exact text and rebuilds output from these offsets.
    """
    if not spans:
        return []

    spans = sorted(spans, key=lambda s: (s[1], s[2]))
    merged: list[list] = []  # [label, start, end]
    for label, start, end in spans:
        if merged and merged[-1][0] == label and text[merged[-1][2]:start].strip() == "":
            # Same label, only whitespace (or nothing) in between -> one entity.
            merged[-1][2] = max(merged[-1][2], end)
            continue
        merged.append([label, start, end])

    out: list[EntityOccurrence] = []
    for label, start, end in merged:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if end > start:
            out.append(EntityOccurrence(label=label, start=start, end=end, text=text[start:end]))
    return out


def find_privacy_filter_ner(text: str) -> list[EntityOccurrence]:
    """
    Detect PII spans with the privacy-filter model and map them onto the LLARS
    label taxonomy.

    Returns EntityOccurrence objects (same contract as find_flair_ner), so the
    caller can feed them straight into select_entities(). Spans whose native
    label has no LLARS mapping are dropped. Adjacent fragments are merged and
    whitespace trimmed (see _merge_and_trim) before returning.
    """
    if not (text or "").strip():
        return []

    clf = _load_pipeline()
    raw_spans = clf(text)

    mapped: list[tuple[str, int, int]] = []
    for span in raw_spans or []:
        native_label = str(span.get("entity_group") or span.get("entity") or "").strip().lower()
        label = PRIVACY_FILTER_LABEL_MAP.get(native_label)
        if not label:
            continue

        start = span.get("start")
        end = span.get("end")
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        # Defensive: clamp and skip empty/invalid spans (mirrors Flair handling).
        start = max(0, min(start, len(text)))
        end = max(0, min(end, len(text)))
        if end <= start:
            continue

        mapped.append((label, start, end))

    return _merge_and_trim(text, mapped)
