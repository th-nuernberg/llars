# LLARS - LLM Assisted Research System

**Version:** 2.9 | **Stand:** 19. Dezember 2025

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
REMOVE_VOLUMES=True ./start_llars.sh
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
- Ressourcen: SQLite/Reco liegen in `app/`, das große Flair-NER Modell wird via Docker Compose aus `docs/docs/projekte/anonymize/models/ner-german-large` gemountet

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
    RATER: Sieht nur zugewiesene Threads (via ScenarioThreadDistribution)

    Zeitprüfung: RatingScenarios.begin <= NOW <= RatingScenarios.end
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

### Embedding Model

```
Model: llamaindex/vdr-2b-multi-v1 (1024 Dimensionen)
Storage: ChromaDB in /app/chroma_db
```

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
│   └── LTabs.vue                  # Tab Navigation Komponente
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

---

## Authentik - NICHT ÄNDERN!

| Invariante | Wert |
|------------|------|
| Client-IDs | llars-backend, llars-frontend |
| Flow-Slug | llars-api-authentication |
| Interner Port | 9000 |

**Bei Änderung von Client-ID/Flow-Slug:** Login bricht ab!

---

**Stand:** 11. Dezember 2025
