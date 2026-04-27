# RQ2: Adaptation Hierarchy — Projektplan

**Forschungsfrage:** In sensitive domains where annotated data is scarce and quality criteria are subjective, when does prompt optimization reach its performance ceiling — and what marginal quality gains does escalation to preference alignment and fine-tuning yield relative to the additional data and oversight cost?

**Zeitraum:** WP6 im Exposé — Q3 2026 bis Q2 2027
**Infrastruktur:** TH Nürnberg GPU-Cluster + LLARS-APIs für Evaluation
**Geplante Publikation:** 1 Paper (Conference TBD)

---

## 1. Kernhypothese

Es gibt eine messbare **Prompt-Engineering-Ceiling** — einen Punkt, ab dem bessere Prompts keine signifikanten Qualitätsverbesserungen mehr bringen. Die zentrale Frage ist, ob und wann Escalation zu DPO oder Fine-Tuning diesen Ceiling durchbricht und welchen Mehrkosten (Daten, Compute, Oversight) dem gegenüberstehen.

```
Erwartete Qualitätskurve:

Quality ▲
        │          ┌─── Fine-Tuning
        │         ╱
        │    ┌───╱──── DPO
        │   ╱  ╱
        │  ╱  ╱  ┌──── Prompt Ceiling
        │ ╱  ╱  ╱
        │╱  ╱──╱
        │  ╱
        │ ╱
        └──────────────────────► Effort / Data
         Prompt    DPO    SFT
```

## 2. Experimentelles Design

### 2.1 Unabhängige Variablen

| Variable | Stufen | Beschreibung |
|----------|--------|-------------|
| **Adaptation Level** | `prompt`, `dpo`, `finetune` | Hierarchie-Stufen |
| **Model** | 3-4 Modelle | z.B. Mistral-Small-3.2, Llama-3.1-8B, Qwen-2.5-7B |
| **Domain** | TBOC + 2 Public Benchmarks | Generalisierbarkeit |
| **Prompt Complexity** | 3-5 Varianten pro Level | Baseline → Chain-of-Thought → Few-Shot → Optimized |
| **Data Budget** | 50, 200, 500, 1000 Samples | Für DPO/FT: Wie viel Daten braucht Escalation? |

### 2.2 Abhängige Variablen

| Metrik | Messung | Tool |
|--------|---------|------|
| **Task Quality** | Multi-dimensionale Likert-Scores (Kohärenz, Relevanz, Fluency, Konsistenz) | LLM-as-Judge (kalibriert via RQ1) |
| **Agreement** | Krippendorff's α zwischen Judge-Runs | scipy / eigene Berechnung |
| **Marginal Gain** | Δ Quality pro Escalation-Stufe | Paired significance tests |
| **Cost** | GPU-Stunden, Datenpunkte, Annotationsaufwand | Logging |
| **Ceiling Detection** | Stagnation über k Prompt-Varianten | Statistischer Test (siehe 4.3) |

### 2.3 Kontrollen

- **Gleicher Judge** für alle Stufen (kein Evaluator-Wechsel zwischen Levels)
- **Gleiche Test-Splits** über alle Bedingungen
- **Multiple Runs** (n=3-5) pro Konfiguration für Varianzschätzung
- **Blind Evaluation** — Judge kennt weder Prompt noch Adaptation-Level

## 3. Daten

### 3.1 Primärdomain: TBOC (Text-Based Online Counselling)

| Dataset | Beschreibung | Verfügbarkeit |
|---------|-------------|---------------|
| TBOC-Anon | Anonymisierte Beratungsgespräche | Vorhanden (TH Nürnberg) |
| TBOC-RP | Rollenspiel-Transkripte | Vorhanden |
| TBOC-Synth | Synthetische Dialoge (LLM-generiert) | Generierbar via LLARS |

**Task:** Informationsextraktion aus Gesprächsverläufen — Zusammenfassungen, Themenidentifikation, Handlungsempfehlungen.

### 3.2 Public Benchmarks (Generalisierbarkeit)

| Benchmark | Domain | Task | Warum relevant |
|-----------|--------|------|---------------|
| **SummEval** | News | Summarization | Multi-dimensionale Bewertung, kein Ground Truth nötig |
| **MT-Bench** | General | Instruction Following | Etablierter LLM-as-Judge Benchmark |
| **CounselChat** / **MEMO** | Mental Health | Counselling QA | Closest public proxy zu TBOC |

### 3.3 Daten für DPO / Fine-Tuning

```
Preference-Paare für DPO:
  - Aus LLARS Evaluation: Ranking-Daten (Bucket-Zuordnungen) → Preference Pairs
  - Aus LLM-as-Judge: Paarweise Vergleiche → chosen/rejected
  - Budget-Experiment: 50 → 200 → 500 → 1000 Paare

SFT-Daten:
  - Top-bewertete Outputs aus Prompt-Phase als Gold-Standard
  - Optional: Experten-korrigierte Outputs
```

## 4. Methodik

### 4.1 Phase 1: Prompt-Ceiling-Detektion

```
Für jedes Modell m ∈ M:
  1. Baseline-Prompt → Evaluate → Score s₀
  2. Iterativ bessere Prompts (CoT, Few-Shot, Optimized):
     p₁, p₂, ..., pₖ → Scores s₁, s₂, ..., sₖ
  3. Ceiling erreicht wenn:
     Δsᵢ = sᵢ - sᵢ₋₁ < ε für j aufeinanderfolgende Iterationen
     (Wilcoxon signed-rank test, p > α)
```

**Prompt-Optimierungsstrategien:**
1. Manual prompt engineering (Baseline, CoT, Few-Shot)
2. OPRO-style LLM-gestützte Optimierung
3. DSPy-Compilation (als Vergleich)

### 4.2 Phase 2: Escalation Experiments

```
Für jedes Modell m das den Ceiling erreicht hat:
  Für jeden Data-Budget b ∈ {50, 200, 500, 1000}:
    1. DPO-Training mit b Preference-Paaren → Evaluate
    2. SFT mit b Gold-Samples → Evaluate
    3. DPO + bester Prompt (Prompt bleibt!) → Evaluate
    4. SFT + bester Prompt → Evaluate
```

**Wichtig:** Prompt-Optimierung wird *nach* DPO/SFT nochmal angewendet — Lyu et al. (2024) zeigen additive Gains.

### 4.3 Statistische Analyse

| Test | Zweck |
|------|-------|
| **Wilcoxon signed-rank** | Paarvergleich prompt vs. DPO vs. SFT (non-parametric, paired) |
| **Friedman test** | Vergleich über alle 3 Stufen (repeated measures) |
| **Effect size (Cliff's δ)** | Praktische Relevanz der Unterschiede |
| **Bootstrap CI** | Konfidenzintervalle für Qualitätsmetriken |
| **Ceiling-Kriterium** | Δ < ε über k Schritte bei Signifikanzniveau α |

### 4.4 Cost-Benefit-Analyse

```
Für jede Escalation-Stufe:
  - Marginal Quality Gain: Δq = q_new - q_prompt_ceiling
  - Marginal Cost: GPU-Stunden + Datenannotation + Oversight-Aufwand
  - Efficiency Ratio: Δq / ΔCost
  → Wann lohnt sich Escalation? (Pareto-Analyse)
```

## 5. Projektstruktur

```
rq2-adaptation-hierarchy/
├── pyproject.toml                 # Dependencies (uv/pip)
├── Makefile                       # make run, make eval, make analyze
├── README.md
│
├── configs/
│   ├── models.yaml                # Model-Registry
│   ├── prompts/                   # Prompt-Templates (.txt / .jinja2)
│   │   ├── baseline_v1.txt
│   │   ├── cot_v1.txt
│   │   ├── fewshot_v1.txt
│   │   └── optimized_v3.txt
│   └── experiments/               # Ein YAML pro Experiment
│       ├── prompt_sweep_tboc.yaml
│       ├── prompt_sweep_summeval.yaml
│       ├── dpo_mistral_tboc.yaml
│       ├── sft_llama_tboc.yaml
│       └── full_hierarchy_tboc.yaml
│
├── src/rq2/
│   ├── __init__.py
│   ├── data/
│   │   ├── loader.py              # TBOC + Benchmark Datensätze
│   │   └── splits.py              # Stratified Train/Val/Test
│   ├── adapt/
│   │   ├── prompt.py              # Prompt-only Generation (via LiteLLM)
│   │   ├── dpo.py                 # DPO-Training (HuggingFace TRL)
│   │   └── finetune.py            # SFT-Training (HuggingFace TRL)
│   ├── generate.py                # Batch-Generation: Config → Outputs
│   ├── evaluate.py                # LLM-as-Judge + optional LLARS-API
│   └── analysis/
│       ├── stats.py               # Significance Tests, Effect Sizes
│       ├── ceiling.py             # Ceiling-Detection Algorithmus
│       └── plots.py               # Publikationsreife Figures
│
├── scripts/
│   ├── run_experiment.py          # CLI: config → generate → evaluate → analyze
│   └── cluster/
│       ├── submit.sh              # SLURM Wrapper
│       └── templates/
│           ├── gpu_job.sh         # DPO/SFT Training
│           └── cpu_job.sh         # Evaluation/Analysis
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_prompt_ceiling.ipynb    # Hauptanalyse Phase 1
│   ├── 03_escalation_gains.ipynb  # Hauptanalyse Phase 2
│   └── 04_cost_benefit.ipynb      # Pareto-Analyse
│
├── tests/
│   ├── test_loader.py
│   ├── test_evaluate.py
│   └── test_stats.py
│
└── results/                       # .gitignored, Symlink zu Cluster-Storage
    └── .gitkeep
```

### Config-Format (Beispiel)

```yaml
# configs/experiments/prompt_sweep_tboc.yaml
experiment: prompt_sweep_tboc
description: "Prompt-Ceiling Detektion auf TBOC-Daten"

dataset:
  name: tboc_counselling
  split: test_v1
  max_samples: 200

models:
  - id: mistral-small-3.2-24b
    provider: litellm
    api_model: mistralai/Mistral-Small-3.2-24B-Instruct-2506
  - id: llama-3.1-8b
    provider: litellm
    api_model: meta-llama/Llama-3.1-8B-Instruct

prompts:
  - configs/prompts/baseline_v1.txt
  - configs/prompts/cot_v1.txt
  - configs/prompts/fewshot_v1.txt
  - configs/prompts/optimized_v3.txt

evaluation:
  method: llm_as_judge
  judge_model: gpt-5-mini
  dimensions:
    - {id: coherence, weight: 0.25}
    - {id: fluency, weight: 0.25}
    - {id: relevance, weight: 0.25}
    - {id: consistency, weight: 0.25}
  scale: {min: 1, max: 5}

runs: 3
seed: 42
output_dir: results/prompt_sweep_tboc
```

### Dependencies

```toml
[project]
name = "rq2-adaptation-hierarchy"
requires-python = ">=3.11"

dependencies = [
    # LLM Interaction
    "litellm>=1.40",           # Unified API (wie in LLARS)
    "jinja2",                  # Prompt Templates

    # Training
    "trl>=0.12",               # DPO + SFT
    "transformers>=4.45",
    "datasets",
    "peft",                    # LoRA Adapter
    "accelerate",              # Multi-GPU
    "bitsandbytes",            # Quantization

    # Evaluation & Analysis
    "scipy",                   # Statistical tests
    "scikit-learn",            # Metrics
    "pandas",
    "numpy",

    # Visualization
    "matplotlib",
    "seaborn",

    # Infrastructure
    "pyyaml",
    "click",                   # CLI
    "tqdm",
    "wandb",                   # Experiment Tracking
]

[project.optional-dependencies]
cluster = ["submitit"]
notebooks = ["jupyterlab", "ipywidgets"]
dev = ["pytest", "ruff"]
```

## 6. Zeitplan (WP6 Detail)

```
Q3 2026 (Jul-Sep)  — Setup & Phase 1
├── Woche 1-2:   Projektstruktur, Data Loader, Cluster-Integration
├── Woche 3-4:   Prompt-Baseline (3 Modelle × 3 Prompts × TBOC)
├── Woche 5-6:   Prompt-Optimierung (OPRO-style, DSPy-Vergleich)
├── Woche 7-8:   Ceiling-Analyse, Public Benchmarks
└── Woche 9-10:  Zwischenauswertung Phase 1, Preference-Daten sammeln

Q4 2026 (Okt-Dez) — Phase 2 & Analyse
├── Woche 1-3:   DPO-Experimente (Modelle × Data Budgets)
├── Woche 4-6:   SFT-Experimente + Prompt-Reoptimierung nach Training
├── Woche 7-8:   Cost-Benefit-Analyse, Pareto-Plots
├── Woche 9-10:  Cross-Domain Validierung (Public Benchmarks)
└── Woche 11-12: Statistische Konsolidierung

Q1 2027 (Jan-Mär) — Paper
├── Woche 1-3:   Paper Draft
├── Woche 4-6:   Revision, Figures finalisieren
└── Woche 7-8:   Submission
```

## 7. Erwartete Ergebnisse & Contribution

### Primärer Beitrag

1. **Empirischer Nachweis** einer Prompt-Engineering-Ceiling in sensitiven Domains
2. **Quantifizierte Escalation-Gains** (Δq pro Stufe) mit statistischer Signifikanz
3. **Cost-Efficiency-Analyse** — wann lohnt sich DPO/SFT gegenüber Prompt-Optimierung?
4. **Data-Budget-Kurven** — wie viele Preference-Paare/Gold-Samples braucht man minimal?

### Erwartete Findings (Hypothesen)

| Hypothese | Basis |
|-----------|-------|
| H1: Prompt-Ceiling wird nach 5-8 systematischen Varianten erreicht | Eigene Vorerfahrung aus LLARS-Evaluierungen |
| H2: DPO bringt 10-20% Gain über Ceiling bei 200+ Preference-Paaren | DPO-Literatur (Rafailov et al., 2023) |
| H3: SFT bringt weitere 5-15% Gain, aber braucht 500+ Samples | Steigerwald & Albrecht (2025) — Open-Source vs. Proprietary Gap |
| H4: Prompt + DPO/SFT kombiniert > einzeln (additiver Effekt) | Lyu et al. (2024), Shin et al. (2025) |
| H5: Gains sind domain-abhängig — sensitiver = größerer DPO-Vorteil | Neue Hypothese |

### Paper-Outline (vorläufig)

```
1. Introduction — Adaptation as Configuration Challenge
2. Related Work — Prompt Eng. / DPO / SFT / Evaluation
3. Method
   3.1 Experimental Setup
   3.2 Ceiling Detection Protocol
   3.3 Escalation Framework
   3.4 Cost-Benefit Analysis
4. Experiments
   4.1 Phase 1: Prompt Ceiling (TBOC + Benchmarks)
   4.2 Phase 2: Escalation Gains (DPO, SFT, Combined)
   4.3 Data Budget Analysis
5. Results
6. Discussion — When to Escalate? Decision Framework
7. Conclusion
```

## 8. Risiken & Mitigation

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|-------------------|------------|
| TBOC-Daten nicht ausreichend für SFT | Mittel | Synthetische Daten via LLARS + Public Benchmarks als Fallback |
| Kein signifikanter Ceiling-Effekt | Niedrig | Dann ist das ein Finding — Prompt-Optimierung konvergiert nicht |
| DPO-Training instabil bei kleinen Budgets | Mittel | LoRA + konservative Hyperparameter, mehrere Seeds |
| GPU-Cluster nicht verfügbar | Niedrig | Quantisierte Modelle (4-bit), kleinere Modelle als Fallback |
| LLM-as-Judge Bias verfälscht Vergleich | Mittel | Multiple Judges + Human-Validation-Subset (→ RQ1 Synergie) |

## 9. Schnittstelle zu LLARS

```
LLARS (Production System)          RQ2 (Research Project)
┌─────────────────────┐            ┌──────────────────────┐
│ Evaluation Data     │───export──→│ data/loader.py       │
│ (Rankings, Ratings) │            │ (Preference Pairs)   │
│                     │            │                      │
│ LLM-as-Judge API    │←──call────│ evaluate.py          │
│ /api/llm/evaluate   │            │ (Evaluation Runs)    │
│                     │            │                      │
│ Prompt Templates    │───export──→│ configs/prompts/     │
│ (Prompt Eng. UI)    │            │ (Template Files)     │
└─────────────────────┘            └──────────────────────┘
```

- **LLARS liefert:** Daten, Evaluation-Infrastruktur, Prompt-Templates
- **RQ2 liefert:** Trainierte Modelle, Ceiling-Metriken, Escalation-Policies (→ Input für RQ3)
- **Kein Code-Sharing** — RQ2 ist ein eigenständiges Repo, kommuniziert über APIs und Dateien

      ▼
    Generation + Judge (wie oben)
    ──► evaluations/pointwise_sft_200__dspy.jsonl

    × 4 Budgets

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                  STUFE 5: KOMBINATIONEN
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    SFT → dann DPO drauf    ──► adapter/sft_dpo_200/   + bester Prompt
    SFT → dann GRPO drauf   ──► adapter/sft_grpo_200/  + bester Prompt

    Jeweils Generation + Judge

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                  LEADERBOARD (alles zusammen)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Alle Evaluations einsammeln ──► leaderboard.md

    | Rank | Konfiguration              | Budget | Coh  | Rel  | Flu  | Con  | Overall |
    |------|----------------------------|--------|------|------|------|------|---------|
    |  1   | SFT+GRPO + DSPy-Prompt     | 1000   | 4.6  | 4.5  | 4.7  | 4.4  |  4.55   |
    |  2   | GRPO + DSPy-Prompt         | 1000   | 4.3  | 4.2  | 4.5  | 4.1  |  4.28   |
    |  3   | DPO + DSPy-Prompt          | 1000   | 4.1  | 4.0  | 4.3  | 3.9  |  4.08   |
    |  4   | SFT + DSPy-Prompt          | 500    | 4.0  | 3.9  | 4.2  | 3.8  |  3.98   |
    |  5   | DSPy-Prompt only           |   -    | 3.7  | 3.6  | 3.9  | 3.6  |  3.70   | ◄ Ceiling
    |  6   | OPRO-Prompt only           |   -    | 3.7  | 3.5  | 3.8  | 3.6  |  3.65   |
    |  7   | Few-Shot only              |   -    | 3.6  | 3.5  | 3.7  | 3.5  |  3.58   |
    |  8   | CoT only                   |   -    | 3.4  | 3.3  | 3.5  | 3.3  |  3.38   |
    |  9   | DPO + Zero-Shot (kein PE)  | 200    | 3.3  | 3.2  | 3.4  | 3.2  |  3.28   |
    | 10   | Zero-Shot only             |   -    | 3.1  | 3.0  | 3.2  | 3.0  |  3.08   |

    + Significance Tests (Wilcoxon) zwischen benachbarten Raengen
    + Ceiling-Kurve als Plot

  Zusammenfassung: Was passiert alles?

  Generierung:  ~30 Konfigurationen × 50 Posts = ~1500 TL;DRs
                (5 Prompts + 4×4 DPO-Budgets + 4×4 GRPO + 4×4 SFT + Combos)

  Evaluation:   ~1500 × Judge-Call = ~1500 Pointwise-Bewertungen

  Training:     ~12 Adapter (DPO×4 + GRPO×4 + SFT×4 Budgets)
                + ~4 Combo-Adapter (SFT→DPO, SFT→GRPO)
