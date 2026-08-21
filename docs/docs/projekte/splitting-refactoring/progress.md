# Splitting & Refactoring - Progress

!!! success "📋 Status: Weitgehend abgeschlossen"
    **Fortschritt:** 14 Major-Refactorings abgeschlossen (siehe CLAUDE.md)

**Konzept:** [Splitting & Refactoring Konzept](konzept.md)
**Umsetzung:** [Splitting & Refactoring Umsetzung](umsetzung.md)
**Gestartet:** November 2025
**Stand:** März 2026

---

## Fortschritts-Übersicht

```mermaid
gantt
    title Splitting & Refactoring Fortschritt
    dateFormat  YYYY-MM-DD
    section Phase 1
    Backend Models (tables.py)    :p1, 2025-01-01, 2d
    section Phase 2
    Backend Routes (judge)        :p2, after p1, 3d
    section Phase 3
    Frontend Judge (JudgeSession) :p3, after p2, 4d
    section Phase 4
    Backend Routes (oncoco, RAG)  :p4, after p3, 3d
    section Phase 5
    Frontend OnCoCo & Admin       :p5, after p4, 3d
    section Phase 6
    Restliche Dateien             :p6, after p5, 2d
```

---

## Phasen-Checkliste

### Phase 1: Backend Models (`tables.py` → 8 Dateien)
- [ ] Ordnerstruktur `app/db/models/` erstellen
- [ ] `user.py` erstellen
- [ ] `permission.py` erstellen
- [ ] `judge.py` erstellen
- [ ] `rag.py` erstellen
- [ ] `chatbot.py` erstellen
- [ ] `oncoco.py` erstellen
- [ ] `pillar.py` erstellen
- [ ] `scenario.py` erstellen
- [ ] `__init__.py` mit Re-Exports
- [ ] `tables.py` deprecated markieren
- [ ] Tests grün

### Phase 2: Backend Routes (`judge_routes.py` → 6 Dateien)
- [ ] `session_routes.py` erstellen
- [ ] `comparison_routes.py` erstellen
- [ ] `evaluation_routes.py` erstellen
- [ ] `kia_sync_routes.py` erstellen
- [ ] `statistics_routes.py` erstellen
- [ ] `stream_routes.py` erstellen
- [ ] `__init__.py` mit Blueprint-Registrierung
- [ ] Alte Datei deprecated markieren
- [ ] Tests grün

### Phase 3: Frontend Judge (`JudgeSession.vue` → 8+ Komponenten)
- [ ] Ordnerstruktur erstellen
- [ ] `useSessionSocket.js` Composable
- [ ] `useSessionState.js` Composable
- [ ] `SessionHeader.vue` Komponente
- [ ] `SessionControls.vue` Komponente
- [ ] `WorkerGrid.vue` Komponente
- [ ] `ComparisonQueue.vue` Komponente
- [ ] `StreamOutput.vue` Komponente
- [ ] Haupt-Komponente refaktorieren
- [ ] Hot-Reload funktioniert
- [ ] Funktionalität identisch

### Phase 4: Backend Routes (oncoco, RAG)
- [ ] `oncoco_routes.py` aufteilen
- [ ] `RAGRoutes.py` aufteilen
- [ ] Tests grün

### Phase 5: Frontend OnCoCo & Admin
- [ ] `OnCoCoResults.vue` aufteilen
- [ ] `AdminRAGSection.vue` aufteilen
- [ ] `WorkerLane.vue` aufteilen
- [ ] Funktionalität identisch

### Phase 6: Restliche Dateien
- [ ] Alle Dateien > 500 Zeilen identifizieren
- [ ] Systematisch aufteilen
- [ ] Finale Validierung

---

## Git-Commits

| Datum | Commit | Beschreibung | Phase |
|-------|--------|--------------|-------|
| - | - | - | - |

---

## Statistiken

### Ausgangslage

| Kategorie | Anzahl Dateien | Gesamtzeilen |
|-----------|----------------|--------------|
| > 1500 Zeilen | 5 | ~12.000 |
| 1000-1500 Zeilen | 8 | ~9.500 |
| 700-1000 Zeilen | 15 | ~12.000 |
| 500-700 Zeilen | 15 | ~8.500 |
| **Gesamt** | **43** | **~42.000** |

### Nach Refactoring (Ziel)

| Kategorie | Anzahl Dateien | Gesamtzeilen |
|-----------|----------------|--------------|
| > 500 Zeilen | 0 | 0 |
| 300-500 Zeilen | ~30 | ~12.000 |
| < 300 Zeilen | ~80 | ~30.000 |
| **Gesamt** | **~110** | **~42.000** |

---

## Offene Punkte

### Blocker

| Problem | Auswirkung | Status |
|---------|------------|--------|
| - | - | - |

### To-Do (Nächste Schritte)

1. [ ] Konzept reviewen lassen
2. [ ] Phase 1 starten (Backend Models)
3. [ ] Nach jeder Phase: Validierung + Commit

### Fragen an Reviewer

- [ ] Sollen alte Import-Pfade dauerhaft als Re-Exports bestehen bleiben?
- [ ] Priorität: Backend-first oder Frontend-first?
- [ ] Soll es einen Feature-Branch geben oder direkt auf main?

---

## Changelog

### 2025-11-28
- 📋 Konzept erstellt
- 📋 Umsetzungs-Template erstellt
- 📋 Progress-Tracking eingerichtet

---

## Abgeschlossene Refactorings (Stand: März 2026)

| Datei | Vorher | Nachher | Reduktion |
|-------|--------|---------|-----------|
| ChatWithBots.vue | 3299 | 774 | -77% |
| LatexCollabWorkspace.vue | 3085 | 1259 | -59% |
| JudgeSession.vue | 2174 | 579 | -73% |
| ChatbotEditor.vue | 1967 | 507 | -74% |
| chat_service.py | 1657 | 590 | -64% |
| latex_collab_routes.py | 1514 | 56 | -96% |
| crawler_service.py | 1415 | 666 | -53% |
| chatbot_routes.py | 1273 | 35 | -97% |
| anonymize_service.py | 1275 | 445 | -65% |
| agent_chat_service.py | 1263 | 301 | -76% |
| judge_worker_pool.py | 1067 | 618 | -42% |
| collection_embedding_service.py | 1046 | 606 | -42% |
| embedding_worker.py | 825 | 67 | -92% |
| markdown_collab_routes.py | 798 | 24 | -97% |

---

## Notizen

> Hier werden wichtige Entscheidungen während der Umsetzung dokumentiert.

- **2025-11-28:** Projekt initialisiert. Warten auf Review des Konzepts.
- **2026-01-27:** 14 Major-Refactorings abgeschlossen. Backend: 425 Dateien, ~126.000 Zeilen. Frontend: 577 Dateien, ~193.000 Zeilen.
