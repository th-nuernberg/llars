# LLM Evaluators Concept (Legacy) for LLARS
## Automated Email Thread Comparison with KIA Pillar Comparison

!!! warning "Legacy Concept (as of 2025)"
    This document describes the historical LLM-as-Judge concept with its own Judge UI and sessions.
    In LLARS (as of 2026-02-05), LLM evaluation is a **configuration in Scenario Manager** (Wizard + Evaluation/Results tabs).
    The content below serves as background and design history.

**Version:** 1.0
**Date:** November 25, 2025
**Author:** Claude Code

---

## Table of contents

1. [Summary](#1-summary)
2. [Research findings](#2-research-findings)
3. [Architecture overview](#3-architecture-overview)
4. [Phase plan](#4-phase-plan)
5. [Pydantic schema design](#5-pydantic-schema-design)
6. [UI/UX concept](#6-uiux-concept)
7. [Session management](#7-session-management)
8. [Queue system](#8-queue-system)
9. [Evaluation dashboard](#9-evaluation-dashboard)
10. [Test plan by phase](#10-test-plan-by-phase)

---

## 1. Summary

### Historical goal (2025)
Implementation of an automated **LLM evaluator** system in LLARS that:
- Compares email threads from different KIA pillars pairwise
- Enables live visualization of LLM evaluation
- Generates structured JSON ratings via a Pydantic schema
- Supports session-based work without an active browser
- Provides statistical analysis of pillar performance

### Current state in LLARS
- LLM evaluation is configured per scenario (Scenario Wizard).
- Selection of system and custom provider models.
- Optional auto-start after scenario creation.
- Live status and results in Scenario Manager (Evaluation/Results tabs).

### KIA pillars (from image)
| Pillar | Description | Threads |
|--------|-------------|---------|
| **Pillar 1** | Role plays | 50 |
| **Pillar 2** | From pillar 1 -> feature (generated subjects/situation descriptions) | 50 |
| **Pillar 3** | Fully anonymized and pseudonymized data | 83 |
| **Pillar 4** | Synthetically generated data | ∞ (theoretical) |
| **Pillar 5** | Data from tests (live testing student counselors) | 36 |

### Use of existing LLARS components
- **LiteLLM client** (`app/llm/litellm_client.py`) - API access
- **ComparisonSession/Evaluation tables** - extend data structure
- **Socket.IO infrastructure** - live streaming
- **Permission system** - access control
- **RAG queue pattern** - inspiration for job queue

---

## 2. Research findings

### 2.1 Existing LLARS metrics

#### Mail history rating metrics (already implemented)
```python
# app/db/tables.py - UserMailHistoryRating
counsellor_coherence_rating  # 1-5 Likert - counselor coherence
client_coherence_rating      # 1-5 Likert - client coherence
quality_rating               # 1-5 Likert - counseling quality
overall_rating               # Binary - authenticity/overall rating
feedback                     # TEXT - free-text feedback
```

These metrics are adopted as **evaluation criteria for the LLM evaluator**.


#### Existing comparison infrastructure
```python
# Already available:
ComparisonSession     # Session management
ComparisonMessage     # Message threads
ComparisonEvaluation  # AI/User selection + reasoning
```

### 2.2 LLM evaluator best practices (web research)

#### Pairwise comparison advantages
> "Pairwise evaluation closely mirrors human decision-making processes by focusing on relative preferences rather than assigning absolute scores."
> - [Evidently AI](https://www.evidentlyai.com/llm-guide/llm-as-a-judge)

> "Studies show that pairwise comparisons lead to more stable results and smaller differences between LLM judgments and human annotations."
> - [Cameron Wolfe](https://cameronrwolfe.substack.com/p/llm-as-a-judge)

#### Position bias mitigation
> "Position bias is identifiable when judgments consistently favor either the first or the second response. Nearly half of all verdicts were position-sensitive."
> - [arXiv Paper](https://arxiv.org/html/2406.07791v1)

**Solution:** position-swap strategy
```python
# Evaluation 1: A vs B
# Evaluation 2: B vs A
# If flipped -> tie/draw
```

#### Chain-of-thought for better evaluations
> "You should ask the LLM to output the rationale PRIOR to its score (as opposed to afterwards)."
> - [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)

#### Counseling-specific evaluation (CounselBench)
> "LLMs often outperform online human therapists in perceived quality, but experts frequently flag their outputs for safety concerns."
> - [CounselBench Paper](https://arxiv.org/html/2506.08584v1)

**Important dimensions for counseling evaluation:**
1. Empathy and emotional support
2. Problem understanding
3. Solution orientation
4. Language appropriateness
5. Professional boundaries
6. Therapeutic techniques

### 2.3 Pydantic for structured output

> "Instructor extracts structured data from any LLM with type safety, validation, and automatic retries."
> - [Instructor Docs](https://python.useinstructor.com/)

**Example pattern:**
```python
class Judgment(BaseModel):
    thought: str = Field(description="Step-by-step reasoning")
    justification: str = Field(description="Explanation for judgment")
    similarity: bool = Field(description="Final verdict")
```

---

## 3. Architecture overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Vue 3)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ JudgeConfig │  │ LiveEvaluation  │  │   JudgeResultsDashboard │  │
│  │   - Upload  │  │  - Streaming    │  │   - Säulen-Matrix       │  │
│  │   - Säulen  │  │  - JSON-Preview │  │   - Win/Loss Stats      │  │
│  │   - Queue   │  │  - Verlauf-View │  │   - Export              │  │
│  └─────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                              │                                       │
│                    Socket.IO (Bidirectional)                         │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          BACKEND (Flask)                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │  JudgeRoutes    │   │  JudgeService    │   │  QueueWorker     │  │
│  │  /api/judge/*   │──▶│  - Pydantic      │◀──│  - Background    │  │
│  │                 │   │  - LiteLLM       │   │  - Persistent    │  │
│  └─────────────────┘   └──────────────────┘   └──────────────────┘  │
│           │                    │                      │              │
│           ▼                    ▼                      ▼              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     MariaDB (Persistence)                      │ │
│  │  judge_sessions | judge_comparisons | judge_evaluations        │ │
│  │  pillar_threads | pillar_statistics                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LiteLLM Proxy                               │
│                  kiz1.in.ohmportal.de/llmproxy/v1                   │
│                    (Mistral / GPT-4o-mini)                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Phase plan

### Phase 1: Database & base structure (week 1-2)

#### 1.1 Create new tables

```python
# app/db/tables.py - Neue Tabellen

class PillarThread(db.Model):
    """Zuordnung von Threads zu KIA-Säulen"""
    __tablename__ = 'pillar_threads'

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey('email_threads.id'), nullable=False)
    pillar_number = Column(Integer, nullable=False)  # 1-5
    pillar_name = Column(String(100))  # "Rollenspiele", etc.
    metadata_json = Column(JSON)  # Zusätzliche Säulen-Metadaten
    created_at = Column(DateTime, default=datetime.utcnow)


class JudgeSession(db.Model):
    """Eine LLM Evaluator Evaluierungs-Session"""
    __tablename__ = 'judge_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    name = Column(String(255))  # Session-Name
    config_json = Column(JSON)  # Konfiguration (Model, Metriken, etc.)
    status = Column(Enum('created', 'queued', 'running', 'paused',
                         'completed', 'failed'), default='created')
    total_comparisons = Column(Integer, default=0)
    completed_comparisons = Column(Integer, default=0)
    current_comparison_id = Column(Integer)  # Aktuell laufender Vergleich
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class JudgeComparison(db.Model):
    """Ein einzelner paarweiser Vergleich"""
    __tablename__ = 'judge_comparisons'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('judge_sessions.id'), nullable=False)
    thread_a_id = Column(Integer, ForeignKey('email_threads.id'), nullable=False)
    thread_b_id = Column(Integer, ForeignKey('email_threads.id'), nullable=False)
    pillar_a = Column(Integer)  # Säule von Thread A
    pillar_b = Column(Integer)  # Säule von Thread B
    position_order = Column(Integer)  # 1 = A|B, 2 = B|A (für Swap)
    status = Column(Enum('pending', 'running', 'completed', 'failed'), default='pending')
    queue_position = Column(Integer)  # Position in Queue
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class JudgeEvaluation(db.Model):
    """Das Evaluationsergebnis eines Vergleichs"""
    __tablename__ = 'judge_evaluations'

    id = Column(Integer, primary_key=True)
    comparison_id = Column(Integer, ForeignKey('judge_comparisons.id'), nullable=False)

    # LLM Output (strukturiert)
    raw_response = Column(Text)  # Vollständige LLM-Antwort
    evaluation_json = Column(JSON)  # Parsed Pydantic-Objekt

    # Einzelne Metriken (denormalisiert für schnelle Queries)
    winner = Column(Enum('A', 'B', 'TIE'), nullable=False)

    # Scores pro Metrik (1-5)
    counsellor_coherence_a = Column(Float)
    counsellor_coherence_b = Column(Float)
    client_coherence_a = Column(Float)
    client_coherence_b = Column(Float)
    quality_a = Column(Float)
    quality_b = Column(Float)
    empathy_a = Column(Float)
    empathy_b = Column(Float)

    # Chain-of-Thought
    reasoning = Column(Text)
    confidence = Column(Float)  # 0.0 - 1.0

    # Position-Swap Tracking
    position_variant = Column(Integer)  # 1 oder 2

    # Timing
    llm_latency_ms = Column(Integer)
    token_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class PillarStatistics(db.Model):
    """Aggregierte Statistiken pro Säulen-Paar"""
    __tablename__ = 'pillar_statistics'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('judge_sessions.id'))
    pillar_a = Column(Integer)
    pillar_b = Column(Integer)
    wins_a = Column(Integer, default=0)
    wins_b = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    avg_confidence = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

#### 1.2 Create migration
```bash
flask db migrate -m "Add LLM Evaluator tables"
flask db upgrade
```

#### 1.3 Test criteria phase 1
- [ ] All tables created and migrated
- [ ] Foreign keys work
- [ ] CRUD operations for all entities
- [ ] Seed data for test pillars

---

### Phase 2: Pydantic schema & LLM integration (week 2-3)

#### 2.1 Pydantic evaluation schema

```python
# app/llm/judge_schema.py

from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class MetricScore(BaseModel):
    """Score für eine einzelne Metrik"""
    score_a: float = Field(ge=1.0, le=5.0, description="Score für Verlauf A (1-5)")
    score_b: float = Field(ge=1.0, le=5.0, description="Score für Verlauf B (1-5)")
    reasoning: str = Field(description="Begründung für die Scores")

class EvaluationCriteria(BaseModel):
    """Bewertungskriterien basierend auf LLARS-Metriken"""

    counsellor_coherence: MetricScore = Field(
        description="Kohärenz der beratenden Person: Wie logisch und zusammenhängend "
                    "sind die Antworten des Beraters?"
    )

    client_coherence: MetricScore = Field(
        description="Kohärenz der ratsuchenden Person: Wie realistisch und "
                    "nachvollziehbar verhält sich der Klient?"
    )

    quality: MetricScore = Field(
        description="Beratungsqualität: Wie gut ist die therapeutische Qualität "
                    "der Beratung insgesamt?"
    )

    empathy: MetricScore = Field(
        description="Empathie: Wie empathisch und verständnisvoll reagiert "
                    "der Berater auf den Klienten?"
    )

    authenticity: MetricScore = Field(
        description="Authentizität: Wie authentisch und natürlich wirkt "
                    "der gesamte Gesprächsverlauf?"
    )

    solution_orientation: MetricScore = Field(
        description="Lösungsorientierung: Wie gut werden konkrete Lösungsansätze "
                    "und Hilfestellungen angeboten?"
    )


class ChainOfThought(BaseModel):
    """Strukturiertes Reasoning vor der Entscheidung"""

    step_1_overview: str = Field(
        description="Kurze Zusammenfassung beider Verläufe"
    )

    step_2_strengths_a: str = Field(
        description="Stärken von Verlauf A"
    )

    step_3_strengths_b: str = Field(
        description="Stärken von Verlauf B"
    )

    step_4_weaknesses_a: str = Field(
        description="Schwächen von Verlauf A"
    )

    step_5_weaknesses_b: str = Field(
        description="Schwächen von Verlauf B"
    )

    step_6_comparison: str = Field(
        description="Direkter Vergleich der wichtigsten Unterschiede"
    )


class JudgeEvaluationResult(BaseModel):
    """Vollständiges Evaluationsergebnis"""

    chain_of_thought: ChainOfThought = Field(
        description="Schrittweises Reasoning VOR der Entscheidung"
    )

    criteria_scores: EvaluationCriteria = Field(
        description="Detaillierte Bewertung nach Kriterien"
    )

    winner: Literal["A", "B", "TIE"] = Field(
        description="Welcher Verlauf ist insgesamt besser? "
                    "A, B, oder TIE bei Gleichstand"
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Konfidenz der Entscheidung (0.0 = unsicher, 1.0 = sehr sicher)"
    )

    final_justification: str = Field(
        description="Abschließende Begründung für die Gesamtentscheidung"
    )
```

#### 2.2 LLM judge service

```python
# app/services/judge_service.py

import instructor
from openai import OpenAI
from app.llm.judge_schema import JudgeEvaluationResult
from app.llm.litellm_client import get_litellm_client
import json

class JudgeService:
    """Service für LLM Evaluator Evaluationen"""

    SYSTEM_PROMPT = """Du bist ein Experte für die Bewertung von Beratungsgesprächen
im Kontext psychologischer Online-Beratung.

Deine Aufgabe ist es, zwei E-Mail-Verläufe zwischen Beratenden und Ratsuchenden
zu vergleichen und zu bewerten, welcher Verlauf qualitativ besser ist.

WICHTIG:
1. Führe ZUERST dein Chain-of-Thought Reasoning durch
2. Bewerte DANN jedes Kriterium einzeln für beide Verläufe
3. Triff ZULETZT deine Gesamtentscheidung

Bewertungskriterien (jeweils 1-5 Skala):
- Berater-Kohärenz: Logik und Zusammenhang der Berater-Antworten
- Klienten-Kohärenz: Realismus des Klientenverhaltens
- Beratungsqualität: Therapeutische Qualität insgesamt
- Empathie: Einfühlungsvermögen des Beraters
- Authentizität: Natürlichkeit des Gesprächs
- Lösungsorientierung: Konkrete Hilfestellungen

Ignoriere die Position der Verläufe (ob A oder B zuerst kommt) -
bewerte rein nach Inhalt und Qualität."""

    def __init__(self, api_key: str, model: str = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"):
        self.client = instructor.from_openai(
            OpenAI(
                base_url="https://kiz1.in.ohmportal.de/llmproxy/v1",
                api_key=api_key
            ),
            mode=instructor.Mode.JSON
        )
        self.model = model

    def format_thread_for_prompt(self, thread_messages: list) -> str:
        """Formatiert einen E-Mail-Verlauf für den Prompt"""
        formatted = []
        for msg in thread_messages:
            role = "BERATER" if msg.get('is_counsellor') else "RATSUCHENDE"
            formatted.append(f"[{role}]: {msg.get('content', '')}")
        return "\n\n".join(formatted)

    async def evaluate_pair(
        self,
        thread_a_messages: list,
        thread_b_messages: list,
        pillar_a: int,
        pillar_b: int,
        stream_callback=None
    ) -> JudgeEvaluationResult:
        """
        Führt paarweisen Vergleich durch.

        Args:
            thread_a_messages: Nachrichten von Verlauf A
            thread_b_messages: Nachrichten von Verlauf B
            pillar_a: Säulennummer von A
            pillar_b: Säulennummer von B
            stream_callback: Optional callback für Streaming-Updates

        Returns:
            JudgeEvaluationResult mit strukturierter Bewertung
        """

        prompt = f"""Vergleiche die folgenden zwei E-Mail-Beratungsverläufe:

=== VERLAUF A (Säule {pillar_a}) ===
{self.format_thread_for_prompt(thread_a_messages)}

=== VERLAUF B (Säule {pillar_b}) ===
{self.format_thread_for_prompt(thread_b_messages)}

Führe eine detaillierte Bewertung durch und bestimme, welcher Verlauf besser ist."""

        # Mit Streaming
        if stream_callback:
            result = await self._evaluate_with_streaming(prompt, stream_callback)
        else:
            result = self.client.chat.completions.create(
                model=self.model,
                response_model=JudgeEvaluationResult,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Niedrig für Konsistenz
                max_tokens=4000
            )

        return result

    async def evaluate_with_position_swap(
        self,
        thread_a_messages: list,
        thread_b_messages: list,
        pillar_a: int,
        pillar_b: int
    ) -> tuple[JudgeEvaluationResult, JudgeEvaluationResult, str]:
        """
        Führt Evaluation mit Position-Swap durch um Bias zu eliminieren.

        Returns:
            (result_ab, result_ba, final_winner)
        """
        # Erste Evaluation: A | B
        result_ab = await self.evaluate_pair(
            thread_a_messages, thread_b_messages,
            pillar_a, pillar_b
        )

        # Zweite Evaluation: B | A (getauscht)
        result_ba = await self.evaluate_pair(
            thread_b_messages, thread_a_messages,
            pillar_b, pillar_a
        )

        # Ergebnis konsolidieren
        # Wenn result_ba "A" sagt, meint es eigentlich B (wegen Swap)
        winner_ab = result_ab.winner
        winner_ba_adjusted = {
            "A": "B",
            "B": "A",
            "TIE": "TIE"
        }.get(result_ba.winner, "TIE")

        # Finales Ergebnis
        if winner_ab == winner_ba_adjusted:
            final_winner = winner_ab
        else:
            # Widerspruch → TIE
            final_winner = "TIE"

        return result_ab, result_ba, final_winner
```

#### 2.3 Test criteria phase 2
- [ ] Pydantic schema validates correctly
- [ ] LiteLLM connection works
- [ ] JSON output is parsed correctly
- [ ] Position swap yields consistent results
- [ ] Streaming callback receives data

---

### Phase 3: API endpoints & queue (week 3-4)

#### 3.1 Judge API routes (current structure)

The implementation is modular (instead of a monolithic `judge_routes.py`) and is registered via `routes/judge/__init__.py` as `/api/judge`.

**Modules (excerpt):**
- `session_routes.py` (CRUD, estimate, comparison modes)
- `session_control_routes.py` (start/pause/resume/delete)
- `comparison_routes.py` (current, queue, comparisons, worker streams)
- `statistics_routes.py` + `statistics_*` (results & analytics)
- `pillar_routes.py` (pillars + assignment)
- `kia_sync_routes.py` (GitLab sync)
- `export_routes.py` (CSV/JSON)

All endpoints are protected via `@authentik_required` and use `@require_permission('feature:comparison:*')`.

```python
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from routes.judge.session_routes import session_bp

@session_bp.route('/sessions', methods=['GET'])
@authentik_required
@require_permission('feature:comparison:view')
def list_sessions():
    ...
```

**Important endpoints (excerpt):**
- `GET /api/judge/comparison-modes`
- `POST /api/judge/estimate`
- `GET/POST /api/judge/sessions`
- `POST /api/judge/sessions/<id>/start|pause|resume`
- `GET /api/judge/sessions/<id>/current|queue|comparisons`
- `GET /api/judge/sessions/<id>/results|verbosity-analysis|thread-performance|position-swap-analysis`
- `GET /api/judge/sessions/<id>/export/csv|export/json`
- `GET /api/judge/pillars` (+ `/pillars/<n>/threads`, `/pillars/<n>/assign`)
- `GET/POST /api/judge/kia/...`

#### 3.2 Socket.IO events for live updates

```python
# app/socketio_handlers/events_judge.py (excerpt)

@socketio.on('judge:join_session')
def handle_join_session(data):
    ...

@socketio.on('judge:leave_session')
def handle_leave_session(data):
    ...

@socketio.on('judge:join_overview')
def handle_join_overview():
    ...

@socketio.on('judge:get_status')
def handle_get_status(data):
    ...
```

**Server -> client (examples):**
- `judge:comparison_start`
- `judge:llm_stream`
- `judge:comparison_complete`
- `judge:progress`
- `judge:session_complete`
- `judge:status`

#### 3.3 Test criteria phase 3
- [ ] All API endpoints reachable with correct permissions
- [ ] Session lifecycle works (create -> configure -> start -> pause)
- [ ] Socket.IO rooms are managed correctly
- [ ] Live broadcasts reach connected clients

---

### Phase 4: Background worker & queue (week 4-5)

#### 4.1 Judge worker

Processing currently runs via a **worker pool** (`app/workers/judge_worker_pool.py`)
with optional parallel workers. The pool is started from the session control routes
(`trigger_judge_worker_pool`) and sends live events (`judge:*`) for progress,
streaming, and completion.

**Relevant files:**
- `app/workers/judge_worker_pool.py` (current, multi-worker)
- `app/workers/judge_worker.py` (legacy single-worker)
- `app/routes/judge/session_control_routes.py`
- `app/routes/judge/session_health_routes.py`

**Pseudocode (simplified):**
```
pool.start(session_id, worker_count)
while pending comparisons:
  worker.claim_next()
  worker.evaluate()
  emit judge:comparison_start / judge:llm_stream / judge:progress
emit judge:session_complete
```

#### 4.2 Test criteria phase 4
- [ ] Worker starts in the background
- [ ] Queue is processed sequentially
- [ ] Pause/resume works
- [ ] Statistics are aggregated correctly
- [ ] Socket.IO broadcasts during processing

---

### Phase 5: Frontend - configuration & upload (week 5-6)

#### 5.1 JudgeConfig.vue

```vue
<!-- llars-frontend/src/components/Judge/JudgeConfig.vue -->
<template>
  <v-container>
    <v-card>
      <v-card-title>
        <v-icon left>mdi-scale-balance</v-icon>
        LLM Evaluator Konfiguration
      </v-card-title>

      <v-card-text>
        <!-- Session Name -->
        <v-text-field
          v-model="sessionName"
          label="Session Name"
          outlined
        />

        <!-- Säulen-Auswahl -->
        <v-card outlined class="mb-4">
          <v-card-subtitle>KIA-Säulen auswählen</v-card-subtitle>
          <v-card-text>
            <v-chip-group
              v-model="selectedPillars"
              multiple
              column
            >
              <v-chip
                v-for="pillar in pillars"
                :key="pillar.number"
                :value="pillar.number"
                filter
                outlined
              >
                <v-avatar left :color="pillar.color">
                  {{ pillar.number }}
                </v-avatar>
                {{ pillar.name }}
                <v-chip small class="ml-2">
                  {{ pillar.threadCount }} Verläufe
                </v-chip>
              </v-chip>
            </v-chip-group>
          </v-card-text>
        </v-card>

        <!-- Vergleichs-Modus -->
        <v-radio-group v-model="comparisonMode" label="Vergleichs-Modus">
          <v-radio
            label="Pillar Sample (schneller Überblick)"
            value="pillar_sample"
          />
          <v-radio
            label="Round Robin (alle Threads Säule A vs. Säule B)"
            value="round_robin"
          />
          <v-radio
            label="Free For All (alle Threads gegeneinander)"
            value="free_for_all"
          />
        </v-radio-group>

        <!-- Samples pro Säule -->
        <v-slider
          v-model="samplesPerPillar"
          label="Verläufe pro Säule"
          :min="1"
          :max="50"
          thumb-label
        />

        <!-- Position Swap -->
        <v-switch
          v-model="positionSwap"
          label="Position-Swap aktivieren (eliminiert Bias)"
          hint="Jeder Vergleich wird zweimal mit getauschten Positionen durchgeführt"
          persistent-hint
        />

        <!-- Zusammenfassung -->
        <v-alert type="info" outlined class="mt-4">
          <strong>Zusammenfassung:</strong>
          <ul>
            <li>{{ selectedPillars.length }} Säulen ausgewählt</li>
            <li>{{ estimatedComparisons }} geschätzte Vergleiche</li>
            <li>{{ positionSwap ? 'Mit' : 'Ohne' }} Position-Swap</li>
          </ul>
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          color="primary"
          :disabled="!isValid"
          @click="createSession"
        >
          <v-icon left>mdi-play</v-icon>
          Session erstellen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// Daten
const sessionName = ref('Neue Evaluation ' + new Date().toLocaleDateString('de-DE'))
const selectedPillars = ref([1, 3])
const comparisonMode = ref('pillar_sample')
const samplesPerPillar = ref(10)
const maxThreadsPerPillar = ref(null)
const positionSwap = ref(true)
const repetitionsPerPair = ref(1)
const workerCount = ref(1)
const estimate = ref(null)

const pillars = ref([
  { number: 1, name: 'Rollenspiele', threadCount: 50, color: 'red' },
  { number: 2, name: 'Feature aus Säule 1', threadCount: 50, color: 'orange' },
  { number: 3, name: 'Anonymisierte Daten', threadCount: 83, color: 'green' },
  { number: 4, name: 'Synthetisch generiert', threadCount: 100, color: 'blue' },
  { number: 5, name: 'Live-Testungen', threadCount: 36, color: 'purple' }
])

// Computed
const estimatedComparisons = computed(() => estimate.value?.total_comparisons || 0)

const isValid = computed(() => {
  return selectedPillars.value.length >= 2 && sessionName.value.length > 0
})

// Methods
async function fetchEstimate() {
  if (selectedPillars.value.length < 2) return
  const payload = {
    pillar_ids: selectedPillars.value,
    comparison_mode: comparisonMode.value,
    samples_per_pillar: samplesPerPillar.value,
    position_swap: positionSwap.value
  }
  if (maxThreadsPerPillar.value) {
    payload.max_threads_per_pillar = maxThreadsPerPillar.value
  }
  const response = await axios.post('/api/judge/estimate', payload)
  estimate.value = response.data
}

async function createSession() {
  try {
    const payload = {
      session_name: sessionName.value,
      pillar_ids: selectedPillars.value,
      comparison_mode: comparisonMode.value,
      samples_per_pillar: samplesPerPillar.value,
      position_swap: positionSwap.value,
      repetitions_per_pair: repetitionsPerPair.value,
      worker_count: workerCount.value
    }
    if (maxThreadsPerPillar.value) {
      payload.max_threads_per_pillar = maxThreadsPerPillar.value
    }

    // Session erstellen
    const createRes = await axios.post('/api/judge/sessions', payload)
    const sessionId = createRes.data.session_id || createRes.data.id

    // Starten
    await axios.post(`/api/judge/sessions/${sessionId}/start`)

    // Zur Session navigieren
    router.push(`/judge/session/${sessionId}`)

  } catch (error) {
    console.error('Session creation failed:', error)
  }
}
</script>
```

#### 5.2 Test criteria phase 5
- [ ] Pillars load correctly
- [ ] Comparison estimation matches
- [ ] Session created and configured
- [ ] Navigation to session works

---

### Phase 6: Frontend - live evaluation view (week 6-7)

#### 6.1 LiveEvaluation.vue

```vue
<!-- llars-frontend/src/components/Judge/LiveEvaluation.vue -->
<template>
  <v-container fluid>
    <!-- Header mit Session-Info -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon left :color="statusColor">{{ statusIcon }}</v-icon>
            {{ session?.name }}
            <v-spacer />
            <v-chip :color="statusColor" small>
              {{ session?.status }}
            </v-chip>
          </v-card-title>

          <!-- Progress -->
          <v-card-text>
            <v-progress-linear
              :value="progress"
              height="25"
              :color="statusColor"
            >
              <template v-slot:default>
                {{ session?.completed_comparisons }} / {{ session?.total_comparisons }}
                ({{ progress.toFixed(1) }}%)
              </template>
            </v-progress-linear>

            <!-- Controls -->
            <v-btn-toggle class="mt-4">
              <v-btn
                v-if="session?.status !== 'running'"
                color="success"
                @click="startSession"
              >
                <v-icon>mdi-play</v-icon>
                Start
              </v-btn>
              <v-btn
                v-if="session?.status === 'running'"
                color="warning"
                @click="pauseSession"
              >
                <v-icon>mdi-pause</v-icon>
                Pause
              </v-btn>
            </v-btn-toggle>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Hauptbereich: Vergleich + JSON Preview -->
    <v-row class="mt-4">
      <!-- Linke Seite: Verlauf A -->
      <v-col cols="5">
        <v-card :outlined="currentWinner === 'A'" :color="currentWinner === 'A' ? 'success lighten-5' : ''">
          <v-card-title>
            <v-chip :color="getPillarColor(currentComparison?.pillar_a)">
              Säule {{ currentComparison?.pillar_a }}
            </v-chip>
            Verlauf A
            <v-icon v-if="currentWinner === 'A'" color="success" right>
              mdi-trophy
            </v-icon>
          </v-card-title>
          <v-card-text class="thread-preview">
            <div
              v-for="(msg, idx) in currentComparison?.thread_a?.messages"
              :key="idx"
              :class="['message', msg.is_counsellor ? 'counsellor' : 'client']"
            >
              <v-chip x-small :color="msg.is_counsellor ? 'blue' : 'green'" class="mb-1">
                {{ msg.is_counsellor ? 'Berater' : 'Ratsuchende' }}
              </v-chip>
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Mitte: LLM Output / JSON Preview -->
      <v-col cols="2">
        <v-card height="100%">
          <v-card-title class="text-center">
            <v-icon>mdi-robot</v-icon>
            LLM Judge
          </v-card-title>
          <v-card-text>
            <!-- Streaming Indicator -->
            <v-progress-circular
              v-if="isStreaming"
              indeterminate
              color="primary"
              class="mb-4"
            />

            <!-- Winner Anzeige -->
            <div v-if="currentResult" class="text-center">
              <v-chip
                x-large
                :color="getWinnerColor(currentResult.winner)"
              >
                {{ currentResult.winner === 'TIE' ? 'Unentschieden' : `Gewinner: ${currentResult.winner}` }}
              </v-chip>
              <div class="mt-2">
                Konfidenz: {{ (currentResult.confidence * 100).toFixed(0) }}%
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Rechte Seite: Verlauf B -->
      <v-col cols="5">
        <v-card :outlined="currentWinner === 'B'" :color="currentWinner === 'B' ? 'success lighten-5' : ''">
          <v-card-title>
            <v-chip :color="getPillarColor(currentComparison?.pillar_b)">
              Säule {{ currentComparison?.pillar_b }}
            </v-chip>
            Verlauf B
            <v-icon v-if="currentWinner === 'B'" color="success" right>
              mdi-trophy
            </v-icon>
          </v-card-title>
          <v-card-text class="thread-preview">
            <div
              v-for="(msg, idx) in currentComparison?.thread_b?.messages"
              :key="idx"
              :class="['message', msg.is_counsellor ? 'counsellor' : 'client']"
            >
              <v-chip x-small :color="msg.is_counsellor ? 'blue' : 'green'" class="mb-1">
                {{ msg.is_counsellor ? 'Berater' : 'Ratsuchende' }}
              </v-chip>
              <div class="message-content">{{ msg.content }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- JSON Preview (expandierbar) -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-header>
              <v-icon left>mdi-code-json</v-icon>
              LLM Response (JSON)
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <pre class="json-preview">{{ streamingJson }}</pre>
            </v-expansion-panel-content>
          </v-expansion-panel>

          <v-expansion-panel>
            <v-expansion-panel-header>
              <v-icon left>mdi-brain</v-icon>
              Chain-of-Thought Reasoning
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-stepper v-if="currentResult?.chain_of_thought" vertical>
                <v-stepper-step step="1" complete>
                  Übersicht
                  <small>{{ currentResult.chain_of_thought.step_1_overview }}</small>
                </v-stepper-step>
                <v-stepper-step step="2" complete>
                  Stärken A
                  <small>{{ currentResult.chain_of_thought.step_2_strengths_a }}</small>
                </v-stepper-step>
                <!-- ... weitere Steps -->
              </v-stepper>
            </v-expansion-panel-content>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>

    <!-- Historie der abgeschlossenen Vergleiche -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon left>mdi-history</v-icon>
            Abgeschlossene Vergleiche
          </v-card-title>
          <v-data-table
            :headers="historyHeaders"
            :items="completedComparisons"
            :items-per-page="10"
            @click:row="showComparisonDetail"
          >
            <template v-slot:item.winner="{ item }">
              <v-chip :color="getWinnerColor(item.winner)" small>
                {{ item.winner }}
              </v-chip>
            </template>
            <template v-slot:item.pillars="{ item }">
              <v-chip :color="getPillarColor(item.pillar_a)" x-small>
                {{ item.pillar_a }}
              </v-chip>
              vs
              <v-chip :color="getPillarColor(item.pillar_b)" x-small>
                {{ item.pillar_b }}
              </v-chip>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { io } from 'socket.io-client'
import axios from 'axios'

const route = useRoute()
const sessionId = route.params.id

// State
const session = ref(null)
const currentComparison = ref(null)
const currentResult = ref(null)
const streamingJson = ref('')
const isStreaming = ref(false)
const completedComparisons = ref([])
const socket = ref(null)

// Computed
const progress = computed(() => {
  if (!session.value) return 0
  return (session.value.completed_comparisons / session.value.total_comparisons) * 100
})

const currentWinner = computed(() => currentResult.value?.winner)

const statusColor = computed(() => {
  const colors = {
    'created': 'grey',
    'queued': 'blue',
    'running': 'green',
    'paused': 'orange',
    'completed': 'success',
    'failed': 'red'
  }
  return colors[session.value?.status] || 'grey'
})

// Socket.IO Setup
onMounted(async () => {
  // Session laden
  await loadSession()
  await loadCompletedComparisons()

	  // Socket verbinden
	  socket.value = io('/judge', {
	    auth: { token: sessionStorage.getItem('auth_token') }
	  })

  socket.value.emit('judge:join_session', { session_id: sessionId })

  // Event Listeners
  socket.value.on('judge:comparison_start', (data) => {
    currentComparison.value = data
    currentResult.value = null
    streamingJson.value = ''
    isStreaming.value = true
  })

  socket.value.on('judge:llm_stream', (data) => {
    streamingJson.value += data.chunk
  })

  socket.value.on('judge:comparison_complete', (data) => {
    currentResult.value = data.evaluation
    isStreaming.value = false
    completedComparisons.value.unshift(data)
  })

  socket.value.on('judge:progress', (data) => {
    session.value.completed_comparisons = data.completed
  })
})

onUnmounted(() => {
  if (socket.value) {
    socket.value.emit('judge:leave_session', { session_id: sessionId })
    socket.value.disconnect()
  }
})

// Methods
async function loadSession() {
  const res = await axios.get(`/api/judge/sessions/${sessionId}`)
  session.value = res.data
}

async function loadCompletedComparisons() {
  const res = await axios.get(`/api/judge/sessions/${sessionId}/results`)
  completedComparisons.value = res.data
}

async function startSession() {
  await axios.post(`/api/judge/sessions/${sessionId}/start`)
  session.value.status = 'running'
}

async function pauseSession() {
  await axios.post(`/api/judge/sessions/${sessionId}/pause`)
  session.value.status = 'paused'
}

function getPillarColor(pillar) {
  const colors = {
    1: 'red',
    2: 'orange',
    3: 'green',
    4: 'blue',
    5: 'purple'
  }
  return colors[pillar] || 'grey'
}

function getWinnerColor(winner) {
  if (winner === 'TIE') return 'grey'
  return 'success'
}
</script>

<style scoped>
.thread-preview {
  max-height: 400px;
  overflow-y: auto;
}

.message {
  padding: 8px;
  margin-bottom: 8px;
  border-radius: 8px;
}

.message.counsellor {
  background-color: rgba(33, 150, 243, 0.1);
  margin-left: 20px;
}

.message.client {
  background-color: rgba(76, 175, 80, 0.1);
  margin-right: 20px;
}

.json-preview {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
</style>
```

#### 6.2 Test criteria phase 6
- [ ] Live view shows current comparisons
- [ ] Streaming JSON is displayed correctly
- [ ] Winner highlight works
- [ ] History updates
- [ ] Socket reconnect on connection loss

---

### Phase 7: Evaluation dashboard (week 7-8)

#### 7.1 JudgeResultsDashboard.vue

```vue
<!-- llars-frontend/src/components/Judge/JudgeResultsDashboard.vue -->
<template>
  <v-container fluid>
    <v-row>
      <!-- Säulen-Matrix -->
      <v-col cols="8">
        <v-card>
          <v-card-title>
            <v-icon left>mdi-table</v-icon>
            Säulen-Vergleichsmatrix
          </v-card-title>
          <v-card-text>
            <table class="matrix-table">
              <thead>
                <tr>
                  <th></th>
                  <th v-for="p in pillars" :key="p">
                    <v-chip :color="getPillarColor(p)" small>
                      Säule {{ p }}
                    </v-chip>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pa in pillars" :key="pa">
                  <td>
                    <v-chip :color="getPillarColor(pa)" small>
                      Säule {{ pa }}
                    </v-chip>
                  </td>
                  <td
                    v-for="pb in pillars"
                    :key="pb"
                    :class="getCellClass(pa, pb)"
                    @click="showDetail(pa, pb)"
                  >
                    <template v-if="pa !== pb">
                      <div class="cell-content">
                        <strong>{{ getWinRate(pa, pb) }}%</strong>
                        <small>{{ getMatchCount(pa, pb) }} Matches</small>
                      </div>
                    </template>
                    <template v-else>
                      <span class="diagonal">-</span>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="legend mt-4">
              <v-chip color="success" small>Gewinner (>60%)</v-chip>
              <v-chip color="warning" small>Ausgeglichen (40-60%)</v-chip>
              <v-chip color="error" small>Verlierer (<40%)</v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Gesamtstatistiken -->
      <v-col cols="4">
        <v-card>
          <v-card-title>
            <v-icon left>mdi-chart-bar</v-icon>
            Gesamtübersicht
          </v-card-title>
          <v-card-text>
            <!-- Säulen-Ranking -->
            <v-list>
              <v-subheader>Säulen-Ranking (nach Gesamtsiegen)</v-subheader>
              <v-list-item
                v-for="(pillar, idx) in pillarRanking"
                :key="pillar.number"
              >
                <v-list-item-avatar>
                  <v-chip :color="idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? '#cd7f32' : 'grey'">
                    {{ idx + 1 }}
                  </v-chip>
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title>
                    Säule {{ pillar.number }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ pillar.wins }} Siege / {{ pillar.losses }} Niederlagen
                  </v-list-item-subtitle>
                </v-list-item-content>
                <v-list-item-action>
                  <v-progress-circular
                    :value="pillar.winRate"
                    :color="pillar.winRate > 50 ? 'success' : 'error'"
                  >
                    {{ pillar.winRate }}%
                  </v-progress-circular>
                </v-list-item-action>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Metriken-Durchschnitte -->
        <v-card class="mt-4">
          <v-card-title>
            <v-icon left>mdi-chart-line</v-icon>
            Durchschnittliche Metriken
          </v-card-title>
          <v-card-text>
            <v-simple-table>
              <thead>
                <tr>
                  <th>Säule</th>
                  <th>Kohärenz</th>
                  <th>Qualität</th>
                  <th>Empathie</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pillar in pillars" :key="pillar">
                  <td>
                    <v-chip :color="getPillarColor(pillar)" x-small>
                      {{ pillar }}
                    </v-chip>
                  </td>
                  <td>{{ getAvgMetric(pillar, 'coherence').toFixed(2) }}</td>
                  <td>{{ getAvgMetric(pillar, 'quality').toFixed(2) }}</td>
                  <td>{{ getAvgMetric(pillar, 'empathy').toFixed(2) }}</td>
                </tr>
              </tbody>
            </v-simple-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Detail-Charts -->
    <v-row class="mt-4">
      <v-col cols="6">
        <v-card>
          <v-card-title>Siege pro Säule</v-card-title>
          <v-card-text>
            <canvas ref="winsChart"></canvas>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6">
        <v-card>
          <v-card-title>Konfidenz-Verteilung</v-card-title>
          <v-card-text>
            <canvas ref="confidenceChart"></canvas>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Export -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-actions>
            <v-btn color="primary" @click="exportCSV">
              <v-icon left>mdi-download</v-icon>
              Export als CSV
            </v-btn>
            <v-btn color="secondary" @click="exportJSON">
              <v-icon left>mdi-code-json</v-icon>
              Export als JSON
            </v-btn>
            <v-btn color="info" @click="exportPDF">
              <v-icon left>mdi-file-pdf-box</v-icon>
              Report als PDF
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
// ... Implementation mit Chart.js für Visualisierungen
</script>

<style scoped>
.matrix-table {
  width: 100%;
  border-collapse: collapse;
}

.matrix-table th,
.matrix-table td {
  padding: 12px;
  text-align: center;
  border: 1px solid #e0e0e0;
}

.matrix-table td.winner {
  background-color: rgba(76, 175, 80, 0.2);
}

.matrix-table td.loser {
  background-color: rgba(244, 67, 54, 0.2);
}

.matrix-table td.neutral {
  background-color: rgba(255, 193, 7, 0.2);
}

.diagonal {
  color: #9e9e9e;
}

.cell-content {
  display: flex;
  flex-direction: column;
}
</style>
```

#### 7.2 Test criteria phase 7
- [ ] Matrix shows correct win rates
- [ ] Ranking is sorted
- [ ] Charts render correctly
- [ ] Export works (CSV, JSON, PDF)

---

### Phase 8: Data upload & pillar management (week 8-9)

#### 8.1 PillarUpload.vue

```vue
<!-- llars-frontend/src/components/Judge/PillarUpload.vue -->
<template>
  <v-container>
    <v-card>
      <v-card-title>
        <v-icon left>mdi-upload</v-icon>
        Säulen-Daten hochladen
      </v-card-title>

      <v-card-text>
        <v-stepper v-model="step">
          <v-stepper-header>
            <v-stepper-step step="1">Säule auswählen</v-stepper-step>
            <v-divider />
            <v-stepper-step step="2">Datei hochladen</v-stepper-step>
            <v-divider />
            <v-stepper-step step="3">Validierung</v-stepper-step>
            <v-divider />
            <v-stepper-step step="4">Import</v-stepper-step>
          </v-stepper-header>

          <v-stepper-content step="1">
            <v-select
              v-model="selectedPillar"
              :items="pillars"
              item-text="name"
              item-value="number"
              label="Säule auswählen"
              outlined
            />
            <v-btn color="primary" @click="step = 2">
              Weiter
            </v-btn>
          </v-stepper-content>

          <v-stepper-content step="2">
            <v-file-input
              v-model="uploadFile"
              label="JSON/CSV Datei"
              accept=".json,.csv"
              show-size
              outlined
            />
            <v-alert type="info" outlined>
              <strong>Erwartetes Format:</strong>
              <pre>{{ expectedFormat }}</pre>
            </v-alert>
            <v-btn color="primary" @click="validateFile">
              Validieren
            </v-btn>
          </v-stepper-content>

          <v-stepper-content step="3">
            <v-alert :type="validationResult.valid ? 'success' : 'error'">
              {{ validationResult.message }}
            </v-alert>
            <v-simple-table v-if="validationResult.preview">
              <thead>
                <tr>
                  <th>Thread</th>
                  <th>Nachrichten</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="thread in validationResult.preview" :key="thread.id">
                  <td>{{ thread.subject }}</td>
                  <td>{{ thread.messageCount }}</td>
                  <td>
                    <v-icon :color="thread.valid ? 'success' : 'error'">
                      {{ thread.valid ? 'mdi-check' : 'mdi-alert' }}
                    </v-icon>
                  </td>
                </tr>
              </tbody>
            </v-simple-table>
            <v-btn
              color="primary"
              :disabled="!validationResult.valid"
              @click="importData"
            >
              Importieren
            </v-btn>
          </v-stepper-content>

          <v-stepper-content step="4">
            <v-progress-linear
              v-if="importing"
              indeterminate
              color="primary"
            />
            <v-alert v-else type="success">
              {{ importResult.imported }} Threads erfolgreich importiert!
            </v-alert>
          </v-stepper-content>
        </v-stepper>
      </v-card-text>
    </v-card>
  </v-container>
</template>
```

#### 8.2 Test criteria phase 8
- [ ] File upload works
- [ ] Validation detects faulty data
- [ ] Import creates correct database entries
- [ ] Pillar assignment is correct

---

## 5. Pydantic schema design (summary)

```python
# Vollständiges Schema

from pydantic import BaseModel, Field
from typing import Literal

class MetricScore(BaseModel):
    score_a: float = Field(ge=1.0, le=5.0)
    score_b: float = Field(ge=1.0, le=5.0)
    reasoning: str

class EvaluationCriteria(BaseModel):
    counsellor_coherence: MetricScore
    client_coherence: MetricScore
    quality: MetricScore
    empathy: MetricScore
    authenticity: MetricScore
    solution_orientation: MetricScore

class ChainOfThought(BaseModel):
    step_1_overview: str
    step_2_strengths_a: str
    step_3_strengths_b: str
    step_4_weaknesses_a: str
    step_5_weaknesses_b: str
    step_6_comparison: str

class JudgeEvaluationResult(BaseModel):
    chain_of_thought: ChainOfThought
    criteria_scores: EvaluationCriteria
    winner: Literal["A", "B", "TIE"]
    confidence: float = Field(ge=0.0, le=1.0)
    final_justification: str
```

---

## 6. UI/UX concept

### 6.1 Navigation

```
/judge
├── /config          → JudgeConfig.vue (Session erstellen)
├── /sessions        → SessionList.vue (Übersicht)
├── /session/:id     → LiveEvaluation.vue (Live-View)
├── /session/:id/results → JudgeResultsDashboard.vue
├── /upload          → PillarUpload.vue (Daten hochladen)
└── /pillar/:id      → PillarDetail.vue (Säulen-Details)
```

### 6.2 Live view layout

```
┌─────────────────────────────────────────────────────────────────┐
│ [Progress Bar] 45/100 (45%)                      [Start][Pause] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │   VERLAUF A  │   │  LLM JUDGE   │   │   VERLAUF B  │        │
│  │   Säule 1    │   │   [Robot]    │   │   Säule 3    │        │
│  │              │   │              │   │              │        │
│  │  [Messages]  │   │  Winner: A   │   │  [Messages]  │        │
│  │              │   │  Conf: 85%   │   │              │        │
│  │              │   │              │   │              │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [JSON Preview Expandable]                                       │
│ [Chain-of-Thought Stepper Expandable]                          │
├─────────────────────────────────────────────────────────────────┤
│ [Historie Table] - Klickbar für Details                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Session management

### 7.1 Session lifecycle

```
                    ┌─────────┐
                    │ CREATED │
                    └────┬────┘
                         │ configure()
                         ▼
                    ┌─────────┐
            ┌───────│ QUEUED  │───────┐
            │       └────┬────┘       │
            │            │ start()    │
            │            ▼            │
            │       ┌─────────┐       │
            │   ┌───│ RUNNING │───┐   │
            │   │   └────┬────┘   │   │
            │   │        │        │   │
   pause()  │   │        │        │   │ error
            │   │        ▼        │   │
            │   │   ┌─────────┐   │   │
            │   └──▶│ PAUSED  │◀──┘   │
            │       └────┬────┘       │
            │            │ resume()   │
            │            │            │
            ▼            ▼            ▼
       ┌─────────┐  ┌──────────┐  ┌────────┐
       │ PAUSED  │  │COMPLETED │  │ FAILED │
       └─────────┘  └──────────┘  └────────┘
```

### 7.2 Persistent sessions

- Sessions run in the backend **independent of the browser**
- User can close the browser and reconnect later
- Socket.IO room join enables live view
- Multiple users can observe the same session (with permission)

---

## 8. Queue system

### 8.1 Queue architecture

```python
# Queue-Generierung
def generate_comparisons(session_id, pillars, mode, samples, position_swap):
    """
    Generiert Queue von Vergleichen.

    Beispiel für pillars=[1,3,5], samples=5, position_swap=True:

    Paare: 1v3, 1v5, 3v5 = 3 Paare
    Pro Paar: 5 Samples = 15 Vergleiche
    Mit Swap: 30 Vergleiche total

    Queue:
    [1v3_sample1_pos1, 1v3_sample1_pos2,
     1v3_sample2_pos1, 1v3_sample2_pos2, ...]
    """
    comparisons = []
    queue_pos = 0

    # Alle Paare generieren
    for i, pa in enumerate(pillars):
        for pb in pillars[i+1:]:
            # Threads für beide Säulen holen
            threads_a = get_pillar_threads(pa, limit=samples)
            threads_b = get_pillar_threads(pb, limit=samples)

            # Paare bilden
            for ta, tb in zip(threads_a, threads_b):
                # Position 1: A | B
                comparisons.append(JudgeComparison(
                    session_id=session_id,
                    thread_a_id=ta.id,
                    thread_b_id=tb.id,
                    pillar_a=pa,
                    pillar_b=pb,
                    position_order=1,
                    queue_position=queue_pos
                ))
                queue_pos += 1

                # Position 2: B | A (Swap)
                if position_swap:
                    comparisons.append(JudgeComparison(
                        session_id=session_id,
                        thread_a_id=tb.id,
                        thread_b_id=ta.id,
                        pillar_a=pb,
                        pillar_b=pa,
                        position_order=2,
                        queue_position=queue_pos
                    ))
                    queue_pos += 1

    db.session.add_all(comparisons)
    db.session.commit()
    return comparisons
```

### 8.2 Worker scaling

Currently: **single worker per session**

Future options:
- Redis queue for multi-worker
- Celery for distributed processing
- Rate limiting for API requests

---

## 9. Evaluation dashboard

### 9.1 Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Win rate** | Win rate of a pillar | wins / (wins + losses + ties) |
| **Elo rating** | Relative ranking | Elo algorithm |
| **Avg confidence** | Average LLM confidence | mean(confidence) |
| **Position bias** | Share of flips on swap | flips / total_swaps |
| **Metric scores** | Average per criterion | mean(criterion_score) |

### 9.2 Visualizations

1. **Pillar matrix**: heatmap of win rates
2. **Bar chart**: total wins per pillar
3. **Radar chart**: metric profile per pillar
4. **Sankey diagram**: comparison flow
5. **Confidence distribution**: histogram

---

## 10. Test plan by phase

### Phase 1 tests
```python
def test_pillar_thread_creation():
    """Teste Säulen-Thread Zuordnung"""
    thread = PillarThread(thread_id=1, pillar_number=1, pillar_name="Rollenspiele")
    assert thread.pillar_number == 1

def test_judge_session_lifecycle():
    """Teste Session-Status-Übergänge"""
    session = JudgeSession(user_id=1, name="Test")
    assert session.status == 'created'
```

### Phase 2 tests
```python
def test_pydantic_schema_validation():
    """Teste Schema-Validierung"""
    result = JudgeEvaluationResult(
        winner="A",
        confidence=0.85,
        # ...
    )
    assert result.winner in ["A", "B", "TIE"]

def test_litellm_connection():
    """Teste API-Verbindung"""
    service = JudgeService(api_key=os.getenv('LITELLM_API_KEY'))
    assert service.client is not None
```

### Phase 3 tests
```python
def test_api_permissions():
    """Teste Permission-Checks"""
    # Ohne Permission
    response = client.get('/api/judge/sessions')
    assert response.status_code == 403

    # Mit Permission
    response = client.get('/api/judge/sessions', headers=auth_headers)
    assert response.status_code == 200

def test_socketio_room_join():
    """Teste Socket-Room-Management"""
    socketio_client.emit('judge:join_session', {'session_id': 1})
    received = socketio_client.get_received()
    assert any(r['name'] == 'judge:joined' for r in received)
```

### Phase 4 tests
```python
def test_worker_queue_processing():
    """Teste Queue-Verarbeitung"""
    session = create_test_session()
    trigger_judge_worker(session.id)
    time.sleep(5)

    session.refresh()
    assert session.completed_comparisons > 0

def test_position_swap_consistency():
    """Teste Bias-Elimination"""
    # Führe beide Swap-Varianten durch
    result_ab, result_ba, final = service.evaluate_with_position_swap(...)

    # Bei konsistenter Bewertung sollte final nicht TIE sein
    # es sei denn beide Evaluationen waren TIE
```

### Phase 5-8 tests
```python
# Frontend-Tests mit Cypress/Playwright
def test_session_creation_ui():
    """E2E: Session erstellen"""
    page.goto('/judge/config')
    page.click('[data-testid="pillar-1"]')
    page.click('[data-testid="pillar-3"]')
    page.click('[data-testid="create-session"]')
    expect(page).to_have_url(re.compile(r'/judge/session/\d+'))

def test_live_updates():
    """E2E: Live-Updates empfangen"""
    page.goto('/judge/session/1')
    page.click('[data-testid="start-session"]')

    # Warte auf ersten Comparison
    expect(page.locator('[data-testid="current-comparison"]')).to_be_visible()
```

---

## Appendix: Sources

### Web research
- [Evidently AI - LLM-as-a-Judge Guide](https://www.evidentlyai.com/llm-guide/llm-as-a-judge)
- [Cameron Wolfe - Using LLMs for Evaluation](https://cameronrwolfe.substack.com/p/llm-as-a-judge)
- [Eugene Yan - LLM Evaluators](https://eugeneyan.com/writing/llm-evaluators/)
- [Instructor - Pairwise LLM Judge](https://python.useinstructor.com/blog/2024/10/17/building-a-pairwise-llm-judge-with-instructor-and-pydantic/)
- [arXiv - Position Bias in Pairwise Comparisons](https://arxiv.org/html/2406.07791v1)
- [CounselBench - Mental Health Evaluation](https://arxiv.org/html/2506.08584v1)
- [Confident AI - Chatbot Evaluation Metrics](https://www.confident-ai.com/blog/llm-chatbot-evaluation-explained-top-chatbot-evaluation-metrics-and-testing-techniques)

### LLARS codebase
- `app/db/tables.py` - existing table definitions
- `app/routes/LLMComparisonRoutes.py` - comparison infrastructure
- `app/single_message_evaluation.py` - single evaluator pattern
- `app/llm/litellm_client.py` - LiteLLM integration
- `llars-frontend/src/components/HistoryGenerator/` - rating UI patterns
