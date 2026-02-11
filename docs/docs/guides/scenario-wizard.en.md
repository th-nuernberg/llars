# Scenario Wizard

**Version:** 2.0 | **Date:** January 2026

The Scenario Wizard is a multi-step assistant for creating evaluation scenarios in LLARS. It helps researchers upload data, automatically detect the evaluation type, and assemble teams.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1     Step 2     Step 3     Step 4     Step 5                │
│  [Data]  →  [Type]  →  [Config] → [Team] →  [Done]                │
└─────────────────────────────────────────────────────────────────────┘
```

| Step | Description |
|------|-------------|
| 1. Upload data | Import files, automatic analysis |
| 2. Task type | Confirm or change evaluation type |
| 3. Configuration | Adjust dimensions, scales, buckets |
| 4. Team | Invite evaluators and LLM models |
| 5. Summary | Review and create |

---

## Step 1: Upload Data

### Supported Formats

| Format | Description | Example |
|--------|-------------|---------|
| **CSV/TSV** | Comma- or tab-separated values | `data.csv` / `data.tsv` |
| **JSON** | Array of objects | `[{...}, {...}]` |
| **JSONL/NDJSON** | One object per line | `data.jsonl` |
| **XLSX** | Excel file | `data.xlsx` |

### Data Formats

LLARS supports two data formats for ranking scenarios:

#### Wide Format (Default)

Each row contains all variants in separate columns:

```csv
source_text,summary_a,summary_b,summary_c
"The original article...","GPT-4 summary","Claude summary","Llama summary"
```

#### Long Format (New!)

The same ID appears multiple times with different variants:

```csv
chat_id,llm_name,output,source
8,gpt-4,"GPT-4 output...","Original text..."
8,claude-3,"Claude output...","Original text..."
8,llama-3,"Llama output...","Original text..."
```

!!! info "Automatic detection"
    LLARS recognizes long format automatically and transforms the data into LLARS format.

### Upload Area

```
┌─────────────────────────────────────────────┐
│  Drop files here or select                 │
│                                             │
│  Supported formats: JSON, JSONL, CSV/TSV,  │
│  XLSX                                      │
└─────────────────────────────────────────────┘
```

After upload, **data analysis** starts automatically.

---

## Automatic Type Detection

### Two-Stage System

LLARS uses an intelligent two-stage system for type detection:

```
┌──────────────────┐      definite      ┌─────────────────┐
│  SchemaDetector  │  ───────────────►  │  Type detected! │
│  (deterministic) │                   └─────────────────┘
└────────┬─────────┘
         │ uncertain
         ▼
┌──────────────────┐
│   AI analysis    │  ───────────────► Type + configuration
│   (LLM-based)    │
└──────────────────┘
```

### 1. SchemaDetector (Deterministic)

The SchemaDetector analyzes field names and recognizes patterns:

| Evaluation type | Detected fields | Priority |
|-----------------|-----------------|----------|
| **Authenticity** | `is_human`, `is_fake`, `synthetic`, `is_ai` | 1 (highest) |
| **Comparison** | `response_a` + `response_b`, `winner` | 2 |
| **Ranking** | `summary_a`, `summary_b`, `summary_c` | 3 |
| **Mail Rating** | `messages[]` array (without `is_human`) | 4 |
| **Rating** | `question` + `response`, `prompt` + `completion` | 5 |
| **Labeling** | `category`, `label`, `sentiment` + content | 6 |

!!! tip "Schema-based detection"
    When SchemaDetector detects a type **definitely**, the UI is marked with a green badge "Auto-detected".

### 2. AI Analysis (Fallback)

If SchemaDetector is uncertain, an LLM analyzes the data:

- Detects more complex patterns
- Suggests suitable presets
- Generates scenario names and descriptions

---

## Long-Format Transformation (New!)

### What is Long Format?

Long-format data contains the same group ID multiple times with different variants:

```
┌─────────────────────────────────────────────────────────────────┐
│ chat_id │ llm_name        │ output              │ source        │
├─────────┼─────────────────┼─────────────────────┼───────────────┤
│ 8       │ gpt-4           │ "GPT-4 response..."  │ "Original..." │
│ 8       │ claude-3        │ "Claude response..." │ "Original..." │
│ 8       │ llama-3         │ "Llama response..."  │ "Original..." │
│ 9       │ gpt-4           │ "GPT-4 response..."  │ "Original..." │
│ 9       │ claude-3        │ "Claude response..." │ "Original..." │
└─────────────────────────────────────────────────────────────────┘
```

### Automatic Field Mapping

LLARS automatically generates a mapping for long-format data:

| Mapping field | Description | Example |
|---------------|-------------|---------|
| `grouping_field` | Groups related rows | `chat_id` |
| `variant_field` | Identifies the variant | `llm_name` |
| `output_field` | Contains the generated content | `output` |
| `reference_field` | Contains the reference/source | `source` |

### Transformation

The data is transformed automatically:

```
Before: 30 rows (long format)
        ↓ transformation
After: 3 ranking items (10 variants each)
```

**Result structure:**

```json
{
  "id": "group_8",
  "reference": {
    "type": "text",
    "content": "Original text..."
  },
  "items": [
    { "id": "item_1", "label": "gpt-4", "content": "GPT-4 response..." },
    { "id": "item_2", "label": "claude-3", "content": "Claude response..." },
    { "id": "item_3", "label": "llama-3", "content": "Llama response..." }
  ]
}
```

---

## Step 2: Task Type

### The 6 Evaluation Types

=== "Rating"

    **Multi-dimensional rating (LLM evaluator)**

    - Likert scales per dimension
    - Weighted overall score
    - Default: coherence, fluency, relevance, consistency

    **Use cases:** text quality, summaries, LLM outputs

=== "Ranking"

    **Sort items into quality buckets**

    - Drag & drop interface
    - Configurable buckets (e.g., good/medium/poor)
    - Ties allowed

    **Use cases:** summary quality, prioritization, LLM comparisons

=== "Labeling"

    **Assign categories**

    - Single-label or multi-label
    - Configurable categories
    - Optional: "Unsure" option

    **Use cases:** topic classification, sentiment analysis

=== "Comparison"

    **Pairwise A/B comparison**

    - Two options side by side
    - Select winner
    - Optional: ties possible

    **Use cases:** model comparisons, preference studies

=== "Authenticity"

    **Real/Fake classification**

    - Binary decision
    - Optional: confidence scale
    - LLARS-specific (psychosocial counseling)

    **Use cases:** detect AI-generated texts

=== "Mail Rating"

    **Rate email threads**

    - Conversation is displayed
    - Multi-dimensional rating
    - LLARS-specific (counseling emails)

    **Use cases:** counseling quality, response quality

### Type Selection

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Rating  │  │ Ranking  │  │ Labeling │  │Comparison│
│  (icon)  │  │  (icon)  │  │  (icon)  │  │  (icon)  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
     |
     └── Auto-detected (Schema Detection)
```

---

## Step 3: Configuration

### Presets

Each evaluation type has pre-configured presets:

#### Rating Presets

| Preset | Dimensions/Type | Scale | Description |
|--------|------------------|-------|-------------|
| `llm-judge-standard` | Coherence, fluency, relevance, consistency | 1-5 | Standard for LLM evaluator |
| `summeval` | 7 dimensions (mixed scales) | variable | Demo with different scale sizes |
| `response-quality` | Helpfulness, accuracy, completeness, clarity | 1-5 | Chat responses |
| `news-article` | Accuracy, objectivity, completeness, readability | 1-5 | News articles |
| `text-quality-3dim` | Content, language, structure | 1-5 | Compact 3 dimensions |
| `likert-5` | Single dimension | 1-5 | Standard Likert scale |
| `likert-7` | Single dimension | 1-7 | Finer granularity |
| `stars-5` | Stars | 1-5 | Classic star rating |
| `stars-10` | Numeric | 1-10 | 10-point scale |
| `percentage` | Slider | 0-100 | Percentage rating |

#### Ranking Presets

| Preset | Buckets/Type | Description |
|--------|--------------|-------------|
| `buckets-3` | Good, medium, poor | Standard 3 categories |
| `buckets-5` | Very good to very poor | Finer granularity |
| `priority` | Ordered | Sort by priority |
| `relevance` | Ordered | Sort by relevance |

#### Labeling Presets

| Preset | Categories | Description |
|--------|------------|-------------|
| `binary-authentic` | Real, fake | Authenticity check |
| `binary-sentiment` | Positive, negative | Binary sentiment analysis |
| `sentiment-3` | Positive, neutral, negative | 3-class sentiment |
| `topic-multilabel` | Configurable | Multiple topics per item |

#### Comparison Presets

| Preset | Type | Description |
|--------|------|-------------|
| `pairwise` | A vs B | Simple pairwise comparison |
| `pairwise-confidence` | A vs B + confidence | With confidence rating |
| `multicriteria` | Multiple criteria | Relevance, quality, clarity |
| `tournament` | Elimination | Tournament format |

### Adjust Configuration

Depending on the type, you can adjust:

- **Dimensions** (Rating): names, descriptions, weighting
- **Scale** (Rating): min, max, step size, labels
- **Buckets** (Ranking): names, colors, order
- **Categories** (Labeling): names, colors, multi-select

---

## Step 4: Build the Team

### Human Evaluators

Users can be invited via user search (name/username + email):

| Role | Description |
|------|-------------|
| **EVALUATOR** | Rates items and can interact |
| **VIEWER** | Read-only, no ratings |

### LLM Models

Available LLMs are loaded dynamically from the system configuration:

- **System models** (admin-configured)
- **Own/shared providers** (provided by the user or team)

!!! info "LLM Evaluation"
    If LLM evaluation is enabled, selected LLMs automatically rate all items after scenario creation based on the configured dimensions.

---

## Step 5: Summary

Overview of all settings:

```
┌─────────────────────────────────────────────────────────────┐
│  Summary                                                    │
├─────────────────────────────────────────────────────────────┤
│  Name:        Summary Quality Study                         │
│  Type:        Ranking (3 buckets)                           │
│  Items:       150                                           │
│  Team:        5 evaluators + 2 LLMs                         │
│  Distribution: Everyone rates everything                    │
├─────────────────────────────────────────────────────────────┤
│                           [Create scenario]                 │
└─────────────────────────────────────────────────────────────┘
```

After creation:

- Scenario is created
- Invitations are sent
- Optional: LLM evaluation starts immediately

---

## Example Data Formats

### Rating Data

```json
[
  {
    "question": "What is the capital of France?",
    "response": "The capital of France is Paris."
  }
]
```

### Ranking Data (Wide Format)

```json
[
  {
    "source_text": "The original article about climate change...",
    "summary_a": "GPT-4 summary...",
    "summary_b": "Claude summary...",
    "summary_c": "Llama summary..."
  }
]
```

### Ranking Data (Long Format)

```csv
doc_id,model,summary,source_text
DOC001,gpt-4,"GPT-4 summary...","Original article..."
DOC001,claude-3,"Claude summary...","Original article..."
DOC001,llama-3,"Llama summary...","Original article..."
```

### Labeling Data

```json
[
  {
    "text": "The product is fantastic!",
    "ground_truth": "positive"
  }
]
```

### Comparison Data

```json
[
  {
    "prompt": "Explain quantum computing",
    "response_a": "GPT-4 response...",
    "response_b": "Claude response...",
    "winner": "a"
  }
]
```

### Authenticity Data

```json
[
  {
    "text": "Text for authenticity check...",
    "is_human": true
  }
]
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scenarios` | POST | Create scenario |
| `/api/ai-assist/analyze-scenario-data/stream` | POST | Streaming AI analysis |
| `/api/ai-assist/transform-long-format` | POST | Transform long format |

---

## Permissions

| Permission | Description |
|------------|-------------|
| `data:manage_scenarios` | Create/edit scenarios |
| `data:import` | Import data |

---

## See Also

- [Scenario Manager](scenario-manager.md) - Manage scenarios
- [Evaluation](evaluation.md) - Run evaluations
- [Evaluation Data Formats](../entwickler/evaluation-datenformate.md) - Technical reference
