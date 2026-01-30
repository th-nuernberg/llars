# Konzept: Self-Testing für den Szenario Manager

**Version:** 1.0
**Datum:** 16. Januar 2026
**Status:** Genehmigt

---

## 1. Übersicht

Dieses Dokument beschreibt die Infrastruktur zum automatischen Testen des Szenario Managers und Wizards mit verschiedenen öffentlichen Datensätzen. Ziel ist es, Entwicklern und Forschern zu ermöglichen, schnell realistische Testszenarien zu erstellen.

### 1.1 Ziele

- Automatisches Herunterladen von öffentlichen NLP-Datensätzen
- Transformation in LLARS-kompatibles Format
- Schnelles Erstellen von Test-Szenarien via API
- Demo-Daten für neue Benutzer bereitstellen

### 1.2 Nicht-Ziele

- Produktions-Daten verarbeiten (nur Testdaten)
- Ersatz für den regulären Import-Workflow

---

## 2. Unterstützte Evaluationstypen

LLARS unterstützt folgende generalisierte Evaluationstypen:

| Type ID | Name | Beschreibung | Anwendungsfälle |
|---------|------|--------------|-----------------|
| 1 | **ranking** | Items sortieren oder in Buckets kategorisieren | Feature-Qualität, Response-Ranking |
| 2 | **rating** | Items auf einer Skala bewerten (Likert, Sterne) | Qualitätsbewertung, Sentiment, E-Mail-Qualität |
| 4 | **comparison** | Paarweiser Vergleich (A vs B) | LLM Response Comparison, RLHF |
| 5 | **labeling** | Kategorien zuweisen (binär, multi-class) | Topic Classification, Fake Detection, Sentiment |

> **Hinweis:** `authenticity` (Fake/Echt) ist jetzt ein Preset des `labeling`-Typs (`binary-authentic`). Der frühere Typ `mail_rating` wurde ebenfalls entfernt - alle Bewertungsaufgaben nutzen nun den generalisierten `rating`-Typ.

---

## 3. Öffentliche Datensätze

### 3.1 Empfohlene Datensätze

#### Anthropic HH-RLHF (Comparison/Ranking)
- **URL:** https://huggingface.co/datasets/Anthropic/hh-rlhf
- **Größe:** ~170k Beispiele
- **Format:** JSONL mit `chosen` und `rejected` Responses
- **Verwendung:** Comparison-Szenarien, Ranking, LLM-Evaluation

#### Stanford Sentiment Treebank (Rating/Labeling)
- **URL:** https://huggingface.co/datasets/stanfordnlp/sst2
- **Größe:** ~70k Beispiele
- **Format:** Text + Sentiment Label
- **Verwendung:** Rating, Labeling, Sentiment-Analyse

#### LMSYS Chatbot Arena (Comparison)
- **URL:** https://huggingface.co/datasets/lmsys/chatbot_arena_conversations
- **Größe:** ~33k Conversations
- **Format:** Multi-Turn Dialoge mit Präferenz-Votes
- **Verwendung:** Comparison, LLM-as-Judge

#### TruthfulQA (Authenticity)
- **URL:** https://huggingface.co/datasets/truthfulqa/truthful_qa
- **Größe:** ~800 Fragen
- **Format:** Question + Truthful/Untruthful Answers
- **Verwendung:** Authenticity, Fact-Checking

#### AG News (Labeling)
- **URL:** https://huggingface.co/datasets/fancyzhx/ag_news
- **Größe:** ~120k Beispiele
- **Format:** Text + Topic Category
- **Verwendung:** Labeling, Topic Classification

### 3.2 Datensatz-Zusammenfassung

```
┌─────────────────┬──────────────┬────────────┬─────────────────────┐
│ Dataset         │ Size         │ LLARS Type │ Primary Use Case    │
├─────────────────┼──────────────┼────────────┼─────────────────────┤
│ HH-RLHF         │ 170k         │ comparison │ LLM Response Eval   │
│ SST-2           │ 70k          │ rating     │ Sentiment Analysis  │
│ Chatbot Arena   │ 33k          │ comparison │ Chatbot Comparison  │
│ TruthfulQA      │ 800          │ authenticity│ Fact Verification  │
│ AG News         │ 120k         │ labeling   │ Topic Classification│
└─────────────────┴──────────────┴────────────┴─────────────────────┘
```

---

## 4. Architektur

### 4.1 Verzeichnisstruktur

```
llars/
├── tests/
│   └── fixtures/
│       └── test_datasets/           # Heruntergeladene Test-Datensätze
│           ├── hh_rlhf/
│           │   ├── sample.json      # Transformierte Samples
│           │   └── metadata.json    # Dataset-Info
│           ├── sst2/
│           ├── truthful_qa/
│           └── ag_news/
│
├── app/
│   ├── routes/
│   │   └── dev/
│   │       ├── __init__.py
│   │       └── test_data_routes.py  # Dev-Only API Routen
│   │
│   └── services/
│       └── test_data/
│           ├── __init__.py
│           ├── dataset_downloader.py    # HuggingFace Download
│           └── dataset_transformer.py   # Format-Transformation
│
└── scripts/
    └── download_test_datasets.py    # CLI Download-Script
```

### 4.2 Komponenten-Diagramm

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Test Data Infrastructure                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ HuggingFace  │───▶│  Downloader  │───▶│  Local JSON Storage  │  │
│  │     API      │    │   Service    │    │  /test_datasets/     │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                             │                        │              │
│                             ▼                        ▼              │
│                    ┌──────────────┐         ┌──────────────┐       │
│                    │ Transformer  │         │  Dev Routes  │       │
│                    │   Service    │◀────────│  /api/dev/*  │       │
│                    └──────────────┘         └──────────────┘       │
│                             │                        │              │
│                             ▼                        ▼              │
│                    ┌──────────────┐         ┌──────────────┐       │
│                    │    LLARS     │         │   Scenario   │       │
│                    │   Format     │────────▶│   Manager    │       │
│                    └──────────────┘         └──────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. API Spezifikation

### 5.1 Dev-Only Routen

> **Sicherheit:** Alle `/api/dev/*` Routen sind nur aktiv wenn `FLASK_ENV=development`

#### GET /api/dev/datasets
Liste aller verfügbaren Test-Datensätze.

**Response:**
```json
{
  "datasets": [
    {
      "id": "hh_rlhf",
      "name": "Anthropic HH-RLHF",
      "description": "Human preference data for helpful/harmless assistant",
      "size": 170000,
      "llars_types": ["comparison", "ranking"],
      "downloaded": true,
      "local_samples": 1000
    }
  ]
}
```

#### POST /api/dev/datasets/{dataset_id}/download
Lädt einen Datensatz herunter und transformiert ihn.

**Request:**
```json
{
  "sample_size": 1000,
  "split": "train"
}
```

**Response:**
```json
{
  "status": "success",
  "dataset_id": "hh_rlhf",
  "samples_downloaded": 1000,
  "output_path": "tests/fixtures/test_datasets/hh_rlhf/sample.json"
}
```

#### POST /api/dev/scenarios/seed
Erstellt ein Szenario mit Test-Daten.

**Request:**
```json
{
  "name": "Test Comparison Scenario",
  "dataset_id": "hh_rlhf",
  "llars_type": "comparison",
  "item_count": 50,
  "add_users": ["admin", "researcher"]
}
```

**Response:**
```json
{
  "status": "success",
  "scenario_id": 123,
  "threads_created": 50,
  "users_added": 2
}
```

#### GET /api/dev/datasets/{dataset_id}/preview
Zeigt Beispiel-Daten eines Datensatzes.

**Response:**
```json
{
  "dataset_id": "hh_rlhf",
  "llars_format": true,
  "samples": [
    {
      "thread_id": "hh_001",
      "subject": "Response Comparison #1",
      "messages": [...],
      "metadata": {"chosen": "response_a"}
    }
  ]
}
```

---

## 6. Daten-Transformation

### 6.1 HH-RLHF → LLARS (Comparison)

**Input:**
```json
{
  "chosen": "Human: How do I bake a cake?\n\nAssistant: Here's a simple recipe...",
  "rejected": "Human: How do I bake a cake?\n\nAssistant: I don't know how to bake."
}
```

**Output (LLARS Thread):**
```json
{
  "thread_id": "hh_rlhf_001",
  "subject": "Response Comparison: How do I bake a cake?",
  "messages": [
    {
      "message_id": 1,
      "sender": "user",
      "content": "How do I bake a cake?",
      "role": "human",
      "timestamp": "2026-01-16T10:00:00Z"
    },
    {
      "message_id": 2,
      "sender": "assistant_a",
      "content": "Here's a simple recipe...",
      "role": "assistant",
      "is_chosen": true,
      "timestamp": "2026-01-16T10:00:01Z"
    },
    {
      "message_id": 3,
      "sender": "assistant_b",
      "content": "I don't know how to bake.",
      "role": "assistant",
      "is_chosen": false,
      "timestamp": "2026-01-16T10:00:02Z"
    }
  ],
  "metadata": {
    "source": "hh_rlhf",
    "ground_truth": "assistant_a",
    "evaluation_type": "comparison"
  }
}
```

### 6.2 SST-2 → LLARS (Rating)

**Input:**
```json
{
  "sentence": "This movie was absolutely fantastic!",
  "label": 1
}
```

**Output (LLARS Thread):**
```json
{
  "thread_id": "sst2_001",
  "subject": "Sentiment: This movie was absolutely fantastic!",
  "messages": [
    {
      "message_id": 1,
      "sender": "text",
      "content": "This movie was absolutely fantastic!",
      "role": "content"
    }
  ],
  "features": [
    {
      "feature_id": 1,
      "feature_type": "sentiment",
      "feature_content": "This movie was absolutely fantastic!"
    }
  ],
  "metadata": {
    "source": "sst2",
    "ground_truth_label": "positive",
    "ground_truth_rating": 5,
    "evaluation_type": "rating"
  }
}
```

### 6.3 AG News → LLARS (Labeling)

**Input:**
```json
{
  "text": "Wall Street rallies as tech stocks surge...",
  "label": 2
}
```

**Output (LLARS Thread):**
```json
{
  "thread_id": "agnews_001",
  "subject": "News Article Classification",
  "messages": [
    {
      "message_id": 1,
      "sender": "article",
      "content": "Wall Street rallies as tech stocks surge...",
      "role": "content"
    }
  ],
  "metadata": {
    "source": "ag_news",
    "ground_truth_label": "Business",
    "available_labels": ["World", "Sports", "Business", "Sci/Tech"],
    "evaluation_type": "labeling"
  }
}
```

---

## 7. Sicherheit

### 7.1 Zugriffsschutz

```python
def dev_only(f):
    """Decorator that only allows access in development mode."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.debug and os.getenv('FLASK_ENV') != 'development':
            abort(404)  # Hide route in production
        return f(*args, **kwargs)
    return decorated
```

### 7.2 Kein Produktions-Zugriff

- Alle Dev-Routen geben 404 in Production
- Keine sensiblen Daten in Test-Datensätzen
- Lokale Speicherung nur in `tests/fixtures/`

---

## 8. Implementierungsplan

### Phase 1: Infrastruktur (Tag 1)
- [x] Konzept dokumentieren
- [ ] Verzeichnisstruktur erstellen
- [ ] Dataset Downloader Service
- [ ] Basis-Transformer implementieren

### Phase 2: Datensätze (Tag 1-2)
- [ ] HH-RLHF Transformer
- [ ] SST-2 Transformer
- [ ] AG News Transformer
- [ ] TruthfulQA Transformer

### Phase 3: API (Tag 2)
- [ ] Dev-Routes Blueprint
- [ ] List Datasets Endpoint
- [ ] Download Endpoint
- [ ] Preview Endpoint
- [ ] Seed Scenario Endpoint

### Phase 4: Integration (Tag 2-3)
- [ ] Integration in Scenario Wizard ("Use Sample Data")
- [ ] Admin-Panel Integration (optional)
- [ ] Dokumentation aktualisieren

---

## 9. Verwendung

### 9.1 CLI Download

```bash
# Alle Datensätze herunterladen (je 100 Samples)
python scripts/download_test_datasets.py --all --limit 100

# Einzelnen Datensatz
python scripts/download_test_datasets.py --dataset hh_rlhf --limit 500
```

### 9.2 API Verwendung

```bash
# Datensatz herunterladen
curl -X POST http://localhost:55080/api/dev/datasets/hh_rlhf/download \
  -H "Content-Type: application/json" \
  -d '{"sample_size": 100}'

# Test-Szenario erstellen
curl -X POST http://localhost:55080/api/dev/scenarios/seed \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HH-RLHF Comparison Test",
    "dataset_id": "hh_rlhf",
    "llars_type": "comparison",
    "item_count": 20
  }'
```

### 9.3 Im Scenario Wizard

1. "New Scenario" klicken
2. Im Daten-Schritt: "Use Sample Data" wählen
3. Datensatz auswählen (z.B. "HH-RLHF")
4. Anzahl Items festlegen
5. Wizard fortsetzen

---

## 10. Offene Fragen

- [ ] Soll Caching für heruntergeladene Datensätze implementiert werden?
- [ ] Maximale Größe für lokale Datensätze?
- [ ] Automatisches Cleanup alter Test-Daten?

---

## Referenzen

- [Anthropic HH-RLHF](https://huggingface.co/datasets/Anthropic/hh-rlhf)
- [HuggingFace Datasets](https://huggingface.co/datasets)
- [MT-Bench](https://huggingface.co/datasets/lmsys/mt_bench_human_judgments)
- [Evidently AI - 250 LLM Benchmarks](https://www.evidentlyai.com/llm-evaluation-benchmarks-datasets)
