# WebSocket API

Diese Seite dokumentiert die wichtigsten Socket.IO WebSocket-Endpunkte und Events.

!!! info "Verbindung"
    LLARS nutzt zwei Socket.IO-Endpunkte:
    - Backend: `http://localhost:55080` mit Pfad `/socket.io/`
    - Collaboration (YJS): `http://localhost:55080/collab` mit Pfad `/collab/socket.io/` (nginx → Port 8082)

---

## Verbindung herstellen

### Client-Setup (JavaScript)

```javascript
import { io } from 'socket.io-client'

const socket = io('http://localhost:55080', {
  path: '/socket.io/',
  auth: {
    token: 'Bearer <access_token>'
  },
  transports: ['websocket', 'polling']
})

socket.on('connect', () => {
  console.log('Connected:', socket.id)
})

socket.on('connect_error', (error) => {
  console.error('Connection failed:', error)
})
```

### Authentifizierung

Alle Namespaces außer dem Default-Namespace erfordern JWT-Authentifizierung:

```javascript
socket.auth = { token: 'Bearer <access_token>' }
socket.connect()
```

---

## Namespaces

LLARS verwendet verschiedene Namespaces für unterschiedliche Funktionen:

| Namespace | Beschreibung | Auth Required |
|-----------|--------------|---------------|
| `/` | Default (Health Check) | ❌ |
| `/chat` | Chat-Streaming | ✅ |
| `/rag` | RAG-Dokument-Updates | ✅ |
| `/collab` | LaTeX/Markdown Collaboration (separater Socket-Server) | ✅ |
| `/judge` | LLM Evaluator Updates | ✅ |
| `/admin` | Docker Monitor, DB Explorer | ✅ (Admin) |
| `/oncoco` | OnCoCo Analyse | ✅ |

**Hinweis:** Die Collaboration-WebSockets laufen über einen separaten Socket.IO-Server hinter `/collab`.
Dadurch ist es ein eigener Endpoint mit eigenem Event-Set, nicht nur ein Namespace.

---

## Chat Namespace (`/chat`)

### Events (Client → Server)

#### `chat:message`

Sendet eine Chat-Nachricht.

```javascript
socket.emit('chat:message', {
  chatbot_id: 1,
  session_id: 'unique-session-id',
  message: 'Hallo, wie geht es dir?',
  conversation_id: null,  // null für neue Konversation
  include_sources: true
})
```

#### `chat:stop`

Stoppt die aktuelle Streaming-Antwort.

```javascript
socket.emit('chat:stop', {
  session_id: 'unique-session-id'
})
```

### Events (Server → Client)

#### `chat:delta`

Streaming-Token der Antwort.

```javascript
socket.on('chat:delta', (data) => {
  // data = { delta: 'Hallo', session_id: '...' }
  responseText += data.delta
})
```

#### `chat:done`

Antwort abgeschlossen.

```javascript
socket.on('chat:done', (data) => {
  // data = {
  //   session_id: '...',
  //   conversation_id: 1,
  //   message_id: 42,
  //   sources: [...],
  //   tokens: { input: 150, output: 200 }
  // }
})
```

#### `chat:error`

Fehler während der Verarbeitung.

```javascript
socket.on('chat:error', (data) => {
  // data = { error: 'Rate limit exceeded', code: 'RATE_LIMIT' }
})
```

---

## RAG Namespace (`/rag`)

### Events (Client → Server)

#### `rag:subscribe`

Abonniert Updates für eine Collection.

```javascript
socket.emit('rag:subscribe', {
  collection_id: 1
})
```

#### `rag:unsubscribe`

Beendet Abonnement.

```javascript
socket.emit('rag:unsubscribe', {
  collection_id: 1
})
```

### Events (Server → Client)

#### `document:progress`

Fortschritt der Dokumentverarbeitung.

```javascript
socket.on('document:progress', (data) => {
  // data = {
  //   document_id: 1,
  //   status: 'processing',  // 'pending' | 'processing' | 'indexed' | 'failed'
  //   progress: 50,          // 0-100
  //   step: 'Creating embeddings',
  //   error: null
  // }
})
```

#### `document:indexed`

Dokument erfolgreich indexiert.

```javascript
socket.on('document:indexed', (data) => {
  // data = {
  //   document_id: 1,
  //   chunk_count: 45,
  //   collection_id: 1
  // }
})
```

#### `collection:updated`

Collection-Statistiken aktualisiert.

```javascript
socket.on('collection:updated', (data) => {
  // data = {
  //   collection_id: 1,
  //   total_documents: 10,
  //   total_chunks: 450,
  //   pending_documents: 2
  // }
})
```

---

## Collab Namespace (`/collab`)

Für LaTeX und Markdown Echtzeit-Kollaboration (YJS).

### Events (Client → Server)

#### `collab:join`

Workspace beitreten.

```javascript
socket.emit('collab:join', {
  workspace_id: 1,
  document_id: 5,
  type: 'latex'  // 'latex' | 'markdown'
})
```

#### `collab:sync`

YJS-Sync-Update senden.

```javascript
socket.emit('collab:sync', {
  document_id: 5,
  update: '<base64-encoded-yjs-update>'
})
```

#### `collab:awareness`

Awareness-Update (Cursor-Position, etc.).

```javascript
socket.emit('collab:awareness', {
  document_id: 5,
  state: {
    user: { name: 'Max', color: '#b0ca97' },
    cursor: { line: 10, ch: 5 }
  }
})
```

#### `collab:leave`

Workspace verlassen.

```javascript
socket.emit('collab:leave', {
  document_id: 5
})
```

### Events (Server → Client)

#### `collab:sync`

YJS-Sync-Update von anderem Client.

```javascript
socket.on('collab:sync', (data) => {
  // data = { document_id: 5, update: '<base64>' }
  Y.applyUpdate(ydoc, decodeUpdate(data.update))
})
```

#### `collab:awareness`

Awareness-Update von anderem Client.

```javascript
socket.on('collab:awareness', (data) => {
  // data = {
  //   document_id: 5,
  //   client_id: 'abc123',
  //   state: { user: {...}, cursor: {...} }
  // }
})
```

#### `collab:users`

Liste aktiver Benutzer im Dokument.

```javascript
socket.on('collab:users', (data) => {
  // data = {
  //   document_id: 5,
  //   users: [
  //     { id: 1, name: 'Max', color: '#b0ca97', cursor: {...} }
  //   ]
  // }
})
```

---

## Judge Namespace (`/judge`)

### Events (Client → Server)

#### `judge:subscribe`

Session-Updates abonnieren.

```javascript
socket.emit('judge:subscribe', {
  session_id: 1
})
```

### Events (Server → Client)

#### `judge:progress`

Fortschritt der Judge-Session.

```javascript
socket.on('judge:progress', (data) => {
  // data = {
  //   session_id: 1,
  //   completed: 25,
  //   total: 100,
  //   current_comparison: {
  //     thread_id: 5,
  //     pillar: 'Relevanz'
  //   }
  // }
})
```

#### `judge:result`

Einzelnes Vergleichsergebnis.

```javascript
socket.on('judge:result', (data) => {
  // data = {
  //   session_id: 1,
  //   comparison_id: 42,
  //   winner: 'A',
  //   confidence: 0.85,
  //   pillar: 'Relevanz'
  // }
})
```

#### `judge:completed`

Session abgeschlossen.

```javascript
socket.on('judge:completed', (data) => {
  // data = {
  //   session_id: 1,
  //   total_comparisons: 100,
  //   summary: {...}
  // }
})
```

---

## Admin Namespace (`/admin`)

!!! warning "Nur für Admins"
    Dieser Namespace erfordert Admin-Berechtigungen.

### Docker Monitor

#### `docker:subscribe`

Docker-Updates abonnieren.

```javascript
socket.emit('docker:subscribe')
```

#### `docker:stats` (Server → Client)

Container-Statistiken.

```javascript
socket.on('docker:stats', (data) => {
  // data = {
  //   containers: [
  //     {
  //       id: 'abc123',
  //       name: 'llars_flask_service',
  //       status: 'running',
  //       cpu_percent: 2.5,
  //       memory_mb: 512,
  //       memory_limit_mb: 2048
  //     }
  //   ],
  //   summary: {
  //     total: 8,
  //     running: 8,
  //     total_cpu: 15.2,
  //     total_memory_mb: 4096
  //   }
  // }
})
```

#### `docker:logs`

Container-Logs abonnieren.

```javascript
socket.emit('docker:logs', {
  container_id: 'abc123',
  tail: 100
})

socket.on('docker:logs', (data) => {
  // data = {
  //   container_id: 'abc123',
  //   logs: ['[2025-12-01 10:00:00] INFO: ...', ...]
  // }
})
```

### DB Explorer

#### `db:list_tables`

Alle Tabellen auflisten.

```javascript
socket.emit('db:list_tables')

socket.on('db:tables', (data) => {
  // data = { tables: ['users', 'chatbots', 'rag_documents', ...] }
})
```

#### `db:query`

Tabelle abfragen.

```javascript
socket.emit('db:query', {
  table: 'users',
  limit: 50,
  offset: 0,
  order_by: 'created_at',
  order_dir: 'desc',
  filters: { role: 'admin' }
})

socket.on('db:result', (data) => {
  // data = {
  //   table: 'users',
  //   rows: [...],
  //   total: 150,
  //   columns: ['id', 'username', 'email', ...]
  // }
})
```

---

## OnCoCo Namespace (`/oncoco`)

### Events

#### `oncoco:analyze`

Analyse starten.

```javascript
socket.emit('oncoco:analyze', {
  text: 'Konversationstext...',
  options: { detailed: true }
})
```

#### `oncoco:result`

Analyse-Ergebnis.

```javascript
socket.on('oncoco:result', (data) => {
  // data = {
  //   categories: [
  //     { name: 'Greeting', confidence: 0.95 },
  //     { name: 'Question', confidence: 0.82 }
  //   ],
  //   analysis_id: 'xyz'
  // }
})
```

---

## Fehlerbehandlung

### Reconnection

Socket.IO reconnect automatisch bei Verbindungsabbruch:

```javascript
socket.on('reconnect', (attemptNumber) => {
  console.log('Reconnected after', attemptNumber, 'attempts')
  // Re-subscribe to rooms/namespaces
})

socket.on('reconnect_error', (error) => {
  console.error('Reconnection failed:', error)
})
```

### Error Events

```javascript
socket.on('error', (data) => {
  // data = { code: 'AUTH_FAILED', message: 'Token expired' }
})
```

### Timeout

```javascript
socket.emit('chat:message', data, (response) => {
  // Acknowledgement callback (optional)
  if (response.error) {
    console.error('Message failed:', response.error)
  }
})
```

---

## Best Practices

### 1. Namespace-Trennung

```javascript
const chatSocket = io('/chat', { auth: { token } })
const ragSocket = io('/rag', { auth: { token } })
```

### 2. Cleanup bei Unmount

```javascript
onUnmounted(() => {
  socket.emit('collab:leave', { document_id })
  socket.disconnect()
})
```

### 3. Exponential Backoff

```javascript
socket.io.on('reconnect_attempt', (attempt) => {
  socket.io.opts.reconnectionDelay = Math.min(1000 * Math.pow(2, attempt), 30000)
})
```
