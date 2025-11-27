# LLARS - LLM-Assisted Rating System

**Version:** 2.4 | **Stand:** 27. November 2025

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

## 🤖 Vorgehen bei komplexen Tasks (für Claude Code)

Dieses Projekt verwendet Claude Code für Entwicklungsaufgaben. Bei komplexen, mehrteiligen Aufgaben sollte folgendes Vorgehen angewendet werden:

### Schritt 1: Analyse & Parallelisierung

```
1. Problem vollständig verstehen (Logs, Code, Doku lesen)
2. Unabhängige Teilaufgaben identifizieren
3. Abhängigkeiten zwischen Tasks erkennen
4. Parallelisierbare Tasks gruppieren
```

### Schritt 2: Parallele Ausführung mit Agents

```
┌─────────────────────────────────────────────────────────────┐
│  Hauptprozess identifiziert 4 unabhängige Probleme          │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │  Agent 1    │    │  Agent 2    │    │  Agent 3    │
   │  Problem A  │    │  Problem B  │    │  Problem C  │
   └─────────────┘    └─────────────┘    └─────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Zusammenführung │
                    │  & Validierung   │
                    └─────────────────┘
```

**Vorteile:**
- Schnellere Bearbeitung durch Parallelisierung
- Jeder Agent fokussiert auf ein spezifisches Problem
- Unabhängige Fehlerbehandlung pro Task

### Schritt 3: Validierung & Iteration

```bash
# Nach Agent-Ausführung immer prüfen:
1. Existieren alle erstellten Dateien?
2. Sind die Änderungen korrekt angewendet?
3. Funktioniert das System noch?

# Bei Fehlern: Iterative Korrektur
while (!funktioniert) {
    identifiziere_problem()
    korrigiere_gezielt()
    teste_erneut()
}
```

### Schritt 4: Dokumentation

Nach erfolgreicher Umsetzung:
1. **CLAUDE.md aktualisieren** - Neue Features/Änderungen dokumentieren
2. **Version hochzählen** - Bei signifikanten Änderungen
3. **Datum aktualisieren** - Stand der Dokumentation

### Beispiel: Authentik-Problem gelöst

```
Problem: Authentik-Integration fehlerhaft (4 Teilprobleme)

Parallelisiert:
├── Agent 1: SECRET_KEY Security Fix (.env Dateien)
├── Agent 2: Auto-Init Script neu schreiben (API-basiert)
├── Agent 3: Setup-Skript erstellen (scripts/)
└── Agent 4: Healthcheck verbessern (docker-compose.yml)

Ergebnis: Alle 4 Agents parallel, dann Validierung, dann Doku
```

### Best Practices für Claude Code in LLARS

| Regel | Beschreibung |
|-------|--------------|
| **TodoWrite nutzen** | Immer Tasks tracken bei >2 Schritten |
| **Agents parallelisieren** | Unabhängige Tasks gleichzeitig starten |
| **Validieren** | Nach jeder Änderung prüfen (Dateien, Logs, Tests) |
| **Iterieren** | Bei Fehlern gezielt nachbessern |
| **Dokumentieren** | CLAUDE.md immer aktuell halten |
| **Keine Annahmen** | Immer erst lesen, dann ändern |

---

## 🚀 Projekt starten

### Erstmalige Einrichtung

```bash
# 1. Environment-Datei erstellen (einmalig)

# Fur DEVELOPMENT (lokale Entwicklung):
cp .env.template.development .env

# ODER fur PRODUCTION:
cp .env.template.production .env
# Dann .env bearbeiten und alle Secrets anpassen!

# 2. Starten
./start_llars.sh
```

### Tägliche Nutzung

```bash
# Normaler Start (nutzt .env)
./start_llars.sh

# Mode uberschreiben (temporar)
./start_llars.sh dev     # Development erzwingen
./start_llars.sh prod    # Production erzwingen
```

### Komplett-Neustart (alle Daten loschen)

```bash
# In .env setzen:
REMOVE_VOLUMES=True

# Dann starten:
./start_llars.sh

# ACHTUNG: Loscht ALLE Daten (DB, Authentik, Cache)!
# In Production wird eine Bestatigung abgefragt.

# Nach dem Start REMOVE_VOLUMES=False zurucksetzen!
```

**Das Skript:**
1. Pruft ob `.env` existiert (sonst Fehler mit Anleitung)
2. Ladt alle Variablen aus `.env`
3. Pruft Docker-Daemon (startet ggf. automatisch)
4. Stoppt alte Container
5. Bei `REMOVE_VOLUMES=True`: Loscht ALLE llars-Volumes
6. Startet Services (Development mit Hot-Reload oder Production)

### Environment Templates

| Template | Zweck | Ports |
|----------|-------|-------|
| `.env.template.development` | Lokale Entwicklung | Alle Ports exponiert (55000er Range) |
| `.env.template.production` | Server-Deployment | Nur nginx:80/443 exponiert |

### Wichtige .env Variablen

```bash
PROJECT_STATE=development        # development | production
PROJECT_HOST=localhost           # oder: llars.your-domain.de
REMOVE_VOLUMES=False             # True = ALLE DATEN WERDEN GELOSCHT!

# Ports (Development: 55000er Range)
NGINX_EXTERNAL_PORT=55080
NGINX_INTERNAL_PORT=80           # WICHTIG: Muss 80 sein!
```

### URLs nach Start (Development)

- **Frontend**: http://localhost:55080
- **Backend API**: http://localhost:55080/api
- **Health Check**: http://localhost:55080/auth/health_check
- **Authentik**: http://localhost:55095
- **Docs**: http://localhost:55800
- **Database**: localhost:55306

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
- Light: `#b0ca97` (primary - original helles Grün), `#f5f5f5` (background)
- Dark: `#5d7a4a` (primary - dunkleres Grün), `#121212` (background)

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

### ⚠️ Light Mode Textfarben - WICHTIG!

Im Light Mode MUSS Text dunkel sein für gute Lesbarkeit. Vuetify's Standard-Opacity für `text-medium-emphasis` (0.6) ist zu hell auf weißem Hintergrund.

**Globale Fixes in `App.vue`:**
```css
/* Light mode: Erhöhte Opacity für besseren Kontrast */
.v-theme--light {
  --v-medium-emphasis-opacity: 0.75;
  --v-high-emphasis-opacity: 0.95;
}

.v-theme--light .text-medium-emphasis {
  color: rgba(0, 0, 0, 0.75) !important;
}
```

**Bei Custom Styles in Komponenten:**
```css
/* FALSCH - Text unsichtbar im Light Mode */
.duration-item {
  background: rgba(var(--v-theme-surface), 0.3);
  /* Kein color definiert - erbt möglicherweise helle Farbe */
}

/* RICHTIG - Text immer lesbar */
.duration-item {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  color: rgb(var(--v-theme-on-surface));  /* Explizit dunkle Textfarbe */
}
```

**Regeln für neue Komponenten:**
1. IMMER `color: rgb(var(--v-theme-on-surface))` setzen wenn Custom Background
2. NIEMALS Text ohne explizite Farbe auf Custom Backgrounds
3. `text-medium-emphasis` Klasse nutzen für Sekundärtext (global gefixt)
4. Bei `text-caption` innerhalb Custom-Container: `color: inherit` nutzen

---

## 💀 Skeleton Loading Pattern

**Status:** ✅ Projektweiter Standard
**Composable:** `llars-frontend/src/composables/useSkeletonLoading.js`

### Regel

**ALLE Seiten und Komponenten MÜSSEN Skeleton Loading verwenden**, um ein flüssiges Ladeerlebnis zu gewährleisten. Niemals sollen Elemente "hässlich aufgebaut" werden - stattdessen werden Platzhalter (Skeletons) angezeigt, bis die Daten geladen sind.

### Prinzipien

1. **Alle Sections haben Skeletons**: Jede Sektion (Stats Cards, Tabellen, Cards) zeigt während des Ladens einen Skeleton-Loader
2. **Paralleles Laden**: Daten werden parallel geladen, Skeletons verschwinden individuell wenn Daten bereit sind
3. **Konsistente Höhen**: Skeleton-Loader haben dieselbe Höhe wie der finale Content
4. **Smooth Transitions**: Übergänge von Skeleton zu Content sind smooth animiert

### Verwendung mit Composable

```javascript
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

// Initialisiere Sections die laden sollen
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['stats', 'table', 'chart'])

// Option 1: Manuell
setLoading('stats', true)
await fetchStats()
setLoading('stats', false)

// Option 2: Mit Wrapper
await withLoading('table', async () => {
  await fetchTableData()
})
```

### Template Pattern

```vue
<!-- Stats Cards -->
<v-col cols="12" sm="6" lg="3">
  <v-skeleton-loader
    v-if="isLoading('stats')"
    type="card"
    height="100"
  ></v-skeleton-loader>
  <v-card v-else class="stat-card">
    <!-- Actual content -->
  </v-card>
</v-col>

<!-- Tabellen -->
<v-skeleton-loader
  v-if="isLoading('table')"
  type="table-heading, table-thead, table-tbody, table-tfoot"
></v-skeleton-loader>
<v-card v-else>
  <v-data-table ...></v-data-table>
</v-card>
```

### Skeleton Types (Vuetify)

| Type | Verwendung |
|------|------------|
| `card` | Stat Cards, Info Cards |
| `table-heading, table-thead, table-tbody, table-tfoot` | Vollständige Tabellen |
| `list-item@3` | Listen (3 Items) |
| `list-item-avatar@3` | Listen mit Avatars |
| `paragraph` | Textblöcke |
| `article` | Artikel-Layout |

### Beispiel: Vollständige Seite

```vue
<template>
  <v-container>
    <!-- Stats laden parallel -->
    <v-row>
      <v-col v-for="i in 4" :key="i" cols="12" sm="6" lg="3">
        <v-skeleton-loader v-if="loadingStats" type="card" height="100" />
        <v-card v-else>...</v-card>
      </v-col>
    </v-row>

    <!-- Info Card -->
    <v-skeleton-loader v-if="loadingInfo" type="card" height="150" />
    <v-card v-else>...</v-card>

    <!-- Tabelle -->
    <v-skeleton-loader
      v-if="loadingTable"
      type="table-heading, table-thead, table-tbody"
    />
    <v-card v-else>
      <v-data-table ...></v-data-table>
    </v-card>
  </v-container>
</template>

<script setup>
const loadingStats = ref(true)
const loadingInfo = ref(true)
const loadingTable = ref(true)

onMounted(async () => {
  // Parallel laden
  Promise.all([
    fetchStats().finally(() => loadingStats.value = false),
    fetchInfo().finally(() => loadingInfo.value = false),
    fetchTable().finally(() => loadingTable.value = false)
  ])
})
</script>
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

**Status:** ✅ Vollständig implementiert (ersetzt Keycloak)
**Dokumentation:** `docs/AUTHENTIK_TESTING_PLAN.md`

### 🚀 Schnellstart: Automatisches Setup

**Wenn die Authentik-Initialisierung fehlschlägt**, verwende das Setup-Skript:

```bash
# Setup-Skript ausführen (automatisch konfiguriert Authentik)
./scripts/setup_authentik.sh

# Überprüfen ob alles funktioniert
./scripts/verify_authentik.sh
```

**Dokumentation:**
- **Quick Start:** `scripts/QUICK_START.md` - Schnelle Anleitung
- **Vollständig:** `scripts/README_AUTHENTIK_SETUP.md` - Detaillierte Dokumentation
- **Übersicht:** `scripts/SETUP_SUMMARY.md` - Architektur & Komponenten
- **Index:** `scripts/INDEX.md` - Navigation durch alle Docs

Das Skript erstellt automatisch:
- ✅ Authentication Flow (`llars-api-authentication`)
- ✅ OAuth2 Providers (Backend + Frontend)
- ✅ Applications (`LLARS Backend`, `LLARS Frontend`)
- ✅ Test Users (`admin`, `akadmin`, `researcher`, `viewer`)

### Übersicht

LLARS verwendet Authentik als Identity Provider mit OAuth2/OIDC:
- **RS256 JWT-Tokens** (asymmetrische Kryptographie)
- **Flow Executor API** für headless/API Authentication
- **JWKS-basierte Token-Validierung**

### Login-Credentials

**Test-Benutzer (erstellt durch Setup-Skript):**

| Benutzername | Passwort | Rollen | Beschreibung |
|--------------|----------|--------|--------------|
| `admin` | `admin123` | user, admin | Admin-Zugang für LLARS |
| `akadmin` | `admin123` | user, admin | Admin für Authentik UI |
| `researcher` | `admin123` | user | Forscher mit Schreibzugriff |
| `viewer` | `admin123` | user | Nur Lesezugriff |

⚠️ **Wichtig:** In Production andere Passwörter verwenden!

### Authentifizierungs-Flow

```
Frontend (Vue.js)
      │
      │ POST /auth/authentik/login {username, password}
      ▼
Backend (Flask)
      │
      │ 1. Start Flow (GET /api/v3/flows/executor/llars-api-authentication/)
      │ 2. Submit Username (POST mit uid_field)
      │ 3. Submit Password (POST mit password)
      │ 4. OAuth2 Authorization Request
      │ 5. Exchange Code for Token
      ▼
Authentik (OIDC Provider)
      │
      │ RS256-signiertes JWT Token
      ▼
Backend → Frontend
      │
      │ Response: { access_token, id_token, llars_roles }
      ▼
Frontend speichert in sessionStorage:
      - auth_token
      - auth_llars_roles
```

### Authentik Setup nach Container-Neustart

Nach einem frischen Container-Start müssen folgende Komponenten in Authentik existieren:

**1. Authentication Flow** (`llars-api-authentication`)
```bash
docker compose exec -T authentik-server ak shell -c "
from authentik.flows.models import Flow, FlowStageBinding, FlowDesignation
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage

flow, created = Flow.objects.get_or_create(
    slug='llars-api-authentication',
    defaults={
        'name': 'LLARS API Authentication',
        'designation': FlowDesignation.AUTHENTICATION,
        'title': 'LLARS API Login'
    }
)
if created:
    id_stage, _ = IdentificationStage.objects.get_or_create(
        name='llars-api-identification',
        defaults={'user_fields': [UserFields.USERNAME, UserFields.E_MAIL]}
    )
    pw_stage, _ = PasswordStage.objects.get_or_create(
        name='llars-api-password',
        defaults={'backends': ['authentik.core.auth.InbuiltBackend']}
    )
    login_stage, _ = UserLoginStage.objects.get_or_create(
        name='llars-api-user-login',
        defaults={'session_duration': 'seconds=0'}
    )
    FlowStageBinding.objects.create(target=flow, stage=id_stage, order=10)
    FlowStageBinding.objects.create(target=flow, stage=pw_stage, order=20)
    FlowStageBinding.objects.create(target=flow, stage=login_stage, order=30)
"
```

**2. OAuth2 Provider** (`llars-backend`)
```bash
docker compose exec -T authentik-server ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.core.models import Application

cert = CertificateKeyPair.objects.filter(name__contains='Self-signed').first()
auth_flow = Flow.objects.get(slug='default-provider-authorization-implicit-consent')

provider, created = OAuth2Provider.objects.get_or_create(
    name='llars-backend',
    defaults={
        'client_id': 'llars-backend',
        'client_secret': 'llars-backend-secret-change-in-production',
        'client_type': 'confidential',
        'authorization_flow': auth_flow,
        'signing_key': cert,
    }
)
scopes = ScopeMapping.objects.filter(managed__startswith='goauthentik.io/providers/oauth2/scope-')
provider.property_mappings.set(scopes)
provider.save()

app, _ = Application.objects.get_or_create(
    slug='llars-backend',
    defaults={'name': 'LLARS Backend', 'provider': provider}
)
"
```

**3. User mit Passwort**
```bash
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User, Group

# Admin User erstellen
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={'name': 'Admin User', 'email': 'admin@localhost', 'is_active': True}
)
admin.set_password('admin123')
admin.save()

# Zur Admin-Gruppe hinzufügen
admin_group = Group.objects.filter(name='authentik Admins').first()
if admin_group:
    admin.ak_groups.add(admin_group)
    admin.save()
"
```

### Backend-Token-Validierung

**Datei:** `app/auth/oidc_validator.py`

```python
from app.auth.oidc_validator import validate_token, get_token_from_request

# Token validieren
token = get_token_from_request()
payload = validate_token(token)  # Returns decoded JWT or None

# User-Info extrahieren
username = payload.get('preferred_username')
groups = payload.get('groups', [])
```

### Decorators

**Datei:** `app/decorators/permission_decorator.py`

```python
from app.decorators.permission_decorator import require_permission

@data_blueprint.route('/api/protected')
@require_permission('feature:my_feature:view')
def protected_route():
    return jsonify({'message': 'Protected'})
```

### Frontend-Integration

**Token-Storage:** `sessionStorage`
- `auth_token` - Access Token (JWT)
- `auth_llars_roles` - Rollen-Array (JSON)

**Axios Interceptor:** `llars-frontend/src/main.js`
```javascript
// Auto-add Bearer Token
axios.interceptors.request.use(config => {
  const token = sessionStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-redirect on 401 (außer bei Login-Requests)
axios.interceptors.response.use(
  response => response,
  async error => {
    const isLoginRequest = error.config?.url?.includes('/auth/') &&
                           error.config?.url?.includes('/login');
    if (error.response?.status === 401 && !isLoginRequest) {
      sessionStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

**Auth Composable:** `llars-frontend/src/composables/useAuth.js`
```javascript
import { useAuth } from '@/composables/useAuth'

const auth = useAuth()
await auth.login(username, password)  // Returns { success, error }
auth.logout()
auth.isAuthenticated.value  // Boolean
auth.isAdmin.value          // Boolean
auth.userRoles.value        // Array ['user', 'admin']
```

### API-Endpoints

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/auth/authentik/login` | POST | Login mit Username/Password |
| `/auth/authentik/validate` | GET | Token validieren |
| `/auth/authentik/me` | GET | User-Info abrufen |
| `/auth/health_check` | GET | Backend Health Check |

### Troubleshooting

**"Authentication service error":**
```bash
# Flow existiert nicht - manuell erstellen (siehe oben)
docker compose logs backend-flask-service | grep -i "flow"
```

**"Invalid credentials" obwohl Passwort korrekt:**
```bash
# Prüfen ob User existiert
docker compose exec authentik-server ak shell -c "
from authentik.core.models import User
print(list(User.objects.values_list('username', flat=True)))
"
```

**Token wird nicht gespeichert:**
```javascript
// Browser Console prüfen
sessionStorage.getItem('auth_token')
sessionStorage.getItem('auth_llars_roles')
```

### ⚠️ Authentik Invarianten - NICHT ÄNDERN!

Die folgenden Konfigurationen sind **kritisch für die Stabilität** von Authentik als Auth-Provider. Änderungen können zu komplettem Auth-Ausfall führen.

#### Kritische Dateien (NIEMALS ohne Grund ändern)

| Datei | Kritische Teile | Warum |
|-------|-----------------|-------|
| `docker-compose.yml` | Authentik Service-Block (Zeilen 177-279) | Service-Abhängigkeiten, Ports, Volumes |
| `.env` | `AUTHENTIK_*` Variablen | Secrets, Client-IDs, URLs |
| `app/routes/authentik_routes.py` | Login-Flow Logik | OAuth2 Flow-Executor Protokoll |
| `app/auth/oidc_validator.py` | Token-Validierung | JWKS-basierte RS256 Validierung |
| `docker/authentik/init-authentik.py` | Provider-Namen, Client-IDs | Müssen mit .env übereinstimmen |

#### Invarianten-Checkliste

**1. Service-Namen (docker-compose.yml)**
```yaml
# DIESE NAMEN DÜRFEN NICHT GEÄNDERT WERDEN:
authentik-server      # Backend erwartet diesen Namen
authentik-worker      # Celery Worker
authentik-db          # PostgreSQL für Authentik
authentik-redis       # Redis für Sessions
```

**2. Client-IDs und Secrets**
```bash
# MÜSSEN ÜBERALL IDENTISCH SEIN:
# .env ↔ init-authentik.py ↔ authentik_routes.py

AUTHENTIK_BACKEND_CLIENT_ID=llars-backend           # NICHT ändern
AUTHENTIK_FRONTEND_CLIENT_ID=llars-frontend         # NICHT ändern
AUTHENTIK_BACKEND_CLIENT_SECRET=<secret>            # Nur in .env ändern
```

**3. Flow-Slug**
```python
# Der Flow-Name ist hardcoded im Backend:
flow_slug = 'llars-api-authentication'  # authentik_routes.py:119

# Wenn geändert, muss auch in Authentik der Flow umbenannt werden!
```

**4. Interne URLs**
```bash
# Backend → Authentik Kommunikation:
AUTHENTIK_INTERNAL_URL=http://authentik-server:9000  # Docker-intern
AUTHENTIK_ISSUER_URL=http://authentik-server:9000/application/o/llars-backend/

# NICHT auf externe URLs ändern (localhost, domain) - bricht Container-Kommunikation!
```

**5. Port-Mapping**
```yaml
# Authentik MUSS auf Port 9000 intern laufen:
AUTHENTIK_INTERNAL_PORT=9000    # Hardcoded in Healthchecks
AUTHENTIK_EXTERNAL_PORT=55095   # Kann geändert werden (nur externe Erreichbarkeit)
```

**6. Healthcheck-Endpoint**
```yaml
# Authentik Healthcheck (docker-compose.yml):
test: ["CMD-SHELL", "wget ... http://localhost:${AUTHENTIK_INTERNAL_PORT}/-/health/live/"]

# Dieser Endpoint ist Authentik-spezifisch - NICHT ändern!
```

**7. SECRET_KEY Anforderungen**
```bash
# AUTHENTIK_SECRET_KEY muss:
# - Mindestens 50 Zeichen lang sein
# - Hohe Entropie haben (base64 oder hex)
# - NIEMALS in Git committed werden
# - Bei Änderung: ALLE Authentik-Container neu starten!

# Generieren:
openssl rand -base64 64
```

#### Was passiert wenn...

| Änderung | Konsequenz | Lösung |
|----------|------------|--------|
| Client-ID geändert | Login schlägt fehl (401) | IDs in .env, init-script UND Authentik UI synchronisieren |
| Flow-Slug geändert | "Authentication service error" (503) | Flow in Authentik umbenennen oder Code zurückändern |
| SECRET_KEY < 50 Zeichen | Django Security Warning, unsichere Tokens | Neuen Key generieren, Container neu starten |
| Interner Port geändert | Healthcheck schlägt fehl, Container unhealthy | Port 9000 beibehalten |
| Service-Name geändert | Backend kann Authentik nicht erreichen | Namen zurückändern |
| Redis entfernt | Sessions funktionieren nicht, Login bricht ab | Redis ist Pflicht für Authentik |

#### Sichere Änderungen

Diese Änderungen sind **sicher** und brechen nichts:

```bash
# ✅ SICHER zu ändern:
AUTHENTIK_EXTERNAL_PORT=55095      # Externer Port (Browser-Zugriff)
AUTHENTIK_BOOTSTRAP_EMAIL=...      # Nur bei Neuinstallation relevant
AUTHENTIK_BOOTSTRAP_PASSWORD=...   # Nur bei Neuinstallation relevant
AUTHENTIK_BACKEND_CLIENT_SECRET=.. # Wenn auch in Authentik UI geändert

# ✅ Neue User hinzufügen (via Setup-Skript oder UI)
# ✅ Neue Rollen in LLARS (MariaDB) - unabhängig von Authentik
# ✅ Redirect-URIs erweitern (für neue Domains)
```

#### Authentik-Architektur verstehen

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Flask     │────▶│  Authentik  │◀────│   Vue.js    │       │
│  │  Backend    │     │   Server    │     │  Frontend   │       │
│  │  :8081      │     │   :9000     │     │   :5173     │       │
│  └─────────────┘     └──────┬──────┘     └─────────────┘       │
│         │                   │                   │               │
│         │            ┌──────┴──────┐            │               │
│         │            │             │            │               │
│         │      ┌─────▼─────┐ ┌─────▼─────┐      │               │
│         │      │ PostgreSQL│ │   Redis   │      │               │
│         │      │   :5432   │ │   :6379   │      │               │
│         │      └───────────┘ └───────────┘      │               │
│         │                                       │               │
│         └───────────────┬───────────────────────┘               │
│                         │                                       │
│                   ┌─────▼─────┐                                 │
│                   │  MariaDB  │  ← LLARS Daten (nicht Auth!)    │
│                   │   :3306   │                                 │
│                   └───────────┘                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Authentik verwaltet:        LLARS (MariaDB) verwaltet:
- User-Identitäten          - LLARS-spezifische Rollen
- Passwörter                - Permissions
- OAuth2 Tokens             - User-zu-Rollen Mapping
- Sessions (Redis)          - Audit Logs
```

#### Vor jeder Authentik-Änderung

```bash
# 1. Backup der aktuellen Konfiguration
docker compose exec authentik-server ak export_blueprint > backup_$(date +%Y%m%d).yaml

# 2. Änderung dokumentieren (was, warum, wann)

# 3. Nach Änderung testen:
./scripts/verify_authentik.sh

# 4. Bei Problemen: Rollback
docker compose down
docker compose up -d
./scripts/setup_authentik.sh  # Neu konfigurieren
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
