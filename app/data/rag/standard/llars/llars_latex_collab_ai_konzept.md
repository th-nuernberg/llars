# LLARS LaTeX Collab KI-Schreibassistent - Implementierungskonzept

**Projekt:** LLARS - LLM Assisted Research System
**Feature:** KI-Schreibassistent für LaTeX/Markdown Collab Editor
**Version:** 1.0.0
**Erstellt:** 29. Dezember 2025
**Pfad:** `/LatexCollabAI` (Test-Version)

---

## 1. ÜBERSICHT & ZIEL

### Was wird gebaut?
Ein KI-Schreibassistent, der direkt im LaTeX/Markdown Collab Editor integriert ist und Wissenschaftler beim Verfassen akademischer Texte unterstützt.

### Kernidee
Kombination aus:
- **Inline-Hilfe** (Ghost Text wie GitHub Copilot)
- **@-Commands** (Schnellbefehle im Editor)
- **AI Sidebar** (Chat + Quick Tools)
- **RAG-basierte Literatursuche** (Zitate aus eigenen Collections)

### Inspiration
- Overleaf AI Assist (TeXGPT, Language Feedback)
- GitHub Copilot (Ghost Text, Next Edit Suggestions)
- Cursor Editor (AI-First, Context-aware)
- Elicit (Research Assistant, Citation Management)

---

## 2. ARCHITEKTUR

### 2.1 System-Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Vue 3 + Vuetify)                        │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    LatexCollabAIWorkspace.vue                        │   │
│  │  ┌────────────┬────────────────────────────────┬─────────────────┐   │   │
│  │  │ Tree Panel │       Editor + Preview         │   AI Sidebar    │   │   │
│  │  │            │  ┌──────────────────────────┐  │  ┌───────────┐  │   │   │
│  │  │ 📁 Files   │  │   CodeMirror 6 Editor    │  │  │ Quick     │  │   │   │
│  │  │            │  │   + Ghost Text Extension │  │  │ Tools     │  │   │   │
│  │  │            │  │   + @-Commands           │  │  ├───────────┤  │   │   │
│  │  │            │  │   + Selection Menu       │  │  │ Chat      │  │   │   │
│  │  │            │  │   + Citation Warnings    │  │  │ Interface │  │   │   │
│  │  │            │  └──────────────────────────┘  │  └───────────┘  │   │   │
│  │  └────────────┴────────────────────────────────┴─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                        │
│                    │     aiWritingService.js       │                        │
│                    └───────────────┬───────────────┘                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │ HTTP/REST API
┌────────────────────────────────────┼────────────────────────────────────────┐
│                           BACKEND (Flask)                                   │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                        │
│                    │   /api/ai-writing/* Routes    │                        │
│                    └───────────────┬───────────────┘                        │
│                                    │                                        │
│           ┌────────────────────────┼────────────────────────┐               │
│           │                        │                        │               │
│  ┌────────┴────────┐  ┌────────────┴────────┐  ┌───────────┴───────┐       │
│  │   completion    │  │     rewrite         │  │    citation       │       │
│  │   _service.py   │  │     _service.py     │  │    _service.py    │       │
│  └────────┬────────┘  └─────────┬───────────┘  └───────┬───────────┘       │
│           │                     │                      │                    │
│           └─────────────────────┼──────────────────────┘                    │
│                                 │                                           │
│                    ┌────────────┴────────────┐                              │
│                    │      LLM Service        │                              │
│                    │      (LiteLLM)          │                              │
│                    └────────────┬────────────┘                              │
│                                 │                                           │
│           ┌─────────────────────┼─────────────────────┐                     │
│           │                     │                     │                     │
│  ┌────────┴────────┐  ┌─────────┴─────────┐  ┌───────┴───────┐             │
│  │   RAG Service   │  │    ChromaDB       │  │   MariaDB     │             │
│  │   (Embeddings)  │  │    (Vectors)      │  │   (Metadata)  │             │
│  └─────────────────┘  └───────────────────┘  └───────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Dateistruktur

```
llars-frontend/src/
├── views/LatexCollabAI/
│   ├── LatexCollabAIHome.vue           # Home (kopiert von LatexCollab)
│   └── LatexCollabAIWorkspace.vue      # Workspace mit AI-Integration
│
├── components/LatexCollabAI/
│   ├── LatexAIEditorPane.vue           # Editor mit AI Extensions
│   ├── LatexPdfViewer.vue              # PDF Preview (wiederverwendet)
│   │
│   ├── ai/                             # AI-spezifische Komponenten
│   │   ├── AISidebar.vue               # Hauptkomponente Sidebar
│   │   ├── AIChat.vue                  # Chat Interface
│   │   ├── AIQuickTools.vue            # Quick Action Buttons
│   │   ├── AISelectionMenu.vue         # Floating Menu bei Selection
│   │   ├── CitationFinder.vue          # RAG-basierte Literatursuche
│   │   ├── CitationWarning.vue         # Inline Warning für fehlende Zitate
│   │   ├── RewritePreview.vue          # Diff-Preview für Umformulierungen
│   │   └── KeyboardShortcutsHelp.vue   # Shortcuts Overlay
│   │
│   └── composables/
│       ├── useAICompletion.js          # Ghost Text Logic
│       ├── useAICommands.js            # @-Command Handler
│       ├── useAIChat.js                # Chat State Management
│       ├── useAICitations.js           # Citation Service Integration
│       └── useAISelection.js           # Selection Menu Logic
│
├── services/
│   └── aiWritingService.js             # API Client für Backend

app/
├── routes/ai_writing/
│   ├── __init__.py                     # Blueprint Setup
│   ├── routes.py                       # API Endpoints
│   └── schemas.py                      # Request/Response Validation
│
├── services/ai_writing/
│   ├── __init__.py
│   ├── completion_service.py           # Text Completion
│   ├── rewrite_service.py              # Umformulierung
│   ├── citation_service.py             # RAG Citation Search
│   ├── chat_service.py                 # Conversational AI
│   ├── review_service.py               # Citation Review
│   └── prompts.py                      # System Prompts
```

---

## 3. FEATURES IM DETAIL

### 3.1 Ghost Text Completion

**Was:** Inline-Textvorschläge als grauer "Ghost Text" am Cursor

**Trigger:**
- Nach 500ms Pause am Satzende (`. `, `? `, `! `)
- Nach LaTeX-Patterns: `\begin{`, `\cite{`, `\ref{`, `\section{`
- Manuelle Aktivierung: `Ctrl+Space`

**Keyboard:**
- `Tab` → Akzeptieren
- `Esc` → Ablehnen
- `Alt+]` → Nächster Vorschlag
- `Alt+[` → Vorheriger Vorschlag

**Technisch:**
```javascript
// CodeMirror 6 Extension
const ghostTextExtension = [
  ghostTextField,           // StateField für Decoration
  ghostTextPlugin,          // ViewPlugin für API Calls
  ghostTextKeymap           // Keymap für Tab/Esc
]

// API Call
POST /api/ai-writing/complete
{
  "context": "500 Tokens vor + nach Cursor",
  "cursor_position": 250,
  "document_type": "latex",
  "max_tokens": 100,
  "temperature": 0.3
}
```

**Styling:**
```css
.ai-ghost-text {
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-style: italic;
  pointer-events: none;
}
```

### 3.2 @-Commands (Inline Commands)

**Was:** Schnellbefehle durch `@` im Editor

**Verfügbare Commands:**

| Command | Funktion | Parameter |
|---------|----------|-----------|
| `@ai <prompt>` | Freier KI-Prompt | Freitext |
| `@rewrite` | Wissenschaftlicher formulieren | - |
| `@expand` | Text ausbauen | - |
| `@summarize` | Zusammenfassen | - |
| `@cite` | Zitate vorschlagen (RAG) | Optional: Suchbegriff |
| `@fix` | LaTeX/Grammatik-Fehler | - |
| `@translate <lang>` | Übersetzen | de, en, fr, es |
| `@abstract` | Abstract generieren | - |
| `@title` | Titel vorschlagen | - |
| `@outline` | Gliederung erstellen | - |

**Technisch:**
```javascript
// CodeMirror Autocomplete
const aiCommandsCompletion = autocompletion({
  override: [
    (context) => {
      const match = context.matchBefore(/@\w*/)
      if (!match) return null
      return {
        from: match.from,
        options: AI_COMMANDS.map(cmd => ({
          label: cmd.name,
          detail: cmd.description,
          apply: () => executeCommand(cmd)
        }))
      }
    }
  ]
})
```

### 3.3 AI Sidebar

**Was:** Ausklappbares Panel rechts mit Chat + Quick Tools

**States:**
- Collapsed: 48px (nur Toggle-Button)
- Expanded: 320px (default)
- Resizable: 280px - 500px

**Quick Tools:**
- Abstract generieren
- Titel vorschlagen
- Alle Zitate prüfen
- LaTeX-Fehler beheben
- Dokument zusammenfassen

**Chat Features:**
- Konversationshistorie pro Dokument
- Dokumentkontext wird automatisch mitgesendet (max 4000 Tokens)
- Markdown-Rendering in Antworten
- Artifacts (einfügbare Code-Blöcke)
- "In Editor einfügen" Button

**Keyboard:** `Ctrl+Shift+A`

### 3.4 RAG Citation Finder

**Was:** Literatursuche in eigenen RAG Collections

**Workflow:**
1. Text markieren oder `@cite` eingeben
2. Dialog öffnet sich
3. Collections auswählen
4. RAG durchsucht semantisch
5. LLM rankt nach Relevanz
6. Zitat einfügen (BibTeX oder Inline)

**API:**
```python
POST /api/ai-writing/find-citations
{
  "claim": "Die digitale Transformation...",
  "context": "Umgebender Text",
  "collection_ids": [1, 2, 3],
  "limit": 10,
  "format": "bibtex"
}
```

**Integration mit bestehendem RAG:**
- Nutzt `get_best_embedding_for_collection()`
- Semantic Search über ChromaDB
- Metadata für BibTeX (Autor, Jahr, Titel)

### 3.5 Citation Reviewer

**Was:** Automatische Prüfung auf fehlende Quellenangaben

**Erkennt:**
- Quantitative Aussagen ("40% der...", "N=120")
- Behauptungen ("Studien zeigen...", "Es ist bewiesen...")
- Definitionen und Fachbegriffe
- Historische Fakten

**UI:**
- Gelbe Wellenlinie unter unbelegten Aussagen
- Inline-Popup mit Vorschlägen
- Status Bar: "2 Warnungen | 5 belegt"

**API:**
```python
POST /api/ai-writing/review-citations
{
  "content": "Gesamter Dokumentinhalt"
}

Response:
{
  "warnings": [
    {
      "position": {"line": 10, "from": 0, "to": 65},
      "text": "40% aller Arbeitsplätze...",
      "type": "statistical_claim",
      "severity": "high",
      "suggestions": [...]
    }
  ]
}
```

### 3.6 Selection Context Menu

**Was:** Floating-Menü bei Textmarkierung

**Aktionen:**
| Icon | Aktion | Shortcut |
|------|--------|----------|
| 🔄 | Umformulieren | Ctrl+Shift+R |
| 📝 | Erweitern | Ctrl+Shift+E |
| ✂️ | Kürzen | Ctrl+Shift+K |
| 📚 | Zitat finden | Ctrl+Shift+C |
| 💬 | In Chat fragen | Ctrl+Shift+? |
| 🔧 | LaTeX prüfen | Ctrl+Shift+L |

**Trigger:** Textmarkierung > 10 Zeichen, 300ms Verzögerung

---

## 4. API ENDPOINTS

### 4.1 Completion
```
POST /api/ai-writing/complete
Authorization: Bearer <token>

Request:
{
  "context": string,          // Text um Cursor (max 1000 Tokens)
  "cursor_position": int,     // Position im Context
  "document_type": "latex" | "markdown",
  "max_tokens": int,          // Default: 100
  "temperature": float        // Default: 0.3
}

Response:
{
  "completion": string,
  "confidence": float,
  "alternatives": string[]
}
```

### 4.2 Rewrite
```
POST /api/ai-writing/rewrite
Authorization: Bearer <token>

Request:
{
  "text": string,             // Zu umformulierender Text
  "style": "academic" | "concise" | "expanded" | "simplified",
  "context": string,          // Umgebender Text für Kontext
  "preserve_meaning": bool    // Default: true
}

Response:
{
  "result": string,
  "changes": [
    {"type": "replaced", "original": string, "new": string}
  ]
}
```

### 4.3 Find Citations
```
POST /api/ai-writing/find-citations
Authorization: Bearer <token>

Request:
{
  "claim": string,            // Zu belegende Aussage
  "context": string,          // Umgebender Text
  "collection_ids": int[],    // RAG Collections
  "limit": int,               // Default: 10
  "format": "bibtex" | "apa" | "mla"
}

Response:
{
  "citations": [
    {
      "relevance": float,
      "title": string,
      "authors": string[],
      "year": int,
      "bibtex": string,
      "snippet": string,
      "collection_name": string
    }
  ]
}
```

### 4.4 Chat
```
POST /api/ai-writing/chat
Authorization: Bearer <token>

Request:
{
  "message": string,
  "document_content": string, // Max 4000 Tokens
  "history": [
    {"role": "user" | "assistant", "content": string}
  ],
  "stream": bool              // Default: true
}

Response (wenn stream=true):
data: {"delta": "Teil", "done": false}
data: {"delta": " der Antwort", "done": true, "artifacts": [...]}

Response (wenn stream=false):
{
  "response": string,
  "artifacts": [...]
}
```

### 4.5 Review Citations
```
POST /api/ai-writing/review-citations
Authorization: Bearer <token>

Request:
{
  "content": string           // Gesamter Dokumentinhalt
}

Response:
{
  "warnings": [
    {
      "position": {"line": int, "from": int, "to": int},
      "text": string,
      "type": "statistical_claim" | "factual_claim" | "definition",
      "severity": "high" | "medium" | "low",
      "suggestions": [Citation]
    }
  ],
  "statistics": {
    "total_claims": int,
    "cited": int,
    "uncited": int
  }
}
```

---

## 5. PERMISSIONS

### Neue Permissions
```python
AI_WRITING_PERMISSIONS = [
  ('feature:markdown_collab:ai', 'Use AI writing assistance'),
  ('feature:markdown_collab:ai:completion', 'Use AI text completion'),
  ('feature:markdown_collab:ai:rewrite', 'Use AI text rewriting'),
  ('feature:markdown_collab:ai:citations', 'Use AI citation suggestions'),
  ('feature:markdown_collab:ai:chat', 'Use AI chat assistant'),
  ('feature:markdown_collab:ai:review', 'Use AI citation review'),
]
```

### Rollen-Zuordnung
| Rolle | completion | rewrite | citations | chat | review |
|-------|------------|---------|-----------|------|--------|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| researcher | ✅ | ✅ | ✅ | ✅ | ✅ |
| chatbot_manager | ✅ | ✅ | ❌ | ✅ | ❌ |
| evaluator | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 6. DATENBANK

### Neue Tabellen

```sql
-- Chat Sessions
CREATE TABLE ai_chat_sessions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  document_id INT NOT NULL,
  user_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (document_id) REFERENCES markdown_collab_documents(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Chat Messages
CREATE TABLE ai_chat_messages (
  id INT PRIMARY KEY AUTO_INCREMENT,
  session_id INT NOT NULL,
  role ENUM('user', 'assistant', 'system') NOT NULL,
  content TEXT NOT NULL,
  artifacts JSON,
  tokens_used INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES ai_chat_sessions(id) ON DELETE CASCADE
);

-- Usage Tracking
CREATE TABLE ai_usage_tracking (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  feature ENUM('completion', 'rewrite', 'citation', 'chat', 'review') NOT NULL,
  tokens_input INT DEFAULT 0,
  tokens_output INT DEFAULT 0,
  model_id VARCHAR(100),
  latency_ms INT,
  success BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Ignorierte Zitat-Warnungen
CREATE TABLE ai_citation_ignores (
  id INT PRIMARY KEY AUTO_INCREMENT,
  document_id INT NOT NULL,
  text_hash VARCHAR(64) NOT NULL,
  ignored_by INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (document_id) REFERENCES markdown_collab_documents(id) ON DELETE CASCADE,
  UNIQUE KEY (document_id, text_hash)
);
```

---

## 7. SYSTEM PROMPTS

### Completion Prompt
```
Du bist ein wissenschaftlicher Schreibassistent. Vervollständige den folgenden Text auf akademische, präzise Weise.

Regeln:
- Halte den Stil des bestehenden Textes bei
- Verwende Fachbegriffe korrekt
- Schreibe prägnant und klar
- Maximale Länge: 1-2 Sätze
- Bei LaTeX: Korrekte Syntax verwenden

Kontext:
{context}

Vervollständige ab Position {cursor_position}:
```

### Rewrite Prompt
```
Du bist ein Lektor für wissenschaftliche Texte. Formuliere den folgenden Text um.

Ziel-Stil: {style}
- academic: Formell, präzise, Fachsprache
- concise: Kurz und prägnant
- expanded: Ausführlicher mit mehr Details
- simplified: Einfacher verständlich

Originaltext:
{text}

Kontext (für Konsistenz):
{context}

Umformulierter Text:
```

### Citation Review Prompt
```
Analysiere den folgenden wissenschaftlichen Text und identifiziere Aussagen, die eine Quellenangabe benötigen.

Kriterien für zitationspflichtige Aussagen:
1. Statistische Behauptungen (Zahlen, Prozente, "N=...")
2. Faktische Aussagen ("Studien zeigen...", "Es ist bewiesen...")
3. Definitionen und Fachbegriffe die nicht selbstverständlich sind
4. Historische Fakten und Daten
5. Fremde Theorien oder Modelle

Ignoriere:
- Allgemeinwissen
- Eigene Schlussfolgerungen des Autors
- Methodenbeschreibungen

Für jede gefundene Aussage gib zurück:
- Exakte Position (Zeile, Start, Ende)
- Den Aussagetext
- Typ (statistical_claim, factual_claim, definition, theory)
- Dringlichkeit (high, medium, low)

Text:
{content}
```

---

## 8. UI/UX DETAILS

### Farben (LLARS Pastel Theme)
```css
--ai-primary: #88c4c8;        /* Soft Teal - AI Accent */
--ai-ghost-text: rgba(var(--v-theme-on-surface), 0.4);
--ai-warning: #e8c87a;        /* Soft Gold - Citation Warning */
--ai-success: #98d4bb;        /* Soft Mint - Cited */
```

### AI Sidebar Styling
```css
.ai-sidebar {
  width: 320px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-left: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  transition: width 0.2s ease;
}

.ai-sidebar.collapsed {
  width: 48px;
}

.ai-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  background: linear-gradient(135deg, var(--llars-primary), var(--llars-accent));
  color: white;
  font-weight: 600;
}
```

### Ghost Text Animation
```css
.ai-ghost-text {
  animation: ghostFadeIn 0.2s ease;
}

@keyframes ghostFadeIn {
  from { opacity: 0; }
  to { opacity: 0.4; }
}
```

### Selection Menu
```css
.ai-selection-menu {
  position: fixed;
  z-index: 1000;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-md);
  padding: 4px;
  display: flex;
  gap: 2px;
  animation: menuScaleIn 0.15s ease;
}

@keyframes menuScaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
```

---

## 9. KEYBOARD SHORTCUTS

| Shortcut | Aktion |
|----------|--------|
| `Tab` | Ghost Text akzeptieren |
| `Esc` | Ghost Text ablehnen |
| `Alt+]` | Nächster Vorschlag |
| `Alt+[` | Vorheriger Vorschlag |
| `Ctrl+Space` | Completion manuell anfordern |
| `Ctrl+Shift+A` | AI Sidebar toggle |
| `Ctrl+Shift+R` | Markierung umformulieren |
| `Ctrl+Shift+C` | Zitat für Markierung finden |
| `Ctrl+Shift+E` | Markierung erweitern |
| `Ctrl+Shift+K` | Markierung kürzen |
| `Ctrl+Shift+?` | Chat fokussieren |
| `Ctrl+Shift+/` | Shortcuts Hilfe anzeigen |

---

## 10. RATE LIMITING

```python
AI_RATE_LIMITS = {
  'completion': {
    'requests_per_minute': 30,
    'tokens_per_day': 50000
  },
  'rewrite': {
    'requests_per_minute': 10,
    'tokens_per_day': 30000
  },
  'chat': {
    'requests_per_minute': 20,
    'tokens_per_day': 100000
  },
  'citation': {
    'requests_per_minute': 10,
    'requests_per_day': 100
  },
  'review': {
    'requests_per_minute': 5,
    'requests_per_day': 20
  }
}
```

---

## 11. IMPLEMENTIERUNGS-REIHENFOLGE

### Phase 1: Foundation
1. [ ] Backend Blueprint + Routes erstellen
2. [ ] LLM Service Integration (LiteLLM)
3. [ ] Basis-Prompts definieren
4. [ ] Frontend Service (aiWritingService.js)
5. [ ] Test-Views kopieren (LatexCollabAI)

### Phase 2: Ghost Text
1. [ ] CodeMirror Ghost Text Extension
2. [ ] Backend /complete Endpoint
3. [ ] Debouncing + Caching
4. [ ] Keyboard Shortcuts (Tab/Esc)

### Phase 3: @-Commands
1. [ ] Autocomplete Extension
2. [ ] Command Parser
3. [ ] Backend Endpoints pro Command
4. [ ] Inline-Ergebnis-Anzeige

### Phase 4: AI Sidebar
1. [ ] Sidebar Komponente (collapsed/expanded)
2. [ ] Quick Tools UI + Integration
3. [ ] Chat Interface
4. [ ] Streaming Response Handler
5. [ ] Artifacts System

### Phase 5: Citation Intelligence
1. [ ] Citation Service mit RAG Integration
2. [ ] Citation Finder Dialog
3. [ ] BibTeX Generator
4. [ ] Citation Reviewer
5. [ ] Warning Decorations

### Phase 6: Polish
1. [ ] Selection Context Menu
2. [ ] Keyboard Shortcuts Help
3. [ ] Error Handling + Loading States
4. [ ] Mobile Responsive
5. [ ] E2E Tests

---

## 12. ABHÄNGIGKEITEN

### Bestehende Services die genutzt werden:
- `services/rag/embedding_model_service.py` - Für Citation Search
- `services/rag/search_service.py` - Semantic Search
- `services/llm/litellm_service.py` - LLM Calls
- `composables/useYjsCollaboration.js` - Real-time Sync

### Neue NPM Packages (Frontend):
- Keine neuen nötig, alles mit CodeMirror 6 möglich

### Neue Python Packages (Backend):
- Keine neuen nötig, LiteLLM bereits vorhanden

---

## 13. WICHTIGE HINWEISE FÜR IMPLEMENTIERUNG

### CodeMirror Extensions
- Extensions müssen als Array zurückgegeben werden
- StateField für persistente Daten
- ViewPlugin für Side-Effects (API Calls)
- Decoration für visuelle Änderungen

### YJS Integration
- AI-Änderungen müssen über YJS transacted werden
- Cursor-Position mit RelativePosition tracken
- Ghost Text NICHT in YJS speichern (nur lokal)

### API Error Handling
- Alle Endpoints mit @handle_api_errors
- Rate Limit Errors: 429 mit Retry-After Header
- Timeout: 30s für Completion, 60s für Chat

### Performance
- Completion Debounce: 500ms
- Chat History: Max 10 Messages im Context
- Document Context: Max 4000 Tokens
- Ghost Text: Nur 1 aktiver Request gleichzeitig

---

## 14. TESTING CHECKLISTE

### Unit Tests
- [ ] completion_service.py
- [ ] rewrite_service.py
- [ ] citation_service.py
- [ ] useAICompletion.js
- [ ] useAICommands.js

### Integration Tests
- [ ] Completion Flow (Frontend → Backend → LLM)
- [ ] Chat Session mit History
- [ ] Citation Search mit RAG

### E2E Tests
- [ ] Ghost Text erscheint und kann akzeptiert werden
- [ ] @-Commands funktionieren
- [ ] Chat-Konversation
- [ ] Citation Finder findet und fügt ein

---

*Dieses Dokument dient als Single Source of Truth für die Implementierung des KI-Schreibassistenten.*
