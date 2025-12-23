# LLARS - LLM Assisted Research System

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit LLMs.

## Features

- **Multi-User Collaboration** - Echtzeit-Zusammenarbeit mit YJS CRDT (Prompt Engineering + Markdown Collab)
- **LLM-Integration** - OpenAI, LiteLLM/Mistral
- **LLM-as-Judge** - Automatisierte paarweise Vergleiche mit Live-Streaming
- **RAG-Pipeline** - Dokumenten-basierte Antworten mit ChromaDB
- **OnCoCo Analyse** - Satzbasierte Klassifikation (68 Kategorien)
- **Evaluierungstools** - Ranking, Rating, Mail Rating, Fake/Echt
- **Chatbot Builder** - Chatbots mit RAG-Integration und Web-Crawler
- **Offline Anonymisierung** - PDF/DOCX/Text pseudonymisieren
- **Markdown Collab** - Gemeinsames Schreiben mit Live-Preview
- **RBAC Permission System** - Rollenbasierte Zugriffskontrolle
- **Authentik Auth** - OAuth2/OIDC Authentifizierung
- **Matomo Analytics** - Self-hosted Tracking (Pageviews + UI Events, optional SSO via Authentik/OIDC)
- **Admin System Tools** - System Monitor, Docker Monitor & DB Explorer (live)
- **KAIMO** - Fallvignetten bearbeiten und auswerten

## Voraussetzungen

- **Docker** & **Docker Compose** ([Installation](https://docs.docker.com/get-docker/))
- **Git**

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/dein-repo/llars.git
cd llars

# 2. Umgebungsvariablen konfigurieren
cp .env.template.development .env

# 3. LLARS starten
./start_llars.sh
```

Das Skript startet alle Docker-Container und konfiguriert Authentik automatisch.

## URLs (Development)

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:55080 |
| **Backend API** | http://localhost:55080/api |
| **Authentik Admin** | http://localhost:55095 |
| **Matomo** | http://localhost:55080/analytics/ |
| **Docs (MkDocs, direkt)** | http://localhost:55800 |
| **Docs (via nginx, dev)** | http://localhost:55080/mkdocs/ |

Hinweis: Matomo ist zusätzlich unter `/matomo/` erreichbar (Alias). Das Frontend nutzt für Tracking die first-party Endpoints `/metrics.js` und `/metrics.php`. In Production wird die Doku unter `/docs/` proxied.

## Test-Benutzer

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | Administrator |
| researcher | admin123 | Researcher |
| viewer | admin123 | Viewer |

## Projektstruktur

```
llars/
├── app/                    # Flask Backend
│   ├── auth/              # Authentifizierung
│   ├── routes/            # API Endpoints
│   ├── services/          # Business Logic
│   └── db/                # Database Models
├── llars-frontend/        # Vue 3 Frontend
│   ├── src/components/    # Vue Komponenten
│   └── src/composables/   # Vue Composables
├── docker/                # Docker Konfiguration
├── scripts/               # Hilfs-Skripte
├── start_llars.sh         # Start-Skript
├── docker-compose.yml     # Docker Compose
├── CLAUDE.md              # Entwickler-Dokumentation
└── REFACTORING_TODO.md    # Offene Refactoring-Tasks
```

## Architektur

```
nginx (:80) → Reverse Proxy
├── /          → Vue Frontend (:5173)
├── /api/      → Flask Backend (:8081)
├── /auth/     → Flask Auth (delegiert an Authentik)
├── /authentik/→ Authentik UI/API (:9000)
├── /analytics/→ Matomo Analytics (:80)
└── /collab/   → YJS WebSocket (:8082)

Databases:
├── MariaDB (:3306)        → Anwendungsdaten
├── MariaDB (:3306)        → Matomo DB
├── PostgreSQL (:5432)     → Authentik
└── ChromaDB               → RAG Vektoren (lokal, /app/storage)
```

## Wichtige Befehle

```bash
# Starten
./start_llars.sh              # Development Mode
./start_llars.sh prod         # Production Mode

# Komplett-Neustart (LÖSCHT ALLE DATEN!)
REMOVE_LLARS_VOLUMES=True ./start_llars.sh

# Logs anzeigen
docker compose logs -f backend-flask-service
docker compose logs -f frontend-vue-service

# Authentik Setup
./scripts/setup_authentik.sh
./scripts/verify_authentik.sh
```

## Konfiguration

Wichtige Umgebungsvariablen in `.env`:

```bash
PROJECT_STATE=development     # oder production
PROJECT_URL=http://localhost:55080
PROJECT_HOST=localhost        # optional (wird aus PROJECT_URL abgeleitet)
NGINX_EXTERNAL_PORT=55080      # Host-Port für nginx
OPENAI_API_KEY=sk-...         # Für LLM-Features
LITELLM_API_KEY=...           # Optional für Mistral
LITELLM_BASE_URL=https://kiz1.in.ohmportal.de/llmproxy/v1
```

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| LLARS nicht erreichbar | `PROJECT_URL`/`NGINX_EXTERNAL_PORT` in .env prüfen |
| Auth-Fehler | `./scripts/setup_authentik.sh` ausführen |
| Container starten nicht | `docker compose down && ./start_llars.sh` |
| Datenbank-Fehler | `REMOVE_LLARS_VOLUMES=True ./start_llars.sh` |

## Dokumentation

- **CLAUDE.md** - Ausführliche Entwickler-Dokumentation
- **REFACTORING_TODO.md** - Offene Refactoring-Aufgaben
- **MIGRATION_ERROR_HANDLING.md** - Error-Handling Migration

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

---

**Entwickler:** Philipp Steigerwald
