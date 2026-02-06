# LLARS Data Importer - Concept

!!! info "Status: Implemented (Wizard)"
    The Data Importer is implemented in the LLARS frontend.
    Some sections in this document describe planned extensions and are marked as **planned**.

**Created:** 2026-01-05
**Author:** Philipp Steigerwald
**Version:** 1.0

---

## Goal

> A universal, AI-assisted data import wizard that guides users through the full process:
> **Upload data → AI analysis (intent) → Review & configuration → Assign users → Execute import**

The LLARS Data Importer makes the system usable for everyone, regardless of data format.
"AI by Design" means an LLM actively helps with understanding, transforming, and preparing the data.

---

## Core Principles

### AI by Design

| Principle | Implementation |
|---------|-----------|
| **LLM as helper** | LLM analyzes uploaded data and suggests transformations |
| **Optional AI** | Every LLM suggestion can be rejected - full control stays with the user |
| **Transparency** | Users always see what the LLM suggests before it is applied |
| **Learning** | **Planned:** system remembers successful mappings for similar datasets |

### Wizard Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     LLARS DATA IMPORTER WIZARD                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [1. Upload] → [2. Describe] → [3. Review & Configure] → [4. Users]  │
│      ↓               ↓                   ↓                 ↓          │
│   Upload files   Intent +            Scenario            Select        │
│                 AI analysis          configuration       evaluators    │
│                                                                       │
│                          →  [5. Execute Import]                       │
│                                  ↓                                   │
│                           Start and finish import                     │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Usage Scenarios

### Supported Evaluation Types

| task_type | Description | Data structure (short) |
|----------|--------------|------------------------|
| **rating** | Evaluate single answers/features | Conversation or single text |
| **ranking** | Sort variants (drag & drop) | Reference + multiple outputs |
| **mail_rating** | Evaluate entire conversations | Conversation |
| **comparison** | Pairwise comparison (A vs B) | text_a/text_b |
| **authenticity** | Fake/real classification | Conversation or text + label |
| **labeling** | Classification | Single text + label |

Note: **LLM Evaluators** are configured in the Scenario Manager (not a separate `task_type`).

### Concrete Use Cases

#### Use Case 1: Human vs Machine Ranking
> "I have 500 conversations. I want people and an LLM to rank them."

**Workflow:**
1. Upload: JSON/CSV with conversations
2. AI: Detects conversation structure and suggests mapping
3. Review: Select "Ranking" and verify configuration
4. Users: Assign evaluators/viewers
5. Execute import and continue in Scenario Manager
6. Optional: Enable LLM Evaluators in Scenario Manager

#### Use Case 2: Fake/Real Detection
> "I have synthetic and real emails. People should identify what is fake."

**Workflow:**
1. Upload: Two folders (fake/, real/) or JSON with `is_fake` flag
2. AI: Detects authenticity format
3. Transform: No transformation needed
4. Scenario: Select "Authenticity"
5. Users: Assign evaluators
6. Execute import and start evaluation in Scenario Manager

#### Use Case 3: LLM Output Quality
> "I have outputs from GPT-4 and Claude. People should judge which is better."

**Workflow:**
1. Upload: JSONL with `{prompt, response_a, response_b, model_a, model_b}`
2. AI: Detects pairwise-comparison format (LMSYS style)
3. Transform: Map to LLARS comparison schema
4. Scenario: Select "Comparison" with model labels
5. Users: Assign evaluators
6. Execute import and start side-by-side evaluation

#### Use Case 4: Assess Consulting Quality
> "I have consulting conversations. Experts should rate the quality."

**Workflow:**
1. Upload: JSON with conversations (client ↔ advisor)
2. AI: Detects roles and suggests mapping
3. Review: Select "Rating" or "Mail Rating"
4. Users: Assign domain experts as evaluators
5. Execute import and start expert evaluation

#### Use Case 5: Custom Dataset
> "I have my own format that LLARS does not know."

**Workflow:**
1. Upload: Arbitrary JSON/CSV
2. AI: Analyzes structure and shows fields
3. Transform: Universal Transformer uses AI mapping
4. **Planned:** Optional transformation script for fine control
5. Execute import and continue with scenario configuration

---

## Wizard Steps in Detail

### Step 1: Upload

**UI elements:**
- Drag & drop zone
- Multi-file upload including folder structure
- Supported formats: `.json`, `.jsonl`/`.ndjson`, `.csv`, `.tsv`
- **XLSX:** UI accepts upload, backend support is **planned**

**Features:**
- Format autodetection
- Progress indicator for multiple files
- Per-file error messages

### Step 2: Describe (Intent + Preview)

**UI elements:**
- Data preview (multiple samples)
- Structure summary (fields, items, format)
- Intent input with example prompts
- Chat interface for follow-up questions

**AI functions:**
- Analyze structure + user intent (`/ai/analyze-intent`)
- Streaming chat for refinement (`/ai/chat-stream`)
- Live configuration (task type, field mapping, labels/buckets)

### Step 3: Review & Configure

**UI elements:**
- Scenario name
- Evaluation type (mail_rating, rating, ranking, comparison, authenticity, labeling)
- Date range (start/end)
- AI analysis summary (mapping, roles, criteria, confidence)
- Data overview (files, items, format)

**Note:**
- Advanced scenario options (e.g., distribution/order) are configured in Scenario Manager.

### Step 4: Users

**UI elements:**
- Select evaluators and viewers
- Quick actions (e.g., all researchers as evaluator)
- Distribution preview for round-robin

### Step 5: Execute Import

**UI elements:**
- Summary (files, items, task type, users)
- Start button with progress indicator
- Success message on completion

**After import:**
- Continue in Scenario Manager (e.g., fine configuration, LLM Evaluators)

## Data Formats

### LLARS Native Format (Target Schema)

```json
{
  "$schema": "llars-import-v1",
  "metadata": {
    "name": "My dataset",
    "description": "Description",
    "task_type": "rating",
    "source": "custom"
  },
  "items": [
    {
      "id": "unique-123",
      "subject": "Consulting on topic X",
      "conversation": [
        {
          "role": "user",
          "content": "Hello, I need help...",
          "timestamp": "2026-01-05T10:00:00Z"
        },
        {
          "role": "assistant",
          "content": "Happy to help you...",
          "timestamp": "2026-01-05T10:05:00Z"
        }
      ],
      "features": [
        {
          "type": "summary",
          "content": "The client asks about...",
          "generated_by": "gpt-4"
        }
      ],
      "metadata": {
        "source_file": "data.json",
        "is_fake": false
      }
    }
  ]
}
```

### Supported Input Formats

| Format | Description | Auto-detection |
|--------|--------------|----------------|
| **LLARS Native** | `llars-import-v1` schema | Yes |
| **OpenAI/ChatML** | `messages: [{role, content}]` | Yes |
| **LMSYS Pairwise** | `{prompt, response_a, response_b}` | Yes |
| **JSONL/NDJSON** | One conversation per line | Yes |
| **CSV/TSV** | Column-based tables | Yes |
| **Generic JSON** | Arbitrary JSON lists | Yes (fallback) |
| **Custom** | Arbitrary structure | AI analysis + mapping |

Note: **XLSX** is planned (UI accepts upload, backend support pending).

---

## Implemented Components

### Backend
- `app/services/data_import/import_service.py` - Orchestration (session, transform, execute)
- `app/services/data_import/format_detector.py` - Format detection + adapter selection
- `app/services/data_import/universal_transformer.py` - AI-assisted transformation
- `app/services/data_import/ai_analyzer.py` - Intent/structure analysis
- `app/services/data_import/schema_validator.py` / `schema_detector.py` - Validation
- `app/services/data_import/adapters/` - Adapters (llars, openai, lmsys, jsonl, csv, generic)
- `app/routes/data_import/import_routes.py` - REST API (`/api/import/...`)

### Frontend
- `llars-frontend/src/views/DataImporter/DataImporterView.vue` - Route `/data-import`
- `llars-frontend/src/components/DataImporter/DataImporterWizard.vue` - Wizard
- `llars-frontend/src/components/DataImporter/steps/` - StepUpload, StepDescribe, StepReviewNew, StepUsers
- `llars-frontend/src/services/importService.js` - API client

### Integration
- `llars-frontend/src/views/ScenarioManager/components/tabs/ScenarioDataTab.vue` uses `/api/import/from-data`

---

## API Endpoints (current)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/import/formats` | Available formats + task types |
| POST | `/api/import/upload` | Upload file (multipart) |
| GET | `/api/import/session/{id}` | Fetch session status |
| GET | `/api/import/session/{id}/sample` | Sample for preview |
| POST | `/api/import/transform` | Execute transformation |
| POST | `/api/import/validate` | Run validation |
| POST | `/api/import/execute` | Execute import to DB |
| DELETE | `/api/import/session/{id}` | Delete session |
| POST | `/api/import/from-data` | Direct import (Wizard/Scenario Manager) |
| POST | `/api/import/ai/analyze` | AI structure analysis |
| POST | `/api/import/ai/analyze-intent` | AI intent + mapping |
| POST | `/api/import/ai/transform` | Apply AI transformation |
| POST | `/api/import/ai/transform-script` | Generate transformation script |
| POST | `/api/import/ai/suggest` | Suggest mapping improvements |
| POST | `/api/import/ai/chat-stream` | SSE chat for config refinement |

---

## Planned Extensions

- XLSX parsing in the backend
- URL/HuggingFace import
- UI for transformation scripts (backend endpoint exists)
- Reusable mapping profiles
