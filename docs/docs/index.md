# LLARS Dokumentation

Willkommen zur Dokumentation des **LLM Assisted Research System (LLARS)**.

## Überblick

LLARS ist eine Plattform zur KI-gestützten Analyse und Bewertung von E-Mail-Konversationen. Kernfunktionen:

- **Mail-Rating & Ranking**: Strukturiertes Bewerten und Vergleichen von Threads
- **LLM-Integration**: OpenAI und LiteLLM/Mistral
- **Authentifizierung**: Authentik (OIDC) mit Rollen- und Rechtemodell
- **Kollaboration**: Yjs für Echtzeit-Synchronisation
- **RAG-Pipeline**: Wissensbasierte Antworten über ChromaDB

## Architektur

**Service-Übersicht (interne Ports)**

```mermaid
flowchart LR
    client((Browser)) -->|HTTP 80/443| nginx[nginx<br/>(:80)]
    nginx -->|/ ->| frontend[Vue<br/>Vite Dev :5173<br/>Static Build]
    nginx -->|/api ->| backend[Flask API<br/>:8081]
    nginx -->|/authentik/ ->| authentik[Authentik<br/>:9000]
    nginx -->|/collab/ ->| yjs[Yjs WebSocket<br/>:8082]

    backend <--> mariadb[(MariaDB<br/>:3306)]
    authentik <--> pg[(PostgreSQL<br/>Authentik DB)]

    backend -->|OIDC| authentik
    yjs -->|JWT Validate| authentik
```

**Standard-Ports (Development)**
- 55080 → nginx (Frontend + API)
- 55173 → Vite Dev Server (direkter Zugriff)
- 55081 → Flask (direkter Dev-Zugriff)
- 55095 → Authentik
- 55082 → Yjs
- 55306 → MariaDB (nur für Debugging)

In Production werden nur 80/443 nach außen exponiert.

## Schnellstart

1. Repository klonen  
2. `.env.template.development` nach `.env` kopieren und anpassen  
3. Startskript ausführen: `./start_llars.sh`  
4. Aufrufen: `http://localhost:55080`

## Weiterführende Infos

Siehe [Getting Started](getting-started/installation.md) für Details zu Installation und Konfiguration.
