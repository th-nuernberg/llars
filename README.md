<p align="center">
  <img src="llars-frontend/src/assets/logo/llars-logo.png" alt="LLARS Logo" width="200">
</p>

<h1 align="center">LLARS - LLM Assisted Research System</h1>

<p align="center">
  <strong>An open-source platform for collaborative prompt engineering, batch generation and hybrid evaluation of LLM outputs</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-3.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/Flask-3.0-green" alt="Flask">
  <img src="https://img.shields.io/badge/Vue-3.4-brightgreen" alt="Vue">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

<p align="center">
  <a href="https://llars.e-beratungsinstitut.de"><strong>Live Instance</strong></a> &middot;
  <a href="https://youtu.be/FdG1nJ7OqE0"><strong>Demo Video</strong></a> &middot;
  <a href="Paper/ijcai26.pdf"><strong>Paper (IJCAI 2026)</strong></a>
</p>

---

## About

LLARS bridges the gap between domain experts and developers for building LLM-based systems. It integrates three tightly connected modules into an end-to-end pipeline:

1. **Collaborative Prompt Engineering** — Real-time co-authoring with version control and instant LLM testing
2. **Batch Generation** — Configurable output production across user-selected prompts x models x data with cost control
3. **Hybrid Evaluation** — Human and LLM evaluators jointly assess outputs through diverse assessment methods, with live agreement metrics and provenance analysis

New prompts and models are automatically available for batch generation, and completed batches can be turned into evaluation scenarios with a single click.

> **Paper:** *LLARS: An Open-Source Platform for Collaborative Prompt Engineering, Batch Generation and Hybrid Evaluation* — IJCAI-ECAI 2026 (Demo Track). The demo video link can be found in the footnote of the "Demo and Conclusion" section at the bottom of the paper.

---

## Live Instance & Demo Video

| | Link |
|---|---|
| **Live Instance** | https://llars.e-beratungsinstitut.de |
| **Demo Video (YouTube)** | https://youtu.be/FdG1nJ7OqE0 |
| **Paper** | Included in this repository (`Paper/ijcai26.pdf`) |

---

## Features

| Category | Features |
|----------|----------|
| **Prompt Engineering** | Real-time collaborative editing (YJS CRDT), version control, instant LLM testing |
| **Batch Generation** | Multi-model x multi-prompt x multi-data generation with cost control |
| **Evaluation** | Rating, Ranking, Pairwise Comparison, Labeling, Authenticity Detection |
| **LLM Evaluator** | Automated evaluation using LLMs as judges with configurable metrics |
| **Agreement Metrics** | Krippendorff's Alpha, agreement heatmaps, provenance analysis |
| **RAG Pipeline** | Document-based retrieval with ChromaDB + hybrid search |
| **Chatbot Builder** | Chatbots with RAG integration and web crawler |
| **Scenario Wizard** | AI-assisted evaluation scenario setup from uploaded data (CSV, JSON, JSONL) |
| **Auth & RBAC** | Authentik OAuth2/OIDC + role-based access control |
| **Design System** | 35+ custom L-components with LLARS signature styling |

---

## Quick Start

### Prerequisites

- **Docker** & **Docker Compose** ([Install](https://docs.docker.com/get-docker/))
- **Git**

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/th-nuernberg/llars.git
cd llars

# 2. Configure environment variables
cp .env.template.development .env

# 3. Start LLARS
./start_llars.sh
```

The script starts all Docker containers and configures Authentik automatically.

### URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik Admin | http://localhost:55095 |

### Default Users

| User | Password | Role |
|------|----------|------|
| admin | admin123 | Administrator |
| researcher | admin123 | Researcher (can create scenarios) |
| evaluator | admin123 | Evaluator (participates in evaluations) |
| chatbot_manager | admin123 | Chatbot Manager |

---

## Architecture

```
nginx (:80) -> Reverse Proxy
|-- /           -> Vue Frontend (:5173)
|-- /api/       -> Flask Backend (:8081)
|-- /auth/      -> Flask Auth -> Authentik
|-- /authentik/ -> Authentik UI (:9000)
|-- /collab/    -> YJS WebSocket (:8082)

Databases:
|-- MariaDB     -> Application data
|-- PostgreSQL  -> Authentik
|-- ChromaDB    -> RAG vectors
```

**Tech Stack:**
- **Backend:** Flask 3.0 + MariaDB 11.2 + ChromaDB + Gunicorn/gevent (production)
- **Frontend:** Vue 3.4 + Vuetify 3.5 + Vite 5.1
- **Realtime:** Socket.IO + YJS CRDT
- **Auth:** Authentik (OAuth2/OIDC, RS256 JWT)

---

## Project Structure

```
llars/
|-- app/                    # Flask Backend
|   |-- auth/              # Authentication
|   |-- routes/            # API Endpoints
|   |-- services/          # Business Logic
|   |-- db/                # Database Models
|   |-- schemas/           # Pydantic Schemas
|-- llars-frontend/        # Vue 3 Frontend
|   |-- src/components/    # Vue Components (35+ L-components)
|   |-- src/composables/   # Vue Composables
|   |-- src/views/         # Page Views
|-- yjs-server/            # YJS WebSocket Server
|-- docker/                # Docker Configuration
|-- Paper/                 # IJCAI 2026 Demo Paper
|-- scripts/               # Utility Scripts
|-- tests/                 # Backend Tests
|-- start_llars.sh         # Startup Script
|-- docker-compose.yml     # Docker Compose
```

---

## Commands

```bash
# Start (development)
./start_llars.sh

# Full restart (DELETES ALL DATA!)
REMOVE_LLARS_VOLUMES=True ./start_llars.sh

# Logs
docker compose logs -f backend-flask-service
docker compose logs -f frontend-vue-service

# Tests
pytest tests/                              # Backend
cd llars-frontend && npm run test:run      # Frontend
cd llars-frontend && npx playwright test   # E2E
```

---

## Configuration

Key environment variables in `.env`:

```bash
PROJECT_STATE=development     # or production
PROJECT_URL=http://localhost:55080
NGINX_EXTERNAL_PORT=55080
OPENAI_API_KEY=sk-...         # For LLM features
LITELLM_API_KEY=...           # Optional for open-source models via LiteLLM
```

---

## License

This project is licensed under the MIT License.

---

<p align="center">
  <strong>Technische Hochschule Nurnberg Georg Simon Ohm</strong><br>
  Faculty of Computer Science, Center for Artificial Intelligence (KIZ)<br>
  Faculty of Social Sciences, Institute for E-Counselling
</p>
