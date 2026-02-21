# LLM Evaluators (Configuration)

!!! success "✅ Status: Complete"
    LLM evaluators are fully implemented as a **configuration in Scenario Manager**.

## Overview

LLM evaluators are not a separate application in LLARS. They are configured per scenario and run as automatic evaluators alongside human ratings.

Typical flow:
- Enable LLM evaluation and select models in the Scenario Wizard
- Evaluation starts automatically after creation (or manually via Scenario Manager)
- Progress and results are visible in the Evaluation/Results tabs

## Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [Concept](konzept.md) | Historical concept from the LLM-as-Judge phase | 🟡 Background |
| [Comparison Modes](comparison-modes-konzept.md) | Comparison modes (Pillar Sample, Round-Robin, Free-for-All) | 🟡 Background |
| [Sampling Strategies](sampling-strategien.md) | Sampling methods for different pillar sizes | 🟡 Background |

## Features (current in LLARS)

- LLM evaluation as a scenario configuration
- Selection of system and custom provider models
- Optional auto-start after scenario creation
- Live status and results overview in Scenario Manager

## Relevant files

```
app/
├── routes/llm/llm_evaluation_routes.py       # Start/stop/progress of LLM evaluation
├── routes/scenarios/scenario_manager_api.py  # LLM evaluators in scenario config
├── services/llm/llm_ai_task_runner.py        # LLM evaluation runner
└── services/evaluation/                      # Evaluation logic and aggregation

llars-frontend/src/views/ScenarioManager/
├── components/ScenarioWizard.vue             # Configure LLM evaluation
├── components/tabs/ScenarioEvaluationTab.vue # LLM status/results
└── composables/useScenarioManager.js         # Start/stop LLM evaluation
```
