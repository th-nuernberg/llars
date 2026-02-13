# LLARS - LLM Assisted Research System

**Version:** 3.0 | **Stand:** 31. Januar 2026

## Projekt-Übersicht

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit LLMs.

**Features:** Rating/Ranking-System | LLM Evaluator | RAG-Pipeline (ChromaDB) | Multi-User Collaboration (YJS) | Authentik Auth | RBAC Permissions | Offline Anonymize Tool | Production-Ready (Gunicorn + gevent)

**Quick Reference:** Dieses Dokument enthält alle wichtigen Informationen für die Entwicklung.

---

## Quick Start

```bash
cp .env.template.development .env
./start_llars.sh

# Komplett-Neustart (LÖSCHT ALLE DATEN!)
REMOVE_LLARS_VOLUMES=True ./start_llars.sh
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik | http://localhost:55095 |

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher (kann Szenarien erstellen) |
| evaluator | admin123 | evaluator (nimmt an Evaluationen teil) |
| chatbot_manager | admin123 | chatbot_manager |

---

## Architektur

```
nginx (:80) → Reverse Proxy
├── / → Vue Frontend (:5173)
├── /api/, /auth/ → Flask Backend (:8081)
├── /analytics/ → Matomo Analytics (:80)
└── /collab/ → YJS WebSocket (:8082)

Databases: MariaDB (:3306 - LLARS), PostgreSQL (:5432 - Authentik)
```

**Backend:** Flask 3.0 + MariaDB 11.2 + ChromaDB
**Frontend:** Vue 3.4 + Vuetify 3.5 + Vite 5.1 + Socket.IO

---

## Production Server (Gunicorn + Gevent)

LLARS verwendet in Production **Gunicorn mit gevent-websocket** für echte WebSocket-Unterstützung.

### Development vs Production

| Modus | `PROJECT_STATE` | Server | WebSocket | Auto-Reload |
|-------|-----------------|--------|-----------|-------------|
| Development | `development` | Flask Dev Server | Polling | ✓ |
| Production | `production` | Gunicorn + gevent | Echte WS | ✗ |

### Wichtige Dateien

```
docker/flask/start_flask.sh     # Dev/Prod Mode Switch
docker/flask/gunicorn.conf.py   # Gunicorn Konfiguration
app/wsgi_gevent.py              # WSGI Entry Point (gevent)
app/wsgi.py                     # WSGI Entry Point (eventlet, nicht empfohlen)
scripts/load_test.py            # Load-Test-Skript
```

### Performance-Benchmarks (Production)

| Metrik | Wert |
|--------|------|
| HTTP Response Time (avg) | 8-80 ms |
| HTTP Throughput | ~100 req/s |
| WebSocket Success Rate | 100% |
| Idle CPU (Flask) | 0.04% |
| Idle RAM (Flask) | ~380 MB |

### Load Testing

```bash
# Quick Test
docker exec llars_flask_service python3 /app/scripts/load_test.py --quick

# Heavy Load
python scripts/load_test.py --users 100 --requests 20 --ws-connections 50
```

### Eventlet vs Gevent

**Eventlet:** DNS-Timeout-Probleme in Docker (`Lookup timed out`)
**Gevent:** Empfohlen - Bessere Docker DNS-Kompatibilität

---

## LLM Modelle & Sichtbarkeit

- Verfügbare Modelle für Nutzer: `GET /api/llm/models/available` (Permission: `feature:llm:view`)
- Admin-Übersicht/Allowlist: `GET /api/llm/models/access/overview`, `PUT /api/llm/models/<id>/access`
- Standard: Keine Zuweisung = öffentlich; sobald Nutzer/Rollen gesetzt sind, gilt die Allowlist.
- DB-Tabelle: `llm_model_permissions`

---

## LLM Provider Registry

- Admin Endpoints: `GET/POST /api/llm/providers`, `PUT/DELETE /api/llm/providers/<id>`, `POST /api/llm/providers/<id>/test`, `POST /api/llm/providers/<id>/sync-models`
- Routing: `llm_models.provider_id` → Provider-Config; Fallback = Default-Provider oder `LITELLM_*`/`OPENAI_API_KEY`
- DB-Tabelle: `llm_providers`

---

## Server-Operationen

### Neustart / Bereinigung

```bash
docker compose down
docker system prune -af --volumes
./start_llars.sh
```

### Datenbank

```bash
# MariaDB Zugriff
docker exec -it llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars

# SQL ausführen
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e "SHOW TABLES;"

# Backup erstellen
docker exec llars_db_service mysqldump -u dev_user -pdev_password_change_me database_llars > backup.sql

# Backup wiederherstellen
cat backup.sql | docker exec -i llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars
```

### Logs

```bash
docker logs -f llars_flask_service          # Backend
docker compose logs -f                       # Alle
docker compose logs -f 2>&1 | grep -i error  # Nur Fehler
```

---

## GitLab CI/CD

```
GitLab: git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars
Server: 141.75.150.128 (internes Netz)
Runner: Shell-Executor direkt auf Server
```

| Stage | Jobs |
|-------|------|
| lint | `lint:backend`, `lint:frontend` |
| test | `test:unit:backend`, `test:unit:frontend`, `test:integration`, `test:e2e` |
| security | `security:routes`, `security:scan` |
| build | `build:docker` (nur main) |
| deploy | `deploy:staging`, `deploy:production` |
| smoke | `smoke:production` |
| rollback | `rollback:production` (manual) |

```
Push to develop → deploy:staging (automatisch)
Push to main    → deploy:production → smoke:production (Auto-Rollback bei Smoke-Fail)
```

**Test-Requirements:** `app/requirements-test.txt` (ohne torch, transformers, flair - ~3GB gespart)

### GitLab API Zugriff

**Skill verfuegbar:** `.claude/skills/ci-cd-debugging/` - Automatisches CI/CD Debugging

Die `.env` enthält GitLab API Credentials für Pipeline-Monitoring:

```bash
# Pipelines abrufen
source .env
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines?per_page=5"

# Jobs einer Pipeline abrufen
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines/{PIPELINE_ID}/jobs"

# Job-Log abrufen (letzte 50 Zeilen)
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/jobs/{JOB_ID}/trace" | tail -50

# CI-Konfiguration validieren
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/ci/lint?ref=main"

# Pipeline manuell triggern
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipeline?ref=main"

# Fehlgeschlagene Pipeline neu starten
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines/{PIPELINE_ID}/retry"
```

### Pipeline Monitoring Script

```bash
# 6h Monitoring, alle 10 Minuten (default)
./scripts/ci/monitor_pipelines.sh

# Custom Laufzeit/Intervall
DURATION_SECONDS=21600 INTERVAL_SECONDS=600 BRANCH=main ./scripts/ci/monitor_pipelines.sh
```

**Umgebungsvariablen (.env):**
- `GITLAB_TOKEN` - API Token mit `read_api` Scope
- `GITLAB_PROJECT_ID` - Projekt-ID (7123)
- `GITLAB_PROJECT_PATH` - Projekt-Pfad

### CI/CD Troubleshooting

| Problem | Loesung |
|---------|---------|
| Pipeline 0 Jobs | Auto-cancel aktiv? YAML validieren |
| E2E Tests scheitern | App auf Server laufen? PLAYWRIGHT_BASE_URL korrekt? |
| Job haengt bei pending | Shell-Runner online? Tags korrekt? |
| Lint fehlschlaegt | flake8 lokal ausfuehren, .flake8 Config pruefen |

---

## Tests - PFLICHT!

Jede neue Komponente/Service MUSS Tests haben.

```bash
# Backend
pytest tests/
pytest --cov=app tests/

# Frontend
cd llars-frontend
npm run test:run
npm run test:coverage
```

### Test-ID Konventionen

| Präfix | Bereich |
|--------|---------|
| `AUTH_` | useAuth |
| `PERM_` | usePermissions |
| `COMP_BTN_` | LBtn |

### Frontend Test-Pattern

```javascript
import { describe, it, expect, vi } from 'vitest'

describe('useExample', () => {
  beforeEach(() => vi.resetModules())

  it('EXAMPLE_001: does something', () => {
    expect(result).toBe('expected')
  })
})
```

### Mocking

```javascript
// Axios
vi.mock('axios', () => ({ default: { get: vi.fn(), post: vi.fn() } }))

// localStorage
vi.stubGlobal('localStorage', { getItem: vi.fn(), setItem: vi.fn() })

// Vue Router
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }))
```

---

## CI/CD Quality Policy

**KRITISCH: Robuste Pipeline ohne Workarounds!**

### Grundprinzipien

1. **Keine `|| true` bei Tests** - Tests MÜSSEN fehlschlagen wenn sie fehlschlagen
2. **Keine `allow_failure: true`** bei kritischen Jobs - Nur bei optionalen Jobs erlaubt
3. **Fix Code oder Test** - Niemals Tests überspringen oder ignorieren
4. **E2E Tests müssen bestehen** - Deployment nur bei grüner Pipeline

### Erlaubte `allow_failure` Jobs

| Job | Grund |
|-----|-------|
| `rollback:production` | Manueller Notfall-Job |
| `smoke:wizard` | Optionaler erweiterter Test |
| `metrics:*` | Reporting, nicht kritisch |

### Verboten

```yaml
# ❌ NIEMALS so:
- pytest tests/ || true
- npm run test:run || true
- npx playwright test || true

# ✅ Korrekt:
- pytest tests/
- npm run test:run
- npx playwright test
```

### E2E Test Best Practices

- **Keine `waitForTimeout()`** - Verwende condition-based waits
- **Web-first assertions** - `toBeVisible()`, `toHaveURL()`, `toHaveText()`
- **`domcontentloaded`** statt `networkidle` - Vermeidet Analytics-Timeouts
- **Consent-Banner früh dismissieren** - Vor Element-Interaktionen

### Bei Test-Fehlern

1. **Analysiere den Fehler** - Lies Logs und Screenshots
2. **Reproduziere lokal** - `npm run e2e:chromium -- --workers=1`
3. **Fix Code ODER Test** - Je nachdem was falsch ist
4. **Verifiziere Pipeline** - Commit, Push, Monitor

---

## Auth & Permissions

### Auth Decorator

```python
@authentik_required
def my_route():
    user = g.authentik_user  # User-OBJEKT (nicht String!)
    user_id = user.id
```

### Permission System

**Sicherheitsmodell:** Deny-by-Default | User überschreibt Rolle | Deny schlägt Grant

| Rolle | Berechtigungen |
|-------|---------------|
| admin | alle |
| researcher | Evaluation + Prompt Engineering + Markdown Collab |
| evaluator | Lesezugriff |
| chatbot_manager | Chatbot + RAG + Prompt Engineering |

**Backend:**
```python
@require_permission('feature:ranking:view')
@handle_api_errors(logger_name='ranking')
def my_route(): ...
```

**Frontend:**
```vue
<v-card v-if="hasPermission('feature:ranking:view')">...</v-card>
```

---

## Error Handling

**ALLE Routes MÜSSEN `@handle_api_errors` nutzen:**

```python
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError

@handle_api_errors(logger_name='module_name')
def get_item(id):
    if not item:
        raise NotFoundError(f'Item {id} not found')  # 404
    # ValidationError → 400, ConflictError → 409
```

---

## RAG-Pipeline

### Embedding Models

```
Priorität | Model                              | Dimensionen
----------|------------------------------------|-----------
1         | llamaindex/vdr-2b-multi-v1 (API)   | 1024
2         | llamaindex/vdr-2b-multi-v1 (Local) | 1024
3         | all-MiniLM-L6-v2 (Local)           | 384
```

**KRITISCH:** Query-Embedding muss zum Document-Embedding passen!

```python
from services.rag.embedding_model_service import get_best_embedding_for_collection
embeddings, model_id, chroma_name, dims = get_best_embedding_for_collection(collection_id)
```

---

## Rating/Ranking System

### Terminologie (Item vs Feature)

| Begriff | Definition | DB-Model | IRR-Rolle |
|---------|-----------|----------|-----------|
| **Item** | Eltern-Entität, gruppiert zusammengehörige Features (z.B. E-Mail-Thread, Quelltext) | `EvaluationItem` | Gruppierung |
| **Feature** | Eine generierte Alternative/Antwort FÜR ein Item (z.B. eine Zusammenfassung) | `Feature` | **Unit of analysis** (Zeile in der Rater-Matrix) |

**Hierarchie:** Item → hat N Features → jedes Feature wird in genau EINEN Bucket einsortiert

**IRR-Berechnung ("Bucket-Krippendorff"):**
- Unit of analysis = Feature (jede Zusammenfassung)
- Jeder Evaluator ordnet jedes Feature einem Bucket zu
- Buckets sind ordinal: gut(3) > mittel(2) > neutral(1) > schlecht(0)
- Ordinales Krippendorff's Alpha (vgl. Steigerwald & Albrecht 2025, Section 3.4)
- Heatmap: Einfache Prozent-Übereinstimmung (gleicher Bucket ja/nein)

```
EvaluationItem (früher EmailThread)
├── Messages[] (Klient ↔ Berater)
└── content (Plain-Text-Inhalt)

Scenario
├── ScenarioUsers[] (OWNER, EVALUATOR oder RATER)
├── ScenarioItems[] (früher ScenarioThreads)
├── config_json (dimensions, labels, scale settings)
└── ItemDimensionRating[] (Multi-dimensionale Bewertungen)
```

| function_type_id | Name | Beschreibung |
|------------------|------|--------------|
| 1 | ranking | Items sortieren oder kategorisieren |
| 2 | rating | Multi-dimensionales Rating (LLM Evaluator Metriken) |
| 3 | mail_rating | E-Mail-Verläufe bewerten (LLARS-spezifisch) |
| 4 | comparison | Items paarweise vergleichen (A vs B) |
| 5 | authenticity | Fake/Echt Bewertung (LLARS-spezifisch) |
| 7 | labeling | Kategorien zuweisen (binär, multi-class) |

### Evaluation Data Schemas (Ground Truth)

**ZENTRALE REFERENZ für alle Evaluationsformate:**

```
Backend (Pydantic):  app/schemas/evaluation_data_schemas.py
Frontend (JS):       llars-frontend/src/schemas/evaluationSchemas.js
Dokumentation:       .claude/plans/evaluation-data-schemas.md
```

**Schema-Struktur:**
```json
{
  "schema_version": "1.0",
  "type": "ranking|rating|mail_rating|comparison|authenticity|labeling",
  "reference": { "type": "text|conversation", "label": "...", "content": "..." },
  "items": [{ "id": "item_1", "label": "...", "source": {...}, "content": "..." }],
  "config": { /* typ-spezifische Konfiguration */ }
}
```

**Wichtige Konventionen:**
- `item.id` = Technische ID (z.B. "item_1") - NIEMALS LLM-Namen!
- `item.label` = UI-Anzeigename (generische Labels)
- `item.source.type` = "human" | "llm" | "unknown"

### Multi-Dimensionales Rating (LLM Evaluator)

Rating verwendet jetzt standardmäßig das multi-dimensionale Format:
- **Layout:** Links Text, rechts mehrere Likert-Skalen pro Dimension
- **Standard-Dimensionen:** Kohärenz, Flüssigkeit, Relevanz, Konsistenz
- **Gewichtung:** Jede Dimension hat ein Gewicht für die Gesamtbewertung
- **Presets:** `llm-judge-standard`, `summeval`, `response-quality`, `news-article`

```json
// Beispiel config_json für Rating
{
  "type": "multi-dimensional",
  "min": 1, "max": 5, "step": 1,
  "dimensions": [
    {"id": "coherence", "name": {"de": "Kohärenz"}, "weight": 0.25},
    {"id": "fluency", "name": {"de": "Flüssigkeit"}, "weight": 0.25}
  ],
  "labels": {"1": {"de": "Sehr schlecht"}, "5": {"de": "Sehr gut"}}
}
```

**Backend-Service:** `app/services/evaluation/dimensional_rating_service.py`
**Frontend-Composable:** `llars-frontend/src/composables/useDimensionalRating.js`

### Scenario Wizard AI System

Der Scenario Wizard nutzt KI um hochgeladene Daten zu analysieren und passende Evaluationstypen vorzuschlagen.

**Wichtige Dateien:**
```
app/services/evaluation/schema_export_service.py  # Schema-Export für AI-Prompts
app/services/ai_assist/field_prompt_service.py    # AI Prompt Templates (DB-gestützt)
app/services/data_import/ai_analyzer.py           # AI Analyse-Logik
```

**Schema-Integration:**
- `SchemaExportService` exportiert Schema-Definitionen aus `evaluation_data_schemas.py`
- AI-Prompts erhalten konsistente Typ-Informationen und Mapping-Beispiele
- Entscheidungsbaum für automatische Evaluationstyp-Erkennung

**Unterstützte Dateiformate:**
- CSV (mit Vergleichsdaten oder Einzeltexten)
- JSON (verschachtelte Strukturen, Konversationen)
- JSONL (eine JSON pro Zeile)
- OpenAI/LMSYS Format (conversation_a/b mit winner)

**Preset-Empfehlungen:**
Die AI empfiehlt automatisch passende Presets aus `evaluationPresets.js`:
- rating: `llm-judge-standard`, `response-quality`, `news-article`
- ranking: `buckets-3`, `buckets-5`
- labeling: `binary-authentic`, `sentiment-3`
- comparison: `pairwise`, `multicriteria`

### Evaluation Status-Berechnung

Der Bewertungsstatus (`pending`, `in_progress`, `done`) wird an mehreren Stellen berechnet:

**Wichtige Dateien:**
- `app/services/scenario_stats_service.py` - `get_progress_stats()` für aggregierte Statistiken
- `app/services/evaluation/session_service.py` - `_get_thread_evaluation_status()` für Einzel-Item-Status
- `app/routes/HelperFunctions.py` - `get_thread_progression_state()` für Progress-Enum

**Status-Werte:**
- `ProgressionStatus.NOT_STARTED` / `'pending'` - Keine Bewertung vorhanden
- `ProgressionStatus.PROGRESSING` / `'in_progress'` - Teilweise bewertet
- `ProgressionStatus.DONE` / `'done'` - Vollständig bewertet

**Dimensions-Config Lokationen (wichtig für Entwickler):**
Die Config kann an verschiedenen Stellen sein je nach Erstellungsart:
```python
# Direkt (manuell erstellt)
config.get('dimensions', [])
# Via Wizard (nested)
config.get('eval_config', {}).get('dimensions', [])
config.get('eval_config', {}).get('config', {}).get('dimensions', [])
```

**ScenarioUsers Rollen:**
- `OWNER` - Szenario-Ersteller, erhält alle Items, wird in `evaluator_stats` gezählt
- `EVALUATOR` - Bewerter, erhält alle Items
- `RATER` - Bewerter mit optionaler Item-Distribution

---

## Frontend Layout

### Viewport-Layout (Fullscreen-Seiten)

```css
.page-container {
  height: calc(100vh - 94px);  /* 64px AppBar + 30px Footer */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel-content {
  flex: 1;
  overflow-y: auto;  /* Nur hier scrollen */
}
```

**Wichtig:** Keine Vuetify Container (`v-container`, `v-row`) für Viewport-Layouts!

### Resizable Panels

```javascript
import { usePanelResize } from '@/composables/usePanelResize'
const { leftPanelStyle, rightPanelStyle, startResize } = usePanelResize({
  initialLeftPercent: 50, storageKey: 'panel-width'
})
```

---

## LLARS Design System

### Signatur: Asymmetrischer Border-Radius

```css
border-radius: 16px 4px 16px 4px;  /* Buttons */
border-radius: 6px 2px 6px 2px;    /* Tags */
```

### Farbpalette

| Farbe | Hex | Verwendung |
|-------|-----|------------|
| Primary | `#b0ca97` | Hauptaktionen |
| Secondary | `#D1BC8A` | Sekundäre Aktionen |
| Accent | `#88c4c8` | Hervorhebung |
| Success | `#98d4bb` | Erfolg |
| Danger | `#e8a087` | Destruktiv |

### Globale Komponenten (35 L-Komponenten)

```vue
<!-- Buttons & Actions -->
<LBtn variant="primary|secondary|accent|danger|cancel|text">
<LIconBtn icon="mdi-edit" tooltip="Bearbeiten" />
<LActionGroup :actions="['view','edit','delete']" @action="handle" />

<!-- Formulare -->
<LCheckbox v-model="checked" label="Option" />
<LRadioGroup v-model="selected" :options="[...]" />
<LSwitch v-model="enabled" label="Aktiviert" />
<LSlider v-model="value" :min="1" :max="10" />
<LRatingScale v-model="rating" :min="1" :max="5" />

<!-- Anzeige -->
<LTag variant="success|info|warning|danger" closable>
<LCard title="Titel" icon="mdi-robot" color="#b0ca97">
<LTabs v-model="tab" :tabs="[{value:'a',label:'Tab A'}]" />
<LTooltip text="Hilfetext"><v-icon>mdi-help</v-icon></LTooltip>
<LAvatar :user="user" size="32" />
<LStatusChip status="active|pending|error" />
<LEvaluationStatus status="done|in_progress|pending" />

<!-- Charts & Statistiken -->
<LChart type="bar|line|pie" :data="chartData" />
<LGauge :value="75" :max="100" label="Progress" />
<LStatCard title="Users" :value="42" icon="mdi-account" />
<LConfusionMatrix :data="matrix" />
<LAgreementHeatmap :evaluators="[...]" :agreements="{...}" />
<LRatingDistribution :distribution="[...]" />

<!-- Loading & Skeleton -->
<LLoading text="Wird geladen..." />
<LSkeleton type="card|list|text" />
<LCardSkeleton />

<!-- Spezial -->
<LUserSearch v-model="selectedUser" />
<LlmModelSelect v-model="model" />
<LLanguageToggle />
<LThemeToggle />
```

---

## Git Commits

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Types:** feat | fix | docs | refactor | chore
**Scopes:** frontend | backend | auth | judge | rag | crawler | db

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Ranking/Rating leer | Zeitraum + User-Rolle prüfen |
| Auth-Fehler | `./scripts/setup_authentik.sh` |
| 502 Bad Gateway (Prod) | `NGINX_EXTERNAL_PORT=80` in `.env` |
| Crawler findet nichts | exclude_patterns prüfen |
| Status "Ausstehend" obwohl bewertet | OWNER-Rolle in ScenarioUsers prüfen, Container neu starten |
| Items-Status inkonsistent | Dimensions-Config Lokationen prüfen (siehe Evaluation Status) |
| Eventlet DNS Timeout | Gevent verwenden: `PROJECT_STATE=production` |
| WebSocket nur Polling | Prüfen: `PROJECT_STATE=production` + Gunicorn mit gevent |
| 429 Too Many Requests | Rate-Limiting aktiv (1000 req/h) - normal bei Load-Tests |

---

## Authentik - NICHT ÄNDERN!

| Invariante | Wert |
|------------|------|
| Client-IDs | llars-backend, llars-frontend |
| Flow-Slug | llars-api-authentication |
| Port | 9000 |

**Bei Änderung:** Login bricht ab!

---

## Wichtige Dateien

```
app/
├── auth/decorators.py            # @authentik_required
├── decorators/
│   ├── permission_decorator.py   # @require_permission
│   └── error_handler.py          # @handle_api_errors
├── routes/                       # API Endpoints
│   ├── scenarios/                # Szenario-Management
│   ├── evaluation_routes.py      # Bewertungs-Endpoints
│   └── HelperFunctions.py        # Progression-State etc.
├── services/
│   ├── evaluation/               # Rating, Session, Dimensional
│   └── scenario_stats_service.py # Progress-Statistiken
├── db/
│   ├── models/                   # SQLAlchemy Models (scenario.py, etc.)
│   └── tables.py                 # Legacy imports
└── main.py

llars-frontend/src/
├── components/
│   ├── common/                   # 35 L-Komponenten (Design System)
│   └── Evaluation/               # EvaluationHub, StatusTag, etc.
├── composables/                  # useAuth, usePermissions, useDimensionalRating
├── views/
│   ├── Evaluation/               # EvaluationItemsOverview, etc.
│   └── ScenarioManager/          # ScenarioWizard, etc.
└── locales/                      # i18n (de.json, en.json)
```

---

## Refactoring Status

### Abgeschlossen (16 Major)

| Task | Zeilen |
|------|--------|
| ChatWithBots.vue | 3299→774 |
| LatexCollabWorkspace.vue | 3085→1259 |
| JudgeSession.vue | 2174→579 |
| ChatbotEditor.vue | 1967→507 |
| chat_service.py | 1657→590 |
| latex_collab_routes.py | 1514→56 |
| crawler_service.py | 1415→666 |
| chatbot_routes.py | 1273→35 |
| anonymize_service.py | 1275→445 |
| agent_chat_service.py | 1263→301 |
| judge_worker_pool.py | 1067→618 |
| collection_embedding_service.py | 1046→606 |
| embedding_worker.py | 825→67 |
| markdown_collab_routes.py | 798→24 |

### Metriken (Stand: 2026-01-27)

```
Backend:  425 Python-Dateien, ~126,000 Zeilen
Frontend: 577 Vue/JS-Dateien, ~193,000 Zeilen

L-Komponenten: 35 (Design System)
```

### Offen

| Bereich | Aktuell | Ziel |
|---------|---------|------|
| Backend Coverage | 21% | 50% |
| Frontend Coverage | 14% | 40% |

---

**Stand:** 31. Januar 2026
