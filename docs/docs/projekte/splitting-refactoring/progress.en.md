# Splitting & Refactoring - Progress

!!! success "📋 Status: Largely completed"
    **Progress:** 14 major refactorings completed (see CLAUDE.md)

**Concept:** [Splitting & Refactoring Concept](konzept.md)
**Implementation:** [Splitting & Refactoring Implementation](umsetzung.md)
**Started:** November 2025
**As of:** March 2026

---

## Progress Overview

```mermaid
gantt
    title Splitting & Refactoring Progress
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
    Remaining Files               :p6, after p5, 2d
```

---

## Phase Checklist

### Phase 1: Backend Models (`tables.py` → 8 files)
- [ ] Create folder structure `app/db/models/`
- [ ] Create `user.py`
- [ ] Create `permission.py`
- [ ] Create `judge.py`
- [ ] Create `rag.py`
- [ ] Create `chatbot.py`
- [ ] Create `oncoco.py`
- [ ] Create `pillar.py`
- [ ] Create `scenario.py`
- [ ] `__init__.py` with re-exports
- [ ] Mark `tables.py` as deprecated
- [ ] Tests green

### Phase 2: Backend Routes (`judge_routes.py` → 6 files)
- [ ] Create `session_routes.py`
- [ ] Create `comparison_routes.py`
- [ ] Create `evaluation_routes.py`
- [ ] Create `kia_sync_routes.py`
- [ ] Create `statistics_routes.py`
- [ ] Create `stream_routes.py`
- [ ] `__init__.py` with blueprint registration
- [ ] Mark old file as deprecated
- [ ] Tests green

### Phase 3: Frontend Judge (`JudgeSession.vue` → 8+ components)
- [ ] Create folder structure
- [ ] `useSessionSocket.js` composable
- [ ] `useSessionState.js` composable
- [ ] `SessionHeader.vue` component
- [ ] `SessionControls.vue` component
- [ ] `WorkerGrid.vue` component
- [ ] `ComparisonQueue.vue` component
- [ ] `StreamOutput.vue` component
- [ ] Refactor main component
- [ ] Hot reload works
- [ ] Functionality identical

### Phase 4: Backend Routes (oncoco, RAG)
- [ ] Split `oncoco_routes.py`
- [ ] Split `RAGRoutes.py`
- [ ] Tests green

### Phase 5: Frontend OnCoCo & Admin
- [ ] Split `OnCoCoResults.vue`
- [ ] Split `AdminRAGSection.vue`
- [ ] Split `WorkerLane.vue`
- [ ] Functionality identical

### Phase 6: Remaining Files
- [ ] Identify all files > 500 lines
- [ ] Split systematically
- [ ] Final validation

---

## Git Commits

| Date | Commit | Description | Phase |
|------|--------|-------------|-------|
| - | - | - | - |

---

## Statistics

### Baseline

| Category | File count | Total lines |
|----------|------------|-------------|
| > 1500 lines | 5 | ~12,000 |
| 1000-1500 lines | 8 | ~9,500 |
| 700-1000 lines | 15 | ~12,000 |
| 500-700 lines | 15 | ~8,500 |
| **Total** | **43** | **~42,000** |

### After Refactor (Target)

| Category | File count | Total lines |
|----------|------------|-------------|
| > 500 lines | 0 | 0 |
| 300-500 lines | ~30 | ~12,000 |
| < 300 lines | ~80 | ~30,000 |
| **Total** | **~110** | **~42,000** |

---

## Open Items

### Blockers

| Problem | Impact | Status |
|---------|--------|--------|
| - | - | - |

### To‑Do (Next Steps)

1. [ ] Get concept reviewed
2. [ ] Start Phase 1 (backend models)
3. [ ] After each phase: validate + commit

### Questions for Reviewer

- [ ] Should old import paths remain as re-exports permanently?
- [ ] Priority: backend-first or frontend-first?
- [ ] Separate feature branch or direct to main?

---

## Changelog

### 2025-11-28
- 📋 Concept created
- 📋 Implementation template created
- 📋 Progress tracking set up

---

## Completed Refactorings (as of March 2026)

| File | Before | After | Reduction |
|------|--------|-------|-----------|
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

## Notes

> Important decisions during implementation are documented here.

- **2025-11-28:** Project initialized. Waiting for concept review.
- **2026-01-27:** 14 major refactorings completed. Backend: 425 files, ~126,000 lines. Frontend: 577 files, ~193,000 lines.
