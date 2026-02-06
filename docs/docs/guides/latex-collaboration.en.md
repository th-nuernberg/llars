# LaTeX Collaboration

**Version:** 1.0 | **Date:** January 2026

LaTeX Collaboration is a real-time collaboration tool for scientific documents. Multiple users can work on LaTeX projects simultaneously, comment, version, and compile PDFs.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LaTeX Collaboration                                              [⚙️]     │
├──────────────────┬──────────────────────────────────────────────────────────┤
│  File Tree        │  Editor                                     PDF Viewer  │
│  ─────────────   │  ───────────────────────────────────────    ─────────── │
│                  │                                                         │
│  📁 Project      │  \documentclass{article}                    ┌─────────┐ │
│  ├── 📄 main.tex │  \begin{document}                           │         │ │
│  ├── 📄 intro.tex│  \section{Introduction}                     │  PDF    │ │
│  ├── 📁 chapters │  Lorem ipsum dolor sit amet...              │         │ │
│  │   └── 📄 ch1  │                      ┌─────────────┐        │         │ │
│  └── 📁 images   │                      │ Comment     │        │         │ │
│                  │                      │ "Fix typo"  │        │         │ │
│  ─────────────   │                      │ [🤖 AI Fix] │        └─────────┘ │
│  Git Panel       │                      └─────────────┘                    │
│  +12 / -3        │                                                         │
│  [Commit]        │                                                         │
└──────────────────┴──────────────────────────────────────────────────────────┘
```

---

## Quick Start

!!! tip "Get to a document in 4 steps"
    1. **Create workspace** → enter name, choose template
    2. **Add documents** → create files and folders
    3. **Edit** → write LaTeX, add comments
    4. **Compile** → generate and download PDF

---

## Workspace

### Create a New Workspace

1. Open **LaTeX Collab** in the navigation
2. Click **New Workspace**
3. Enter a name (e.g. "IJCAI Paper 2026")
4. Choose a template (article, report, etc.)

### Workspace Settings

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Workspace Settings                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Name:        [IJCAI Paper 2026_______________]                            │
│                                                                             │
│  Visibility:                                                               │
│  ◉ Private    (Only me and invited members)                                │
│  ○ Team       (All team members)                                           │
│  ○ Organization                                                            │
│                                                                             │
│  Main Document:                                                             │
│  [main.tex                           ▼]                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Setting | Description |
|---------|-------------|
| **Name** | Display name of the workspace |
| **Visibility** | Access level (private, team, org) |
| **Main Document** | Entry point for PDF compilation |

---

## File Tree & Panels

The left area combines **file tree**, **Git status**, and **outline**:

```
┌─────────────────────────────┐
│  Files                      │
├─────────────────────────────┤
│                             │
│  📁 IJCAI Paper 2026        │
│  ├── 📄 main.tex     [⭐]   │
│  ├── 📄 abstract.tex        │
│  ├── 📄 introduction.tex    │
│  ├── 📁 sections            │
│  │   ├── 📄 related.tex     │
│  │   ├── 📄 method.tex      │
│  │   └── 📄 results.tex     │
│  ├── 📁 figures             │
│  │   ├── 🖼️ diagram.png     │
│  │   └── 🖼️ results.pdf     │
│  └── 📄 references.bib      │
│                             │
│  [+ File]  [+ Folder]       │
│                             │
└─────────────────────────────┘
```

### Manage Files

| Action | Description |
|--------|-------------|
| **New File** | Create a `.tex` file |
| **New Folder** | Create subfolder |
| **Rename** | Double click or right click |
| **Move** | Drag & drop into folder |
| **Delete** | Right click → Delete |
| **Set as Main Document** | Star icon for compilation |

### Upload Assets

Images and PDFs can be uploaded:

- **Drag & drop** into the file tree
- **Right click** → Upload asset
- Supported formats: PNG, JPG, PDF, EPS

### Outline

The outline shows the structure of the current document (parts/chapters/sections).
A click jumps directly to the position in the editor.

---

## Editor

The Monaco editor provides professional LaTeX editing:

### Features

| Feature | Description |
|---------|-------------|
| **Syntax Highlighting** | LaTeX commands highlighted in color |
| **Autocomplete** | `\begin{` → suggestions for environments |
| **Bracket Matching** | Matching brackets highlighted |
| **Line Numbers** | For error navigation |
| **Multiple Cursors** | Ctrl+click for parallel edits |
| **Review Mode** | Focused view for comments |
| **Ghost Text (optional)** | AI suggestions as subtle overlay |

### Real-Time Collaboration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  main.tex                                             🟢 admin  🔵 researcher│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1  │ \documentclass{article}                                              │
│  2  │ \usepackage[utf8]{inputenc}                                          │
│  3  │                                                                      │
│  4  │ \begin{document}                                                     │
│  5  │                                                                      │
│  6  │ \section{Introduction}               ← 🟢 admin editing here          │
│  7  │ Lorem ipsum dolor sit amet...                                        │
│  8  │                                                                      │
│  9  │ \section{Methods}                    ← 🔵 researcher here            │
│ 10  │ We propose a novel approach...                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Live cursor** of other users visible
- **Color coding** per user
- **Conflict-free** editing via YJS

---

## Comments

### Create a Comment

1. **Select text** in the editor
2. Click the **comment icon** or `Ctrl+Shift+C`
3. **Write comment** → submit

```
┌─────────────────────────────────────────┐
│  New Comment                             │
├─────────────────────────────────────────┤
│                                         │
│  Selected text:                          │
│  "Lorem ipsum dolor sit amet"           │
│                                         │
│  Comment:                                │
│  [Add a source here______________]       │
│  [for the claim.________________]        │
│                                         │
│                    [Cancel] [Send]       │
│                                         │
└─────────────────────────────────────────┘
```

### Comment Thread

Comments can have replies:

```
┌─────────────────────────────────────────┐
│  💬 admin · 2 hours ago                 │
│  ───────────────────────────────────    │
│  "Lorem ipsum dolor sit amet"           │
│                                         │
│  A source should be added               │
│  for the claim.                         │
│                                         │
│  └─ 💬 researcher · 1 hour ago           │
│     Which source do you mean?           │
│                                         │
│  └─ 💬 admin · 30 min ago                │
│     Smith et al. 2024                   │
│                                         │
│  [Reply]  [🤖 AI Resolve]  [✓ Resolve]   │
└─────────────────────────────────────────┘
```

### AI-Assisted Comment Resolution

The AI can apply comments automatically:

1. **Open comment**
2. Click **AI Resolve**
3. AI analyzes context and comment
4. **Suggested change** is shown
5. **Apply change** or reject

```
┌─────────────────────────────────────────┐
│  🤖 LLARS AI                            │
│  ───────────────────────────────────    │
│                                         │
│  Change suggested:                       │
│                                         │
│  - Lorem ipsum dolor sit amet           │
│  + Lorem ipsum dolor sit amet           │
│    (Smith et al., 2024).                │
│                                         │
│  Explanation:                            │
│  I added the citation as requested      │
│  in the comment.                        │
│                                         │
│           [Reject]  [Apply]             │
└─────────────────────────────────────────┘
```

!!! tip "AI context"
    The AI considers 1000 characters before and after the selected text
    for better understanding.

**Streaming:** During AI processing, tokens are streamed live and shown at the end
as a proposal you can apply.

---

## Git Versioning

### Git Panel

The Git panel shows uncommitted changes:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Git                                                         [↗ Expand]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Changes: +12 / -3 lines                                                   │
│                                                                             │
│  Modified files:                                                           │
│  ☑ main.tex           (+5, -2)                                             │
│  ☑ introduction.tex   (+7, -1)                                             │
│  ☐ references.bib     (+0, -0)                                             │
│                                                                             │
│  Commit message:                                                            │
│  [Reworked introduction______________]                                    │
│                                                                             │
│  [Create commit]                                                            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Recent commits:                                                            │
│  ├── "Abstract finalized" (admin) · 2 hrs ago                             │
│  ├── "Method added" (researcher) · 1 day ago                              │
│  └── "Initial version" (admin) · 3 days ago                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Diff View

Click a modified file to see differences:

```
┌────────────────────────────┬────────────────────────────┐
│  Before                    │  After                     │
├────────────────────────────┼────────────────────────────┤
│  \section{Introduction}    │  \section{Introduction}    │
│                            │                            │
│  Lorem ipsum dolor sit     │  Lorem ipsum dolor sit     │
│  amet.                     │  amet, consectetur         │
│                            │  adipiscing elit.          │
│                            │                            │
│  We propose a method.      │  We propose a novel        │
│                            │  approach based on deep    │
│                            │  learning.                 │
└────────────────────────────┴────────────────────────────┘
```

### Restore Commit

1. Open **commit history**
2. Select a **commit**
3. Click **Restore**
4. The document is reset to the commit version

!!! warning "Caution"
    Restoring overwrites current content. Create a commit first
    to preserve changes.

### Version Compilation

The PDF preview can be built for **current files** or **a commit**.
Select this in the compile toolbar.

---

## PDF Compilation

### Compile

1. Click **Compile** (or `Ctrl+S`)
2. **latexmk** is executed
3. The **PDF** is shown in the viewer

### Compilation Log

On errors, the log is shown:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Compilation Log                                               [Close]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⚠️ Warnings (2)                                                            │
│  ├── Line 45: Underfull \hbox                                               │
│  └── Line 78: Package hyperref Warning                                      │
│                                                                             │
│  ❌ Errors (1)                                                              │
│  └── Line 23: Undefined control sequence \unknowncommand                    │
│                                                                             │
│  [Jump to line 23]                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Auto-Compile

You can enable auto-compile in the toolbar menu:

- **Auto-compile** on/off
- **Delay** (ms)
- **Enable sync** (for SyncTeX)

### SyncTeX Navigation

Bidirectional sync between editor and PDF:

| Action | Result |
|--------|--------|
| **Editor → PDF** | Click line → PDF scrolls to position |
| **PDF → Editor** | Ctrl+click in PDF → editor jumps to line |

---

## Sharing & Members

### Invite Members

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Share Workspace                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Invite users:                                                              │
│  [researcher@example.com_________] [+ Invite]                               │
│                                                                             │
│  Current members:                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  👤 admin          Owner         ──                                  │  │
│  │  👤 researcher     Member        [Remove]                            │  │
│  │  👤 evaluator      Member        [Remove]                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Roles

| Role | Rights |
|------|--------|
| **Owner** | Full control, can manage members |
| **Member** | Edit, comment, compile |

---

## Zotero (Optional)

Zotero libraries can be integrated:

- BibTeX files are synced automatically
- Zotero files are **read-only**
- Connect via OAuth or API key

---

## Import/Export

### ZIP Export

1. **Menu** → **Export as ZIP**
2. Full project is downloaded
3. Contains all files, images, and assets

### ZIP Import

1. **Menu** → **Import ZIP**
2. Select ZIP file
3. Structure is created in the workspace

---

## API Endpoints

### Workspace

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/latex-collab/workspaces` | GET | List workspaces |
| `/api/latex-collab/workspaces` | POST | Create workspace |
| `/api/latex-collab/workspaces/:id` | GET | Workspace details |
| `/api/latex-collab/workspaces/:id` | PATCH | Update workspace |
| `/api/latex-collab/workspaces/:id` | DELETE | Delete workspace |
| `/api/latex-collab/workspaces/:id/leave` | POST | Leave workspace |
| `/api/latex-collab/workspaces/:id/members` | GET/POST | Manage members |
| `/api/latex-collab/workspaces/:id/members/:username` | DELETE | Remove member |

### Documents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/latex-collab/workspaces/:id/tree` | GET | Fetch file tree |
| `/api/latex-collab/documents/content` | POST | Load document content |
| `/api/latex-collab/documents` | POST | Create file/folder |
| `/api/latex-collab/workspaces/:id/main` | PATCH | Set main document |
| `/api/latex-collab/documents/:id` | PATCH | Rename, move |
| `/api/latex-collab/documents/:id` | DELETE | Delete |

### Comments

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/latex-collab/workspaces/:id/comments` | GET | Workspace comments |
| `/api/latex-collab/documents/:id/comments` | GET/POST | Comments |
| `/api/latex-collab/comments/:id` | PATCH/DELETE | Update/delete comment |
| `/api/latex-collab/comments/:id/replies` | POST | Replies |
| `/api/latex-collab/comments/:id/ai-resolve/status` | GET | AI status |
| `/api/latex-collab/comments/:id/ai-resolve` | POST | AI resolve |

### Git / Commits

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/latex-collab/workspaces/:id/changes` | GET | Workspace changes |
| `/api/latex-collab/workspaces/:id/commit` | POST | Commit workspace |
| `/api/latex-collab/documents/:id/commits` | GET | Commit list |
| `/api/latex-collab/documents/:id/commits/:commit_id` | GET | Commit details |
| `/api/latex-collab/documents/:id/commit` | POST | Commit document |
| `/api/latex-collab/documents/:id/baseline` | GET | Fetch baseline |
| `/api/latex-collab/documents/:id/diff` | GET | Fetch diff |
| `/api/latex-collab/documents/:id/rollback` | POST | Rollback |
| `/api/latex-collab/documents/:id/restore` | POST | Restore |

### Compilation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/latex-collab/workspaces/:id/compile` | POST | Start compilation |
| `/api/latex-collab/compile/:id` | GET | Compile status |
| `/api/latex-collab/workspaces/:id/pdf` | GET | Download PDF |
| `/api/latex-collab/compile/:id/synctex/forward` | POST | SyncTeX forward |
| `/api/latex-collab/compile/:id/synctex/inverse` | POST | SyncTeX inverse |

### Assets

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/latex-collab/workspaces/:id/assets` | POST | Upload asset |
| `/api/latex-collab/assets/:id` | GET | Download asset |

### ZIP

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/latex-collab/workspaces/:id/export` | GET | Workspace as ZIP |
| `/api/latex-collab/workspaces/import` | POST | ZIP → new workspace |
| `/api/latex-collab/workspaces/:id/import` | POST | ZIP → existing workspace |

---

## Socket.IO Events (Realtime)

| Event | Description |
|-------|-------------|
| `latex_collab:workspace_shared` | Workspace shared |
| `latex_collab:commit_created` | Commit created |
| `latex_collab:comment_changed` | Comment changed |
| `latex_collab:workspace_comment_changed` | Workspace comments changed |
| `latex_collab:compile_status` | Compile status update |
| `latex_collab:ai_resolve:token` | AI token stream |
| `latex_collab:ai_resolve:completed` | AI suggestion ready |
| `latex_collab:ai_resolve:error` | AI error |

---

## Permissions

| Permission | Description |
|------------|-------------|
| `feature:latex_collab:view` | View workspaces |
| `feature:latex_collab:edit` | Edit, comment |
| `feature:latex_collab:share` | Manage members |

---

## See Also

- [Prompt Engineering](prompt-engineering.md) - Create prompts
- [Permission System](permission-system.md) - Access rights
