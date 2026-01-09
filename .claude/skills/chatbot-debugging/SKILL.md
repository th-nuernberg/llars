---
name: chatbot-debugging
description: Debug and test LLARS chatbots. Use when testing chatbot responses, checking RAG configuration, investigating chat errors, debugging socket communication, or when user mentions chatbot issues.
---

# Chatbot Debugging for LLARS

## Quick Start

### Test a Chatbot via REST API

```bash
# 1. Get auth token (extract from Flask logs - tokens are passed via socket.io)
TOKEN=$(docker logs llars_flask_service 2>&1 | grep -o 'token=eyJ[^&]*' | tail -1 | cut -d= -f2)
echo "Token: ${TOKEN:0:50}..."

# 2. List available chatbots
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:55080/api/chatbots" | python3 -c "import sys,json; [print(f'ID {c[\"id\"]}: {c[\"name\"]} ({c[\"build_status\"]})') for c in json.load(sys.stdin).get('chatbots',[])]"

# 3. Send test message
curl -s -X POST "http://localhost:55080/api/chatbots/{CHATBOT_ID}/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hallo, was kannst du?", "session_id": "debug-session-1", "include_sources": true}' | python3 -m json.tool
```

### Test Chat via Admin Endpoint (no conversation saved)

```bash
curl -s -X POST "http://localhost:55080/api/chatbots/{CHATBOT_ID}/test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test question"}' | python3 -m json.tool
```

## Database Inspection

### Connect to MariaDB

```bash
docker exec -it llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars
```

### Check Chatbot Configuration

```sql
-- List all chatbots with config
SELECT id, name, display_name, model_name, rag_enabled, is_active, is_public, build_status
FROM chatbots ORDER BY id;

-- Check RAG settings for a chatbot
SELECT c.id, c.name, c.rag_enabled, c.rag_retrieval_k, c.rag_min_relevance,
       ps.agent_mode, ps.task_type, ps.tools_enabled
FROM chatbots c
LEFT JOIN chatbot_prompt_settings ps ON c.id = ps.chatbot_id
WHERE c.id = {CHATBOT_ID};

-- Check assigned collections
SELECT cc.chatbot_id, cc.collection_id, rc.name as collection_name,
       cc.is_primary, cc.priority, cc.weight
FROM chatbot_collections cc
JOIN rag_collections rc ON cc.collection_id = rc.id
WHERE cc.chatbot_id = {CHATBOT_ID};
```

### Check Recent Conversations

```sql
-- Recent conversations for a chatbot
SELECT c.id, c.session_id, c.username, c.message_count, c.title,
       c.started_at, c.last_message_at
FROM chatbot_conversations c
WHERE c.chatbot_id = {CHATBOT_ID}
ORDER BY c.started_at DESC LIMIT 10;

-- Messages in a conversation
SELECT id, role, LEFT(content, 100) as content_preview,
       tokens_input, tokens_output, response_time_ms, created_at
FROM chatbot_messages
WHERE conversation_id = {CONVERSATION_ID}
ORDER BY created_at;

-- Check RAG sources for a message
SELECT id, rag_sources FROM chatbot_messages WHERE id = {MESSAGE_ID};
```

### Performance Analysis

```sql
-- Slowest responses
SELECT m.id, c.chatbot_id, b.name, m.response_time_ms, m.tokens_output, m.created_at
FROM chatbot_messages m
JOIN chatbot_conversations c ON m.conversation_id = c.id
JOIN chatbots b ON c.chatbot_id = b.id
WHERE m.role = 'assistant' AND m.response_time_ms > 10000
ORDER BY m.response_time_ms DESC LIMIT 20;

-- Average response time per chatbot
SELECT c.chatbot_id, b.name,
       COUNT(*) as msg_count,
       AVG(m.response_time_ms) as avg_ms,
       MAX(m.response_time_ms) as max_ms
FROM chatbot_messages m
JOIN chatbot_conversations c ON m.conversation_id = c.id
JOIN chatbots b ON c.chatbot_id = b.id
WHERE m.role = 'assistant'
GROUP BY c.chatbot_id ORDER BY avg_ms DESC;
```

## Common Issues & Solutions

### Issue 1: "Ein Fehler ist aufgetreten" (Generic Error)

**Cause:** Backend error during chat processing

**Debug Steps:**
```bash
# Check Flask logs for the actual error
docker logs llars_flask_service --since 5m 2>&1 | grep -i -A5 "error\|exception\|traceback"

# Look for specific chatbot stream errors
docker logs llars_flask_service 2>&1 | grep -i "chatbot stream error"
```

**Common Causes:**
- LLM provider unavailable (check LiteLLM proxy)
- RAG collection has no embeddings
- Database connection issues
- Missing imports in socket handlers (see Known Bugs below)

### Issue 2: Empty Response / Fallback Message

**Symptom:** Bot returns "Ich konnte leider keine passende Antwort finden"

**Check RAG Configuration:**
```sql
-- Chatbot has RAG enabled?
SELECT rag_enabled, rag_retrieval_k, rag_min_relevance FROM chatbots WHERE id = {ID};

-- Collections assigned?
SELECT COUNT(*) FROM chatbot_collections WHERE chatbot_id = {ID};

-- Collection has documents?
SELECT rc.id, rc.name, COUNT(rdc.id) as chunk_count
FROM rag_collections rc
JOIN chatbot_collections cc ON rc.id = cc.collection_id
LEFT JOIN rag_document_chunks rdc ON rc.id = rdc.collection_id
WHERE cc.chatbot_id = {ID}
GROUP BY rc.id;
```

**Solution:**
1. Verify collection has embeddings
2. Lower `rag_min_relevance` (default 0.05)
3. Increase `rag_retrieval_k` (default 8)

### Issue 3: Socket Connection Errors

**Symptom:** Frontend shows "Connection lost" or chat doesn't stream

**Check Socket.IO:**
```bash
# Check socket handler logs
docker logs llars_flask_service 2>&1 | grep -i socket

# Verify socket endpoint
curl -s "http://localhost:55080/socket.io/?EIO=4&transport=polling"
```

**Common Causes:**
- Token not sent in socket event
- Token expired
- CORS issues (check ALLOWED_ORIGINS)

### Issue 4: Authentication Errors

**Symptom:** `chatbot:error {error: "Authentication required"}`

**Debug:**
```bash
# Verify token is valid
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:55080/api/auth/verify" | python3 -m json.tool
```

**Fix:** Ensure frontend sends `token` parameter in `chatbot:stream` event

### Issue 5: Access Denied to Chatbot

**Symptom:** Chatbot not visible or "Access denied"

**Check Access:**
```sql
-- Is chatbot active and public?
SELECT is_active, is_public, allowed_roles, created_by FROM chatbots WHERE id = {ID};

-- User in allowlist?
SELECT * FROM chatbot_user_access WHERE chatbot_id = {ID} AND username = '{USERNAME}';
```

**Solution:**
- Make public: `UPDATE chatbots SET is_public=1 WHERE id={ID};`
- Or add user: `INSERT INTO chatbot_user_access (chatbot_id, username, granted_at) VALUES ({ID}, '{USER}', NOW());`

### Issue 6: LLM Provider Errors

**Symptom:** Timeout or model not found

**Check LiteLLM Proxy:**
```bash
# Check proxy health
curl -s "http://localhost:55085/health" | python3 -m json.tool

# Check proxy logs
docker logs llars_litellm_proxy --since 5m

# List available models
curl -s "http://localhost:55085/v1/models" | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin).get('data',[])]"
```

**Check Provider Config:**
```sql
SELECT id, name, api_type, base_url, is_active, is_default FROM llm_providers;
SELECT model_name, provider_id FROM llm_models WHERE model_name LIKE '%{MODEL}%';
```

## Service Logs

```bash
# All chatbot-related logs
docker logs llars_flask_service 2>&1 | grep -i chatbot

# Socket events
docker logs llars_flask_service 2>&1 | grep -i "chatbot:stream\|chatbot:response\|chatbot:error"

# RAG retrieval
docker logs llars_flask_service 2>&1 | grep -i "rag\|retrieval\|embedding"

# Agent mode
docker logs llars_flask_service 2>&1 | grep -i "agent\|react\|reflact"
```

## Key Files

| File | Purpose |
|------|---------|
| `app/db/models/chatbot.py` | Database models |
| `app/routes/chatbot/chatbot_chat_routes.py` | REST chat endpoints |
| `app/socketio_handlers/events_chatbot.py` | WebSocket streaming |
| `app/services/chatbot/chat_service.py` | Main chat orchestration |
| `app/services/chatbot/agent_chat_service.py` | Agent reasoning modes |
| `app/services/chatbot/chat_rag_retrieval.py` | RAG/vector search |
| `app/services/chatbot/chatbot_access_service.py` | Access control |

## Socket Event Reference

### Client -> Server

```javascript
// Join chat room
emit('chatbot:join', { session_id: 'session-123' })

// Send message (streaming)
emit('chatbot:stream', {
  chatbot_id: 123,
  message: "User question",
  session_id: "session-123",
  token: "jwt-token",           // REQUIRED
  conversation_id: 456          // optional, to continue
})
```

### Server -> Client

```javascript
// RAG sources found
on('chatbot:sources', { sources: [{footnote_id, title, excerpt, url}] })

// Response chunk (streaming)
on('chatbot:response', { content: "text chunk", complete: false })

// Stream finished
on('chatbot:complete', { conversation_id, message_id, tokens, response_time_ms, title })

// Error occurred
on('chatbot:error', { error: "message", code: "AUTH_REQUIRED|FORBIDDEN|BOT_INACTIVE" })

// Agent mode status (ReAct/ReflAct)
on('chatbot:agent_status', { type: "thinking|thought|action|observation", ... })
```

## Agent Mode Debugging

### Check Agent Configuration

```sql
SELECT chatbot_id, agent_mode, task_type, agent_max_iterations, tools_enabled
FROM chatbot_prompt_settings WHERE chatbot_id = {ID};
```

### Agent Modes

| Mode | Description |
|------|-------------|
| standard | Single-shot response (no reasoning) |
| act | Tool calls only, no visible reasoning |
| react | THOUGHT -> ACTION -> OBSERVATION cycles |
| reflact | Goal-state reflection before actions |

### Agent Tools

| Tool | Description |
|------|-------------|
| rag_search | Semantic vector search in collections |
| lexical_search | Keyword-based search |
| web_search | Tavily API (if enabled) |
| respond | Generate final answer |

## RAG Debugging

### Test RAG Search Directly

```python
# In Flask shell: docker exec -it llars_flask_service flask shell
from services.chatbot.chat_rag_retrieval import ChatRAGRetrieval
from db.models.chatbot import Chatbot

chatbot = Chatbot.query.get(1)
retrieval = ChatRAGRetrieval(chatbot)
context, sources = retrieval.get_multi_collection_context("test query")
print(f"Found {len(sources)} sources")
for s in sources[:3]:
    print(f"  - {s['title']}: {s['excerpt'][:50]}...")
```

### Check Embedding Vectors

```sql
-- Documents with embeddings
SELECT rc.name, COUNT(rdc.id) as chunks,
       SUM(CASE WHEN rdc.embedding IS NOT NULL THEN 1 ELSE 0 END) as with_embedding
FROM rag_collections rc
LEFT JOIN rag_document_chunks rdc ON rc.id = rdc.collection_id
GROUP BY rc.id;
```

## Quick Fixes

### Reset Chatbot to Working State

```sql
-- Reactivate chatbot
UPDATE chatbots SET is_active = 1, build_status = 'ready', build_error = NULL WHERE id = {ID};

-- Clear stuck conversations
DELETE FROM chatbot_conversations WHERE chatbot_id = {ID} AND message_count = 0;
```

### Restart Services

```bash
# Restart Flask (chat service)
docker restart llars_flask_service

# Restart LiteLLM (LLM provider)
docker restart llars_litellm_proxy

# Restart ChromaDB (embeddings)
docker restart llars_chroma_service
```

## Known Bugs & Fixes

### Bug: "name 'os' is not defined" in Socket Handler (Fixed 2026-01-08)

**Symptom:**
```
ERROR - Chatbot stream error: name 'os' is not defined
  File "events_chatbot.py", line 744, in handle_chatbot_stream
  File "events_chatbot.py", line 219, in _get_rag_images_for_sources
```

**Cause:** Missing `import os` in `app/socketio_handlers/events_chatbot.py`

**Fix Applied:**
```python
# Line 24-27 in events_chatbot.py
import logging
import os          # <-- This was missing
import time
import base64
```

**After Fix:** Restart Flask service with `docker restart llars_flask_service`

### Checking Collection Embeddings

```sql
-- Verify embeddings exist (vector_id indicates embedded)
SELECT
    rc.name as collection_name,
    COUNT(rdc.id) as total_chunks,
    SUM(CASE WHEN rdc.vector_id IS NOT NULL THEN 1 ELSE 0 END) as embedded_chunks,
    ROUND(100 * SUM(CASE WHEN rdc.vector_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(rdc.id), 1) as percent_embedded
FROM rag_collections rc
JOIN rag_documents rd ON rc.id = rd.collection_id
JOIN rag_document_chunks rdc ON rd.id = rdc.document_id
GROUP BY rc.id, rc.name;
```

### Full Chat Test via curl

```bash
# Extract token from logs
TOKEN=$(docker logs llars_flask_service 2>&1 | grep -o 'token=eyJ[^&]*' | tail -1 | cut -d= -f2)

# Create conversation
CONV=$(curl -s -X POST "http://localhost:55080/api/chatbots/3/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Debug-Test"}')

CONV_ID=$(echo "$CONV" | python3 -c "import sys,json; print(json.load(sys.stdin).get('conversation',{}).get('id',''))")
SESSION_ID=$(echo "$CONV" | python3 -c "import sys,json; print(json.load(sys.stdin).get('conversation',{}).get('session_id',''))")

# Send message
curl -s -X POST "http://localhost:55080/api/chatbots/3/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Hallo, wer bist du?\", \"session_id\": \"$SESSION_ID\", \"conversation_id\": $CONV_ID, \"include_sources\": true}" | python3 -m json.tool
```
