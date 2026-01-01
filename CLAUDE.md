# LLARS - LLM Assisted Research System

**Version:** 3.0 | **Stand:** 31. Dezember 2025

## Projekt-Übersicht

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit LLMs.

**Features:** Rating/Ranking-System | LLM-as-Judge | RAG-Pipeline (ChromaDB) | Multi-User Collaboration (YJS) | Authentik Auth | RBAC Permissions | Offline Anonymize Tool

---

## Projekt starten

```bash
# Ersteinrichtung
cp .env.template.development .env
./start_llars.sh

# Komplett-Neustart (LÖSCHT ALLE DATEN!)
REMOVE_LLARS_VOLUMES=True ./start_llars.sh
```

### URLs (Development)

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik | http://localhost:55095 |
| Matomo | http://localhost:55080/analytics/ |

### Test-Benutzer

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher (RATER) |
| viewer | admin123 | viewer (VIEWER) |
| chatbot_manager | admin123 | chatbot_manager |

---

## Server-Operationen

### Neustart mit System-Prune

```bash
# Container stoppen
docker compose down

# System bereinigen (alle ungenutzten Images, Container, Volumes entfernen)
docker system prune -af --volumes

# Neu starten
./start_llars.sh
```

### User-Seeder (Projekt-Benutzer anlegen)

Der User-Seeder liegt in einem separaten Repository: `llars-seeder/`

```bash
cd /path/to/llars-seeder

# 1. .env konfigurieren
cat > .env << 'EOF'
PROJECT_URL=http://localhost:55080      # Lokale Entwicklung
# PROJECT_URL=https://llars.example.com # Produktion
SYSTEM_ADMIN_API_KEY=llars-admin-key-change-in-production-12345
EOF

# 2. users.yaml anpassen (Benutzer definieren)

# 3. Seeder ausführen
./provision_users.sh
```

### Backup erstellen

```bash
# Vollständiges Datenbank-Backup
docker exec llars_db_service mysqldump -u dev_user -pdev_password_change_me database_llars > backup_$(date +%Y%m%d)/full_backup.sql

# Nur bestimmte Tabellen (z.B. Evaluierungsdaten)
docker exec llars_db_service mysqldump -u dev_user -pdev_password_change_me database_llars \
  authenticity_conversations user_authenticity_votes comparison_sessions comparison_evaluations \
  > backup_$(date +%Y%m%d)/evaluation_data.sql
```

### Backup wiederherstellen

```bash
# SQL-Backup in Container kopieren und ausführen
docker cp backup_20251223/evaluation_data.sql llars_db_service:/tmp/evaluation_data.sql
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars \
  -e "source /tmp/evaluation_data.sql"

# Alternativ: Piped
cat backup_20251223/evaluation_data.sql | docker exec -i llars_db_service \
  mariadb -u dev_user -pdev_password_change_me database_llars
```

### Datenbank-Migrationen

Bei Schema-Änderungen manuell SQL ausführen:

```bash
# Migration erstellen (Beispiel: neue Tabelle)
cat > migrations/001_add_collection_embeddings.sql << 'EOF'
CREATE TABLE IF NOT EXISTS collection_embeddings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    collection_id INT NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    model_source ENUM('local', 'litellm') NOT NULL,
    embedding_dimensions INT NOT NULL,
    chroma_collection_name VARCHAR(255) NOT NULL UNIQUE,
    status ENUM('idle', 'processing', 'completed', 'failed') DEFAULT 'idle',
    progress INT DEFAULT 0,
    chunk_count INT DEFAULT 0,
    error_message TEXT,
    priority INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (collection_id) REFERENCES rag_collections(id) ON DELETE CASCADE,
    UNIQUE KEY unique_collection_model (collection_id, model_id),
    INDEX idx_collection_id (collection_id),
    INDEX idx_model_id (model_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority)
);
EOF

# Migration ausführen
docker cp migrations/001_add_collection_embeddings.sql llars_db_service:/tmp/
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars \
  -e "source /tmp/001_add_collection_embeddings.sql"
```

**Hinweis:** SQLAlchemy erstellt fehlende Tabellen automatisch beim Start. Migrationen sind nur für Schema-Änderungen an bestehenden Tabellen nötig.

### Lexical Search Index (FTS)

- Trigram-basierter FTS-Index liegt unter `app/data/rag/indexes/lexical_index.sqlite`.
- Pfad kann per `LEXICAL_INDEX_PATH` überschrieben werden.
- Index wird bei `lexical_search` pro Collection lazy aufgebaut und beim Embedding/Update/Delete aktualisiert.

### Logs prüfen

```bash
# Flask-Backend Logs
docker logs -f llars_flask_service

# Alle Container-Logs
docker compose logs -f

# Nur Fehler
docker compose logs -f 2>&1 | grep -i error
```

---

## GitLab CI/CD Pipeline

### Übersicht

LLARS verwendet GitLab CI/CD für automatisiertes Testing und Deployment. Die Pipeline-Konfiguration liegt in `.gitlab-ci.yml`.

```
GitLab: git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars
Server: 141.75.150.128 (internes Netz)
Runner: Shell-Executor direkt auf LLARS Server (kein SSH nötig)
```

### Pipeline Stages

| Stage | Jobs | Beschreibung |
|-------|------|--------------|
| **lint** | `lint:backend`, `lint:frontend` | Code-Qualität (flake8, eslint) - allow_failure |
| **test** | `test:unit:backend`, `test:unit:frontend`, `test:integration`, `test:e2e`, `security:scan` | Tests + Security |
| **build** | `build:docker` | Docker Images bauen (nur main) |
| **deploy** | `deploy:staging`, `deploy:production`, `smoke:test`, `rollback:production` | Deployment |

### Automatisches Deployment

```
Push to develop → deploy:staging (automatisch)
Push to main    → deploy:production (nach erfolgreichen Tests + Build)
```

### Shell Runner (auf Server)

Der GitLab Runner läuft direkt auf dem LLARS Server mit Shell-Executor. Kein SSH nötig für Deployments!

```bash
# Runner-Konfiguration: /etc/gitlab-runner/config.toml
[[runners]]
  name = "llars-server-shell"
  executor = "shell"
  tags = ["shell"]       # Jobs müssen tag: shell haben
  run_untagged = false   # Nimmt keine ungetaggten Jobs an
```

**Wichtige Verzeichnisse:**
```
/var/llars/              # LLARS Projekt
/etc/gitlab-runner/      # Runner-Konfiguration
~gitlab-runner/.cache/   # CI Cache
```

### Test Requirements (Lightweight)

Für CI/CD Tests wird `app/requirements-test.txt` verwendet, die schwere ML-Pakete ausschließt:

```
Ausgeschlossen (~3GB gespart):
- torch
- transformers
- sentence-transformers
- flair
- langchain-huggingface
```

Die Tests mocken diese Dependencies.

### System Dependencies (CI Jobs)

Python-Jobs benötigen System-Pakete für Compilation:

```yaml
before_script:
  - apt-get update && apt-get install -y --no-install-recommends build-essential libffi-dev libssl-dev pkg-config
  - pip install --upgrade pip
```

### Troubleshooting CI/CD

| Problem | Lösung |
|---------|--------|
| Pipeline startet nicht | Prüfen ob CI/CD aktiviert: Settings → General → Visibility |
| Runner offline | `sudo gitlab-runner status` auf Server |
| test:unit:backend failed | Prüfen ob `requirements-test.txt` verwendet wird |
| Deploy fehlgeschlagen | Logs prüfen: `docker logs llars_flask_service` |
| pip install timeout | ML-Pakete in requirements-test.txt? Sollten ausgeschlossen sein |
| Permission denied | `/var/llars` muss für `gitlab-runner` schreibbar sein |

### GitLab Runner Verwaltung (auf Server)

```bash
# Status prüfen
sudo gitlab-runner status

# Registrierte Runner anzeigen
sudo gitlab-runner list

# Runner neu starten
sudo systemctl restart gitlab-runner

# Logs prüfen
sudo journalctl -u gitlab-runner -f
```

### Pipeline-Status prüfen

```bash
# Via GitLab UI
open "https://git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars/-/pipelines"

# Via API (Token in lokaler .env)
curl -s -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/kiz-nlp%2Fllars%2Fllars/pipelines?per_page=5"
```

---

## Software Tests - PFLICHT!

**WICHTIG:** Jede neue Komponente, Composable oder Service MUSS mit Tests abgedeckt werden. Ohne Tests wird kein Code akzeptiert.

### Testübersicht

| Bereich | Tool | Pfad |
|---------|------|------|
| **Backend Unit** | pytest | `tests/unit/` |
| **Backend Integration** | pytest | `tests/integration/` |
| **Frontend Components** | Vitest | `llars-frontend/tests/components/` |
| **Frontend Composables** | Vitest | `llars-frontend/tests/composables/` |

### Tests ausführen

```bash
# Backend Tests
cd /path/to/llars
pytest tests/                              # Alle Tests
pytest tests/unit/                         # Nur Unit Tests
pytest --cov=app --cov-report=html tests/  # Mit Coverage

# Frontend Tests
cd llars-frontend
npm run test:run                           # Alle Tests (einmalig)
npm run test                               # Watch Mode
npm run test:coverage                      # Mit Coverage
npm run test:run -- tests/composables/useAuth.spec.js  # Einzelne Datei
```

### Test-ID Konventionen

Jeder Test hat eine eindeutige ID für Traceability:

| Präfix | Bereich | Beispiel |
|--------|---------|----------|
| `AUTH_` | useAuth Composable | AUTH_001, AUTH_002 |
| `PERM_` | usePermissions | PERM_001 |
| `COMP_BTN_` | LBtn Component | COMP_BTN_001 |
| `COMP_TAG_` | LTag Component | COMP_TAG_001 |
| `SKEL_` | useSkeletonLoading | SKEL_001 |
| `MOBILE_` | useMobile | MOBILE_001 |

### Frontend Test-Pattern (Vitest + Vue Test Utils)

```javascript
// tests/composables/useExample.spec.js
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useExample } from '@/composables/useExample'

describe('useExample Composable', () => {
  beforeEach(() => {
    vi.resetModules()  // Wichtig für Singleton-Composables!
  })

  describe('Exports', () => {
    it('EXAMPLE_001: exports useExample function', () => {
      expect(typeof useExample).toBe('function')
    })

    it('EXAMPLE_002: returns expected properties', () => {
      const result = useExample()
      expect(result).toHaveProperty('someValue')
      expect(result).toHaveProperty('someFunction')
    })
  })

  describe('Functionality', () => {
    it('EXAMPLE_003: does something specific', () => {
      const { someFunction } = useExample()
      const result = someFunction('input')
      expect(result).toBe('expected output')
    })
  })
})
```

### Komponenten ohne Tests zu zerstören ändern

**Regel 1: Props-Kompatibilität wahren**
```javascript
// SCHLECHT - Bricht bestehende Tests
// Vorher: <LBtn variant="primary">
// Nachher: <LBtn type="primary">  // Prop umbenannt!

// GUT - Rückwärtskompatibel
props: {
  variant: String,
  type: String,  // Neuer Name
}
computed: {
  resolvedType() {
    return this.type || this.variant  // Fallback auf alten Namen
  }
}
```

**Regel 2: Emit-Events nicht umbenennen**
```javascript
// SCHLECHT
emit('onUpdate')  // Vorher: emit('update')

// GUT - Beide Events emittieren während Übergang
emit('update', value)
emit('onUpdate', value)  // Neues Event zusätzlich
```

**Regel 3: Default-Werte beibehalten**
```javascript
// SCHLECHT - Ändert Default-Verhalten
props: {
  size: { type: String, default: 'large' }  // War: 'default'
}

// GUT - Default unverändert lassen
props: {
  size: { type: String, default: 'default' }
}
```

**Regel 4: CSS-Klassen nicht entfernen**
```vue
<!-- SCHLECHT -->
<div class="new-class">  <!-- .container entfernt -->

<!-- GUT -->
<div class="container new-class">  <!-- Alte Klasse behalten -->
```

### Kaputte Tests reparieren

**Schritt 1: Fehler verstehen**
```bash
npm run test:run -- tests/components/LBtn.spec.js
# Zeigt genau welcher Test fehlschlägt und warum
```

**Schritt 2: Typische Fehlerursachen**

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `Expected "X" but got "Y"` | Rückgabewert geändert | Test-Erwartung anpassen ODER Code-Änderung überdenken |
| `Property "X" not found` | Prop/Export entfernt | Prop wiederherstellen ODER alle Tests updaten |
| `Cannot read property of undefined` | Mock fehlt | Mock hinzufügen (axios, localStorage, etc.) |
| `TypeError: X is not a function` | API geändert | Funktion wiederherstellen ODER Tests anpassen |

**Schritt 3: Test anpassen (wenn Code-Änderung korrekt ist)**
```javascript
// Test-Datei öffnen und Erwartung aktualisieren
it('COMP_BTN_005: renders with correct size class', () => {
  const wrapper = mount(LBtn, { props: { size: 'small' } })
  // Vorher:
  // expect(wrapper.classes()).toContain('v-btn--size-small')
  // Nachher (neue Implementierung):
  expect(wrapper.classes()).toContain('l-btn--small')
})
```

**Schritt 4: Alle Tests erneut ausführen**
```bash
npm run test:run  # Sicherstellen dass keine Seiteneffekte
```

### Mocking-Patterns

**Axios mocken:**
```javascript
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn()
  }
}))

// In Test:
import axios from 'axios'
axios.get.mockResolvedValue({ data: { success: true } })
```

**localStorage mocken:**
```javascript
const mockStorage = {}
vi.stubGlobal('localStorage', {
  getItem: vi.fn((key) => mockStorage[key] || null),
  setItem: vi.fn((key, value) => { mockStorage[key] = value }),
  removeItem: vi.fn((key) => { delete mockStorage[key] }),
  clear: vi.fn(() => { Object.keys(mockStorage).forEach(k => delete mockStorage[k]) })
})
```

**Vue Router mocken:**
```javascript
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn()
  }),
  useRoute: () => ({
    params: {},
    query: {}
  })
}))
```

**Vuetify useDisplay mocken:**
```javascript
vi.mock('vuetify', () => ({
  useDisplay: () => ({
    mobile: { value: false },
    smAndDown: { value: false },
    mdAndUp: { value: true },
    width: { value: 1024 },
    height: { value: 768 }
  })
}))
```

### Checkliste vor Commit

- [ ] Alle bestehenden Tests laufen durch: `npm run test:run`
- [ ] Neue Komponente/Composable hat eigene Test-Datei
- [ ] Test-IDs sind eindeutig und folgen Konvention
- [ ] Edge Cases getestet (null, undefined, leere Arrays, etc.)
- [ ] Fehlerbehandlung getestet (API-Fehler, Timeouts)
- [ ] Coverage prüfen: `npm run test:coverage`

### Test-Dokumentation

Vollständige Testanforderungen: `docs/testing/README.md`

```
docs/testing/
├── README.md                    # Übersicht + Quick Start
├── leitfaden/                   # How-To Guides
├── anforderungen/               # Was getestet werden muss
│   ├── frontend/                # Frontend-Spezifisch
│   ├── backend/                 # Backend-Spezifisch
│   └── security/                # Security-Tests
└── checklisten/                 # Smoke Test, Release Checklist
```

---

## Architektur

```
nginx (:80) → Reverse Proxy
├── / → Vue Frontend (:5173)
├── /api/, /auth/ → Flask Backend (:8081)
├── /analytics/ → Matomo Analytics (:80)
└── /collab/ → YJS WebSocket (:8082)

Databases: MariaDB (:3306 - LLARS), MariaDB (:3306 - Matomo), PostgreSQL (:5432 - Authentik)
```

**Backend:** Flask 3.0 + MariaDB 11.2 + ChromaDB
**Frontend:** Vue 3.4 + Vuetify 3.5 + Vite 5.1 + Socket.IO

---

## Matomo Analytics (Self-hosted)

- Auto-Setup via Docker Compose Service `matomo-init` (DB + Superuser + Site)
- Frontend Tracking: `llars-frontend/src/plugins/llars-metrics.js` (SPA Pageviews + Click Events + optional User-ID)
- Matomo UI: `/analytics/` (Alias: `/matomo/`), Tracking: `/metrics.js` + `/metrics.php` (first-party, weniger Blocker)
- Optional SSO: `MATOMO_OIDC_ENABLED=true` + `AUTHENTIK_PUBLIC_URL` + `AUTHENTIK_MATOMO_*` (RebelOIDC Plugin)
- Runtime-Config über LLARS DB (Admin Panel): `GET/PATCH /api/admin/analytics/settings` (Table `analytics_settings`)

## Admin System Tools

- Docker Monitor (Admin → Docker): Live Container-Status, CPU/RAM und Logs via Socket.IO Namespace `/admin` (`docker:*`)
  - Voraussetzung: `/var/run/docker.sock` ist gemountet und die Backend-User-Group darf schreiben (Dev: `start_llars.sh` setzt `DOCKER_SOCK_GID` und versucht `chmod g+w`).
  - Security Hinweis: Zugriff auf `docker.sock` erlaubt prinzipiell Host-Docker Kontrolle → nur für Admins aktivieren.
- DB Explorer (Admin → DB): Read-only Tabellen-Viewer (live) via Socket.IO Namespace `/admin` (`db:*`)

## Docker Base Images

- Wenn Docker Hub Probleme macht (z.B. OAuth Token 500), nutzt LLARS für die offiziellen Images die Public ECR Mirror-Registry: `public.ecr.aws/docker/library/*` (Python/Node/Nginx/Postgres/Redis/MariaDB/Matomo).

---

## Offline Anonymize Tool

- Frontend: `/Anonymize` (Kachel auf Home), Permission: `feature:anonymize:view`
- Backend: `GET /api/anonymize/health`, `POST /api/anonymize/pseudonymize`, `POST /api/anonymize/pseudonymize-file`
- Ressourcen: SQLite-DB liegt in `docs/docs/projekte/anonymize/database` (via Docker Compose nach `/app/data/anonymize` gemountet), Reco in `app/models/anonymize/recommender_system`, großes Flair-NER Modell wird aus `docs/docs/projekte/anonymize/models/ner-german-large` gemountet

---

## Rating/Ranking System

Das Kernfeature von LLARS: Bewertung von LLM-generierten Features für E-Mail-Konversationen.

### Konzept

```
EmailThread (Beratungs-E-Mail)
├── Messages[] (Klient ↔ Berater Dialog)
└── Features[] (LLM-generierte Analysen)
    ├── GPT-4: "Situation Summary", "Client Needs", ...
    ├── Claude-3: "Situation Summary", "Client Needs", ...
    └── Mistral-7B: "Situation Summary", "Client Needs", ...

Scenario (Rating oder Ranking)
├── ScenarioUsers[] (User + Rolle: VIEWER oder RATER)
├── ScenarioThreads[] (zugewiesene Threads)
└── ScenarioThreadDistribution[] (welcher RATER bewertet welchen Thread)
└── config_json (distribution_mode: all|round_robin, order_mode: none|shuffle_same|shuffle_per_user)
```

### Function Types

| ID | Name | Beschreibung |
|----|------|--------------|
| 1 | ranking | Features nach Qualität sortieren (Drag & Drop) |
| 2 | rating | Features einzeln bewerten (Sterne/Skala) |
| 3 | mail_rating | Gesamte E-Mail-Konversation bewerten |

### Wichtige Tabellen

```sql
feature_function_types  -- ranking(1), rating(2), mail_rating(3)
rating_scenarios        -- Szenarien mit begin/end Zeitraum
scenario_users          -- User-Rollen: VIEWER oder RATER
scenario_threads        -- Threads im Szenario
scenario_thread_distribution  -- RATER → Thread Zuweisung
email_threads           -- E-Mail-Konversationen (function_type_id!)
features                -- LLM-generierte Inhalte (thread_id, type_id, llm_id)
```

### Zugriffskontrolle

```python
# app/routes/HelperFunctions.py
def get_user_threads(user_id, function_type_id):
    """
    VIEWER: Sieht alle Threads im Szenario
    RATER: Abhängig von distribution_mode
      - all: alle Threads wie Viewer
      - round_robin: nur zugeordnete Threads (ScenarioThreadDistribution)

    Zeitprüfung: RatingScenarios.begin <= NOW <= RatingScenarios.end
    order_mode steuert die Thread-Reihenfolge:
      - none: sortiert nach thread_id
      - shuffle_same: gleiche Mischung für alle (Seed = scenario_id)
      - shuffle_per_user: unterschiedliche Mischung pro Nutzer (Seed = scenario_id:user_id)
    """
```

### API Endpoints

```
GET /api/email_threads/rankings      # Ranking-Threads für User
GET /api/email_threads/ratings       # Rating-Threads für User
GET /api/email_threads/rankings/<id> # Thread-Details mit Features
POST /api/save_ranking/<id>          # Ranking speichern
```

### Demo-Szenarien (Development)

Im Dev-Mode werden automatisch Demo-Szenarien erstellt (`app/db/seeders/scenarios.py`):

- **Demo Rating Szenario**: 2 Threads (function_type_id=2), researcher=RATER, viewer=VIEWER
- **Demo Ranking Szenario**: 1 Thread (function_type_id=1), researcher=RATER, viewer=VIEWER
- **Demo Verlauf Bewerter Szenario**: 2 Threads (function_type_id=3), researcher=RATER, viewer=VIEWER
- 5 E-Mail-Threads mit realistischen Beratungsanfragen
- Features für alle Threads (4 Typen × 3 LLMs)

---

## Auth Decorator - WICHTIG!

`g.authentik_user` ist ein **User-Objekt** (nicht String!):

```python
# app/auth/decorators.py
@authentik_required
def my_route():
    user = g.authentik_user  # User-Objekt mit .id, .username
    user_id = user.id        # Für DB-Queries
```

Bei Login wird der User automatisch in der DB erstellt (`get_or_create_user`).

---

## User Profile (Avatar + Collab Color)

- Einstellungen: `GET/PATCH /api/users/me/settings` (collab_color, avatar_seed, avatar_url, avatar_changes_left)
- Avatar: `POST/PATCH/DELETE /api/users/me/avatar` (Upload, neues Standardbild, Reset)
- Avatar-URL: `/api/users/avatar/<avatar_public_id>` (Bildauslieferung)
- Limit: 3 Avatar-Änderungen pro Tag, Speicherort `app/storage/avatars` (Default)

---

## Permission System

**Sicherheitsmodell:** Deny-by-Default | User überschreibt Rolle | Deny schlägt Grant

### Rollen (Auszug)

- **admin**: alle Permissions
- **researcher**: Evaluation + Prompt Engineering + Markdown Collab + Anonymize + KAIMO (kein RAG/Chatbot Admin)
- **viewer**: Lesezugriff (u. a. Prompt Engineering, RAG, Chatbots, Markdown Collab)
- **chatbot_manager**: Chatbot-Verwaltung (inkl. Wizard/Publish/Share) + RAG-Dokumente (eigene/geteilte) + Prompt Engineering + Markdown Collab

### Chatbot/RAG Access-Logik

- Chatbots: Owner darf immer, Sharing via Allowlist (User/Rollen), Admin override.
- RAG: Sichtbar = public **oder** Owner **oder** explizit geteilt (Dokumente **oder** Collections); Bearbeiten/Löschen nur Owner/Admin bzw. mit expliziter Permission.
- RAG Collections: Teilen via `/api/rag/collections/<id>/access` erweitert Zugriff auf alle enthaltenen Dokumente (inkl. Socket.IO Queue Updates).

### Backend

```python
from decorators.permission_decorator import require_permission

@bp.route('/api/feature')
@require_permission('feature:ranking:view')
@handle_api_errors(logger_name='ranking')
def my_route(): ...
```

### Frontend

```vue
<script setup>
import { usePermissions } from '@/composables/usePermissions'
const { hasPermission } = usePermissions()
</script>
<template>
  <v-card v-if="hasPermission('feature:ranking:view')">...</v-card>
</template>
```

---

## Error Handling

**ALLE Routes MÜSSEN `@handle_api_errors` nutzen:**

```python
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError

@bp.route('/items/<int:id>')
@require_permission('feature:items:view')
@handle_api_errors(logger_name='module_name')
def get_item(id):
    item = Item.query.get(id)
    if not item:
        raise NotFoundError(f'Item {id} not found')
    return jsonify({'success': True, 'item': item.to_dict()})
```

| Exception | Status |
|-----------|--------|
| `NotFoundError` | 404 |
| `ValidationError` | 400 |
| `ConflictError` | 409 |

---

## RAG-Pipeline / Webcrawler

### Crawler-Konfiguration

```python
# app/services/crawler/modules/playwright_crawler.py
exclude_patterns = [
    r'\.css$', r'\.js$', r'\.json$',  # Keine Code-Dateien
    r'/feed/?$', r'/rss/?$',           # Keine Feeds
    r'/wp-admin', r'/wp-login',        # Keine Admin-Seiten
]
```

### Screenshots (lange Seiten)

```python
# app/services/crawler/modules/screenshot_capture.py
capture_long_page()  # Splittet Seiten >4000px in mehrere Screenshots
```

### Embedding Model (Multi-Model-Architektur)

LLARS unterstützt mehrere Embedding-Modelle pro Collection mit robuster Fallback-Kette:

```
Priorität  | Model                                | Source   | Dimensionen
-----------|--------------------------------------|----------|------------
1 (höchste)| llamaindex/vdr-2b-multi-v1           | LiteLLM  | 1024
2          | llamaindex/vdr-2b-multi-v1           | Local    | 1024
3 (fallback)| sentence-transformers/all-MiniLM-L6-v2| Local    | 384
```

**Wichtige Tabellen:**
- `llm_models`: Model-Konfiguration (model_type='embedding', is_default)
- `collection_embeddings`: Tracking welche Models pro Collection verfügbar sind
- `rag_document_chunks.embedding_model`: Model das für jeden Chunk verwendet wurde

**KRITISCH:** Query-Embedding muss IMMER zum Document-Embedding passen (gleiche Dimensionen)!

**Services:**
- `services/rag/embedding_model_service.py`: Zentraler Service für Model-Verfügbarkeit
- `get_best_embedding_for_collection()`: Findet bestes verfügbares Model für eine Collection

```python
from services.rag.embedding_model_service import get_best_embedding_for_collection

# Gibt (embeddings, model_id, chroma_collection_name, dimensions) zurück
embeddings, model_id, chroma_name, dims = get_best_embedding_for_collection(collection_id)
```

### LLM Models (DB Single Source of Truth)

- Tabelle: `llm_models`
- Typen: `model_type` = llm | embedding | reranker
- Capabilities: `supports_vision`, `supports_reasoning`, `supports_streaming`, `supports_function_calling`
- Defaults pro Typ via `is_default`

---

## LLM-as-Judge

Automatisierte paarweise Vergleiche von E-Mail-Konversationen.

```
GET/POST /api/judge/sessions
POST     /api/judge/sessions/<id>/start|pause
GET      /api/judge/pillars
```

---

## Wichtige Dateien

```
app/
├── auth/decorators.py            # @authentik_required, get_or_create_user
├── decorators/
│   ├── permission_decorator.py
│   └── error_handler.py
├── routes/
│   ├── HelperFunctions.py        # get_user_threads, can_access_thread
│   └── rating/ranking_routes.py
├── services/crawler/             # Webcrawler + Screenshots
├── db/
│   ├── tables.py                 # Alle Models
│   └── seeders/scenarios.py      # Demo-Szenarien
└── main.py

llars-frontend/src/
├── components/
│   ├── Ranker/Ranker.vue
│   └── Rater/Rater.vue
└── composables/
    ├── usePermissions.js
    └── useAuth.js
```

---

## Frontend Viewport Layout

Seiten die den gesamten Viewport nutzen sollen (ohne Scrolling) müssen AppBar + App-Footer berücksichtigen.

### Höhenberechnung

```
AppBar:     64px
App-Footer: 30px
━━━━━━━━━━━━━━━━
Gesamt:     94px → height: calc(100vh - 94px)
```

### Korrektes Layout-Pattern

```vue
<template>
  <div class="page-container">
    <div class="main-content">
      <div class="left-panel">
        <div class="panel-header">...</div>
        <div class="panel-content">...</div>  <!-- overflow-y: auto -->
      </div>
      <div class="right-panel">
        <div class="panel-header">...</div>
        <div class="panel-content">...</div>  <!-- overflow-y: auto -->
      </div>
    </div>
    <div class="action-bar">...</div>  <!-- flex-shrink: 0 -->
  </div>
</template>

<style scoped>
.page-container {
  height: calc(100vh - 94px);  /* 64px AppBar + 30px Footer */
  display: flex;
  flex-direction: column;
  overflow: hidden;  /* WICHTIG! */
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;  /* WICHTIG! */
}

.left-panel, .right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-content {
  flex: 1;
  overflow-y: auto;  /* Nur hier scrollen! */
}

.action-bar {
  flex-shrink: 0;  /* Fixiert am unteren Rand */
  padding: 8px 16px;
}
</style>
```

### Wichtige Regeln

1. **Keine Vuetify Container** für Viewport-Layouts: `v-container`, `v-row`, `v-col` haben eigene Styles die Flexbox stören
2. **overflow: hidden** auf allen Containern außer dem scrollbaren Bereich
3. **flex-shrink: 0** für fixierte Elemente (Header, Action-Bar)
4. **Plain `<div>`** statt Vuetify-Komponenten für Layout-Struktur

### Resizable Panels

Für Layouts mit verstellbaren Panels das `usePanelResize` Composable verwenden:

```javascript
import { usePanelResize } from '@/composables/usePanelResize'

const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 50,
  minLeftPercent: 25,
  maxLeftPercent: 75,
  storageKey: 'my-panel-width'  // Speichert Position in localStorage
})
```

```vue
<template>
  <div ref="containerRef" class="main-content">
    <div class="left-panel" :style="leftPanelStyle()">...</div>
    <div class="resize-divider" :class="{ resizing: isResizing }" @mousedown="startResize">
      <div class="resize-handle"></div>
    </div>
    <div class="right-panel" :style="rightPanelStyle()">...</div>
  </div>
</template>
```

### Beispiel-Komponenten

- `llars-frontend/src/components/Home.vue`
- `llars-frontend/src/components/Ranker/RankerDetail.vue`
- `llars-frontend/src/components/Rater/RaterDetail.vue`
- `llars-frontend/src/components/Judge/JudgeOverview.vue`
- `llars-frontend/src/components/Judge/JudgeSession.vue`
- `llars-frontend/src/components/Judge/JudgeConfig.vue`
- `llars-frontend/src/composables/usePanelResize.js`

---

## Progressive / Staggered Loading

Bei Seiten mit mehreren unabhängigen Daten-Sektionen (z.B. Admin-Dashboard, Docker Monitor) sollen die Sektionen **nacheinander erscheinen** statt alle gleichzeitig zu laden und dann auf einmal zu rendern.

### Warum?

- **Bessere UX**: User sieht sofort ersten Content statt lange auf leere Skeleton-Loader zu starren
- **Gefühlte Performance**: Progressives Rendering wirkt schneller, auch wenn die Gesamtladezeit gleich ist
- **Reduzierte kognitive Last**: Inhalte erscheinen in verdaulichen Stücken

### Pattern: Staggered Loading

```javascript
// Konfigurierbare Verzögerungen pro Sektion
const STAGGER_DELAYS = {
  summary: 0,      // Sofort
  charts: 150,     // 150ms später
  table: 300,      // 300ms später
  logs: 450        // 450ms später
}

const staggeredLoadingTimers = {}

const setStaggeredLoading = (sections, loading) => {
  // Alte Timer aufräumen
  Object.values(staggeredLoadingTimers).forEach(timer => clearTimeout(timer))

  if (loading) {
    // Loading setzen: sofort
    sections.forEach(section => setLoading(section, true))
  } else {
    // Loading entfernen: gestaffelt
    sections.forEach(section => {
      const delay = STAGGER_DELAYS[section] || 0
      staggeredLoadingTimers[section] = setTimeout(() => {
        setLoading(section, false)
      }, delay)
    })
  }
}

// Cleanup in onBeforeUnmount
onBeforeUnmount(() => {
  Object.values(staggeredLoadingTimers).forEach(timer => clearTimeout(timer))
})
```

### Anwendungsfälle

| Szenario | Empfehlung |
|----------|------------|
| **Mehrere unabhängige API-Calls** | Staggered Loading |
| **Dashboard mit Widgets** | Staggered Loading |
| **Einzelner API-Call** | Normales Loading |
| **Abhängige Daten (A → B)** | Sequentielles Loading |

### Beispiel-Komponenten

- `llars-frontend/src/components/Admin/sections/AdminDockerMonitorSection.vue`

---

## LLARS Design System

LLARS verwendet ein einheitliches Design-System mit Pastel-Farbpalette und asymmetrischem Styling.

### Signatur-Element: Asymmetrischer Border-Radius

Das charakteristische LLARS-Design nutzt asymmetrische Ecken:

```css
/* Buttons */
border-radius: 16px 4px 16px 4px;

/* Tags/Chips */
border-radius: 6px 2px 6px 2px;
```

### Farbpalette (Pastel Theme)

| Farbe | Hex | Verwendung |
|-------|-----|------------|
| **Primary** | `#b0ca97` | Hauptaktionen (Sage Green) |
| **Secondary** | `#D1BC8A` | Sekundäre Aktionen (Golden Beige) |
| **Accent** | `#88c4c8` | Hervorgehobene Aktionen (Soft Teal) |
| **Success** | `#98d4bb` | Erfolg (Soft Mint) |
| **Info** | `#a8c5e2` | Information (Soft Blue) |
| **Warning** | `#e8c87a` | Warnung (Soft Gold) |
| **Danger** | `#e8a087` | Destruktive Aktionen (Soft Coral) |
| **Gray** | `#9e9e9e` | Neutral/Abbrechen |

### Globale Komponenten

Alle globalen Komponenten sind in `main.js` registriert und überall verfügbar:

#### LBtn - Button

```vue
<LBtn variant="primary" prepend-icon="mdi-plus">Erstellen</LBtn>
<LBtn variant="secondary">Download</LBtn>
<LBtn variant="accent">Spezial-Aktion</LBtn>
<LBtn variant="danger">Löschen</LBtn>
<LBtn variant="cancel">Abbrechen</LBtn>
<LBtn variant="text">Text Button</LBtn>
<LBtn variant="outlined">Outlined</LBtn>
```

**Props:**
- `variant`: primary | secondary | accent | success | danger | cancel | text | outlined
- `size`: small | default | large
- `prepend-icon` / `append-icon`: MDI Icon Name
- `loading`: Boolean
- `disabled`: Boolean
- `block`: Boolean (volle Breite)

#### LTag - Tag/Chip

```vue
<LTag variant="primary">Status</LTag>
<LTag variant="success" prepend-icon="mdi-check">Fertig</LTag>
<LTag variant="danger" closable @close="handleClose">Entfernen</LTag>
```

**Props:**
- `variant`: primary | secondary | accent | success | info | warning | danger | gray
- `size`: small | default | large
- `prepend-icon` / `append-icon`: MDI Icon Name
- `closable`: Boolean

#### LActionGroup - Action Button Group

Gruppierte Icon-Buttons für Tabellenzeilen und Karten-Aktionen.

```vue
<!-- Einfache Preset-Nutzung -->
<LActionGroup
  :actions="['view', 'edit', 'delete']"
  @action="handleAction"
/>

<!-- Mit Custom-Actions und Presets gemischt -->
<LActionGroup
  :actions="[
    'stats',
    { key: 'custom', icon: 'mdi-star', tooltip: 'Favorit' },
    'delete'
  ]"
  @action="handleAction"
/>

<!-- Mit Slot für Dialog-Trigger -->
<LActionGroup :actions="['stats', 'edit', 'delete']" @action="handleAction">
  <template #edit>
    <MyEditDialog :item="item" />
  </template>
</LActionGroup>
```

**Preset Actions:**
- `view`: Anzeigen (mdi-eye)
- `edit`: Bearbeiten (mdi-pencil)
- `delete`: Löschen (mdi-delete, danger)
- `stats`: Statistiken (mdi-chart-bar)
- `download`: Herunterladen (mdi-download)
- `copy`: Kopieren (mdi-content-copy)
- `lock` / `unlock`: Sperren/Entsperren
- `refresh`: Aktualisieren (mdi-refresh)
- `close`: Schließen (mdi-close)
- `add`: Hinzufügen (mdi-plus, success)
- `play` / `pause` / `stop`: Steuerung

**Props:**
- `actions`: Array von Preset-Namen (Strings) oder Action-Objekten
- `size`: x-small | small | default | large | x-large
- `gap`: none | xs | sm | md | lg
- `align`: start | center | end

**Action-Objekt:**
```javascript
{
  key: 'custom',      // Eindeutiger Identifier
  icon: 'mdi-star',   // Icon
  tooltip: 'Tooltip', // Tooltip-Text
  variant: 'primary', // Button-Variante
  loading: false,     // Loading-State
  disabled: false     // Disabled-State
}
```

#### LSlider - Farbverlauf-Slider

Slider mit dynamischem Farbverlauf basierend auf dem Wert. Initial grau, wird bei Interaktion farbig.

```vue
<!-- Standard Gradient (rot → gelb → grün) -->
<LSlider v-model="confidence" :min="0" :max="100" :step="5" />

<!-- Feste Farbe -->
<LSlider v-model="rating" :min="1" :max="5" color-mode="fixed" color="primary" />

<!-- Sofort farbig (ohne initiales Grau) -->
<LSlider v-model="value" :start-active="true" />
```

**Props:**
- `modelValue`: v-model Wert
- `min` / `max` / `step`: Slider-Bereich
- `colorMode`: 'gradient' (rot→grün) | 'fixed' (feste Farbe)
- `color`: Farbe bei colorMode='fixed'
- `startActive`: Boolean - sofort farbig starten
- `thumbLabel`: Boolean - Thumb-Label anzeigen
- `density`: Vuetify density

**Features:**
- Initial grau, wird bei erster Interaktion farbig
- Farbverlauf: niedrig=rot, mittel=gelb, hoch=grün
- LLARS asymmetrischer Border-Radius auf Thumb
- Smooth Transition bei Farbwechsel

#### LCard - Card

Flexible Card-Komponente für Entity-Listen (Chatbots, Collections, Workspaces).

```vue
<LCard
  title="Mein Chatbot"
  subtitle="chatbot-id"
  icon="mdi-robot"
  color="#b0ca97"
  status="Aktiv"
  status-variant="success"
  :stats="[
    { icon: 'mdi-folder', value: 3, label: 'Collections' },
    { icon: 'mdi-message', value: 12, label: 'Gespräche' }
  ]"
>
  <p>Beschreibung hier</p>

  <template #tags>
    <LTag variant="info" size="sm">RAG</LTag>
  </template>

  <template #actions>
    <LBtn variant="text" size="small">Bearbeiten</LBtn>
  </template>
</LCard>
```

**Props:**
- `title` / `subtitle`: Titel und Untertitel
- `icon`: MDI Icon Name für Avatar
- `color`: Akzentfarbe (Border-Top + Avatar)
- `status` / `status-variant`: Status-Badge (LTag)
- `stats`: Array von `{ icon, value, label }` für Stats-Row
- `clickable`: Macht Card klickbar mit Hover-Effekt
- `flat`: Ohne Schatten
- `outlined`: Outline-Style statt elevated

**Slots:**
- `default`: Hauptinhalt (Beschreibung)
- `header`: Custom Header (ersetzt Standard-Header)
- `avatar`: Custom Avatar-Inhalt
- `status`: Custom Status-Badge
- `stats`: Custom Stats-Row
- `tags`: Tags/Badges unter Stats
- `actions`: Action-Buttons unten

#### LTabs - Tab Navigation

Moderne Tab-Navigation mit LLARS-Design (Primary-Hintergrund, asymmetrischer Border-Radius).

```vue
<LTabs
  v-model="activeTab"
  :tabs="[
    { value: 'chatbots', label: 'Chatbots', icon: 'mdi-robot' },
    { value: 'collections', label: 'Collections', icon: 'mdi-folder-multiple' },
    { value: 'documents', label: 'Dokumente', icon: 'mdi-file-document-multiple', badge: 5 }
  ]"
/>

<!-- Tab Content (mit v-window oder v-if) -->
<v-window v-model="activeTab">
  <v-window-item value="chatbots">...</v-window-item>
  <v-window-item value="collections">...</v-window-item>
</v-window>
```

**Props:**
- `modelValue` (v-model): Aktiver Tab-Wert
- `tabs`: Array von `{ value, label, icon?, badge? }`
- `variant`: `filled` (default) | `outlined` | `underlined`
- `grow`: Boolean - Tabs nehmen gleiche Breite ein

**Events:**
- `update:modelValue`: Bei Tab-Wechsel

#### LTooltip - Tooltip Wrapper

Universeller Tooltip-Wrapper für beliebige Elemente. Kann mit `text`-Prop oder `#content`-Slot verwendet werden.

```vue
<!-- Einfacher Text-Tooltip -->
<LTooltip text="Dies ist ein hilfreicher Hinweis">
  <v-icon>mdi-help-circle</v-icon>
</LTooltip>

<!-- Mit Position -->
<LTooltip text="Speichert das Dokument" location="top">
  <LBtn variant="primary">Speichern</LBtn>
</LTooltip>

<!-- Mit Custom Content (HTML/Komponenten) -->
<LTooltip>
  <v-chip>Status</v-chip>
  <template #content>
    <div><strong>Details:</strong></div>
    <ul><li>Item 1</li><li>Item 2</li></ul>
  </template>
</LTooltip>
```

**Props:**
- `text`: Tooltip-Text (String)
- `location`: 'top' | 'bottom' | 'start' | 'end' | 'left' | 'right' (default: 'bottom')
- `openDelay`: Verzögerung vor Anzeige in ms (default: 300)
- `closeDelay`: Verzögerung vor Ausblenden in ms (default: 0)
- `inline`: Boolean - `display: inline` statt `inline-block`

**Slots:**
- `default`: Element das den Tooltip triggert
- `content`: Custom Tooltip-Inhalt (ersetzt `text` Prop)

### CSS Custom Properties

Alle Design-Variablen sind in `llars-frontend/src/styles/global.css` definiert:

```css
:root {
  /* Farben */
  --llars-primary: #b0ca97;
  --llars-secondary: #D1BC8A;
  --llars-accent: #88c4c8;

  /* Border-Radius */
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;
  --llars-radius-xs: 6px 2px 6px 2px;

  /* Spacing */
  --llars-spacing-sm: 8px;
  --llars-spacing-md: 16px;
  --llars-spacing-lg: 24px;

  /* Shadows */
  --llars-shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --llars-shadow-md: 0 4px 8px rgba(0, 0, 0, 0.08);
}
```

### Button-Verwendung nach Kontext

| Kontext | Variant | Beispiel |
|---------|---------|----------|
| Hauptaktion | `primary` | Speichern, Erstellen, Starten |
| Sekundäre Aktion | `secondary` | Download, Export |
| Spezial/Hervorhebung | `accent` | Neuer Block, Testen |
| Destruktiv | `danger` | Löschen, Abmelden |
| Abbrechen/Schließen | `cancel` | Abbrechen, Schließen |
| Dezent | `text` | Weniger wichtige Aktionen |

### Dateien

```
llars-frontend/src/
├── styles/global.css              # CSS Custom Properties, globale Styles
├── components/common/
│   ├── LBtn.vue                   # Button Komponente
│   ├── LIconBtn.vue               # Icon Button
│   ├── LActionGroup.vue           # Action Button Group (Tabellen-Aktionen)
│   ├── LSlider.vue                # Farbverlauf-Slider (rot→grün)
│   ├── LTag.vue                   # Tag/Chip Komponente
│   ├── LCard.vue                  # Card Komponente
│   ├── LTabs.vue                  # Tab Navigation Komponente
│   └── LTooltip.vue               # Tooltip Wrapper
└── main.js                        # Globale Registrierung
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

## Datenbank-Zugriff

### MariaDB (LLARS Hauptdatenbank)

```bash
# Via Docker (empfohlen)
docker exec -it llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars

# SQL-Datei ausführen
docker cp migration.sql llars_db_service:/tmp/migration.sql
docker exec llars_db_service bash -c "mariadb -u dev_user -pdev_password_change_me database_llars < /tmp/migration.sql"

# Einzelnen SQL-Befehl ausführen
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e "SHOW TABLES;"
```

### Zugangsdaten (Development)

| Parameter | Wert |
|-----------|------|
| Host | llars_db_service (intern) / localhost:55306 (extern) |
| User | dev_user |
| Passwort | dev_password_change_me |
| Datenbank | database_llars |
| Root-Passwort | dev_root_password_change_me |

### PostgreSQL (Authentik)

```bash
docker exec -it llars_authentik_db psql -U authentik_dev -d authentik_dev
```

| Parameter | Wert |
|-----------|------|
| Host | llars_authentik_db (intern) |
| User | authentik_dev |
| Datenbank | authentik_dev |

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Ranking/Rating leer | Zeitraum prüfen (begin/end), User-Rolle prüfen (RATER vs VIEWER) |
| User nicht in DB | Login erstellt User automatisch via `get_or_create_user` |
| Auth-Fehler | `./scripts/setup_authentik.sh` |
| Crawler findet nichts | gzip-Decompression, exclude_patterns prüfen |
| DB-Migration nötig | SQL via `docker exec` ausführen (siehe Datenbank-Zugriff) |
| **502 Bad Gateway (Produktion)** | `NGINX_EXTERNAL_PORT=80` in `.env` setzen (siehe unten) |

### 502 Bad Gateway auf Produktion

**Symptom:** HTTPS via externen Reverse Proxy gibt 502 Bad Gateway, aber `curl http://localhost:55080` funktioniert.

**Ursache:** Externer Reverse Proxy (z.B. auf separatem Server) erwartet Port 80, aber LLARS nginx läuft auf Port 55080.

**Diagnose:**
```bash
# DNS prüfen - zeigt auf externen Proxy?
dig +short llars.example.com

# Server-IP prüfen
hostname -I

# Wenn unterschiedlich → externer Reverse Proxy im Einsatz

# Lokaler Test
curl -s -o /dev/null -w '%{http_code}' http://localhost:55080/  # 200 = LLARS läuft

# HTTPS Test
curl -s -I https://llars.example.com/  # 502 = Proxy kann Backend nicht erreichen
```

**Lösung:**
```bash
# Port auf 80 setzen für externen Proxy
echo 'NGINX_EXTERNAL_PORT=80' >> /var/llars/.env

# Nginx neu starten
cd /var/llars && docker compose up -d nginx-service

# Verifizieren
docker port llars_nginx_service  # Sollte "80/tcp -> 0.0.0.0:80" zeigen
```

**Hintergrund:**
- Development: `NGINX_EXTERNAL_PORT=55080` (Default) - kein Konflikt mit Host-Webserver
- Produktion mit externem Proxy: `NGINX_EXTERNAL_PORT=80` - Proxy verbindet zu Port 80

---

## Authentik - NICHT ÄNDERN!

| Invariante | Wert |
|------------|------|
| Client-IDs | llars-backend, llars-frontend |
| Flow-Slug | llars-api-authentication |
| Interner Port | 9000 |

**Bei Änderung von Client-ID/Flow-Slug:** Login bricht ab!

---

**Stand:** 31. Dezember 2025
