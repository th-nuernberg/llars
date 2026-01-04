# LLARS - LLM Assisted Research System

**Version:** 3.0 | **Stand:** 3. Januar 2026

## Projekt-Übersicht

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit LLMs.

**Features:** Rating/Ranking-System | LLM-as-Judge | RAG-Pipeline (ChromaDB) | Multi-User Collaboration (YJS) | Authentik Auth | RBAC Permissions | Offline Anonymize Tool

**Quick Reference:** Siehe `agent.md` für kompakte Kurzreferenz.

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
| researcher | admin123 | researcher (RATER) |
| viewer | admin123 | viewer (VIEWER) |
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
| build | `build:docker` (nur main) |
| deploy | `deploy:staging`, `deploy:production` |

```
Push to develop → deploy:staging (automatisch)
Push to main    → deploy:production (nach Tests)
```

**Test-Requirements:** `app/requirements-test.txt` (ohne torch, transformers, flair - ~3GB gespart)

### GitLab API Zugriff

Die `.env` enthält GitLab API Credentials für Pipeline-Monitoring:

```bash
# Pipelines abrufen
source .env
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines?per_page=5"

# Jobs einer Pipeline abrufen
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines/{PIPELINE_ID}/jobs"

# Job-Log abrufen
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/jobs/{JOB_ID}/trace"
```

**Umgebungsvariablen (.env):**
- `GITLAB_TOKEN` - API Token mit `api` Scope
- `GITLAB_PROJECT_ID` - Projekt-ID (7123)
- `GITLAB_PROJECT_PATH` - Projekt-Pfad

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
| viewer | Lesezugriff |
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

```
EmailThread
├── Messages[] (Klient ↔ Berater)
└── Features[] (LLM-generierte Analysen)

Scenario
├── ScenarioUsers[] (VIEWER oder RATER)
├── ScenarioThreads[]
└── config_json (distribution_mode, order_mode)
```

| function_type_id | Name | Beschreibung |
|------------------|------|--------------|
| 1 | ranking | Features sortieren (Drag & Drop) |
| 2 | rating | Features bewerten (Sterne) |
| 3 | mail_rating | E-Mail-Konversation bewerten |

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

### Globale Komponenten

```vue
<!-- Buttons -->
<LBtn variant="primary|secondary|accent|danger|cancel|text">

<!-- Tags -->
<LTag variant="success|info|warning|danger" closable>

<!-- Cards -->
<LCard title="Titel" icon="mdi-robot" color="#b0ca97">

<!-- Tabs -->
<LTabs v-model="tab" :tabs="[{value:'a',label:'Tab A'}]" />

<!-- Action Groups -->
<LActionGroup :actions="['view','edit','delete']" @action="handle" />

<!-- Tooltips -->
<LTooltip text="Hilfetext"><v-icon>mdi-help</v-icon></LTooltip>
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
├── services/                     # Business Logic
├── db/tables.py                  # Alle Models
└── main.py

llars-frontend/src/
├── components/common/            # LBtn, LTag, LCard, etc.
├── composables/                  # useAuth, usePermissions
└── views/
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

### Metriken (Stand: 2026-01-03)

```
Backend:  287 Python-Dateien, 72,607 Zeilen
Frontend: 293 Vue/JS-Dateien, 112,096 Zeilen

Docstring Coverage: 82% Functions, 75% Classes, 93% Modules
JSDoc Coverage: 35% (Components 31%, Composables 69%)

Große Dateien (>500 Zeilen): Backend 12, Frontend 82
```

### Offen

| Bereich | Aktuell | Ziel |
|---------|---------|------|
| Backend Coverage | 21% | 50% |
| Frontend Coverage | 14% | 40% |

---

**Stand:** 3. Januar 2026
