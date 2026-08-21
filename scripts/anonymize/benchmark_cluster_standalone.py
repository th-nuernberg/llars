#!/usr/bin/env python3
"""
Standalone (repo-independent) benchmark: openai/privacy-filter vs.
flair/ner-german-large, for running on the KIZ cluster.

WHY a second, standalone script
--------------------------------
`benchmark_privacy_filter_vs_flair.py` imports the LLARS anonymize service and
is meant to run inside the flask container. The cluster does NOT have the LLARS
repo, and - more importantly - flair (old transformers) and privacy-filter (new
transformers) do not coexist cleanly in one Python env. So this script:

  * has zero LLARS imports (the privacy-filter -> LLARS label map is inlined),
  * runs ONE engine per invocation and dumps detected spans to JSON,
  * has a --merge mode that loads both dumps and reports cross-engine agreement.

This lets each engine run in its own venv (flair venv vs. the transformers-5
`rq2v3` env) and still be compared apples-to-apples on the same corpus.

USAGE (on the cluster)
----------------------
    # privacy-filter in the transformers-5 env (GPU):
    python benchmark_cluster_standalone.py --engine privacy-filter --dump pf.json
    # flair in a flair venv:
    python benchmark_cluster_standalone.py --engine flair --dump flair.json
    # combine:
    python benchmark_cluster_standalone.py --merge flair.json pf.json

Each --engine run also prints timing (cold load, warm mean/p95) and per-label
counts. The merge step prints PER/LOC span agreement.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time

# privacy-filter native span types -> LLARS label taxonomy (kept in sync with
# anonymize_constants.PRIVACY_FILTER_LABEL_MAP).
PRIVACY_FILTER_LABEL_MAP = {
    "private_person": "PER",
    "private_address": "STREET",
    "private_email": "MAIL",
    "private_phone": "PHONE",
    "private_url": "URL",
    "private_date": "DATE",
    "account_number": "IBAN",
    "secret": "SECRET",
}

PRIVACY_FILTER_MODEL_ID = "openai/privacy-filter"
FLAIR_MODEL_ID = "flair/ner-german-large"

# Synthetic German counselling-style snippets - all invented PII.
DEFAULT_CORPUS: list[str] = [
    ("Guten Tag, mein Name ist Sandra Hofmann, ich bin 34 Jahre alt und wohne "
     "in der Lindenstraße 12 in 90402 Nürnberg. Mein Sohn Lukas (8) hat seit "
     "der Trennung von meinem Mann Probleme in der Schule."),
    ("Ich heiße Mehmet Yılmaz und erreiche Sie am besten unter 0176 12345678 "
     "oder mehmet.yilmaz@example.de. Der Termin am 14. März 2024 um 15:30 Uhr "
     "passt mir leider nicht."),
    ("Frau Dr. Petra Bauer aus Regensburg hat mich an die Beratungsstelle in "
     "München überwiesen. Meine Tochter Anna ist 16 und sehr zurückgezogen, "
     "seit wir im August nach Bayern gezogen sind."),
    ("Mein Partner Thomas und ich streiten oft über Geld. Wir leben in Köln, "
     "Hauptstraße 5, und ich arbeite halbtags bei der Firma Müller GmbH. Meine "
     "IBAN ist DE89 3704 0044 0532 0130 00, falls das relevant ist."),
    ("Hallo, ich bin Julia, 27, aus einem kleinen Dorf bei Leipzig. Mein "
     "Ex-Freund schreibt mir ständig auf Instagram unter dem Profil "
     "https://instagram.com/julia_l_92 und ich fühle mich bedroht."),
]


def _merge_and_trim(text: str, spans: list[dict]) -> list[dict]:
    """Re-join BIOES fragments of the same label and trim whitespace offsets.
    Mirrors anonymize_privacy_filter_detection._merge_and_trim."""
    if not spans:
        return []
    spans = sorted(spans, key=lambda s: (s["start"], s["end"]))
    merged: list[dict] = []
    for s in spans:
        if merged and merged[-1]["label"] == s["label"] and text[merged[-1]["end"]:s["start"]].strip() == "":
            merged[-1]["end"] = max(merged[-1]["end"], s["end"])
            continue
        merged.append(dict(s))
    out: list[dict] = []
    for s in merged:
        st, en = s["start"], s["end"]
        while st < en and text[st].isspace():
            st += 1
        while en > st and text[en - 1].isspace():
            en -= 1
        if en > st:
            out.append({"label": s["label"], "start": st, "end": en, "text": text[st:en]})
    return out


def _load_corpus(path: str | None) -> list[str]:
    if not path:
        return DEFAULT_CORPUS
    with open(path, "r", encoding="utf-8") as fh:
        docs = [b.strip().replace("\n", " ") for b in fh.read().split("\n\n")]
    return [d for d in docs if d] or DEFAULT_CORPUS


# ---------------------------------------------------------------- detectors

def detect_privacy_filter(corpus: list[str]) -> tuple[list[list[dict]], dict]:
    import torch
    from transformers import pipeline

    device = 0 if torch.cuda.is_available() else -1
    hw = torch.cuda.get_device_name(0) if device == 0 else "cpu"

    t0 = time.perf_counter()
    clf = pipeline(
        task="token-classification",
        model=PRIVACY_FILTER_MODEL_ID,
        aggregation_strategy="simple",
        trust_remote_code=True,
        device=device,
    )
    _ = clf(corpus[0])  # warm up / first inference
    cold = time.perf_counter() - t0

    per_doc: list[list[dict]] = []
    times: list[float] = []
    for i, text in enumerate(corpus):
        t = time.perf_counter()
        spans = clf(text)
        if i > 0:
            times.append(time.perf_counter() - t)
        mapped: list[dict] = []
        for s in spans or []:
            native = str(s.get("entity_group") or s.get("entity") or "").lower()
            label = PRIVACY_FILTER_LABEL_MAP.get(native)
            if not label:
                continue
            st, en = s.get("start"), s.get("end")
            if not isinstance(st, int) or not isinstance(en, int) or en <= st:
                continue
            mapped.append({"label": label, "start": st, "end": en, "text": text[st:en]})
        per_doc.append(_merge_and_trim(text, mapped))

    return per_doc, {"engine": "privacy-filter", "hardware": hw, "cold_s": cold, "warm_times": times}


def detect_flair(corpus: list[str]) -> tuple[list[list[dict]], dict]:
    import torch
    import flair
    from flair.models import SequenceTagger
    from flair.data import Sentence

    use_cuda = torch.cuda.is_available()
    flair.device = torch.device("cuda" if use_cuda else "cpu")
    hw = torch.cuda.get_device_name(0) if use_cuda else "cpu"

    t0 = time.perf_counter()
    tagger = SequenceTagger.load(FLAIR_MODEL_ID)
    s0 = Sentence(corpus[0])
    tagger.predict(s0)
    cold = time.perf_counter() - t0

    per_doc: list[list[dict]] = []
    times: list[float] = []
    for i, text in enumerate(corpus):
        t = time.perf_counter()
        sent = Sentence(text)
        tagger.predict(sent)
        if i > 0:
            times.append(time.perf_counter() - t)
        mapped: list[dict] = []
        for span in sent.get_spans("ner"):
            label = span.get_label("ner").value  # PER/LOC/ORG/MISC
            st, en = int(span.start_position), int(span.end_position)
            if en <= st:
                continue
            mapped.append({"label": label, "start": st, "end": en, "text": text[st:en]})
        per_doc.append(mapped)

    return per_doc, {"engine": "flair", "hardware": hw, "cold_s": cold, "warm_times": times}


# ---------------------------------------------------------------- reporting

def _report_single(per_doc: list[list[dict]], meta: dict) -> None:
    print(f"\n=== Engine: {meta['engine']}  (hardware: {meta['hardware']}) ===")
    print(f"  cold load + first inference: {meta['cold_s']:8.2f} s")
    wt = meta.get("warm_times") or []
    if wt:
        mean_ms = statistics.mean(wt) * 1000
        p95_ms = sorted(wt)[max(0, int(len(wt) * 0.95) - 1)] * 1000
        print(f"  warm inference: mean {mean_ms:7.1f} ms/doc, p95 {p95_ms:7.1f} ms/doc ({len(wt)} docs)")
    counts: dict[str, int] = {}
    for ents in per_doc:
        for e in ents:
            counts[e["label"]] = counts.get(e["label"], 0) + 1
    total = sum(counts.values())
    print(f"  detected {total} entities: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


def _overlaps(a: dict, b: dict) -> bool:
    return a["start"] < b["end"] and b["start"] < a["end"]


def _merge(flair_path: str, pf_path: str) -> None:
    with open(flair_path) as f:
        fl = json.load(f)
    with open(pf_path) as f:
        pf = json.load(f)
    fl_docs, pf_docs = fl["per_doc"], pf["per_doc"]
    _report_single(fl_docs, fl["meta"])
    _report_single(pf_docs, pf["meta"])

    print("\n=== Cross-engine span agreement (overlap-based) ===")
    for label in ("PER", "LOC"):
        ft = pt = fm = pm = 0
        for fd, pd in zip(fl_docs, pf_docs):
            fls = [e for e in fd if e["label"] == label]
            pfs = [e for e in pd if e["label"] == label]
            ft += len(fls)
            pt += len(pfs)
            fm += sum(1 for a in fls if any(_overlaps(a, b) for b in pfs))
            pm += sum(1 for a in pfs if any(_overlaps(a, b) for b in fls))
        fpct = (100.0 * fm / ft) if ft else 0.0
        ppct = (100.0 * pm / pt) if pt else 0.0
        print(f"  {label}: Flair {ft} ({fpct:.0f}% also in privacy-filter), "
              f"privacy-filter {pt} ({ppct:.0f}% also in Flair)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["flair", "privacy-filter"])
    ap.add_argument("--dump", help="Write detected spans + meta to this JSON file")
    ap.add_argument("--file", help="Optional corpus file (blank line separates docs)")
    ap.add_argument("--merge", nargs=2, metavar=("FLAIR_JSON", "PF_JSON"))
    args = ap.parse_args()

    if args.merge:
        _merge(*args.merge)
        return 0

    if not args.engine:
        ap.error("either --engine or --merge is required")

    corpus = _load_corpus(args.file)
    print(f"Corpus: {len(corpus)} documents; engine={args.engine}")

    if args.engine == "privacy-filter":
        per_doc, meta = detect_privacy_filter(corpus)
    else:
        per_doc, meta = detect_flair(corpus)

    _report_single(per_doc, meta)

    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as fh:
            json.dump({"meta": meta, "per_doc": per_doc}, fh, ensure_ascii=False, indent=2)
        print(f"\nWrote {args.dump}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
