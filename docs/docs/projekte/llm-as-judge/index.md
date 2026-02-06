# LLM Evaluators (Konfiguration)

!!! success "✅ Status: Abgeschlossen"
    LLM-Evaluatoren sind als **Konfiguration im Szenario-Manager** vollständig implementiert.

## Übersicht

LLM Evaluators sind keine separate Anwendung in LLARS. Sie werden pro Szenario konfiguriert und laufen als automatische Evaluatoren neben menschlichen Bewertungen.

Typischer Ablauf:
- Im Scenario Wizard LLM-Evaluation aktivieren und Modelle auswählen
- Evaluierung startet automatisch nach dem Erstellen (oder manuell über den Scenario Manager)
- Fortschritt und Ergebnisse sind in den Evaluation/Results-Tabs sichtbar

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Konzept](konzept.md) | Historisches Konzept aus der LLM-as-Judge-Phase | 🟡 Hintergrund |
| [Comparison Modes](comparison-modes-konzept.md) | Vergleichsmodi (Pillar Sample, Round-Robin, Free-for-All) | 🟡 Hintergrund |
| [Sampling Strategien](sampling-strategien.md) | Sampling-Methoden für unterschiedliche Säulengrößen | 🟡 Hintergrund |

## Features (aktuell in LLARS)

- LLM-Evaluation als Szenario-Konfiguration
- Auswahl von System- und eigenen Provider-Modellen
- Automatischer Start nach Szenario-Erstellung (optional)
- Live-Status und Ergebnisübersicht im Scenario Manager

## Relevante Dateien

```
app/
├── routes/llm/llm_evaluation_routes.py       # Start/Stop/Progress der LLM-Evaluation
├── routes/scenarios/scenario_manager_api.py  # LLM-Evaluatoren im Szenario-Config
├── services/llm/llm_ai_task_runner.py        # LLM-Evaluation Runner
└── services/evaluation/                      # Bewertungslogik und Aggregationen

llars-frontend/src/views/ScenarioManager/
├── components/ScenarioWizard.vue             # LLM-Evaluation konfigurieren
├── components/tabs/ScenarioEvaluationTab.vue # LLM-Status/Ergebnisse
└── composables/useScenarioManager.js         # Start/Stop LLM-Evaluation
```
