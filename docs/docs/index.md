# LLARS Documentation

Welcome to the LLARS (LLM-Assisted Rating System) Platform documentation.

## Overview

LLARS is a comprehensive platform for email rating and analysis using Large Language Models (LLMs). The system provides:

- **Email Thread Management**: Organize and rate email conversations
- **LLM Integration**: Leverage advanced AI models for content analysis
- **User Management**: Keycloak-based authentication and authorization
- **Collaborative Editing**: Real-time document collaboration with Yjs
- **RAG Pipeline**: Retrieval-Augmented Generation for contextual responses

## Architecture

**Service-Übersicht (interne Ports)**  
```text
┌──────────────────┐
│  nginx (Port 80) │  ← Reverse Proxy + Load Balancer
└─────────┬────────┘
          │
    ┌─────┼─────────────────┬──────────────────┬────────────────┐
    │     │                 │                  │                │
┌───▼──┐ ┌▼────────┐  ┌────▼─────┐  ┌────────▼──────┐  ┌──────▼───────┐
│ Vue  │ │ Flask   │  │ Keycloak │  │ YJS WebSocket │  │  Supervisor  │
│:5173 │ │ :8081   │  │  :8090   │  │     :8082     │  │   Service    │
└──────┘ └─────┬───┘  └────┬─────┘  └───────┬───────┘  └──────┬───────┘
               │           │                 │                 │
        ┌──────┴───────────┴─────────────────┴─────────────────┘
        │
   ┌────▼──────┐        ┌────────────┐
   │  MariaDB  │        │ PostgreSQL │
   │   :3306   │        │   :5432    │
   └───────────┘        └────────────┘
     (LLARS DB)         (Keycloak DB)
```

**Externe Ports (Development-Defaults)**  
- 55080 → nginx (http)  
- 55173 → Vue Dev Server  
- 55081 → Flask (direct dev access)  
- 55090 → Keycloak  
- 55082 → YJS Server  
- 55306 → MariaDB (falls explizit freigegeben)  

**Production**  
- Nur 443/80 nach nginx; alle anderen Services sind intern erreichbar.

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run `docker compose up -d`
4. Access the application at `http://localhost:55080`

## Development

See the [Getting Started](getting-started/installation.md) section for detailed installation and configuration instructions.
