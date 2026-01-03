# Konzepte

Dieser Ordner enthält technische Konzepte und Planungsdokumente für LLARS.

## Dokumente

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Refactoring-Plan 2026](refactoring-plan-2026.md) | Code-Review und Refactoring-Roadmap | In Planung |

## Übersicht

### Refactoring-Plan 2026

Der Refactoring-Plan identifiziert große Dateien und Monolith-Komponenten, die aufgeteilt werden sollten:

**Kritische Komponenten:**
- `ChatWithBots.vue` (3299 Zeilen) - Aufteilen in 8-10 Subkomponenten
- `ChatService` + `AgentChatService` (3510 Zeilen) - Aufteilen in 5 Services
- Route-Dateien (>1200 Zeilen) - Modularisieren

**Geschätzter Gesamtaufwand:** 15-20 Personentage

---

*Stand: Januar 2026*
