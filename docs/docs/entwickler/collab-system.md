# Collaboration System

Diese Seite dokumentiert das Echtzeit-Kollaborationssystem für den Markdown Editor.

!!! info "Technologie-Stack"
    - **YJS** - CRDT-basierte Konfliktlösung
    - **Socket.IO** - Echtzeit-WebSocket-Kommunikation
    - **CodeMirror 6** - Editor-Integration
    - **MariaDB** - Persistente Speicherung

---

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend                                   │
│         ┌──────────────┐            ┌──────────────────────┐        │
│         │MarkdownEditor│            │  WorkspaceGitPanel   │        │
│         │    Pane      │            │                      │        │
│         └──────┬───────┘            └──────────┬───────────┘        │
│                │                                │                    │
│      ┌─────────▼─────────┐              ┌──────▼──────────┐         │
│      │useYjsCollaboration│              │  checkForChanges │         │
│      │   (Composable)    │◄─────────────│    (API Call)    │         │
│      └─────────┬─────────┘              └─────────────────┘         │
│                │ document_saved                                      │
└────────────────┼─────────────────────────────────────────────────────┘
                 │ Socket.IO (/collab)
                 ▼
┌───────────────────────────────────────────────────────────────────┐
│                        YJS Server (:8082)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │  Y.Doc      │  │  Room       │  │   Workspace Room        │   │
│  │  Cache      │  │  Manager    │  │   (document_saved)      │   │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘   │
│         │                │                      │                  │
│         └────────────────┼──────────────────────┘                  │
│                          │                                         │
│                   ┌──────▼──────┐                                  │
│                   │ saveYdocToDB │                                  │
│                   │ (2s debounce)│                                  │
│                   └──────┬──────┘                                  │
└──────────────────────────┼─────────────────────────────────────────┘
                           │ SQL
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│                      MariaDB                                       │
│                 ┌──────────────────┐                              │
│                 │markdown_documents│                              │
│                 │ - content (YJS)  │                              │
│                 │ - content_text   │                              │
│                 └──────────────────┘                              │
└───────────────────────────────────────────────────────────────────┘
```

---

## Datenfluss

### 1. Editor-Synchronisation (YJS)

```mermaid
sequenceDiagram
    participant User1 as Benutzer 1
    participant Editor1 as Editor (Browser 1)
    participant YJS as YJS Server
    participant Editor2 as Editor (Browser 2)
    participant User2 as Benutzer 2

    User1->>Editor1: Tippt Text
    Editor1->>YJS: sync_update (Y.Doc Delta)
    YJS->>Editor2: sync_update (Broadcast)
    Editor2->>User2: Zeigt Änderung

    Note over YJS: Nach 2s Inaktivität
    YJS->>YJS: saveYdocToDB()
    YJS-->>Editor1: document_saved
    YJS-->>Editor2: document_saved
```

### 2. Git Panel Echtzeit-Updates

```mermaid
sequenceDiagram
    participant Editor as EditorPane
    participant YJS as YJS Server
    participant Parent as WorkspaceComponent
    participant GitPanel as GitPanel

    Editor->>YJS: sync_update
    Note over YJS: 2s Debounce
    YJS->>YJS: saveYdocToDB()
    YJS->>Editor: document_saved (WebSocket)
    Editor->>Parent: @document-saved Event
    Parent->>GitPanel: checkForChanges()
    GitPanel->>GitPanel: API: GET /changes
    GitPanel->>GitPanel: UI aktualisieren
```

---

## YJS Server Events

### Socket.IO Namespace: `/collab`

Der YJS Server läuft auf Port 8082 und kommuniziert über Socket.IO.

### Room-Struktur

```javascript
// Dokument-Rooms (für Sync)
"markdown_{document_id}"   // z.B. "markdown_15"

// Workspace-Rooms (für document_saved Events)
"workspace_markdown_{workspace_id}"   // z.B. "workspace_markdown_1"
```

### Events (Client → Server)

#### `join_room`

Tritt einem Dokument-Room bei und automatisch dem zugehörigen Workspace-Room.

```javascript
socket.emit('join_room', {
  room: 'markdown_15',    // Dokument-Room
  username: 'admin'
})

// Server führt automatisch aus:
// 1. socket.join('markdown_15')
// 2. socket.join('workspace_markdown_{workspace_id}')
```

#### `sync_update`

Sendet YJS-Änderungen an andere Clients.

```javascript
socket.emit('sync_update', {
  room: 'markdown_15',
  update: Array.from(Y.encodeStateAsUpdate(ydoc))
})
```

#### `leave_room`

Verlässt einen Room.

```javascript
socket.emit('leave_room', {
  room: 'markdown_15'
})
```

#### `reload_room`

Erzwingt Neuladen aus der Datenbank (nach Rollback).

```javascript
socket.emit('reload_room', { room: 'markdown_15' }, (response) => {
  // response = { success: true }
})
```

### Events (Server → Client)

#### `snapshot_document`

Vollständiger Dokument-State beim Beitreten.

```javascript
socket.on('snapshot_document', (fullUpdate) => {
  Y.applyUpdate(ydoc, new Uint8Array(fullUpdate))
})
```

#### `sync_update`

Inkrementelles Update von anderen Clients.

```javascript
socket.on('sync_update', ({ update }) => {
  Y.applyUpdate(ydoc, new Uint8Array(update))
})
```

#### `document_saved`

Wird an alle Clients im Workspace-Room gesendet, nachdem ein Dokument in der DB gespeichert wurde.

```javascript
socket.on('document_saved', (data) => {
  // data = {
  //   documentId: 15,
  //   workspaceId: 1,
  //   kind: 'markdown',
  //   contentLength: 1500,
  //   savedAt: '2025-01-03T12:00:00.000Z'
  // }

  // Typische Verwendung: Git Panel aktualisieren
  if (data.workspaceId === currentWorkspaceId) {
    gitPanel.checkForChanges()
  }
})
```

**Wichtig:** Dieses Event wird an den **Workspace-Room** gesendet, nicht an den Dokument-Room. Dadurch erhalten alle Benutzer im selben Workspace das Event, unabhängig davon welches Dokument sie gerade bearbeiten.

#### `room_state`

Aktuelle Benutzer und Cursor-Positionen.

```javascript
socket.on('room_state', (state) => {
  // state = {
  //   users: { socketId: { username, color } },
  //   cursors: { socketId: { line, ch } }
  // }
})
```

#### `user_joined` / `user_left`

Benutzer betritt/verlässt den Room.

```javascript
socket.on('user_joined', ({ userId, username, color }) => {
  // Neuen Benutzer in UI anzeigen
})

socket.on('user_left', ({ userId }) => {
  // Benutzer-Cursor entfernen
})
```

---

## Frontend-Integration

### useYjsCollaboration Composable

Das Composable verwaltet die Socket.IO-Verbindung und YJS-Dokument-Synchronisation.

```javascript
import { useYjsCollaboration } from '@/components/PromptEngineering/composables/useYjsCollaboration'

const collaboration = useYjsCollaboration(
  roomId,           // Ref<string> - z.B. 'markdown_15'
  username,         // string
  processYDoc,      // Callback für Dokument-Updates
  onUpdateCursor,   // Callback für Cursor-Updates
  {
    autoSync: true,
    onColorUpdate: (userId, color) => { /* ... */ },
    onDocumentSaved: (data) => {
      // Echtzeit Git Panel Updates
      emit('document-saved', data)
    }
  }
)

const {
  ydoc,           // Ref<Y.Doc>
  socket,         // Ref<Socket>
  users,          // Ref<Object>
  initialize,     // () => void
  cleanup,        // () => void
  switchRoom,     // (oldRoom, newRoom) => void
  reloadRoom,     // () => Promise<boolean>
  reloadAnyRoom   // (roomName) => Promise<boolean>
} = collaboration
```

### Editor-Integration (MarkdownEditorPane)

```vue
<script setup>
const emit = defineEmits([
  'content-change',
  'document-saved'  // Für Git Panel Updates
])

const collaboration = useYjsCollaboration(roomId, username, processYDoc, onUpdateCursor, {
  autoSync: true,
  onDocumentSaved: (data) => {
    emit('document-saved', data)
  }
})
</script>
```

### Parent-Component (MarkdownCollabWorkspace)

```vue
<template>
  <MarkdownEditorPane
    ref="editorRef"
    :document="selectedNode"
    @document-saved="handleDocumentSaved"
  />

  <WorkspaceGitPanel
    ref="gitPanelRef"
    :workspace-id="workspaceId"
  />
</template>

<script setup>
const gitPanelRef = ref(null)

function handleDocumentSaved(data) {
  // Nur aktualisieren wenn Event für unseren Workspace ist
  if (data.workspaceId === workspaceId.value) {
    gitPanelRef.value?.checkForChanges?.()
  }
}
</script>
```

---

## Datenbank-Schema

### markdown_documents

```sql
CREATE TABLE markdown_documents (
  id INT PRIMARY KEY AUTO_INCREMENT,
  workspace_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  content LONGTEXT,           -- YJS JSON State
  content_text LONGTEXT,      -- Plain Text (für Suche/Diff)
  node_type ENUM('file', 'folder'),
  parent_id INT,
  order_index INT DEFAULT 0,
  last_editor_username VARCHAR(255),
  created_at DATETIME,
  updated_at DATETIME,
  deleted_at DATETIME,        -- Soft Delete

  FOREIGN KEY (workspace_id) REFERENCES markdown_workspaces(id),
  INDEX idx_workspace (workspace_id),
  INDEX idx_parent (parent_id)
);
```

### Dual-Content-Speicherung

Jedes Dokument hat zwei Content-Felder:

| Feld | Beschreibung | Verwendung |
|------|--------------|------------|
| `content` | YJS JSON State | Collaboration-Sync |
| `content_text` | Plain Text | Git-Diff, Suche, Baseline |

**Fallback-Logik:** Wenn `content` korrupt ist (z.B. nach Crash), wird `content_text` als Fallback verwendet.

---

## Git-Integration

### Workspace-Level Git Panel

Das Git Panel zeigt Änderungen für **alle Dokumente** im Workspace an.

```
┌─────────────────────────────────────┐
│ Git-Änderungen (3 Dateien)          │
├─────────────────────────────────────┤
│ ☑ README.md         +15 -3    [M]  │
│ ☑ kapitel1.md       +42 -0    [M]  │
│ ☐ notizen.md        +5  -2    [M]  │
├─────────────────────────────────────┤
│ Commit-Nachricht:                   │
│ ┌─────────────────────────────────┐ │
│ │ Kapitel 1 erweitert            │ │
│ └─────────────────────────────────┘ │
│                    [Commit]         │
└─────────────────────────────────────┘
```

### API-Endpunkte

#### GET `/api/markdown-collab/workspaces/{id}/changes`

Gibt alle uncommitted Änderungen zurück.

```json
{
  "success": true,
  "workspace_id": 1,
  "changed_files": [
    {
      "id": 15,
      "title": "README.md",
      "path": "README.md",
      "status": "M",
      "insertions": 15,
      "deletions": 3,
      "has_baseline": true
    }
  ],
  "deleted_files": [],
  "total_changes": 3
}
```

#### POST `/api/markdown-collab/workspaces/{id}/commit`

Committet mehrere Dateien gleichzeitig.

```json
// Request
{
  "message": "Kapitel 1 erweitert",
  "document_ids": [15, 16, 17]
}

// Response
{
  "success": true,
  "commits": [
    { "id": 100, "document_id": 15, "message": "..." },
    { "id": 101, "document_id": 16, "message": "..." }
  ],
  "total_committed": 2
}
```

### Echtzeit-Updates Flow

```
1. Benutzer tippt in Editor
   │
   ▼
2. YJS sync_update an Server (sofort)
   │
   ▼
3. Server speichert nach 2s Inaktivität
   │
   ▼
4. Server emittiert document_saved an Workspace-Room
   │
   ▼
5. Frontend empfängt Event
   │
   ▼
6. Git Panel ruft checkForChanges() auf
   │
   ▼
7. API-Call: GET /workspaces/{id}/changes
   │
   ▼
8. UI aktualisiert sich
```

---

## Rollback-Mechanismus

### Problem: YJS-Cache-Invalidierung

Beim Rollback muss der YJS-Server seinen Cache invalidieren, da er sonst veraltete Daten ausliefert.

### Lösung: reload_room Event

```javascript
// Frontend nach Rollback
async function handleRollback(payload) {
  const documentId = payload.documentId
  const roomName = `markdown_${documentId}`

  if (selectedDocumentId === documentId) {
    // Dokument ist offen: Kompletter Reload
    await editorRef.value?.reloadRoom?.()
  } else {
    // Dokument nicht offen: Nur Cache invalidieren
    await editorRef.value?.reloadAnyRoom?.(roomName)
  }
}
```

### Server-Seite (reload_room Handler)

```javascript
socket.on('reload_room', async (data, callback) => {
  const room = data.room

  // 1. Pending Save abbrechen
  const timer = saveTimers.get(room)
  if (timer) {
    clearTimeout(timer)
    saveTimers.delete(room)
  }

  // 2. Cache löschen
  ydocs.delete(room)

  // 3. Neu aus DB laden
  const doc = await loadYdocFromDB(room)
  ydocs.set(room, doc)

  // 4. An alle Clients broadcasten
  const fullState = Y.encodeStateAsUpdate(doc)
  io.to(room).emit('snapshot_document', fullState)

  callback({ success: true })
})
```

---

## Fehlerbehandlung

### Korrupte YJS-Daten

Wenn `content` nicht geparst werden kann, wird `content_text` als Fallback verwendet:

```javascript
async function loadYdocFromDB(roomName) {
  const [rows] = await pool.query(
    'SELECT content, content_text FROM markdown_documents WHERE id = ?',
    [roomId]
  )

  if (rows[0].content) {
    try {
      const doc = jsonToYdoc(rows[0].content)
      const text = doc.getText('content').toString()

      // Prüfen ob YJS-Inhalt valide ist
      if (text.length > 0 || !rows[0].content_text) {
        return doc
      }
    } catch (e) {
      console.error('YJS parse failed, using content_text fallback')
    }
  }

  // Fallback: content_text verwenden
  if (rows[0].content_text) {
    const doc = new Y.Doc()
    doc.getText('content').insert(0, rows[0].content_text)
    return doc
  }

  return new Y.Doc()
}
```

### Verbindungsabbruch

Socket.IO reconnect automatisch:

```javascript
socket.io.opts = {
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000
}

socket.on('reconnect', () => {
  // Room neu beitreten
  socket.emit('join_room', { room: currentRoom })
})
```

---

## Performance-Optimierungen

### 1. Debounced Persistence

Speicherung erfolgt erst nach 2 Sekunden Inaktivität:

```javascript
// Bei jedem sync_update
const existingTimer = saveTimers.get(room)
if (existingTimer) clearTimeout(existingTimer)

saveTimers.set(room, setTimeout(async () => {
  await saveYdocToDB(room, doc, ...)
}, 2000))
```

### 2. Workspace-Room-Broadcasts

`document_saved` Events gehen nur an Clients im selben Workspace, nicht an alle:

```javascript
const workspaceRoom = `workspace_markdown_${workspaceId}`
io.to(workspaceRoom).emit('document_saved', data)
```

### 3. Selektive Git Panel Updates

Git Panel aktualisiert nur bei Events für den aktuellen Workspace:

```javascript
function handleDocumentSaved(data) {
  if (data.workspaceId === workspaceId.value) {
    gitPanelRef.value?.checkForChanges?.()
  }
}
```

---

## Debugging

### YJS Server Logs

```bash
docker logs -f llars_yjs_service
```

Relevante Log-Nachrichten:

```
[join_room] Also joined workspace room: workspace_markdown_1
[saveYdocToDB] Room: markdown_15, docId: 15, contentLength: 1500
[document_saved] Emitted to workspace_markdown_1 for markdown doc 15
[reload_room] START - Reloading room "markdown_15" from database
```

### Frontend Console

```javascript
// In useYjsCollaboration
socket.on('document_saved', (data) => {
  console.log('[useYjsCollaboration] document_saved received:', data)
})

// In Parent Component
function handleDocumentSaved(data) {
  console.log('[MarkdownCollabWorkspace] document_saved received:', data)
}
```

### Netzwerk-Tab

WebSocket-Frames in Chrome DevTools:

1. **Filter:** `WS`
2. **Frames:** `document_saved`, `sync_update`, `snapshot_document`

---

## Troubleshooting

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Git Panel aktualisiert nicht | Event nicht empfangen | Prüfen ob im Workspace-Room |
| Dokument leer nach Rollback | YJS-Cache nicht invalidiert | `reloadRoom()` aufrufen |
| Änderungen gehen verloren | Speicherung vor Disconnect | `flush_document` vor Navigation |
| Cursor springt | Race Condition bei Sync | `applyingRemoteUpdate` Flag prüfen |

---

## Dateien

### Backend (YJS Server)

```
yjs-server/
├── server.js           # Express + Socket.IO Setup
├── websocket.js        # Event Handler + saveYdocToDB
└── db/
    └── db.js           # MySQL Pool
```

### Frontend

```
llars-frontend/src/
├── components/
│   ├── MarkdownCollab/
│   │   ├── MarkdownEditorPane.vue
│   │   └── MarkdownGitPanel.vue (deprecated)
│   └── PromptEngineering/
│       └── composables/
│           └── useYjsCollaboration.js
└── views/
    └── MarkdownCollab/
        └── MarkdownCollabWorkspace.vue
```
