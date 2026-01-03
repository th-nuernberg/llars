# LLARS Refactoring-Plan 2026

**Version:** 1.0
**Erstellt:** 01. Januar 2026
**Status:** In Planung

---

## 1. Executive Summary

Die Code-Analyse des LLARS-Projekts hat signifikante Refactoring-Möglichkeiten identifiziert. Die Hauptprobleme sind:

- **Monolith-Komponenten**: Vue-Komponenten mit >3000 Zeilen
- **God-Object Services**: Backend-Services mit >30 Methoden
- **Überfüllte Route-Dateien**: Einzelne Dateien mit >40 Endpoints
- **Fehlende Service-Trennung**: Business-Logik vermischt mit DB-Zugriff

**Geschätzter Gesamtaufwand:** 15-20 Personentage

---

## 2. Analyse: Größte Dateien

### 2.1 Frontend (Vue-Komponenten)

| Rang | Datei | Zeilen | Kritikalität |
|------|-------|--------|--------------|
| 1 | `components/ChatWithBots.vue` | **3299** | 🔴 KRITISCH |
| 2 | `views/LatexCollab/LatexCollabWorkspace.vue` | **2857** | 🔴 KRITISCH |
| 3 | `components/Judge/JudgeSession.vue` | **2174** | 🔴 KRITISCH |
| 4 | `components/Admin/ChatbotAdmin/ChatbotEditor.vue` | **1966** | 🟠 HOCH |
| 5 | `components/Admin/ChatbotAdmin/ChatbotBuilderWizard.vue` | **1623** | 🟠 HOCH |
| 6 | `components/Admin/sections/AuthenticityStatsDialog.vue` | **1510** | 🟠 HOCH |
| 7 | `components/Admin/sections/AdminDockerMonitorSection.vue` | **1419** | 🟡 MITTEL |
| 8 | `views/MarkdownCollab/MarkdownCollabWorkspace.vue` | **1329** | 🟡 MITTEL |
| 9 | `components/MarkdownCollab/MarkdownGitPanel.vue` | **1260** | 🟡 MITTEL |
| 10 | `components/parts/CreateScenarioDialog.vue` | **1252** | 🟡 MITTEL |

### 2.2 Backend (Python Services)

| Rang | Datei | Zeilen | Methoden | Kritikalität |
|------|-------|--------|----------|--------------|
| 1 | `services/chatbot/agent_chat_service.py` | **1853** | 36 | 🔴 KRITISCH |
| ~~2~~ | ~~`services/chatbot/chat_service.py`~~ | ~~1657→**590**~~ | ~~33~~ | ✅ Refaktoriert |
| 2 | `services/crawler/modules/crawler_service.py` | **1415** | 29 | 🟠 HOCH |
| 4 | `services/anonymize/anonymize_service.py` | **1275** | - | 🟡 MITTEL |
| 5 | `workers/judge_worker_pool.py` | **1067** | - | 🟡 MITTEL |
| 6 | `services/rag/collection_embedding_service.py` | **1045** | 15 | 🟡 MITTEL |

### 2.3 Backend (Routes)

| Rang | Datei | Zeilen | Endpoints | Kritikalität |
|------|-------|--------|-----------|--------------|
| 1 | `routes/chatbot/chatbot_routes.py` | **1270** | ~40 | 🟠 HOCH |
| 2 | `routes/latex_collab/latex_collab_routes.py` | **1251** | ~40 | 🟠 HOCH |
| 3 | `routes/markdown_collab/markdown_collab_routes.py` | **804** | ~40 | 🟡 MITTEL |

### 2.4 SocketIO Handler

| Datei | Zeilen | Handler | Kritikalität |
|-------|--------|---------|--------------|
| `socketio_handlers/events_chatbot.py` | **862** | 12 | 🟠 HOCH |
| `socketio_handlers/events_rag.py` | **532** | 21 | 🟡 MITTEL |

---

## 3. Detaillierte Problem-Analyse

### 3.1 ChatWithBots.vue (3299 Zeilen) - KRITISCH

**Aktuelle Struktur:**
- 98 State-Variablen (ref, computed, etc.)
- 30+ Funktionen im Setup
- Vermischte Concerns:
  - Sidebar-Verwaltung (Desktop + Mobile)
  - Chat-Rendering
  - Message-Streaming
  - Source-Panel
  - Fullscreen-Dialog
  - File-Upload
  - Analytics-Tracking

**Refactoring-Ziel-Struktur:**

```
components/Chat/
├── ChatWithBots.vue              (~400 Zeilen - Orchestration)
├── sidebar/
│   ├── ChatSidebar.vue           (~300 Zeilen)
│   ├── ChatbotList.vue           (~200 Zeilen)
│   ├── ChatbotGroupItem.vue      (~150 Zeilen)
│   └── ConversationList.vue      (~200 Zeilen)
├── messages/
│   ├── ChatMessages.vue          (~250 Zeilen)
│   ├── MessageItem.vue           (~200 Zeilen)
│   ├── UserMessage.vue           (~100 Zeilen)
│   ├── BotMessage.vue            (~200 Zeilen)
│   └── SourceCitation.vue        (~100 Zeilen)
├── input/
│   ├── MessageInput.vue          (~250 Zeilen)
│   ├── FileUploadArea.vue        (~150 Zeilen)
│   └── SendButton.vue            (~80 Zeilen)
├── panels/
│   ├── SourcePanel.vue           (~200 Zeilen)
│   └── SourceDetail.vue          (~150 Zeilen)
└── composables/
    ├── useChatState.js           (~150 Zeilen)
    ├── useChatSocket.js          (~200 Zeilen)
    ├── useMessageFormatting.js   (~100 Zeilen)
    ├── useSourcePanel.js         (~100 Zeilen)
    └── useFileUpload.js          (~100 Zeilen)
```

**Geschätzter Aufwand:** 3 Tage

---

### 3.2 ChatService + AgentChatService (3510 Zeilen kombiniert) - KRITISCH

**Aktuelle Probleme:**
- `ChatService`: 33 Methoden - mischt Chat-Logik, RAG-Retrieval, Datenvorbereitung
- `AgentChatService`: 36 Methoden - erbt von ChatService + fügt Agent-Patterns hinzu
- Vermischte Verantwortlichkeiten:
  - Title-Normalisierung (`_normalize_title`, `_is_placeholder_title`)
  - Query-Expansion (`_QUERY_SYNONYMS`, `_STOPWORDS_DE`)
  - RAG-Retrieval (`get_rag_sources`, `_build_rag_context`)
  - Agent-Reasoning (`get_agent_mode`, `get_task_type`)
  - Streaming-Management
  - Datenbankoperationen

**Refactoring-Ziel-Struktur:**

```
services/chatbot/
├── chat_service.py               (~400 Zeilen - Core Chat + Streaming)
├── agent_service.py              (~300 Zeilen - Agent-Pattern-Logik)
├── chat_title_service.py         (~100 Zeilen - Title-Normalisierung)
├── query_enrichment_service.py   (~150 Zeilen - Query-Expansion, Stopwords)
├── rag_context_service.py        (~200 Zeilen - RAG Context Building)
└── chat_repository.py            (~150 Zeilen - DB-Operationen)
```

**Geschätzter Aufwand:** 2-3 Tage

---

### 3.3 Route-Dateien (chatbot_routes.py, latex_collab_routes.py)

**Aktuelles Problem:**
- Single-File mit zu vielen Verantwortlichkeiten
- Schwer zu testen und zu warten
- Keine klare Endpoint-Gruppierung

**Refactoring-Ziel für chatbot_routes.py:**

```
routes/chatbot/
├── __init__.py                   (Blueprint-Registrierung)
├── chatbot_crud_routes.py        (~200 Zeilen - CRUD Chatbots)
├── conversation_routes.py        (~200 Zeilen - Conversations)
├── message_routes.py             (~150 Zeilen - Messages)
├── sharing_routes.py             (~150 Zeilen - Access/Sharing)
└── builder_routes.py             (~150 Zeilen - Wizard-Integration)
```

**Refactoring-Ziel für latex_collab_routes.py:**

```
routes/latex_collab/
├── __init__.py                   (Blueprint-Registrierung)
├── workspace_routes.py           (~200 Zeilen - Workspace CRUD)
├── document_routes.py            (~200 Zeilen - Document CRUD)
├── compilation_routes.py         (~150 Zeilen - LaTeX Compilation)
├── collaboration_routes.py       (~150 Zeilen - Real-time Collab)
└── export_routes.py              (~100 Zeilen - Export/Download)
```

**Geschätzter Aufwand:** 2 Tage

---

### 3.4 SocketIO Handler (events_chatbot.py)

**Aktuelles Problem:**
- 12 Event Handler in einer Datei
- Vermischung von Streaming, Error-Handling, Datenbanklogik
- Schwer zu debuggen

**Refactoring-Ziel-Struktur:**

```
socketio_handlers/chatbot/
├── __init__.py                   (Handler-Registrierung)
├── stream_handler.py             (~200 Zeilen)
├── message_handler.py            (~150 Zeilen)
├── conversation_handler.py       (~150 Zeilen)
└── error_handler.py              (~100 Zeilen)
```

**Geschätzter Aufwand:** 1 Tag

---

## 4. Code-Duplikation

### 4.1 Identifizierte Duplikationen

| Bereich | Vorkommen | Lösung |
|---------|-----------|--------|
| Access Control Logic | 5+ Stellen | Zentrale `AccessControlService` |
| RAG Context Building | 3+ Stellen | `RAGContextFormatter` Service |
| Permission Checking | Verstreut | Decorator-Pattern konsistent nutzen |
| Title Normalization | 2+ Stellen | `NamingService` |
| Error Response Formatting | 10+ Stellen | Einheitliches Error-Response-Format |

### 4.2 Konsolidierungs-Plan

```python
# Neue zentrale Services
services/
├── access_control_service.py     # Zentrale Access-Logik
├── naming_service.py             # Title/Name-Normalisierung
└── response_formatter.py         # Einheitliche API-Responses
```

---

## 5. Composables-Analyse (Frontend)

### 5.1 Große Composables

| Composable | Zeilen | Empfehlung |
|-----------|--------|------------|
| `useQuillEditor.js` | 675 | Aufteilen in Editor + Toolbar + Formatting |
| `useWizardSession.js` | 577 | State + Validation + Navigation trennen |
| `useBuilderState.js` | 550 | State + Persistence + Defaults trennen |
| `useOnCoCoAnalysis.js` | 503 | Analysis + Matrix + Export trennen |
| `useAuth.js` | 476 | Auth + Permissions + Session trennen |

### 5.2 Empfohlene Struktur

```
composables/
├── auth/
│   ├── useAuth.js               (~150 Zeilen - Core Auth)
│   ├── usePermissions.js        (~100 Zeilen - Permission Checks)
│   └── useSession.js            (~100 Zeilen - Session Management)
├── wizard/
│   ├── useWizardState.js        (~150 Zeilen - State)
│   ├── useWizardValidation.js   (~150 Zeilen - Validation)
│   └── useWizardNavigation.js   (~100 Zeilen - Navigation)
└── editor/
    ├── useQuillCore.js          (~200 Zeilen - Core Editor)
    ├── useQuillToolbar.js       (~150 Zeilen - Toolbar)
    └── useQuillFormatting.js    (~150 Zeilen - Formatting)
```

---

## 6. Refactoring-Roadmap

### Phase 1: Kritische Komponenten (Sprint 1-2)

| Task | Aufwand | Priorität | Abhängigkeiten |
|------|---------|-----------|----------------|
| ChatWithBots.vue aufteilen | 3 Tage | 🔴 P1 | - |
| ChatService refactoren | 2-3 Tage | 🔴 P1 | - |
| AgentChatService refactoren | 1-2 Tage | 🔴 P1 | ChatService |

### Phase 2: Route-Organisation (Sprint 3)

| Task | Aufwand | Priorität | Abhängigkeiten |
|------|---------|-----------|----------------|
| chatbot_routes.py aufteilen | 1 Tag | 🟠 P2 | - |
| latex_collab_routes.py aufteilen | 1 Tag | 🟠 P2 | - |
| SocketIO Handler modularisieren | 1 Tag | 🟠 P2 | - |

### Phase 3: Service-Layer (Sprint 4)

| Task | Aufwand | Priorität | Abhängigkeiten |
|------|---------|-----------|----------------|
| AccessControlService erstellen | 1 Tag | 🟡 P3 | - |
| Code-Duplikation eliminieren | 2 Tage | 🟡 P3 | AccessControlService |
| Composables aufteilen | 2 Tage | 🟡 P3 | - |

### Phase 4: Weitere Komponenten (Sprint 5-6)

| Task | Aufwand | Priorität | Abhängigkeiten |
|------|---------|-----------|----------------|
| JudgeSession.vue aufteilen | 2 Tage | 🟡 P3 | - |
| LatexCollabWorkspace.vue aufteilen | 2 Tage | 🟡 P3 | - |
| ChatbotEditor.vue aufteilen | 1-2 Tage | 🟡 P3 | - |

---

## 7. Coding Guidelines für Refactoring

### 7.1 Maximale Dateigrößen

| Typ | Max. Zeilen | Begründung |
|-----|-------------|------------|
| Vue-Komponente | 500 | Lesbarkeit, Single Responsibility |
| Python Service | 400 | Testbarkeit, Fokus |
| Route-Datei | 300 | Übersichtlichkeit |
| Composable | 200 | Wiederverwendbarkeit |
| SocketIO Handler | 200 | Debugging |

### 7.2 Komponenten-Split-Kriterien

Eine Komponente sollte aufgeteilt werden wenn:
- [ ] Mehr als 500 Zeilen Code
- [ ] Mehr als 20 ref/reactive Variablen
- [ ] Mehr als 10 Funktionen
- [ ] Mehr als 3 verschiedene Verantwortlichkeiten
- [ ] Verschachtelte Template-Strukturen >4 Ebenen

### 7.3 Service-Split-Kriterien

Ein Service sollte aufgeteilt werden wenn:
- [ ] Mehr als 400 Zeilen Code
- [ ] Mehr als 15 Methoden
- [ ] Methoden die nicht zusammengehören
- [ ] Mehrere externe Dependencies
- [ ] Schwer zu testen (>10 Mocks nötig)

---

## 8. Testing-Strategie

### 8.1 Test-Abdeckung vor Refactoring

Vor dem Refactoring sollten Tests existieren für:
- [ ] Alle öffentlichen API-Methoden
- [ ] Kritische Business-Logik
- [ ] Edge Cases

### 8.2 Test-Migration

```
Schritt 1: Bestehende Tests sichern
Schritt 2: Tests auf neue Struktur anpassen
Schritt 3: Neue Unit-Tests für extrahierte Services
Schritt 4: Integration-Tests aktualisieren
```

---

## 9. Risiko-Bewertung

### 9.1 Hohe Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Breaking Changes in API | Mittel | Hoch | Backward-Compatibility Layer |
| Regression Bugs | Mittel | Hoch | Comprehensive Testing |
| Performance-Degradation | Niedrig | Mittel | Performance-Benchmarks |

### 9.2 Mitigation-Strategien

1. **Feature Flags**: Neue Komponenten hinter Feature Flags
2. **Incremental Rollout**: Schrittweise Aktivierung
3. **A/B Testing**: Vergleich alt vs. neu
4. **Monitoring**: Error-Rate-Monitoring nach Deployment

---

## 10. Erfolgs-Metriken

### 10.1 Quantitative Metriken

| Metrik | Aktuell | Ziel |
|--------|---------|------|
| Größte Vue-Komponente | 3299 Zeilen | <500 Zeilen |
| Größter Service | 1853 Zeilen | <400 Zeilen |
| Durchschnittliche Datei | ~600 Zeilen | <300 Zeilen |
| Code-Duplikation | ~15% | <5% |

### 10.2 Qualitative Metriken

- [ ] Verbesserte Testbarkeit
- [ ] Schnellere Onboarding-Zeit für neue Entwickler
- [ ] Reduzierte Bug-Fix-Zeit
- [ ] Bessere Code-Reviews

---

## 11. Positive Befunde

Die Analyse hat auch positive Aspekte identifiziert:

- ✅ **Models gut strukturiert**: Klare Trennung (rag.py, chatbot.py, scenario.py)
- ✅ **Permission-System**: Dedizierter Service mit klarem Pattern
- ✅ **Wenig technische Schulden**: Nur 17 TODO/FIXME im Backend, 8 im Frontend
- ✅ **Async-Support**: Services nutzen async für Performance
- ✅ **Design System**: LBtn, LTag, LCard - konsistente UI-Komponenten
- ✅ **Error Handling**: Zentraler Decorator vorhanden

---

## 12. Nächste Schritte

### Sofort (diese Woche)

1. [ ] Review dieses Dokuments mit Team
2. [ ] Priorisierung der Tasks bestätigen
3. [ ] Sprint-Planung aktualisieren

### Kurzfristig (nächste 2 Wochen)

4. [ ] Tests für ChatWithBots.vue schreiben
5. [ ] Tests für ChatService schreiben
6. [ ] Refactoring ChatWithBots.vue starten

### Mittelfristig (nächster Monat)

7. [ ] Phase 1 abschließen
8. [ ] Phase 2 starten
9. [ ] Dokumentation aktualisieren

---

## 13. Fortschritts-Tracker

### 13.1 Abgeschlossene Tasks

| Datum | Task | Dateien | Änderung |
|-------|------|---------|----------|
| 2026-01-01 | JWT Security verbessert | `app/auth/auth_utils.py` | `extract_username_without_validation()` priorisiert jetzt validierte Contexts aus `g.authentik_user`. Fallback auf unverifizierten Token mit Warning-Log. |
| 2026-01-01 | Debug-Endpoints gesichert | `app/routes/judge/session_debug_routes.py` | Alle 3 Debug-Routes verwenden jetzt `@debug_route_protected` + `@handle_api_errors`. Erfordert SYSTEM_ADMIN_API_KEY. |
| 2026-01-01 | Debug-Endpoints verifiziert | `app/routes/oncoco/oncoco_debug_routes.py` | Bereits korrekt mit `@debug_route_protected` geschützt (keine Änderung nötig). |
| 2026-01-01 | Memory Leak Fix | `LatexEditorPane.vue` | `ghostTextTimer` wird jetzt in `onUnmounted()` aufgeräumt. Verhindert Timer-Akkumulation bei wiederholtem Component-Mounting. |
| 2026-01-01 | Deprecated Code entfernt | `app/routes/mail_rating/` | Komplettes Verzeichnis gelöscht (5 Dateien). Duplikat von `rating/` - war nicht in registry.py registriert. |
| 2026-01-01 | SQL Injection Fix | `app/db/seeders/schema_patches.py` | Input-Validierung mit Regex-Patterns für SQL-Identifier und Column-Definitionen. Verhindert Injection in ALTER TABLE Statements. |
| 2026-01-01 | CollabAccessService extrahiert | `app/services/collab/collab_access_service.py`, `latex_collab_routes.py`, `markdown_collab_routes.py` | Zentraler Service für Workspace/Document Access Control. Eliminiert Code-Duplikation zwischen LaTeX und Markdown Collaboration. |
| 2026-01-01 | ChatWithBots.vue aufgeteilt | `ChatWithBots.vue`, `ChatWithBots/` (8 neue Dateien) | Hauptkomponente von 3299 auf 1135 Zeilen reduziert. Extrahierte Composables: useChatSocket.js, useChatSidebar.js, useSourcePanel.js. Extrahierte Komponenten: ChatSidebar.vue, ChatMessageList.vue, ChatInput.vue, SourcePanel.vue. |

### 13.2 Security-Status

| Issue | Datei | Status | Priorität |
|-------|-------|--------|-----------|
| JWT `verify_signature=False` in ungeschütztem Context | `app/auth/auth_utils.py` | ✅ Behoben | KRITISCH |
| Debug-Endpoints ohne Auth | `session_debug_routes.py` | ✅ Behoben | HOCH |
| OnCoCo Debug-Endpoints | `oncoco_debug_routes.py` | ✅ Bereits sicher | HOCH |
| SQL Injection Risiko | `app/db/seeders/schema_patches.py:44` | ✅ Behoben | HOCH |

**Alle bekannten Security-Issues wurden behoben.**

### 13.3 Code-Analyse Zusammenfassung

```
Analyse durchgeführt: 2026-01-01
Analysierte Dateien:
  - Backend: 96 Route-Dateien, 116 Service-Dateien, 18 Model-Dateien
  - Frontend: 170 Komponenten, 13 Composables

Behobene Probleme:
  - Security Issues: 3/3 behoben ✓
  - Code-Duplikation: mail_rating/ gelöscht ✓
  - Memory Leak: ghostTextTimer behoben ✓
  - CollabAccessService: Extrahiert ✓

Offene Refactorings:
  - Große Dateien (>1000 Zeilen): 8 Backend, 6 Frontend

Test Coverage:
  - Backend Services: 21% (18/84)
  - Frontend Components: 14% (24/170)
  - Composables: 100% (13/13)
```

### 13.4 Nächste Prioritäten

| # | Task | Aufwand | Abhängigkeiten |
|---|------|---------|----------------|
| ~~1~~ | ~~chat_service.py aufteilen~~ | ~~2-3 Tage~~ | ✅ Erledigt (1657→590 Zeilen) |
| 1 | latex_collab_routes.py aufteilen | 2-3 Tage | - |
| 2 | JudgeSession.vue aufteilen | 2 Tage | - |
| 3 | agent_chat_service.py aufteilen | 2-3 Tage | - |
| 4 | Test Coverage verbessern (Backend 21% → 50%) | 3-4 Tage | - |

---

## Anhang A: Datei-Inventar

### A.1 Frontend-Dateien >800 Zeilen

```
llars-frontend/src/
├── components/
│   ├── ChatWithBots.vue                              (3299)
│   ├── Judge/JudgeSession.vue                        (2174)
│   ├── Admin/ChatbotAdmin/ChatbotEditor.vue          (1966)
│   ├── Admin/ChatbotAdmin/ChatbotBuilderWizard.vue   (1623)
│   ├── Admin/sections/AuthenticityStatsDialog.vue    (1510)
│   ├── Admin/sections/AdminDockerMonitorSection.vue  (1419)
│   ├── MarkdownCollab/MarkdownGitPanel.vue           (1260)
│   ├── parts/CreateScenarioDialog.vue                (1252)
│   └── ...
└── views/
    ├── LatexCollab/LatexCollabWorkspace.vue          (2857)
    └── MarkdownCollab/MarkdownCollabWorkspace.vue    (1329)
```

### A.2 Backend-Dateien >800 Zeilen

```
app/
├── services/
│   ├── chatbot/agent_chat_service.py                 (1853)
│   ├── chatbot/chat_service.py                       (590) ✅ refaktoriert
│   ├── chatbot/chat_rag_retrieval.py                 (682) ← NEU
│   ├── chatbot/chat_conversation_service.py          (325) ← NEU
│   ├── chatbot/chat_title_service.py                 (181) ← NEU
│   ├── chatbot/chat_prompt_builder.py                (126) ← NEU
│   ├── crawler/modules/crawler_service.py            (1415)
│   ├── anonymize/anonymize_service.py                (1275)
│   ├── rag/collection_embedding_service.py           (1045)
│   └── crawler/modules/crawler_core.py               (924)
├── routes/
│   ├── chatbot/chatbot_routes.py                     (1270)
│   ├── latex_collab/latex_collab_routes.py           (1251)
│   └── markdown_collab/markdown_collab_routes.py     (804)
├── workers/
│   ├── judge_worker_pool.py                          (1067)
│   └── embedding_worker.py                           (825)
└── socketio_handlers/
    └── events_chatbot.py                             (862)
```

---

## Anhang B: Referenzen

- [CLAUDE.md](../../../CLAUDE.md) - Projekt-Dokumentation
- [Vue Style Guide](https://vuejs.org/style-guide/)
- [Python Clean Code](https://github.com/zedr/clean-code-python)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

*Dokument erstellt im Rahmen des LLARS Code-Reviews 2026*
