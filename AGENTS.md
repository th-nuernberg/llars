# LLARS - LLM Assisted Research System

**Version:** 2.6 | **Stand:** 28. November 2025

## Projekt-Übersicht

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit LLMs.

**Features:** Multi-User Collaboration (YJS CRDT) | LLM-Integration (OpenAI, LiteLLM/Mistral) | RBAC Permission System | Authentik Auth | Light/Dark Mode | RAG-Pipeline (ChromaDB) | LLM-as-Judge

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
REMOVE_VOLUMES=True ./start_llars.sh
```

### URLs (Development)

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik | http://localhost:55095 |
| Database | localhost:55306 |

### Wichtige .env Variablen

```bash
PROJECT_STATE=development|production
PROJECT_HOST=localhost
NGINX_INTERNAL_PORT=80    # MUSS 80 sein!
REMOVE_VOLUMES=False
```

---

## Architektur

**Backend:** Flask 3.0 + MariaDB 11.2 + OpenAI + ChromaDB
**Frontend:** Vue 3.4 + Vuetify 3.5 + Vite 5.1 + Socket.IO + Y.js
**Auth:** Authentik (OAuth2/OIDC, RS256 JWT)

```
nginx (:80) → Reverse Proxy
├── / → Vue Frontend (:5173)
├── /api/, /auth/ → Flask Backend (:8081)
└── /collab/ → YJS WebSocket (:8082)

Databases: MariaDB (:3306), PostgreSQL (:5432 - Authentik)
```

---

## Permission System

**Sicherheitsmodell:** Deny-by-Default | User-Permissions überschreiben Rollen | Explizites Deny schlägt Grant

### Permissions (17 total)

```
feature:mail_rating:{view,edit,delete}  feature:ranking:{view,edit}
feature:rating:{view,edit}              feature:prompt_engineering:{view,edit}
feature:comparison:{view,edit}          feature:history_generation:view
admin:{permissions,roles}:manage        admin:users:view
data:{export,import}
```

### Rollen

| Rolle | Beschreibung |
|-------|--------------|
| admin | Alle 17 Permissions |
| researcher | Alle View + Edit (11) |
| viewer | Nur View (5) |

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
GET/POST /api/judge/sessions          # Session CRUD
POST     /api/judge/sessions/<id>/start|pause
GET      /api/judge/sessions/<id>/current|queue|comparisons
GET      /api/judge/pillars           # Verfügbare Säulen
POST     /api/judge/sync              # GitLab Sync
```

### Socket.IO Events

```javascript
// Client → Server
socket.emit('judge:join_session', { session_id })

// Server → Client
socket.on('judge:progress', { session_id, status, completed, total })
socket.on('judge:llm_stream', { session_id, token })
socket.on('judge:comparison_complete', { comparison_id, winner, confidence })
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
| LLARS nicht erreichbar | `NGINX_INTERNAL_PORT=80` in .env prüfen |
| Auth-Fehler | `./scripts/setup_authentik.sh` ausführen |
| Permission-System fehlt | `docker compose restart backend-flask-service` |
| Session startet nicht | Session-Status muss created/queued/paused sein |

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
