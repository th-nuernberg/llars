# LLARS Frontend

Vue 3 + Vuetify 3 Single-Page Application für das LLM Assisted Research System.

## Tech Stack

| Technologie | Version | Zweck |
|-------------|---------|-------|
| Vue | 3.4 | Reactive Framework |
| Vuetify | 3.5 | Material Design UI |
| Vite | 5.1 | Build Tool |
| Socket.IO | 4.x | Echtzeit-Kommunikation |
| Y.js | 13.x | CRDT für Kollaboration |
| Pinia | 2.x | State Management |

## Projekt-Struktur

```
src/
├── components/
│   ├── Admin/              # Admin-Dashboard (Permissions, Docker, DB, Analytics)
│   ├── Anonymize/          # Offline-Anonymisierung
│   ├── Chat.vue            # Chatbot-Interface
│   ├── ChatbotOverview.vue # Chatbot-Liste
│   ├── common/             # LLARS Design System (LBtn, LTag, LCard, etc.)
│   ├── comparison/         # Feature-Vergleiche
│   ├── Home.vue            # Dashboard mit Feature-Kacheln
│   ├── Judge/              # LLM Evaluator Sessions
│   ├── MarkdownCollab/     # Kollaboratives Markdown
│   ├── OnCoCo/             # Counselor-Kondition Analyse
│   ├── PromptEngineering/  # Prompt-Entwicklung
│   ├── Rater/              # Feature-Rating
│   └── Ranker/             # Feature-Ranking
├── composables/
│   ├── useAuth.js          # Authentik OIDC
│   ├── usePermissions.js   # RBAC Permission Checks
│   ├── usePanelResize.js   # Resizable Panels
│   └── useAppTheme.js      # Light/Dark Mode
├── plugins/
│   ├── vuetify.js          # Vuetify Config + LLARS Theme
│   ├── llars-metrics.js    # Matomo Analytics
│   └── index.js            # Plugin Registry
├── services/
│   └── socketService.js    # Socket.IO Singleton
├── styles/
│   └── global.css          # CSS Custom Properties
├── views/                  # Route-spezifische Views
├── router.js               # Vue Router
└── main.js                 # App Einstieg
```

## Installation

```bash
# Dependencies installieren
npm install

# Development Server (HMR)
npm run dev

# Production Build
npm run build
```

## URLs (Development)

| Route | Beschreibung |
|-------|--------------|
| `/` | Home Dashboard |
| `/Rater` | Feature-Rating |
| `/Ranker` | Feature-Ranking |
| `/PromptEngineering` | Prompt-Entwicklung |
| `/MarkdownCollab` | Kollaboratives Markdown |
| `/Judge` | LLM Evaluator |
| `/OnCoCo` | Counselor-Kondition Analyse |
| `/Chatbots` | Chatbot-Verwaltung |
| `/Chat/:id` | Chat mit Chatbot |
| `/Anonymize` | Offline-Anonymisierung |
| `/admin` | Admin-Dashboard |

## LLARS Design System

Globale Komponenten (registriert in `main.js`):

| Komponente | Beschreibung |
|------------|--------------|
| `<LBtn>` | Button mit LLARS-Styling (variant: primary/secondary/accent/danger) |
| `<LIconBtn>` | Icon-Button |
| `<LTag>` | Tag/Chip |
| `<LCard>` | Entity-Card (Chatbots, Collections) |
| `<LTabs>` | Tab-Navigation |
| `<LSlider>` | Farbverlauf-Slider (rot→gruen) |
| `<LTooltip>` | Tooltip-Wrapper |
| `<LActionGroup>` | Tabellen-Aktionen (view/edit/delete Presets) |

### Design-Merkmale

- **Asymmetrischer Border-Radius**: `16px 4px 16px 4px`
- **Pastel-Farbpalette**: Sage Green (#b0ca97), Soft Teal (#88c4c8), etc.
- **CSS Custom Properties**: `--llars-primary`, `--llars-radius`, etc.

## Permission System

```vue
<script setup>
import { usePermissions } from '@/composables/usePermissions'
const { hasPermission, hasAnyPermission } = usePermissions()
</script>

<template>
  <LBtn v-if="hasPermission('feature:chatbots:edit')">
    Chatbot bearbeiten
  </LBtn>
</template>
```

## Authentik Integration

```javascript
import { useAuth } from '@/composables/useAuth'

const { user, isAuthenticated, login, logout, getToken } = useAuth()

// Token fuer API-Calls
const token = await getToken()
fetch('/api/endpoint', {
  headers: { Authorization: `Bearer ${token}` }
})
```

## Socket.IO Namespaces

| Namespace | Zweck |
|-----------|-------|
| `/` | Allgemein (Chat, Crawler) |
| `/admin` | Docker Monitor, DB Explorer |
| `/collab` (via nginx) | YJS Kollaboration |

## Viewport-Layout

Fullscreen-Seiten (ohne Scrolling):

```css
.page-container {
  height: calc(100vh - 94px);  /* 64px AppBar + 30px Footer */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

## Matomo Analytics

Tracking wird via `llars-metrics.js` Plugin automatisch initialisiert:

- Pageviews (SPA-Routes)
- Link-Tracking
- Click-Events (via `data-matomo-category` Attribute)
- Optional: User-ID Tracking

Elemente ausschliessen:
```html
<div data-matomo-ignore>Wird nicht getrackt</div>
```

## Environment Variables

Werden zur Build-Zeit via Vite injiziert:

```bash
VITE_API_URL=/api
VITE_MATOMO_URL=/analytics/
```

## Scripts

```bash
npm run dev      # Development mit HMR
npm run build    # Production Build
npm run preview  # Preview Production Build
npm run lint     # ESLint
```

## Referenzen

- [Vue 3](https://vuejs.org/)
- [Vuetify 3](https://vuetifyjs.com/)
- [Vite](https://vitejs.dev/)
- [Y.js](https://docs.yjs.dev/)
- [Socket.IO Client](https://socket.io/docs/v4/client-api/)
