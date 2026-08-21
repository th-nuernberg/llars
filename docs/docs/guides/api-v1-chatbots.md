# LLARS v1 Chatbot API

**Version:** 1.0 | **Stand:** Mai 2026

Programmatische REST-API zum Anlegen, Verwalten und Befragen von Chatbots — inklusive
Wizard-Quickbuild, das aus einer URL einen vollständigen RAG-Chatbot in einem POST
erstellt. Alle Endpunkte liegen unter `/api/v1/chatbots*` bzw. `/api/v1/chatbot-wizard*`.

## Authentifizierung

Identisch zur Scenario-API: `X-API-Key` (persönlich oder System) **oder** OAuth Bearer.
Siehe [v1 Scenario API](api-v1-scenarios.md#authentifizierung).

## Scopes

API-Keys können auf eine der folgenden Scope-Listen eingeschränkt werden:

| Scope | Erlaubt | RBAC-Fallback (für OAuth) |
|---|---|---|
| `chatbot:read` | `GET /api/v1/chatbots*`, `GET /api/v1/chatbot-wizard/*` | `feature:chatbots:view` |
| `chatbot:write` | `POST` / `PATCH` / `DELETE` / `PUT` auf `/api/v1/chatbots*` und `/api/v1/chatbot-wizard*` | `feature:chatbots:edit`, `feature:chatbots:delete` |
| `admin:*` | Überschreibt alles | `admin:permissions:manage` |

Chatbot-Scopes sind strikt von `scenario:*` getrennt — ein nur für Studien
gedachter Key kann keine Bots verwalten.

## CRUD-Endpunkte

| Methode | Pfad | Scope | Zweck |
|---|---|---|---|
| `GET` | `/api/v1/chatbots` | `chatbot:read` | Liste sichtbarer Chatbots (paginiert) |
| `POST` | `/api/v1/chatbots` | `chatbot:write` | One-Shot-Create (manuell **oder** mit `wizard.crawl_url` für Auto-Crawl) |
| `GET` | `/api/v1/chatbots/{id}` | `chatbot:read` | Einzelnen Chatbot lesen |
| `PATCH` | `/api/v1/chatbots/{id}` | `chatbot:write` | Vollständiges Update (alle Felder optional) |
| `PATCH` | `/api/v1/chatbots/{id}/tweak` | `chatbot:write` | Quick-Edit (`system_prompt`, `temperature`, `model_name`, `rag_*`) |
| `DELETE` | `/api/v1/chatbots/{id}` | `chatbot:write` | Hart löschen |
| `POST` | `/api/v1/chatbots/{id}/duplicate` | `chatbot:write` | Klonen |

## Sub-Resourcen

### Collections (RAG)

| Methode | Pfad | Scope |
|---|---|---|
| `GET` | `/api/v1/chatbots/{id}/collections` | `chatbot:read` |
| `POST` | `/api/v1/chatbots/{id}/collections` | `chatbot:write` |
| `PATCH` | `/api/v1/chatbots/{id}/collections/{coll_id}` | `chatbot:write` |
| `DELETE` | `/api/v1/chatbots/{id}/collections/{coll_id}` | `chatbot:write` |

### Access (Allowlist)

| Methode | Pfad | Scope |
|---|---|---|
| `GET` | `/api/v1/chatbots/{id}/access` | `chatbot:read` |
| `PUT` | `/api/v1/chatbots/{id}/access` | `chatbot:write` |

`allowed_roles` ist regex-restricted auf `evaluator`, `assessor`, `viewer`,
`researcher`, `chatbot_manager`. Privilegierte Rollen wie `admin` werden mit
**400** abgelehnt.

### Konversationen + Messages (read-only für Analytics)

| Methode | Pfad | Scope |
|---|---|---|
| `GET` | `/api/v1/chatbots/{id}/conversations` | `chatbot:read` |
| `GET` | `/api/v1/chatbots/{id}/conversations/{conv_id}` | `chatbot:read` |
| `GET` | `/api/v1/chatbots/{id}/conversations/{conv_id}/messages?include_rag=false` | `chatbot:read` |

### Chat

| Methode | Pfad | Scope | Zweck |
|---|---|---|---|
| `GET` | `/api/v1/chatbots/{id}/capabilities` | `chatbot:read` | Vision-/RAG-Support, akzeptierte File-Typen |
| `POST` | `/api/v1/chatbots/{id}/chat` | `chatbot:write` | Message senden; mit `"stream": true` als Server-Sent Events |

## Wizard

### One-Shot-Quickbuild

Eine URL rein → fertiger Chatbot raus (Crawl + Embedding asynchron im Hintergrund).

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

Antwort (`201 Created`):

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

Polling auf `polling_url` bis `build_status: "ready"`.

`auto_finalize: true` bedeutet, dass im Backend ein Daemon-Thread läuft, der nach Abschluss von Crawl + Embedding automatisch `generate-field('all')` und `finalize` ausführt. Du musst nichts tun außer pollen. In dem extrem seltenen Fall, dass der Thread nicht gestartet werden konnte (`auto_finalize: false`), musst du die letzten beiden Schritte selber via Multi-Step-Endpoints anstoßen.

### Multi-Step-Sessions

| Methode | Pfad | Scope | Schritt |
|---|---|---|---|
| `POST` | `/api/v1/chatbot-wizard/sessions` | `chatbot:write` | 1) Stub-Bot anlegen |
| `POST` | `/api/v1/chatbot-wizard/sessions/{id}/crawl` | `chatbot:write` | 2) Crawl starten |
| `POST` | `/api/v1/chatbot-wizard/sessions/{id}/generate-field` | `chatbot:write` | 3) LLM generiert Felder (`name` / `system_prompt` / `welcome_message` / `all`); `stream=true` für SSE |
| `POST` | `/api/v1/chatbot-wizard/sessions/{id}/finalize` | `chatbot:write` | 4) `build_status='ready'` setzen |
| `GET` | `/api/v1/chatbot-wizard/sessions/{id}` | `chatbot:read` | Status |
| `GET` | `/api/v1/chatbot-wizard/sessions/{id}/status` | `chatbot:read` | Polling-freundlicher Alias |
| `DELETE` | `/api/v1/chatbot-wizard/sessions/{id}` | `chatbot:write` | Abbrechen + draft-Bot löschen |

## Curl-Quickref

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
  -d '{"message":"Was kostet ein Premium-Abo?"}' \
  https://llars/api/v1/chatbots/17/chat

# Chat (SSE stream)
curl -N -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"message":"Was kostet ein Premium-Abo?","stream":true}' \
  https://llars/api/v1/chatbots/17/chat
```

## Sicherheit / Hardening

Alle Hardening-Patterns aus dem Scenario-Surface kommen mit:

- **Privilege-Escalation-Block** (C1): `access.allowed_roles` regex-restricted
- **Slug-Squat-Style-Block** (C2): Mutationen verlangen `user_can_manage_chatbot`
- **DoS-Cap** (H1): `collections` ≤ 20, `allowed_usernames` ≤ 200
- **IDOR-Maskierung** (M1): Non-Owner auf fremdem Chatbot bekommt 404 (nicht 409),
  also keine ID-Existenz-Lecks

## Out-of-Scope

- File-Uploads im API-Chat (multipart/form-data) — bleibt der Browser-/Socket.IO-API
  überlassen. Programmatische Clients schicken Text-only.
- Embedding-/Crawl-Re-Index ohne kompletten Wizard-Lauf
- WebSocket-Stream (nur SSE über `stream=true`)
