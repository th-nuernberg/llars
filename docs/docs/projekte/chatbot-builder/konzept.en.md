# Chatbot Builder with Web Crawler RAG Pipeline - Concept

!!! success "Status: Implemented (as of February 2026)"
    The Chatbot Builder is production-ready and replaces the former `chatbot-rag` concept.
    This document is a living spec. It summarizes the current architecture and API.

**Created:** 2025-11-28  
**Author:** Claude (AI Assistant)  
**Version:** 2.1 (reviewed, updated to implementation)

---

## Goal

An **integrated chatbot builder** with a seamless web‑crawler RAG pipeline. Users can create a fully configured chatbot from a website in a few steps. AI‑assisted generation of system prompts, welcome messages, names, icons, and colors accelerates configuration.

**Core flow:**
```
Enter URL → Crawl → Embed → Configure → Test → Publish
```

---

## Requirements (Summary)

### Functional

- Crawl a URL and store each page as a document
- Hash‑based de‑duplication with n:m collection ↔ documents
- Live embedding progress per collection (Socket.IO)
- Wizard workflow integrated into chatbot creation
- Generate buttons for key fields (name, prompt, welcome, icon, color)
- Admin test dialog for tweaking and testing
- Pause/cancel/resume build pipeline

### Non‑functional

- Real‑time progress without polling
- Robust WebSocket reconnection
- Consistent API structure under `/api/chatbots/*`
- Backward compatibility with existing chatbot/RAG functionality

---

## Database Design (Implemented)

### Tables / Relations

```
rag_documents ↔ rag_document_chunks
rag_collections ↔ collection_document_links ↔ rag_documents
rag_collections ↔ collection_embeddings
chatbots ↔ chatbot_collections
```

### Key fields

- `rag_document_chunks`: `embedding_model`, `embedding_dimensions`, `embedding_status`, `embedding_error`
- `rag_collections`: `source_type`, `source_url`, `crawl_job_id`, `embedding_status`, `embedding_progress`, `embedding_error`
- `chatbots`: `build_status`, `build_error`, `source_url`, `primary_collection_id`
- `collection_embeddings`: multi‑model embedding tracking per collection

---

## API Design (Current)

### Wizard lifecycle

- `POST /api/chatbots/wizard`  
  Starts the wizard and creates a draft chatbot.  
  Request: `{ "url": "...", "crawler_config": { "max_pages": 50, "max_depth": 3, "use_playwright": true, "use_vision_llm": false, "take_screenshots": true } }`

- `POST /api/chatbots/<id>/wizard/crawl`  
  Starts crawl + embedding pipeline.

- `GET /api/chatbots/<id>/wizard/status`  
  Returns wizard session + progress (Redis‑first, DB fallback).

- `POST /api/chatbots/<id>/wizard/finalize`  
  Finalizes config and marks chatbot as ready.

- `POST /api/chatbots/<id>/wizard/generate-field`  
  Field generation. Supports non‑streaming JSON or SSE streaming (`stream: true`).

- `POST /api/chatbots/<id>/cancel-build`  
  Cancel build process.

- `POST /api/chatbots/<id>/resume-build`  
  Resume a paused build.

- `GET /api/chatbots/<id>/admin-test`  
  Admin test data for dialog.

- `PATCH /api/chatbots/<id>/tweak`  
  Quick updates (temperature, rag_k, prompt, etc.).

### RAG embedding endpoints

- `POST /api/rag/collections/<id>/embed`  
  Start collection embedding.

- `GET /api/rag/collections/<id>/embed/status`  
  Embedding status.

- `DELETE /api/rag/collections/<id>/embed`  
  Pause/stop embedding.

### Crawler endpoints

- `POST /api/crawler/start`  
  Start background crawl with live updates.

---

## Wizard Steps (UI)

1. **URL + crawler config**  
2. **Crawling progress**  
3. **Embedding progress**  
4. **Configuration** (AI‑generated fields)  
5. **Review/Test**

---

## Socket.IO Events

- Wizard: `wizard:state`, `wizard:progress`, `wizard:status_changed`, `wizard:elapsed_time`, `wizard:error`
- Crawler: `crawler:progress`, `crawler:status`, `crawler:page_crawled`, `crawler:complete`, `crawler:error`
- RAG: `rag:collection_status`, `rag:collection_progress`, `rag:collection_completed`, `rag:collection_error`

---

## Permissions

| Permission | Description |
|------------|-------------|
| `feature:chatbots:view` | View and use chatbots |
| `feature:chatbots:edit` | Create/edit chatbots, use wizard |
| `feature:chatbots:delete` | Delete chatbots |
| `feature:rag:view` | View collections/documents |
| `feature:rag:edit` | Create collections, start crawler |
| `feature:rag:delete` | Delete collections/documents |

---

## Validation (Key Rules)

- URL must be valid and reachable; no localhost/intranet
- Collection name: `^[a-z0-9-]+$`, max 255, unique
- Chatbot name: `^[a-z0-9-]+$`, max 100, unique
- System prompt: 10–10,000 chars
- Temperature: 0.0–2.0
- Max pages: 1–500, max depth: 1–10

---

## Rate Limiting

LLARS uses a global Flask‑Limiter:

- Development: `10000/day`, `1000/hour`
- Production: `200/day`, `50/hour`

Wizard endpoints and crawler job status endpoints are exempt.

---

## Migration Notes (Summary)

Existing data is compatible. New fields are additive; existing chatbots default to `build_status=ready`.

---

## Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Should field generation use crawled context? | Yes |
| What about >500 pages? | Hard limit at 500, warning at >200 |
| Preview before embedding? | No, too complex at MVP |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-11-28 | Initial concept |
| 2.1 | 2025-11-28 | Review updates, schema + API |
