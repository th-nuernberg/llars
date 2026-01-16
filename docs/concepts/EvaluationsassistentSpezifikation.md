# Evaluationsassistent - Finale Spezifikation

**Version:** 1.0 | **Stand:** 14. Januar 2026
**Status:** APPROVED - Ready for Implementation
**Ziel:** IJCAI-ECAI 2026 Demo Track (Deadline: 16. Februar 2026)

---

## 1. Entscheidungen

### 1.1 LLM-Evaluator Trigger
**Entscheidung:** Sofort bei Szenario-Start

- LLMs beginnen automatisch wenn `scenario.begin <= now`
- Async-Worker startet im Hintergrund
- Kein manueller Eingriff nötig
- Live-Monitoring zeigt Fortschritt

### 1.2 Prompt-Template Verwaltung
**Entscheidung:** Globale Defaults + Override pro Szenario

- Admin verwaltet globale Default-Prompts im Admin-Panel
- Researcher können pro Szenario überschreiben
- Versionierung der Prompts für Reproduzierbarkeit

### 1.3 Token-Budget & Tracking
**Entscheidung:** Budget pro User mit detailliertem Tracking

Tracking erfasst:
- Wer (User)
- Wieviele Tokens (input + output)
- Welches Szenario
- Welches Model
- Wann (Timestamp)
- Kosten (berechnet aus Token-Preisen)

Budget-Enforcement:
- X Tokens/Monat pro Researcher (konfigurierbar)
- Warnung bei 80% Verbrauch
- Hard-Stop bei 100%

### 1.4 Fehlerbehandlung
**Entscheidung:** 3 Retries + Queue für später

- Max 3 Retries bei JSON-Fehlern
- Exponential Backoff bei Rate-Limits
- Queue für Provider-Ausfälle
- Fehler werden gespeichert mit Details

### 1.5 Agreement-Metriken
**Entscheidung:** Alle mit Tooltip-Erklärung

| Metrik | Formel | Anwendung |
|--------|--------|-----------|
| Prozentuale Übereinstimmung | `matches / total` | Basis-Metrik |
| Cohen's Kappa | `(p_o - p_e) / (1 - p_e)` | Paarweise, kategorisch |
| Fleiss' Kappa | Erweiterung Cohen | Multi-Rater |
| Krippendorff's Alpha | `1 - D_o / D_e` | Universell |
| Kendall's Tau | Konkordanz/Diskordanz | Rankings |
| Spearman's Rho | Rang-Korrelation | Ordinal |

### 1.6 Export-Formate
**Entscheidung:** Alle

- CSV (Basis)
- JSON (Programmatisch)
- LaTeX-Tabellen (Paper-ready)
- Excel (.xlsx) (Formatiert)
- PDF-Report (Zusammenfassung)

### 1.7 Datenbank
**Entscheidung:** Neue Tabellen erstellen

- `prompt_templates` - Prompt-Verwaltung
- `llm_usage_tracking` - Token-Tracking
- `user_token_budgets` - Budget-Verwaltung

### 1.8 UI-Integration
**Entscheidung:** Neuer Menüpunkt

- "🧪 Evaluationsassistent" als Top-Level-Eintrag
- Separate Navigation von Admin-Panel
- Rollenbasierte Sichtbarkeit

---

## 2. Architektur-Übersicht

### 2.1 Neue Datenbank-Tabellen

```sql
-- Prompt-Templates
CREATE TABLE prompt_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,  -- ranking, rating, authenticity, etc.
    version VARCHAR(20) DEFAULT '1.0',

    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,

    variables JSON,  -- ["features", "thread_content", ...]
    output_schema_version VARCHAR(20) DEFAULT '1.0',

    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    created_by VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_task_default (task_type, is_default)
);

-- LLM Usage Tracking
CREATE TABLE llm_usage_tracking (
    id INT PRIMARY KEY AUTO_INCREMENT,

    user_id INT NOT NULL,
    scenario_id INT,
    thread_id INT,
    model_id VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,

    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    total_tokens INT GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,

    estimated_cost_usd DECIMAL(10, 6),  -- Geschätzte Kosten

    prompt_template_id INT,
    prompt_version VARCHAR(20),

    processing_time_ms INT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (scenario_id) REFERENCES rating_scenarios(id),
    FOREIGN KEY (prompt_template_id) REFERENCES prompt_templates(id),

    INDEX idx_user_month (user_id, created_at),
    INDEX idx_scenario (scenario_id),
    INDEX idx_model (model_id)
);

-- User Token Budgets
CREATE TABLE user_token_budgets (
    id INT PRIMARY KEY AUTO_INCREMENT,

    user_id INT NOT NULL UNIQUE,
    monthly_token_limit INT NOT NULL DEFAULT 1000000,  -- 1M Tokens default

    current_month_usage INT DEFAULT 0,
    last_reset_date DATE,

    warning_threshold_percent INT DEFAULT 80,
    is_hard_limit BOOLEAN DEFAULT TRUE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Erweiterung LLMTaskResult
ALTER TABLE llm_task_results
ADD COLUMN reasoning_json JSON AFTER payload_json,
ADD COLUMN prompt_template_id INT AFTER reasoning_json,
ADD COLUMN prompt_version VARCHAR(20) AFTER prompt_template_id,
ADD COLUMN input_tokens INT AFTER prompt_version,
ADD COLUMN output_tokens INT AFTER input_tokens,
ADD COLUMN processing_time_ms INT AFTER output_tokens;
```

### 2.2 Backend-Services

```
app/services/
├── evaluation_assistant/
│   ├── __init__.py
│   ├── scenario_service.py          # Szenario CRUD für Researcher
│   ├── llm_evaluator_service.py     # LLM-Evaluation Orchestration
│   ├── prompt_template_service.py   # Prompt-Template Verwaltung
│   ├── token_budget_service.py      # Budget-Tracking & Enforcement
│   ├── agreement_metrics_service.py # IRR-Metriken Berechnung
│   └── export_service.py            # Export-Generierung
```

### 2.3 Frontend-Komponenten

```
llars-frontend/src/
├── views/
│   └── EvaluationAssistant/
│       ├── EvaluationAssistant.vue      # Haupt-Container
│       ├── MyScenariosDashboard.vue     # Meine Szenarien
│       ├── ScenarioWizard.vue           # Szenario erstellen
│       ├── ScenarioMonitor.vue          # Live-Monitoring
│       ├── ResponseExplorer.vue         # Transparenz-Explorer
│       ├── ResultsExport.vue            # Export-Center
│       └── ParticipateHub.vue           # Teilnehmer-Ansicht
│
├── components/
│   └── EvaluationAssistant/
│       ├── ResponseCard.vue             # Universal Response
│       ├── LlmProgressCard.vue          # LLM-Fortschritt
│       ├── AgreementMetrics.vue         # Metriken mit Tooltips
│       ├── TokenUsageChart.vue          # Budget-Visualisierung
│       └── displays/
│           ├── RankingResponseDisplay.vue
│           ├── RatingResponseDisplay.vue
│           ├── AuthenticityResponseDisplay.vue
│           ├── MailRatingResponseDisplay.vue
│           └── ComparisonResponseDisplay.vue
```

### 2.4 API-Endpoints

```python
# Evaluation Assistant Routes
/api/evaluation/
├── GET    /my-scenarios                    # Eigene Szenarien
├── POST   /scenarios                       # Szenario erstellen
├── GET    /scenarios/<id>                  # Szenario-Details
├── PUT    /scenarios/<id>                  # Szenario bearbeiten
├── DELETE /scenarios/<id>                  # Szenario löschen
├── GET    /scenarios/<id>/monitor          # Live-Monitoring Daten
├── GET    /scenarios/<id>/responses        # Alle Responses
├── GET    /scenarios/<id>/responses/<tid>  # Thread-Responses
├── GET    /scenarios/<id>/metrics          # Agreement-Metriken
├── POST   /scenarios/<id>/export           # Export generieren
├── GET    /my-assignments                  # Meine Aufgaben (Evaluator)
├── GET    /my-budget                       # Mein Token-Budget
│
# Prompt Template Routes (Admin)
/api/admin/prompt-templates/
├── GET    /                                # Alle Templates
├── POST   /                                # Template erstellen
├── GET    /<id>                            # Template-Details
├── PUT    /<id>                            # Template bearbeiten
├── DELETE /<id>                            # Template löschen
├── POST   /<id>/set-default                # Als Default setzen
│
# Token Budget Routes (Admin)
/api/admin/token-budgets/
├── GET    /                                # Alle Budgets
├── GET    /usage-report                    # Nutzungs-Report
├── PUT    /user/<id>                       # Budget anpassen
├── POST   /reset/<id>                      # Budget zurücksetzen
```

---

## 3. Szenario-Typen & LLM-Schemas

### 3.1 Ranking

**Menschliche Eingabe:** Drag & Drop in 4 Buckets
**LLM-Schema:**
```python
class RankingEvaluationResult(BaseModel):
    buckets: Dict[Literal["gut", "mittel", "schlecht", "neutral"], BucketReasoning]
    overall_assessment: str
    reasoning: str
    confidence: float  # 0-1
```

### 3.2 Rating

**Menschliche Eingabe:** 1-5 Sterne pro Feature
**LLM-Schema:**
```python
class RatingEvaluationResult(BaseModel):
    ratings: List[FeatureRating]  # feature_id, rating, reasoning
    average_rating: float
    thread_summary: str
    reasoning: str
    confidence: float
```

### 3.3 Authenticity (Fake/Echt)

**Menschliche Eingabe:** real/fake + Confidence + Notes
**LLM-Schema:**
```python
class AuthenticityEvaluationResult(BaseModel):
    vote: Literal["real", "fake"]
    confidence_score: int  # 1-5
    indicators: List[AuthenticityIndicator]
    linguistic_analysis: str
    behavioral_analysis: str
    reasoning: str
    confidence: float
```

### 3.4 Mail Rating

**Menschliche Eingabe:** 1-5 Gesamtbewertung
**LLM-Schema:**
```python
class MailRatingEvaluationResult(BaseModel):
    overall_rating: int  # 1-5
    criteria: List[QualityCriterion]  # name, score, reasoning
    strengths: List[str]
    areas_for_improvement: List[str]
    summary: str
    reasoning: str
    confidence: float
```

### 3.5 Comparison

**Menschliche Eingabe:** A/B/Tie Auswahl
**LLM-Schema:**
```python
class ComparisonEvaluationResult(BaseModel):
    winner: Literal["A", "B", "TIE"]
    confidence_score: int  # 1-5
    reasoning: str
    confidence: float
```

### 3.6 Text Classification

**Menschliche Eingabe:** Label-Auswahl
**LLM-Schema:**
```python
class ClassificationEvaluationResult(BaseModel):
    label: str
    confidence_score: int  # 1-5
    alternative_labels: List[Dict]
    key_phrases: List[str]
    reasoning: str
    confidence: float
```

---

## 4. Socket.IO Events

### 4.1 Client → Server

```javascript
// Szenario subscriben
socket.emit('scenario:subscribe', { scenario_id: 123 })
socket.emit('scenario:unsubscribe', { scenario_id: 123 })
```

### 4.2 Server → Client

```javascript
// LLM-Evaluation Events
'scenario:llm_started'     // { scenario_id, model_id, thread_id, timestamp }
'scenario:llm_completed'   // { scenario_id, model_id, thread_id, result_summary, timestamp }
'scenario:llm_progress'    // { scenario_id, model_id, completed, total, current_thread, avg_time_ms }
'scenario:llm_error'       // { scenario_id, model_id, thread_id, error, timestamp }

// Allgemeine Events
'scenario:stats_updated'   // { scenario_id, stats }
'scenario:human_completed' // { scenario_id, user_id, thread_id, timestamp }
```

---

## 5. Agreement-Metriken mit Erklärungen

### 5.1 Metriken-Definitionen

```javascript
const METRICS = {
  percent_agreement: {
    name: "Prozentuale Übereinstimmung",
    formula: "Übereinstimmungen / Gesamt × 100",
    tooltip: "Anteil der Fälle, in denen alle Bewerter übereinstimmen. Einfach zu verstehen, aber ignoriert Zufallsübereinstimmung.",
    range: "0-100%",
    interpretation: {
      excellent: ">90%",
      good: "75-90%",
      moderate: "50-75%",
      poor: "<50%"
    }
  },
  cohens_kappa: {
    name: "Cohen's Kappa (κ)",
    formula: "κ = (p_o - p_e) / (1 - p_e)",
    tooltip: "Misst Übereinstimmung zwischen zwei Bewertern, bereinigt um Zufallsübereinstimmung. Werte über 0.6 gelten als substantiell.",
    range: "-1 bis 1",
    interpretation: {
      excellent: ">0.8",
      good: "0.6-0.8",
      moderate: "0.4-0.6",
      poor: "<0.4"
    }
  },
  fleiss_kappa: {
    name: "Fleiss' Kappa",
    formula: "Erweiterung von Cohen's Kappa für n Bewerter",
    tooltip: "Für mehr als zwei Bewerter. Misst, wie konsistent alle Bewerter kategorische Urteile fällen.",
    range: "-1 bis 1",
    interpretation: {
      excellent: ">0.8",
      good: "0.6-0.8",
      moderate: "0.4-0.6",
      poor: "<0.4"
    }
  },
  krippendorff_alpha: {
    name: "Krippendorff's Alpha (α)",
    formula: "α = 1 - D_o / D_e (beobachtete/erwartete Disagreement)",
    tooltip: "Universelle Metrik für alle Datentypen (nominal, ordinal, interval, ratio). Robust bei fehlenden Daten. Standard in der Inhaltsanalyse.",
    range: "0 bis 1",
    interpretation: {
      excellent: ">0.8",
      good: "0.67-0.8",
      tentative: "0.67-0.8 (tentative conclusions)",
      poor: "<0.67"
    }
  },
  kendall_tau: {
    name: "Kendall's Tau (τ)",
    formula: "τ = (C - D) / √((C+D+T_x)(C+D+T_y))",
    tooltip: "Misst Übereinstimmung bei Rankings. Zählt konkordante vs. diskordante Paare. Ideal für Ranking-Szenarien.",
    range: "-1 bis 1",
    interpretation: {
      strong: ">0.7",
      moderate: "0.4-0.7",
      weak: "<0.4"
    }
  },
  spearman_rho: {
    name: "Spearman's Rho (ρ)",
    formula: "ρ = 1 - (6 × Σd²) / (n(n²-1))",
    tooltip: "Rang-Korrelationskoeffizient. Misst, wie stark zwei Rankings korrelieren. Gut für ordinale Daten.",
    range: "-1 bis 1",
    interpretation: {
      strong: ">0.7",
      moderate: "0.4-0.7",
      weak: "<0.4"
    }
  }
}
```

---

## 6. Implementierungs-Reihenfolge

### Phase 1: Backend-Grundlagen (Prio: HOCH)
1. DB-Migrationen (neue Tabellen)
2. Pydantic-Schemas für alle Szenario-Typen
3. PromptTemplate Service
4. Token-Tracking Service
5. Erweiterung LLMAITaskRunner mit Structured Output

### Phase 2: LLM-Integration (Prio: HOCH)
1. Constrained Decoding Service
2. Auto-Start bei Szenario-Aktivierung
3. Socket.IO Events für Live-Updates
4. Fehlerbehandlung & Retry-Logik

### Phase 3: Frontend-Grundstruktur (Prio: HOCH)
1. Router-Setup mit neuen Routes
2. EvaluationAssistant.vue (Container)
3. MyScenariosDashboard.vue
4. ScenarioWizard.vue (angepasst)

### Phase 4: Transparenz & Monitoring (Prio: MITTEL)
1. ScenarioMonitor.vue mit Live-Updates
2. ResponseExplorer.vue
3. ResponseCard.vue + Display-Komponenten
4. AgreementMetrics.vue

### Phase 5: Export & Polish (Prio: MITTEL)
1. ResultsExport.vue
2. Export-Services (CSV, JSON, LaTeX, Excel, PDF)
3. Token-Budget UI im Admin
4. Prompt-Template UI im Admin

### Phase 6: Tests & Demo (Prio: HOCH)
1. Unit-Tests Backend
2. Integration-Tests LLM-Evaluation
3. E2E-Tests Frontend
4. Demo-Daten & Walkthrough

---

## 7. Test-Strategie

### 7.1 LLM-Evaluation Tests

```python
# Tests für jeden Szenario-Typ
def test_ranking_llm_evaluation():
    """Test dass Ranking LLM-Evaluation funktioniert."""
    scenario = create_test_scenario(function_type="ranking")
    add_llm_evaluator(scenario, "gpt-4o-mini")  # Günstig für Tests

    # Trigger evaluation
    LLMAITaskRunner.run_for_scenario(scenario.id)

    # Verify results
    results = LLMTaskResult.query.filter_by(scenario_id=scenario.id).all()
    assert len(results) > 0
    for r in results:
        assert r.payload_json is not None
        assert "buckets" in r.payload_json
        assert r.reasoning_json is not None

def test_rating_llm_evaluation():
    """Test dass Rating LLM-Evaluation funktioniert."""
    # Similar pattern...

def test_authenticity_llm_evaluation():
    """Test dass Authenticity LLM-Evaluation funktioniert."""
    # Similar pattern...
```

### 7.2 Agreement-Metriken Tests

```python
def test_krippendorff_alpha():
    """Test Krippendorff's Alpha Berechnung."""
    # Known test case from literature
    ratings = [
        [1, 2, 3, 3, 2, 1],  # Rater 1
        [1, 2, 3, 3, 2, 2],  # Rater 2
        [None, 3, 3, 3, 2, 1],  # Rater 3 (mit missing)
    ]
    alpha = calculate_krippendorff_alpha(ratings)
    assert 0.6 < alpha < 0.8  # Expected range
```

---

## 8. Risiken & Mitigations

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| LLM-Kosten explodieren | Mittel | Hoch | Token-Budget mit Hard-Limit |
| LLM liefert ungültiges JSON | Hoch | Mittel | 3 Retries + Schema-Validierung |
| Rate-Limits erreicht | Mittel | Mittel | Exponential Backoff + Queue |
| Socket.IO Verbindungsabbruch | Niedrig | Niedrig | Auto-Reconnect + State-Sync |
| Deadline nicht erreichbar | Mittel | Hoch | MVP first, Nice-to-have später |

---

## 9. MVP Definition (für IJCAI Deadline)

### Must-Have (MVP)
- [ ] Szenario-Erstellung mit LLM-Evaluatoren
- [ ] Auto-Start LLM-Evaluation bei Szenario-Aktivierung
- [ ] Live-Monitoring (Fortschritt)
- [ ] Transparenz-Explorer (Responses ansehen)
- [ ] Mind. 3 Agreement-Metriken
- [ ] CSV + JSON Export
- [ ] Funktioniert für: Ranking, Rating, Authenticity

### Nice-to-Have
- [ ] Mail Rating, Comparison, Classification
- [ ] PDF-Report Export
- [ ] LaTeX-Export
- [ ] Token-Budget UI
- [ ] Prompt-Template Editor UI

---

**Freigegeben am:** 14. Januar 2026
**Implementierung startet:** Sofort
