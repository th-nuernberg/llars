# OnCoCo Analyse System

!!! success "✅ Status: Implementiert"
    Das OnCoCo-Analysesystem ist **vollständig umgesetzt** und produktiv nutzbar.

## Übersicht

OnCoCo (Online Counseling Conversations) klassifiziert Beratungs‑Konversationen satzbasiert
mit einem 68‑Kategorien‑System (XLM‑RoBERTa Large, bilingual DE/EN). Die Analyse ist
direkt im UI verfügbar und umfasst Live‑Fortschritt, Verteilungen, Transition‑Heatmaps
und statistische Säulenvergleiche.

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Konzept](konzept.md) | Implementierungs‑ und Architekturüberblick | ✅ Aktualisiert |

## Features

- 68‑Klassen‑Kategorisierung (40 Berater, 28 Klient)
- Live‑Analyse mit Socket.IO Progress‑Updates
- Label‑Verteilungen (Filter nach Säule, Level, Rolle)
- Transition‑Matrizen als Heatmaps + Top‑Transitions
- Säulen‑Vergleich (Matrix‑Comparison Metrics)
- KIA‑Daten‑Sync direkt aus dem UI
- Resume/Force‑Resume bei „stuck“ Analysen

## UI‑Einstieg

- Übersicht: `/oncoco`
- Neue Analyse: `/oncoco/config`
- Ergebnisse: `/oncoco/results/:id`
- Modell & Labels: `/oncoco/info`

## Relevante Dateien

```
app/
├── routes/oncoco/                 # Info, Pillars, Analyses, Results, Matrix, Debug
├── services/oncoco/
│   ├── oncoco_service.py
│   └── oncoco_labels.py
└── services/judge/kia_sync_service.py  # KIA Data Sync

llars-frontend/src/components/OnCoCo/
├── OnCoCoOverview.vue
├── OnCoCoConfig.vue
├── OnCoCoResults.vue
├── OnCoCoInfo.vue
├── TransitionHeatmap.vue
└── MatrixComparisonMetrics.vue
```
