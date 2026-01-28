<p align="center">
  <img src="llars-frontend/src/assets/logo/llars-logo.png" alt="LLARS Logo" width="200">
</p>

<h1 align="center">LLARS - LLM Assisted Research System</h1>

<p align="center">
  <strong>Kollaborative Bewertung von E-Mails und Szenarien mit LLMs</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-3.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/Flask-3.0-green" alt="Flask">
  <img src="https://img.shields.io/badge/Vue-3.4-brightgreen" alt="Vue">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## Features

| Kategorie | Features |
|-----------|----------|
| **Evaluation** | Ranking, Rating, Mail Rating, Fake/Echt-Erkennung |
| **LLM-as-Judge** | Automatisierte paarweise Vergleiche mit Live-Streaming |
| **RAG-Pipeline** | Dokumenten-basierte Antworten mit ChromaDB + Hybrid Search |
| **Chatbot Builder** | Chatbots mit RAG-Integration und Web-Crawler |
| **Collaboration** | Echtzeit-Zusammenarbeit mit YJS CRDT (Prompt Engineering, Markdown, LaTeX) |
| **OnCoCo Analyse** | Satzbasierte Klassifikation (68 Kategorien) |
| **Anonymisierung** | Offline PDF/DOCX/Text pseudonymisieren |
| **KAIMO** | Fallvignetten bearbeiten und auswerten |
| **Admin Tools** | System Monitor, Docker Monitor, DB Explorer (live) |
| **Auth & RBAC** | Authentik OAuth2/OIDC + rollenbasierte Zugriffskontrolle |
| **Analytics** | Matomo Self-hosted Tracking (optional SSO) |

---

## Schnellstart

### Voraussetzungen

- **Docker** & **Docker Compose** ([Installation](https://docs.docker.com/get-docker/))
- **Git**

### Installation

```bash
# 1. Repository klonen
git clone https://git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars.git
cd llars

# 2. Umgebungsvariablen konfigurieren
cp .env.template.development .env

# 3. LLARS starten
./start_llars.sh
```

Das Skript startet alle Docker-Container und konfiguriert Authentik automatisch.

---

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik Admin | http://localhost:55095 |
| Matomo Analytics | http://localhost:55080/analytics/ |
| Dokumentation | http://localhost:55080/docs/ |

---

## Test-Benutzer

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | Administrator |
| researcher | admin123 | Researcher |
| evaluator | admin123 | Evaluator |
| chatbot_manager | admin123 | Chatbot Manager |

---

## Architektur

```
nginx (:80) → Reverse Proxy
├── /           → Vue Frontend (:5173)
├── /api/       → Flask Backend (:8081)
├── /auth/      → Flask Auth → Authentik
├── /authentik/ → Authentik UI (:9000)
├── /analytics/ → Matomo (:80)
├── /collab/    → YJS WebSocket (:8082)
└── /docs/    → MkDocs (:8000)

Databases:
├── MariaDB     → Anwendungsdaten
├── PostgreSQL  → Authentik
└── ChromaDB    → RAG Vektoren
```

**Tech Stack:**
- **Backend:** Flask 3.0 + MariaDB 11.2 + ChromaDB
- **Frontend:** Vue 3.4 + Vuetify 3.5 + Vite 5.1
- **Realtime:** Socket.IO + YJS CRDT
- **Auth:** Authentik (OAuth2/OIDC, RS256 JWT)

---

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
├── yjs-server/            # YJS WebSocket Server
├── docker/                # Docker Konfiguration
├── docs/                  # MkDocs Dokumentation
├── scripts/               # Hilfs-Skripte
├── tests/                 # Backend Tests
├── start_llars.sh         # Start-Skript
├── docker-compose.yml     # Docker Compose
├── CLAUDE.md              # Entwickler-Dokumentation
└── AGENTS.md              # AI-Agent Referenz
```

---

## Wichtige Befehle

```bash
# Starten
./start_llars.sh              # Development Mode
./start_llars.sh prod         # Production Mode

# Komplett-Neustart (LÖSCHT ALLE DATEN!)
REMOVE_LLARS_VOLUMES=True ./start_llars.sh

# Logs
docker compose logs -f backend-flask-service
docker compose logs -f frontend-vue-service

# Authentik Setup
./scripts/setup_authentik.sh
./scripts/verify_authentik.sh

# Tests
pytest tests/                              # Backend
cd llars-frontend && npm run test:run      # Frontend
cd llars-frontend && npx playwright test   # E2E
```

---

## Konfiguration

Wichtige Umgebungsvariablen in `.env`:

```bash
PROJECT_STATE=development     # oder production
PROJECT_URL=http://localhost:55080
NGINX_EXTERNAL_PORT=55080
OPENAI_API_KEY=sk-...         # Für LLM-Features
LITELLM_API_KEY=...           # Optional für Mistral
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| LLARS nicht erreichbar | `PROJECT_URL`/`NGINX_EXTERNAL_PORT` in .env prüfen |
| Auth-Fehler | `./scripts/setup_authentik.sh` ausführen |
| 502 Bad Gateway (Prod) | `NGINX_EXTERNAL_PORT=80` in .env setzen |
| Container starten nicht | `docker compose down && ./start_llars.sh` |
| Datenbank-Fehler | `REMOVE_LLARS_VOLUMES=True ./start_llars.sh` |

---

## Dokumentation

| Datei | Beschreibung |
|-------|--------------|
| `CLAUDE.md` | Ausführliche Entwickler-Dokumentation |
| `AGENTS.md` | Kompakte AI-Agent Referenz |
| `docs/` | MkDocs Projektdokumentation |
| `scripts/README_AUTHENTIK_SETUP.md` | Authentik Setup Guide |

---

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

---

<p align="center">
  <strong>Entwickler:</strong> Philipp Steigerwald<br>
  <strong>Stand:</strong> Januar 2026
</p>
