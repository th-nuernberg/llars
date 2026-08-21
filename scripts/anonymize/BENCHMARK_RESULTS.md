# Anonymize NER Benchmark: openai/privacy-filter vs. flair/ner-german-large

**Datum:** 2026-06-03 · **Cluster:** KIZ (kiz0) · **Korpus:** 5 synthetische deutsche
Beratungs-Snippets (erfundene PII, siehe `benchmark_cluster_standalone.py`).

## Setup

| Engine | Modell | Env (transformers) | Hardware |
|--------|--------|--------------------|----------|
| privacy-filter | `openai/privacy-filter` (1.5B, 50M aktiv) | rq2v3 (5.8.1) | RTX 2080 Ti (GPU) |
| flair | `flair/ner-german-large` | flair-venv (4.57.6) | CPU (flair-torch cu130 ohne Cluster-GPU-Treiber) |

> Speed nicht 1:1 vergleichbar (GPU vs. CPU), aber beide in derselben Größenordnung.

## Ergebnisse (nach Fragmentierungs-Fix im Detector)

| Metrik | privacy-filter | flair |
|--------|----------------|-------|
| Cold-Load + 1. Inferenz | 5,8 s (Modell gecacht; 54 s beim Erst-Download) | 37,8 s |
| Warm-Inferenz (mean) | 254 ms/Dok (GPU) | 174 ms/Dok (CPU) |
| Entities gesamt | 15 | 21 |
| Labels | PER=5, STREET=4, DATE=2, MAIL/PHONE/IBAN/URL=1 | PER=9, LOC=8, ORG=4 |

Vor dem Fix waren es 26 fragmentierte Spans (`'Sandra Hof'`+`'mann'`); nach dem
Merge sind es 15 saubere Spans (`'Sandra Hofmann'`, `'0176 12345678'`,
`'mehmet.yilmaz@example.de'`, `'DE89 3704 0044 0532 0130 00'` …).

### Cross-Engine-Agreement (Span-Overlap)
- **PER**: privacy-filter 5 Spans (alle echte Personen, 100 % auch in Flair),
  Flair 9 Spans (7 echte Personen + 2 Falsch-Positive: E-Mail-Local-Part,
  URL-Fragment). Recall echte Personen: **Flair 7/7, privacy-filter 5/7**
  (verpasst *Lukas*, *Thomas*), dafür privacy-filter **0 Falsch-Positive**.
- **LOC**: 0 % — privacy-filter hat **kein Orts-Label**; Flair findet 8 (alle korrekt).

## Befunde (deutscher Beratungstext)

**Flair ist auf den entscheidenden Labels (PER, LOC) klar überlegen:**
- Saubere, **nicht-fragmentierte** Spans (`'Sandra Hofmann'`) — Voraussetzung für
  konsistente Ersetzung in LLARS.
- Erkennt **Orte** (LOC=8) → LLARS ersetzt sie durch realistische Gemeinden.
- Höhere PER-Recall.
- Falsch-Positive: tagged E-Mail-Local-Part / URL-Fragment gelegentlich als PER
  (in LLARS unkritisch, da MAIL/URL per Regex Vorrang haben).

**privacy-filter (nach Fix) — Stärken & verbleibende Schwächen auf Deutsch:**
- ✅ **Fragmentierung behoben** (`_merge_and_trim`): benachbarte Spans gleichen
  Labels werden zusammengeführt, Whitespace-Offsets getrimmt → saubere Spans,
  taugen jetzt für die konsistente Ersetzung in LLARS.
- ✅ **Keine Falsch-Positive** bei PER (Flair tagged hier E-Mail/URL-Fragmente).
- ✅ Breite native PII-Taxonomie (Mail, Phone, Date, IBAN/account, **secret**).
- ❌ **Kein LOC, kein AGE.** Städte landen via `private_address` → STREET (nur
  maskiert, keine realistische Gemeinde-Ersetzung).
- ❌ **Verfehlte deutsche Entities**: *München, Regensburg, Bayern, Leipzig, Lukas,
  Thomas, Müller GmbH* nicht erkannt — die Englisch-Zentrierung bleibt der
  limitierende Faktor (Recall echte Personen 5/7 vs. Flair 7/7).

## Empfehlung

- **Flair bleibt Default-NER für deutsche Beratungsverläufe.**
- privacy-filter ist als **4. Engine eingebaut** (opt-in), aber als Drop-in-Ersatz
  für Deutsch **nicht** geeignet. Sinnvoll höchstens als Zusatzsignal für
  MAIL/secret — was LLARS-Regex aber bereits abdeckt.
- Die Fragmentierung ist teils ein Pipeline-Aggregations-Artefakt; der native
  Viterbi-Decoder des Modells könnte sauberere Spans liefern (zusätzlicher
  Engineering-Aufwand, ändert aber nichts an fehlendem LOC/AGE).

## Reproduktion

```bash
# auf kiz (über kiz-rsync, non-interaktiv):
WORK=/nfs/scratch/staff/steigerwaldph/llars-anonbench
export HF_HOME=/nfs/scratch/staff/steigerwaldph/.cache/huggingface
# privacy-filter (GPU, transformers-5 env):
srun --partition=p0,p6 --qos=interactive --gres=gpu:1 --time=00:20:00 --mem=16G \
  /nfs/scratch/staff/steigerwaldph/envs/rq2v3/bin/python -u \
  $WORK/benchmark_cluster_standalone.py --engine privacy-filter --dump pf.json
# flair (eigenes venv, sonst transformers-Konflikt):
$WORK/flair-venv/bin/python $WORK/benchmark_cluster_standalone.py --engine flair --dump flair.json
# Vergleich:
python $WORK/benchmark_cluster_standalone.py --merge flair.json pf.json
```
