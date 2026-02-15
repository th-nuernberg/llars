# Prompt Engineering

**Version:** 1.0 | **Date:** January 2026

Prompt Engineering is a collaborative workspace for designing, organizing, testing, and versioning prompts. It combines a visual block editor with Git-like version control, variable management, and LLM testing features.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Prompt Engineering                                     [+ New Prompt]       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  My Prompts                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ API Assistant   │  │ Support Bot     │  │ Code Review     │             │
│  │ Updated:        │  │ Updated:        │  │ Updated:        │             │
│  │ Today           │  │ Yesterday       │  │ 3 days ago      │             │
│  │ 👤 👤 +2        │  │                 │  │ 👤              │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  Shared with me                                                            │
│  ┌─────────────────┐                                                        │
│  │ Team Prompt     │                                                        │
│  │ By: researcher  │                                                        │
│  └─────────────────┘                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

!!! tip "Your first prompt in 5 steps"
    1. **New Prompt** -> enter name -> create
    2. **Add block** -> e.g. "System Instruction"
    3. **Enter text** -> rich text editor with formatting
    4. **Use variables** -> insert `{{variable}}` via drag & drop
    5. **Test** -> run prompt with an LLM

---

## Editor Workspace

After clicking a prompt, the editor opens:

```
┌────────────────────┬───────────────────────────────────────────────────────┐
│  Sidebar           │  Editor                                               │
│  ───────────────   │  ──────────────────────────────────────────────────   │
│                    │                                                       │
│  🟢 Online: 2      │  ┌─────────────────────────────────────────────────┐ │
│                    │  │ ≡ System Instruction                [✎] [🗑]   │ │
│  Actions:          │  ├─────────────────────────────────────────────────┤ │
│  [+ Block]         │  │ You are a helpful assistant.                    │ │
│  [📝 Variables]    │  │ Always respond in {{language}}.                 │ │
│  [👁 Preview]      │  └─────────────────────────────────────────────────┘ │
│  [🧪 Test]          │                                                       │
│                    │  ┌─────────────────────────────────────────────────┐ │
│  Variables:        │  │ ≡ User Context                      [✎] [🗑]   │ │
│  ┌──────────────┐  │  ├─────────────────────────────────────────────────┤ │
│  │ {{language}} │  │  │ The user asks: {{user_query}}                   │ │
│  │ {{user_query}}│  │  │                                                 │ │
│  └──────────────┘  │  └─────────────────────────────────────────────────┘ │
│                    │                                                       │
│  Import/Export:    │                                                       │
│  [⬇ Download]      │                                                       │
│  [📋 Copy]         │                                                       │
│                    │                                                       │
│  Git:              │                                                       │
│  [+12/-3 Synced]   │                                                       │
│                    │                                                       │
└────────────────────┴───────────────────────────────────────────────────────┘
```

---

## Features

### Block-Based Editing

Prompts consist of multiple blocks that can be edited individually:

| Action | Description |
|--------|-------------|
| **Add block** | Click "+ Block" -> enter name |
| **Rename block** | Double click on title or pencil icon |
| **Delete block** | Trash icon -> confirm |
| **Move block** | Drag handle (≡) |
| **Edit text** | Rich text editor with formatting |

!!! info "Block structure"
    Typical blocks: `System Instruction`, `Context`, `Examples`, `User Query`, `Output Format`

!!! tip "System block for batch generation"
    If a block has the title `System`, Batch Generation uses that content as the **system prompt**.
    All remaining blocks are concatenated in order into one **user prompt**.

---

### Variable System

Variables enable dynamic prompts:

```
Syntax: {{variable_name}}
Allowed: letters, numbers, underscores
Examples: {{language}}, {{user_query}}, {{context_data}}
```

#### Manage variables

```
┌─────────────────────────────────────────┐
│  Variable Manager                       │
├─────────────────────────────────────────┤
│  New variable:                          │
│  Name: [user_name________]              │
│  Value: [John Doe__________]            │
│  [+ Add]                                │
├─────────────────────────────────────────┤
│  Existing variables:                    │
│  ┌────────────────────────────────────┐ │
│  │ {{language}}  -> "German"    [🗑]  │ │
│  │ {{context}}   -> "Support..." [🗑] │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

| Feature | Description |
|---------|-------------|
| **Palette** | Drag & drop from sidebar into editor |
| **Manager** | CRUD for variable names and values |
| **Extraction** | Auto-detect from prompt text |
| **Synchronization** | Real-time sync between users |

---

### Real-Time Collaboration

Multiple users can work on the same prompt simultaneously:

```
┌─────────────────────────────────────────┐
│  🟢 Online (3)                          │
│  ├── admin (Owner)         🔴           │
│  ├── researcher            🟢           │
│  └── evaluator             🔵           │
└─────────────────────────────────────────┘
```

| Feature | Description |
|---------|-------------|
| **Live cursor** | Color-coded cursor per user |
| **Text highlighting** | Changes by other users are highlighted |
| **Auto-sync** | Changes are synchronized instantly |
| **Conflict-free** | CRDT technology (Yjs) prevents conflicts |

!!! tip "Technology"
    Collaboration uses Yjs + Socket.IO for real-time, conflict-free synchronization.

---

### Test a Prompt

The test dialog allows running prompts with different LLMs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Test Prompt                                                                │
├────────────────────────────┬────────────────────────────────────────────────┤
│  Variables                 │  Configuration                                 │
│  ─────────────────         │  ──────────────────────────────────────────    │
│                            │                                                │
│  {{language}}              │  Model: [GPT-4o          ▼]                    │
│  [German_______]  ✓        │  Temperature: [0.7_______]                     │
│                            │  Max Tokens: [2000______]                      │
│  {{user_query}}            │                                                │
│  [How does ...]  ✓         │  [ ] JSON mode                                 │
│                            │                                                │
│  {{context}}               │  [▶ Run]                                       │
│  [_______________]  ⚠      │                                                │
│                            ├────────────────────────────────────────────────┤
│                            │  Response                                     │
│                            │  ──────────────────────────────────────────    │
│                            │  The feature works as follows...               │
│                            │  █                                             │
│                            │                                                │
└────────────────────────────┴────────────────────────────────────────────────┘
```

| Option | Description |
|--------|-------------|
| **Model** | GPT-4o, Claude 3.5, Mistral, etc. |
| **Temperature** | 0.0 (deterministic) to 1.0 (creative) |
| **Max Tokens** | Maximum response length |
| **JSON Mode** | Force structured JSON responses |
| **Streaming** | Real-time display of generation |

---

### Git Version Control

Changes can be versioned like Git:

```
┌─────────────────────────────────────────┐
│  Git Panel                    [▼]       │
├─────────────────────────────────────────┤
│  Status: +12 / -3 lines changed         │
│                                         │
│  Contributions:                         │
│  admin:      +8 / -2                    │
│  researcher: +4 / -1                    │
│                                         │
│  Commit message:                        │
│  [Added variable___________]            │
│  [Create commit]                         │
├─────────────────────────────────────────┤
│  History:                               │
│  ├── "Added variable" (admin)           │
│  │   2 hours ago                        │
│  ├── "Improved system prompt"           │
│  │   1 day ago                          │
│  └── "Initial version"                  │
│      3 days ago                         │
└─────────────────────────────────────────┘
```

| Feature | Description |
|---------|-------------|
| **Commit** | Snapshot of the current state |
| **Diff tracking** | Insertions/deletions per block |
| **Contribution tracking** | Changes per user |
| **History** | Up to 200 commits stored |
| **Snapshot view** | Full content of each commit |

---

### Sharing & Permissions

Prompts can be shared with other users:

| Role | Rights |
|------|--------|
| **Owner** | Full rights + manage sharing |
| **Shared user** | Read + edit, no sharing |

```
┌─────────────────────────────────────────┐
│  Shared with:                           │
│  ┌────────────────────────────────────┐ │
│  │ 👤 researcher            [Remove] │ │
│  │ 👤 evaluator             [Remove] │ │
│  └────────────────────────────────────┘ │
│                                         │
│  Add user:                              │
│  [Search...___________] [+ Share]       │
└─────────────────────────────────────────┘
```

---

### Import/Export

| Format | Description |
|--------|-------------|
| **JSON Download** | Block names as keys, content as values |
| **Clipboard** | Same format to clipboard |
| **JSON Upload** | Import with option: append or replace |

**Export format:**
```json
{
  "System Instruction": "You are a helpful assistant...",
  "User Context": "The user asks: {{user_query}}"
}
```

---

## Workflow Example

### Create and test a prompt

1. **Create**: `/promptengineering` -> "New Prompt" (German UI: "Neuer Prompt") -> "API Assistant"
2. **Structure**: Add blocks:
   - `System Instruction` -> role and behavior
   - `Context` -> context information
   - `Output Format` -> desired output format
3. **Variables**: Insert `{{api_endpoint}}`, `{{user_request}}`
4. **Test**: Test dialog -> fill variables -> run
5. **Version**: Git panel -> commit "Initial version"
6. **Share**: Add team members

---

## Preview Mode

The preview dialog shows the composed prompt:

| Mode | Description |
|------|-------------|
| **Placeholder** | `{{variables}}` highlighted as tags |
| **Resolved** | Variables replaced with values |

!!! warning "Unresolved variables"
    Variables without values are highlighted in orange in resolved mode.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/prompts` | GET | List own prompts |
| `/api/prompts` | POST | Create a new prompt |
| `/api/prompts/:id` | GET | Prompt details |
| `/api/prompts/:id` | PUT | Update prompt |
| `/api/prompts/:id` | DELETE | Delete prompt |
| `/api/prompts/:id/rename` | PUT | Rename prompt |
| `/api/prompts/:id/share` | POST | Share with user |
| `/api/prompts/:id/unshare` | POST | Revoke sharing |
| `/api/prompts/:id/commit` | POST | Create commit |
| `/api/prompts/:id/commits` | GET | Commit history |
| `/api/prompts/shared` | GET | Shared prompts |
| `/api/prompts/templates` | GET | Prompts for batch generation |

---

## Permissions

| Permission | Description |
|------------|-------------|
| `feature:prompts:view` | View prompts |
| `feature:prompts:manage` | Create/edit prompts |

---

## See Also

- [Batch Generation](batch-generation.md) - Run prompts at scale
- [Permission System](permission-system.md) - Access control
- [Chatbot Wizard](chatbot-wizard.md) - Create chatbots with prompts
