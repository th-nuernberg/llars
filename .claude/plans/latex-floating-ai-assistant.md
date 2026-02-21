# Konzept: Floating AI Assistant für LaTeX Collab

## Übersicht

Ein elegantes, draggables und minimierbares Chat-Fenster, das über dem LaTeX-Dokument schwebt und **kontextbewusst** mit dem Dokument interagieren kann. Anders als die bisherige AISidebar soll dieses Fenster:

1. **Minimierbar** in eine kleine Icon-Leiste (kein hässlicher Floating Button)
2. **Dokument-aware**: Kennt automatisch Titel, Sections, aktuelle Selektion
3. **Agent-fähig**: Kann selbstständig Änderungen im Dokument vornehmen
4. **Integriert**: Bestehende Shortcuts (@rewrite, @expand, etc.) über Chat nutzbar

---

## Zielzustand

### Minimierter Zustand
```
┌──────────────────────────────────────────────────────────────────┐
│  [Editor Toolbar]                         [🤖 AI] [📝] [⚙️]     │
└──────────────────────────────────────────────────────────────────┘
                                              ↑
                                        Minimierte Icons
                                        Klick öffnet Panel
```

### Expandierter Zustand
```
┌──────────────────────────────────┐
│ 🤖 AI Assistant          ─  □  × │  ← Draggable Header
├──────────────────────────────────┤
│ 📄 main.tex | Section 2.1        │  ← Kontext-Anzeige
├──────────────────────────────────┤
│                                  │
│  [Chat History]                  │
│                                  │
│  User: Schreibe mir einen        │
│        besseren Titel            │
│                                  │
│  AI: Hier sind 3 Vorschläge:     │
│      1. "Machine Learning..."    │  ← Mit "Einsetzen" Button
│      [Einsetzen] [Kopieren]      │
│                                  │
├──────────────────────────────────┤
│ 💬 Message eingeben...     [↑]   │  ← Input
├──────────────────────────────────┤
│ [Titel] [Abstract] [Fix] [mehr▾] │  ← Quick Actions
└──────────────────────────────────┘
```

---

## Architektur

### Komponenten-Struktur

```
llars-frontend/src/components/LatexCollabAI/
├── FloatingAIAssistant/
│   ├── FloatingAIAssistant.vue        # Hauptkomponente (draggable Panel)
│   ├── AIAssistantHeader.vue          # Header mit Kontext + Controls
│   ├── AIAssistantChat.vue            # Chat-Verlauf mit Actions
│   ├── AIAssistantInput.vue           # Input + Quick Actions
│   ├── AIAssistantMinimized.vue       # Minimierte Toolbar-Icons
│   └── composables/
│       ├── useDocumentContext.js      # Dokument-Kontext extrahieren
│       ├── useAIAgentActions.js       # Agent-Aktionen (Replace, Insert)
│       └── useAssistantState.js       # Panel-State (position, minimized)
```

### Datenfluss

```
┌─────────────────────────────────────────────────────────────────┐
│                    LatexCollabWorkspace                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  LatexEditorPane                                          │  │
│  │  - getCurrentContent()                                    │  │
│  │  - getSelectionText()                                     │  │
│  │  - replaceRange(from, to, text)  ← AI Agent nutzt das    │  │
│  │  - highlightRange(from, to)                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                           ↑↓                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FloatingAIAssistant                                      │  │
│  │  - Erhält ref zu Editor                                   │  │
│  │  - Liest Kontext (Titel, Section, Selection)              │  │
│  │  - Führt Agent-Actions aus (Replace, Insert)              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features im Detail

### 1. Dokument-Kontext (useDocumentContext.js)

Der Assistent weiß automatisch über das Dokument Bescheid:

```javascript
const documentContext = computed(() => ({
  // Aus Dokument extrahiert via Regex
  title: extractTitle(content),           // \title{...}
  author: extractAuthor(content),         // \author{...}
  abstract: extractAbstract(content),     // \begin{abstract}...\end{abstract}
  sections: extractSections(content),     // Array von {level, title, line}

  // Aktuelle Position
  currentSection: getCurrentSection(cursorLine, sections),

  // Selektion
  selection: {
    text: selectedText,
    from: selectionStart,
    to: selectionEnd
  },

  // Metadaten
  documentClass: extractDocumentClass(content),  // article, report, etc.
  packages: extractPackages(content),            // \usepackage{...}
  wordCount: countWords(content),
  fileName: currentFileName
}))
```

**Regex-Patterns für LaTeX:**
```javascript
const PATTERNS = {
  title: /\\title\s*\{([^}]*)\}/,
  author: /\\author\s*\{([^}]*)\}/,
  abstract: /\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}/,
  section: /\\(section|subsection|subsubsection)\*?\s*\{([^}]*)\}/g,
  documentClass: /\\documentclass(?:\[.*?\])?\{([^}]*)\}/,
  usePackage: /\\usepackage(?:\[.*?\])?\{([^}]*)\}/g
}
```

### 2. Agent-Aktionen (useAIAgentActions.js)

Die KI kann **selbstständig Änderungen** im Dokument vornehmen:

```javascript
const agentActions = {
  // Titel ersetzen
  replaceTitle: async (newTitle) => {
    const match = content.match(/\\title\s*\{[^}]*\}/)
    if (match) {
      const from = match.index
      const to = from + match[0].length
      editor.replaceRange(from, to, `\\title{${newTitle}}`, {
        collabUser: 'LLARS KI',
        collabColor: '#9B59B6'
      })
      return { success: true, message: `Titel geändert zu "${newTitle}"` }
    }
    return { success: false, message: 'Kein \\title{} gefunden' }
  },

  // Abstract ersetzen
  replaceAbstract: async (newAbstract) => { ... },

  // Section einfügen
  insertSection: async (title, content, afterSection) => { ... },

  // Text an Position ersetzen
  replaceAtRange: async (from, to, newText) => {
    editor.replaceRange(from, to, newText, {
      collabUser: 'LLARS KI',
      collabColor: '#9B59B6'
    })
    editor.highlightRange(from, from + newText.length)
  },

  // Selektion ersetzen (für rewrite, expand, etc.)
  replaceSelection: async (newText) => {
    const { from, to } = editor.getSelectionRange()
    return agentActions.replaceAtRange(from, to, newText)
  }
}
```

### 3. Chat mit Agent-Befehlen

Die KI versteht **natürlichsprachliche Befehle** und führt passende Aktionen aus:

```
User: "Schreibe mir einen besseren Titel"

AI Response:
{
  "message": "Basierend auf deinem Dokument über Machine Learning schlage ich vor:",
  "suggestions": [
    "Deep Learning Approaches for Natural Language Processing",
    "A Comprehensive Study of Neural Network Architectures",
    "Modern Machine Learning: Methods and Applications"
  ],
  "actions": [
    { "type": "replace_title", "value": "...", "label": "Einsetzen" }
  ]
}
```

**UI zeigt:**
```
┌────────────────────────────────────┐
│ AI: Basierend auf deinem Dokument  │
│     schlage ich vor:               │
│                                    │
│ 1. "Deep Learning Approaches..."   │
│    [Einsetzen] [Kopieren]          │
│                                    │
│ 2. "A Comprehensive Study..."      │
│    [Einsetzen] [Kopieren]          │
│                                    │
│ 3. "Modern Machine Learning..."    │
│    [Einsetzen] [Kopieren]          │
└────────────────────────────────────┘
```

Klick auf **[Einsetzen]** → `agentActions.replaceTitle("Deep Learning...")` wird ausgeführt.

### 4. Quick Actions (erweitert)

Vordefinierte Aktionen mit **automatischer Anwendung**:

| Action | Kontext | Ergebnis |
|--------|---------|----------|
| **Titel** | Liest aktuellen Titel | Schlägt 3 Alternativen vor mit [Einsetzen] |
| **Abstract** | Liest gesamtes Dokument | Generiert Abstract mit [Einsetzen] |
| **Fix LaTeX** | Gesamtes Dokument oder Selektion | Zeigt Fixes mit [Alle anwenden] |
| **Rewrite** | Aktuelle Selektion | Ersetzt automatisch oder zeigt Optionen |
| **Expand** | Aktuelle Selektion | Ersetzt mit expandiertem Text |
| **Summarize** | Aktuelle Selektion | Ersetzt mit Zusammenfassung |
| **Translate** | Aktuelle Selektion | Übersetzt und ersetzt |

### 5. Kontext-Anzeige im Header

Zeigt immer den aktuellen Kontext:

```
┌──────────────────────────────────┐
│ 📄 main.tex                      │  ← Dateiname
│ 📍 Section 2.1: Methods          │  ← Aktuelle Position
│ ✂️ "...selected text..." (42w)   │  ← Wenn selektiert
└──────────────────────────────────┘
```

---

## Backend-Erweiterungen

### Neuer Endpoint: `/api/ai-writing/agent-action`

```python
@ai_writing_bp.route('/agent-action', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='ai_writing')
def execute_agent_action():
    """
    Führt Agent-Aktionen basierend auf natürlichsprachlichen Befehlen aus.
    """
    data = request.get_json()
    user_message = data.get('message')
    document_context = data.get('context', {})

    # Context enthält:
    # - title, author, abstract
    # - current_section
    # - selection (text, from, to)
    # - full_content (optional, für komplexe Anfragen)

    response = ai_agent_service.process_request(
        message=user_message,
        context=document_context
    )

    return jsonify({
        'success': True,
        'message': response.message,
        'suggestions': response.suggestions,
        'actions': response.actions  # [{type, value, label, range}]
    })
```

### AI Agent Service

```python
class AIAgentService:
    """
    Verarbeitet natürlichsprachliche Befehle und generiert
    strukturierte Aktionen für das Frontend.
    """

    INTENT_PATTERNS = {
        'title': r'(titel|title|überschrift)',
        'abstract': r'(abstract|zusammenfassung)',
        'rewrite': r'(umschreiben|rewrite|formulier)',
        'expand': r'(erweitern|expand|ausführ)',
        'fix': r'(fix|korrigier|fehler)',
    }

    def process_request(self, message: str, context: dict) -> AgentResponse:
        intent = self._detect_intent(message)

        if intent == 'title':
            return self._handle_title_request(message, context)
        elif intent == 'abstract':
            return self._handle_abstract_request(message, context)
        # ... etc.
        else:
            return self._handle_general_chat(message, context)

    def _handle_title_request(self, message, context):
        current_title = context.get('title', '')
        document_summary = self._summarize_document(context.get('full_content', ''))

        titles = self.llm.generate_titles(document_summary, current_title)

        return AgentResponse(
            message=f"Basierend auf deinem Dokument hier 3 Titel-Vorschläge:",
            suggestions=titles,
            actions=[
                {'type': 'replace_title', 'value': t, 'label': 'Einsetzen'}
                for t in titles
            ]
        )
```

---

## UI/UX Design

### States

1. **Minimiert**: Kleine Icons in der oberen rechten Ecke
   ```
   [🤖] [📝 2] [⚙️]
         ↑ Badge zeigt ungelesene Messages
   ```

2. **Normal**: Draggables Panel (Standard-Größe: 400x500px)

3. **Erweitert**: Größeres Panel für komplexe Interaktionen

### Animationen

- **Öffnen**: Scale + Fade In (200ms)
- **Schließen**: Scale Down zu Icon-Position (200ms)
- **Drag**: Smooth mit Snap-to-Edges

### LLARS Design System

```css
/* Asymmetrischer Border-Radius */
border-radius: 16px 4px 16px 4px;

/* Gradient Header */
background: linear-gradient(135deg, #b0ca97 0%, #88c4c8 100%);

/* AI Message Highlight */
.ai-action-button {
  background: rgba(155, 89, 182, 0.15);  /* LLARS KI Purple */
  border: 1px solid rgba(155, 89, 182, 0.3);
}
```

---

## Implementierungsplan

### Phase 1: Basis-Panel (Geschätzt: ~400 LOC)
- [ ] `FloatingAIAssistant.vue` - Draggables, minimierbares Panel
- [ ] `AIAssistantMinimized.vue` - Minimierte Icon-Leiste
- [ ] `useAssistantState.js` - Position, Size, Minimized State (localStorage)

### Phase 2: Dokument-Kontext (~200 LOC)
- [ ] `useDocumentContext.js` - Regex-Extraktion von Titel, Sections, etc.
- [ ] Kontext-Anzeige im Header
- [ ] Automatische Aktualisierung bei Cursor-Bewegung

### Phase 3: Chat-Integration (~300 LOC)
- [ ] `AIAssistantChat.vue` - Chat-Verlauf mit strukturierten Responses
- [ ] `AIAssistantInput.vue` - Input mit Quick Actions
- [ ] Integration mit bestehendem `useAIChat.js`

### Phase 4: Agent-Aktionen (~350 LOC)
- [ ] `useAIAgentActions.js` - Replace/Insert Funktionen
- [ ] Backend: `/api/ai-writing/agent-action` Endpoint
- [ ] Backend: `AIAgentService` für Intent-Detection
- [ ] UI: Action-Buttons in Chat-Messages ([Einsetzen], [Kopieren])

### Phase 5: Integration & Polish (~150 LOC)
- [ ] Integration in `LatexCollabWorkspace.vue`
- [ ] Keyboard Shortcuts (Cmd+J öffnet Panel)
- [ ] i18n (de.json, en.json)
- [ ] Animation & Transitions

---

## Vergleich: Alt vs. Neu

| Feature | AISidebar (Alt) | FloatingAIAssistant (Neu) |
|---------|-----------------|---------------------------|
| Position | Fixiert rechts | Frei draggable |
| Minimieren | Floating Button | Elegante Icon-Leiste |
| Dokument-Kontext | Manuell senden | Automatisch erkannt |
| Titel ändern | Copy & Paste | [Einsetzen] Button |
| Agent-Aktionen | Keine | Replace, Insert, etc. |
| Quick Tools | In Sidebar | Im Panel integriert |

---

## Offene Fragen / Entscheidungen

1. **Koexistenz**: Soll AISidebar komplett ersetzt oder parallel existieren?
   - **Empfehlung**: Parallel, User kann wählen (Setting)

2. **Kontext-Tiefe**: Wie viel Dokument-Inhalt an AI senden?
   - **Empfehlung**: Nur relevante Sections + Selektion (Token-Limit beachten)

3. **Undo für Agent-Aktionen**: Wie wird Undo gehandhabt?
   - **Empfehlung**: Yjs-History nutzt automatisch, zusätzlich Chat-History zeigt was geändert wurde

4. **Multi-File Support**: Soll Agent auch andere Dateien im Workspace bearbeiten können?
   - **Empfehlung**: Phase 2, erstmal nur aktuelle Datei

---

## Zusammenfassung

Das Floating AI Assistant Panel bietet:

✅ **Elegantes UI** - Draggable, minimierbar, LLARS Design
✅ **Dokument-Aware** - Automatische Erkennung von Titel, Sections, etc.
✅ **Agent-Fähig** - Selbstständige Änderungen im Dokument
✅ **Integriert** - Bestehende AI-Features (rewrite, expand, etc.) nutzbar
✅ **User-Friendly** - [Einsetzen] Buttons statt Copy & Paste

**Geschätzter Gesamtumfang**: ~1400 LOC (Frontend + Backend)
