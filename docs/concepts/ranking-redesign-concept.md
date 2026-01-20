# Ranking Redesign Konzept

**Status:** Entwurf | **Stand:** Januar 2026

---

## Teil 1: LLM Ranking Prompt - Analyse & Fix

### Aktueller Zustand (Problem)

Der aktuelle Ranking-Prompt in `llm_ai_task_runner.py` hat mehrere Probleme:

```python
# Aktuell (Zeile 649-658):
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

**Probleme:**

| Problem | Beschreibung | Auswirkung |
|---------|--------------|------------|
| Kein Kontext | Source-Text (Original-Artikel) wird nicht mitgeliefert | LLM kann Qualität nicht beurteilen |
| Falsche Kriterien | Prompt für "Beratungsgespräche" statt Summaries | Unpassende Bewertungskriterien |
| Fehlende Metrik-Beschreibung | Keine Erklärung was "gut/mittel/schlecht" bedeutet | Inkonsistente Bewertungen |

### Lösung: Kontext-basierter Prompt

```python
# NEU: Mit Source-Text und klaren Kriterien
def _run_ranking(model_id: str, thread_ids: Iterable[int], scenario_id: int) -> None:
    # ... bestehender Code ...

    for thread_id in thread_ids:
        # NEU: Hole auch die Messages (Source-Text)
        messages = Message.query.filter_by(item_id=thread_id).all()
        source_text = next(
            (m.content for m in messages if m.sender == "Source Article"),
            None
        )

        features = Feature.query.filter_by(item_id=thread_id).all()
        # ... shuffle features ...

        # NEU: Kontext-basierter Prompt
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

### Änderungen in `llm_ai_task_runner.py`

| Datei | Zeile | Änderung |
|-------|-------|----------|
| `llm_ai_task_runner.py` | 624 | Messages laden: `messages = Message.query.filter_by(item_id=thread_id).all()` |
| `llm_ai_task_runner.py` | 625+ | Source-Text extrahieren |
| `llm_ai_task_runner.py` | 649-658 | Neuer Prompt mit Kontext und Kriterien |

---

## Teil 2: Rater/Ranker UI Redesign

### Aktueller Zustand

**URL:** `/Rater/:id` → `RankerDetail.vue`

**Aktuelles Layout:**
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

### Probleme mit aktuellem UI

| Problem | Beschreibung |
|---------|--------------|
| **Redundanz** | Summaries erscheinen links (Features) UND rechts (Messages) - verwirrend |
| **Horizontales Layout** | 3 Buckets nebeneinander = wenig Platz pro Bucket |
| **Expansion Panel** | Umständlich bei nur einem Feature-Typ |
| **"E-Mail Verlauf"** | Irreführender Name für Summary-Szenarien |
| **Keine Nummerierung** | Items sind schwer zu referenzieren |

### Neues Konzept: Summary-optimiertes Layout

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

### Neue Komponenten-Struktur

```
views/Evaluation/
├── RankingSession.vue          # NEU: Haupt-Container
│   ├── components/
│   │   ├── SourceTextPanel.vue # NEU: Kollabierbare Quelltextanzeige
│   │   ├── RankingBuckets.vue  # NEU: Vertikale Bucket-Liste
│   │   ├── RankingItem.vue     # NEU: Einzelnes Item mit ID-Badge
│   │   └── RankingProgress.vue # NEU: Fortschrittsanzeige
│   └── composables/
│       ├── useRankingSession.js
│       └── useRankingDragDrop.js
```

### Design-Änderungen

| Element | Alt | Neu |
|---------|-----|-----|
| **Layout** | 2 Spalten (Features + Messages) | 1 Spalte (Source oben, Buckets unten) |
| **Buckets** | 3 horizontal + 1 Neutral unten | 4 vertikal gestapelt |
| **Items** | Ohne ID | Mit alphabetischer ID (A, B, C...) |
| **Source** | Rechtes Panel "E-Mail Verlauf" | Kollabierbare Box oben |
| **Panel-Titel** | "E-Mail Verlauf" | "Originaltext" |
| **Empty State** | Keine Anleitung | "Items hierher ziehen" |

### Responsives Verhalten

**Desktop (>1200px):**
```
┌──────────────────────────────────────────────┐
│ Source (50%)    │    Buckets (50%)           │
└──────────────────────────────────────────────┘
```

**Tablet/Mobile (<1200px):**
```
┌──────────────────────────────────────────────┐
│ Source (kollabiert, expandierbar)            │
├──────────────────────────────────────────────┤
│ Buckets (100%)                               │
└──────────────────────────────────────────────┘
```

---

## Teil 3: Implementierungsplan

### Phase 1: LLM Prompt Fix (Priorität: Hoch)

1. `llm_ai_task_runner.py` anpassen:
   - Messages für Thread laden
   - Source-Text extrahieren
   - Neuen Prompt mit Kontext erstellen

2. Prompt-Template aktualisieren:
   - `prompt_template_service.py` für konfigurierbaren Ranking-Prompt
   - Variable `{source_text}` hinzufügen

### Phase 2: UI Redesign (Priorität: Mittel)

1. Neue Komponenten erstellen:
   - `SourceTextPanel.vue`
   - `RankingBuckets.vue`
   - `RankingItem.vue`

2. `RankerDetail.vue` refactoren:
   - Neues Layout implementieren
   - Vertikale Buckets
   - Item-IDs (A, B, C...)

3. Routing anpassen:
   - `/scenarios/:id/evaluate/ranking` statt `/Rater/:id`
   - Integration in ScenarioWorkspace

### Phase 3: Testing & Dokumentation

1. E2E-Tests für Ranking-Flow
2. Unit-Tests für Prompt-Generierung
3. Dokumentation aktualisieren

---

## Metriken für Erfolg

| Metrik | Aktuell | Ziel |
|--------|---------|------|
| LLM Ranking-Qualität | Nicht messbar (kein Kontext) | Inter-Rater-Agreement >0.6 |
| UI Verständlichkeit | Unklar (Summary-Redundanz) | Single Source of Truth |
| Mobile Nutzbarkeit | Eingeschränkt | Voll funktional |

---

## Offene Fragen

1. **Szenario-spezifische Prompts:** Soll der Prompt je nach Szenario-Typ (Summary, Features, etc.) anpassbar sein?
2. **LLM-Reasoning:** Soll die LLM-Begründung für das Ranking dem User angezeigt werden?
3. **Ground Truth:** Sollen die Human-Scores aus SummEval als Referenz angezeigt werden?
