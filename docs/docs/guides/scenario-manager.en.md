# Scenario Manager

**Version:** 2.0 | **Date:** January 2026

The Scenario Manager is the central management interface for evaluation scenarios in LLARS. Researchers can manage scenarios, monitor progress, and analyze results.

---

## Overview

The Scenario Manager consists of two main areas:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Scenario Manager                               [+ New Scenario]    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │  My Scenarios (3)    │  │  Invitations (2)     │                 │
│  └──────────────────────┘  └──────────────────────┘                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │ Scenario Card  │  │ Scenario Card  │  │ Scenario Card  │        │
│  └────────────────┘  └────────────────┘  └────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tab: My Scenarios

Shows all scenarios you created.

### Scenario Card

```
┌────────────────────────────────────────┐
│  [⭐] Summary Quality Study    [Menu]   │
│  Rating · Evaluating                    │
│                                         │
│  ████████████░░░░  75%                  │
│                                         │
│  👥 5 Evaluators  ·  🤖 2 LLMs         │
│  Created: 15.01.2026  ·  150 Threads   │
└────────────────────────────────────────┘
```

| Element | Description |
|---------|-------------|
| **Icon** | Evaluation type (⭐ Rating, ↕️ Ranking, etc.) |
| **Name** | Scenario name |
| **Type** | Evaluation type + status badge |
| **Progress** | Overall progress of all evaluators |
| **Team** | Number of human evaluators + LLMs |
| **Date** | Creation date |
| **Threads** | Number of threads/items |
| **Menu** | Actions (3-dot menu) |

### Status Badges

| Status | Color | Meaning |
|--------|-------|---------|
| **Draft** | Gray | Not started yet |
| **Data collection** | Blue | Items are being imported |
| **Evaluating** | Blue | Ratings are being collected |
| **Analyzing** | Yellow | Results are being analyzed |
| **Completed** | Green | All ratings finished |
| **Archived** | Gray | Inactive |

### Actions

| Action | Description |
|--------|-------------|
| **Open** | Click card → workspace |
| **Settings** | Change scenario configuration |
| **Duplicate** | Create a copy with new data |
| **Archive** | Deactivate scenario |
| **Delete** | Delete scenario and all data |

---

## Tab: Invitations

Shows scenarios you were invited to as an evaluator.

### Invitation Card

```
┌────────────────────────────────────────┐
│  [↕️] LLM Comparison Benchmark          │
│  Ranking · Invited by admin             │
│                                         │
│  Your progress: 12/20 (60%)             │
│  ████████████░░░░░░░░                   │
│                                         │
│  [Reject] [Accept]                      │
│  (after accepting: [Go to Evaluation]   │
│   + "Leave" option)                     │
└────────────────────────────────────────┘
```

!!! warning "Limited visibility"
    Invited evaluators are routed to the **evaluation overview** and see **only their own progress**, not the overall progress or other results.

### Invitation Status

| Status | Description |
|--------|-------------|
| **Pending** | Invitation not accepted yet |
| **Accepted** | Invitation accepted, evaluation possible |
| **Rejected** | Invitation declined |

---

## Workspace

After clicking a scenario card, the **workspace** opens with multiple tabs:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Summary Quality Study                                   [⚙️]       │
├───────────┬───────────┬───────────┬───────────┬────────────────────┤
│ Overview  │   Data    │ Evaluation│   Team    │                    │
└───────────┴───────────┴───────────┴───────────┴────────────────────┘
```

| Tab | Description |
|-----|--------------|
| **Overview** | Quick overview, progress, quick actions |
| **Data** | Import and manage items |
| **Evaluation** | Live stats, metrics, export |
| **Team** | Manage evaluators and LLMs |

!!! note "Settings"
    The gear icon (⚙️) in the top right opens the scenario settings dialog.
    Invited evaluators do not see this workspace.

---

### Tab: Overview

Quick overview of the scenario:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Summary                                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Type:         Rating (Multi-Dimensional)                         │
│  Items:        150                                                │
│  Dimensions:   Coherence, Fluency, Relevance, Consistency         │
│  Scale:        1-5 (Likert)                                       │
├─────────────────────────────────────────────────────────────────────┤
│  Overall Progress                                                │
│  ████████████████░░░░░░░░░░░░░░░░  45%                           │
│  675 / 1500 ratings                                              │
├─────────────────────────────────────────────────────────────────────┤
│  [Go to Evaluation]  [Start LLM Evaluation]  [Export]             │
└─────────────────────────────────────────────────────────────────────┘
```

Additional quick actions:
- Import data
- Start LLM evaluation
- View results

---

### Tab: Evaluation

Live statistics for ongoing evaluation:

#### Progress Overview

```
┌────────────────────────────────────────┐
│  Evaluator Progress                    │
├────────────────────────────────────────┤
│  admin        ████████████████  100%   │
│  researcher   ████████████░░░░   75%   │
│  evaluator1   ████████░░░░░░░░   50%   │
│  LLM-A        ████████████████  100%   │
│  LLM-B        ████████████████  100%   │
└────────────────────────────────────────┘
```

#### Agreement Metrics & Heatmaps

Shows agreement and consistency between evaluators (e.g., Kappa/Alpha/ICC) as well as heatmaps:

```
┌────────────────────────────────────────────────────────┐
│  Inter-Rater Agreement                                 │
├────────────────────────────────────────────────────────┤
│               admin  researcher  eval1  LLM-A  LLM-B   │
│  admin         -       0.82      0.75   0.88   0.85    │
│  researcher   0.82      -        0.78   0.84   0.81    │
│  evaluator1   0.75     0.78       -     0.79   0.77    │
│  LLM-A        0.88     0.84      0.79    -     0.91    │
│  LLM-B        0.85     0.81      0.77   0.91    -      │
└────────────────────────────────────────────────────────┘
```

!!! info "Agreement values"
    - **> 0.8**: High agreement (green)
    - **0.6-0.8**: Moderate agreement (yellow)
    - **< 0.6**: Low agreement (red)

#### Dimension Distribution (Rating)

Shows rating distributions per dimension:

```
┌────────────────────────────────────────┐
│  Coherence                             │
│  1: ██░░░░░░░░  10%                    │
│  2: ████░░░░░░  20%                    │
│  3: ██████░░░░  30%                    │
│  4: ████████░░  25%                    │
│  5: ███░░░░░░░  15%                    │
│  Avg 3.2                                │
└────────────────────────────────────────┘
```

---

### Tab: Team

Manage evaluators:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Team Members                                     [+ Invite]        │
├─────────────────────────────────────────────────────────────────────┤
│  👤 admin           Owner        100%  ████████████████             │
│  👤 researcher      Evaluator     75%  ████████████░░░░             │
│  👤 evaluator1      Evaluator     50%  ████████░░░░░░░░             │
│  🤖 LLM Model A      LLM          100%  ████████████████            │
│  🤖 LLM Model B      LLM          100%  ████████████████            │
└─────────────────────────────────────────────────────────────────────┘
```

#### Roles

| Role | Description |
|------|-------------|
| **Owner** | Scenario creator, full rights |
| **Evaluator** | Rates items and can interact |
| **Viewer** | Read-only, no ratings |

#### LLM Evaluation

!!! tip "Add LLM models"
    LLM evaluators are currently selected during scenario creation in the Wizard. The Team tab shows them; add/remove in the Team tab is not fully implemented yet.

#### Invitation Status

Invitations are shown as status badges on team cards (pending, accepted, rejected). Rejected invitations can be re-sent.

#### Export Functions

In the Evaluation tab, results can be exported directly:

| Format | Description |
|--------|-------------|
| **CSV** | All ratings as a table |
| **JSON** | Structured data |

#### Evaluator Filter

Toggle between:
- **All** - All evaluators
- **Human** - Human evaluators only
- **LLM** - AI evaluators only

---

### Tab: Data

Manage items to be evaluated:

- Upload items (JSON, JSONL, CSV/TSV, XLSX)
- View existing threads/items
- Delete threads/items

---

### Settings Dialog

Accessible via the gear icon (⚙️):

- Edit **name & description**
- Set **time period** (start/end)
- Configure **distribution**
- Configure **order** (fixed/random)
- Set **visibility** and **status**
- **Delete scenario**

---

## Create a New Scenario

1. Click **"+ New Scenario"** in the top right
2. The [Scenario Wizard](scenario-wizard.md) opens
3. Follow the 5 steps

---

## Permissions

### Owner (Creator)

| Action | Allowed |
|--------|---------|
| Open workspace | ✅ |
| See overall progress | ✅ |
| Manage team | ✅ |
| View stats/results | ✅ |
| Change settings | ✅ |
| Start LLM evaluation | ✅ |
| Delete scenario | ✅ |

### Evaluator (Invited)

| Action | Allowed |
|--------|---------|
| Perform evaluation | ✅ |
| See own progress | ✅ |
| Open evaluation overview | ✅ |
| Open workspace | ❌ |
| See overall progress | ❌ |
| See team | ❌ |
| See results | ❌ |

### Viewer (Invited, read-only)

| Action | Allowed |
|--------|---------|
| View evaluation | ✅ |
| Submit ratings | ❌ |
| See own progress | ✅ |
| Open workspace | ❌ |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scenarios` | GET | List all scenarios |
| `/api/scenarios` | POST | Create new scenario |
| `/api/scenarios/:id` | GET | Scenario details |
| `/api/scenarios/:id` | PUT | Update scenario |
| `/api/scenarios/:id` | DELETE | Delete scenario |
| `/api/scenarios/:id/stats` | GET | Live statistics |
| `/api/scenarios/:id/export` | GET | Export results |

---

## See Also

- [Scenario Wizard](scenario-wizard.md) - Create scenarios
- [Evaluation](evaluation.md) - Run evaluations
- [Permission System](permission-system.md) - Access rights
