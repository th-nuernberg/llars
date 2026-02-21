# OnCoCo Analysis System

!!! success "✅ Status: Implemented"
    The OnCoCo analysis system is **fully implemented** and ready for production use.

## Overview

OnCoCo (Online Counseling Conversations) classifies counseling conversations at sentence level
with a 68‑category system (XLM‑RoBERTa Large, bilingual DE/EN). The analysis is available in the
UI and includes live progress, distributions, transition heatmaps, and statistical pillar comparisons.

## Documentation

| Document | Description | Status |
|----------|--------------|--------|
| [Concept](konzept.md) | Implementation and architecture overview | ✅ Updated |

## Features

- 68‑class categorization (40 counselor, 28 client)
- Live analysis with Socket.IO progress updates
- Label distributions (filter by pillar, level, role)
- Transition matrices as heatmaps + top transitions
- Pillar comparison (matrix comparison metrics)
- KIA data sync directly from the UI
- Resume/force‑resume for stuck analyses

## UI Entry Points

- Overview: `/oncoco`
- New analysis: `/oncoco/config`
- Results: `/oncoco/results/:id`
- Model & labels: `/oncoco/info`

## Relevant Files

```
app/
├── routes/oncoco/                 # Info, Pillars, Analyses, Results, Matrix, Debug
├── services/oncoco/
│   ├── oncoco_service.py
│   └── oncoco_labels.py
└── services/judge/kia_sync_service.py  # KIA data sync

llars-frontend/src/components/OnCoCo/
├── OnCoCoOverview.vue
├── OnCoCoConfig.vue
├── OnCoCoResults.vue
├── OnCoCoInfo.vue
├── TransitionHeatmap.vue
└── MatrixComparisonMetrics.vue
```
