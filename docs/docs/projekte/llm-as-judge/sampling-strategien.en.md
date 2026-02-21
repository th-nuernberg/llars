# Concept: Sampling Strategies for Uneven Pillar Sizes (Legacy)

!!! warning "Legacy Concept (as of 2025)"
    This document describes sampling strategies from the historical Judge-UI phase.
    In LLARS (as of 2026-02-05), LLM evaluators are primarily used as a **configuration in Scenario Manager**.
    The content serves as background and design history.

**Date:** November 25, 2025
**Status:** Legacy (partially historically implemented)
**Author:** Claude / Philipp Steigerwald

---

## 1. Problem statement

The KIA data pillars have different numbers of email threads:

| Pillar | Description | Expected size |
|-------|--------------|-----------------|
| 1 | Role plays | Medium (~50-100) |
| 2 | Feature from pillar 1 | Variable |
| 3 | Anonymized data | Large (~200+) |
| 4 | Synthetically generated | Variable |
| 5 | Live tests | Small (~20-50) |

**Problem:** How do we compare fairly if, for example, pillar 3 has 200+ threads but pillar 5 only 30?

---

## 2. Sampling strategies

### 2.1 Strategy A: Fixed samples per pillar (historically implemented)

**Principle:** A fixed number of threads is drawn per pillar (`samples_per_pillar`).

```
Pillar 1: 80 threads  -> Sample: 10
Pillar 3: 200 threads -> Sample: 10
Pillar 5: 30 threads  -> Sample: 10
```

**Pros:**
- Easy to implement
- Same number of comparisons per pillar pair
- No overrepresentation bias

**Cons:**
- Many threads from larger pillars are ignored
- May not be representative of the full population

**Usage:** Standard mode in `pillar_sample` (N is explicitly set).

---

### 2.2 Strategy B: Bootstrap sampling with replacement

**Principle:** For smaller pillars, threads are used multiple times (with replacement).

```
Pillar 1: 80 threads  -> Sample: 50 (unique)
Pillar 5: 30 threads  -> Sample: 50 (with ~20 repeats)
```

**Pros:**
- All threads are used
- Larger sample sizes possible
- Statistical method for variance estimation

**Cons:**
- Repeated threads can bias results
- Not a truly "new" comparison when repeated

**Recommendation:** Only use if statistical confidence intervals are required.

---

### 2.3 Strategy C: Weighted sampling

**Principle:** Larger pillars are weighted more heavily.

```python
# Example calculation
weight_pillar_1 = len(threads_1) / total_threads  # e.g. 0.25
weight_pillar_3 = len(threads_3) / total_threads  # e.g. 0.65
weight_pillar_5 = len(threads_5) / total_threads  # e.g. 0.10

# Weighted win rate
weighted_win_rate = wins * weight
```

**Pros:**
- Accounts for the "importance" of each pillar
- Fair with different data volumes

**Cons:**
- More complex calculation
- Harder to interpret

**Recommendation:** For final reports, not for live comparisons.

---

### 2.4 Strategy D: Round robin with repetitions (recommended, historical)

**Principle:** Multiple passes (`repetitions_per_pair`), each with random threads.

```
Pass 1: Thread 1 vs Thread A, Thread 2 vs Thread B, ...
Pass 2: Thread 3 vs Thread C, Thread 4 vs Thread D, ...
Pass 3: Thread 5 vs Thread E, Thread 1 vs Thread F, ... (repeats begin)
```

**Flow:**
1. For each pillar pair (e.g. 1 vs 3):
2. Per pass: random selection of N threads from each pillar
3. 1:1 pairing of threads
4. For small pillars: threads are reused in later passes

**Pros:**
- All threads have a chance to be compared
- Repetitions increase statistical reliability
- Position swap per comparison reduces position bias
- Already implemented (`repetitions_per_pair` parameter)

**Cons:**
- More comparisons = higher API cost
- Longer runtime

**Configuration:**
```javascript
// JudgeConfig.vue
{
  samplesPerPillar: 10,     // Per pass
  repetitionsPerPair: 3,    // Number of passes
  positionSwap: true        // A/B and B/A
}
// -> Total: 10 × 3 × 2 = 60 comparisons per pillar pair
```

---

## 3. Recommended configuration

### Scenario: Explorative analysis (fast)

```javascript
{
  selectedPillars: [1, 3, 5],
  samplesPerPillar: 5,
  repetitionsPerPair: 1,
  positionSwap: true
}
// Pairs: 3 (1-3, 1-5, 3-5)
// Comparisons: 3 × 5 × 2 = 30 comparisons
// Duration: ~5 minutes
```

### Scenario: Robust evaluation (recommended)

```javascript
{
  selectedPillars: [1, 3, 5],
  samplesPerPillar: 10,
  repetitionsPerPair: 3,
  positionSwap: true
}
// Pairs: 3 (1-3, 1-5, 3-5)
// Comparisons: 3 × 10 × 3 × 2 = 180 comparisons
// Duration: ~30 minutes
```

### Scenario: Full evaluation (scientific)

```javascript
{
  selectedPillars: [1, 3, 5],
  samplesPerPillar: 20,
  repetitionsPerPair: 5,
  positionSwap: true
}
// Pairs: 3 (1-3, 1-5, 3-5)
// Comparisons: 3 × 20 × 5 × 2 = 600 comparisons
// Duration: ~100 minutes
```

---

## 4. Validation metrics

### 4.1 Sample coverage

Measures the percentage of threads in a pillar that were actually compared.

```python
coverage = unique_threads_compared / total_threads_in_pillar
```

**Goal:** > 50% for small pillars, > 20% for large pillars

### 4.2 Repetition overlap

Measures how often the same threads were used in different passes.

```python
overlap_rate = repeated_threads / total_thread_uses
```

**Goal:** < 30% (lower = more variety)

### 4.3 Win-rate variance across repetitions

Measures result stability.

```python
# Win rates per pass
win_rates = [win_rate_rep1, win_rate_rep2, win_rate_rep3]
variance = np.var(win_rates)
```

**Goal:** variance < 0.05 (stable results)

---

## 5. Thread performance tracking (NEW)

### 5.1 Why track thread performance?

Tracking individual threads allows us to:

1. **Quality validation:** Threads that lose against many opponents are likely lower quality
2. **Likert consistency:** Does a thread receive similar ratings regardless of opponent?
3. **Sampling bias detection:** Was a thread used too often or too rarely?

### 5.2 Per-thread metrics

```python
# For each thread used in comparisons:
{
    'thread_id': 123,
    'pillar': 1,
    'usage_count': 5,           # How often was the thread used?
    'unique_opponents': 4,       # Against how many different threads?
    'wins': 3,
    'losses': 1,
    'ties': 1,
    'win_rate': 0.6,
    'performance_score': 0.4,   # win_rate - loss_rate (-1 to +1)
    'is_consistent_winner': True,
    'is_consistent_loser': False,

    # Likert consistency (NEW)
    'likert_scores': {
        'quality': {'mean': 4.2, 'std_dev': 0.3, 'is_consistent': True},
        'empathy': {'mean': 3.8, 'std_dev': 0.8, 'is_consistent': False},
        ...
    },
    'likert_consistency_score': 0.75  # 0-1, higher = more consistent
}
```

### 5.3 Likert consistency analysis

**Question:** If thread A is rated multiple times, does it receive similar Likert scores?

**Example:**
```
Thread A vs Thread X: quality_a = 4
Thread A vs Thread Y: quality_a = 4
Thread A vs Thread Z: quality_a = 5
-> std_dev = 0.47, is_consistent = True

Thread B vs Thread X: quality_b = 2
Thread B vs Thread Y: quality_b = 5
Thread B vs Thread Z: quality_b = 3
-> std_dev = 1.25, is_consistent = False
```

**Interpretation:**
- **Consistent (std_dev < 0.5):** The LLM rates this thread reliably
- **Inconsistent (std_dev > 0.5):** Ratings vary widely - possible reasons:
  - Thread has mixed quality
  - LLM is uncertain
  - Opponent-dependent evaluation

### 5.4 Consistent winners/losers

**Consistent winner:** Thread with >= 70% win rate over at least 3 comparisons
- These threads represent high pillar quality
- Useful for benchmark creation

**Consistent loser:** Thread with >= 70% loss rate over at least 3 comparisons
- These threads represent low quality
- Candidates for manual review

### 5.5 API endpoint

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

## 6. Implementation roadmap

### Phase 1: Basics (already implemented)

- [x] `repetitions_per_pair` parameter in JudgeConfig
- [x] Round-robin sampling in backend
- [x] Position-swap consistency analysis
- [x] Thread-performance endpoint with usage tracking
- [x] Likert consistency analysis per thread

### Phase 2: Extensions (next steps)

- [ ] Thread-performance section in JudgeResults.vue
- [ ] Sample coverage visualization
- [ ] Warning when a small pillar has < samples_per_pillar
- [ ] Export thread-performance data

### Phase 3: Advanced strategies

- [ ] Weighted sampling as an option
- [ ] Bootstrap confidence intervals
- [ ] Automatic strategy recommendation based on pillar size
- [ ] Thread-quality clustering based on Likert scores

---

## 7. Frontend extensions

### 7.1 Pillar info in JudgeConfig

Show available thread counts per pillar:

```vue
<v-chip v-for="pillar in availablePillars" ...>
  {{ pillar.name }}
  <v-badge :content="pillar.threadCount" color="info" />
</v-chip>
```

### 7.2 Warning for uneven pillars

```vue
<v-alert v-if="hasUnequalPillars" type="warning">
  The selected pillars have different sizes.
  Recommendation: Increase repetitions to {{ recommendedRepetitions }}.
</v-alert>
```

### 7.3 Coverage display in Results

```vue
<v-card title="Sample Coverage">
  <v-list>
    <v-list-item v-for="pillar in coverage">
      Pillar {{ pillar.id }}: {{ pillar.coverage }}%
      ({{ pillar.used }}/{{ pillar.total }})
    </v-list-item>
  </v-list>
</v-card>
```

---

## 8. Summary

| Strategy | Fairness | Effort | Recommendation |
|-----------|----------|---------|------------|
| Proportional | High | Low | Standard |
| Bootstrap | Medium | Medium | Confidence intervals |
| Weighted | High | High | Final reports |
| **Round robin** | **High** | **Medium** | **Recommended** |

**Recommendation:** Round robin with `repetitions_per_pair >= 3` for robust results with uneven pillar sizes. The current implementation supports this.

---

## 9. Position-swap consistency analysis (NEW)

### 9.1 Background

Position-swap consistency is a critical quality metric for LLM evaluation. Based on:
- [Zheng et al. (2023): "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"](https://arxiv.org/abs/2306.05685)
- [arXiv:2406.07791: "Judging the Judges: Position Bias in Pairwise Assessments"](https://arxiv.org/abs/2406.07791)

### 9.2 Metrics

| Metric | Description | Target |
|--------|--------------|--------|
| **Consistency rate** | % of swap pairs where the same thread wins | >= 80% (excellent) |
| **Primacy bias** | Tendency to prefer position A (first) | < 20% |
| **Recency bias** | Tendency to prefer position B (last) | < 20% |
| **Likert stability** | How much scores change on position swap | Δ <= 1 |

### 9.3 Interpretation

```
Consistency rate >= 80%  -> "excellent" - results are reliable
Consistency rate >= 60%  -> "good" - acceptable, slight position bias
Consistency rate >= 40%  -> "fair" - significant bias, caution
Consistency rate < 40%   -> "poor" - results not trustworthy
```

### 9.4 Position bias types

**Primacy bias (position A preferred):**
```
Original:  A=Thread1, B=Thread2 -> Winner: A (Thread1)
Swapped:   A=Thread2, B=Thread1 -> Winner: A (Thread2)
-> Different thread wins, but always position A
```

**Recency bias (position B preferred):**
```
Original:  A=Thread1, B=Thread2 -> Winner: B (Thread2)
Swapped:   A=Thread2, B=Thread1 -> Winner: B (Thread1)
-> Different thread wins, but always position B
```

### 9.5 Likert score stability

Checks whether the same thread receives similar scores regardless of being A or B:

```
Thread 123 as position A: quality=4, empathy=5
Thread 123 as position B: quality=3, empathy=5
-> quality Δ=1 (stable), empathy Δ=0 (very stable)
```

**Stability criteria:**
- Δ <= 1: stable
- Δ > 1: unstable (position influences rating)

### 9.6 API endpoint

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

### 9.7 Recommendations for low consistency rate

1. **Majority voting:** Multiple evaluations per pair, majority decision
2. **Score averaging:** Average Likert scores across positions
3. **Tie annotation:** Treat inconsistency as "tie" (PandaLM approach)
4. **Few-shot prompting:** Examples in the prompt increase consistency

---

## 10. References

- Zheng et al. (2023): "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
- arXiv:2406.07791: "Judging the Judges: Position Bias in Pairwise Assessments"
- LMSYS Chatbot Arena: position bias mitigation strategies
- Bradley-Terry model for pairwise comparisons
