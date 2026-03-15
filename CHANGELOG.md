# LLARS Changelog

All notable changes to the LLARS (LLM Assisted Research System) project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Versioning

LLARS uses **tag-based semantic versioning** computed via `git describe --tags --match "v*" --first-parent`.
Given a tag `vMAJOR.MINOR.PATCH`, the formula produces `MAJOR.MINOR.(PATCH + N)` where N is the number
of commits since the tag. At the tagged commit itself, N=0 and the version matches the tag exactly.
Tags: `v1.0.0` (2026-03-09), `v1.1.0` (2026-03-13). Future releases will be tagged on `main` after
each dev-to-main merge.

---

## [Unreleased]

### 2026-03-15

#### Fixed
- **KRITISCH: Frontend Healthcheck nutzte `wget` (nicht installiert in nginx:alpine)** - verursachte 9h17min Production-Downtime nach Server-Reboot. `unattended-upgrades` Kernel-Update loeste Reboot aus → `llars.service` startete `docker compose up -d` → Frontend-Healthcheck schlug fehl (wget fehlt) → Frontend "unhealthy" → nginx `depends_on: condition: service_healthy` blockiert → nginx blieb im "Created"-Status. Fix: Healthcheck auf `curl` umgestellt (in nginx:alpine enthalten).

#### Added
- **2-Achsen Berechtigungsmodell fuer Szenarien** - Ersetzt einfache `role`-Spalte durch `access_level` (OWNER/MANAGER/MEMBER) + Capability-Flags (`is_viewer`, `is_assessor`). Ermoeglicht feingranulare Kontrolle: z.B. Manager ohne Evaluations-Sicht oder Viewer mit Assessor-Aufgabe.
- **Neuer Settings-Tab im Scenario Manager** - Ersetzt Settings-Popup-Dialog. Enthaelt alle Szenario-Einstellungen + Team-Uebersicht mit Tag-basierter Rollenverwaltung und Toggle-Switches fuer Viewer/Assessor-Flags.

---

## [1.1.0] - 2026-03-13

Changes since v1.0.0 (2026-03-09).

### 2026-03-13

#### Fixed
- **MariaDB 11.2.2 auf 11.2.6 aktualisiert** - behebt SEGFAULT-Absturz in der Datenbank
- **pypdf 6.7.5 auf 6.8.0 aktualisiert** - behebt CVE-2026-31826 (Sicherheitsluecke)
- **Bucket-Spalte auf VARCHAR(255) erweitert** fuer benutzerdefinierte Labels in Ranking-Szenarien
- Owner erhaelt automatisch VIEWER-Berechtigung; Team-Sichtbarkeit im Scenario Manager korrigiert
- Nginx DNS Auto-Heal nach Container-Neustarts
- Syntax-Fehler im GenerationJobDetail Socket-Handler behoben
- Zahlreiche E2E-Test-Fixes: User-Suche, Share-Dialog, Rate-Limit-Vermeidung, Workflow-Robustheit

### 2026-03-12

#### Added
- **Generation Job Sharing** - Jobs koennen mit anderen Nutzern geteilt werden (read-only)
- E2E-Tests fuer Dev-Branch automatisch mit gleicher Suite wie Main

#### Fixed
- Konsistente Avatare in allen User-Listen (Backend + Frontend)
- Fehlende `ItemComparisonEvaluation`-Model-Klasse ergaenzt
- E2E-Workflow-Tests mit SYSTEM_ADMIN_API_KEY stabilisiert

#### Changed
- `build_avatar_url()` wird jetzt ueberall statt manueller URL-Konstruktion verwendet

### 2026-03-11

#### Fixed
- E2E Tile-Regression: `requiresAdmin` fuer Pipeline-Routes, Redirect-Erkennung
- E2E-Fixes fuer Staging 429 Rate-Limits
- Bootstrap-Variablen fuer e2e:dev Job ergaenzt

#### Performance
- CI-Pipeline: venv/node_modules Caching mit File-Hash-Keys eingefuehrt

### 2026-03-10

#### Added
- **Tag-basiertes Versionierungssystem** mit `/api/version` Endpoint
- **117 neue LLM-Tests** + Smoke-Tests + E2E LLM-Stream-Test
- LLM Prompt Response Smoke-Test und Handler-Integrationstests

#### Fixed
- **Flask==3.0.3 und Werkzeug==3.0.6 gepinnt** - behebt Socket.IO Session-Fehler (kritisch)
- **LLM Evaluator Anti-DDoS**: Lock + Permanent-Failure-Detection verhindern Server-Ueberlastung
- Docker Hub TLS-Timeouts: `syntax=docker/dockerfile:1` Direktiven entfernt
- Flask-SocketIO auf 5.4.1 aktualisiert, Encryption-Key-Fallback korrigiert
- NameError-Crashes im LLM Ranking Runner behoben
- Socket.IO xhr-post-Fehler in Prompt Engineering und Chat beseitigt
- LLM Auto-Start und Socket.IO-Konnektivitaet wiederhergestellt
- Smart CACHE_BUST statt --no-cache fuer Docker Builds (verhindert Disk-Full)

#### Documentation
- LLM Evaluator Anti-DDoS Architektur dokumentiert; Code-Dokumentationsrichtlinie eingefuehrt

### 2026-03-09

#### Added
- **Markdown Scenario Briefings** end-to-end (Judge-Szenarien mit Markdown-Beschreibungen)
- **Admin Research Groups** mit neuem Master-Detail-Layout redesigned
- **Semantische Versionsverwaltung** mit Branch-aware Auto-Increment
- Branch und Commit-Hash werden neben der Version in der AppBar angezeigt

#### Fixed
- Segfault im Route-Test-Teardown behoben
- E2E Tile-Regression-Failures korrigiert
- Git-Version als Build-Arg an Docker-Frontend-Builds uebergeben
- SQLite Connection Pool wird vor Table-Drop korrekt disposed
- Langchain Dependency-Konflikt und Seeder-Constraint-Fehler behoben
- Dependency-Audit-Pipeline wiederhergestellt

---

## [1.0.0] - 2026-03-09

Erster getaggter Release. Umfasst die gesamte Projektentwicklung seit Maerz 2024.

### Highlights

- Vollstaendiges Evaluationsframework mit 6 Bewertungstypen (Ranking, Rating, Mail Rating, Comparison, Authenticity, Labeling)
- Multi-dimensionales Rating-System mit Presets (SummEval, LLM-Judge-Standard, etc.)
- LLM-as-Judge mit automatischer Evaluierung und Anti-DDoS-Schutzschichten
- Collaborative Prompt Engineering mit YJS-WebSocket-Sync
- RAG-Pipeline mit ChromaDB, Embedding-Models und Reranking
- Scenario Wizard mit AI-gestuetzter Datenanalyse und Typ-Erkennung
- Blue-Green Deployment mit automatischem Rollback
- RBAC-Berechtigungssystem mit Authentik-Integration

### Maerz 2026 (vor Tag)

#### Added
- **Deutsche Bahn Preisagent** - DB-Preismonitoring als neues Tool
- **Dev-Branch CI/CD Pipeline** fuer llars-dev Server mit eigenem Blue-Green Deployment
- Mobile Views fuer DB Agent und LaTeX Collaboration
- Conference Manager mit PDF-Viewer
- LaTeX Collab PDF-Downloads

#### Fixed
- Blue-Green Deployment: Switch-Job, Smoke-Tests gegen Staging-Nginx
- Aggressive Disk-Cleanup in CI fuer /var-Speicherprobleme
- Stabilisierung der Nightly-Tile-Tests und Privacy-Recovery
- Relative Production-URLs fuer Frontend

### Februar 2026

#### Added
- **Conference Manager** - Verwaltung von Konferenzen und Papers
- **Manager-Rolle** fuer Szenarien; Evaluator in Assessor umbenannt
- **User LLM Providers** - Nutzer koennen eigene LLM-Provider anlegen und teilen
- **Automated Pipeline** Feature (admin-only) fuer automatisierte Evaluierungs-Pipelines
- **IONOS AI Model Hub** Katalog mit Kosten-Tracking und Token-Abrechnung
- **Referral-System** mit Live-Slug-Validation und verbesserter UX
- **Provenance-Analyse** - Herkunftsanalyse fuer Konversationspartner und Prompts
- **Demo-Video-Framework** fuer IJCAI 2026 mit Two-Speaker-TTS und Overlay-System
- openai_compatible und vLLM Provider-Unterstuetzung
- Provider-Prefix-Routing fuer LLM-Modelle (Global/{Hersteller}/{Modell})
- Server-side Generation-to-Scenario Import mit Format-Erkennung
- Per-Dimension Agreement-Metriken fuer Rating/Mail-Rating
- Skeleton Loading + Fade-Transitions fuer Scenario Evaluation Tab
- Batch Generation mit gruppierten, farbcodierten Output-Listen
- i18n-Uebersetzungen fuer RAG, DataImporter und Admin-Sections
- Automatische MkDocs-Sprachumschaltung basierend auf LLARS-Locale

#### Fixed
- N+1-Queries in Evaluation-Session-Loading und Scenario-Stats eliminiert
- Legacy `llms`-Tabelle entfernt, durchgehend model_id Strings verwendet
- Bucket-Distribution und Provenance vollstaendig dynamisch gemacht
- Generation Stream Reconnect und Pre-Request-Latenz optimiert
- i18n SyntaxError durch unescapte @-Zeichen in Locale-Messages behoben
- 502 Bad Gateway nach --update durch Nginx-Restart behoben

#### Security
- SSRF-Schutz und Access-Control-Enforcement verstaerkt

### Januar 2026

#### Added
- **Gunicorn + gevent** fuer Production WebSocket-Unterstuetzung (statt Flask Dev Server)
- **User API Key Management** - Nutzer koennen eigene API-Keys verwalten
- **AI Writing Assistant** fuer LaTeX Collaboration mit Streaming
- **Floating Git Panel** / Version Control Panel fuer Prompt Engineering
- **MkDocs Dokumentation** als RAG Knowledge Base fuer Chatbot
- **KaiMo Case Sharing** mit per-User-Ownership und Auto-Save
- AI-Analyse fuer Scenario Wizard verbessert (Dateiformaterkennung)
- LFloatingWindow Komponente
- Scenario-Invite-Flow verbessert

#### Fixed
- Chatbot: PROJECT_URL-Platzhalter in RAG-Kontext und LLM-Antworten ersetzt
- Socket.IO Background-Thread App-Context und LLM-Client-Initialisierung
- AI-Comment-Kontext auf 1000 Zeichen erhoeht, Nginx-Timeout angepasst

### Dezember 2025

#### Added
- **CI/CD Pipeline** vollstaendig mit GitLab Shell Runner konfiguriert
- **Zotero OAuth Integration** fuer LaTeX Collaboration
- **System Settings** Admin-Section mit Runtime-Config
- **AI Writing Assistant** fuer LaTeX Collaboration
- Markdown Collaboration mit YJS-Sync verbessert
- System Settings Datenbank-Tabelle fuer Laufzeitkonfiguration
- Pytest-Konfiguration und Test-Struktur aufgebaut
- Comprehensive Unit- und Integrationstests (Frontend + Backend)

#### Fixed
- ChromaDB page_content=None Bug (defensive Behandlung)
- PDF.js Worker: MIME-Types, CSP, auto-copy bei Build
- Frontend Healthcheck Timeout auf 60s start_period angepasst
- Collection Embedding Service und Seeder-Verbesserungen

### November 2025

#### Changed
- **Grosses Refactoring** (16 Major-Refactorings abgeschlossen):
  - ChatWithBots.vue (3299 auf 774 Zeilen), JudgeSession.vue (2174 auf 579)
  - ChatbotEditor.vue (1967 auf 507), chat_service.py (1657 auf 590)
  - crawler_service.py (1415 auf 666), anonymize_service.py (1275 auf 445)
  - Composable-Extraktion fuer alle grossen Vue-Komponenten
  - Backend-Routes in modulare Dateien aufgeteilt (judge, oncoco, RAG, statistics, sessions)
  - `tables.py` in modulare Model-Dateien aufgeteilt (Phase 1)
  - Web-Crawler in modulare Komponenten gesplittet

### September - Oktober 2024

#### Added
- Authentik OAuth2 Integration mit RBAC
- Ranking- und Rating-System Grundfunktionen
- LLM Integration (OpenAI, LiteLLM)
- Chatbot-Builder mit RAG-Integration
- Web-Crawler fuer Wissensbasen

### Maerz - August 2024

#### Added
- **Projektstart** - Vue 3 + Flask Backend initialisiert
- Grundlegende Ranker/Rater Dashboards
- Drag-and-Drop Ranking-Interface
- E-Mail-Thread-Verwaltung und Szenario-Grundstruktur
- MariaDB-Integration mit ersten Tabellen
- Docker-Compose Setup mit Hot-Reloading
- Authentik User-Management Grundlagen

---

## Links

- Repository: git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars
- Production: 141.75.150.128
- Dev: 141.75.150.86
