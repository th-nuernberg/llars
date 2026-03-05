# Scenario Wizard

**Status:** Production | **As of:** January 2026

## Overview

The Scenario Wizard is a multi‑step assistant for creating evaluation scenarios in LLARS. It helps researchers upload data, choose the right evaluation type, and assemble teams.

## Evaluation Types

LLARS supports 4 generalized evaluation types plus 2 LLARS‑specific types:

| Type | Description | Use cases | Presets |
|------|-------------|-----------|---------|
| **rating** | Multi‑dimensional rating (LLM‑as‑Judge) | Text quality, LLM evaluation, summaries | LLM‑Judge Standard, SummEval, Answer Quality, News Articles |
| **ranking** | Sort or categorize items | Prioritization, quality tiers, relevance sorting | 3 categories, 5 categories, priority, relevance |
| **labeling** | Assign categories | Classification, topic detection, authenticity check | Binary (real/fake), multi‑class, multi‑label |
| **comparison** | Pairwise comparisons | A/B tests, preference studies, model comparisons | Pairwise, with confidence, multi‑criteria |

LLARS‑specific types (psychosocial online counseling):

| Type | Description | Base type | Presets |
|------|-------------|-----------|---------|
| **mail_rating** | Multi‑dimensional rating of counseling e‑mails | rating | Counseling quality, response quality, simple rating |
| **authenticity** | Detect real vs. fake messages | labeling | Message authenticity, AI detection, urgency |

> **Note:** LLARS‑specific types reuse the generalized base types (`mail_rating` → `rating`, `authenticity` → `labeling`).

## Wizard Steps

### Step 1: Upload data

- **Supported formats:** JSON, CSV, XLSX
- **Drag & drop** or file picker
- **AI analysis:** Automatic detection of evaluation type
- **Preview:** First records are shown
- **Examples:** Ideal format in tab **Data format** (next to Invitations)

```
┌─────────────────────────────────────────────┐
│  📁 Drop files here or select              │
│                                             │
│  Supported formats: JSON, CSV, XLSX         │
└─────────────────────────────────────────────┘
```

### Step 2: Define task type

- **AI suggestion:** Based on data analysis
- **Manual selection:** 4 generalized + 2 LLARS‑specific types
- **Descriptions:** Explain each type

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Rating  │  │ Ranking  │  │ Labeling │  │Comparison│
│    ⭐    │  │    ↕️    │  │    🏷️    │  │    ⚖️    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Step 3: Configuration

Depending on the selected type:

**Rating (multi‑dimensional):**
- **Type:** Multi‑dimensional (LLM‑as‑Judge) or classic (Likert, stars)
- **Dimensions:** Coherence, Fluency, Relevance, Consistency (customizable)
- **Scale:** min, max, step (default: 1‑5)
- **Weighting:** Each dimension has a weight for overall score
- **Presets:** LLM‑Judge Standard, SummEval, Answer Quality, News Articles

**Ranking:**
- Define bucket categories
- Ordering vs. categorization
- Allow ties

**Labeling:**
- Define categories
- Allow multi‑label
- Enable "uncertain" option

**Comparison:**
- Comparison criteria
- Allow ties
- Enable confidence scale

**Distribution settings:**
- `all`: All evaluators rate all items
- `random`: Random distribution
- `sequential`: Sequential assignment

### Step 4: Build team

- **Human evaluators:** Invite users
- **LLM models:** Automatic evaluation by AI
- **Roles:** EVALUATOR, RATER

### Step 5: Summary

- Overview of all settings
- Create scenario
- Optional: start LLM evaluation immediately

## AI Analysis

The wizard uses an LLM to analyze uploaded data:

```python
# Prompt for data analysis
SCENARIO_ANALYSIS_FIELD_KEY = "scenario.analysis"

# Analyzes:
# - Data structure (fields, types)
# - Use case
# - Recommended configuration
```

### Heuristics in the prompt

| Data trait | Suggested type |
|------------|----------------|
| Ground‑truth labels | labeling |
| Pairwise comparisons | comparison |
| Items for ordering/categories | ranking |
| Quality/attribute scoring | rating |

## Technical Details

### Frontend components

```
ScenarioManager/
├── components/
│   ├── ScenarioWizard.vue          # main wizard
│   ├── EvaluationConfigEditor.vue  # type configuration
│   └── config/
│       ├── RatingConfigEditor.vue
│       ├── RankingConfigEditor.vue
│       ├── LabelingConfigEditor.vue
│       ├── ComparisonConfigEditor.vue
│       └── EvaluationPreview.vue
├── config/
│   └── evaluationPresets.js        # presets & types
└── composables/
    ├── useScenarioManager.js       # CRUD operations
    └── useDataImport.js            # data import
```

### Backend endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scenarios` | POST | Create scenario |
| `/api/ai-assist/analyze-scenario-data` | POST | AI analysis |
| `/api/import/upload` | POST | Upload file |
| `/api/import/transform` | POST | Transform data |

### Database mapping

```javascript
// Frontend → backend type IDs
const ID_TYPE_MAP = {
  ranking: 1,
  rating: 2,
  comparison: 4,
  labeling: 7,
  mail_rating: 3,
  authenticity: 5
}
```

## Presets

### Rating presets

| ID | Name | Scale | Description |
|----|------|-------|-------------|
| `likert-5` | Likert‑5 | 1-5 | Standard 5‑point Likert |
| `likert-7` | Likert‑7 | 1-7 | Finer granularity |
| `stars-5` | 5 stars | 1-5 | Classic star rating |
| `percentage` | Percentage | 0-100 | Slider 0‑100% |

### Labeling presets

| ID | Name | Categories | Description |
|----|------|------------|-------------|
| `binary-authentic` | Real/Fake | 2 | Authenticity check |
| `binary-sentiment` | Positive/Negative | 2 | Sentiment analysis |
| `sentiment-3` | 3‑class sentiment | 3 | Includes neutral |
| `topic-multilabel` | Topic tags | n | Multi‑label |

### Ranking presets

| ID | Name | Buckets | Description |
|----|------|---------|-------------|
| `buckets-3` | 3 categories | Good/Medium/Bad | Standard |
| `buckets-5` | 5 categories | Very good to very bad | Finer |
| `priority` | Priority | Ordered | Ranking |

### Comparison presets

| ID | Name | Description |
|----|------|-------------|
| `pairwise` | Pairwise comparison | A vs B |
| `pairwise-confidence` | With confidence | + confidence rating |
| `multicriteria` | Multi-criteria | Multiple dimensions |

### Mail-rating presets

| ID | Name | Description |
|----|------|-------------|
| `beratungsqualitaet` | Counseling quality | Multi-dimensional rating of counseling emails |
| `antwortqualitaet` | Response quality | Rating quality of individual counselor responses |
| `einfach` | Simple rating | Quick overall rating without dimensions |
| `custom` | Custom | Define your own rating dimensions |

### Authenticity presets

| ID | Name | Description |
|----|------|-------------|
| `nachricht-echtheit` | Message authenticity | Real vs. fake counseling messages |
| `ki-generiert` | AI detection | AI-generated vs. human |
| `dringlichkeit` | Urgency assessment | Acute to low |
| `custom` | Custom | Define your own categories |

## Localization

The wizard supports DE and EN:

```json
// de.json
{
  "scenarioManager": {
    "wizard": {
      "step1": { "title": "Daten hochladen" },
      "step2": { "title": "Aufgabentyp wählen" },
      "step3": { "title": "Konfiguration" },
      "step4": { "title": "Team zusammenstellen" },
      "step5": { "title": "Zusammenfassung" }
    },
    "types": {
      "rating": "Rating",
      "ranking": "Ranking",
      "labeling": "Labeling",
      "comparison": "Vergleich"
    }
  }
}
```

## Permissions

| Permission | Description |
|------------|-------------|
| `data:manage_scenarios` | Create/edit scenarios |
| `feature:rating:view` | View ratings |
| `feature:rating:edit` | Edit ratings |

## Example workflow

1. **Researcher opens Scenario Manager**
2. **Clicks "New Scenario"** → Wizard opens
3. **Uploads sentiment dataset** (CSV with texts)
4. **AI analyzes** → Suggests "labeling" with "binary-sentiment"
5. **Researcher accepts** or selects a different preset
6. **Configures distribution** (all rate all)
7. **Invites team** (3 evaluators + GPT-4)
8. **Creates scenario** → Evaluation starts

## Data formats for import

### Rating data

```json
[
  {
    "id": "1",
    "text": "The text to be rated...",
    "category": "Optional: category"
  }
]
```

### Ranking data (e.g. summary quality)

**IMPORTANT:** For ranking scenarios like summary quality:
- The **source text** is shown as context (right panel)
- The **items to rank** (e.g. summaries) are stored as features (left panel)

```json
[
  {
    "subject": "Summary Ranking: Article title",
    "source_text": "The full original text serving as context...",
    "items": [
      { "id": "A", "content": "First summary..." },
      { "id": "B", "content": "Second summary..." },
      { "id": "C", "content": "Third summary..." }
    ],
    "task": "Rank the summaries by quality"
  }
]
```

**Technical implementation:**
- `source_text` → stored as **Message** (displayed on the right)
- `items` → stored as **Features** (ranking on the left)
- Items are NOT stored as messages!

### Labeling data

```json
[
  {
    "id": "1",
    "text": "The text to classify...",
    "ground_truth": "category_a"  // Optional for accuracy calculation
  }
]
```

### Comparison data

```json
[
  {
    "id": "1",
    "context": "Optional context...",
    "option_a": "First option to compare",
    "option_b": "Second option to compare",
    "task": "Which option is better?"
  }
]
```

### Authenticity data

```json
[
  {
    "id": "1",
    "text": "The text for authenticity check...",
    "is_fake": true  // Ground truth for accuracy/F1 calculation
  }
]
```

## See also

- [Ranking scenarios in detail](./ranking-scenarios.md)
- [Scenario Manager testing](./scenario-manager-testing.md)
- [Database schema](../../entwickler/datenbank-schema.md)
- [Permission system](../../guides/permission-system.md)
