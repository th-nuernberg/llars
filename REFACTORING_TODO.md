# LLARS Refactoring - Vollständige Aufgabenliste

**Erstellt:** 7. Dezember 2025
**Letzte Aktualisierung:** 7. Dezember 2025
**Status:** Aktive Bearbeitung

---

## Zusammenfassung

| Kategorie | Anzahl | Status |
|-----------|--------|--------|
| Dateien >1000 Zeilen | 6 → 2 | ✅ 4 erledigt |
| Dateien 700-1000 Zeilen | 18 | ⚠️ Ausstehend |
| Dateien 500-700 Zeilen | 25+ | ⚠️ Ausstehend |
| Routes ohne @handle_api_errors | 58 | 🔴 Kritisch |
| Routes mit direkten DB-Ops | 15 | ⚠️ Ausstehend |
| Vue ohne Skeleton Loading | 94 | ⚠️ Ausstehend |
| Duplicate Routes | 1 | ✅ Erledigt |
| Bare Except Clauses | 5 | ✅ Erledigt |

---

## PRIORITÄT 1: Error-Handling Migration (58 Routes)

**Problem:** 58 Route-Dateien nutzen NICHT den `@handle_api_errors` Decorator.

**Dokumentation:** `MIGRATION_ERROR_HANDLING.md`

### Sofort zu migrieren (kritische Pfade):

| Route-Datei | DB-Ops | Priorität |
|-------------|--------|-----------|
| `chatbot/chatbot_routes.py` | ✅ Hat es | Fertig |
| `judge/session_routes.py` | 13 | Kritisch |
| `judge/comparison_routes.py` | 14 | Kritisch |
| `judge/session_control_routes.py` | 11 | Kritisch |
| `rag/collection_routes.py` | 23 | Kritisch |
| `rag/document_routes.py` | ✅ Hat Service | Hoch |
| `oncoco/oncoco_analysis_routes.py` | 27 | Hoch |
| `scenarios/scenario_crud.py` | 28 | Hoch |
| `prompts/prompt_routes.py` | 31 | Hoch |
| `kaimo/kaimo_user_routes.py` | 22 | Hoch |

### Weitere Routes ohne @handle_api_errors:

```
app/routes/llm/llm_routes.py
app/routes/rating/mail_rating_stats.py
app/routes/rating/mail_rating_threads.py
app/routes/rating/ranking_routes.py
app/routes/rating/mail_rating_history.py
app/routes/rating/rating_routes.py
app/routes/rating/mail_rating_messages.py
app/routes/auth/data_routes.py
app/routes/auth/auth_routes.py
app/routes/crawler/crawler_routes.py
app/routes/mail_rating/*.py (4 Dateien)
app/routes/permissions/permission_routes.py
app/routes/rag/search_routes.py
app/routes/rag/admin_routes.py
app/routes/rag/RAGRoutes.py
app/routes/RatingRoutes.py
app/routes/RankingRoutes.py
app/routes/HelperFunctions.py
app/routes/scenarios/*.py (4 Dateien)
app/routes/judge/*.py (12 Dateien)
app/routes/oncoco/*.py (7 Dateien)
app/routes/comparison/comparison_routes.py
app/routes/LLMComparisonRoutes.py
app/routes/UserPromptRoutes.py
app/routes/kaimo/*.py (2 Dateien)
app/routes/authentik_routes.py
app/routes/routes.py
```

---

## PRIORITÄT 2: Große Frontend-Dateien (>1000 Zeilen)

### Erledigt ✅

| Datei | Zeilen | Reduktion | Methode |
|-------|--------|-----------|---------|
| `JudgeResults.vue` | 1447 → 215 | 85% | 8 Subkomponenten + 4 Composables |
| `ChatbotBuilderWizard.vue` | 1147 → 584 | 49% | 4 Steps + 2 Composables |

### Ausstehend

| Datei | Zeilen | Problem | Lösung |
|-------|--------|---------|--------|
| `JudgeSession.vue` | 1716 | Sehr komplex | Aufteilen in ViewModes, Controls |
| `WorkerLane.vue` | 1136 | Real-time Stream | WorkerCard, StreamDisplay |
| `KaimoCaseEditor.vue` | 1034 | Edit + Validation | Sections extrahieren |
| `ChatWithBots.vue` | 1022 | Chat + RAG | Composables extrahieren |
| `OnCoCoResults.vue` | 1022 | Aggregation | Sections extrahieren |
| `AdminRAGSection.vue` | 1009 | Admin Panel | Subkomponenten |

---

## PRIORITÄT 3: Große Dateien (700-1000 Zeilen)

### Frontend

| Datei | Zeilen | Priorität |
|-------|--------|-----------|
| `MatrixComparisonMetrics.vue` | 880 | Hoch |
| `WebCrawlerTool.vue` | 831 | Mittel |
| `OnCoCoInfo.vue` | 780 | Mittel |
| `ScenarioDetailsDialog.vue` | 771 | Mittel |
| `PromptEngineering.vue` | 756 | Mittel |
| `SingleWorkerFullscreenDialog.vue` | 748 | Niedrig |
| `Documentation.vue` | 740 | Niedrig |
| `PromptEngineeringDetail.vue` | 737 | Mittel |
| `RankerDetail.vue` | 717 | Niedrig |
| `CreateScenarioDialog.vue` | 711 | Mittel |
| `sidebar.vue` (PromptEngineering) | 700 | Niedrig |

### Backend

| Datei | Zeilen | Problem | Lösung |
|-------|--------|---------|--------|
| `crawler_service.py` | 742 | Crawling + RAG + SocketIO | Event-Emitter |
| `crawler_core.py` | 734 | Web + Content | Bereits modular |
| `oncoco_service.py` | 719 | Model + Classification | Sentence-Service |
| `judge_worker_pool.py` | 700 | Thread + DB | Orchestration |

---

## PRIORITÄT 4: Service-Layer für Routes

Routes mit >10 direkten DB-Operationen sollten Services nutzen:

| Route | DB-Ops | Neuer Service |
|-------|--------|---------------|
| `document_routes.py` | ✅ | `DocumentService` (fertig) |
| `UserPromptRoutes.py` | 31 | `PromptService` |
| `prompt_routes.py` | 31 | `PromptService` |
| `scenario_crud.py` | 28 | `ScenarioService` |
| `oncoco_analysis_routes.py` | 27 | `OnCoCoAnalysisService` |
| `collection_routes.py` | 23 | `CollectionService` |
| `kaimo_user_routes.py` | 22 | `KaimoService` |
| `oncoco_debug_routes.py` | 15 | Teil von OnCoCoService |
| `scenario_management.py` | 15 | `ScenarioService` |
| `comparison_routes.py` | 14 | `ComparisonService` |
| `session_routes.py` | 13 | Teil von JudgeService |
| `llm_routes.py` | 13 | `LLMService` |
| `RatingRoutes.py` | 12 | `RatingService` |
| `rating_routes.py` | 12 | `RatingService` |
| `HelperFunctions.py` | 12 | Refactor zu Utils |
| `session_control_routes.py` | 11 | Teil von JudgeService |

---

## PRIORITÄT 5: Skeleton Loading (94 Komponenten fehlen)

### Top 15 Kritische Komponenten ohne Skeleton Loading:

| Komponente | Lädt Daten | Priorität |
|------------|------------|-----------|
| `RaterDetail.vue` | Ja | Kritisch |
| `HistoryGenerationDetail.vue` | Ja | Kritisch |
| `PromptEngineeringDetail.vue` | Ja | Kritisch |
| `ChatbotEditor.vue` | Ja | Hoch |
| `ChatbotManager.vue` | Ja | Hoch |
| `KaimoAssessmentView.vue` | Ja | Hoch |
| `KaimoDocumentsView.vue` | Ja | Hoch |
| `OnCoCoOverview.vue` | Ja | Hoch |
| `OnCoCoInfo.vue` | Ja | Hoch |
| `JudgeConfig.vue` | Ja | Hoch |
| `JudgeOverview.vue` | Ja | Hoch |
| `ComparisonChat.vue` | Ja | Mittel |
| `AdminRAG.vue` | Ja | Mittel |
| `AdminHome.vue` | Ja | Mittel |
| `FloatingChat.vue` | Nein | Niedrig |

### Bereits implementiert (18 Komponenten):

- `OnCoCoResults.vue`
- `AdminRAGSection.vue`
- `ChatWithBots.vue`
- `JudgeResults.vue` (indirekt via Subkomponenten)
- Plus 14 weitere aus früheren Sessions

---

## Dateien 500-700 Zeilen (Mittlere Priorität)

| Datei | Zeilen |
|-------|--------|
| `OnCoCoOverview.vue` | 676 |
| `KaimoAssessmentView.vue` | 669 |
| `ChatbotEditor.vue` | 658 |
| `JudgeConfig.vue` | 638 |
| `AdminRAG.vue` | 630 |
| `kia_sync_service.py` | 623 |
| `oncoco_analysis_routes.py` | 614 |
| `ComparisonChat.vue` | 612 |
| `ChatbotManager.vue` | 607 |
| `oncoco_labels.py` | 602 |
| `KaimoDocumentsView.vue` | 592 |
| `judge_service.py` | 576 |
| `CurrentComparisonView.vue` | 569 |
| `permission_service.py` | 562 |
| `chat_service.py` | 558 |

---

## Fortschritt (Session 7. Dezember)

### Erledigt ✅

- [x] Duplicate llm_routes.py gelöscht
- [x] Bare Except Clauses gefixt (5 Dateien)
- [x] JudgeResults.vue aufgeteilt (85% Reduktion)
- [x] ChatbotBuilderWizard.vue aufgeteilt (49% Reduktion)
- [x] DocumentService erstellt
- [x] Skeleton Loading: OnCoCoResults, AdminRAGSection, ChatWithBots
- [x] README.md aktualisiert
- [x] CLAUDE.md aktualisiert

### In Arbeit 🔄

- [ ] Error-Handling Migration (58 Routes)
- [ ] Weitere große Dateien aufteilen

### Ausstehend ⏳

- [ ] Service-Layer für 15 Routes
- [ ] Skeleton Loading für 94 Komponenten
- [ ] JudgeSession.vue aufteilen (1716 Zeilen!)

---

## Empfohlene Reihenfolge

1. **Error-Handling Migration** (kritisch für Stabilität)
   - Top 10 Routes mit meisten DB-Ops

2. **JudgeSession.vue aufteilen** (größte Datei)
   - In ViewModes, Controls, etc.

3. **Service-Layer** für kritische Routes
   - PromptService, ScenarioService, etc.

4. **Skeleton Loading** für Top 15 Komponenten

5. **Weitere Komponenten** aufteilen (700-1000 Zeilen)
