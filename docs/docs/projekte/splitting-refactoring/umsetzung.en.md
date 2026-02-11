# Splitting & Refactoring - Implementation

!!! info "🔧 Status: Ready for implementation"
    This document summarizes concrete implementation steps.
    See [Progress](progress.md) for current status.

**Concept:** [Splitting & Refactoring Concept](konzept.md)  
**Created:** 2025-11-28  
**Author:** Claude Code

---

## Overview

This document describes the step-by-step execution of the split/refactor work. For full code snippets and exact file content, refer to the German version (`umsetzung.md`).

### Implementation Order

1. Phase 1: Backend Models (`tables.py`)
2. Phase 2: Backend Routes (`judge_routes.py`)
3. Phase 3: Frontend Judge (`JudgeSession.vue`)
4. Phase 4: Backend Routes (oncoco, RAG)
5. Phase 5: Frontend OnCoCo & Admin
6. Phase 6: Remaining files

---

## Phase 1: Backend Models (`tables.py`)

**Goal:** Split `app/db/tables.py` (~1,260 lines) into domain model files under `app/db/models/`.

Key steps:
- Create `app/db/models/` structure and `__init__.py` re-exports
- Move models into `user.py`, `permission.py`, `judge.py`, `rag.py`, `chatbot.py`, `oncoco.py`, `pillar.py`, `scenario.py`
- Mark `tables.py` as deprecated (keep compatibility)

---

## Phase 2: Backend Routes (`judge_routes.py`)

**Goal:** Split `app/routes/judge/judge_routes.py` into smaller route modules.

Key steps:
- Introduce sub‑routes: `session_routes.py`, `comparison_routes.py`, `evaluation_routes.py`, `kia_sync_routes.py`, `statistics_routes.py`, `stream_routes.py`
- Wire them via `__init__.py`
- Keep route behavior unchanged

---

## Phase 3: Frontend Judge (`JudgeSession.vue`)

**Goal:** Split large Vue component into sub‑components + composables.

Key steps:
- Create folder `JudgeSession/`
- Extract UI components (header, controls, queue, stream, etc.)
- Move logic into composables (`useSessionSocket`, `useSessionState`, `useWorkerManagement`)

---

## Phase 4: Backend Routes (OnCoCo, RAG)

**Goal:** Split `oncoco_routes.py` and `RAGRoutes.py` into modules per responsibility.

---

## Phase 5: Frontend OnCoCo & Admin

**Goal:** Split large Vue components (OnCoCo results, Admin RAG section, WorkerLane).

---

## Phase 6: Remaining Files

**Goal:** Systematically split all remaining files > 500 lines and complete validation.

---

## Validation Checklist

- Behavior unchanged after split
- Imports/backward compatibility intact
- Tests green
- Hot reload works for Vue

---

## Notes

Detailed code snippets and templates are in the German implementation document.
