# Batch Generation

**Version:** 1.0 | **Date:** January 2026

Batch Generation enables running prompts at scale with different LLM models. It connects prompt engineering with evaluation by automatically generating outputs from combinations of input data, prompts, and models.

---

## Overview

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                              BATCH GENERATION                                  │
│                                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                       │
│  │ Input Data  │    │   Prompts   │    │   Models    │                       │
│  │   (Items)   │  × │ (Templates) │  × │   (LLMs)    │                       │
│  │     10      │    │      2      │    │      3      │  =  60 Outputs        │
│  └─────────────┘    └─────────────┘    └─────────────┘                       │
│         ↓                  ↓                  ↓                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        Generation Job                                   │ │
│  │  ████████████████████████░░░░░░░░  75%  ·  45/60 done  ·  $2.35          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│         ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Export: CSV, JSON  |  Convert to Evaluation Scenario                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

!!! tip "Batch Generation in 5 Steps"
    1. **Open hub** → `/generation` or navigation
    2. **New job** → start wizard
    3. **Configure** → choose sources, prompts, models
    4. **Start** → watch real-time progress
    5. **Export** → CSV/JSON or create evaluation scenario

---

## Generation Hub

The hub shows all jobs for the current user:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Batch Generation                                          [+ New Job]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Active Jobs                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🔄 LLM Comparison Study                             [⏸] [✕]        │   │
│  │  ████████████████░░░░░░░░  68%  ·  34/50  ·  $1.23                  │   │
│  │  GPT-4, Claude 3.5  ·  Started: 5 min ago                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Completed Jobs                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐                        │
│  │ ✓ Summary Test       │  │ ✓ Prompt Iteration   │                        │
│  │   100/100 · $4.50    │  │   25/25 · $0.85      │                        │
│  │   2 hours ago        │  │   Yesterday          │                        │
│  └──────────────────────┘  └──────────────────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Job Status

| Status | Icon | Description |
|--------|------|-------------|
| **Created** | ○ | Job configured, not started yet |
| **Queued** | ◷ | Waiting for processing |
| **Running** | 🔄 | Active generation |
| **Paused** | ⏸ | Paused, can be resumed |
| **Completed** | ✓ | All outputs generated |
| **Failed** | ✕ | Job stopped due to error |
| **Cancelled** | ○ | Cancelled by the user |

---

## Job Wizard

The 5-step wizard guides you through configuration:

### Step 1: Select Sources

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Input Data                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Choose source:                                                            │
│                                                                             │
│  ◉ From Scenario                                                           │
│    [LLM Evaluator Study         ▼]  ·  150 Items                           │
│                                                                             │
│  ○ Manual Input                                                            │
│    Upload JSON/CSV or paste text                                           │
│                                                                             │
│  ○ Prompt Only (no input data)                                             │
│    Prompt is self-contained, no external data required                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Source Type | Description | Use Case |
|------------|-------------|----------|
| **Scenario** | Items from an existing evaluation scenario | Process existing data |
| **Manual** | Upload JSON, CSV or plaintext | Test new data |
| **Prompt Only** | Try different prompts across multiple models; Prompt Engineering variables are applied automatically | Quickly compare prompt templates |

---

### Step 2: Select Prompts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: Prompt Templates                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Available prompts:                                                        │
│                                                                             │
│  ☑ Summary Standard                                                        │
│    Variables: {{content}}, {{language}}                                    │
│                                                                             │
│  ☑ Summary Short                                                           │
│    Variables: {{content}}                                                  │
│                                                                             │
│  ☐ Detailed Analysis                                                       │
│    Variables: {{content}}, {{criteria}}                                    │
│                                                                             │
│  Selected: 2 prompts                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

!!! info "Prompt Integration"
    Prompts are loaded from the [Prompt Engineering](prompt-engineering.md) module.
    Variables are automatically replaced by input data.
    If a block is titled `System`, it is used as the system prompt.
    All other blocks are merged in order into a single user prompt.

**Variable aliases:**
The generator recognizes common field names automatically:

| Alias | Description |
|-------|--------------|
| `{{content}}`, `{{input}}`, `{{text_content}}`, `{{thread_content}}`, `{{thread}}` | Main content |
| `{{messages}}`, `{{email_thread}}`, `{{email_content}}` | Email thread / messages |
| `{{subject}}`, `{{betreff}}` | Subject |

---

### Step 3: Select Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: LLM Models                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ☑ GPT-4o                    $5.00 / 1M input   $15.00 / 1M output         │
│  ☑ Claude 3.5 Sonnet         $3.00 / 1M input   $15.00 / 1M output         │
│  ☐ GPT-4 Turbo               $10.00 / 1M input  $30.00 / 1M output         │
│  ☐ Llama 3 70B               $0.70 / 1M input   $0.90 / 1M output          │
│                                                                             │
│  Selected: 2 models                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Step 4: Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4: Parameters                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Job Name:                                                                 │
│  [LLM Comparison Study_____________________________]                        │
│                                                                             │
│  Generation parameters:                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Temperature:     [0.7_______]  (0.0 - 2.0)                           │  │
│  │  Max Tokens:      [1000______]  (optional)                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Limits:                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Budget Limit (USD):     [10.00_____]                                │  │
│  │  Max Retries:            [3_________]                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| **Temperature** | Creativity (0 = deterministic, 2 = creative) | 0.7 |
| **Max Tokens** | Maximum output length (optional) | - |
| **Budget Limit** | Pauses job if exceeded | - |
| **Max Retries** | Retries on error | 3 |

---

### Step 5: Review & Start

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5: Summary                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Job Name: [LLM Comparison Study_______________]                           │
│                                                                             │
│  Configuration:                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Input data:    150 items from "LLM Evaluator Study"                  │  │
│  │  Prompts:       2 templates                                           │  │
│  │  Models:        GPT-4o, Claude 3.5 Sonnet                             │  │
│  │  ───────────────────────────────────────────────────────────         │  │
│  │  Total:         600 outputs (150 × 2 × 2)                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Cost estimate:                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  GPT-4o:              300 × ~1000 tokens  ≈  $4.50                   │  │
│  │  Claude 3.5 Sonnet:   300 × ~1000 tokens  ≈  $2.70                   │  │
│  │  ───────────────────────────────────────────────────────────         │  │
│  │  Estimated total:    ~$7.20                                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                              [Create and start job]         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Job Detail View

After starting, the detail view shows real-time progress:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LLM Comparison Study                                  [⏸] [✕] [↓ Export] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Progress                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ████████████████████████████░░░░░░░░░░░░░░  68%                     │  │
│  │  408 / 600 completed  ·  2 failed  ·  $4.89                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Currently processing:                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  🔄 Item #127  ·  Summary Standard  ·  GPT-4o                         │  │
│  │     Tokens: 234... █                                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Outputs                                                     [Filter ▼]    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  #408  ✓  Item #85  ·  Short  ·  Claude   ·  $0.012  ·  1.2s          │  │
│  │  #407  ✓  Item #85  ·  Short  ·  GPT-4o   ·  $0.018  ·  0.9s          │  │
│  │  #406  ✓  Item #84  ·  Standard  ·  Claude   ·  $0.015  ·  1.5s      │  │
│  │  ...                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                        [< Back]  Page 1/20  [Next >]        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Updates (Socket.IO)

| Event | Description |
|-------|-------------|
| `generation:job:started` | Job started |
| `generation:job:progress` | Progress update |
| `generation:item:started` | Individual item is processing |
| `generation:item:token` | Streaming token received |
| `generation:item:completed` | Item generated successfully |
| `generation:item:failed` | Item failed |
| `generation:job:completed` | Job completed |
| `generation:job:failed` | Job failed |
| `generation:job:budget_exceeded` | Budget limit reached |

---

## Export & Further Processing

### Export Formats

| Format | Description | Use |
|--------|-------------|-----|
| **CSV** | Tabular with metadata | Excel, analytics tools |
| **JSON** | Structured with full config | Programmatic processing |

**CSV columns:**
- `output_id`, `source_item_id`, `prompt_variant`, `model_name`
- `generated_content`, `input_tokens`, `output_tokens`, `cost_usd`
- `processing_time_ms`, `status`, `error_message`
- `created_at`, `completed_at`

---

### Convert to Evaluation Scenario

Generated outputs can be used directly as an evaluation scenario:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Create Evaluation Scenario                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Scenario Name:  [LLM Comparison Evaluation________]                        │
│                                                                             │
│  Evaluation Type:                                                          │
│  ○ Rating (multi-dimensional)                                              │
│  ◉ Ranking (sort items)                                                    │
│  ○ Comparison (A vs B)                                                     │
│  ○ Labeling (assign categories)                                            │
│                                                                             │
│  Configuration:                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Items: 150 (grouped by source)                                       │  │
│  │  Variants per item: 4 (2 prompts × 2 models)                          │  │
│  │  Evaluators: [Invite after creation]                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                              [Create scenario]              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

!!! tip "Workflow Integration"
    After creating the scenario, evaluators can rate the generated outputs
    in the [Scenario Manager](scenario-manager.md).

---

## API Endpoints

### Job Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generation/jobs` | GET | Get jobs for the user |
| `/api/generation/jobs` | POST | Create a new job |
| `/api/generation/jobs/:id` | GET | Job details |
| `/api/generation/jobs/:id` | DELETE | Delete job |

### Job Lifecycle

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generation/jobs/:id/start` | POST | Start job |
| `/api/generation/jobs/:id/pause` | POST | Pause job |
| `/api/generation/jobs/:id/cancel` | POST | Cancel job |

### Outputs & Export

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generation/jobs/:id/outputs` | GET | Outputs (paginated) |
| `/api/generation/outputs/:id` | GET | Single output |
| `/api/generation/jobs/:id/export/csv` | POST | CSV export |
| `/api/generation/jobs/:id/export/json` | POST | JSON export |
| `/api/generation/jobs/:id/to-scenario` | POST | Convert to scenario |

### Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generation/jobs/:id/statistics` | GET | Job statistics |
| `/api/generation/estimate` | POST | Cost estimate |

---

## Permissions

| Permission | Description |
|------------|-------------|
| `feature:generation:view` | View jobs and outputs |
| `feature:generation:create` | Create jobs |
| `feature:generation:manage` | Start/pause/cancel jobs |
| `feature:generation:export` | Export outputs |
| `feature:generation:to_scenario` | Create evaluation scenarios |

---

## Error Handling

### Automatic Retries

On errors, outputs are retried automatically:

| Attempt | Wait Time |
|---------|-----------|
| 1 | 1 second |
| 2 | 5 seconds |
| 3 | 15 seconds |

After 3 failed attempts, the output is marked as `FAILED`.

### Budget Exceeded

When the budget limit is reached:
1. Job is automatically paused
2. User receives a notification
3. Budget can be increased and the job resumed

---

## FAQ

??? question "How are costs calculated?"
    Costs are based on the token prices of the selected models.
    A cost estimate is shown before starting.
    Actual costs can vary (usually lower).

??? question "Can I change a running job?"
    No. Pause the job and create a new one with the changed configuration.

??? question "What happens if the connection drops?"
    The job continues in the backend. On reconnection, the current status
    is synchronized including partially generated content.

??? question "How many jobs can I run in parallel?"
    One job per user. Additional jobs are queued.

---

## See Also

- [Prompt Engineering](prompt-engineering.md) - Create and manage prompts
- [Scenario Manager](scenario-manager.md) - Manage evaluation scenarios
- [Evaluation](evaluation.md) - Perform evaluations
