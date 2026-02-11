# Splitting & Refactoring - Concept

!!! warning "📋 Status: Concept"
    This project is in the **concept phase**.
    Goal: bring all files under 500 lines.

**Created:** 2025-11-28  
**Author:** Claude Code  
**Version:** 1.0

---

## Goal

All large files in the LLARS project should be split into smaller, logically grouped modules. Target size: **max 500 lines per file**. This improves maintainability, testability, and readability.

---

## File Overview

### 🔴 CRITICAL (>1500 lines) - Highest priority

| File | Lines | Type | Priority |
|------|-------|------|----------|
| `llars-frontend/src/components/Judge/JudgeSession.vue` | 4,191 | Vue | P1 |
| `app/routes/judge/judge_routes.py` | 2,596 | Python | P1 |
| `app/routes/oncoco/oncoco_routes.py` | 1,934 | Python | P1 |
| `llars-frontend/src/components/Judge/JudgeResults.vue` | 1,808 | Vue | P1 |
| `llars-frontend/src/components/OnCoCo/OnCoCoResults.vue` | 1,533 | Vue | P1 |

### 🟠 HIGH (1000-1500 lines)

| File | Lines | Type | Priority |
|------|-------|------|----------|
| `llars-frontend/src/components/Admin/sections/AdminRAGSection.vue` | 1,406 | Vue | P2 |
| `llars-frontend/src/components/PromptEngineering/PromptEngineeringDetail.vue` | 1,373 | Vue | P2 |
| `llars-frontend/src/components/Judge/WorkerLane.vue` | 1,350 | Vue | P2 |
| `llars-frontend/src/components/Admin/CrawlerAdmin/WebCrawlerTool.vue` | 1,298 | Vue | P2 |
| `app/db/tables.py` | 1,260 | Python | P2 |
| `app/routes/rag/RAGRoutes.py` | 1,202 | Python | P2 |
| `llars-frontend/src/components/Ranker/RankerDetail.vue` | 1,031 | Vue | P2 |
| `app/services/crawler/web_crawler.py` | 1,024 | Python | P2 |

### 🟡 MEDIUM (700-1000 lines)

| File | Lines | Type | Priority |
|------|-------|------|----------|
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

### 🟢 LOW (500-700 lines)

| File | Lines | Type | Priority |
|------|-------|------|----------|
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

## Splitting Strategies

### Backend (Python)

#### 1. Split routes by function

**Example: `judge_routes.py` (2,596 lines)**

```
app/routes/judge/
├── __init__.py              # Blueprint registration
├── session_routes.py        # Session CRUD (~400 lines)
├── comparison_routes.py     # Comparison endpoints (~400 lines)
├── evaluation_routes.py     # Evaluation/results (~400 lines)
├── kia_sync_routes.py       # GitLab sync (~300 lines)
├── statistics_routes.py     # Statistics (~300 lines)
└── stream_routes.py         # Streaming endpoints (~300 lines)
```

#### 2. Split models by domain

**Example: `tables.py` (1,260 lines)**

```
app/db/models/
├── __init__.py              # Export all models
├── user.py                  # User, UserGroup, UserRole (~150 lines)
├── permission.py            # Permission, Role, etc. (~200 lines)
├── judge.py                 # JudgeSession, Comparison, etc. (~250 lines)
├── rag.py                   # RAGCollection, Document, etc. (~200 lines)
├── chatbot.py               # Chatbot, Conversation, etc. (~150 lines)
├── oncoco.py                # OnCoCoAnalysis, Labels (~150 lines)
├── pillar.py                # PillarThread, Statistics (~100 lines)
└── scenario.py              # Scenario, Rating models (~150 lines)
```

#### 3. Split services by responsibility

**Example: `web_crawler.py` (1,024 lines)**

```
app/services/crawler/
├── __init__.py
├── crawler_service.py       # Core service (~300 lines)
├── url_queue.py             # URL queue management (~200 lines)
├── html_parser.py           # HTML extraction (~200 lines)
├── sitemap_parser.py        # Sitemap processing (~150 lines)
└── robots_handler.py        # robots.txt handling (~100 lines)
```

---

### Frontend (Vue)

#### 1. Split components into sub-components

**Example: `JudgeSession.vue` (4,191 lines)**

```
llars-frontend/src/components/Judge/JudgeSession/
├── JudgeSession.vue         # Main container (~300 lines)
├── SessionHeader.vue        # Header with stats (~200 lines)
├── SessionControls.vue      # Play/Pause/Stop (~150 lines)
├── WorkerGrid.vue           # Worker lane container (~200 lines)
├── ComparisonQueue.vue      # Queue display (~300 lines)
├── ComparisonDetail.vue     # Active comparison (~400 lines)
├── StreamOutput.vue         # LLM stream viewer (~250 lines)
├── SessionProgress.vue      # Progress display (~150 lines)
└── composables/
    ├── useSessionSocket.js  # Socket.IO logic (~200 lines)
    ├── useSessionState.js   # State management (~200 lines)
    └── useWorkerManagement.js # Worker logic (~150 lines)
```

#### 2. Move logic into composables

**Principle:**
- Template: presentation only
- Script: orchestration only
- Composables: business logic, API calls, state

**Example:**
```javascript
// Before: everything in one component
// After:
import { useJudgeSession } from './composables/useJudgeSession'
import { useSocketEvents } from './composables/useSocketEvents'

const { session, workers, queue } = useJudgeSession(sessionId)
const { connect, disconnect } = useSocketEvents(sessionId)
```

#### 3. Extract shared components

Reusable UI elements:
- `StatCard.vue` - stats cards
- `ProgressRing.vue` - progress display
- `StreamViewer.vue` - LLM output
- `ThreadPreview.vue` - thread preview
- `ConfirmDialog.vue` - confirmation dialogs

---

## Proposed Folder Structure

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
│   │   ├── statistics_routes.py
│   │   └── stream_routes.py
│   ├── oncoco/
│   │   ├── __init__.py
│   │   ├── analysis_routes.py
│   │   └── labels_routes.py
│   └── rag/
│       ├── __init__.py
│       ├── collection_routes.py
│       └── search_routes.py
│
├── services/
│   ├── crawler/
│   ├── judge/
│   ├── oncoco/
│   ├── rag/
│   └── chatbot/
│
└── db/
    └── models/
        ├── user.py
        ├── permission.py
        ├── judge.py
        ├── rag.py
        ├── chatbot.py
        ├── oncoco.py
        └── scenario.py
```

### Frontend

```
llars-frontend/src/components/
├── Judge/
│   └── JudgeSession/
│       ├── JudgeSession.vue
│       ├── SessionHeader.vue
│       ├── SessionControls.vue
│       └── ...
├── OnCoCo/
│   └── OnCoCoResults/
│       ├── OnCoCoResults.vue
│       ├── ResultsHeader.vue
│       └── ...
└── Admin/
    └── CrawlerAdmin/
        ├── WebCrawlerTool.vue
        ├── CrawlerSettings.vue
        └── ...
```

---

## Guidelines

1. **One responsibility per module**
2. **Keep components below 500 lines**
3. **Extract shared UI into common components**
4. **Use composables for business logic**
5. **Keep routes thin; move logic to services**

---

## Risks

- Large refactors can introduce regressions
- Test coverage may be insufficient
- Vue components might have tightly coupled state

---

## Next Steps

1. Confirm the priority list
2. Split P1 files first (judge routes + core views)
3. Add regression tests
4. Continue with P2/P3
