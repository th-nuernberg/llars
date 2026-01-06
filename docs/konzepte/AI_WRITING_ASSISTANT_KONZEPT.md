# KI-Schreibassistent für LaTeX/Markdown Collab Editor

**Version:** 1.0
**Erstellt:** 29. Dezember 2025
**Status:** Konzeptphase
**Ziel:** Integration einer kontextbewussten KI-Assistenz für wissenschaftliches Schreiben

---

## Inhaltsverzeichnis

1. [Executive Summary](#1-executive-summary)
2. [Architektur-Übersicht](#2-architektur-übersicht)
3. [Feature-Spezifikationen](#3-feature-spezifikationen)
4. [Technische Implementierung](#4-technische-implementierung)
5. [UI/UX Design](#5-uiux-design)
6. [Datenmodell & API](#6-datenmodell--api)
7. [Permissions & Sicherheit](#7-permissions--sicherheit)
8. [Implementierungs-Roadmap](#8-implementierungs-roadmap)
9. [Testing & QA](#9-testing--qa)
10. [Referenzen & Inspirationen](#10-referenzen--inspirationen)

---

## 1. Executive Summary

### 1.1 Projektziel

Integration einer KI-Assistenz in den bestehenden Markdown Collab Editor, die Wissenschaftler beim Schreiben von Papers, Dissertationen und anderen akademischen Texten unterstützt.

### 1.2 Kernfunktionen

| Feature | Beschreibung | Priorität |
|---------|-------------|-----------|
| Ghost Text Completion | Inline-Vorschläge wie GitHub Copilot | Hoch |
| @-Commands | Schnellbefehle im Editor (@cite, @rewrite, etc.) | Hoch |
| AI Sidebar | Chat + Quick Tools Panel | Mittel |
| RAG Citation Finder | Literatursuche in eigenen Collections | Hoch |
| Citation Reviewer | Automatische Prüfung auf fehlende Zitate | Mittel |
| Selection Context Menu | Floating-Menü bei Textmarkierung | Mittel |

### 1.3 Inspirationsquellen

- [Overleaf AI Assist](https://www.digital-science.com/blog/2025/06/digital-science-launches-new-cutting-edge-ai-writing-tools-for-20-million-overleaf-users/)
- [GitHub Copilot](https://code.visualstudio.com/docs/copilot/ai-powered-suggestions)
- [Cursor Editor](https://cursor.com/)
- [Elicit Research Assistant](https://elicit.com/)

---

## 2. Architektur-Übersicht

### 2.1 System-Architektur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Vue 3)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  MarkdownCollab │  │   AI Sidebar    │  │   CodeMirror Extensions     │  │
│  │   Workspace     │  │   Component     │  │   (Ghost Text, Commands)    │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘  │
│           │                    │                          │                 │
│           └────────────────────┼──────────────────────────┘                 │
│                                │                                            │
│                    ┌───────────┴───────────┐                                │
│                    │   AI Writing Service  │                                │
│                    │   (Frontend Service)  │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │ HTTP/REST
┌────────────────────────────────┼────────────────────────────────────────────┐
│                              BACKEND (Flask)                                │
├────────────────────────────────┼────────────────────────────────────────────┤
│                                │                                            │
│                    ┌───────────┴───────────┐                                │
│                    │  AI Writing Routes    │                                │
│                    │  /api/ai-writing/*    │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│           ┌────────────────────┼────────────────────┐                       │
│           │                    │                    │                       │
│  ┌────────┴────────┐  ┌────────┴────────┐  ┌───────┴───────┐               │
│  │   Completion    │  │    Rewrite      │  │   Citation    │               │
│  │    Service      │  │    Service      │  │   Service     │               │
│  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘               │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                            │
│                    ┌───────────┴───────────┐                                │
│                    │     LLM Service       │                                │
│                    │   (LiteLLM Proxy)     │                                │
│                    └───────────┬───────────┘                                │
│                                │                                            │
│           ┌────────────────────┼────────────────────┐                       │
│           │                    │                    │                       │
│  ┌────────┴────────┐  ┌────────┴────────┐  ┌───────┴───────┐               │
│  │   RAG Service   │  │  ChromaDB       │  │   MariaDB     │               │
│  │  (Embeddings)   │  │  (Vectors)      │  │   (Metadata)  │               │
│  └─────────────────┘  └─────────────────┘  └───────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Komponenten-Übersicht

#### Frontend-Komponenten
- [ ] `AISidebar.vue` - Hauptkomponente für AI-Panel
- [ ] `AIChat.vue` - Chat-Interface
- [ ] `AIQuickTools.vue` - Schnellzugriff-Buttons
- [ ] `AISelectionMenu.vue` - Floating-Menü bei Textauswahl
- [ ] `CitationFinder.vue` - RAG-basierte Literatursuche
- [ ] `CitationWarning.vue` - Inline-Warnung für fehlende Zitate
- [ ] `RewritePreview.vue` - Vorschau für Textumformulierungen

#### Frontend-Composables
- [ ] `useAICompletion.js` - Ghost Text Logic
- [ ] `useAICommands.js` - @-Command Handler
- [ ] `useAIChat.js` - Chat State Management
- [ ] `useAICitations.js` - Citation Service Integration
- [ ] `useAISelection.js` - Selection Menu Logic

#### Backend-Services
- [ ] `completion_service.py` - Text Completion
- [ ] `rewrite_service.py` - Text Rewriting
- [ ] `citation_service.py` - RAG Citation Search
- [ ] `chat_service.py` - Conversational AI
- [ ] `review_service.py` - Citation Review

---

## 3. Feature-Spezifikationen

### 3.1 Ghost Text Completion

#### Beschreibung
Inline-Textvorschläge, die als "Ghost Text" (grau/transparent) am Cursor erscheinen. Inspiriert von GitHub Copilot.

#### Verhalten
```
User tippt: "Die Ergebnisse zeigen, dass"
Ghost Text: ░░ die Intervention eine signifikante Reduktion (p<0.05) bewirkte.

Tastenkürzel:
- [Tab]     → Vorschlag akzeptieren
- [Esc]     → Vorschlag ablehnen
- [Alt+]]   → Nächster Vorschlag
- [Alt+[]   → Vorheriger Vorschlag
- [Ctrl+Space] → Manuell anfordern
```

#### Trigger-Bedingungen
- [ ] Nach 500ms Pause am Satzende (`. `, `? `, `! `)
- [ ] Nach LaTeX-Patterns (`\begin{`, `\cite{`, `\ref{`)
- [ ] Nach Markdown-Patterns (`## `, `- `, `1. `)
- [ ] Manuelle Aktivierung via Tastenkürzel
- [ ] Konfigurierbare Verzögerung (User Setting)

#### Technische Anforderungen
- [ ] CodeMirror 6 Extension für Ghost Text Widget
- [ ] Debouncing (500ms default, konfigurierbar)
- [ ] Caching von Vorschlägen
- [ ] Abbruch bei neuer Eingabe
- [ ] Max. 100 Tokens pro Completion
- [ ] Temperatur: 0.3 (niedrig für Konsistenz)

#### Akzeptanzkriterien
- [ ] Ghost Text erscheint nach konfigurierter Verzögerung
- [ ] Tab akzeptiert und fügt Text ein
- [ ] Esc verwirft Vorschlag
- [ ] Keine Interferenz mit normaler Eingabe
- [ ] Performance: <500ms Antwortzeit (nach Debounce)

---

### 3.2 @-Commands (Inline Commands)

#### Beschreibung
Schnellbefehle, die durch Eingabe von `@` im Editor getriggert werden.

#### Verfügbare Commands

| Command | Beschreibung | Parameter |
|---------|-------------|-----------|
| `@ai <prompt>` | Freier KI-Prompt | Freitext |
| `@rewrite` | Wissenschaftlicher formulieren | - |
| `@expand` | Text erweitern/ausbauen | - |
| `@summarize` | Text zusammenfassen | - |
| `@cite` | Zitate vorschlagen (RAG) | Optional: Suchbegriff |
| `@fix` | LaTeX/Grammatik-Fehler | - |
| `@translate <lang>` | Übersetzen | Zielsprache (de, en, fr, es) |
| `@abstract` | Abstract generieren | - |
| `@title` | Titel vorschlagen | - |
| `@outline` | Gliederung erstellen | - |

#### Verhalten
```
User tippt: @
Autocomplete erscheint:
┌─────────────────────────────────────────────┐
│ @ai        💬 Freier KI-Prompt              │
│ @rewrite   ✏️  Wissenschaftlicher formulieren │
│ @cite      📚 Zitate vorschlagen (RAG)      │
│ @expand    📝 Text erweitern                │
│ ...                                         │
└─────────────────────────────────────────────┘
```

#### Technische Anforderungen
- [ ] CodeMirror Autocomplete Extension
- [ ] Command Parser für Parameter-Extraktion
- [ ] Kontext-Awareness (markierter Text oder Cursor-Position)
- [ ] Inline-Ergebnis oder Dialog je nach Command
- [ ] Undo-Support für alle Änderungen

#### Akzeptanzkriterien
- [ ] @ triggert Autocomplete-Menü
- [ ] Commands sind filterbar durch Tippen
- [ ] Enter führt Command aus
- [ ] Esc bricht ab
- [ ] Ergebnisse werden korrekt eingefügt

---

### 3.3 AI Sidebar

#### Beschreibung
Ausklappbares Panel auf der rechten Seite mit Chat-Interface und Quick Tools.

#### Struktur
```
┌──────────────────────────────────────┐
│  🤖 KI-Assistent            [−] [×]  │
├──────────────────────────────────────┤
│                                      │
│  ┌────────────────────────────────┐  │
│  │ QUICK TOOLS                    │  │
│  ├────────────────────────────────┤  │
│  │ [📝 Abstract generieren     ]  │  │
│  │ [🏷️  Titel vorschlagen       ]  │  │
│  │ [✅ Zitate prüfen           ]  │  │
│  │ [🔧 LaTeX-Fehler beheben    ]  │  │
│  └────────────────────────────────┘  │
│                                      │
│  ─────────────────────────────────   │
│                                      │
│  CHAT                                │
│  ┌────────────────────────────────┐  │
│  │ [Chat History]                 │  │
│  └────────────────────────────────┘  │
│                                      │
├──────────────────────────────────────┤
│ ┌──────────────────────────────┐ [📤]│
│ │ Nachricht eingeben...        │    │
│ └──────────────────────────────┘    │
└──────────────────────────────────────┘
```

#### States
- [ ] Collapsed (nur Icon-Leiste, 48px breit)
- [ ] Expanded (volle Breite, 320px default)
- [ ] Resizable (min 280px, max 500px)

#### Quick Tools
- [ ] Abstract generieren
- [ ] Titel vorschlagen
- [ ] Alle Zitate prüfen
- [ ] LaTeX-Fehler beheben
- [ ] Dokument zusammenfassen
- [ ] Gliederung vorschlagen

#### Chat Features
- [ ] Konversationshistorie (pro Dokument)
- [ ] Dokumentkontext wird automatisch mitgesendet
- [ ] Artifacts (einfügbare Code-Blöcke)
- [ ] Markdown-Rendering in Antworten
- [ ] Copy-to-Clipboard für Antworten
- [ ] "In Editor einfügen" Button

#### Technische Anforderungen
- [ ] LocalStorage für Sidebar-State
- [ ] Session Storage für Chat History
- [ ] Streaming-Response Support
- [ ] Max. 4000 Tokens Dokumentkontext
- [ ] Keyboard Shortcut: Ctrl+Shift+A

#### Akzeptanzkriterien
- [ ] Sidebar ist ein-/ausklappbar
- [ ] State persistiert über Sessions
- [ ] Chat funktioniert mit Dokumentkontext
- [ ] Quick Tools führen Aktionen aus
- [ ] Ergebnisse können eingefügt werden

---

### 3.4 RAG Citation Finder

#### Beschreibung
Literatursuche in den RAG Collections des Nutzers mit Relevanz-Ranking.

#### Workflow
1. User markiert Behauptung oder nutzt @cite
2. Dialog öffnet sich mit Suchfeld
3. RAG durchsucht ausgewählte Collections
4. LLM rankt Ergebnisse nach Relevanz
5. User kann Zitate einfügen (BibTeX oder Inline)

#### UI
```
┌─────────────────────────────────────────────────────────────────────────┐
│     📚 Zitate finden                                              [×]   │
├─────────────────────────────────────────────────────────────────────────┤
│  Markierter Text:                                                       │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ "Die digitale Transformation stellt Organisationen vor            │  │
│  │  fundamentale Herausforderungen"                                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Collections: [✓] Digitalisierung  [✓] Management  [ ] Statistik       │
│                                                                         │
│  📊 Gefundene Quellen (5)                                               │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 📄 Brynjolfsson & McAfee (2014)                      Relevanz: 96%│  │
│  │    "The Second Machine Age"                                       │  │
│  │    └─ "...digital technologies are transforming..."               │  │
│  │    [📋 BibTeX] [✏️ Einfügen] [👁 Details]                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                                        [Abbrechen]  [Ausgewählte einfügen]│
└─────────────────────────────────────────────────────────────────────────┘
```

#### Integration mit bestehendem RAG
- [ ] Nutzung von `get_best_embedding_for_collection()`
- [ ] Semantic Search über ChromaDB
- [ ] Metadata-Extraktion (Autor, Jahr, Titel)
- [ ] BibTeX-Generierung aus Metadaten

#### Technische Anforderungen
- [ ] Multi-Collection Suche
- [ ] Relevanz-Scoring via LLM
- [ ] BibTeX-Export
- [ ] APA/MLA/Chicago Formatierung
- [ ] Caching von Suchergebnissen

#### Akzeptanzkriterien
- [ ] Suche in mehreren Collections möglich
- [ ] Ergebnisse sind nach Relevanz sortiert
- [ ] BibTeX kann kopiert werden
- [ ] Inline-Zitat kann eingefügt werden
- [ ] Performance: <3s für Suche

---

### 3.5 Citation Reviewer

#### Beschreibung
Automatische Analyse des Dokuments auf Aussagen, die eine Quellenangabe benötigen.

#### Erkennungskriterien
- Quantitative Aussagen ("40% der...", "N=120")
- Behauptungen ("Studien zeigen...", "Es ist bewiesen...")
- Fremde Definitionen
- Historische Fakten

#### UI im Editor
```
│  6  │ Künstliche Intelligenz wird 40% aller Arbeitsplätze beeinflussen.
│     │                                                              [⚠️]
│     │                          ┌────────────────────────────────────┐
│     │                          │ ⚠️ Zitat empfohlen                 │
│     │                          │                                    │
│     │                          │ Vorschläge:                        │
│     │                          │ 📚 McKinsey (2017) - 94%           │
│     │                          │ 📚 Frey & Osborne (2017) - 89%     │
│     │                          │                                    │
│     │                          │ [Einfügen] [Ignorieren] [Alle]     │
│     │                          └────────────────────────────────────┘
```

#### Status Bar
```
┌────────────────────────────────────────────────────────────────────────┐
│  🔍 Zitat-Prüfung: 2 Warnungen │ 5 korrekt belegt │ [Alle prüfen]     │
└────────────────────────────────────────────────────────────────────────┘
```

#### Technische Anforderungen
- [ ] LLM-basierte Claim Extraction
- [ ] Regex für offensichtliche Patterns (Zahlen, "Studie zeigt")
- [ ] CodeMirror Decoration für Warnungen
- [ ] Gutter Marker für schnelle Übersicht
- [ ] Batch-Verarbeitung für "Alle prüfen"

#### Akzeptanzkriterien
- [ ] Unbelegte Aussagen werden markiert
- [ ] Warnungen sind nicht aufdringlich
- [ ] Vorschläge können eingefügt werden
- [ ] "Ignorieren" versteckt Warnung
- [ ] Status zeigt Gesamtübersicht

---

### 3.6 Selection Context Menu

#### Beschreibung
Floating-Menü, das bei Textmarkierung erscheint.

#### UI
```
████████████████████████████████████
██ Markierter Text                ██
████████████████████████████████████
              │
    ┌─────────┴─────────┐
    │ 🔄  ✂️  📚  💬  🔧 │
    └───────────────────┘

Hover-Labels:
🔄 Umformulieren
✂️ Kürzen
📚 Zitat finden
💬 Fragen...
🔧 LaTeX prüfen
```

#### Trigger
- [ ] Textmarkierung > 10 Zeichen
- [ ] Verzögerung: 300ms nach Markierung
- [ ] Ausblenden bei Cursor-Bewegung außerhalb

#### Aktionen
| Icon | Aktion | Shortcut |
|------|--------|----------|
| 🔄 | Umformulieren | Ctrl+Shift+R |
| 📝 | Erweitern | Ctrl+Shift+E |
| ✂️ | Kürzen | Ctrl+Shift+K |
| 📚 | Zitat finden | Ctrl+Shift+C |
| 💬 | In Chat fragen | Ctrl+Shift+? |
| 🔧 | LaTeX prüfen | Ctrl+Shift+L |

#### Technische Anforderungen
- [ ] Positionierung relativ zur Selektion
- [ ] Collision Detection (Viewport-Grenzen)
- [ ] Keyboard-Navigation
- [ ] Touch-Support für Mobile

#### Akzeptanzkriterien
- [ ] Menü erscheint bei Textmarkierung
- [ ] Position ist immer sichtbar
- [ ] Aktionen funktionieren korrekt
- [ ] Keyboard Shortcuts funktionieren
- [ ] Menü verschwindet bei Klick außerhalb

---

## 4. Technische Implementierung

### 4.1 Backend API Endpoints

#### Completion API
```python
POST /api/ai-writing/complete
{
    "context": "Text vor und nach Cursor (max 1000 Tokens)",
    "cursor_position": 500,
    "document_type": "latex|markdown",
    "max_tokens": 100,
    "temperature": 0.3
}

Response:
{
    "completion": "vorgeschlagener Text",
    "confidence": 0.85,
    "alternatives": ["Alternative 1", "Alternative 2"]
}
```

#### Rewrite API
```python
POST /api/ai-writing/rewrite
{
    "text": "Originaltext",
    "style": "academic|concise|expanded|simplified",
    "context": "Umgebender Text für Kontext",
    "preserve_meaning": true
}

Response:
{
    "result": "Umformulierter Text",
    "changes": [
        {"type": "replaced", "original": "...", "new": "..."}
    ]
}
```

#### Citation API
```python
POST /api/ai-writing/find-citations
{
    "claim": "Zu belegende Aussage",
    "context": "Umgebender Text",
    "collection_ids": [1, 2, 3],
    "limit": 10,
    "format": "bibtex|apa|mla"
}

Response:
{
    "citations": [
        {
            "relevance": 0.96,
            "title": "The Second Machine Age",
            "authors": ["Brynjolfsson", "McAfee"],
            "year": 2014,
            "bibtex": "@book{brynjolfsson2014...}",
            "snippet": "...relevant excerpt...",
            "collection_name": "Digitalisierung"
        }
    ]
}
```

#### Chat API
```python
POST /api/ai-writing/chat
{
    "message": "User-Nachricht",
    "document_content": "Aktueller Dokumentinhalt (max 4000 Tokens)",
    "history": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "stream": true
}

Response (Stream):
data: {"delta": "Teil", "done": false}
data: {"delta": " der ", "done": false}
data: {"delta": "Antwort", "done": true, "artifacts": [...]}
```

#### Review API
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
    ],
    "statistics": {
        "total_claims": 15,
        "cited": 12,
        "uncited": 3
    }
}
```

### 4.2 Backend Implementation Checklist

#### Routes & Controllers
- [ ] `app/routes/ai_writing/__init__.py` - Blueprint Setup
- [ ] `app/routes/ai_writing/routes.py` - API Endpoints
- [ ] `app/routes/ai_writing/schemas.py` - Request/Response Schemas

#### Services
- [ ] `app/services/ai_writing/__init__.py` - Service Exports
- [ ] `app/services/ai_writing/completion_service.py`
- [ ] `app/services/ai_writing/rewrite_service.py`
- [ ] `app/services/ai_writing/citation_service.py`
- [ ] `app/services/ai_writing/chat_service.py`
- [ ] `app/services/ai_writing/review_service.py`
- [ ] `app/services/ai_writing/prompts.py` - System Prompts

#### Integration
- [ ] LiteLLM Proxy Integration
- [ ] RAG Service Integration
- [ ] Rate Limiting
- [ ] Usage Tracking (Analytics)

### 4.3 Frontend Implementation Checklist

#### Services
- [ ] `llars-frontend/src/services/aiWritingService.js` - API Client

#### Composables
- [ ] `llars-frontend/src/components/MarkdownCollab/composables/useAICompletion.js`
- [ ] `llars-frontend/src/components/MarkdownCollab/composables/useAICommands.js`
- [ ] `llars-frontend/src/components/MarkdownCollab/composables/useAIChat.js`
- [ ] `llars-frontend/src/components/MarkdownCollab/composables/useAICitations.js`
- [ ] `llars-frontend/src/components/MarkdownCollab/composables/useAISelection.js`

#### Components
- [ ] `llars-frontend/src/components/MarkdownCollab/ai/AISidebar.vue`
- [ ] `llars-frontend/src/components/MarkdownCollab/ai/AIChat.vue`
- [ ] `llars-frontend/src/components/MarkdownCollab/ai/AIQuickTools.vue`
- [ ] `llars-frontend/src/components/MarkdownCollab/ai/AISelectionMenu.vue`
- [ ] `llars-frontend/src/components/MarkdownCollab/ai/CitationFinder.vue`
- [ ] `llars-frontend/src/components/MarkdownCollab/ai/CitationWarning.vue`
- [ ] `llars-frontend/src/components/MarkdownCollab/ai/RewritePreview.vue`
- [ ] `llars-frontend/src/components/MarkdownCollab/ai/KeyboardShortcutsHelp.vue`

#### CodeMirror Extensions
- [ ] Ghost Text Widget Extension
- [ ] @-Commands Autocomplete Extension
- [ ] Citation Warning Decoration Extension
- [ ] Selection Menu Extension

---

## 5. UI/UX Design

### 5.1 Design System Integration

#### Farben (LLARS Pastel Theme)
```css
--ai-primary: #88c4c8;        /* Soft Teal - AI Accent */
--ai-ghost-text: rgba(var(--v-theme-on-surface), 0.4);
--ai-warning: #e8c87a;        /* Soft Gold - Citation Warning */
--ai-success: #98d4bb;        /* Soft Mint - Cited */
```

#### Komponenten-Styling
```css
/* AI Sidebar */
.ai-sidebar {
  width: 320px;
  border-left: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 0;
}

.ai-sidebar.collapsed {
  width: 48px;
}

/* AI Toggle Header */
.ai-toggle {
  background: linear-gradient(135deg, var(--llars-primary), var(--llars-accent));
  color: white;
  border-radius: 0 0 var(--llars-radius-sm);
}

/* Ghost Text */
.ai-ghost-text {
  color: var(--ai-ghost-text);
  font-style: italic;
  pointer-events: none;
}

/* Citation Warning */
.ai-citation-warning {
  background: rgba(232, 200, 122, 0.15);
  border-bottom: 2px wavy var(--ai-warning);
}

/* Selection Menu */
.ai-selection-menu {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-md);
}
```

### 5.2 Responsive Design

#### Breakpoints
| Breakpoint | Verhalten |
|------------|-----------|
| Desktop (>1200px) | Sidebar + Editor nebeneinander |
| Tablet (768-1200px) | Sidebar als Overlay |
| Mobile (<768px) | Sidebar als Bottom Sheet |

#### Mobile-Anpassungen
- [ ] Bottom Sheet statt Sidebar
- [ ] Vereinfachtes Selection Menu (nur Icons)
- [ ] Ghost Text deaktiviert (Performance)
- [ ] Touch-optimierte Buttons

### 5.3 Accessibility

- [ ] ARIA Labels für alle interaktiven Elemente
- [ ] Keyboard Navigation vollständig
- [ ] Screen Reader Support für Ghost Text
- [ ] High Contrast Mode Support
- [ ] Focus Management bei Dialogen

### 5.4 Animationen

```css
/* Sidebar Toggle */
.ai-sidebar {
  transition: width 0.2s ease;
}

/* Ghost Text Erscheinen */
.ai-ghost-text {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 0.4; }
}

/* Selection Menu */
.ai-selection-menu {
  animation: scaleIn 0.15s ease;
  transform-origin: top center;
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
```

---

## 6. Datenmodell & API

### 6.1 Neue Datenbank-Tabellen

#### ai_chat_sessions
```sql
CREATE TABLE ai_chat_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    document_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES markdown_collab_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_document_user (document_id, user_id)
);
```

#### ai_chat_messages
```sql
CREATE TABLE ai_chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    artifacts JSON,
    tokens_used INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session (session_id)
);
```

#### ai_usage_tracking
```sql
CREATE TABLE ai_usage_tracking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    feature ENUM('completion', 'rewrite', 'citation', 'chat', 'review') NOT NULL,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    model_id VARCHAR(100),
    latency_ms INT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_feature (user_id, feature),
    INDEX idx_created (created_at)
);
```

#### ai_citation_ignores
```sql
CREATE TABLE ai_citation_ignores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    document_id INT NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    line_number INT,
    ignored_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES markdown_collab_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (ignored_by) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_ignore (document_id, text_hash)
);
```

### 6.2 Migration Checklist

- [ ] Migration Script erstellen
- [ ] Indizes optimieren
- [ ] Foreign Keys validieren
- [ ] Rollback Script

---

## 7. Permissions & Sicherheit

### 7.1 Neue Permissions

```python
# app/db/seeders/permissions.py

AI_WRITING_PERMISSIONS = [
    # Basis-Permission
    ('feature:markdown_collab:ai', 'Use AI writing assistance'),

    # Feature-spezifische Permissions
    ('feature:markdown_collab:ai:completion', 'Use AI text completion'),
    ('feature:markdown_collab:ai:rewrite', 'Use AI text rewriting'),
    ('feature:markdown_collab:ai:citations', 'Use AI citation suggestions'),
    ('feature:markdown_collab:ai:chat', 'Use AI chat assistant'),
    ('feature:markdown_collab:ai:review', 'Use AI citation review'),

    # Admin-Permissions
    ('admin:ai_writing:view_usage', 'View AI usage statistics'),
    ('admin:ai_writing:manage_limits', 'Manage AI usage limits'),
]
```

### 7.2 Rollen-Zuordnung

| Rolle | completion | rewrite | citations | chat | review |
|-------|------------|---------|-----------|------|--------|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| researcher | ✅ | ✅ | ✅ | ✅ | ✅ |
| chatbot_manager | ✅ | ✅ | ❌ | ✅ | ❌ |
| evaluator | ❌ | ❌ | ❌ | ❌ | ❌ |

### 7.3 Rate Limiting

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

### 7.4 Sicherheitsmaßnahmen

- [ ] Input Sanitization für alle Prompts
- [ ] Output Filtering (keine sensiblen Daten)
- [ ] Prompt Injection Prevention
- [ ] Rate Limiting per User
- [ ] Token Budget per User/Tag
- [ ] Audit Logging für AI-Nutzung

---

## 8. Implementierungs-Roadmap

### Phase 1: Foundation (Woche 1-2)

#### Backend Setup
- [ ] Blueprint und Route-Struktur erstellen
- [ ] LLM Service Integration (LiteLLM)
- [ ] Basis-Prompts definieren
- [ ] Unit Tests für Services

#### Frontend Setup
- [ ] AI Service erstellen
- [ ] Basis-Composables anlegen
- [ ] AI Sidebar Komponente (ohne Funktionen)

### Phase 2: Core Features (Woche 3-4)

#### Ghost Text Completion
- [ ] CodeMirror Extension entwickeln
- [ ] Backend Endpoint implementieren
- [ ] Debouncing & Caching
- [ ] Keyboard Shortcuts

#### @-Commands
- [ ] Autocomplete Extension
- [ ] Command Parser
- [ ] Backend Endpoints für jeden Command
- [ ] Inline-Ergebnis-Anzeige

### Phase 3: AI Sidebar (Woche 5-6)

#### Chat Interface
- [ ] Chat UI Komponente
- [ ] Streaming Response Handler
- [ ] Chat History Persistenz
- [ ] Artifacts System

#### Quick Tools
- [ ] Tool-Buttons UI
- [ ] Backend-Integration
- [ ] Ergebnis-Dialoge

### Phase 4: Citation Intelligence (Woche 7-8)

#### RAG Integration
- [ ] Citation Service mit RAG
- [ ] BibTeX Generator
- [ ] Citation Finder Dialog

#### Citation Review
- [ ] Claim Extraction
- [ ] Warning Decorations
- [ ] Review Status Bar

### Phase 5: Polish & Testing (Woche 9-10)

#### UX Verbesserungen
- [ ] Selection Context Menu
- [ ] Keyboard Shortcuts Help
- [ ] Loading States
- [ ] Error Handling

#### Testing & QA
- [ ] E2E Tests
- [ ] Performance Optimierung
- [ ] Accessibility Audit
- [ ] User Acceptance Testing

---

## 9. Testing & QA

### 9.1 Unit Tests

#### Backend Tests
- [ ] `test_completion_service.py`
- [ ] `test_rewrite_service.py`
- [ ] `test_citation_service.py`
- [ ] `test_chat_service.py`
- [ ] `test_review_service.py`
- [ ] `test_ai_routes.py`

#### Frontend Tests
- [ ] `useAICompletion.spec.js`
- [ ] `useAICommands.spec.js`
- [ ] `useAIChat.spec.js`
- [ ] `AISidebar.spec.js`
- [ ] `CitationFinder.spec.js`

### 9.2 Integration Tests

- [ ] Completion Flow (Frontend → Backend → LLM → Frontend)
- [ ] Chat Session Flow
- [ ] Citation Search Flow (inkl. RAG)
- [ ] Rate Limiting Behaviour

### 9.3 E2E Tests

- [ ] Ghost Text erscheint und kann akzeptiert werden
- [ ] @-Commands funktionieren end-to-end
- [ ] Chat-Konversation vollständig
- [ ] Citation Finder findet und fügt ein
- [ ] Citation Review markiert und kann ignoriert werden

### 9.4 Performance Tests

- [ ] Completion Latency < 500ms (p95)
- [ ] Chat Response Start < 1s (p95)
- [ ] Citation Search < 3s (p95)
- [ ] Memory Footprint < 50MB zusätzlich

### 9.5 Accessibility Tests

- [ ] Keyboard-only Navigation
- [ ] Screen Reader Compatibility
- [ ] Color Contrast (WCAG AA)
- [ ] Focus Management

---

## 10. Referenzen & Inspirationen

### 10.1 Produkte & Tools

| Tool | Feature | Inspiration für |
|------|---------|-----------------|
| [Overleaf AI Assist](https://www.digital-science.com/blog/2025/06/digital-science-launches-new-cutting-edge-ai-writing-tools-for-20-million-overleaf-users/) | TeXGPT, Language Feedback | LaTeX-spezifische Hilfe |
| [GitHub Copilot](https://code.visualstudio.com/docs/copilot/ai-powered-suggestions) | Ghost Text, NES | Inline Completion UX |
| [Cursor](https://cursor.com/) | AI-First Editor | Context-aware Chat |
| [Elicit](https://elicit.com/) | Research Assistant | Citation Finding |
| [Semantic Scholar](https://www.semanticscholar.org/) | TLDR Summaries | Paper Summarization |
| [Writefull](https://www.writefull.com/writefull-for-overleaf) | Language Feedback | Academic Writing Style |

### 10.2 UX Pattern Resources

- [Shape of AI](https://www.shapeof.ai) - AI UX Patterns
- [AI UI Patterns](https://www.patterns.dev/react/ai-ui-patterns/) - React AI Patterns
- [Smashing Magazine - AI Interfaces](https://www.smashingmagazine.com/2025/07/design-patterns-ai-interfaces/)

### 10.3 Technische Dokumentation

- [CodeMirror 6 Documentation](https://codemirror.net/docs/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

---

## Changelog

| Version | Datum | Änderungen |
|---------|-------|------------|
| 1.0 | 29.12.2025 | Initial Konzept |

---

## Appendix

### A. System Prompts

#### Completion System Prompt
```
Du bist ein wissenschaftlicher Schreibassistent. Vervollständige den folgenden Text auf akademische, präzise Weise.
- Halte den Stil des bestehenden Textes bei
- Verwende Fachbegriffe korrekt
- Schreibe prägnant und klar
- Maximale Länge: 1-2 Sätze
```

#### Rewrite System Prompt
```
Du bist ein Lektor für wissenschaftliche Texte. Formuliere den folgenden Text um:
- Verwende akademischen Sprachstil
- Eliminiere umgangssprachliche Ausdrücke
- Verbessere die Satzstruktur
- Behalte die ursprüngliche Bedeutung bei
```

#### Citation Review System Prompt
```
Analysiere den folgenden Text und identifiziere Aussagen, die eine Quellenangabe benötigen:
- Statistische Behauptungen (Zahlen, Prozente)
- Faktische Aussagen ("Studien zeigen...")
- Definitionen und Fachbegriffe
- Historische Fakten

Gib für jede Aussage zurück:
- Position im Text
- Art der Aussage
- Dringlichkeit (hoch/mittel/niedrig)
```

### B. Keyboard Shortcuts Reference

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

### C. Error Codes

| Code | Beschreibung | User Message |
|------|--------------|--------------|
| `AI_001` | Rate Limit erreicht | "Zu viele Anfragen. Bitte warte einen Moment." |
| `AI_002` | Token Budget erschöpft | "Tägliches AI-Limit erreicht." |
| `AI_003` | LLM nicht verfügbar | "KI-Service momentan nicht verfügbar." |
| `AI_004` | Ungültige Eingabe | "Eingabe konnte nicht verarbeitet werden." |
| `AI_005` | Timeout | "Anfrage hat zu lange gedauert." |
