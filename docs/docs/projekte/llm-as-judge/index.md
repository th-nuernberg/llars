# LLM Evaluator System

!!! success "✅ Status: Abgeschlossen"
    Das Basis-System ist **vollständig implementiert**.
    Erweiterungen (Comparison Modes, Sampling) sind in Planung.

## Übersicht

Das LLM Evaluator System ermöglicht automatisierte paarweise Vergleiche von E-Mail-Konversationen. Ein LLM bewertet, welche Antwort qualitativ besser ist.

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Konzept](konzept.md) | Ursprüngliches Konzept mit 8 Phasen | ✅ Implementiert |
| [Comparison Modes](comparison-modes-konzept.md) | Vergleichsmodi (Pillar Sample, Round-Robin, Free-for-All) | ✅ Implementiert |
| [Sampling Strategien](sampling-strategien.md) | Sampling-Methoden für unterschiedliche Säulengrößen | 🟡 Teilweise |

## Features

- Paarweise Vergleiche von E-Mail-Threads
- Live-Streaming der LLM-Bewertung
- Multi-Worker-Architektur
- ELO-Rating System
- Socket.IO Live-Updates

## Relevante Dateien

```
app/
├── routes/judge/              # Session-, Comparison-, Stats-, Pillar- & Sync-Routen
├── services/judge/
│   ├── judge_service.py
│   ├── kia_sync_service.py
│   └── comparison_generator.py
└── workers/judge_worker.py

llars-frontend/src/components/Judge/
├── JudgeOverview.vue
├── JudgeConfig.vue
├── JudgeSession.vue
└── JudgeResults.vue
```
