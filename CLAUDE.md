# LLARS - LLM-Assisted Rating System

**Version:** 2.2 | **Stand:** 25. November 2025

## 🎯 Projekt-Übersicht

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit LLMs.

**Hauptfeatures:**
- Multi-User Collaboration via YJS CRDT
- LLM-Integration (OpenAI, LiteLLM/Mistral)
- Granulares Permission System (RBAC)
- Authentik Authentication
- Light/Dark Mode
- RAG-Pipeline (ChromaDB)
- **LLM-as-Judge**: Automatisierte paarweise Bewertung von E-Mail-Threads

---

## 🚀 Projekt starten

```bash
# Schnellstart
./start_llars.sh

# Komplett-Neustart mit frischer Datenbank
# In .env setzen: REMOVE_VOLUMES=True
# Dann: ./start_llars.sh
# ACHTUNG: Löscht alle Daten!
```

**Das Skript:**
1. Prüft Docker-Daemon
2. Lädt `.env`-Variablen
3. Stoppt alte Container (bei REMOVE_VOLUMES=True werden Volumes gelöscht)
4. Startet Services (Development mit Hot-Reload oder Production)

### Wichtige .env Variablen

```bash
PROJECT_STATE=development        # development | production
PROJECT_HOST=localhost
REMOVE_VOLUMES=False            # True = Datenbanken werden gelöscht!

# Ports (Development: 55000er Range)
NGINX_EXTERNAL_PORT=55080
NGINX_INTERNAL_PORT=80          # WICHTIG: Muss 80 sein!
```

### URLs nach Start

- **Frontend**: http://localhost:55080
- **Backend API**: http://localhost:55080/api
- **Health Check**: http://localhost:55080/auth/health_check
- **YJS WebSocket**: ws://localhost:55080/collab/socket.io

---

## 🏗️ Architektur

### Tech-Stack

**Backend:** Flask 3.0 + MariaDB 11.2 + Keycloak 26.0 + OpenAI + ChromaDB
**Frontend:** Vue 3.4 + Vuetify 3.5 + Vite 5.1 + Socket.IO + Y.js
**Infrastructure:** Nginx + Docker Compose + YJS Server (Node.js 23)

### Service-Übersicht

```
nginx (Port 80) → Reverse Proxy
├── Vue Frontend (:5173)
├── Flask Backend (:8081)
├── Keycloak (:8090)
├── YJS WebSocket (:8082)
└── Supervisor Service

Databases:
├── MariaDB (:3306) - LLARS Data
└── PostgreSQL (:5432) - Keycloak
```

---

## 🔐 Berechtigungssystem

**Status:** ✅ Vollständig implementiert
**Dokumentation:** `PERMISSION_SYSTEM_STATUS.md`

### Sicherheitsmodell

- **Deny-by-Default**: Alle Features erfordern explizite Berechtigung
- **Direct Override**: User-Permissions überschreiben Rollen
- **Deny Precedence**: Explizites Deny schlägt Grant
- **Full Audit Trail**: Alle Änderungen geloggt

### Datenbank-Schema (6 Tabellen)

```sql
permissions              -- 17 verfügbare Permissions
roles                    -- 3 Rollen (admin, researcher, viewer)
role_permissions         -- Mapping: Rollen → Permissions
user_permissions         -- Direkte User-Permissions (Overrides)
user_roles               -- Mapping: User → Rollen
permission_audit_log     -- Audit Trail
```

### Verfügbare Permissions (17 total)

**Feature (12):**
```
feature:mail_rating:{view,edit,delete}
feature:ranking:{view,edit}
feature:rating:{view,edit}
feature:prompt_engineering:{view,edit}
feature:comparison:{view,edit}
feature:history_generation:view
```

**Admin (3):**
```
admin:permissions:manage
admin:roles:manage
admin:users:view
```

**Data (2):**
```
data:{export,import}
```

### Rollen

| Rolle | Permissions | Use Case |
|-------|-------------|----------|
| **admin** | Alle 17 | Vollzugriff + User-Management |
| **researcher** | 11 (alle View + Edit) | Forscher mit Schreibzugriff |
| **viewer** | 5 (nur View) | Lesezugriff |

### Backend-Nutzung

**Route schützen:**
```python
from app.decorators.permission_decorator import require_permission

@data_blueprint.route('/api/my-feature')
@require_permission('feature:my_feature:view')
def my_feature():
    return jsonify({'message': 'Protected'})
```

**Decorators:**
- `@require_permission('key')` - Genau eine Permission
- `@require_any_permission('key1', 'key2')` - OR-Logik
- `@require_all_permissions('key1', 'key2')` - AND-Logik

### Frontend-Nutzung

```vue
<script setup>
import { usePermissions } from '@/composables/usePermissions'
const { hasPermission, isAdmin } = usePermissions()
</script>

<template>
  <v-card v-if="hasPermission('feature:mail_rating:view')">
    <!-- Feature Content -->
  </v-card>
</template>
```

### Admin-Dashboard

**URL:** `/AdminPermissions` (requires `admin:permissions:manage`)

**3 Tabs:**
1. Benutzer - User suchen, Rollen zuweisen/entfernen
2. Rollen - Übersicht aller Rollen
3. Berechtigungen - Alle Permissions nach Kategorie

---

## 🎨 Theme-System

**Status:** ✅ Light/Dark Mode vollständig implementiert

### Theme-Konfiguration

**Datei:** `llars-frontend/src/config/theme.js`

**Farben:**
- Light: `#b0ca97` (primary), `#f5f5f5` (background)
- Dark: `#8fbc6b` (primary), `#121212` (background)

### Theme wechseln

**Via UserSettingsDialog:**
- Hell - Erzwingt Light Mode
- Dunkel - Erzwingt Dark Mode
- System - Folgt System-Theme automatisch

**Persistierung:** `localStorage.setItem('theme-preference', 'dark')`

**API:**
```javascript
import { useTheme } from 'vuetify'
const theme = useTheme()

theme.global.name.value = 'dark'  // Switch to dark
const isDark = theme.global.current.value.dark  // Check current
```

---

## ⚖️ LLM-as-Judge System

**Status:** ✅ Vollständig implementiert
**Dokumentation:** Diese Sektion

### Übersicht

Das LLM-as-Judge System ermöglicht automatisierte paarweise Vergleiche von E-Mail-Konversationen aus verschiedenen Datenquellen (Säulen). Ein LLM bewertet, welche Antwort qualitativ besser ist.

### Architektur

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Vue Frontend   │────▶│  Flask Backend  │────▶│  LiteLLM Proxy  │
│  JudgeSession   │     │  JudgeRoutes    │     │  Mistral Model  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │ Socket.IO             │
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Live Updates   │     │  Judge Worker   │
│  judge:*        │◀────│  Background     │
└─────────────────┘     └─────────────────┘
```

### Datenquellen (5 Säulen)

| Säule | Name | GitLab-Pfad |
|-------|------|-------------|
| 1 | Rollenspiele | `data/saeule_1/raw/json` |
| 2 | Feature (deaktiviert) | - |
| 3 | Anonymisierte Daten | `data/saeule_3/raw/json` |
| 4 | Synthetisch (deaktiviert) | - |
| 5 | Live-Testungen | `data/saeule_5/raw/json` |

**GitLab Repository:** `git.informatik.fh-nuernberg.de/e-beratung/kia/kia-data`

### LLM-Konfiguration

```bash
# .env
LITELLM_API_KEY=sk-...
LITELLM_BASE_URL=https://kiz1.in.ohmportal.de/llmproxy/v1

# Modell (in JudgeService)
mistralai/Mistral-Small-3.2-24B-Instruct-2506
```

### Datenbank-Schema

```sql
-- Säulen-Management
pillar_threads           -- E-Mail-Threads pro Säule
pillar_statistics        -- Statistiken (win_rate, elo_score)

-- Session-Management
judge_sessions           -- Evaluations-Sessions
judge_comparisons        -- Einzelne Vergleiche (A vs B)
judge_evaluations        -- LLM-Bewertungsergebnisse
```

**Session-Status:** `created` → `queued` → `running` → `completed/failed/paused`

### Backend-API (app/routes/judge/judge_routes.py)

```python
# Sessions
GET  /api/judge/sessions           # Alle Sessions auflisten
POST /api/judge/sessions           # Neue Session erstellen
GET  /api/judge/sessions/<id>      # Session-Details

# Session-Control
POST /api/judge/sessions/<id>/start   # Session starten
POST /api/judge/sessions/<id>/pause   # Session pausieren

# Live-Daten
GET  /api/judge/sessions/<id>/current      # Aktuelle Comparison
GET  /api/judge/sessions/<id>/queue        # Warteschlange
GET  /api/judge/sessions/<id>/comparisons  # Abgeschlossene

# KIA Sync
GET  /api/judge/pillars            # Verfügbare Säulen
POST /api/judge/sync               # Sync von GitLab
```

**Permissions:**
- `feature:comparison:view` - Lesen
- `feature:comparison:edit` - Erstellen/Starten

### Socket.IO Events (Live Updates)

**Client → Server:**
```javascript
socket.emit('judge:join_session', { session_id: 123 });
socket.emit('judge:leave_session', { session_id: 123 });
socket.emit('judge:get_status', { session_id: 123 });
```

**Server → Client:**
```javascript
socket.on('judge:joined', (data) => { /* Room beigetreten */ });
socket.on('judge:progress', (data) => {
  // { session_id, status, completed, total }
});
socket.on('judge:comparison_start', (data) => {
  // { session_id, comparison_id, pillar_a, pillar_b }
});
socket.on('judge:llm_stream', (data) => {
  // { session_id, token } - Live LLM Output
});
socket.on('judge:comparison_complete', (data) => {
  // { session_id, comparison_id, winner, confidence }
});
socket.on('judge:session_complete', (data) => {
  // { session_id, status }
});
```

### Frontend-Komponenten

```
llars-frontend/src/components/Judge/
├── JudgeOverview.vue    # Session-Liste
├── JudgeConfig.vue      # Session erstellen
├── JudgeSession.vue     # Live-Ansicht + Queue
└── JudgeResults.vue     # Ergebnisübersicht
```

### Services & Worker

**KIA Sync Service:** `app/services/judge/kia_sync_service.py`
```python
# Holt Threads aus GitLab
service = KIASyncService()
threads = service.sync_pillar(pillar_id=1)
```

**Judge Service:** `app/services/judge/judge_service.py`
```python
# Führt LLM-Bewertung durch
service = JudgeService()
result = service.evaluate_comparison(comparison_id)
# → { winner: 'A', confidence: 0.85, reasoning: '...' }
```

**Judge Worker:** `app/workers/judge_worker.py`
```python
# Background-Worker für async Evaluations
# Sendet Socket.IO Events für Live Updates
```

### Troubleshooting

**GitLab Token 401:**
```bash
# Nach Token-Update in .env:
docker compose up -d --force-recreate backend-flask-service
```

**Session startet nicht:**
```bash
# Session-Status prüfen (muss created/queued/paused sein)
curl http://localhost:55080/api/judge/sessions/123
```

**Keine Live-Updates:**
```javascript
// Browser Console: Socket verbunden?
// Sollte zeigen: "[Judge Socket] Connected"
// und: "[Judge Socket] Joined session room: ..."
```

---

## 🔐 Authentik-Integration

**Status:** ✅ Implementiert (ersetzt Keycloak)

**Clients:**
- `llars-frontend` (Public) - Frontend Auth
- `llars-backend` (Confidential) - Backend Service Account

**Authentik-Rollen:**
- `admin` - Admin-Dashboard-Zugriff
- `rater` - Basis-Rolle
- `viewer` - Lesezugriff

**Hinweis:** Granulare Feature-Control läuft über Permission-System.

### Backend-Token-Validierung

**Datei:** `app/auth/authentik_validator.py`

```python
def validate_authentik_token(token: str):
    """Validiert Authentik JWT-Token"""
    # RS256 JWT Validation gegen Authentik JWKS
```

### Decorators

```python
@authentik_required  # Token muss valide sein
@admin_required      # Admin-Rolle erforderlich
```

### Frontend-Integration

**Axios Interceptor:**
```javascript
// Auto-add Bearer Token
axios.interceptors.request.use(config => {
  const token = sessionStorage.getItem('kc_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-refresh on 401
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

---

## 🚀 Services

### 1. Nginx (Port 80 intern, 55080 extern)

**WICHTIG:** `NGINX_INTERNAL_PORT=80` in `.env` setzen!

**Routing:**
- `/` → Vue Frontend
- `/api/` → Flask Backend
- `/auth/` → Flask Backend
- `/collab/` → YJS WebSocket

### 2. Flask Backend (Port 8081)

**Hauptfunktionen:**
- REST API (CRUD)
- Keycloak-Token-Validierung
- Permission-System
- LLM-Integration (OpenAI)
- RAG-Pipeline (ChromaDB)

**API-Routen:**
```python
# Auth
/auth/keycloak/me          GET   @keycloak_required
/auth/keycloak/validate    GET   Token-Validierung

# Permissions
/api/permissions/*         GET   Permission-System API

# Data
/api/scenarios             GET   @admin_required
/api/ratings              GET   @keycloak_required
/api/rankings             GET   @keycloak_required
```

**Rate Limiting:**
- Default: 200/Tag, 50/Stunde
- Auth-Endpoints: Spezielle Limits

### 3. Vue.js Frontend (Port 5173)

**Hauptkomponenten:**
- `Login.vue` - Keycloak-Login
- `Home.vue` - Permission-filtered Dashboard
- `AdminPermissions.vue` - Permission-Management
- `UserSettingsDialog.vue` - Theme & Settings
- `PromptEngineering.vue` - Kollaborativer Editor

### 4. YJS WebSocket Server (Port 8082)

**Features:**
- JWT-Authentifizierung
- Y.js CRDT (konfliktfreie Sync)
- Cursor-Tracking
- Auto-Save zu MariaDB

### 5. MariaDB (Port 3306)

**Wichtige Tabellen:**
- `rating_scenarios` - Bewertungsszenarien
- `mail_ratings` - Mail-Bewertungen
- `user_prompts` - YJS-Dokumente
- `rankings` - Rankings
- Permission-System (6 Tabellen)

---

## 🔒 Sicherheit

### Implementiert ✅

**Auth & Authorization:**
- Keycloak OpenID Connect (RS256 JWT)
- Token-Signatur + Expiration
- RBAC (Keycloak) + Permission-System
- WebSocket JWT-Auth

**API-Schutz:**
- `@keycloak_required` auf allen Routes
- `@require_permission()` für Features
- Rate Limiting (Flask-Limiter)
- CORS-Konfiguration

**Production:**
- Debug-Modus nur in Development
- Secrets in `.env`
- Docker Port-Isolation
- Non-Root Container Users

**Frontend:**
- Token Auto-Refresh
- XSS-Schutz (DOMPurify)
- Permission-Based UI

### Noch zu tun ⚠️

1. SSL/TLS (Let's Encrypt)
2. Secrets Management (Vault)
3. Security Headers (CSP, X-Frame-Options)

---

## 💻 Entwicklung

### Setup

```bash
git clone <repository-url>
cd llars
cp .env.example .env
./start_llars.sh
```

### Hot-Reload

- Frontend: Vite Watch-Mode
- Backend: Flask Debug Auto-Reload
- YJS: Nodemon Auto-Restart

### Testing

```bash
# Backend
docker compose exec backend-flask-service pytest

# Frontend
cd llars-frontend && npm run test
```

---

## 🚀 Deployment

### Production Checklist

- [ ] `.env` Secrets ändern
- [ ] `PROJECT_STATE=production`
- [ ] `FLASK_ENV=production`
- [ ] SSL/TLS-Zertifikate konfigurieren
- [ ] Rate Limiting auf Redis umstellen
- [ ] Backup-Strategie einrichten
- [ ] Monitoring einrichten

```bash
./start_llars.sh  # Nutzt PROJECT_STATE aus .env
docker compose logs -f
```

---

## 📚 API-Dokumentation

### Authentifizierung

```bash
# Token holen (Testing)
curl -X POST http://localhost:55090/realms/llars/protocol/openid-connect/token \
  -d "client_id=llars-frontend" \
  -d "username=admin" \
  -d "password=admin123" \
  -d "grant_type=password"

# API-Call mit Token
curl http://localhost:55080/api/permissions/my-permissions \
  -H "Authorization: Bearer <token>"
```

### Permission API

```bash
# My permissions
GET /api/permissions/my-permissions

# All permissions (admin)
GET /api/permissions

# User permissions (admin)
GET /api/permissions/user/<username>

# Assign role (admin)
POST /api/permissions/assign-role
Body: {"username": "user123", "role_name": "researcher"}
```

---

## 🐛 Troubleshooting

### LLars nicht erreichbar

```bash
# .env prüfen:
NGINX_INTERNAL_PORT=80  # MUSS 80 sein!

docker compose down && docker compose up -d --build
```

### Keycloak startet nicht

```bash
docker compose logs keycloak-service
# Häufig: PostgreSQL nicht bereit oder Port 8090 belegt
```

### Permission-System nicht initialisiert

```bash
docker compose logs backend-flask-service | grep -i permission
# Erwartete Ausgabe: "Permission system initialized successfully"

docker compose restart backend-flask-service
```

---

## 📝 Wichtige Dateien

```
llars/
├── app/                              # Flask Backend
│   ├── auth/
│   │   ├── authentik_validator.py    # Authentik JWT Validation
│   │   └── decorators.py
│   ├── services/
│   │   ├── permission_service.py     # Permission Logic
│   │   └── judge/                    # LLM-as-Judge Services
│   │       ├── judge_service.py      # LLM Evaluation
│   │       └── kia_sync_service.py   # GitLab Data Sync
│   ├── workers/
│   │   └── judge_worker.py           # Background Evaluation Worker
│   ├── socketio_handlers/
│   │   └── events_judge.py           # Judge Socket.IO Events
│   ├── decorators/
│   │   └── permission_decorator.py   # Route Protection
│   ├── routes/
│   │   ├── PermissionRoutes.py       # Permission API
│   │   ├── rag/RAGRoutes.py          # RAG-Pipeline API
│   │   └── judge/judge_routes.py     # LLM-as-Judge API
│   └── db/
│       ├── tables.py                 # Permission + Judge Tabellen
│       └── db.py                     # initialize_permissions()
├── llars-frontend/
│   └── src/
│       ├── components/
│       │   ├── AdminPermissions.vue
│       │   ├── UserSettingsDialog.vue
│       │   └── Judge/                # LLM-as-Judge Views
│       │       ├── JudgeOverview.vue
│       │       ├── JudgeConfig.vue
│       │       ├── JudgeSession.vue
│       │       └── JudgeResults.vue
│       ├── composables/
│       │   └── usePermissions.js
│       └── config/
│           └── theme.js
├── yjs-server/
│   ├── auth.js                       # JWT Validation
│   └── websocket.js
├── docker-compose.yml
├── start_llars.sh
└── .env
```

---

## 🔄 Status

**Stand: 25. November 2025**

### ✅ Abgeschlossen

- Authentik-Integration (100%)
- Permission-System (100%)
- Theme-System (100%)
- Security-Härtung (85%)
- API-Schutz (100%)
- LLM-as-Judge System (100%)
- RAG-Pipeline (100%)

### ⚠️ In Arbeit

- SSL/TLS (0%)
- MkDocs Dokumentation (95%)

### 📋 Nächste Schritte

1. Production SSL-Setup
2. Secrets Management (Vault)
3. Enhanced Monitoring (Prometheus/Grafana)

---

**Entwickler:** Philipp Steigerwald
**Hauptdokumentation:** CLAUDE.md
**Permission System:** PERMISSION_SYSTEM_STATUS.md
