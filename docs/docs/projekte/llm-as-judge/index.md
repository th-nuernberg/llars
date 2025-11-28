# LLM-as-Judge System

!!! success "✅ Status: Abgeschlossen"
    Das Basis-System ist **vollständig implementiert**.
    Erweiterungen (Comparison Modes, Sampling) sind in Planung.

## Übersicht

Das LLM-as-Judge System ermöglicht automatisierte paarweise Vergleiche von E-Mail-Konversationen. Ein LLM bewertet, welche Antwort qualitativ besser ist.

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Konzept](konzept.md) | Ursprüngliches Konzept mit 8 Phasen | ✅ Implementiert |
| [Comparison Modes](comparison-modes-konzept.md) | Erweiterte Vergleichsmodi (Round-Robin, Free-for-All) | 📋 Geplant |
| [Sampling Strategien](sampling-strategien.md) | Faire Sampling-Methoden für unterschiedliche Säulengrößen | 📋 Geplant |

## Features

- Paarweise Vergleiche von E-Mail-Threads
- Live-Streaming der LLM-Bewertung
- Multi-Worker-Architektur
- ELO-Rating System
- Socket.IO Live-Updates

## Relevante Dateien

```
app/
├── routes/judge/judge_routes.py
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
