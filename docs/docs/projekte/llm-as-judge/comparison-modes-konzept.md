# LLM Evaluators: Erweiterte Vergleichs-Modi & Multi-Worker (Legacy)

!!! warning "Legacy-Konzept (Stand 2025)"
    Diese Erweiterungen beziehen sich auf die historische Judge-UI mit Sessions.
    In LLARS (Stand 2026-02-05) werden LLM-Evaluatoren primär als **Konfiguration im Scenario Manager** genutzt.
    Die Inhalte dienen als Hintergrund und Design-Historie.

**Version:** 1.0
**Datum:** 26. November 2025
**Status:** Legacy (historisch implementiert)

---

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Vergleichs-Modi](#vergleichs-modi)
3. [Multi-Worker Architektur](#multi-worker-architektur)
4. [ELO-Rating System](#elo-rating-system)
5. [UI-Konzept](#ui-konzept)
6. [Implementierungs-Phasen](#implementierungs-phasen)
7. [API-Referenz](#api-referenz)

---

## Übersicht

### Historischer Stand (2025)

Das LLM Evaluator System unterstützte mehrere Vergleichs-Modi (`pillar_sample`, `round_robin`, `free_for_all`)
inkl. optionalem Position-Swap. Die Verarbeitung lief über einen **JudgeWorkerPool** mit konfigurierbarer
Parallelisierung (`worker_count`).

### Aktueller Stand in LLARS

- LLM-Evaluation wird pro Szenario konfiguriert (Scenario Wizard).
- Auswahl von System- und eigenen Provider-Modellen.
- Optionaler Auto-Start nach Szenario-Erstellung.
- Live-Status und Ergebnisse im Scenario Manager (Evaluation/Results Tabs).

### Umgesetzte Erweiterungen

1. **Flexible Vergleichs-Modi**: Unterschiedliche Strategien für verschiedene Anwendungsfälle
2. **Multi-Worker Parallelisierung**: Mehrere Worker für schnellere Verarbeitung
3. **ELO-Rating**: Thread-Level Ranking für detaillierte Analyse
4. **Erweiterte Statistiken**: Konsistenz, Bias, Thread-Performance

---

## Vergleichs-Modi

### 1. Pillar Sample (Standard)

```
Modus: pillar_sample
```

**Beschreibung:**
- Säulen-Paare werden gebildet (z.B. Säule 1 vs Säule 3)
- Pro Paar werden N zufällige Threads ausgewählt und 1:1 verglichen
- Thread A₁ vs B₁, Thread A₂ vs B₂, etc.

**Formel:**
```
Vergleiche = Säulen-Paare × Samples × (2 wenn Position-Swap)
           = (n × (n-1) / 2) × samples × swap_multiplier
```

**Beispiel (Säulen 1, 3, 5 mit 10 Samples):**
```
Säulen-Paare: 3 (1v3, 1v5, 3v5)
Vergleiche: 3 × 10 × 2 = 60
```

**Use Case:** Schneller Überblick, welche Säule im Durchschnitt besser performt

---

### 2. Round Robin (implementiert)

```
Modus: round_robin
```

**Beschreibung:**
- Jeder Thread einer Säule spielt gegen jeden Thread der anderen Säule
- Vollständiges Turnier innerhalb der Säulen-Paarungen
- Ermöglicht Thread-Level Statistiken innerhalb des Säulen-Kontexts

**Formel:**
```
Für Säulen-Paar (i, j):
  Vergleiche = threads_in_i × threads_in_j

Gesamt = Σ (nᵢ × nⱼ) für alle Säulen-Paare
```

**Beispiel (Säulen 1, 3, 5 mit je 10 Threads):**
```
Säule 1 vs 3: 10 × 10 = 100 Vergleiche
Säule 1 vs 5: 10 × 10 = 100 Vergleiche
Säule 3 vs 5: 10 × 10 = 100 Vergleiche
─────────────────────────────────────────
Gesamt:                300 Vergleiche
Mit Position-Swap:     600 Vergleiche
```

**Use Case:** Umfassende Säulen-Analyse mit Thread-Level Statistiken

---

### 3. Free For All (implementiert)

```
Modus: free_for_all
```

**Beschreibung:**
- **ALLE** Threads gegen **ALLE** anderen Threads
- Säulen-Zugehörigkeit wird bei der Paarung ignoriert
- Ermöglicht absolutes Ranking aller Threads
- Säulen werden nur für Aggregation/Analyse genutzt

**Formel:**
```
Vergleiche = N × (N-1) / 2
```

**Beispiel (30 Threads total):**
```
30 × 29 / 2 = 435 Vergleiche
Mit Position-Swap: 870 Vergleiche
```

**Datenbank-Änderung:**
- Threads aus derselben Säule können gegeneinander antreten
- `pillar_a` und `pillar_b` können identisch sein

**Use Case:**
- Ermitteln der absolut besten/schlechtesten Threads
- ELO-Rating für jeden einzelnen Thread
- Konsistenz-Analyse auf Thread-Ebene
- Cross-Säulen-Überraschungen finden (z.B. schwacher Thread aus "guter" Säule)

---

### Vergleichs-Übersicht

| Modus | Granularität | Komplexität | Laufzeit | Use Case |
|-------|--------------|-------------|----------|----------|
| `pillar_sample` | Säule | O(n²) Säulen | Kurz | Schneller Überblick |
| `round_robin` | Thread (in Paarung) | O(n²) pro Paar | Mittel | Säulen-Vergleich |
| `free_for_all` | Thread (alle) | O(N²) total | Lang | Vollständiges Ranking |

---

## Multi-Worker Architektur

### Übersicht

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
│                    │   Queue   │  (DB mit Row-Level Lock)   │
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

### Worker-Pool Implementierung

```python
class JudgeWorkerPool:
    """
    Verwaltet mehrere parallele Worker für eine Session.
    """

    def __init__(self, session_id: int, worker_count: int, app):
        self.session_id = session_id
        self.worker_count = min(worker_count, 5)  # Max 5 Worker
        self.workers: List[JudgeWorker] = []
        self.app = app

    def start(self):
        """Startet alle Worker."""
        for i in range(self.worker_count):
            worker = JudgeWorker(
                session_id=self.session_id,
                worker_id=i,
                app=self.app
            )
            self.workers.append(worker)
            worker.start()

    def stop(self):
        """Stoppt alle Worker gracefully."""
        for worker in self.workers:
            worker.stop()
        self.workers.clear()
```

### Thread-sichere Comparison-Zuweisung

```python
def _get_next_comparison(self, worker_id: int):
    """
    Holt die nächste freie Comparison mit DB-Level Lock.

    Verwendet `FOR UPDATE SKIP LOCKED` um Race Conditions zu vermeiden.
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

### Socket.IO Events mit Worker-ID

```javascript
// Server → Client Events

// Comparison startet bei einem Worker
socket.emit('judge:comparison_start', {
    session_id: 123,
    worker_id: 0,           // NEU
    comparison_id: 456,
    thread_a_id: 12,
    thread_b_id: 45,
    pillar_a: 1,
    pillar_b: 3
});

// LLM Stream von einem Worker
socket.emit('judge:llm_stream', {
    session_id: 123,
    worker_id: 0,           // NEU
    token: '{"winner":'
});

// Comparison abgeschlossen
socket.emit('judge:comparison_complete', {
    session_id: 123,
    worker_id: 0,           // NEU
    winner: 'A',
    confidence: 0.85
});

// Aggregierter Status aller Worker
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

## ELO-Rating System

### Übersicht

Das ELO-System ermöglicht ein relatives Ranking aller Threads basierend auf ihren Vergleichsergebnissen.

**Parameter:**
- **Start-ELO:** 1500 (für alle Threads)
- **K-Faktor:** 32 (Standard Schach-Wert)
- **Scope:** Session-bezogen (nicht persistent über Sessions)

### ELO-Berechnung

```python
def calculate_elo_change(rating_a: float, rating_b: float,
                         winner: str, k: int = 32) -> tuple[float, float]:
    """
    Berechnet ELO-Änderungen nach einem Match.

    Args:
        rating_a: Aktuelles ELO von Thread A
        rating_b: Aktuelles ELO von Thread B
        winner: 'A', 'B', oder 'TIE'
        k: K-Faktor (höher = größere Änderungen)

    Returns:
        Tuple (new_rating_a, new_rating_b)
    """
    # Erwartete Gewinnwahrscheinlichkeiten
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 - expected_a

    # Tatsächliches Ergebnis
    if winner == 'A':
        score_a, score_b = 1.0, 0.0
    elif winner == 'B':
        score_a, score_b = 0.0, 1.0
    else:  # TIE
        score_a, score_b = 0.5, 0.5

    # Neue Ratings
    new_rating_a = rating_a + k * (score_a - expected_a)
    new_rating_b = rating_b + k * (score_b - expected_b)

    return new_rating_a, new_rating_b
```

### Datenbank-Schema

```sql
-- Neue Tabelle für Thread-ELO (Session-scoped)
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

### Thread-Leaderboard Response

```json
{
    "leaderboard": [
        {
            "rank": 1,
            "thread_id": 42,
            "pillar": 3,
            "pillar_name": "Anonymisierte Daten",
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
        },
        // ... weitere Threads
    ],
    "pillar_aggregates": {
        "1": { "avg_elo": 1520, "threads": 10 },
        "3": { "avg_elo": 1580, "threads": 10 },
        "5": { "avg_elo": 1400, "threads": 10 }
    }
}
```

---

## UI-Konzept

### JudgeConfig.vue - Erweiterte Konfiguration

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Neue Judge Session                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Session Name: [____________________________]                           │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Säulen auswählen:                                                      │
│  [✓] Säule 1   [✓] Säule 3   [✓] Säule 5   [ ] Säule 2   [ ] Säule 4   │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Vergleichs-Modus:                                                      │
│                                                                         │
│  ◉ Pillar Sample (Schnell)                                              │
│    └─ Zufällige Samples pro Säulen-Paar                                 │
│       Geschätzte Vergleiche: ~60                                        │
│                                                                         │
│  ○ Round Robin (Umfassend)                                              │
│    └─ Jeder Thread einer Säule gegen jeden der anderen                  │
│       Geschätzte Vergleiche: ~300                                       │
│                                                                         │
│  ○ Free For All (Vollständig)                                           │
│    └─ Jeder Thread gegen jeden anderen Thread                           │
│       Geschätzte Vergleiche: ~435                                       │
│       ⚠️ Lange Laufzeit (~72 Minuten bei 1 Worker)                      │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Parallele Worker: [===●===] 3                                          │
│  ℹ️ 3 Worker arbeiten parallel. Geschätzte Zeit: ~24 Minuten            │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  [✓] Position-Swap aktivieren (verdoppelt Vergleiche)                   │
│  [✓] ELO-Rating berechnen                                               │
│                                                                         │
│  Max. Threads pro Säule: [__15__] (optional, für Round Robin/FFA)       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Zusammenfassung:                                                       │
│  • 3 Säulen × ~10 Threads = 30 Threads                                  │
│  • Free For All: 435 Basis-Vergleiche                                   │
│  • Mit Position-Swap: 870 Vergleiche                                    │
│  • Mit 3 Workern: ~29 Minuten                                           │
│                                                                         │
│                                        [Session erstellen & starten]    │
└─────────────────────────────────────────────────────────────────────────┘
```

### JudgeSession.vue - Multi-Worker Live-Ansicht

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Session: Free-For-All Evaluation                            [Pause]   │
│  ████████████████████░░░░░░░░░░░░░░░░░░░  45% (392/870)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Worker: [●W1] [●W2] [●W3]  ← Klick für Fokus                          │
│                                                                         │
├────────────────────┬────────────────────┬────────────────────┬──────────┤
│                    │                    │                    │          │
│  ┌──────────────┐  │  ┌──────────────┐  │  ┌──────────────┐  │  Queue   │
│  │  Worker 1    │  │  │  Worker 2    │  │  │  Worker 3    │  │  ──────  │
│  │  ● Aktiv     │  │  │  ● Aktiv     │  │  │  ● Aktiv     │  │  478     │
│  ├──────────────┤  │  ├──────────────┤  │  ├──────────────┤  │ pending  │
│  │              │  │  │              │  │  │              │  │          │
│  │ T#12 (S1)    │  │  │ T#7 (S3)     │  │  │ T#23 (S5)    │  │  #394    │
│  │     vs       │  │  │     vs       │  │  │     vs       │  │  T12vT89 │
│  │ T#45 (S3)    │  │  │ T#89 (S5)    │  │  │ T#34 (S1)    │  │          │
│  │              │  │  │              │  │  │              │  │  #395    │
│  ├──────────────┤  │  ├──────────────┤  │  ├──────────────┤  │  T7vT34  │
│  │              │  │  │              │  │  │              │  │          │
│  │ {"winner":   │  │  │ {"step_2":   │  │  │ {"scores":   │  │  #396    │
│  │  "A", ...    │  │  │  "Die Be...  │  │  │  {"A": {...  │  │  T23vT45 │
│  │  ___         │  │  │  ___         │  │  │  ___         │  │          │
│  │              │  │  │              │  │  │              │  │   ...    │
│  ├──────────────┤  │  ├──────────────┤  │  ├──────────────┤  │          │
│  │              │  │  │              │  │  │              │  │          │
│  │ A: ●●●●○    │  │  │ A: ●●●○○    │  │  │ A: ●●●●●    │  │          │
│  │ B: ●●●○○    │  │  │ B: ●●●●○    │  │  │ B: ●●○○○    │  │          │
│  │              │  │  │              │  │  │              │  │          │
│  │ → A (82%)    │  │  │ → ???        │  │  │ → A (91%)    │  │          │
│  │              │  │  │              │  │  │              │  │          │
│  └──────────────┘  │  └──────────────┘  │  └──────────────┘  │          │
│                    │                    │                    │          │
│  [Vollbild]        │  [Vollbild]        │  [Vollbild]        │          │
│                    │                    │                    │          │
└────────────────────┴────────────────────┴────────────────────┴──────────┘
```

### JudgeResults.vue - Erweiterungen für Free For All

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Ergebnisse: Free-For-All Evaluation                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Übersicht] [Thread-Leaderboard] [ELO-Verteilung] [Säulen-Matrix]     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Thread-Leaderboard (Top 10)                                            │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Rank │ Thread │ Säule │ ELO  │ W/L/T    │ Win%  │ Ø Konf. │ Ø Score  │
│  ─────┼────────┼───────┼──────┼──────────┼───────┼─────────┼──────────│
│  🥇 1 │ T#42   │ S3    │ 1847 │ 22/5/2   │ 76%   │ 82%     │ 4.2      │
│  🥈 2 │ T#17   │ S3    │ 1802 │ 20/6/3   │ 69%   │ 79%     │ 4.1      │
│  🥉 3 │ T#8    │ S1    │ 1756 │ 18/8/3   │ 62%   │ 75%     │ 3.9      │
│     4 │ T#91   │ S5    │ 1721 │ 17/9/3   │ 59%   │ 71%     │ 3.8      │
│     5 │ T#33   │ S1    │ 1698 │ 16/10/3  │ 55%   │ 68%     │ 3.7      │
│   ... │ ...    │ ...   │ ...  │ ...      │ ...   │ ...     │ ...      │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  ELO-Verteilung nach Säule                                              │
│                                                                         │
│  Säule 1 │ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁ │ Ø 1520 │ Min: 1320 │ Max: 1756            │
│  Säule 3 │ ▁▂▃▅▇███▇▅▃▂▁   │ Ø 1620 │ Min: 1380 │ Max: 1847            │
│  Säule 5 │ ▁▃▅▆▇▆▅▃▂▁      │ Ø 1460 │ Min: 1280 │ Max: 1721            │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Überraschungs-Findings                                                 │
│                                                                         │
│  ⚡ T#8 (Säule 1) performt 25% besser als Säulen-Durchschnitt          │
│  ⚠️ T#55 (Säule 3) performt 30% schlechter als Säulen-Durchschnitt     │
│  🎯 T#91 (Säule 5) ist konsistentester Thread (σ = 0.12)               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementierungs-Phasen

### Phase 1: Vergleichs-Modi Backend ✅ (Aktuell)

**Dateien:**
- `app/routes/judge/judge_routes.py` - Erweiterte Comparison-Generierung
- `app/services/judge/comparison_generator.py` - Neue Service-Klasse

**Aufgaben:**
1. `round_robin` Modus implementieren
2. `free_for_all` Modus implementieren
3. Validierung und Schätzungs-Endpunkte

### Phase 2: Vergleichs-Modi Frontend

**Dateien:**
- `llars-frontend/src/components/Judge/JudgeConfig.vue`

**Aufgaben:**
1. Radio-Group für Modi-Auswahl
2. Dynamische Vergleichs-Schätzung
3. Warnungen bei langer Laufzeit
4. Max-Threads-pro-Säule Option

### Phase 3: Multi-Worker Backend

**Dateien:**
- `app/workers/judge_worker.py` - Worker-Pool
- `app/workers/judge_worker_pool.py` - Neue Klasse
- `app/db/tables.py` - worker_id Feld

**Aufgaben:**
1. `JudgeWorkerPool` Klasse
2. Thread-sichere Comparison-Zuweisung
3. Worker-ID in Socket.IO Events
4. Worker-Count in config_json

### Phase 4: Multi-Worker Frontend

**Dateien:**
- `llars-frontend/src/components/Judge/JudgeSession.vue`
- `llars-frontend/src/components/Judge/WorkerLane.vue` (neu)
- `llars-frontend/src/components/Judge/JudgeConfig.vue`

**Aufgaben:**
1. Worker-Lane Komponente
2. Multi-Stream Handling
3. Worker-Count Slider
4. Responsive Layout

### Phase 5: ELO-Rating System

**Dateien:**
- `app/db/tables.py` - ThreadEloScore Tabelle
- `app/services/judge/elo_service.py` (neu)
- `app/routes/judge/judge_routes.py` - Leaderboard Endpoint
- `llars-frontend/src/components/Judge/JudgeResults.vue`

**Aufgaben:**
1. ELO-Berechnung nach jeder Evaluation
2. Thread-Leaderboard API
3. ELO-Verteilung Visualisierung
4. Überraschungs-Findings

---

## API-Referenz

### Neue/Geänderte Endpoints

#### POST /api/judge/sessions

**Request Body (erweitert):**
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

**comparison_mode Werte:**
- `pillar_sample` (default) - Zufällige Samples pro Säulen-Paar
- `round_robin` - Alle Threads einer Säule gegen alle der anderen
- `free_for_all` - Alle Threads gegen alle

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
            "name": "Rollenspiele",
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

## Offene Punkte

- [ ] Rate-Limiting bei vielen Workern (LLM-API)
- [ ] Worker-Failure Recovery
- [ ] Partial Results bei Abbruch
- [ ] Export mit ELO-Daten

---

**Autor:** Claude (AI Assistant)
**Projekt:** LLARS - LLM Assisted Research System
