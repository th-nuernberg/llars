# Ranking-Szenarien in LLARS

## Übersicht

Ranking-Szenarien ermöglichen es Nutzern, mehrere Items (z.B. Zusammenfassungen eines Textes) in Qualitätskategorien zu sortieren.

## Datenmodell

```
EvaluationItem (function_type_id=1 für Ranking)
├── Messages[]
│   ├── Message 1: Quelltext (sender: "Source Article")
│   ├── Message 2: Item A (sender: "Summary A")
│   ├── Message 3: Item B (sender: "Summary B")
│   └── ...
└── Features[]  <-- WICHTIG: Das sind die rankbaren Items!
    ├── Feature 1: Summary A (type_id=Summary, llm_id=SummEval)
    ├── Feature 2: Summary B (type_id=Summary, llm_id=SummEval)
    └── ...
```

### Wichtige Tabellen

| Tabelle | Zweck |
|---------|-------|
| `evaluation_items` | Container für Ranking-Aufgabe |
| `messages` | Textinhalte (Anzeige im rechten Panel) |
| `features` | **Rankbare Items** (Anzeige im linken Panel) |
| `feature_types` | Typ des Features (z.B. "Summary") |
| `llms` | Quelle des Features (z.B. "SummEval", "GPT-4") |
| `user_feature_rankings` | Nutzer-Rankings (Bucket: Gut/Mittel/Schlecht) |

## Ranking UI

Die Ranking-Oberfläche besteht aus zwei Panels:

### Linkes Panel: Features zum Ranken
- Zeigt Features gruppiert nach FeatureType
- 4 Buckets pro FeatureType:
  - **Gut** - Hohe Qualität
  - **Mittel** - Mittlere Qualität
  - **Schlecht** - Niedrige Qualität
  - **Neutral** - Noch nicht gerankt (Standard)
- Nutzer zieht Features per Drag&Drop zwischen Buckets

### Rechtes Panel: Quelltext (NUR Kontext!)
- Zeigt NUR den Quelltext/Originalartikel als Message
- **WICHTIG:** Summaries werden NICHT als Messages erstellt!
- Summaries erscheinen NUR im linken Panel als Features
- Dient als Kontext/Referenz beim Ranken

## Daten anlegen

### 1. Demo-Daten (demo_datasets.py)

```python
RANKING_SAMPLES = [
    {
        "subject": "Summary Ranking: Artikeltitel",
        "source_text": "Der vollständige Originaltext...",
        "summaries": [
            {
                "id": "A",
                "content": "Zusammenfassung A...",
                "human_scores": {"relevance": 4.5, "avg": 4.5}
            },
            {
                "id": "B",
                "content": "Zusammenfassung B...",
                "human_scores": {"relevance": 2.0, "avg": 2.0}
            },
            # ... weitere Zusammenfassungen
        ],
        "task": "Ranken Sie die Zusammenfassungen nach Qualität"
    },
]
```

### 2. Seeding (scenarios.py)

```python
# 1. EvaluationItem erstellen
thread = EvaluationItem(
    chat_id=11000 + idx,
    institut_id=1,
    subject=sample['subject'],
    function_type_id=1  # ranking
)
db.session.add(thread)
db.session.flush()

# 2. Quelltext als Message
db.session.add(Message(
    item_id=thread.item_id,
    sender='Source Article',
    content=sample['source_text']
))

# 3. Für jede Summary: NUR Feature erstellen (NICHT Message!)
# Summaries werden NICHT als Messages erstellt - sie erscheinen nur
# im linken Panel als rankbare Items, NICHT im rechten Panel
summary_ft = FeatureType.query.filter_by(name='Summary').first()
summeval_llm = LLM.query.filter_by(name='SummEval').first()

for summary in sample['summaries']:
    # Feature für Ranking (WICHTIG!)
    # KEINE Message erstellen - nur der Quelltext soll rechts angezeigt werden
    db.session.add(Feature(
        item_id=thread.item_id,
        type_id=summary_ft.type_id,
        llm_id=summeval_llm.llm_id,
        content=summary['content']
    ))

# 4. Zu Szenario hinzufügen
st = ScenarioThreads(scenario_id=ranking_scenario.id, item_id=thread.item_id)
db.session.add(st)
```

### 3. Benötigte Stammdaten

```python
# FeatureType "Summary" muss existieren
ft = FeatureType.query.filter_by(name='Summary').first()
if not ft:
    ft = FeatureType(name='Summary')
    db.session.add(ft)

# LLM für Datenquelle (z.B. "SummEval" für SummEval-Dataset)
llm = LLM.query.filter_by(name='SummEval').first()
if not llm:
    llm = LLM(name='SummEval')
    db.session.add(llm)
```

## API Endpoints

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /api/email_threads/rankings` | Liste aller Ranking-Items |
| `GET /api/email_threads/rankings/<id>` | Einzelnes Item mit Messages & Features |
| `GET /api/email_threads/<id>/current_ranking` | Aktueller Ranking-Stand des Nutzers |
| `POST /api/save_ranking/<id>` | Ranking speichern |

## SummEval-Dataset

Das Demo verwendet das [SummEval-Dataset](https://huggingface.co/datasets/mteb/summeval):

- 100 Quell-Artikel (CNN News)
- Je 16 verschiedene System-generierte Zusammenfassungen
- Human-Ratings für: Coherence, Consistency, Fluency, Relevance
- Skala: 1-5 (5 = beste Qualität)

In LLARS werden 15 Artikel mit je 5 Zusammenfassungen verwendet (unterschiedliche Qualitätsstufen).

## Verifikation

```sql
-- Prüfen ob Features erstellt wurden
SELECT e.subject, COUNT(f.feature_id) as feature_count
FROM evaluation_items e
LEFT JOIN features f ON e.item_id = f.item_id
WHERE e.function_type_id = 1
GROUP BY e.subject
LIMIT 5;

-- Erwartetes Ergebnis: 5 Features pro Ranking-Item
```

## Häufige Fehler

### Keine Features im Ranking-Panel

**Problem**: Messages werden angezeigt, aber nichts zu ranken.

**Ursache**: Features wurden nicht erstellt - nur Messages.

**Lösung**: Für jedes rankbare Item ein Feature mit korrektem `type_id` und `llm_id` erstellen.

### Summaries werden im rechten Panel angezeigt

**Problem**: Summaries erscheinen sowohl links (Features) als auch rechts (Messages).

**Ursache**: Summaries wurden fälschlicherweise auch als Messages erstellt.

**Lösung**: Summaries NUR als Features erstellen, NICHT als Messages. Nur der Quelltext/Originalartikel soll als Message erstellt werden.

### FeatureType "Summary" nicht gefunden

**Problem**: `feature_types.get('Summary')` gibt `None` zurück.

**Ursache**: FeatureType wurde nicht in der Initialisierung hinzugefügt.

**Lösung**: 'Summary' zur FeatureType-Initialisierungsliste hinzufügen (scenarios.py, ca. Zeile 127).
