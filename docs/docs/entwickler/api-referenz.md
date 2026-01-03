# API-Referenz

Diese Seite dokumentiert alle REST-API-Endpunkte des LLARS-Backends.

!!! info "Base URL"
    Alle Endpunkte sind relativ zur Base URL: `http://localhost:55080/api`

---

## Authentifizierung

Alle API-Endpunkte (außer `/auth/*`) erfordern einen gültigen JWT-Token im Authorization-Header:

```http
Authorization: Bearer <access_token>
```

### Token erhalten

```http
POST /auth/login
```

Wird über Authentik OAuth2/OIDC Flow gehandhabt. Siehe [Authentik Setup](../guides/authentik-setup.md).

---

## Chatbot API

### Chatbots

#### Liste aller Chatbots

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
      "description": "Kundensupport Assistent",
      "is_published": true,
      "owner_id": 1,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### Chatbot erstellen

```http
POST /api/chatbots
Content-Type: application/json

{
  "name": "Neuer Bot",
  "description": "Beschreibung",
  "llm_model_id": 1,
  "system_prompt": "Du bist ein hilfreicher Assistent."
}
```

**Response:** `201 Created`

#### Chatbot Details

```http
GET /api/chatbots/{id}
```

#### Chatbot aktualisieren

```http
PATCH /api/chatbots/{id}
Content-Type: application/json

{
  "name": "Aktualisierter Name",
  "description": "Neue Beschreibung"
}
```

#### Chatbot löschen

```http
DELETE /api/chatbots/{id}
```

---

### Chat-Nachrichten

#### Nachricht senden

```http
POST /api/chatbots/{id}/chat
Content-Type: application/json

{
  "message": "Hallo, wie kann ich dir helfen?",
  "session_id": "unique-session-id",
  "conversation_id": null,
  "include_sources": true
}
```

**Response (Streaming):**
```
data: {"delta": "Hallo"}
data: {"delta": "! Ich"}
data: {"delta": " kann"}
data: {"done": true, "sources": [...], "conversation_id": 1}
```

#### Konversation abrufen

```http
GET /api/chatbots/{id}/conversations/{conversation_id}
```

**Response:**
```json
{
  "success": true,
  "conversation": {
    "id": 1,
    "title": "Erste Unterhaltung",
    "messages": [
      {"role": "user", "content": "Hallo"},
      {"role": "assistant", "content": "Hallo! Wie kann ich helfen?"}
    ]
  }
}
```

---

## RAG API

### Collections

#### Alle Collections

```http
GET /api/rag/collections
```

**Query-Parameter:**
- `include_stats` (bool): Chunk-Statistiken einschließen

#### Collection erstellen

```http
POST /api/rag/collections
Content-Type: application/json

{
  "name": "Wissensbasis",
  "description": "Dokumente für Kundensupport"
}
```

#### Collection Details

```http
GET /api/rag/collections/{id}
```

#### Collection löschen

```http
DELETE /api/rag/collections/{id}
```

---

### Dokumente

#### Dokument hochladen

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
    "filename": "handbuch.pdf",
    "status": "pending",
    "mime_type": "application/pdf"
  }
}
```

#### Dokument-Status

```http
GET /api/rag/documents/{id}
```

**Response:**
```json
{
  "success": true,
  "document": {
    "id": 1,
    "filename": "handbuch.pdf",
    "status": "indexed",
    "chunk_count": 45,
    "processed_at": "2025-12-01T10:05:00Z"
  }
}
```

#### Dokument löschen

```http
DELETE /api/rag/documents/{id}
```

---

### Suche

#### Semantische Suche

```http
POST /api/rag/search
Content-Type: application/json

{
  "query": "Wie setze ich mein Passwort zurück?",
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
      "content": "Um Ihr Passwort zurückzusetzen...",
      "score": 0.89,
      "metadata": {
        "filename": "handbuch.pdf",
        "page_number": 5
      }
    }
  ]
}
```

---

## Judge API

### Sessions

#### Alle Sessions

```http
GET /api/judge/sessions
```

#### Session erstellen

```http
POST /api/judge/sessions
Content-Type: application/json

{
  "name": "GPT-4 vs Claude Vergleich",
  "pillar_ids": [1, 2, 3],
  "sampling_strategy": "random",
  "sample_size": 50
}
```

#### Session starten

```http
POST /api/judge/sessions/{id}/start
```

#### Session pausieren

```http
POST /api/judge/sessions/{id}/pause
```

#### Session-Statistiken

```http
GET /api/judge/sessions/{id}/stats
```

---

### Pillars (Bewertungskriterien)

#### Alle Pillars

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
      "name": "Relevanz",
      "description": "Wie relevant ist die Antwort für die Frage?",
      "weight": 1.0
    }
  ]
}
```

---

## Admin API

### System-Einstellungen

#### Alle Einstellungen

```http
GET /api/admin/settings
```

**Permission:** `admin:settings:view`

#### Einstellung aktualisieren

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

#### Analytics-Einstellungen

```http
GET /api/admin/analytics/settings
PATCH /api/admin/analytics/settings
```

---

### Benutzer

#### Alle Benutzer

```http
GET /api/admin/users
```

**Query-Parameter:**
- `page` (int): Seitennummer
- `per_page` (int): Einträge pro Seite
- `search` (string): Suchbegriff

#### Benutzer-Permissions

```http
GET /api/admin/users/{id}/permissions
PATCH /api/admin/users/{id}/permissions
```

---

## User API

### Profil

#### Eigenes Profil

```http
GET /api/users/me
```

#### Profil aktualisieren

```http
PATCH /api/users/me/settings
Content-Type: application/json

{
  "collab_color": "#b0ca97",
  "avatar_seed": "random-seed"
}
```

#### Avatar hochladen

```http
POST /api/users/me/avatar
Content-Type: multipart/form-data

file: <image>
```

---

## Error Responses

### Standard-Fehlerformat

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

### HTTP-Status-Codes

| Code | Bedeutung |
|------|-----------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request (Validierungsfehler) |
| 401 | Unauthorized (Kein Token) |
| 403 | Forbidden (Keine Berechtigung) |
| 404 | Not Found |
| 409 | Conflict |
| 500 | Internal Server Error |

---

## Rate Limiting

!!! warning "In Entwicklung"
    Rate Limiting ist aktuell nicht implementiert.

Geplante Limits:
- 100 Requests/Minute für Chat-Endpunkte
- 1000 Requests/Minute für andere Endpunkte

---

## WebSocket-Endpunkte

Für Echtzeit-Updates siehe [WebSocket API](websocket-api.md).
