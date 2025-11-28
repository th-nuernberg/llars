# Splitting & Refactoring - Konzept

!!! warning "📋 Status: Konzept"
    Dieses Projekt befindet sich in der **Konzeptphase**.
    Ziel: Alle Dateien unter 500 Zeilen bringen.

**Erstellt:** 2025-11-28
**Autor:** Claude Code
**Version:** 1.0

---

## Ziel

Alle großen Dateien im LLARS-Projekt sollen in kleinere, logisch zusammenhängende Module aufgeteilt werden. Zielgröße: **maximal 500 Zeilen pro Datei**. Dies verbessert Wartbarkeit, Testbarkeit und Lesbarkeit des Codes.

---

## Dateien-Übersicht

### 🔴 KRITISCH (>1500 Zeilen) - Höchste Priorität

| Datei | Zeilen | Typ | Priorität |
|-------|--------|-----|-----------|
| `llars-frontend/src/components/Judge/JudgeSession.vue` | 4.191 | Vue | P1 |
| `app/routes/judge/judge_routes.py` | 2.596 | Python | P1 |
| `app/routes/oncoco/oncoco_routes.py` | 1.934 | Python | P1 |
| `llars-frontend/src/components/Judge/JudgeResults.vue` | 1.808 | Vue | P1 |
| `llars-frontend/src/components/OnCoCo/OnCoCoResults.vue` | 1.533 | Vue | P1 |

### 🟠 HOCH (1000-1500 Zeilen)

| Datei | Zeilen | Typ | Priorität |
|-------|--------|-----|-----------|
| `llars-frontend/src/components/Admin/sections/AdminRAGSection.vue` | 1.406 | Vue | P2 |
| `llars-frontend/src/components/PromptEngineering/PromptEngineeringDetail.vue` | 1.373 | Vue | P2 |
| `llars-frontend/src/components/Judge/WorkerLane.vue` | 1.350 | Vue | P2 |
| `llars-frontend/src/components/Admin/CrawlerAdmin/WebCrawlerTool.vue` | 1.298 | Vue | P2 |
| `app/db/tables.py` | 1.260 | Python | P2 |
| `app/routes/rag/RAGRoutes.py` | 1.202 | Python | P2 |
| `llars-frontend/src/components/Ranker/RankerDetail.vue` | 1.031 | Vue | P2 |
| `app/services/crawler/web_crawler.py` | 1.024 | Python | P2 |

### 🟡 MITTEL (700-1000 Zeilen)

| Datei | Zeilen | Typ | Priorität |
|-------|--------|-----|-----------|
| `llars-frontend/src/components/Admin/ChatbotAdmin/ChatbotEditor.vue` | 901 | Vue | P3 |
| `llars-frontend/src/components/HistoryGenerator/HistoryGenerationDetail.vue` | 883 | Vue | P3 |
| `llars-frontend/src/components/OnCoCo/MatrixComparisonMetrics.vue` | 880 | Vue | P3 |
| `llars-frontend/src/components/comparison/ComparisonChat.vue` | 855 | Vue | P3 |
| `llars-frontend/src/components/Judge/JudgeConfig.vue` | 835 | Vue | P3 |
| `llars-frontend/src/components/Admin/AdminRAG.vue` | 835 | Vue | P3 |
| `llars-frontend/src/components/OnCoCo/OnCoCoInfo.vue` | 780 | Vue | P3 |
| `llars-frontend/src/components/parts/ScenarioDetailsDialog.vue` | 771 | Vue | P3 |
| `llars-frontend/src/components/Orga/Documentation.vue` | 740 | Vue | P3 |
| `llars-frontend/src/components/PromptEngineering/PromptEngineering.vue` | 734 | Vue | P3 |
| `llars-frontend/src/components/ChatWithBots.vue` | 728 | Vue | P3 |
| `llars-frontend/src/components/parts/CreateScenarioDialog.vue` | 714 | Vue | P3 |
| `app/services/oncoco/oncoco_service.py` | 719 | Python | P3 |
| `app/workers/judge_worker_pool.py` | 700 | Python | P3 |
| `llars-frontend/src/components/PromptEngineering/sidebar.vue` | 700 | Vue | P3 |

### 🟢 NIEDRIG (500-700 Zeilen)

| Datei | Zeilen | Typ | Priorität |
|-------|--------|-----|-----------|
| `llars-frontend/src/components/OnCoCo/OnCoCoOverview.vue` | 676 | Vue | P4 |
| `app/ComparisonFunctions.py` | 673 | Python | P4 |
| `app/services/judge/kia_sync_service.py` | 623 | Python | P4 |
| `app/db/db.py` | 622 | Python | P4 |
| `app/services/oncoco/oncoco_labels.py` | 602 | Python | P4 |
| `app/services/judge/judge_service.py` | 576 | Python | P4 |
| `llars-frontend/src/components/Admin/ChatbotAdmin/ChatbotManager.vue` | 568 | Vue | P4 |
| `app/services/permission_service.py` | 562 | Python | P4 |
| `app/services/chatbot/chat_service.py` | 552 | Python | P4 |
| `llars-frontend/src/components/Admin/AdminUserProgressStats.vue` | 545 | Vue | P4 |
| `app/routes/chatbot/chatbot_routes.py` | 530 | Python | P4 |
| `llars-frontend/src/components/Chat.vue` | 527 | Vue | P4 |
| `app/services/chatbot/chatbot_service.py` | 522 | Python | P4 |
| `app/workers/judge_worker.py` | 505 | Python | P4 |
| `llars-frontend/src/components/FloatingChat.vue` | 504 | Vue | P4 |

---

## Splitting-Strategien

### Backend (Python)

#### 1. Routes aufteilen nach Funktion

**Beispiel: `judge_routes.py` (2.596 Zeilen)**

```
app/routes/judge/
├── __init__.py              # Blueprint-Registrierung
├── session_routes.py        # Session CRUD (~400 Zeilen)
├── comparison_routes.py     # Comparison Endpoints (~400 Zeilen)
├── evaluation_routes.py     # Evaluation/Results (~400 Zeilen)
├── kia_sync_routes.py       # GitLab Sync (~300 Zeilen)
├── statistics_routes.py     # Statistiken (~300 Zeilen)
└── stream_routes.py         # Streaming Endpoints (~300 Zeilen)
```

#### 2. Models aufteilen nach Domain

**Beispiel: `tables.py` (1.260 Zeilen)**

```
app/db/models/
├── __init__.py              # Alle Models exportieren
├── user.py                  # User, UserGroup, UserRole (~150 Zeilen)
├── permission.py            # Permission, Role, etc. (~200 Zeilen)
├── judge.py                 # JudgeSession, Comparison, etc. (~250 Zeilen)
├── rag.py                   # RAGCollection, Document, etc. (~200 Zeilen)
├── chatbot.py               # Chatbot, Conversation, etc. (~150 Zeilen)
├── oncoco.py                # OnCoCoAnalysis, Labels (~150 Zeilen)
├── pillar.py                # PillarThread, Statistics (~100 Zeilen)
└── scenario.py              # Scenario, Rating models (~150 Zeilen)
```

#### 3. Services aufteilen nach Verantwortlichkeit

**Beispiel: `web_crawler.py` (1.024 Zeilen)**

```
app/services/crawler/
├── __init__.py
├── crawler_service.py       # Hauptservice (~300 Zeilen)
├── url_queue.py             # URL-Queue-Management (~200 Zeilen)
├── html_parser.py           # HTML-Extraktion (~200 Zeilen)
├── sitemap_parser.py        # Sitemap-Verarbeitung (~150 Zeilen)
└── robots_handler.py        # robots.txt Handling (~100 Zeilen)
```

---

### Frontend (Vue)

#### 1. Komponenten in Sub-Komponenten aufteilen

**Beispiel: `JudgeSession.vue` (4.191 Zeilen)**

```
llars-frontend/src/components/Judge/JudgeSession/
├── JudgeSession.vue         # Hauptcontainer (~300 Zeilen)
├── SessionHeader.vue        # Header mit Stats (~200 Zeilen)
├── SessionControls.vue      # Play/Pause/Stop (~150 Zeilen)
├── WorkerGrid.vue           # Worker-Lane-Container (~200 Zeilen)
├── ComparisonQueue.vue      # Queue-Anzeige (~300 Zeilen)
├── ComparisonDetail.vue     # Aktiver Vergleich (~400 Zeilen)
├── StreamOutput.vue         # LLM-Stream-Viewer (~250 Zeilen)
├── SessionProgress.vue      # Fortschrittsanzeige (~150 Zeilen)
└── composables/
    ├── useSessionSocket.js  # Socket.IO Logic (~200 Zeilen)
    ├── useSessionState.js   # State Management (~200 Zeilen)
    └── useWorkerManagement.js # Worker Logic (~150 Zeilen)
```

#### 2. Logik in Composables auslagern

**Prinzip:**
- Template: Nur Darstellung
- Script: Nur Orchestrierung
- Composables: Business-Logik, API-Calls, State

**Beispiel:**
```javascript
// Vorher: Alles in einer Komponente
// Nachher:
import { useJudgeSession } from './composables/useJudgeSession'
import { useSocketEvents } from './composables/useSocketEvents'

const { session, workers, queue } = useJudgeSession(sessionId)
const { connect, disconnect } = useSocketEvents(sessionId)
```

#### 3. Shared Components extrahieren

Wiederverwendbare UI-Elemente:
- `StatCard.vue` - Statistik-Karten
- `ProgressRing.vue` - Fortschrittsanzeige
- `StreamViewer.vue` - LLM-Output-Anzeige
- `ThreadPreview.vue` - Thread-Vorschau
- `ConfirmDialog.vue` - Bestätigungs-Dialoge

---

## Vorgeschlagene Ordnerstruktur

### Backend

```
app/
├── routes/
│   ├── judge/
│   │   ├── __init__.py
│   │   ├── session_routes.py
│   │   ├── comparison_routes.py
│   │   ├── evaluation_routes.py
│   │   ├── kia_sync_routes.py
│   │   └── statistics_routes.py
│   ├── oncoco/
│   │   ├── __init__.py
│   │   ├── analysis_routes.py
│   │   ├── matrix_routes.py
│   │   └── comparison_routes.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── collection_routes.py
│   │   ├── document_routes.py
│   │   └── search_routes.py
│   └── chatbot/
│       ├── __init__.py
│       ├── chatbot_routes.py
│       └── conversation_routes.py
├── db/
│   ├── __init__.py
│   ├── base.py
│   └── models/
│       ├── __init__.py
│       ├── user.py
│       ├── permission.py
│       ├── judge.py
│       ├── rag.py
│       ├── chatbot.py
│       ├── oncoco.py
│       └── scenario.py
└── services/
    ├── crawler/
    │   ├── __init__.py
    │   ├── crawler_service.py
    │   ├── url_queue.py
    │   └── html_parser.py
    └── judge/
        ├── __init__.py
        ├── judge_service.py
        ├── evaluation_service.py
        └── statistics_service.py
```

### Frontend

```
llars-frontend/src/components/
├── Judge/
│   ├── JudgeSession/
│   │   ├── JudgeSession.vue
│   │   ├── SessionHeader.vue
│   │   ├── WorkerGrid.vue
│   │   └── composables/
│   ├── JudgeResults/
│   │   ├── JudgeResults.vue
│   │   ├── StatisticsPanel.vue
│   │   ├── LeaderboardTable.vue
│   │   └── ExportPanel.vue
│   └── WorkerLane/
│       ├── WorkerLane.vue
│       ├── WorkerProgress.vue
│       └── EvaluationDisplay.vue
├── OnCoCo/
│   ├── Results/
│   │   ├── OnCoCoResults.vue
│   │   ├── LabelDistribution.vue
│   │   └── TransitionMatrix.vue
│   └── ...
├── Admin/
│   ├── RAG/
│   │   ├── AdminRAGSection.vue
│   │   ├── CollectionList.vue
│   │   └── DocumentManager.vue
│   └── ...
└── shared/
    ├── StatCard.vue
    ├── ProgressRing.vue
    ├── StreamViewer.vue
    └── ConfirmDialog.vue
```

---

## Splitting-Regeln

### Allgemein

1. **Max 500 Zeilen pro Datei** - Harte Grenze
2. **Single Responsibility** - Jede Datei hat eine klare Aufgabe
3. **Keine zirkulären Abhängigkeiten** - Klare Import-Hierarchie
4. **Exports in `__init__.py`** - Saubere öffentliche API

### Python-spezifisch

1. Routes nach HTTP-Verb oder Resource gruppieren
2. Services nach Use-Case trennen
3. Models nach Domain-Bereich trennen
4. Helpers/Utils in eigene Dateien

### Vue-spezifisch

1. Template < 200 Zeilen → sonst Sub-Komponenten
2. Script < 300 Zeilen → sonst Composables
3. Styles in eigene Dateien bei > 100 Zeilen
4. Wiederverwendbare Teile → shared/

---

## Implementierungs-Reihenfolge

### Phase 1: Backend Models (tables.py)
**Begründung:** Basis für alles andere, keine Abhängigkeiten

### Phase 2: Backend Routes (judge_routes.py)
**Begründung:** Größte Datei, höchster Impact

### Phase 3: Frontend Judge (JudgeSession.vue)
**Begründung:** Kritischste und größte UI-Komponente

### Phase 4: Backend Routes (oncoco_routes.py, RAGRoutes.py)
**Begründung:** Zweitgrößte Route-Dateien

### Phase 5: Frontend OnCoCo & Admin
**Begründung:** Nächstgrößte Vue-Komponenten

### Phase 6: Restliche Dateien
**Begründung:** Kleinere Dateien, weniger kritisch

---

## Nicht-funktionale Anforderungen

| Anforderung | Beschreibung |
|-------------|--------------|
| **Keine Breaking Changes** | Alle bestehenden Imports müssen weiter funktionieren |
| **Tests bleiben grün** | Keine Regression in Funktionalität |
| **Hot-Reload** | Frontend-Änderungen sofort sichtbar |
| **Backwards Compatibility** | Alte Pfade über Re-Exports verfügbar |

---

## Risiken

| Risiko | Mitigation |
|--------|------------|
| Zirkuläre Imports | Klare Layer-Architektur definieren |
| Vergessene Imports | Automatisierte Import-Prüfung |
| Breaking Changes | Re-Exports in `__init__.py` |
| Merge-Konflikte | Kleine, atomare Commits |

---

## Abnahme-Kriterien

- [ ] Alle Dateien unter 500 Zeilen
- [ ] Keine neuen Lint-Fehler
- [ ] Alle Tests grün
- [ ] Anwendung startet und funktioniert
- [ ] Hot-Reload funktioniert
- [ ] Keine zirkulären Imports

---

## Offene Fragen

- [ ] Sollen alte Import-Pfade deprecated werden oder dauerhaft als Re-Exports bestehen bleiben?
- [ ] Priorität: Backend-first oder Frontend-first?

---

## Reviewer

| Reviewer | Datum | Status |
|----------|-------|--------|
| Philipp | - | Ausstehend |
