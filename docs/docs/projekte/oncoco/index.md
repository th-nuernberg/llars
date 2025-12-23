# OnCoCo Analyse System

!!! success "✅ Status: Abgeschlossen"
    Das OnCoCo-Analysesystem ist **vollständig implementiert**.

## Übersicht

OnCoCo (Online Counseling Conversations) ermöglicht die automatische Klassifizierung von Beratungs-Konversationen mit einem 68-Kategorien-System basierend auf XLM-RoBERTa.

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Konzept](konzept.md) | Detailliertes Integrationskonzept mit Visualisierungen | ✅ Implementiert |

## Features

- 68-Klassen Kategorisierung (40 Berater, 28 Klient)
- Transitions-Matrizen und Heatmaps
- Säulen-Vergleichsanalyse
- Label-Hierarchie (5 Ebenen)
- Batch-Verarbeitung

## Relevante Dateien

```
app/
├── routes/oncoco/            # Info, Pillars, Analyses, Results, Matrix, Debug
├── services/oncoco/
│   ├── oncoco_service.py
│   └── oncoco_labels.py
└── models/oncoco/

llars-frontend/src/components/OnCoCo/
├── OnCoCoOverview.vue
├── OnCoCoResults.vue
├── TransitionHeatmap.vue
└── MatrixComparisonMetrics.vue
```
