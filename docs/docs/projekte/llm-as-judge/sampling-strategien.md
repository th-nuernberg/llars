# Konzept: Sampling-Strategien bei unterschiedlich großen Säulen (Legacy)

!!! warning "Legacy-Konzept (Stand 2025)"
    Dieses Dokument beschreibt Sampling-Strategien aus der Judge-UI-Phase.
    In LLARS (Stand 2026-02-05) werden LLM-Evaluatoren primär als **Konfiguration im Scenario Manager** genutzt.
    Die Inhalte dienen als Hintergrund und Design-Historie.

**Datum:** 25. November 2025
**Status:** Legacy (teilweise historisch implementiert)
**Autor:** Claude / Philipp Steigerwald

---

## 1. Problemstellung

Die KIA-Datensäulen haben unterschiedlich viele E-Mail-Threads:

| Säule | Beschreibung | Erwartete Größe |
|-------|--------------|-----------------|
| 1 | Rollenspiele | Mittel (~50-100) |
| 2 | Feature aus Säule 1 | Variabel |
| 3 | Anonymisierte Daten | Groß (~200+) |
| 4 | Synthetisch generiert | Variabel |
| 5 | Live-Testungen | Klein (~20-50) |

**Problem:** Wie vergleichen wir fair, wenn z.B. Säule 3 über 200 Threads hat, aber Säule 5 nur 30?

---

## 2. Sampling-Strategien

### 2.1 Strategie A: Fixed Samples per Pillar (historisch implementiert)

**Prinzip:** Pro Säule wird eine feste Anzahl Threads gezogen (`samples_per_pillar`).

```
Säule 1: 80 Threads  → Sample: 10
Säule 3: 200 Threads → Sample: 10
Säule 5: 30 Threads  → Sample: 10
```

**Vorteile:**
- Einfach zu implementieren
- Gleiche Anzahl Vergleiche pro Säulenpaar
- Keine Verzerrung durch Überrepräsentation

**Nachteile:**
- Viele Daten aus größeren Säulen werden ignoriert
- Möglicherweise nicht repräsentativ für die Gesamtpopulation

**Verwendung:** Standardmodus in `pillar_sample` (N wird explizit gesetzt).

---

### 2.2 Strategie B: Bootstrap Sampling mit Replacement

**Prinzip:** Bei kleineren Säulen werden Threads mehrfach verwendet (mit Ersetzung).

```
Säule 1: 80 Threads  → Sample: 50 (einmalig)
Säule 5: 30 Threads  → Sample: 50 (mit ~20 Wiederholungen)
```

**Vorteile:**
- Alle Threads werden genutzt
- Größere Sample-Größen möglich
- Statistische Methode zur Varianzschätzung

**Nachteile:**
- Wiederholte Threads können Ergebnisse verzerren
- Kein echter "neuer" Vergleich bei Wiederholung

**Empfehlung:** Nur verwenden, wenn statistische Konfidenzintervalle berechnet werden sollen.

---

### 2.3 Strategie C: Gewichtetes Sampling

**Prinzip:** Größere Säulen werden mit höherem Gewicht bewertet.

```python
# Beispiel-Berechnung
weight_pillar_1 = len(threads_1) / total_threads  # z.B. 0.25
weight_pillar_3 = len(threads_3) / total_threads  # z.B. 0.65
weight_pillar_5 = len(threads_5) / total_threads  # z.B. 0.10

# Gewichtete Win-Rate
weighted_win_rate = wins * weight
```

**Vorteile:**
- Berücksichtigt die "Wichtigkeit" jeder Säule
- Fair bei unterschiedlichen Datenmengen

**Nachteile:**
- Komplexere Berechnung
- Schwerer zu interpretieren

**Empfehlung:** Für finale Auswertungen, nicht für Live-Vergleiche.

---

### 2.4 Strategie D: Round-Robin mit Wiederholungen (Empfohlen, historisch)

**Prinzip:** Mehrere Durchläufe (`repetitions_per_pair`), bei jedem Durchlauf zufällige Threads.

```
Durchlauf 1: Thread 1 vs Thread A, Thread 2 vs Thread B, ...
Durchlauf 2: Thread 3 vs Thread C, Thread 4 vs Thread D, ...
Durchlauf 3: Thread 5 vs Thread E, Thread 1 vs Thread F, ... (Wiederholung beginnt)
```

**Ablauf:**
1. Für jedes Säulenpaar (z.B. 1 vs 3):
2. Pro Durchlauf: Zufällige Auswahl von N Threads aus jeder Säule
3. 1:1 Paarung der Threads
4. Bei kleiner Säule: Threads werden in späteren Durchläufen wiederverwendet

**Vorteile:**
- Alle Threads haben Chance, verglichen zu werden
- Mehrfache Wiederholungen erhöhen statistische Sicherheit
- Position-Swap pro Vergleich reduziert Position-Bias
- Bereits implementiert (`repetitions_per_pair` Parameter)

**Nachteile:**
- Höhere Anzahl Vergleiche = mehr API-Kosten
- Längere Laufzeit

**Konfiguration:**
```javascript
// JudgeConfig.vue
{
  samplesPerPillar: 10,     // Pro Durchlauf
  repetitionsPerPair: 3,    // Anzahl Durchläufe
  positionSwap: true        // A/B und B/A
}
// → Gesamt: 10 × 3 × 2 = 60 Vergleiche pro Säulenpaar
```

---

## 3. Empfohlene Konfiguration

### Szenario: Explorative Analyse (schnell)

```javascript
{
  selectedPillars: [1, 3, 5],
  samplesPerPillar: 5,
  repetitionsPerPair: 1,
  positionSwap: true
}
// Paare: 3 (1-3, 1-5, 3-5)
// Vergleiche: 3 × 5 × 2 = 30 Vergleiche
// Dauer: ~5 Minuten
```

### Szenario: Robuste Evaluation (empfohlen)

```javascript
{
  selectedPillars: [1, 3, 5],
  samplesPerPillar: 10,
  repetitionsPerPair: 3,
  positionSwap: true
}
// Paare: 3 (1-3, 1-5, 3-5)
// Vergleiche: 3 × 10 × 3 × 2 = 180 Vergleiche
// Dauer: ~30 Minuten
```

### Szenario: Vollständige Evaluation (wissenschaftlich)

```javascript
{
  selectedPillars: [1, 3, 5],
  samplesPerPillar: 20,
  repetitionsPerPair: 5,
  positionSwap: true
}
// Paare: 3 (1-3, 1-5, 3-5)
// Vergleiche: 3 × 20 × 5 × 2 = 600 Vergleiche
// Dauer: ~100 Minuten
```

---

## 4. Metriken zur Validierung

### 4.1 Sample Coverage

Misst, wie viel Prozent der Threads einer Säule tatsächlich verglichen wurden.

```python
coverage = unique_threads_compared / total_threads_in_pillar
```

**Ziel:** > 50% bei kleinen Säulen, > 20% bei großen Säulen

### 4.2 Repetition Overlap

Misst, wie oft dieselben Threads in verschiedenen Durchläufen verwendet wurden.

```python
overlap_rate = repeated_threads / total_thread_uses
```

**Ziel:** < 30% (niedrig = mehr Vielfalt)

### 4.3 Win-Rate Varianz über Repetitions

Misst die Stabilität der Ergebnisse.

```python
# Win-Rates pro Durchlauf berechnen
win_rates = [win_rate_rep1, win_rate_rep2, win_rate_rep3]
variance = np.var(win_rates)
```

**Ziel:** Varianz < 0.05 (stabile Ergebnisse)

---

## 5. Thread-Performance-Tracking (NEU)

### 5.1 Warum Thread-Performance tracken?

Durch das Tracking einzelner Threads können wir:

1. **Qualitäts-Validierung:** Threads die gegen viele verschiedene Gegner verlieren sind wahrscheinlich qualitativ schwächer
2. **Likert-Konsistenz prüfen:** Bekommt ein Thread ähnliche Bewertungen egal gegen wen er antritt?
3. **Sampling-Bias erkennen:** Wurde ein Thread zu oft/zu selten verwendet?

### 5.2 Per-Thread Metriken

```python
# Für jeden Thread der in Vergleichen verwendet wurde:
{
    'thread_id': 123,
    'pillar': 1,
    'usage_count': 5,           # Wie oft wurde der Thread verwendet?
    'unique_opponents': 4,       # Gegen wie viele verschiedene Threads?
    'wins': 3,
    'losses': 1,
    'ties': 1,
    'win_rate': 0.6,
    'performance_score': 0.4,   # win_rate - loss_rate (-1 bis +1)
    'is_consistent_winner': True,
    'is_consistent_loser': False,

    # Likert-Konsistenz (NEU)
    'likert_scores': {
        'quality': {'mean': 4.2, 'std_dev': 0.3, 'is_consistent': True},
        'empathy': {'mean': 3.8, 'std_dev': 0.8, 'is_consistent': False},
        ...
    },
    'likert_consistency_score': 0.75  # 0-1, höher = konsistenter
}
```

### 5.3 Likert-Konsistenz-Analyse

**Frage:** Wenn Thread A mehrfach bewertet wird, bekommt er immer ähnliche Likert-Scores?

**Beispiel:**
```
Thread A vs Thread X: quality_a = 4
Thread A vs Thread Y: quality_a = 4
Thread A vs Thread Z: quality_a = 5
→ std_dev = 0.47, is_consistent = True ✓

Thread B vs Thread X: quality_b = 2
Thread B vs Thread Y: quality_b = 5
Thread B vs Thread Z: quality_b = 3
→ std_dev = 1.25, is_consistent = False ✗
```

**Interpretation:**
- **Konsistent (std_dev < 0.5):** Das LLM bewertet diesen Thread zuverlässig
- **Inkonsistent (std_dev > 0.5):** Die Bewertung variiert stark - mögliche Gründe:
  - Thread hat gemischte Qualität
  - LLM ist unsicher
  - Opponent-abhängige Bewertung

### 5.4 Consistent Winners/Losers

**Consistent Winner:** Thread mit >= 70% Win-Rate über mindestens 3 Vergleiche
- Diese Threads repräsentieren hohe Qualität der Säule
- Nützlich für Benchmark-Erstellung

**Consistent Loser:** Thread mit >= 70% Loss-Rate über mindestens 3 Vergleiche
- Diese Threads repräsentieren niedrige Qualität
- Kandidaten für manuelle Überprüfung

### 5.5 API Endpoint

```
GET /api/judge/sessions/{id}/thread-performance

Response:
{
    "total_threads": 45,
    "total_comparisons": 120,
    "avg_usage_per_thread": 5.3,
    "coverage_stats": {
        "over_sampled_count": 3,
        "under_sampled_count": 8,
        "evenly_sampled_count": 34
    },
    "threads": [...],
    "pillar_summary": {...},
    "consistent_winners": [...],
    "consistent_losers": [...],
    "likert_consistency": {
        "global": {
            "quality": {"mean": 3.8, "std_dev": 0.9},
            "empathy": {"mean": 4.1, "std_dev": 0.7}
        },
        "inconsistent_threads": [...]
    }
}
```

---

## 6. Implementierungs-Roadmap

### Phase 1: Basis (Bereits implementiert)

- [x] `repetitions_per_pair` Parameter in JudgeConfig
- [x] Round-Robin Sampling in Backend
- [x] Position-Swap Konsistenz-Analyse
- [x] Thread-Performance Endpoint mit Usage-Tracking
- [x] Likert-Konsistenz-Analyse per Thread

### Phase 2: Erweiterungen (Nächste Schritte)

- [ ] Thread-Performance Sektion in JudgeResults.vue
- [ ] Sample Coverage Visualisierung
- [ ] Warnung wenn kleine Säule < samples_per_pillar hat
- [ ] Export der Thread-Performance Daten

### Phase 3: Erweiterte Strategien

- [ ] Gewichtetes Sampling als Option
- [ ] Bootstrap Confidence Intervals
- [ ] Automatische Strategie-Empfehlung basierend auf Säulengrößen
- [ ] Thread-Qualitäts-Clustering basierend auf Likert-Scores

---

## 7. Frontend-Erweiterungen

### 7.1 Säulen-Info in JudgeConfig

Zeige die verfügbare Thread-Anzahl pro Säule an:

```vue
<v-chip v-for="pillar in availablePillars" ...>
  {{ pillar.name }}
  <v-badge :content="pillar.threadCount" color="info" />
</v-chip>
```

### 7.2 Warnung bei ungleichen Säulen

```vue
<v-alert v-if="hasUnequalPillars" type="warning">
  Die ausgewählten Säulen haben unterschiedliche Größen.
  Empfehlung: Erhöhen Sie die Wiederholungen auf {{ recommendedRepetitions }}.
</v-alert>
```

### 7.3 Coverage-Anzeige in Results

```vue
<v-card title="Sample Coverage">
  <v-list>
    <v-list-item v-for="pillar in coverage">
      Säule {{ pillar.id }}: {{ pillar.coverage }}%
      ({{ pillar.used }}/{{ pillar.total }})
    </v-list-item>
  </v-list>
</v-card>
```

---

## 8. Zusammenfassung

| Strategie | Fairness | Aufwand | Empfehlung |
|-----------|----------|---------|------------|
| Proportional | Hoch | Niedrig | Standard |
| Bootstrap | Mittel | Mittel | Konfidenzintervalle |
| Gewichtet | Hoch | Hoch | Finale Reports |
| **Round-Robin** | **Hoch** | **Mittel** | **Empfohlen** |

**Empfehlung:** Round-Robin mit `repetitions_per_pair >= 3` für robuste Ergebnisse bei unterschiedlich großen Säulen. Die aktuelle Implementierung unterstützt dies bereits.

---

## 9. Position-Swap Konsistenz-Analyse (NEU)

### 9.1 Hintergrund

Position-Swap Konsistenz ist ein kritisches Qualitätsmaß für LLM Evaluator Evaluationen. Basierend auf:
- [Zheng et al. (2023): "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"](https://arxiv.org/abs/2306.05685)
- [arXiv:2406.07791: "Judging the Judges: Position Bias in Pairwise Assessments"](https://arxiv.org/abs/2406.07791)

### 9.2 Metriken

| Metrik | Beschreibung | Zielwert |
|--------|--------------|----------|
| **Consistency Rate** | % der Swap-Paare wo gleicher Thread gewinnt | ≥ 80% (excellent) |
| **Primacy Bias** | Tendenz, Position A (ersten) zu bevorzugen | < 20% |
| **Recency Bias** | Tendenz, Position B (letzten) zu bevorzugen | < 20% |
| **Likert Stability** | Wie stark ändern sich Scores bei Positionswechsel? | Δ ≤ 1 |

### 9.3 Interpretation

```
Consistency Rate ≥ 80%  → "excellent" - Ergebnisse sind zuverlässig
Consistency Rate ≥ 60%  → "good" - Akzeptabel, leichte Position Bias
Consistency Rate ≥ 40%  → "fair" - Signifikanter Bias, Vorsicht
Consistency Rate < 40%  → "poor" - Ergebnisse nicht vertrauenswürdig
```

### 9.4 Position Bias Typen

**Primacy Bias (Position A bevorzugt):**
```
Original:  A=Thread1, B=Thread2 → Winner: A (Thread1)
Swapped:   A=Thread2, B=Thread1 → Winner: A (Thread2)
→ Unterschiedlicher Thread gewinnt, aber immer Position A
```

**Recency Bias (Position B bevorzugt):**
```
Original:  A=Thread1, B=Thread2 → Winner: B (Thread2)
Swapped:   A=Thread2, B=Thread1 → Winner: B (Thread1)
→ Unterschiedlicher Thread gewinnt, aber immer Position B
```

### 9.5 Likert-Score Stabilität

Prüft ob der gleiche Thread ähnliche Scores erhält, unabhängig ob als A oder B:

```
Thread 123 als Position A: quality=4, empathy=5
Thread 123 als Position B: quality=3, empathy=5
→ quality Δ=1 (stabil), empathy Δ=0 (sehr stabil)
```

**Stabilitäts-Kriterien:**
- Δ ≤ 1: Stabil
- Δ > 1: Instabil (Position beeinflusst Bewertung)

### 9.6 API Endpoint

```
GET /api/judge/sessions/{id}/position-swap-analysis

Response:
{
    "summary": {
        "total_swap_pairs": 30,
        "consistency_rate": 0.8333,
        "consistent_wins": 20,
        "consistent_ties": 5,
        "inconsistent": 5
    },
    "position_bias": {
        "primacy_count": 2,
        "recency_count": 3,
        "dominant_bias": "balanced"
    },
    "likert_stability": {
        "quality": {"mean_delta": 0.5, "stability_rate": 0.85},
        "empathy": {"mean_delta": 0.3, "stability_rate": 0.92},
        ...
    },
    "interpretation": {
        "overall_quality": "excellent",
        "recommendations": ["Position-swap consistency is acceptable."]
    },
    "pairs": [
        {
            "thread_1_id": 123,
            "thread_2_id": 456,
            "is_consistent": true,
            "consistency_type": "consistent_win",
            "likert_comparison": {...}
        },
        ...
    ]
}
```

### 9.7 Empfehlungen bei niedrigem Consistency Rate

1. **Majority Voting:** Mehrere Evaluationen pro Paar, Mehrheitsentscheidung
2. **Score Averaging:** Likert-Scores über Positionen mitteln
3. **Tie Annotation:** Bei Inkonsistenz als "Tie" werten (PandaLM Ansatz)
4. **Few-Shot Prompting:** Beispiele im Prompt erhöhen Konsistenz

---

## 10. Referenzen

- Zheng et al. (2023): "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
- arXiv:2406.07791: "Judging the Judges: Position Bias in Pairwise Assessments"
- LMSYS Chatbot Arena: Position Bias Mitigation Strategies
- Bradley-Terry Model für paarweise Vergleiche
