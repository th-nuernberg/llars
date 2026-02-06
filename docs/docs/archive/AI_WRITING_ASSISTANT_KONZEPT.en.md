# AI Writing Assistant for LaTeX/Markdown Collab Editor

**Version:** 1.0
**Created:** December 29, 2025
**Status:** Concept phase
**Goal:** Integration of a context‑aware AI assistant for scientific writing

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Feature Specifications](#3-feature-specifications)
4. [Technical Implementation](#4-technical-implementation)
5. [UI/UX Design](#5-uiux-design)
6. [Data Model & API](#6-data-model--api)
7. [Permissions & Security](#7-permissions--security)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Testing & QA](#9-testing--qa)
10. [References & Inspirations](#10-references--inspirations)

---

## 1. Executive Summary

### 1.1 Project Goal

Integrate an AI assistant into the existing Markdown Collab editor to help researchers write papers, dissertations, and other academic texts.

### 1.2 Core Features

| Feature | Description | Priority |
|---------|-------------|-----------|
| Ghost Text Completion | Inline suggestions like GitHub Copilot | High |
| @ Commands | Quick commands in the editor (@cite, @rewrite, etc.) | High |
| AI Sidebar | Chat + quick tools panel | Medium |
| RAG Citation Finder | Literature search in the user’s collections | High |
| Citation Reviewer | Automatic check for missing citations | Medium |
| Selection Context Menu | Floating menu on text selection | Medium |

### 1.3 Inspiration Sources

- [Overleaf AI Assist](https://www.digital-science.com/blog/2025/06/digital-science-launches-new-cutting-edge-ai-writing-tools-for-20-million-overleaf-users/)
- [GitHub Copilot](https://code.visualstudio.com/docs/copilot/ai-powered-suggestions)
- [Cursor Editor](https://cursor.com/)
- [Elicit Research Assistant](https://elicit.com/)

---

## 2. Architecture Overview

### 2.1 System Architecture

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

### 2.2 Component Overview

#### Frontend Components
- [ ] `AISidebar.vue` - Main component for the AI panel
- [ ] `AIChat.vue` - Chat interface
- [ ] `AIQuickTools.vue` - Quick access buttons
- [ ] `AISelectionMenu.vue` - Floating menu on text selection
- [ ] `CitationFinder.vue` - RAG‑based literature search
- [ ] `CitationWarning.vue` - Inline warning for missing citations
- [ ] `RewritePreview.vue` - Preview for rephrasing

#### Frontend Composables
- [ ] `useAICompletion.js` - Ghost text logic
- [ ] `useAICommands.js` - @ command handler
- [ ] `useAIChat.js` - Chat state management
- [ ] `useAICitations.js` - Citation service integration
- [ ] `useAISelection.js` - Selection menu logic

#### Backend Services
- [ ] `completion_service.py` - Text completion
- [ ] `rewrite_service.py` - Text rewriting
- [ ] `citation_service.py` - RAG citation search
- [ ] `chat_service.py` - Conversational AI
- [ ] `review_service.py` - Citation review

---

## 3. Feature Specifications

### 3.1 Ghost Text Completion

#### Description
Inline text suggestions that appear as ghost text (gray/transparent) at the cursor. Inspired by GitHub Copilot.

#### Behavior
```
User types: "Die Ergebnisse zeigen, dass"
Ghost Text: ░░ die Intervention eine signifikante Reduktion (p<0.05) bewirkte.

Keyboard shortcuts:
- [Tab]     → accept suggestion
- [Esc]     → reject suggestion
- [Alt+]]   → next suggestion
- [Alt+[]   → previous suggestion
- [Ctrl+Space] → request manually
```

#### Trigger Conditions
- [ ] After 500ms pause at end of sentence (`. `, `? `, `! `)
- [ ] After LaTeX patterns (`\begin{`, `\cite{`, `\ref{`)
- [ ] After Markdown patterns (`## `, `- `, `1. `)
- [ ] Manual trigger via keyboard shortcut
- [ ] Configurable delay (user setting)

#### Technical Requirements
- [ ] CodeMirror 6 extension for ghost text widget
- [ ] Debouncing (500ms default, configurable)
- [ ] Caching of suggestions
- [ ] Cancel on new input
- [ ] Max 100 tokens per completion
- [ ] Temperature: 0.3 (low for consistency)

#### Acceptance Criteria
- [ ] Ghost text appears after configured delay
- [ ] Tab accepts and inserts text
- [ ] Esc discards suggestion
- [ ] No interference with normal input
- [ ] Performance: <500ms response time (after debounce)

---

### 3.2 @ Commands (Inline Commands)

#### Description
Quick commands triggered by typing `@` in the editor.

#### Available Commands

| Command | Description | Parameters |
|---------|-------------|-----------|
| `@ai <prompt>` | Free AI prompt | Free text |
| `@rewrite` | Rephrase more academically | - |
| `@expand` | Expand/enrich text | - |
| `@summarize` | Summarize text | - |
| `@cite` | Suggest citations (RAG) | Optional: search term |
| `@fix` | Fix LaTeX/grammar errors | - |
| `@translate <lang>` | Translate | Target language (de, en, fr, es) |
| `@abstract` | Generate abstract | - |
| `@title` | Suggest title | - |
| `@outline` | Create outline | - |

#### Behavior
```
User types: @
Autocomplete appears:
┌─────────────────────────────────────────────┐
│ @ai        💬 Free AI prompt                │
│ @rewrite   ✏️  Rephrase academically        │
│ @cite      📚 Suggest citations (RAG)       │
│ @expand    📝 Expand text                   │
│ ...                                         │
└─────────────────────────────────────────────┘
```

#### Technical Requirements
- [ ] CodeMirror autocomplete extension
- [ ] Command parser for parameter extraction
- [ ] Context awareness (selection or cursor position)
- [ ] Inline result or dialog depending on command
- [ ] Undo support for all changes

#### Acceptance Criteria
- [ ] @ triggers autocomplete menu
- [ ] Commands filter as you type
- [ ] Enter executes the command
- [ ] Esc cancels
- [ ] Results are inserted correctly

---
### 3.3 AI Sidebar

#### Description
Collapsible panel on the right with chat interface and quick tools.

#### Structure
```
┌──────────────────────────────────────┐
│  🤖 AI Assistant            [−] [×]  │
├──────────────────────────────────────┤
│                                      │
│  ┌────────────────────────────────┐  │
│  │ QUICK TOOLS                    │  │
│  ├────────────────────────────────┤  │
│  │ [📝 Generate abstract       ]  │  │
│  │ [🏷️  Suggest title         ]  │  │
│  │ [✅ Check citations         ]  │  │
│  │ [🔧 Fix LaTeX errors        ]  │  │
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
│ │ Enter message...             │    │
│ └──────────────────────────────┘    │
└──────────────────────────────────────┘
```

#### States
- [ ] Collapsed (icon bar only, 48px wide)
- [ ] Expanded (full width, 320px default)
- [ ] Resizable (min 280px, max 500px)

#### Quick Tools
- [ ] Generate abstract
- [ ] Suggest title
- [ ] Check all citations
- [ ] Fix LaTeX errors
- [ ] Summarize document
- [ ] Suggest outline

#### Chat Features
- [ ] Conversation history (per document)
- [ ] Document context is automatically included
- [ ] Artifacts (insertable code blocks)
- [ ] Markdown rendering in responses
- [ ] Copy‑to‑clipboard for responses
- [ ] "Insert into editor" button

#### Technical Requirements
- [ ] LocalStorage for sidebar state
- [ ] Session storage for chat history
- [ ] Streaming response support
- [ ] Max 4000 tokens document context
- [ ] Keyboard shortcut: Ctrl+Shift+A

#### Acceptance Criteria
- [ ] Sidebar can be collapsed/expanded
- [ ] State persists across sessions
- [ ] Chat works with document context
- [ ] Quick tools run actions
- [ ] Results can be inserted

---

### 3.4 RAG Citation Finder

#### Description
Literature search across the user’s RAG collections with relevance ranking.

#### Workflow
1. User selects a claim or uses @cite
2. Dialog opens with search field
3. RAG searches selected collections
4. LLM ranks results by relevance
5. User inserts citations (BibTeX or inline)

#### UI
```
┌─────────────────────────────────────────────────────────────────────────┐
│     📚 Find citations                                           [×]     │
├─────────────────────────────────────────────────────────────────────────┤
│  Selected text:                                                       │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ "Digital transformation poses fundamental challenges to           │  │
│  │  organizations"                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Collections: [✓] Digitalization  [✓] Management  [ ] Statistics        │
│                                                                         │
│  📊 Sources found (5)                                                   │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 📄 Brynjolfsson & McAfee (2014)                      Relevance: 96%│  │
│  │    "The Second Machine Age"                                       │  │
│  │    └─ "...digital technologies are transforming..."               │  │
│  │    [📋 BibTeX] [✏️ Insert] [👁 Details]                             │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                                        [Cancel]  [Insert selected]       │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Integration with Existing RAG
- [ ] Use `get_best_embedding_for_collection()`
- [ ] Semantic search via ChromaDB
- [ ] Metadata extraction (author, year, title)
- [ ] BibTeX generation from metadata

#### Technical Requirements
- [ ] Multi‑collection search
- [ ] Relevance scoring via LLM
- [ ] BibTeX export
- [ ] APA/MLA/Chicago formatting
- [ ] Result caching

#### Acceptance Criteria
- [ ] Search across multiple collections
- [ ] Results sorted by relevance
- [ ] BibTeX can be copied
- [ ] Inline citation can be inserted
- [ ] Performance: <3s per search

---

### 3.5 Citation Reviewer

#### Description
Automatic analysis of the document for statements that require citations.

#### Detection Criteria
- Quantitative statements ("40% of...", "N=120")
- Claims ("Studies show...", "It is proven...")
- External definitions
- Historical facts

#### UI in Editor
```
│  6  │ Artificial intelligence will affect 40% of all jobs.
│     │                                                              [⚠️]
│     │                          ┌────────────────────────────────────┐
│     │                          │ ⚠️ Citation recommended            │
│     │                          │                                    │
│     │                          │ Suggestions:                       │
│     │                          │ 📚 McKinsey (2017) - 94%            │
│     │                          │ 📚 Frey & Osborne (2017) - 89%      │
│     │                          │                                    │
│     │                          │ [Insert] [Ignore] [All]             │
│     │                          └────────────────────────────────────┘
```

#### Status Bar
```
┌────────────────────────────────────────────────────────────────────────┐
│  🔍 Citation check: 2 warnings │ 5 correctly cited │ [Check all]       │
└────────────────────────────────────────────────────────────────────────┘
```

#### Technical Requirements
- [ ] LLM‑based claim extraction
- [ ] Regex for obvious patterns (numbers, "study shows")
- [ ] CodeMirror decorations for warnings
- [ ] Gutter markers for overview
- [ ] Batch processing for "Check all"

#### Acceptance Criteria
- [ ] Uncited statements are marked
- [ ] Warnings are non‑intrusive
- [ ] Quick actions are available
- [ ] Batch mode works

---

### 3.6 Selection Context Menu

#### Description
Floating menu on text selection with quick AI actions.

#### UI
```
┌─────────────────────────────────────────┐
│  AI Actions                             │
├─────────────────────────────────────────┤
│  ✏️  Rewrite                             │
│  📝  Expand                              │
│  📚  Suggest citations                   │
│  🌍  Translate                           │
│  ✅  Check claim                          │
└─────────────────────────────────────────┘
```

#### Trigger
- [ ] Text selection in editor
- [ ] Right‑click on selection
- [ ] Keyboard shortcut (Ctrl+Shift+M)

#### Actions
- [ ] Rewrite selection
- [ ] Expand selection
- [ ] Summarize selection
- [ ] Translate selection
- [ ] Suggest citations
- [ ] Check for missing citations

#### Technical Requirements
- [ ] Context menu component
- [ ] Positioning relative to selection
- [ ] Hide when clicking outside
- [ ] Keyboard navigation
- [ ] Works in LaTeX + Markdown mode

#### Acceptance Criteria
- [ ] Menu appears on selection
- [ ] Actions run on selected text
- [ ] Results are insertable
- [ ] Menu closes properly

---
## 4. Technical Implementation

### 4.1 Backend API Endpoints

#### Completion API
```python
POST /api/ai-writing/complete
{
    "context": "Text before and after cursor (max 1000 tokens)",
    "cursor_position": 500,
    "document_type": "latex|markdown",
    "max_tokens": 100,
    "temperature": 0.3
}

Response:
{
    "completion": "suggested text",
    "confidence": 0.85,
    "alternatives": ["Alternative 1", "Alternative 2"]
}
```

#### Rewrite API
```python
POST /api/ai-writing/rewrite
{
    "text": "Original text",
    "style": "academic|concise|expanded|simplified",
    "context": "Surrounding text for context",
    "preserve_meaning": true
}

Response:
{
    "result": "Rewritten text",
    "changes": [
        {"type": "replaced", "original": "...", "new": "..."}
    ]
}
```

#### Citation API
```python
POST /api/ai-writing/find-citations
{
    "claim": "Statement to support",
    "context": "Surrounding text",
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
            "collection_name": "Digitalization"
        }
    ]
}
```

#### Chat API
```python
POST /api/ai-writing/chat
{
    "message": "User message",
    "document_content": "Current document content (max 4000 tokens)",
    "history": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "stream": true
}

Response (Stream):
data: {"delta": "Part", "done": false}
data: {"delta": " of ", "done": false}
data: {"delta": "answer", "done": true, "artifacts": [...]}
```

#### Review API
```python
POST /api/ai-writing/review-citations
{
    "content": "Full document content"
}

Response:
{
    "warnings": [
        {
            "position": {"line": 10, "from": 0, "to": 65},
            "text": "40% of all jobs...",
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
- [ ] `app/routes/ai_writing/__init__.py` - Blueprint setup
- [ ] `app/routes/ai_writing/routes.py` - API endpoints
- [ ] `app/routes/ai_writing/schemas.py` - Request/response schemas

#### Services
- [ ] `app/services/ai_writing/__init__.py` - Service exports
- [ ] `app/services/ai_writing/completion_service.py`
- [ ] `app/services/ai_writing/rewrite_service.py`
- [ ] `app/services/ai_writing/citation_service.py`
- [ ] `app/services/ai_writing/chat_service.py`
- [ ] `app/services/ai_writing/review_service.py`
- [ ] `app/services/ai_writing/prompts.py` - System prompts

#### Integration
- [ ] LiteLLM proxy integration
- [ ] RAG service integration
- [ ] Rate limiting
- [ ] Usage tracking (analytics)

### 4.3 Frontend Implementation Checklist

#### Services
- [ ] `llars-frontend/src/services/aiWritingService.js` - API client

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
- [ ] Ghost text widget extension
- [ ] @ commands autocomplete extension
- [ ] Citation warning decoration extension
- [ ] Selection menu extension

---

## 5. UI/UX Design

### 5.1 Design System Integration

#### Colors (LLARS Pastel Theme)
```css
--ai-primary: #88c4c8;        /* Soft Teal - AI Accent */
--ai-ghost-text: rgba(var(--v-theme-on-surface), 0.4);
--ai-warning: #e8c87a;        /* Soft Gold - Citation Warning */
--ai-success: #98d4bb;        /* Soft Mint - Cited */
```

#### Component Styling
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
| Breakpoint | Behavior |
|------------|----------|
| Desktop (>1200px) | Sidebar + editor side by side |
| Tablet (768-1200px) | Sidebar as overlay |
| Mobile (<768px) | Sidebar as bottom sheet |

#### Mobile Adjustments
- [ ] Bottom sheet instead of sidebar
- [ ] Simplified selection menu (icons only)
- [ ] Ghost text disabled (performance)
- [ ] Touch‑optimized buttons

### 5.3 Accessibility

- [ ] ARIA labels for all interactive elements
- [ ] Full keyboard navigation
- [ ] Screen reader support for ghost text
- [ ] High contrast mode support
- [ ] Focus management for dialogs

### 5.4 Animations

```css
/* Sidebar toggle */
.ai-sidebar {
  transition: width 0.2s ease;
}

/* Ghost text appearance */
.ai-ghost-text {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 0.4; }
}

/* Selection menu */
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

## 6. Data Model & API

### 6.1 New Database Tables

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

- [ ] Create migration script
- [ ] Optimize indexes
- [ ] Validate foreign keys
- [ ] Rollback script

---

## 7. Permissions & Security

### 7.1 New Permissions

```python
# app/db/seeders/permissions.py

AI_WRITING_PERMISSIONS = [
    # Base permission
    ('feature:markdown_collab:ai', 'Use AI writing assistance'),

    # Feature-specific permissions
    ('feature:markdown_collab:ai:completion', 'Use AI text completion'),
    ('feature:markdown_collab:ai:rewrite', 'Use AI text rewriting'),
    ('feature:markdown_collab:ai:citations', 'Use AI citation suggestions'),
    ('feature:markdown_collab:ai:chat', 'Use AI chat assistant'),
    ('feature:markdown_collab:ai:review', 'Use AI citation review'),

    # Admin permissions
    ('admin:ai_writing:view_usage', 'View AI usage statistics'),
    ('admin:ai_writing:manage_limits', 'Manage AI usage limits'),
]
```

### 7.2 Role Mapping

| Role | completion | rewrite | citations | chat | review |
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

### 7.4 Security Measures

- [ ] Input sanitization for all prompts
- [ ] Output filtering (no sensitive data)
- [ ] Prompt‑injection prevention
- [ ] Per‑user rate limiting
- [ ] Token budget per user/day
- [ ] Audit logging for AI usage

---
## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

#### Backend Setup
- [ ] Create blueprint and route structure
- [ ] LLM service integration (LiteLLM)
- [ ] Define base prompts
- [ ] Unit tests for services

#### Frontend Setup
- [ ] Create AI service
- [ ] Add base composables
- [ ] AI sidebar component (without features)

### Phase 2: Core Features (Week 3-4)

#### Ghost Text Completion
- [ ] Develop CodeMirror extension
- [ ] Implement backend endpoint
- [ ] Debouncing & caching
- [ ] Keyboard shortcuts

#### @ Commands
- [ ] Autocomplete extension
- [ ] Command parser
- [ ] Backend endpoints for each command
- [ ] Inline result display

### Phase 3: AI Sidebar (Week 5-6)

#### Chat Interface
- [ ] Chat UI component
- [ ] Streaming response handler
- [ ] Chat history persistence
- [ ] Artifacts system

#### Quick Tools
- [ ] Tool buttons UI
- [ ] Backend integration
- [ ] Result dialogs

### Phase 4: Citation Intelligence (Week 7-8)

#### RAG Integration
- [ ] Citation service with RAG
- [ ] BibTeX generator
- [ ] Citation finder dialog

#### Citation Review
- [ ] Claim extraction
- [ ] Warning decorations
- [ ] Review status bar

### Phase 5: Polish & Testing (Week 9-10)

#### UX Improvements
- [ ] Selection context menu
- [ ] Keyboard shortcuts help
- [ ] Loading states
- [ ] Error handling

#### Testing & QA
- [ ] E2E tests
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] User acceptance testing

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

- [ ] Completion flow (frontend → backend → LLM → frontend)
- [ ] Chat session flow
- [ ] Citation search flow (incl. RAG)
- [ ] Rate limiting behavior

### 9.3 E2E Tests

- [ ] Ghost text appears and can be accepted
- [ ] @ commands work end‑to‑end
- [ ] Chat conversation completes
- [ ] Citation finder finds and inserts
- [ ] Citation review marks and can be ignored

### 9.4 Performance Tests

- [ ] Completion latency < 500ms (p95)
- [ ] Chat response start < 1s (p95)
- [ ] Citation search < 3s (p95)
- [ ] Memory footprint < 50MB additional

### 9.5 Accessibility Tests

- [ ] Keyboard‑only navigation
- [ ] Screen reader compatibility
- [ ] Color contrast (WCAG AA)
- [ ] Focus management

---

## 10. References & Inspirations

### 10.1 Products & Tools

| Tool | Feature | Inspiration for |
|------|---------|-----------------|
| [Overleaf AI Assist](https://www.digital-science.com/blog/2025/06/digital-science-launches-new-cutting-edge-ai-writing-tools-for-20-million-overleaf-users/) | TeXGPT, Language Feedback | LaTeX‑specific help |
| [GitHub Copilot](https://code.visualstudio.com/docs/copilot/ai-powered-suggestions) | Ghost Text, NES | Inline completion UX |
| [Cursor](https://cursor.com/) | AI‑first editor | Context‑aware chat |
| [Elicit](https://elicit.com/) | Research assistant | Citation finding |
| [Semantic Scholar](https://www.semanticscholar.org/) | TLDR summaries | Paper summarization |
| [Writefull](https://www.writefull.com/writefull-for-overleaf) | Language feedback | Academic writing style |

### 10.2 UX Pattern Resources

- [Shape of AI](https://www.shapeof.ai) - AI UX patterns
- [AI UI Patterns](https://www.patterns.dev/react/ai-ui-patterns/) - React AI patterns
- [Smashing Magazine - AI Interfaces](https://www.smashingmagazine.com/2025/07/design-patterns-ai-interfaces/)

### 10.3 Technical Documentation

- [CodeMirror 6 Documentation](https://codemirror.net/docs/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

---

## Changelog

| Version | Date | Changes |
|---------|-------|---------|
| 1.0 | 2025-12-29 | Initial concept |

---

## Appendix

### A. System Prompts

#### Completion System Prompt
```
You are a scientific writing assistant. Complete the following text in an academic, precise way.
- Keep the style of the existing text
- Use technical terms correctly
- Write concisely and clearly
- Max length: 1-2 sentences
```

#### Rewrite System Prompt
```
You are an editor for scientific texts. Rewrite the following text:
- Use academic language
- Remove colloquial expressions
- Improve sentence structure
- Preserve the original meaning
```

#### Citation Review System Prompt
```
Analyze the following text and identify statements that require citations:
- Statistical claims (numbers, percentages)
- Factual statements ("studies show...")
- Definitions and technical terms
- Historical facts

For each statement return:
- Position in text
- Type of statement
- Urgency (high/medium/low)
```

### B. Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| `Tab` | Accept ghost text |
| `Esc` | Reject ghost text |
| `Alt+]` | Next suggestion |
| `Alt+[` | Previous suggestion |
| `Ctrl+Space` | Request completion manually |
| `Ctrl+Shift+A` | Toggle AI sidebar |
| `Ctrl+Shift+R` | Rewrite selection |
| `Ctrl+Shift+C` | Find citation for selection |
| `Ctrl+Shift+E` | Expand selection |
| `Ctrl+Shift+K` | Shorten selection |
| `Ctrl+Shift+?` | Focus chat |

### C. Error Codes

| Code | Description | User Message |
|------|--------------|--------------|
| `AI_001` | Rate limit reached | "Too many requests. Please wait a moment." |
| `AI_002` | Token budget exhausted | "Daily AI limit reached." |
| `AI_003` | LLM unavailable | "AI service is currently unavailable." |
| `AI_004` | Invalid input | "Input could not be processed." |
| `AI_005` | Timeout | "Request took too long." |
