# Ranking Redesign Concept

**Status:** Draft | **As of:** January 2026

---

## Part 1: LLM Ranking Prompt - Analysis & Fix

### Current state (problem)

The current ranking prompt in `llm_ai_task_runner.py` has multiple issues:

```python
# Current (line 649-658):
system_prompt = (
    "Du bist ein strenger Evaluator für Feature-Rankings. "
    "Antworte ausschließlich im JSON-Format."
)
user_prompt = (
    "Ordne alle Feature-IDs genau einmal einem Bucket zu. "
    f"Erlaubte Buckets: {buckets_list}.\n"
    f"Gib JSON im Format:\n{json_example}\n\n"
    "Features (zufällig sortiert):\n"
    + "\n".join(feature_lines)
)
```

**Problems:**

| Problem | Description | Impact |
|---------|-------------|--------|
| No context | Source text (original article) is missing | LLM cannot judge quality |
| Wrong criteria | Prompt for "consultation calls" instead of summaries | Wrong evaluation criteria |
| Missing metric explanation | No definition of "good/medium/bad" | Inconsistent ratings |

### Solution: Context‑based prompt

```python
# NEW: With source text and clear criteria
def _run_ranking(model_id: str, thread_ids: Iterable[int], scenario_id: int) -> None:
    # ... existing code ...

    for thread_id in thread_ids:
        # NEW: Also fetch messages (source text)
        messages = Message.query.filter_by(item_id=thread_id).all()
        source_text = next(
            (m.content for m in messages if m.sender == "Source Article"),
            None
        )

        features = Feature.query.filter_by(item_id=thread_id).all()
        # ... shuffle features ...

        # NEW: Context‑based prompt
        system_prompt = """Du bist ein Experte für die Bewertung von Textzusammenfassungen.
Deine Aufgabe ist es, Summaries nach ihrer Qualität zu ranken.

Bewertungskriterien (nach SummEval):
- **Kohärenz**: Logischer Aufbau und Zusammenhang der Sätze
- **Konsistenz**: Faktentreue zum Originaltext (keine Halluzinationen)
- **Flüssigkeit**: Grammatik, Lesbarkeit, natürlicher Sprachfluss
- **Relevanz**: Wichtigste Informationen des Originals erfasst

Antworte AUSSCHLIESSLICH im JSON-Format."""

        user_prompt = f"""Bewerte die folgenden Summaries basierend auf dem Originaltext.

ORIGINALTEXT:
{source_text}

SUMMARIES (zufällig sortiert):
{feature_lines}

Ordne jede Summary-ID einem Bucket zu:
- **gut**: Erfasst Kerninhalt, faktisch korrekt, gut lesbar
- **mittel**: Akzeptabel, aber mit Schwächen (fehlende Details, leichte Fehler)
- **schlecht**: Unvollständig, faktisch falsch, oder schlecht lesbar

JSON-Format:
{json_example}"""
```

### Changes in `llm_ai_task_runner.py`

| File | Line | Change |
|------|------|--------|
| `llm_ai_task_runner.py` | 624 | Load messages: `messages = Message.query.filter_by(item_id=thread_id).all()` |
| `llm_ai_task_runner.py` | 625+ | Extract source text |
| `llm_ai_task_runner.py` | 649-658 | New prompt with context and criteria |

---

## Part 2: Rater/Ranker UI Redesign

### Current state

**URL:** `/Rater/:id` → `RankerDetail.vue`

**Current layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ ← Ranking    Summary Ranking: Siberian Wildfires    Thread #55│
├────────────────────────────────┬─────────────────────────────┤
│ ☰ Features                     │ ✉ E-Mail Verlauf            │
│                                │                             │
│ ▼ Zusammenfassung              │ Source Article (15:34)      │
│ ┌────┐ ┌────┐ ┌────┐          │ (CNN) A fiery sunset...     │
│ │Gut │ │Mit-│ │Sch-│          │                             │
│ │    │ │tel │ │lec-│          │ Summary A (16:34)           │
│ │Item│ │    │ │ht  │          │ ...                         │
│ │    │ │Item│ │    │          │                             │
│ └────┘ └────┘ └────┘          │ Summary B (17:34)           │
│                                │ ...                         │
│ ┌──────────────────────┐      │                             │
│ │ Neutral              │      │ Summary C (18:34)           │
│ │ [Item] [Item]        │      │ ...                         │
│ └──────────────────────┘      │                             │
└────────────────────────────────┴─────────────────────────────┘
```

### Problems with the current UI

| Problem | Description |
|---------|-------------|
| **Redundancy** | Summaries appear left (features) and right (messages) - confusing |
| **Horizontal layout** | 3 buckets side‑by‑side = little space per bucket |
| **Expansion panel** | Awkward with a single feature type |
| **"E‑mail history"** | Misleading label for summary scenarios |
| **No numbering** | Items are hard to reference |

### New concept: Summary‑optimized layout

```
┌──────────────────────────────────────────────────────────────┐
│ ← Ranking    Summary Ranking: Siberian Wildfires     1/15 ▶ │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 ORIGINALTEXT                                    [−][□]  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ (CNN) A fiery sunset greeted people in Washington     │ │
│  │ Sunday. The deep reddish color caught Seattle native  │ │
│  │ Tim Durkan's eye... [mehr anzeigen]                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📝 SUMMARIES RANKEN                          5 von 5 sortiert│
│  ┌────────────────────────────────────────────────────────┐ │
│  │                                                        │ │
│  │  ┌─ GUT ──────────────────────────────────────────┐  │ │
│  │  │  A  (CNN) A fiery sunset greeted people...     │  │ │
│  │  │  D  Stunning sunsets were the result of...     │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  ┌─ MITTEL ───────────────────────────────────────┐  │ │
│  │  │  B  A fiery sunset greeted people...           │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  ┌─ SCHLECHT ─────────────────────────────────────┐  │ │
│  │  │  (leer - Items hierher ziehen)                 │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  ┌─ UNBEWERTET ───────────────────────────────────┐  │ │
│  │  │  C  Raging wildfires in parts of Siberia...    │  │ │
│  │  │  E  The deep reddish color caught Seattle...   │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Speichern] [Zurücksetzen]                    Auto-Save: ✓ │
└──────────────────────────────────────────────────────────────┘
```

### New component structure

```
views/Evaluation/
├── RankingSession.vue          # NEW: main container
│   ├── components/
│   │   ├── SourceTextPanel.vue # NEW: collapsible source text
│   │   ├── RankingBuckets.vue  # NEW: vertical bucket list
│   │   ├── RankingItem.vue     # NEW: item with ID badge
│   │   └── RankingProgress.vue # NEW: progress indicator
│   └── composables/
│       ├── useRankingSession.js
│       └── useRankingDragDrop.js
```

### Design changes

| Element | Old | New |
|---------|-----|-----|
| **Layout** | 2 columns (features + messages) | 1 column (source top, buckets below) |
| **Buckets** | 3 horizontal + 1 neutral bottom | 4 stacked vertically |
| **Items** | No IDs | Alphabetical ID (A, B, C...) |
| **Source** | Right panel "E‑mail history" | Collapsible box on top |
| **Panel title** | "E‑mail history" | "Original text" |
| **Empty state** | No guidance | "Drag items here" |

### Responsive behavior

**Desktop (>1200px):**
- Full width, all buckets visible
- Source panel expandable

**Tablet (768‑1200px):**
- Source panel collapses by default
- Buckets reduce height

**Mobile (<768px):**
- Source text becomes full‑screen modal
- Buckets stacked with scroll

---

## Part 3: Auto‑Save and Validation

### Auto‑Save

- Save on each drag/drop
- Save after each rating
- UI indicator for save state

### Validation

- All items must be placed into a bucket before completion
- Warn if bucket is empty

---

## Part 4: Migration Strategy

1. Build new components in parallel
2. Feature flag to switch UI
3. User testing and rollout

---

## Open Questions

- Keep or remove old layout?
- Should we allow custom bucket labels?
- Should we allow ties across buckets?

---

## Status

**Concept only.** No implementation yet.
