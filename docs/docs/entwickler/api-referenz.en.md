# API Reference

This page documents selected REST API endpoints of the LLARS backend.
For the full list, see `app/routes/` and `app/routes/registry.py`.

!!! info "Base URL"
    All endpoints are relative to the base URL: `http://localhost:55080/api`

---

## Authentication

All API endpoints (except `/auth/*`) require a valid JWT token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

### Obtain a token

```http
POST /auth/login
```

Handled by the Authentik OAuth2/OIDC flow. See [Authentik Setup](../guides/authentik-setup.md).

---

## Chatbot API

### Chatbots

#### List all chatbots

```http
GET /api/chatbots
```

**Response:**
```json
{
  "success": true,
  "chatbots": [
    {
      "id": 1,
      "name": "Support Bot",
      "description": "Customer support assistant",
      "is_published": true,
      "owner_id": 1,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### Create chatbot

```http
POST /api/chatbots
Content-Type: application/json

{
  "name": "New Bot",
  "description": "Description",
  "llm_model_id": 1,
  "system_prompt": "You are a helpful assistant."
}
```

**Response:** `201 Created`

#### Chatbot details

```http
GET /api/chatbots/{id}
```

#### Update chatbot

```http
PATCH /api/chatbots/{id}
Content-Type: application/json

{
  "name": "Updated name",
  "description": "New description"
}
```

#### Delete chatbot

```http
DELETE /api/chatbots/{id}
```

---

### Chat messages

#### Send a message

```http
POST /api/chatbots/{id}/chat
Content-Type: application/json

{
  "message": "Hello, how can you help?",
  "session_id": "unique-session-id",
  "conversation_id": null,
  "include_sources": true
}
```

**Response (streaming):**
```
data: {"delta": "Hello"}
data: {"delta": "! I"}
data: {"delta": " can"}
data: {"done": true, "sources": [...], "conversation_id": 1}
```

#### Fetch conversation

```http
GET /api/chatbots/{id}/conversations/{conversation_id}
```

**Response:**
```json
{
  "success": true,
  "conversation": {
    "id": 1,
    "title": "First conversation",
    "messages": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi! How can I help?"}
    ]
  }
}
```

---

## RAG API

### Collections

#### List all collections

```http
GET /api/rag/collections
```

**Query parameters:**
- `include_stats` (bool): include chunk statistics

#### Create collection

```http
POST /api/rag/collections
Content-Type: application/json

{
  "name": "Knowledge Base",
  "description": "Documents for customer support"
}
```

#### Collection details

```http
GET /api/rag/collections/{id}
```

#### Delete collection

```http
DELETE /api/rag/collections/{id}
```

---

### Documents

#### Upload document

```http
POST /api/rag/documents
Content-Type: multipart/form-data

file: <binary>
collection_id: 1
```

**Response:**
```json
{
  "success": true,
  "document": {
    "id": 1,
    "filename": "manual.pdf",
    "status": "pending",
    "mime_type": "application/pdf"
  }
}
```

#### Document status

```http
GET /api/rag/documents/{id}
```

**Response:**
```json
{
  "success": true,
  "document": {
    "id": 1,
    "filename": "manual.pdf",
    "status": "indexed",
    "chunk_count": 45,
    "processed_at": "2025-12-01T10:05:00Z"
  }
}
```

#### Delete document

```http
DELETE /api/rag/documents/{id}
```

---

### Search

#### Semantic search

```http
POST /api/rag/search
Content-Type: application/json

{
  "query": "How do I reset my password?",
  "collection_ids": [1, 2],
  "top_k": 5,
  "include_content": true
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "document_id": 1,
      "chunk_index": 12,
      "content": "To reset your password...",
      "score": 0.89,
      "metadata": {
        "filename": "manual.pdf",
        "page_number": 5
      }
    }
  ]
}
```

---

## Judge API

### Sessions

#### List all sessions

```http
GET /api/judge/sessions
```

#### Create session

```http
POST /api/judge/sessions
Content-Type: application/json

{
  "name": "GPT-4 vs Claude comparison",
  "pillar_ids": [1, 2, 3],
  "sampling_strategy": "random",
  "sample_size": 50
}
```

#### Start session

```http
POST /api/judge/sessions/{id}/start
```

#### Pause session

```http
POST /api/judge/sessions/{id}/pause
```

#### Session statistics

```http
GET /api/judge/sessions/{id}/stats
```

---

### Pillars (evaluation criteria)

#### List all pillars

```http
GET /api/judge/pillars
```

**Response:**
```json
{
  "success": true,
  "pillars": [
    {
      "id": 1,
      "name": "Relevance",
      "description": "How relevant is the answer to the question?",
      "weight": 1.0
    }
  ]
}
```

---

## Admin API

### System settings

#### List all settings

```http
GET /api/admin/settings
```

**Permission:** `admin:settings:view`

#### Update setting

```http
PATCH /api/admin/settings/{key}
Content-Type: application/json

{
  "value": "new_value"
}
```

**Permission:** `admin:settings:edit`

---

### Analytics

#### Analytics settings

```http
GET /api/admin/analytics/settings
PATCH /api/admin/analytics/settings
```

---

### Users

#### List all users

```http
GET /api/admin/users
```

**Query parameters:**
- `page` (int): page number
- `per_page` (int): items per page
- `search` (string): search term

#### User permissions

```http
GET /api/admin/users/{id}/permissions
PATCH /api/admin/users/{id}/permissions
```

---

## User API

### Profile

#### Own profile

```http
GET /api/users/me
```

#### Update profile

```http
PATCH /api/users/me/settings
Content-Type: application/json

{
  "collab_color": "#b0ca97",
  "avatar_seed": "random-seed"
}
```

#### Upload avatar

```http
POST /api/users/me/avatar
Content-Type: multipart/form-data

file: <image>
```

---

## Error responses

### Standard error format

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": {}
  }
}
```

### HTTP status codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (no token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict |
| 500 | Internal Server Error |

---

## Rate limiting

!!! warning "In development"
    Rate limiting is not implemented yet.

Planned limits:
- 100 requests/minute for chat endpoints
- 1000 requests/minute for other endpoints

---

## WebSocket endpoints

For real-time updates, see [WebSocket API](websocket-api.md).
