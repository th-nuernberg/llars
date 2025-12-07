# LLARS Refactoring - Kritische Aufgaben

**Erstellt:** 7. Dezember 2025
**Letzte Aktualisierung:** 7. Dezember 2025
**Status:** Phase 1-4 abgeschlossen

---

## Zusammenfassung

| Kategorie | Anzahl | Status |
|-----------|--------|--------|
| Dateien >1000 Zeilen | 6 → 2 | ✅ 4 erledigt |
| Dateien 700-1000 Zeilen | 12 | Ausstehend |
| Fehlende Service-Layer | 6 → 5 Routes | ✅ 1 erledigt |
| Skeleton Loading fehlt | 86 → 81 Komponenten | ✅ 5 hinzugefügt |
| Duplicate Routes | 1 | ✅ Erledigt |
| Bare Except Clauses | 5 | ✅ Erledigt |

---

## Phase 1: Quick-Fixes ✅ ERLEDIGT

### 1.1 Duplicate llm_routes löschen
- [x] **Datei:** `/app/routes/llm_routes.py` (GELÖSCHT)
- [x] **Behalten:** `/app/routes/llm/llm_routes.py`

### 1.2 Bare Except Clauses fixen
- [x] `app/routes/scenarios/scenario_crud.py` → `except (ValueError, TypeError)`
- [x] `app/services/crawler/modules/crawler_service.py` → `except Exception`
- [x] `app/services/oncoco/oncoco_service.py` → `except Exception`

---

## Phase 2: Kritische Dateien (>1000 Zeilen) - TEILWEISE ERLEDIGT

### Frontend

| Datei | Zeilen | Status |
|-------|--------|--------|
| `JudgeResults.vue` | 1447 → 215 | ✅ 85% Reduktion (8 Komponenten + 4 Composables) |
| `ChatbotBuilderWizard.vue` | 1147 → 584 | ✅ 49% Reduktion (4 Step-Komponenten + 2 Composables) |
| `WorkerLane.vue` | 1136 | Ausstehend |
| `KaimoCaseEditor.vue` | 1034 | Ausstehend |
| `ChatWithBots.vue` | 1020 | Ausstehend (Skeleton Loading hinzugefügt) |
| `OnCoCoResults.vue` | 1002 | Ausstehend (Skeleton Loading hinzugefügt) |

### Backend

| Datei | Zeilen | Status |
|-------|--------|--------|
| `crawler_service.py` | 742 | Ausstehend |
| `crawler_core.py` | 734 | Ausstehend |
| `oncoco_service.py` | 719 | Ausstehend |
| `judge_worker_pool.py` | 700 | Ausstehend |

---

## Phase 3: Fehlende Service-Layer - TEILWEISE ERLEDIGT

| Route | DB Ops | Status |
|-------|--------|--------|
| `document_routes.py` | 512+ | ✅ `DocumentService` erstellt (637 → 291 Zeilen, 54% Reduktion) |
| `oncoco_analysis_routes.py` | 200+ | Ausstehend |
| `oncoco_matrix_routes.py` | 180+ | Ausstehend |
| `session_routes.py` | 150+ | Ausstehend |
| `scenario_crud.py` | 140+ | Ausstehend |
| `kaimo_user_routes.py` | 130+ | Ausstehend |

---

## Phase 4: Skeleton Loading - TEILWEISE ERLEDIGT

**Status:** 18/99 Komponenten implementiert (18%)

### Hinzugefügt:
- [x] `OnCoCoResults.vue` - ['data', 'tabs']
- [x] `AdminRAGSection.vue` - ['stats', 'embedding', 'collections', 'documents']
- [x] `ChatWithBots.vue` - ['chatbots']

### Ausstehend:

**Judge:**
- [ ] `CurrentComparisonView.vue`

**OnCoCo:**
- [ ] `OnCoCoOverview.vue`
- [ ] `OnCoCoInfo.vue`

**Kaimo:**
- [ ] `KaimoCaseEditor.vue`
- [ ] `KaimoAssessmentView.vue`
- [ ] `KaimoDocumentsView.vue`

**Weitere:**
- [ ] `HistoryGenerationDetail.vue`
- [ ] `RaterDetail.vue`

---

## Phase 5: Hohe Priorität (700-1000 Zeilen) - AUSSTEHEND

| Datei | Zeilen | Priorität |
|-------|--------|-----------|
| `AdminRAGSection.vue` | 984 | Hoch (Skeleton Loading hinzugefügt) |
| `MatrixComparisonMetrics.vue` | 880 | Hoch |
| `WebCrawlerTool.vue` | 831 | Mittel |
| `OnCoCoInfo.vue` | 780 | Mittel |
| `ScenarioDetailsDialog.vue` | 771 | Mittel |

---

## Erstellte Dateien in dieser Session

### Backend
- `app/services/rag/document_service.py` (543 Zeilen)

### Frontend - JudgeResults
- `components/Judge/Results/ResultsOverview.vue`
- `components/Judge/Results/ResultsRanking.vue`
- `components/Judge/Results/ResultsMetrics.vue`
- `components/Judge/Results/ResultsPositionSwap.vue`
- `components/Judge/Results/ResultsVerbosity.vue`
- `components/Judge/Results/ResultsThreadPerformance.vue`
- `components/Judge/Results/ResultsComparisons.vue`
- `components/Judge/Results/ResultsExport.vue`
- `composables/useJudgeResults.js`
- `composables/useJudgeMatrix.js`
- `composables/useJudgeHelpers.js`
- `composables/useResultsConstants.js`

### Frontend - ChatbotBuilderWizard
- `components/Admin/ChatbotAdmin/BuilderSteps/StepCrawlerConfig.vue`
- `components/Admin/ChatbotAdmin/BuilderSteps/StepCollectionSetup.vue`
- `components/Admin/ChatbotAdmin/BuilderSteps/StepChatbotConfig.vue`
- `components/Admin/ChatbotAdmin/BuilderSteps/StepReview.vue`
- `components/Admin/ChatbotAdmin/BuilderSteps/README.md`
- `composables/useBuilderState.js`
- `composables/useBuilderValidation.js`

---

## Fortschritt

- [x] Phase 1.1: Duplicate llm_routes
- [x] Phase 1.2: Bare Except Clauses
- [x] Phase 2: JudgeResults.vue (85% Reduktion)
- [x] Phase 2: ChatbotBuilderWizard.vue (49% Reduktion)
- [x] Phase 3: DocumentService
- [x] Phase 4: Skeleton Loading (5 Komponenten)
- [ ] Phase 2: Verbleibende große Dateien
- [ ] Phase 3: Weitere Services
- [ ] Phase 5: Hohe Priorität
