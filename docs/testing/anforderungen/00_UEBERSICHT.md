# LLARS Testanforderungen - Gesamtübersicht

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Systemübersicht

### Technologie-Stack

| Schicht | Technologie | Test-Tool |
|---------|-------------|-----------|
| Frontend | Vue 3.4 + Vuetify 3.5 | Vitest + Vue Test Utils |
| Backend | Flask 3.0 + SQLAlchemy | pytest + pytest-flask |
| Database | MariaDB 11.2 | pytest (SQLite in-memory) |
| Vector DB | ChromaDB 0.5.20 | pytest + Mocks |
| Realtime | Socket.IO + YJS | pytest + Playwright |
| Auth | Authentik OIDC | pytest + Mocks |
| E2E | - | Playwright |

### System-Metriken

| Metrik | Anzahl |
|--------|--------|
| Backend Blueprints | 38 |
| API Endpoints | 364+ |
| Socket.IO Events | 50+ |
| Frontend Seiten | 54+ |
| DB Models | 20+ |
| Services | 40+ |
| Permissions | 43 |
| Rollen | 4 |

---

## Kritische Pfade (Müssen IMMER funktionieren)

### 1. Authentifizierung
```
Login → Token erhalten → API-Zugriff → Logout
```
**Tests:** Token-Validierung, Expired Tokens, Invalid Tokens, Logout

### 2. RAG Pipeline
```
Upload → Chunking → Embedding → ChromaDB → Suche → Ergebnis
```
**Tests:** File-Upload, Chunk-Größe, Embedding-Dimensionen, Search-Ranking

### 3. Chatbot-Erstellung
```
Wizard Start → Dokumente hochladen → Embedding → Konfiguration → Chat
```
**Tests:** Wizard-Flow, Collection-Binding, LLM-Antworten

### 4. LLM-as-Judge
```
Session erstellen → Vergleiche konfigurieren → Starten → Ergebnisse
```
**Tests:** Session-Status, Queue-Management, Worker-Streaming

### 5. Kollaboratives Editieren
```
Workspace öffnen → Dokument editieren → Sync → Andere User sehen Änderungen
```
**Tests:** YJS-Sync, Conflict Resolution, Reconnection

---

## Alle Test-Bereiche im Überblick

### A. Frontend-Seiten (54+ Seiten)

| Seite | Route | Priorität | Dokument |
|-------|-------|-----------|----------|
| Login | `/login` | P0 | [01_SEITEN_NAVIGATION.md](frontend/01_SEITEN_NAVIGATION.md) |
| Home | `/Home` | P0 | [01_SEITEN_NAVIGATION.md](frontend/01_SEITEN_NAVIGATION.md) |
| Ranker | `/Ranker` | P1 | [02_EVALUATION_FEATURES.md](frontend/02_EVALUATION_FEATURES.md) |
| Rater | `/Rater` | P1 | [02_EVALUATION_FEATURES.md](frontend/02_EVALUATION_FEATURES.md) |
| Judge | `/judge` | P1 | [02_EVALUATION_FEATURES.md](frontend/02_EVALUATION_FEATURES.md) |
| OnCoCo | `/oncoco` | P1 | [02_EVALUATION_FEATURES.md](frontend/02_EVALUATION_FEATURES.md) |
| Markdown Collab | `/MarkdownCollab` | P1 | [03_COLLAB_EDITOREN.md](frontend/03_COLLAB_EDITOREN.md) |
| LaTeX Collab | `/LatexCollab` | P1 | [03_COLLAB_EDITOREN.md](frontend/03_COLLAB_EDITOREN.md) |
| Chat | `/chat` | P1 | [04_CHAT_CHATBOTS.md](frontend/04_CHAT_CHATBOTS.md) |
| Admin | `/admin` | P0 | [05_ADMIN_DASHBOARD.md](frontend/05_ADMIN_DASHBOARD.md) |
| Anonymize | `/Anonymize` | P2 | [01_SEITEN_NAVIGATION.md](frontend/01_SEITEN_NAVIGATION.md) |
| KAIMO | `/kaimo` | P2 | [02_EVALUATION_FEATURES.md](frontend/02_EVALUATION_FEATURES.md) |

### B. Backend-Routen (364+ Endpoints)

| Modul | Endpoints | Priorität | Dokument |
|-------|-----------|-----------|----------|
| Auth | 10 | P0 | [01_AUTH_ROUTES.md](backend/01_AUTH_ROUTES.md) |
| Permissions | 12 | P0 | [01_AUTH_ROUTES.md](backend/01_AUTH_ROUTES.md) |
| Users | 15 | P1 | [02_API_ROUTES.md](backend/02_API_ROUTES.md) |
| RAG | 35 | P0 | [02_API_ROUTES.md](backend/02_API_ROUTES.md) |
| Chatbot | 40 | P1 | [02_API_ROUTES.md](backend/02_API_ROUTES.md) |
| Judge | 50 | P1 | [02_API_ROUTES.md](backend/02_API_ROUTES.md) |
| Rating/Ranking | 30 | P1 | [02_API_ROUTES.md](backend/02_API_ROUTES.md) |
| Collab | 40 | P1 | [02_API_ROUTES.md](backend/02_API_ROUTES.md) |
| Crawler | 10 | P2 | [02_API_ROUTES.md](backend/02_API_ROUTES.md) |
| Socket.IO | 50 | P1 | [03_SOCKETIO_EVENTS.md](backend/03_SOCKETIO_EVENTS.md) |

### C. Features

| Feature | Komponenten | Priorität | Dokument |
|---------|-------------|-----------|----------|
| RAG Pipeline | Upload, Chunking, Embedding, Search | P0 | [01_RAG_PIPELINE.md](features/01_RAG_PIPELINE.md) |
| LLM Integration | Chat, Streaming, Models | P0 | [02_LLM_INTEGRATION.md](features/02_LLM_INTEGRATION.md) |
| YJS Collaboration | Sync, Awareness, Recovery | P1 | [03_YJS_COLLABORATION.md](features/03_YJS_COLLABORATION.md) |
| LaTeX Kompilierung | pdflatex, biber, SyncTeX | P1 | [04_LATEX_KOMPILIERUNG.md](features/04_LATEX_KOMPILIERUNG.md) |
| Anonymisierung | NER, Regex, Pseudonymisierung | P2 | [05_ANONYMISIERUNG.md](features/05_ANONYMISIERUNG.md) |

### D. Security

| Bereich | Tests | Priorität | Dokument |
|---------|-------|-----------|----------|
| RBAC Permissions | 43 Permissions | P0 | [01_BERECHTIGUNGEN.md](security/01_BERECHTIGUNGEN.md) |
| Rollen-Matrix | 4 Rollen × Features | P0 | [02_ROLLEN_MATRIX.md](security/02_ROLLEN_MATRIX.md) |
| Route Protection | Alle 364+ Routes | P0 | [03_ROUTE_PROTECTION.md](security/03_ROUTE_PROTECTION.md) |

---

## Test-Kategorien nach Priorität

### P0 - Kritisch (Muss vor jedem Deploy grün sein)

- [ ] Login/Logout funktioniert
- [ ] Token-Validierung korrekt
- [ ] Admin kann Admin-Dashboard sehen
- [ ] Evaluator kann NICHT Admin-Dashboard sehen
- [ ] Researcher kann nur seine Kacheln sehen
- [ ] RAG Upload funktioniert
- [ ] Chatbot antwortet
- [ ] LLM-Streaming funktioniert
- [ ] Embeddings werden erstellt
- [ ] Suche findet Dokumente

### P1 - Wichtig (Sollte vor Release getestet werden)

- [ ] Alle Kacheln auf Home klickbar
- [ ] Ranker Drag & Drop funktioniert
- [ ] Rater Bewertung speichert
- [ ] Judge Session startet
- [ ] Markdown Editor synchronisiert
- [ ] LaTeX kompiliert zu PDF
- [ ] Collab-Farbe änderbar
- [ ] Avatar änderbar
- [ ] Chatbot-Wizard durchlaufen
- [ ] Szenarien anlegen funktioniert

### P2 - Nice-to-have

- [ ] Performance unter Last
- [ ] Edge Cases
- [ ] Mobile Responsiveness
- [ ] Error Recovery
- [ ] Offline-Handling

---

## Quick Reference: Rollen-Zugriff

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|-------|------------|-----------------|--------|
| Home Dashboard | ✅ | ✅ | ✅ | ✅ |
| Ranking/Rating | ✅ | ✅ | ❌ | ✅ (view) |
| Judge | ✅ | ❌ | ❌ | ❌ |
| Chatbot erstellen | ✅ | ❌ | ✅ | ❌ |
| Chatbot nutzen | ✅ | ✅ | ✅ | ✅ |
| RAG verwalten | ✅ | ❌ | ✅ | ❌ |
| Markdown Collab | ✅ | ✅ | ✅ | ✅ (view) |
| LaTeX Collab | ✅ | ✅ | ✅ | ✅ (view) |
| LaTeX AI | ✅ | ✅ | ✅ | ❌ |
| Anonymize | ✅ | ✅ | ❌ | ✅ |
| KAIMO | ✅ | ✅ | ❌ | ✅ |
| Admin Dashboard | ✅ | ❌ | ⚠️ (nur Chatbots) | ❌ |
| User Management | ✅ | ❌ | ❌ | ❌ |
| Docker Monitor | ✅ | ❌ | ❌ | ❌ |
| DB Explorer | ✅ | ❌ | ❌ | ❌ |
| System Settings | ✅ | ❌ | ❌ | ❌ |

---

## Nächste Schritte

1. **Lies die Detail-Dokumente** in den Unterordnern
2. **Führe den Smoke Test** aus: [SMOKE_TEST.md](../checklisten/SMOKE_TEST.md)
3. **Implementiere Tests** nach dem [Leitfaden](../leitfaden/LLARS_TEST_LEITFADEN.md)

---

**Letzte Aktualisierung:** 30. Dezember 2025
