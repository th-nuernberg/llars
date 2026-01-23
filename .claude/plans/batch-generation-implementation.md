# Implementierungsplan: Batch Generation Module

**Ziel:** Brücke zwischen Prompt Engineering (B) und Evaluation (C) mit Daten (A)

**Stand:** 22. Januar 2026

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         BATCH GENERATION MODULE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  INPUTS:                                       OUTPUTS:                          │
│  ┌────────────────────────────┐               ┌────────────────────────────┐    │
│  │ • EvaluationItems (A)      │               │ • GeneratedOutputs         │    │
│  │ • PromptTemplates (B)      │  ──────────►  │   - source_item_id         │    │
│  │ • LLM Models               │               │   - prompt_template_id     │    │
│  │ • GenerationConfig         │               │   - llm_model_id           │    │
│  └────────────────────────────┘               │   - generated_content      │    │
│                                               │   - token_usage            │    │
│                                               └─────────────┬──────────────┘    │
│                                                             │                   │
│                                                             ▼                   │
│                                               ┌────────────────────────────┐    │
│                                               │ • Export (CSV/JSON)        │    │
│                                               │ • → Evaluation Scenario    │    │
│                                               └────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Datenbank-Modelle

### 1.1 GenerationJob Model

**Datei:** `app/db/models/generation_job.py`

```python
class GenerationJob(db.Model):
    """Ein Batch-Generation-Auftrag."""
    __tablename__ = 'generation_jobs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    # Status
    status = db.Column(db.Enum(
        'CREATED', 'QUEUED', 'RUNNING', 'PAUSED',
        'COMPLETED', 'FAILED', 'CANCELLED'
    ), default='CREATED')

    # Konfiguration
    config_json = db.Column(db.JSON)  # Siehe 1.3

    # Quellen
    source_scenario_id = db.Column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    # ODER direkte Item-IDs in config_json

    # Fortschritt
    total_items = db.Column(db.Integer, default=0)
    completed_items = db.Column(db.Integer, default=0)
    failed_items = db.Column(db.Integer, default=0)

    # Metadaten
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Beziehungen
    outputs = db.relationship('GeneratedOutput', backref='job', lazy='dynamic')
    target_scenario = db.relationship('RatingScenario', foreign_keys=[...])
```

### 1.2 GeneratedOutput Model

**Datei:** `app/db/models/generated_output.py`

```python
class GeneratedOutput(db.Model):
    """Ein einzelner generierter Output."""
    __tablename__ = 'generated_outputs'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('generation_jobs.id'), nullable=False)

    # Tracking: Was wurde verwendet?
    source_item_id = db.Column(db.Integer, db.ForeignKey('evaluation_items.item_id'))
    prompt_template_id = db.Column(db.Integer, db.ForeignKey('prompt_templates.id'))
    llm_model_id = db.Column(db.Integer, db.ForeignKey('llm_models.id'))

    # Prompt-Variante (falls mehrere Prompts getestet werden)
    prompt_variant_name = db.Column(db.String(100))

    # Der generierte Inhalt
    generated_content = db.Column(db.Text, nullable=False)

    # Rendered Prompts (für Debugging/Nachvollziehbarkeit)
    rendered_system_prompt = db.Column(db.Text)
    rendered_user_prompt = db.Column(db.Text)

    # Token-Tracking
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    total_cost = db.Column(db.Float)

    # Status
    status = db.Column(db.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'), default='PENDING')
    error_message = db.Column(db.Text)

    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    processing_time_ms = db.Column(db.Integer)

    # Beziehungen
    source_item = db.relationship('EvaluationItem')
    prompt_template = db.relationship('PromptTemplate')
    llm_model = db.relationship('LLMModel')
```

### 1.3 config_json Schema

```json
{
  "mode": "matrix",  // "matrix" | "sequential"

  "sources": {
    "type": "scenario",  // "scenario" | "items" | "import"
    "scenario_id": 123,
    // ODER
    "item_ids": [1, 2, 3],
    // ODER
    "import_session_id": "uuid"
  },

  "prompts": [
    {
      "template_id": 1,
      "variant_name": "Standard",
      "variables": {}  // Überschreibungen
    },
    {
      "template_id": 2,
      "variant_name": "Kurz",
      "variables": {"max_length": "50 Wörter"}
    }
  ],

  "llm_models": [
    {"model_id": "gpt-4"},
    {"model_id": "claude-3-sonnet"}
  ],

  "generation_params": {
    "temperature": 0.7,
    "max_tokens": 1000
  },

  "output": {
    "create_scenario": true,
    "scenario_name": "Zusammenfassungs-Vergleich",
    "evaluation_type": "ranking",  // "ranking" | "rating" | "comparison"
    "export_format": null  // "csv" | "json" | null
  }
}
```

### 1.4 Alembic Migration

**Datei:** `app/db/migrations/versions/xxx_add_generation_tables.py`

- [ ] `generation_jobs` Tabelle
- [ ] `generated_outputs` Tabelle
- [ ] Indizes für häufige Queries

---

## Phase 2: Backend Services

### 2.1 BatchGenerationService

**Datei:** `app/services/generation/batch_generation_service.py`

```python
class BatchGenerationService:
    """Orchestriert Batch-Generierungen."""

    def create_job(self, name: str, config: dict, created_by: str) -> GenerationJob:
        """Erstellt einen neuen Generation-Job."""
        pass

    def start_job(self, job_id: int) -> None:
        """Startet die Verarbeitung eines Jobs."""
        pass

    def pause_job(self, job_id: int) -> None:
        """Pausiert einen laufenden Job."""
        pass

    def cancel_job(self, job_id: int) -> None:
        """Bricht einen Job ab."""
        pass

    def get_job_status(self, job_id: int) -> dict:
        """Gibt den aktuellen Status zurück."""
        pass

    def get_job_outputs(self, job_id: int, page: int, per_page: int) -> list:
        """Gibt generierte Outputs paginiert zurück."""
        pass

    def _build_generation_matrix(self, config: dict) -> list[tuple]:
        """Erstellt alle Item × Prompt × LLM Kombinationen."""
        pass

    def _process_single_item(self, item, prompt, llm_model, params) -> GeneratedOutput:
        """Generiert einen einzelnen Output."""
        pass
```

### 2.2 GenerationWorker

**Datei:** `app/services/generation/generation_worker.py`

```python
class GenerationWorker:
    """Worker für asynchrone Generation."""

    def __init__(self, job_id: int):
        self.job_id = job_id
        self.should_stop = False

    async def run(self):
        """Hauptschleife für die Generierung."""
        pass

    def _emit_progress(self, completed: int, total: int):
        """Socket.IO Event für Fortschritt."""
        pass

    def _handle_error(self, output: GeneratedOutput, error: Exception):
        """Fehlerbehandlung für einzelne Items."""
        pass
```

### 2.3 OutputExportService

**Datei:** `app/services/generation/output_export_service.py`

```python
class OutputExportService:
    """Export von generierten Outputs."""

    def export_to_csv(self, job_id: int) -> BytesIO:
        """Exportiert Outputs als CSV."""
        pass

    def export_to_json(self, job_id: int) -> dict:
        """Exportiert Outputs als JSON."""
        pass

    def create_evaluation_scenario(self, job_id: int, config: dict) -> RatingScenario:
        """Erstellt ein Evaluation-Szenario aus den Outputs."""
        pass
```

---

## Phase 3: API Routes

### 3.1 Generation Routes

**Datei:** `app/routes/generation/generation_routes.py`

```
POST   /api/generation/jobs                    # Job erstellen
GET    /api/generation/jobs                    # Alle Jobs listen
GET    /api/generation/jobs/<id>               # Job-Details
POST   /api/generation/jobs/<id>/start         # Job starten
POST   /api/generation/jobs/<id>/pause         # Job pausieren
POST   /api/generation/jobs/<id>/cancel        # Job abbrechen
DELETE /api/generation/jobs/<id>               # Job löschen

GET    /api/generation/jobs/<id>/outputs       # Outputs abrufen (paginiert)
GET    /api/generation/jobs/<id>/outputs/<oid> # Einzelner Output

POST   /api/generation/jobs/<id>/export/csv    # CSV Export
POST   /api/generation/jobs/<id>/export/json   # JSON Export
POST   /api/generation/jobs/<id>/to-scenario   # Als Evaluation-Szenario

GET    /api/generation/preview                 # Matrix-Vorschau (ohne Ausführung)
```

### 3.2 Socket.IO Events

```python
# Server → Client
'generation:job:started'      # Job gestartet
'generation:job:progress'     # Fortschritt {completed, total, current_item}
'generation:job:completed'    # Job fertig
'generation:job:failed'       # Job fehlgeschlagen
'generation:item:completed'   # Einzelnes Item fertig
'generation:item:failed'      # Einzelnes Item fehlgeschlagen
```

---

## Phase 4: Frontend

### 4.1 Service

**Datei:** `llars-frontend/src/services/generationApi.js`

```javascript
export const generationApi = {
  // Jobs
  createJob(data) { return axios.post('/api/generation/jobs', data) },
  getJobs() { return axios.get('/api/generation/jobs') },
  getJob(id) { return axios.get(`/api/generation/jobs/${id}`) },
  startJob(id) { return axios.post(`/api/generation/jobs/${id}/start`) },
  pauseJob(id) { return axios.post(`/api/generation/jobs/${id}/pause`) },
  cancelJob(id) { return axios.post(`/api/generation/jobs/${id}/cancel`) },
  deleteJob(id) { return axios.delete(`/api/generation/jobs/${id}`) },

  // Outputs
  getOutputs(jobId, params) { return axios.get(`/api/generation/jobs/${jobId}/outputs`, { params }) },

  // Export
  exportCsv(id) { return axios.post(`/api/generation/jobs/${id}/export/csv`, {}, { responseType: 'blob' }) },
  exportJson(id) { return axios.post(`/api/generation/jobs/${id}/export/json`) },
  createScenario(id, config) { return axios.post(`/api/generation/jobs/${id}/to-scenario`, config) },

  // Preview
  previewMatrix(config) { return axios.get('/api/generation/preview', { params: config }) }
}
```

### 4.2 Composable

**Datei:** `llars-frontend/src/composables/useGeneration.js`

```javascript
export function useGeneration() {
  const jobs = ref([])
  const currentJob = ref(null)
  const outputs = ref([])
  const progress = ref({ completed: 0, total: 0 })

  // Socket.IO Listener für Live-Updates
  function setupSocketListeners() { ... }

  // Job-Management
  async function loadJobs() { ... }
  async function loadJob(id) { ... }
  async function createJob(config) { ... }
  async function startJob(id) { ... }

  // Export
  async function downloadCsv(id) { ... }
  async function createEvaluationScenario(id, config) { ... }

  return { jobs, currentJob, outputs, progress, ... }
}
```

### 4.3 Komponenten

**Struktur:**
```
llars-frontend/src/components/Generation/
├── GenerationHub.vue              # Übersicht aller Jobs
├── GenerationWizard.vue           # Neuen Job erstellen (Wizard)
├── GenerationJobDetail.vue        # Job-Details & Outputs
├── GenerationProgress.vue         # Live-Fortschrittsanzeige
├── GenerationOutputTable.vue      # Output-Liste mit Vorschau
├── GenerationExportDialog.vue     # Export-Optionen
└── GenerationToScenarioDialog.vue # In Evaluation überführen
```

#### 4.3.1 GenerationWizard.vue (Hauptkomponente)

**Wizard-Schritte:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  SCHRITT 1: Datenquelle                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Woher kommen die Daten?                                           │
│                                                                     │
│  ○ Bestehendes Szenario                                            │
│    [Dropdown: Szenario auswählen]                                  │
│                                                                     │
│  ○ Items direkt auswählen                                          │
│    [Multi-Select mit Suche]                                        │
│                                                                     │
│  ○ Neue Daten importieren                                          │
│    [→ Import-Wizard öffnen]                                        │
│                                                                     │
│  Ausgewählt: 50 Items                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SCHRITT 2: Prompt(s) auswählen                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Welche Prompts sollen verwendet werden?                           │
│                                                                     │
│  ☑ Zusammenfassung Standard (v1.2)                                 │
│  ☑ Zusammenfassung Kurz (v1.0)                                     │
│  ☐ Sentiment-Analyse (v2.1)                                        │
│                                                                     │
│  [+ Neuen Prompt erstellen]                                        │
│                                                                     │
│  Variablen-Überschreibungen:                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Prompt: Zusammenfassung Kurz                                │   │
│  │ Variable: max_length = [50 Wörter        ]                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SCHRITT 3: LLM(s) auswählen                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Welche Modelle sollen verwendet werden?                           │
│                                                                     │
│  ☑ GPT-4 Turbo          $0.03/1k input                             │
│  ☑ Claude 3 Sonnet      $0.003/1k input                            │
│  ☐ Llama 3.1 70B        $0.001/1k input                            │
│                                                                     │
│  Generierungs-Parameter:                                           │
│  Temperature: [0.7    ]                                            │
│  Max Tokens:  [1000   ]                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SCHRITT 4: Matrix-Vorschau                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  50 Items × 2 Prompts × 2 LLMs = 200 Generierungen          │   │
│  │                                                              │   │
│  │  Geschätzte Kosten: ~$4.50                                   │   │
│  │  Geschätzte Dauer: ~15 Minuten                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Matrix:                                                           │
│  ┌────────────────┬────────────────┬────────────────┐             │
│  │                │ GPT-4 Turbo    │ Claude Sonnet  │             │
│  ├────────────────┼────────────────┼────────────────┤             │
│  │ Standard       │ 50 Outputs     │ 50 Outputs     │             │
│  │ Kurz           │ 50 Outputs     │ 50 Outputs     │             │
│  └────────────────┴────────────────┴────────────────┘             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SCHRITT 5: Output-Konfiguration                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Was soll mit den Outputs passieren?                               │
│                                                                     │
│  ☑ Evaluation-Szenario erstellen                                   │
│    Name: [Zusammenfassungs-Vergleich Jan 2026    ]                 │
│    Typ:  [● Ranking  ○ Rating  ○ Comparison]                       │
│                                                                     │
│  ☑ Export ermöglichen (CSV/JSON)                                   │
│                                                                     │
│  Job-Name: [Batch Gen - 2026-01-22              ]                  │
│                                                                     │
│                              [Abbrechen]  [Job erstellen & starten] │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 Router

**Datei:** `llars-frontend/src/router.js` (erweitern)

```javascript
{
  path: '/generation',
  name: 'GenerationHub',
  component: () => import('@/components/Generation/GenerationHub.vue'),
  meta: { requiresAuth: true, permission: 'feature:generation:view' }
},
{
  path: '/generation/new',
  name: 'GenerationWizard',
  component: () => import('@/components/Generation/GenerationWizard.vue'),
  meta: { requiresAuth: true, permission: 'feature:generation:create' }
},
{
  path: '/generation/:id',
  name: 'GenerationJobDetail',
  component: () => import('@/components/Generation/GenerationJobDetail.vue'),
  meta: { requiresAuth: true, permission: 'feature:generation:view' }
}
```

### 4.5 Navigation

- Neuer Menüpunkt "Generation" zwischen "Prompt Engineering" und "Evaluation"
- Icon: `mdi-cog-transfer` oder `mdi-play-box-multiple`

---

## Phase 5: Integration

### 5.1 Prompt Engineering → Generation

- Button "In Batch Generation verwenden" bei Prompt-Templates
- Öffnet Wizard mit vorausgewähltem Prompt

### 5.2 Data Import → Generation

- Option im Import-Wizard: "Direkt zur Generation"
- Übergibt importierte Items an Generation-Wizard

### 5.3 Generation → Evaluation

- "Als Szenario erstellen" bei abgeschlossenen Jobs
- Automatische Erstellung eines Evaluation-Szenarios
- Mapping: GeneratedOutput → EvaluationItem

### 5.4 Evaluation Scenario Wizard → Generation

- Option im Scenario Wizard: "Items erst generieren lassen"
- Verzweigt zum Generation-Wizard, kehrt zurück

---

## Phase 6: Permissions

### 6.1 Neue Permissions

```python
# In app/services/auth/permission_service.py erweitern

GENERATION_PERMISSIONS = {
    'feature:generation:view': 'Generation-Jobs ansehen',
    'feature:generation:create': 'Generation-Jobs erstellen',
    'feature:generation:manage': 'Generation-Jobs verwalten (pausieren, abbrechen)',
    'feature:generation:export': 'Outputs exportieren',
    'feature:generation:to_scenario': 'Outputs in Evaluation überführen',
}
```

### 6.2 Rollen-Mapping

| Rolle | Permissions |
|-------|-------------|
| admin | alle |
| researcher | view, create, manage, export, to_scenario |
| evaluator | view |
| chatbot_manager | view, create |

---

## Phase 7: Tests

### 7.1 Backend Tests

**Datei:** `tests/unit/services/generation/test_batch_generation_service.py`

- [ ] `test_create_job_with_scenario_source`
- [ ] `test_create_job_with_item_ids`
- [ ] `test_build_generation_matrix_single_prompt_single_llm`
- [ ] `test_build_generation_matrix_multi_prompt_multi_llm`
- [ ] `test_start_job_updates_status`
- [ ] `test_pause_job`
- [ ] `test_cancel_job`
- [ ] `test_process_single_item_success`
- [ ] `test_process_single_item_failure`
- [ ] `test_export_csv`
- [ ] `test_export_json`
- [ ] `test_create_evaluation_scenario`

### 7.2 Frontend Tests

**Datei:** `llars-frontend/src/composables/__tests__/useGeneration.spec.js`

- [ ] `GEN_001: createJob sends correct payload`
- [ ] `GEN_002: startJob updates status`
- [ ] `GEN_003: socket progress updates state`
- [ ] `GEN_004: downloadCsv triggers download`

---

## Implementierungs-Reihenfolge

### Sprint 1: Foundation (Backend)
1. [ ] DB-Modelle erstellen (`generation_job.py`, `generated_output.py`)
2. [ ] Alembic Migration schreiben und ausführen
3. [ ] `BatchGenerationService` Grundstruktur
4. [ ] API Routes (CRUD für Jobs)
5. [ ] Unit Tests für Service

### Sprint 2: Generation Engine
6. [ ] `GenerationWorker` mit LLM-Integration
7. [ ] Socket.IO Events für Progress
8. [ ] Error Handling & Retry-Logik
9. [ ] `OutputExportService` (CSV, JSON)
10. [ ] Integration Tests

### Sprint 3: Frontend Wizard
11. [ ] `generationApi.js` Service
12. [ ] `useGeneration.js` Composable
13. [ ] `GenerationWizard.vue` (5 Schritte)
14. [ ] `GenerationHub.vue` (Job-Liste)
15. [ ] `GenerationJobDetail.vue`

### Sprint 4: Integration & Polish
16. [ ] `GenerationProgress.vue` mit Live-Updates
17. [ ] `GenerationToScenarioDialog.vue`
18. [ ] Navigation & Permissions
19. [ ] Integration mit Prompt Engineering
20. [ ] Integration mit Evaluation

### Sprint 5: Testing & Docs
21. [ ] E2E Tests
22. [ ] Dokumentation aktualisieren
23. [ ] CLAUDE.md erweitern

---

## Offene Fragen

1. **Rate Limiting:** Wie viele parallele LLM-Requests?
   - Vorschlag: Konfigurierbar, Default 5 parallel

2. **Kosten-Limit:** Soll es ein Budget-Limit pro Job geben?
   - Vorschlag: Optional, Warning bei >$10

3. **Output-Speicherung:** Wie lange werden Outputs aufbewahrt?
   - Vorschlag: Unbegrenzt, manuelles Löschen

4. **Retry-Strategie:** Wie oft bei Fehlern wiederholen?
   - Vorschlag: 3 Versuche mit exponential backoff

---

## Abhängigkeiten

- `PromptTemplateService` (existiert ✅)
- `LLMStructuredEvaluator` / `LLMClientFactory` (existiert ✅)
- `EvaluationItem` Model (existiert ✅)
- `RatingScenario` Model (existiert ✅)
- Socket.IO Integration (existiert ✅)
- Token Tracking Service (existiert ✅)
