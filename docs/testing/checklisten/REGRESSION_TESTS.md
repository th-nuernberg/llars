# LLARS Regression Test Checkliste

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Zweck

Diese Checkliste dient zur systematischen Überprüfung aller Kernfunktionalitäten nach größeren Änderungen.

**Geschätzte Dauer:** 1-2 Stunden
**Wann ausführen:** Nach größeren Refactorings, Dependency-Updates, Infrastructure-Änderungen

---

## 1. Authentifizierung & Authorization

### Login/Logout

| Test | Status | Notizen |
|------|--------|---------|
| Login mit admin/admin123 | ⬜ | |
| Login mit researcher/admin123 | ⬜ | |
| Login mit evaluator/admin123 | ⬜ | |
| Falsches Passwort → Fehler | ⬜ | |
| Logout → Redirect zu /login | ⬜ | |
| Token wird gelöscht | ⬜ | |

### Permissions

| Test | Status | Notizen |
|------|--------|---------|
| Admin sieht alle Kacheln | ⬜ | |
| Researcher: kein Judge/OnCoCo | ⬜ | |
| Viewer: nur View-Rechte | ⬜ | |
| /admin für Nicht-Admin → 403 | ⬜ | |

---

## 2. Navigation & UI

### Home Dashboard

| Test | Status | Notizen |
|------|--------|---------|
| Home lädt | ⬜ | |
| Alle Kacheln klickbar | ⬜ | |
| Kategorien-Sidebar funktioniert | ⬜ | |
| Mobile Responsive | ⬜ | |

### Navigation

| Test | Status | Notizen |
|------|--------|---------|
| AppBar sichtbar | ⬜ | |
| User-Menu funktioniert | ⬜ | |
| Footer sichtbar | ⬜ | |
| 404-Seite bei ungültiger URL | ⬜ | |

---

## 3. LLM Integration

### Chat

| Test | Status | Notizen |
|------|--------|---------|
| /chat lädt | ⬜ | |
| Chatbot-Liste sichtbar | ⬜ | |
| Message senden | ⬜ | |
| Bot antwortet | ⬜ | |
| Streaming funktioniert | ⬜ | |
| Conversation History | ⬜ | |

### Models

| Test | Status | Notizen |
|------|--------|---------|
| LLM Models in Dropdown | ⬜ | |
| Embedding Models verfügbar | ⬜ | |
| Model-Wechsel funktioniert | ⬜ | |

---

## 4. RAG Pipeline

### Upload

| Test | Status | Notizen |
|------|--------|---------|
| PDF Upload | ⬜ | |
| TXT Upload | ⬜ | |
| Multi-File Upload | ⬜ | |
| Ungültiger Typ → Fehler | ⬜ | |

### Embedding

| Test | Status | Notizen |
|------|--------|---------|
| Embedding startet | ⬜ | |
| Progress-Anzeige | ⬜ | |
| Status: completed | ⬜ | |
| Fehler werden angezeigt | ⬜ | |

### Retrieval

| Test | Status | Notizen |
|------|--------|---------|
| Chat findet Dokumente | ⬜ | |
| Sources werden angezeigt | ⬜ | |
| Chunks sind korrekt | ⬜ | |

---

## 5. Evaluation Features

### Ranking

| Test | Status | Notizen |
|------|--------|---------|
| /Ranker lädt | ⬜ | |
| Thread-Liste sichtbar | ⬜ | |
| Features angezeigt | ⬜ | |
| Drag & Drop funktioniert | ⬜ | |
| Speichern funktioniert | ⬜ | |

### Rating

| Test | Status | Notizen |
|------|--------|---------|
| /Rater lädt | ⬜ | |
| Bewertungsskala sichtbar | ⬜ | |
| Rating speichern | ⬜ | |

### Judge (Admin only)

| Test | Status | Notizen |
|------|--------|---------|
| /Judge lädt | ⬜ | |
| Session erstellen | ⬜ | |
| Session starten | ⬜ | |
| Progress-Updates | ⬜ | |

---

## 6. Kollaborative Editoren

### Markdown Collab

| Test | Status | Notizen |
|------|--------|---------|
| /MarkdownCollab lädt | ⬜ | |
| Workspace erstellen | ⬜ | |
| Editor funktioniert | ⬜ | |
| Preview aktualisiert | ⬜ | |
| Speichern funktioniert | ⬜ | |

### LaTeX Collab

| Test | Status | Notizen |
|------|--------|---------|
| /LatexCollab lädt | ⬜ | |
| Workspace erstellen | ⬜ | |
| Editor funktioniert | ⬜ | |
| Kompilieren → PDF | ⬜ | |
| PDF-Preview | ⬜ | |
| Fehler werden angezeigt | ⬜ | |

### Collab Color

| Test | Status | Notizen |
|------|--------|---------|
| User-Settings öffnen | ⬜ | |
| Farbe ändern | ⬜ | |
| Farbe wird gespeichert | ⬜ | |

---

## 7. Admin-Bereich

### Dashboard

| Test | Status | Notizen |
|------|--------|---------|
| /admin lädt | ⬜ | |
| Alle Tabs sichtbar | ⬜ | |

### Docker Monitor

| Test | Status | Notizen |
|------|--------|---------|
| Container-Liste | ⬜ | |
| CPU/Memory Charts | ⬜ | |
| Logs streaming | ⬜ | |

### DB Explorer

| Test | Status | Notizen |
|------|--------|---------|
| Tabellen-Liste | ⬜ | |
| Tabelle auswählen | ⬜ | |
| Daten laden | ⬜ | |

### System Health

| Test | Status | Notizen |
|------|--------|---------|
| Host Metrics | ⬜ | |
| API Stats | ⬜ | |
| WebSocket Stats | ⬜ | |

### User Management

| Test | Status | Notizen |
|------|--------|---------|
| User-Liste | ⬜ | |
| User Details | ⬜ | |
| User sperren | ⬜ | |
| User entsperren | ⬜ | |

### Scenario Management

| Test | Status | Notizen |
|------|--------|---------|
| Szenarien-Liste | ⬜ | |
| Szenario erstellen | ⬜ | |
| Threads zuweisen | ⬜ | |
| User zuweisen | ⬜ | |

---

## 8. Anonymisierung

| Test | Status | Notizen |
|------|--------|---------|
| /Anonymize lädt | ⬜ | |
| Text eingeben | ⬜ | |
| Pseudonymisieren | ⬜ | |
| Namen werden ersetzt | ⬜ | |
| Highlighting funktioniert | ⬜ | |

---

## 9. WebSocket Events

### Chat Streaming

| Test | Status | Notizen |
|------|--------|---------|
| chatbot:stream | ⬜ | |
| chatbot:response | ⬜ | |
| chatbot:complete | ⬜ | |

### RAG Updates

| Test | Status | Notizen |
|------|--------|---------|
| rag:queue_list | ⬜ | |
| rag:collection_progress | ⬜ | |
| rag:document_processed | ⬜ | |

### Admin Namespace

| Test | Status | Notizen |
|------|--------|---------|
| docker:stats | ⬜ | |
| db:table | ⬜ | |
| host:stats | ⬜ | |

---

## 10. API Endpoints

### Auth

| Endpoint | Status | Notizen |
|----------|--------|---------|
| POST /auth/authentik/login | ⬜ | |
| GET /auth/authentik/me | ⬜ | |
| GET /auth/authentik/validate | ⬜ | |

### RAG

| Endpoint | Status | Notizen |
|----------|--------|---------|
| POST /api/rag/documents/upload | ⬜ | |
| GET /api/rag/collections | ⬜ | |
| POST /api/rag/collections/:id/embed | ⬜ | |

### Chatbots

| Endpoint | Status | Notizen |
|----------|--------|---------|
| GET /api/chatbots | ⬜ | |
| POST /api/chatbots | ⬜ | |
| POST /api/chatbots/:id/chat | ⬜ | |

### Admin

| Endpoint | Status | Notizen |
|----------|--------|---------|
| GET /api/admin/users | ⬜ | |
| GET /api/admin/scenarios | ⬜ | |

---

## 11. Browser-Kompatibilität

| Browser | Status | Notizen |
|---------|--------|---------|
| Chrome 120+ | ⬜ | |
| Firefox 120+ | ⬜ | |
| Safari 17+ | ⬜ | |
| Edge 120+ | ⬜ | |

---

## 12. Zusammenfassung

### Bereiche

| Bereich | Status |
|---------|--------|
| Authentifizierung | ⬜ OK / ⬜ FAIL |
| Navigation | ⬜ OK / ⬜ FAIL |
| LLM Integration | ⬜ OK / ⬜ FAIL |
| RAG Pipeline | ⬜ OK / ⬜ FAIL |
| Evaluation | ⬜ OK / ⬜ FAIL |
| Collab Editoren | ⬜ OK / ⬜ FAIL |
| Admin-Bereich | ⬜ OK / ⬜ FAIL |
| Anonymisierung | ⬜ OK / ⬜ FAIL |
| WebSockets | ⬜ OK / ⬜ FAIL |
| API Endpoints | ⬜ OK / ⬜ FAIL |

### Gesamtergebnis

⬜ **PASSED** - Alle kritischen Tests bestanden
⬜ **FAILED** - Kritische Fehler gefunden

---

## 13. Gefundene Probleme

| ID | Bereich | Beschreibung | Severity | Status |
|----|---------|--------------|----------|--------|
| | | | | |

---

## 14. Tester-Informationen

| Feld | Wert |
|------|------|
| Tester | |
| Datum | |
| Branch/Version | |
| Umgebung | |
| Browser | |
| Dauer | |

---

**Letzte Aktualisierung:** 30. Dezember 2025
