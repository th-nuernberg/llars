#!/usr/bin/env python3
"""
Benchmark: OpenAI privacy-filter vs. Flair (ner-german-large) for the LLARS
anonymize pipeline.

WHAT this measures
------------------
For a set of synthetic German counselling-style texts (no real PII), it runs
both NER engines that LLARS can plug under the anonymize pipeline and reports:

  * cold model-load time (first call, includes any download)
  * warm per-text inference time (mean / p95)
  * detected entity counts, broken down by the LLARS label taxonomy
  * cross-engine span agreement on PER and LOC (the labels that matter most for
    counselling data) - i.e. how often the two engines mark the *same* span

WHY a separate script and not a unit test
------------------------------------------
Both models are large and CPU-bound; this is a profiling/quality tool meant to
be run manually (typically inside the flask container, which already has torch,
flair and transformers installed), not in CI.

USAGE
-----
    docker exec llars_flask_service python3 /app/scripts/anonymize/benchmark_privacy_filter_vs_flair.py
    # or, with a custom corpus (one text per line, blank lines separate docs):
    docker exec llars_flask_service python3 /app/scripts/anonymize/benchmark_privacy_filter_vs_flair.py --file /tmp/cases.txt
    # only one engine:
    ... benchmark_privacy_filter_vs_flair.py --engines flair
    ... benchmark_privacy_filter_vs_flair.py --engines privacy-filter

NOTE on German quality
----------------------
privacy-filter is English-centric (its model card warns of degraded quality on
non-English text). Read the agreement numbers with that in mind: low PER/LOC
agreement on German text usually means privacy-filter missed spans Flair caught,
not the other way round.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from typing import Callable

# Allow running both as `python3 /app/scripts/...` (cwd=/app) and standalone.
sys.path.insert(0, "/app")
try:
    from services.anonymize.anonymize_entity_detection import find_flair_ner
    from services.anonymize.anonymize_privacy_filter_detection import (
        find_privacy_filter_ner,
        privacy_filter_quick_status,
    )
    from services.anonymize.anonymize_constants import EntityOccurrence
except Exception as exc:  # pragma: no cover
    print(f"[FATAL] Could not import anonymize services: {exc}")
    print("        Run this inside the flask container (cwd /app).")
    sys.exit(1)


# Synthetic German counselling-style snippets. All names/addresses/numbers are
# invented - do NOT replace with real case data when committing.
DEFAULT_CORPUS: list[str] = [
    (
        "Guten Tag, mein Name ist Sandra Hofmann, ich bin 34 Jahre alt und wohne "
        "in der Lindenstraße 12 in 90402 Nürnberg. Mein Sohn Lukas (8) hat seit "
        "der Trennung von meinem Mann Probleme in der Schule."
    ),
    (
        "Ich heiße Mehmet Yılmaz und erreiche Sie am besten unter 0176 12345678 "
        "oder mehmet.yilmaz@example.de. Der Termin am 14. März 2024 um 15:30 Uhr "
        "passt mir leider nicht."
    ),
    (
        "Frau Dr. Petra Bauer aus Regensburg hat mich an die Beratungsstelle in "
        "München überwiesen. Meine Tochter Anna ist 16 und sehr zurückgezogen, "
        "seit wir im August nach Bayern gezogen sind."
    ),
    (
        "Mein Partner Thomas und ich streiten oft über Geld. Wir leben in Köln, "
        "Hauptstraße 5, und ich arbeite halbtags bei der Firma Müller GmbH. Meine "
        "IBAN ist DE89 3704 0044 0532 0130 00, falls das relevant ist."
    ),
    (
        "Hallo, ich bin Julia, 27, aus einem kleinen Dorf bei Leipzig. Mein "
        "Ex-Freund schreibt mir ständig auf Instagram unter dem Profil "
        "https://instagram.com/julia_l_92 und ich fühle mich bedroht."
    ),
]

ENGINES: dict[str, Callable[[str], list[EntityOccurrence]]] = {
    "flair": find_flair_ner,
    "privacy-filter": find_privacy_filter_ner,
}


def _load_corpus(path: str | None) -> list[str]:
    if not path:
        return DEFAULT_CORPUS
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    # Blank line separates documents.
    docs = [block.strip().replace("\n", " ") for block in raw.split("\n\n")]
    return [d for d in docs if d] or DEFAULT_CORPUS


def _spans_for_label(entities: list[EntityOccurrence], label: str) -> list[tuple[int, int]]:
    return [(e.start, e.end) for e in entities if e.label == label]


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def _agreement(a_spans: list[tuple[int, int]], b_spans: list[tuple[int, int]]) -> int:
    """Count a_spans that overlap at least one b_span."""
    return sum(1 for a in a_spans if any(_overlaps(a, b) for b in b_spans))


def run_engine(name: str, fn: Callable[[str], list[EntityOccurrence]], corpus: list[str]):
    print(f"\n=== Engine: {name} ===")

    # Cold load = first call (model load + first inference). Timed separately so
    # the per-doc numbers below reflect warm inference only.
    t0 = time.perf_counter()
    first = fn(corpus[0])
    cold_s = time.perf_counter() - t0
    print(f"  cold load + first inference: {cold_s:8.2f} s")

    per_doc_times: list[float] = []
    results: list[list[EntityOccurrence]] = [first]
    for text in corpus[1:]:
        t = time.perf_counter()
        results.append(fn(text))
        per_doc_times.append(time.perf_counter() - t)

    if per_doc_times:
        mean_ms = statistics.mean(per_doc_times) * 1000
        p95_ms = sorted(per_doc_times)[max(0, int(len(per_doc_times) * 0.95) - 1)] * 1000
        print(f"  warm inference: mean {mean_ms:7.1f} ms/doc, p95 {p95_ms:7.1f} ms/doc ({len(per_doc_times)} docs)")

    label_counts: dict[str, int] = {}
    for ents in results:
        for e in ents:
            label_counts[e.label] = label_counts.get(e.label, 0) + 1
    total = sum(label_counts.values())
    print(f"  detected {total} entities: " + ", ".join(f"{k}={v}" for k, v in sorted(label_counts.items())))

    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Benchmark privacy-filter vs. Flair NER")
    ap.add_argument("--file", help="Optional corpus file (blank line separates docs)")
    ap.add_argument(
        "--engines",
        default="flair,privacy-filter",
        help="Comma-separated subset of: flair,privacy-filter",
    )
    args = ap.parse_args()

    corpus = _load_corpus(args.file)
    selected = [e.strip() for e in args.engines.split(",") if e.strip() in ENGINES]
    if not selected:
        print(f"[FATAL] No valid engines in '{args.engines}'. Choose from {list(ENGINES)}.")
        return 1

    print(f"Corpus: {len(corpus)} documents")
    if "privacy-filter" in selected:
        print(f"privacy-filter status: {privacy_filter_quick_status()}")

    results: dict[str, list[list[EntityOccurrence]]] = {}
    for name in selected:
        try:
            results[name] = run_engine(name, ENGINES[name], corpus)
        except Exception as exc:
            print(f"  [ERROR] engine '{name}' failed: {exc}")

    # Cross-engine agreement (only if both ran).
    if "flair" in results and "privacy-filter" in results:
        print("\n=== Cross-engine span agreement (overlap-based) ===")
        for label in ("PER", "LOC"):
            flair_total = pf_total = flair_matched = pf_matched = 0
            for fl_ents, pf_ents in zip(results["flair"], results["privacy-filter"]):
                fl = _spans_for_label(fl_ents, label)
                pf = _spans_for_label(pf_ents, label)
                flair_total += len(fl)
                pf_total += len(pf)
                flair_matched += _agreement(fl, pf)
                pf_matched += _agreement(pf, fl)
            fl_pct = (100.0 * flair_matched / flair_total) if flair_total else 0.0
            pf_pct = (100.0 * pf_matched / pf_total) if pf_total else 0.0
            print(
                f"  {label}: Flair found {flair_total} ({fl_pct:.0f}% also found by privacy-filter), "
                f"privacy-filter found {pf_total} ({pf_pct:.0f}% also found by Flair)"
            )

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
