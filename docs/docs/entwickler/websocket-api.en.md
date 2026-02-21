# WebSocket API

This page documents the most important Socket.IO WebSocket endpoints and events.

!!! info "Connection"
    LLARS uses two Socket.IO endpoints:
    - Backend: `http://localhost:55080` with path `/socket.io/`
    - Collaboration (YJS): `http://localhost:55080/collab` with path `/collab/socket.io/` (nginx → port 8082)

---

## Establish a connection

### Client setup (JavaScript)

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

### Authentication

All namespaces except the default namespace require JWT authentication:

```javascript
socket.auth = { token: 'Bearer <access_token>' }
socket.connect()
```

---

## Namespaces

LLARS uses different namespaces for different functions:

| Namespace | Description | Auth Required |
|-----------|-------------|---------------|
| `/` | Default (health check) | ❌ |
| `/chat` | Chat streaming | ✅ |
| `/rag` | RAG document updates | ✅ |
| `/collab` | LaTeX/Markdown collaboration (separate socket server) | ✅ |
| `/judge` | LLM evaluator updates | ✅ |
| `/admin` | Docker monitor, DB explorer | ✅ (Admin) |
| `/oncoco` | OnCoCo analysis | ✅ |

**Note:** Collaboration WebSockets run on a separate Socket.IO server behind `/collab`.
That makes it its own endpoint with its own event set, not just a namespace.

---

## Chat namespace (`/chat`)

### Events (Client → Server)

#### `chat:message`

Send a chat message.

```javascript
socket.emit('chat:message', {
  chatbot_id: 1,
  session_id: 'unique-session-id',
  message: 'Hello, how are you?',
  conversation_id: null,  // null for new conversation
  include_sources: true
})
```

#### `chat:stop`

Stop the current streaming response.

```javascript
socket.emit('chat:stop', {
  session_id: 'unique-session-id'
})
```

### Events (Server → Client)

#### `chat:delta`

Streaming tokens of the response.

```javascript
socket.on('chat:delta', (data) => {
  // data = { delta: 'Hello', session_id: '...' }
  responseText += data.delta
})
```

#### `chat:done`

Response completed.

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

Error during processing.

```javascript
socket.on('chat:error', (data) => {
  // data = { error: 'Rate limit exceeded', code: 'RATE_LIMIT' }
})
```

---

## RAG namespace (`/rag`)

### Events (Client → Server)

#### `rag:subscribe`

Subscribe to updates for a collection.

```javascript
socket.emit('rag:subscribe', {
  collection_id: 1
})
```

#### `rag:unsubscribe`

End subscription.

```javascript
socket.emit('rag:unsubscribe', {
  collection_id: 1
})
```

### Events (Server → Client)

#### `document:progress`

Progress of document processing.

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

Document successfully indexed.

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

Collection statistics updated.

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

## Collab namespace (`/collab`)

For LaTeX and Markdown real-time collaboration (YJS).

### Events (Client → Server)

#### `collab:join`

Join a workspace.

```javascript
socket.emit('collab:join', {
  workspace_id: 1,
  document_id: 5,
  type: 'latex'  // 'latex' | 'markdown'
})
```

#### `collab:sync`

Send YJS sync update.

```javascript
socket.emit('collab:sync', {
  document_id: 5,
  update: '<base64-encoded-yjs-update>'
})
```

#### `collab:awareness`

Awareness update (cursor position, etc.).

```javascript
socket.emit('collab:awareness', {
  document_id: 5,
  state: {
    cursor: { line: 10, ch: 5 },
    user: { name: 'Philipp', color: '#b0ca97' }
  }
})
```

### Events (Server → Client)

#### `collab:sync`

Receive YJS updates from other users.

```javascript
socket.on('collab:sync', (data) => {
  // data = { update: '<base64>' }
})
```

#### `collab:awareness`

Receive awareness updates.

```javascript
socket.on('collab:awareness', (data) => {
  // data = { users: [...], cursors: [...] }
})
```

---

## Judge namespace (`/judge`)

### Events (Client → Server)

#### `judge:subscribe`

Subscribe to session updates.

```javascript
socket.emit('judge:subscribe', {
  session_id: 1
})
```

### Events (Server → Client)

#### `judge:progress`

Progress of the judge session.

```javascript
socket.on('judge:progress', (data) => {
  // data = {
  //   session_id: 1,
  //   completed: 25,
  //   total: 100,
  //   current_comparison: {
  //     thread_id: 5,
  //     pillar: 'Relevance'
  //   }
  // }
})
```

#### `judge:result`

Single comparison result.

```javascript
socket.on('judge:result', (data) => {
  // data = {
  //   session_id: 1,
  //   comparison_id: 42,
  //   winner: 'A',
  //   confidence: 0.85,
  //   pillar: 'Relevance'
  // }
})
```

#### `judge:completed`

Session completed.

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

## Admin namespace (`/admin`)

!!! warning "Admins only"
    This namespace requires admin permissions.

### Docker monitor

#### `docker:subscribe`

Subscribe to Docker updates.

```javascript
socket.emit('docker:subscribe')
```

#### `docker:stats` (Server → Client)

Container statistics.

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

Subscribe to container logs.

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

### DB explorer

#### `db:list_tables`

List all tables.

```javascript
socket.emit('db:list_tables')

socket.on('db:tables', (data) => {
  // data = { tables: ['users', 'chatbots', 'rag_documents', ...] }
})
```

#### `db:query`

Query a table.

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

## OnCoCo namespace (`/oncoco`)

### Events

#### `oncoco:analyze`

Start analysis.

```javascript
socket.emit('oncoco:analyze', {
  text: 'Conversation text...',
  options: { detailed: true }
})
```

#### `oncoco:result`

Analysis result.

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

## Error handling

### Reconnection

Socket.IO automatically reconnects after disconnect:

```javascript
socket.on('reconnect', (attemptNumber) => {
  console.log('Reconnected after', attemptNumber, 'attempts')
  // Re-subscribe to rooms/namespaces
})

socket.on('reconnect_error', (error) => {
  console.error('Reconnection failed:', error)
})
```

### Error events

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

## Best practices

### 1. Namespace separation

```javascript
const chatSocket = io('/chat', { auth: { token } })
const ragSocket = io('/rag', { auth: { token } })
```

### 2. Cleanup on unmount

```javascript
onUnmounted(() => {
  socket.emit('collab:leave', { document_id })
  socket.disconnect()
})
```

### 3. Exponential backoff

```javascript
socket.io.on('reconnect_attempt', (attempt) => {
  socket.io.opts.reconnectionDelay = Math.min(1000 * Math.pow(2, attempt), 30000)
})
```
