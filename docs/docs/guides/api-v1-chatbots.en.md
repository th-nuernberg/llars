# LLARS v1 Chatbot API

**Version:** 1.0 | **Last updated:** May 2026

Programmatic REST API to create, manage, and query chatbots — including a
wizard quickbuild that turns a URL into a full RAG chatbot in a single POST.
All endpoints live under `/api/v1/chatbots*` and `/api/v1/chatbot-wizard*`.

## Authentication

Identical to the Scenario API: `X-API-Key` (personal or system) **or** OAuth
bearer. See [v1 Scenario API](api-v1-scenarios.en.md#authentication).

## Scopes

| Scope | Allows | RBAC fallback (OAuth) |
|---|---|---|
| `chatbot:read` | `GET /api/v1/chatbots*`, `GET /api/v1/chatbot-wizard/*` | `feature:chatbots:view` |
| `chatbot:write` | `POST` / `PATCH` / `DELETE` / `PUT` on `/api/v1/chatbots*` and `/api/v1/chatbot-wizard*` | `feature:chatbots:edit`, `feature:chatbots:delete` |
| `admin:*` | Overrides everything | `admin:permissions:manage` |

Chatbot scopes are deliberately separate from `scenario:*` — a study-only key
cannot manage bots.

## CRUD endpoints

| Method | Path | Scope | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/chatbots` | `chatbot:read` | List visible chatbots (paginated) |
| `POST` | `/api/v1/chatbots` | `chatbot:write` | One-shot create (manual **or** with `wizard.crawl_url` for auto-crawl) |
| `GET` | `/api/v1/chatbots/{id}` | `chatbot:read` | Read a single chatbot |
| `PATCH` | `/api/v1/chatbots/{id}` | `chatbot:write` | Full partial update |
| `PATCH` | `/api/v1/chatbots/{id}/tweak` | `chatbot:write` | Quick edit (`system_prompt`, `temperature`, `model_name`, `rag_*`) |
| `DELETE` | `/api/v1/chatbots/{id}` | `chatbot:write` | Hard delete |
| `POST` | `/api/v1/chatbots/{id}/duplicate` | `chatbot:write` | Clone |

## Sub-resources

### Collections (RAG)

| Method | Path | Scope |
|---|---|---|
| `GET` | `/api/v1/chatbots/{id}/collections` | `chatbot:read` |
| `POST` | `/api/v1/chatbots/{id}/collections` | `chatbot:write` |
| `PATCH` | `/api/v1/chatbots/{id}/collections/{coll_id}` | `chatbot:write` |
| `DELETE` | `/api/v1/chatbots/{id}/collections/{coll_id}` | `chatbot:write` |

### Access (allowlist)

| Method | Path | Scope |
|---|---|---|
| `GET` | `/api/v1/chatbots/{id}/access` | `chatbot:read` |
| `PUT` | `/api/v1/chatbots/{id}/access` | `chatbot:write` |

`allowed_roles` is regex-restricted to `evaluator`, `assessor`, `viewer`,
`researcher`, `chatbot_manager`. Privileged roles like `admin` are rejected
with **400**.

### Conversations + messages (read-only for analytics)

| Method | Path | Scope |
|---|---|---|
| `GET` | `/api/v1/chatbots/{id}/conversations` | `chatbot:read` |
| `GET` | `/api/v1/chatbots/{id}/conversations/{conv_id}` | `chatbot:read` |
| `GET` | `/api/v1/chatbots/{id}/conversations/{conv_id}/messages?include_rag=false` | `chatbot:read` |

### Chat

| Method | Path | Scope | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/chatbots/{id}/capabilities` | `chatbot:read` | Vision / RAG / accepted file types |
| `POST` | `/api/v1/chatbots/{id}/chat` | `chatbot:write` | Send a message; `"stream": true` for Server-Sent Events |

## Wizard

### Quickbuild (one-shot)

A URL goes in → a fully built chatbot comes out (crawl + embed run async).

```bash
curl -X POST https://llars.example.org/api/v1/chatbot-wizard/quickbuild \
  -H "X-API-Key: $LLARS_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "crawl": {
      "crawl_url": "https://example.com/help",
      "max_pages": 50,
      "max_depth": 3
    },
    "model_name": "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506",
    "access": {"is_public": false, "allowed_roles": ["evaluator"]}
  }'
```

Response (`201 Created`):

```json
{
  "success": true,
  "chatbot_id": 17,
  "session_id": 17,
  "build_status": "crawling",
  "job_id": "crawl-9f3a..",
  "polling_url": "/api/v1/chatbot-wizard/sessions/17/status",
  "auto_finalize": true
}
```

Poll `polling_url` until `build_status: "ready"`.

`auto_finalize: true` means the backend spawned a daemon thread that runs `generate-field('all')` + `finalize` automatically once crawl + embedding finish. You only need to poll. In the rare case the thread fails to start (`auto_finalize: false`), drive the final two steps yourself via the multi-step endpoints.

### Multi-step sessions

| Method | Path | Scope | Step |
|---|---|---|---|
| `POST` | `/api/v1/chatbot-wizard/sessions` | `chatbot:write` | 1) Create stub bot |
| `POST` | `/api/v1/chatbot-wizard/sessions/{id}/crawl` | `chatbot:write` | 2) Start crawl |
| `POST` | `/api/v1/chatbot-wizard/sessions/{id}/generate-field` | `chatbot:write` | 3) LLM-generate fields (`name` / `system_prompt` / `welcome_message` / `all`); `stream=true` for SSE |
| `POST` | `/api/v1/chatbot-wizard/sessions/{id}/finalize` | `chatbot:write` | 4) Set `build_status='ready'` |
| `GET` | `/api/v1/chatbot-wizard/sessions/{id}` | `chatbot:read` | Status |
| `GET` | `/api/v1/chatbot-wizard/sessions/{id}/status` | `chatbot:read` | Polling-friendly alias |
| `DELETE` | `/api/v1/chatbot-wizard/sessions/{id}` | `chatbot:write` | Cancel + delete draft bot |

## Curl quickref

```bash
# List
curl -H "X-API-Key: $K" https://llars/api/v1/chatbots?limit=20

# Create (manual, no crawl)
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"name":"helpdesk","display_name":"Helpdesk","system_prompt":"You answer support questions."}' \
  https://llars/api/v1/chatbots

# Tweak temperature
curl -X PATCH -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"temperature":0.4}' https://llars/api/v1/chatbots/17/tweak

# Chat (non-stream)
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"message":"What does the premium plan cost?"}' \
  https://llars/api/v1/chatbots/17/chat

# Chat (SSE stream)
curl -N -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"message":"What does the premium plan cost?","stream":true}' \
  https://llars/api/v1/chatbots/17/chat
```

## Security / hardening

All hardening patterns from the scenario surface come along:

- **Privilege escalation block** (C1): `access.allowed_roles` regex-restricted
- **Slug-squat-style block** (C2): mutations require `user_can_manage_chatbot`
- **DoS cap** (H1): `collections` ≤ 20, `allowed_usernames` ≤ 200
- **IDOR masking** (M1): non-owners on a foreign chatbot get a 404 (not 409),
  so the route does not leak ID existence

## Out-of-scope

- File uploads in the API chat (multipart/form-data) — left to the browser /
  Socket.IO surface. Programmatic clients send text-only.
- Embedding / crawl re-index without a full wizard run
- WebSocket streaming (only SSE via `stream=true`)
