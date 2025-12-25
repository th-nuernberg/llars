# LLARS - LLM Assisted Research System

**Version:** 2.6 | **Stand:** 28. November 2025

## Projekt-Übersicht

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit LLMs.

**Features:** Multi-User Collaboration (YJS CRDT) | LLM-Integration (OpenAI, LiteLLM/Mistral) | LLM-as-Judge | OnCoCo Analyse | RAG-Pipeline (ChromaDB) | Chatbot Builder + RAG | Markdown Collab | Offline Anonymisierung | RBAC Permission System | Authentik Auth | Matomo Analytics | Admin System Tools | KAIMO

---

## Claude Code Workflow

### Komplexe Tasks parallelisieren

```
1. Problem analysieren → Unabhängige Teilaufgaben identifizieren
2. Agents parallel starten für unabhängige Probleme
3. Nach Ausführung validieren: Dateien existieren? Änderungen korrekt? System funktioniert?
4. Bei Fehlern: Iterativ korrigieren
5. CLAUDE.md aktualisieren bei signifikanten Änderungen
```

### Best Practices

| Regel | Beschreibung |
|-------|--------------|
| TodoWrite nutzen | Tasks tracken bei >2 Schritten |
| Agents parallelisieren | Unabhängige Tasks gleichzeitig |
| Validieren | Nach jeder Änderung prüfen |
| Keine Annahmen | Erst lesen, dann ändern |

---

## Projekt starten

```bash
# Ersteinrichtung
cp .env.template.development .env  # oder .env.template.production
./start_llars.sh

# Täglicher Start
./start_llars.sh              # Nutzt .env
./start_llars.sh dev|prod     # Mode überschreiben

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
| Docs (direkt) | http://localhost:55800 |
| Docs (via nginx, dev) | http://localhost:55080/mkdocs/ |
| Database | localhost:55306 |

### Wichtige .env Variablen

```bash
PROJECT_STATE=development|production
PROJECT_URL=http://localhost:55080
PROJECT_HOST=localhost            # optional (wird aus PROJECT_URL abgeleitet)
NGINX_EXTERNAL_PORT=55080          # Host-Port für nginx
REMOVE_LLARS_VOLUMES=False
```

---

## Architektur

**Backend:** Flask 3.0 + MariaDB 11.2 + OpenAI + ChromaDB
**Frontend:** Vue 3.4 + Vuetify 3.5 + Vite 5.1 + Socket.IO + Y.js
**Auth:** Authentik (OAuth2/OIDC, RS256 JWT)

```
nginx (:80) → Reverse Proxy
├── / → Vue Frontend (:5173)
├── /api/ → Flask Backend (:8081)
├── /auth/ → Flask Auth (delegiert an Authentik)
├── /authentik/ → Authentik UI/API (:9000)
├── /analytics/ → Matomo (:80)
├── /mkdocs/ (dev) | /docs/ (prod) → MkDocs (:8000)
└── /collab/ → YJS WebSocket (:8082)

Databases: MariaDB (:3306), MariaDB (Matomo, :3306), PostgreSQL (:5432 - Authentik)
```

---

## Permission System

**Sicherheitsmodell:** Deny-by-Default | User-Permissions überschreiben Rollen | Explizites Deny schlägt Grant

### Permissions (40 total)

```
feature:mail_rating:{view,edit}
feature:ranking:{view,edit}
feature:rating:{view,edit}
feature:comparison:{view,edit}
feature:authenticity:{view,edit}
feature:prompt_engineering:{view,edit}
feature:markdown_collab:{view,edit,share}
feature:rag:{view,edit,delete,share}
feature:chatbots:{view,edit,delete,advanced,share}
feature:anonymize:view
feature:judge:{view,edit}
feature:oncoco:{view,edit}
feature:kaimo:{view,edit}
admin:permissions:manage
admin:users:manage
admin:roles:manage
admin:system:configure
admin:kaimo:{manage,results}
data:{export,import,delete}
```

### Rollen

| Rolle | Beschreibung |
|-------|--------------|
| admin | Alle 40 Permissions |
| researcher | Evaluierung + Prompt Engineering + Markdown Collab + Anonymisierung + KAIMO (19) |
| chatbot_manager | Chatbot + RAG + Prompt Engineering + Markdown Collab (14) |
| viewer | Lesezugriff + ausgewählte Edit-Rechte (13) |

### Backend-Nutzung

```python
from app.decorators.permission_decorator import require_permission

@route('/api/feature')
@require_permission('feature:my_feature:view')
def my_feature(): ...

# Weitere: @require_any_permission(), @require_all_permissions()
```

### Frontend-Nutzung

```vue
<script setup>
import { usePermissions } from '@/composables/usePermissions'
const { hasPermission, isAdmin } = usePermissions()
</script>
<template>
  <v-card v-if="hasPermission('feature:mail_rating:view')">...</v-card>
</template>
```

---

## Theme System

**Config:** `llars-frontend/src/config/theme.js`
**Speicherung:** `localStorage.setItem('theme-preference', 'dark')`

### Light Mode Textfarben - WICHTIG!

Bei Custom Backgrounds IMMER explizite Textfarbe setzen:

```css
/* RICHTIG */
.custom-element {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  color: rgb(var(--v-theme-on-surface));
}
```

---

## Skeleton Loading

**Composable:** `llars-frontend/src/composables/useSkeletonLoading.js`

**Regel:** ALLE Seiten MÜSSEN Skeleton Loading verwenden.

```javascript
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['stats', 'table'])
await withLoading('table', async () => await fetchData())
```

```vue
<v-skeleton-loader v-if="isLoading('stats')" type="card" height="100" />
<v-card v-else>...</v-card>
```

---

## LLM-as-Judge System

Automatisierte paarweise Vergleiche von E-Mail-Konversationen aus 5 Säulen (GitLab: `kia-data`).

### API Endpoints

```
GET      /api/judge/comparison-modes          # Vergleichsmodi
POST     /api/judge/estimate                  # Vergleichs-Estimate
GET/POST /api/judge/sessions                  # Session CRUD
GET      /api/judge/sessions/<id>             # Session Details
POST     /api/judge/sessions/<id>/start|pause|resume
GET      /api/judge/sessions/<id>/current|queue|comparisons
GET      /api/judge/sessions/<id>/results
GET      /api/judge/sessions/<id>/verbosity-analysis
GET      /api/judge/sessions/<id>/thread-performance
GET      /api/judge/sessions/<id>/position-swap-analysis
GET      /api/judge/sessions/<id>/export/csv|export/json
GET      /api/judge/pillars
GET      /api/judge/pillars/<n>/threads
POST     /api/judge/pillars/<n>/assign
GET      /api/judge/kia/status|check|config
POST     /api/judge/kia/sync
POST     /api/judge/kia/sync/<n>
POST     /api/judge/kia/config
```

### Socket.IO Events

```javascript
// Client → Server
socket.emit('judge:join_session', { session_id })
socket.emit('judge:leave_session', { session_id })
socket.emit('judge:join_overview')
socket.emit('judge:leave_overview')
socket.emit('judge:get_status', { session_id })

// Server → Client
socket.on('judge:joined', { session_id, room })
socket.on('judge:left', { session_id, room })
socket.on('judge:overview_joined', { room })
socket.on('judge:error', { message })
socket.on('judge:status', { session_id, status, completed, total, progress })
socket.on('judge:comparison_start', { session_id, comparison_id, worker_id })
socket.on('judge:progress', { session_id, status, completed, total })
socket.on('judge:llm_stream', { session_id, token })
socket.on('judge:comparison_complete', { comparison_id, winner, confidence })
socket.on('judge:session_complete', { session_id, total, completed })
```

---

## Authentik Integration

### Setup

```bash
./scripts/setup_authentik.sh    # Automatisches Setup
./scripts/verify_authentik.sh   # Verifizieren
```

### Test-Benutzer

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| viewer | admin123 | viewer |

### Token-Validierung (Backend)

```python
from app.auth.oidc_validator import validate_token, get_token_from_request
payload = validate_token(get_token_from_request())
```

### Frontend

```javascript
import { useAuth } from '@/composables/useAuth'
const auth = useAuth()
await auth.login(username, password)
// Token in sessionStorage: auth_token, auth_llars_roles
```

### ⚠️ Authentik Invarianten - NICHT ÄNDERN!

| Invariante | Wert |
|------------|------|
| Service-Namen | authentik-server, authentik-worker, authentik-db, authentik-redis |
| Client-IDs | llars-backend, llars-frontend |
| Flow-Slug | llars-api-authentication |
| Interner Port | 9000 |
| SECRET_KEY | ≥50 Zeichen, nie committen |

**Bei Änderung von Client-ID/Flow-Slug:** Login bricht komplett ab!

---

## Git Commits

**Format:** Conventional Commits

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Types:** feat | fix | docs | refactor | style | test | chore | security | perf
**Scopes:** frontend | backend | auth | judge | rag | chatbot | crawler | db | docker

**Nicht committen:** .env, *.pem, *.safetensors, *.bin, __pycache__/, node_modules/

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| LLARS nicht erreichbar | `NGINX_EXTERNAL_PORT` in .env prüfen |
| Auth-Fehler | `./scripts/setup_authentik.sh` ausführen |
| Permission-System fehlt | `docker compose restart backend-flask-service` |
| Session startet nicht | Session-Status muss created/queued/paused sein |
| **502 Bad Gateway (Produktion)** | `NGINX_EXTERNAL_PORT=80` in `.env` setzen |

### 502 Bad Gateway auf Produktion

**Symptom:** HTTPS via externen Reverse Proxy gibt 502 Bad Gateway, aber lokal funktioniert alles.

**Ursache:** Externer Reverse Proxy erwartet Port 80, aber LLARS nginx läuft auf Default-Port 55080.

**Diagnose:**
```bash
# DNS zeigt auf anderen Server als LLARS?
dig +short llars.example.com    # Externer Proxy IP
hostname -I                      # LLARS Server IP
# Wenn unterschiedlich → externer Reverse Proxy

# Lokal OK?
curl -s -o /dev/null -w '%{http_code}' http://localhost:55080/  # 200 = LLARS läuft

# HTTPS fehlerhaft?
curl -s -I https://llars.example.com/  # 502 = Proxy erreicht Backend nicht
```

**Lösung:**
```bash
# Port 80 für externen Proxy setzen
echo 'NGINX_EXTERNAL_PORT=80' >> /var/llars/.env
cd /var/llars && docker compose up -d nginx-service

# Verifizieren
docker port llars_nginx_service  # → "80/tcp -> 0.0.0.0:80"
```

**Port-Konfiguration:**
| Umgebung | NGINX_EXTERNAL_PORT | Grund |
|----------|---------------------|-------|
| Development | 55080 (Default) | Kein Konflikt mit Host-Webserver |
| Produktion (direkt) | 80 oder 443 | Direkter Zugriff |
| Produktion (ext. Proxy) | 80 | Proxy verbindet zu Port 80 |

---

## Wichtige Dateien

```
app/
├── auth/oidc_validator.py         # JWT Validation
├── decorators/permission_decorator.py
├── services/
│   ├── permission_service.py
│   └── judge/                     # LLM-as-Judge
├── routes/
│   ├── judge/judge_routes.py
│   └── rag/RAGRoutes.py
└── db/tables.py                   # Alle Models

llars-frontend/src/
├── composables/
│   ├── usePermissions.js
│   └── useAuth.js
├── components/Judge/
└── config/theme.js
```

---

## Status

**Stand:** 28. November 2025

| Feature | Status |
|---------|--------|
| Authentik-Integration | ✅ 100% |
| Permission-System | ✅ 100% |
| LLM-as-Judge | ✅ 100% |
| RAG-Pipeline | ✅ 100% |
| Theme-System | ✅ 100% |
| SSL/TLS | ⚠️ 0% |

---

**Entwickler:** Philipp Steigerwald
