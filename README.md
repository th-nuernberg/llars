# LLARS - LLM Assisted Research System

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit LLMs.

## Features

- **Multi-User Collaboration** - Echtzeit-Zusammenarbeit mit YJS CRDT
- **LLM-Integration** - OpenAI, LiteLLM/Mistral
- **LLM-as-Judge** - Automatisierte paarweise Vergleiche
- **RAG-Pipeline** - Dokumenten-basierte Antworten mit ChromaDB
- **RBAC Permission System** - Rollenbasierte Zugriffskontrolle
- **Authentik Auth** - OAuth2/OIDC Authentifizierung
- **Matomo Analytics** - Self-hosted Tracking (Pageviews + UI Events, optional SSO via Authentik/OIDC)
- **Chatbot Builder** - Chatbots mit RAG-Integration erstellen

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
| **Matomo** | http://localhost:55080/matomo/ |

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
├── /auth/     → Flask Auth (:8081)
├── /matomo/   → Matomo Analytics (:80)
└── /collab/   → YJS WebSocket (:8082)

Databases:
├── MariaDB (:3306)        → Anwendungsdaten
├── MariaDB (:3306)        → Matomo
├── PostgreSQL (:5432)     → Authentik
└── ChromaDB               → RAG Vektoren
```

## Wichtige Befehle

```bash
# Starten
./start_llars.sh              # Development Mode
./start_llars.sh prod         # Production Mode

# Komplett-Neustart (LÖSCHT ALLE DATEN!)
REMOVE_VOLUMES=True ./start_llars.sh

# Logs anzeigen
docker compose logs -f backend-flask-service
docker compose logs -f frontend-vite-service

# Authentik Setup
./scripts/setup_authentik.sh
./scripts/verify_authentik.sh
```

## Konfiguration

Wichtige Umgebungsvariablen in `.env`:

```bash
PROJECT_STATE=development     # oder production
PROJECT_HOST=localhost
NGINX_INTERNAL_PORT=80        # MUSS 80 sein!
OPENAI_API_KEY=sk-...         # Für LLM-Features
LITELLM_API_KEY=...           # Optional für Mistral
```

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| LLARS nicht erreichbar | `NGINX_INTERNAL_PORT=80` in .env prüfen |
| Auth-Fehler | `./scripts/setup_authentik.sh` ausführen |
| Container starten nicht | `docker compose down && ./start_llars.sh` |
| Datenbank-Fehler | `REMOVE_VOLUMES=True ./start_llars.sh` |

## Dokumentation

- **CLAUDE.md** - Ausführliche Entwickler-Dokumentation
- **REFACTORING_TODO.md** - Offene Refactoring-Aufgaben
- **MIGRATION_ERROR_HANDLING.md** - Error-Handling Migration

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

---

**Entwickler:** Philipp Steigerwald
