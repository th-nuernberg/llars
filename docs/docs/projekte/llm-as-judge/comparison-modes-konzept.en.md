# LLM Evaluators: Advanced Comparison Modes & Multi-Worker (Legacy)

!!! warning "Legacy Concept (as of 2025)"
    These extensions refer to the historical Judge UI with sessions.
    In LLARS (as of 2026-02-05), LLM evaluators are primarily used as a **configuration in Scenario Manager**.
    The content serves as background and design history.

**Version:** 1.0
**Date:** November 26, 2025
**Status:** Legacy (historically implemented)

---

## Table of contents

1. [Overview](#overview)
2. [Comparison modes](#comparison-modes)
3. [Multi-worker architecture](#multi-worker-architecture)
4. [ELO rating system](#elo-rating-system)
5. [UI concept](#ui-concept)
6. [Implementation phases](#implementation-phases)
7. [API reference](#api-reference)

---

## Overview

### Historical status (2025)

The LLM evaluator system supported multiple comparison modes (`pillar_sample`, `round_robin`, `free_for_all`)
including optional position swap. Processing ran via a **JudgeWorkerPool** with configurable
parallelization (`worker_count`).

### Current state in LLARS

- LLM evaluation is configured per scenario (Scenario Wizard).
- Selection of system and custom provider models.
- Optional auto-start after scenario creation.
- Live status and results in Scenario Manager (Evaluation/Results tabs).

### Implemented extensions

1. Flexible comparison modes: different strategies for different use cases
2. Multi-worker parallelization: multiple workers for faster processing
3. ELO rating: thread-level ranking for detailed analysis
4. Extended statistics: consistency, bias, thread performance

---

## Comparison modes

### 1. Pillar sample (standard)

```
Mode: pillar_sample
```

**Description:**
- Pillar pairs are formed (e.g. pillar 1 vs pillar 3)
- N random threads are selected per pair and compared 1:1
- Thread A1 vs B1, Thread A2 vs B2, etc.

**Formula:**
```
Comparisons = pillar pairs × samples × (2 if position swap)
            = (n × (n-1) / 2) × samples × swap_multiplier
```

**Example (pillars 1, 3, 5 with 10 samples):**
```
Pillar pairs: 3 (1v3, 1v5, 3v5)
Comparisons: 3 × 10 × 2 = 60
```

**Use case:** Quick overview of which pillar performs better on average

---

### 2. Round robin (implemented)

```
Mode: round_robin
```

**Description:**
- Every thread in a pillar plays against every thread in the other pillar
- Full tournament within pillar pairings
- Enables thread-level statistics within the pillar context

**Formula:**
```
For pillar pair (i, j):
  comparisons = threads_in_i × threads_in_j

Total = Σ (n_i × n_j) for all pillar pairs
```

**Example (pillars 1, 3, 5 with 10 threads each):**
```
Pillar 1 vs 3: 10 × 10 = 100 comparisons
Pillar 1 vs 5: 10 × 10 = 100 comparisons
Pillar 3 vs 5: 10 × 10 = 100 comparisons
─────────────────────────────────────────
Total:                300 comparisons
With position swap:   600 comparisons
```

**Use case:** Comprehensive pillar analysis with thread-level statistics

---

### 3. Free for all (implemented)

```
Mode: free_for_all
```

**Description:**
- **All** threads against **all** other threads
- Pillar assignment is ignored during pairing
- Enables absolute ranking of all threads
- Pillars are only used for aggregation/analysis

**Formula:**
```
Comparisons = N × (N-1) / 2
```

**Example (30 threads total):**
```
30 × 29 / 2 = 435 comparisons
With position swap: 870 comparisons
```

**Database change:**
- Threads from the same pillar can compete
- `pillar_a` and `pillar_b` can be identical

**Use case:**
- Identify the best/worst threads overall
- ELO rating for each thread
- Consistency analysis on thread level
- Discover cross-pillar surprises (e.g. weak thread from a "good" pillar)

---

### Comparison overview

| Mode | Granularity | Complexity | Runtime | Use case |
|------|-------------|------------|---------|----------|
| `pillar_sample` | Pillar | O(n^2) pillars | Short | Quick overview |
| `round_robin` | Thread (per pairing) | O(n^2) per pair | Medium | Pillar comparison |
| `free_for_all` | Thread (all) | O(N^2) total | Long | Full ranking |

---

## Multi-worker architecture

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    JudgeWorkerPool                          │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Worker 0 │  │Worker 1 │  │Worker 2 │  │Worker 3 │  ...   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴─────┬──────┴────────────┘              │
│                          │                                  │
│                    ┌─────▼─────┐                            │
│                    │   Queue   │  (DB with row-level lock)   │
│                    │  PENDING  │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │    Socket.IO Room     │
              │  judge_session_{id}   │
              └───────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Client 1 │   │ Client 2 │   │ Client 3 │
    └──────────┘   └──────────┘   └──────────┘
```

### Worker pool implementation

```python
class JudgeWorkerPool:
    """
    Manages multiple parallel workers for a session.
    """

    def __init__(self, session_id: int, worker_count: int, app):
        self.session_id = session_id
        self.worker_count = min(worker_count, 5)  # Max 5 workers
        self.workers: List[JudgeWorker] = []
        self.app = app

    def start(self):
        """Start all workers."""
        for i in range(self.worker_count):
            worker = JudgeWorker(
                session_id=self.session_id,
                worker_id=i,
                app=self.app
            )
            self.workers.append(worker)
            worker.start()

    def stop(self):
        """Stop all workers gracefully."""
        for worker in self.workers:
            worker.stop()
        self.workers.clear()
```

### Thread-safe comparison assignment

```python
def _get_next_comparison(self, worker_id: int):
    """
    Fetch the next available comparison with DB-level lock.

    Uses `FOR UPDATE SKIP LOCKED` to avoid race conditions.
    """
    with db.session.begin_nested():
        comparison = JudgeComparison.query.filter_by(
            session_id=self.session_id,
            status=JudgeComparisonStatus.PENDING
        ).with_for_update(skip_locked=True) \
         .order_by(JudgeComparison.queue_position) \
         .first()

        if comparison:
            comparison.status = JudgeComparisonStatus.RUNNING
            comparison.worker_id = worker_id
            comparison.started_at = datetime.now()
            db.session.commit()

        return comparison
```

### Socket.IO events with worker ID

```javascript
// Server -> client events

// Comparison starts on a worker
socket.emit('judge:comparison_start', {
    session_id: 123,
    worker_id: 0,           // NEW
    comparison_id: 456,
    thread_a_id: 12,
    thread_b_id: 45,
    pillar_a: 1,
    pillar_b: 3
});

// LLM stream from a worker
socket.emit('judge:llm_stream', {
    session_id: 123,
    worker_id: 0,           // NEW
    token: '{"winner":'
});

// Comparison completed
socket.emit('judge:comparison_complete', {
    session_id: 123,
    worker_id: 0,           // NEW
    winner: 'A',
    confidence: 0.85
});

// Aggregated status of all workers
socket.emit('judge:workers_status', {
    session_id: 123,
    workers: [
        { worker_id: 0, status: 'running', comparison_id: 456 },
        { worker_id: 1, status: 'running', comparison_id: 457 },
        { worker_id: 2, status: 'idle', comparison_id: null }
    ],
    queue_pending: 152,
    completed: 135,
    total: 300
});
```

---

## ELO rating system

### Overview

The ELO system enables a relative ranking of all threads based on their comparison results.

**Parameters:**
- **Start ELO:** 1500 (for all threads)
- **K factor:** 32 (standard chess value)
- **Scope:** session-based (not persistent across sessions)

### ELO calculation

```python
def calculate_elo_change(rating_a: float, rating_b: float,
                         winner: str, k: int = 32) -> tuple[float, float]:
    """
    Calculate ELO changes after a match.

    Args:
        rating_a: Current ELO of thread A
        rating_b: Current ELO of thread B
        winner: 'A', 'B', or 'TIE'
        k: K factor (higher = larger changes)

    Returns:
        Tuple (new_rating_a, new_rating_b)
    """
    # Expected win probabilities
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 - expected_a

    # Actual outcome
    if winner == 'A':
        score_a, score_b = 1.0, 0.0
    elif winner == 'B':
        score_a, score_b = 0.0, 1.0
    else:  # TIE
        score_a, score_b = 0.5, 0.5

    # New ratings
    new_rating_a = rating_a + k * (score_a - expected_a)
    new_rating_b = rating_b + k * (score_b - expected_b)

    return new_rating_a, new_rating_b
```

### Database schema

```sql
-- New table for thread ELO (session-scoped)
CREATE TABLE thread_elo_scores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    thread_id INT NOT NULL,
    pillar_number INT NOT NULL,
    elo_score FLOAT DEFAULT 1500,
    matches_played INT DEFAULT 0,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    ties INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES judge_sessions(id),
    FOREIGN KEY (thread_id) REFERENCES email_threads(id),
    UNIQUE KEY unique_session_thread (session_id, thread_id)
);
```

### Thread leaderboard response

```json
{
    "leaderboard": [
        {
            "rank": 1,
            "thread_id": 42,
            "pillar": 3,
            "pillar_name": "Anonymized data",
            "elo_score": 1847,
            "matches_played": 29,
            "wins": 22,
            "losses": 5,
            "ties": 2,
            "win_rate": 0.76,
            "avg_confidence": 0.82,
            "avg_likert_scores": {
                "counsellor_coherence": 4.2,
                "client_coherence": 4.0,
                "quality": 4.5,
                "empathy": 4.3,
                "authenticity": 4.1,
                "solution_orientation": 4.4
            }
        }
        // ... more threads
    ],
    "pillar_aggregates": {
        "1": { "avg_elo": 1520, "threads": 10 },
        "3": { "avg_elo": 1580, "threads": 10 },
        "5": { "avg_elo": 1400, "threads": 10 }
    }
}
```

---

## UI concept

### JudgeConfig.vue - extended configuration

```
┌─────────────────────────────────────────────────────────────────────────┐
│  New Judge Session                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Session name: [____________________________]                           │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Select pillars:                                                        │
│  [x] Pillar 1   [x] Pillar 3   [x] Pillar 5   [ ] Pillar 2   [ ] Pillar 4│
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Comparison mode:                                                       │
│                                                                         │
│  (o) Pillar Sample (fast)                                               │
│      - Random samples per pillar pair                                   │
│      Estimated comparisons: ~60                                         │
│                                                                         │
│  ( ) Round Robin (comprehensive)                                        │
│      - Every thread in one pillar vs every in the other                 │
│      Estimated comparisons: ~300                                        │
│                                                                         │
│  ( ) Free For All (complete)                                            │
│      - Every thread vs every other thread                               │
│      Estimated comparisons: ~435                                        │
│      Warning: long runtime (~72 minutes with 1 worker)                  │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Parallel workers: [===o===] 3                                          │
│  Info: 3 workers in parallel. Estimated time: ~24 minutes               │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  [x] Enable position swap (doubles comparisons)                         │
│  [x] Calculate ELO rating                                               │
│                                                                         │
│  Max threads per pillar: [__15__] (optional, for Round Robin/FFA)       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Summary:                                                               │
│  - 3 pillars x ~10 threads = 30 threads                                 │
│  - Free For All: 435 base comparisons                                   │
│  - With position swap: 870 comparisons                                  │
│  - With 3 workers: ~29 minutes                                          │
│                                                                         │
│                                        [Create & start session]         │
└─────────────────────────────────────────────────────────────────────────┘
```

### JudgeSession.vue - multi-worker live view

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Session: Free-For-All Evaluation                            [Pause]   │
│  ████████████████████░░░░░░░░░░░░░░░░░░░  45% (392/870)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Workers: [●W1] [●W2] [●W3]  <- click to focus                           │
│                                                                         │
├────────────────────┬────────────────────┬────────────────────┬──────────┤
│                    │                    │                    │          │
│  ┌──────────────┐  │  ┌──────────────┐  │  ┌──────────────┐  │  Queue   │
│  │  Worker 1    │  │  │  Worker 2    │  │  │  Worker 3    │  │  ──────  │
│  │  ● Active    │  │  │  ● Active    │  │  │  ● Active    │  │  478     │
│  ├──────────────┤  │  ├──────────────┤  │  ├──────────────┤  │ pending  │
│  │              │  │  │              │  │  │              │  │          │
│  │ T#12 (P1)    │  │  │ T#7 (P3)     │  │  │ T#23 (P5)    │  │  #394    │
│  │     vs       │  │  │     vs       │  │  │     vs       │  │  T12vT89 │
│  │ T#45 (P3)    │  │  │ T#89 (P5)    │  │  │ T#34 (P1)    │  │          │
│  │              │  │  │              │  │  │              │  │  #395    │
│  ├──────────────┤  │  ├──────────────┤  │  ├──────────────┤  │  T7vT34  │
│  │              │  │  │              │  │  │              │  │          │
│  │ {"winner":  │  │  │ {"step_2":  │  │  │ {"scores":  │  │  #396    │
│  │  "A", ...   │  │  │  "The co...  │  │  │  {"A": {... │  │  T23vT45 │
│  │  ___         │  │  │  ___         │  │  │  ___         │  │          │
│  │              │  │  │              │  │  │              │  │   ...    │
│  ├──────────────┤  │  ├──────────────┤  │  ├──────────────┤  │          │
│  │              │  │  │              │  │  │              │  │          │
│  │ A: ●●●●o    │  │  │ A: ●●●oo    │  │  │ A: ●●●●●    │  │          │
│  │ B: ●●●oo    │  │  │ B: ●●●●o    │  │  │ B: ●●ooo    │  │          │
│  │              │  │  │              │  │  │              │  │          │
│  │ -> A (82%)   │  │  │ -> ???      │  │  │ -> A (91%)   │  │          │
│  │              │  │  │              │  │  │              │  │          │
│  └──────────────┘  │  └──────────────┘  │  └──────────────┘  │          │
│                    │                    │                    │          │
│  [Fullscreen]      │  [Fullscreen]      │  [Fullscreen]      │          │
│                    │                    │                    │          │
└────────────────────┴────────────────────┴────────────────────┴──────────┘
```

### JudgeResults.vue - extensions for Free For All

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Results: Free-For-All Evaluation                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Overview] [Thread Leaderboard] [ELO Distribution] [Pillar Matrix]     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Thread Leaderboard (Top 10)                                            │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Rank │ Thread │ Pillar │ ELO  │ W/L/T    │ Win%  │ Avg Conf │ Avg Score │
│  ─────┼────────┼───────┼──────┼──────────┼───────┼──────────┼──────────│
│  1    │ T#42   │ P3    │ 1847 │ 22/5/2   │ 76%   │ 82%      │ 4.2      │
│  2    │ T#17   │ P3    │ 1802 │ 20/6/3   │ 69%   │ 79%      │ 4.1      │
│  3    │ T#8    │ P1    │ 1756 │ 18/8/3   │ 62%   │ 75%      │ 3.9      │
│  4    │ T#91   │ P5    │ 1721 │ 17/9/3   │ 59%   │ 71%      │ 3.8      │
│  5    │ T#33   │ P1    │ 1698 │ 16/10/3  │ 55%   │ 68%      │ 3.7      │
│   ... │ ...    │ ...   │ ...  │ ...      │ ...   │ ...      │ ...      │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  ELO distribution by pillar                                             │
│                                                                         │
│  Pillar 1 │ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁ │ Avg 1520 │ Min: 1320 │ Max: 1756          │
│  Pillar 3 │ ▁▂▃▅▇███▇▅▃▂▁   │ Avg 1620 │ Min: 1380 │ Max: 1847          │
│  Pillar 5 │ ▁▃▅▆▇▆▅▃▂▁      │ Avg 1460 │ Min: 1280 │ Max: 1721          │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Surprise findings                                                      │
│                                                                         │
│  - T#8 (Pillar 1) performs 25% better than pillar average               │
│  - T#55 (Pillar 3) performs 30% worse than pillar average               │
│  - T#91 (Pillar 5) is the most consistent thread (sigma = 0.12)         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation phases

### Phase 1: Comparison modes backend (current)

**Files:**
- `app/routes/judge/judge_routes.py` - extended comparison generation
- `app/services/judge/comparison_generator.py` - new service class

**Tasks:**
1. Implement `round_robin` mode
2. Implement `free_for_all` mode
3. Validation and estimation endpoints

### Phase 2: Comparison modes frontend

**Files:**
- `llars-frontend/src/components/Judge/JudgeConfig.vue`

**Tasks:**
1. Radio group for mode selection
2. Dynamic comparison estimation
3. Warnings for long runtimes
4. Max threads per pillar option

### Phase 3: Multi-worker backend

**Files:**
- `app/workers/judge_worker.py` - worker pool
- `app/workers/judge_worker_pool.py` - new class
- `app/db/tables.py` - `worker_id` field

**Tasks:**
1. `JudgeWorkerPool` class
2. Thread-safe comparison assignment
3. Worker ID in Socket.IO events
4. Worker count in `config_json`

### Phase 4: Multi-worker frontend

**Files:**
- `llars-frontend/src/components/Judge/JudgeSession.vue`
- `llars-frontend/src/components/Judge/WorkerLane.vue` (new)
- `llars-frontend/src/components/Judge/JudgeConfig.vue`

**Tasks:**
1. Worker lane component
2. Multi-stream handling
3. Worker count slider
4. Responsive layout

### Phase 5: ELO rating system

**Files:**
- `app/db/tables.py` - `ThreadEloScore` table
- `app/services/judge/elo_service.py` (new)
- `app/routes/judge/judge_routes.py` - leaderboard endpoint
- `llars-frontend/src/components/Judge/JudgeResults.vue`

**Tasks:**
1. ELO calculation after each evaluation
2. Thread leaderboard API
3. ELO distribution visualization
4. Surprise findings

---

## API reference

### New/changed endpoints

#### POST /api/judge/sessions

**Request body (extended):**
```json
{
    "session_name": "Free-For-All Test",
    "pillar_ids": [1, 3, 5],
    "comparison_mode": "free_for_all",
    "max_threads_per_pillar": 15,
    "position_swap": true,
    "worker_count": 3,
    "calculate_elo": true
}
```

**comparison_mode values:**
- `pillar_sample` (default) - random samples per pillar pair
- `round_robin` - all threads in one pillar vs all threads in the other
- `free_for_all` - all threads vs all threads

#### GET /api/judge/sessions/{id}/estimate

**Response:**
```json
{
    "comparison_mode": "free_for_all",
    "total_threads": 30,
    "base_comparisons": 435,
    "with_position_swap": 870,
    "estimated_duration_minutes": 72,
    "with_workers": {
        "1": 72,
        "2": 36,
        "3": 24,
        "4": 18,
        "5": 15
    }
}
```

#### GET /api/judge/sessions/{id}/thread-leaderboard

**Response:**
```json
{
    "leaderboard": [
        {
            "rank": 1,
            "thread_id": 42,
            "pillar": 3,
            "elo_score": 1847,
            "matches_played": 29,
            "wins": 22,
            "losses": 5,
            "ties": 2,
            "win_rate": 0.76
        }
    ],
    "pillar_aggregates": {
        "1": { "avg_elo": 1520, "thread_count": 10 },
        "3": { "avg_elo": 1580, "thread_count": 10 },
        "5": { "avg_elo": 1400, "thread_count": 10 }
    }
}
```

#### GET /api/judge/sessions/{id}/elo-distribution

**Response:**
```json
{
    "pillars": {
        "1": {
            "name": "Role plays",
            "elo_scores": [1320, 1450, 1520, 1580, 1756],
            "mean": 1520,
            "median": 1520,
            "std_dev": 142,
            "min": 1320,
            "max": 1756
        }
    }
}
```

---

## Open items

- Rate limiting for many workers (LLM API)
- Worker failure recovery
- Partial results on abort
- Export with ELO data

---

**Author:** Claude (AI Assistant)
**Project:** LLARS - LLM Assisted Research System
