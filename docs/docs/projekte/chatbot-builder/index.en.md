# Chatbot Builder with Web Crawler RAG Pipeline

!!! success "Status: Implemented (as of February 2026)"
    The Chatbot Builder is production-ready and replaces the former `chatbot-rag` concept.
    The wizard guides you through 5 steps from URL → Crawl → Embedding → Configuration → Review.

## Overview

An **integrated chatbot builder** that connects web crawling, RAG embeddings, and chatbot configuration. Users can create a website-based chatbot in just a few steps.

**Core idea:**
```
Enter URL → Crawl → Embed → Configure → Test → Publish
```

## Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [Concept](konzept.md) | Technical spec (DB, API, Frontend) | Updated |
| [Hybrid Search](hybrid-search.md) | Current search stack (standard + agent tools) | Implemented |
| [Chatbot Wizard](../../guides/chatbot-wizard.md) | Step-by-step guide | Current |

## Implemented Features

- 5-step wizard: URL → Crawl → Embedding → Config → Review
- Web crawler with Playwright option, screenshots, optional Vision LLM
- Hash-based de-duplication + n:m collection ↔ documents
- Collection embedding progress via Socket.IO
- Field generation (name, display name, prompt, welcome, icon, color)
- Pause/Resume/Cancel of the build pipeline
- Admin test dialog in the Chatbot Manager

## Open Items

- Sitemap.xml discovery in the crawler (planned)
- Multi-collection selection in the wizard (currently post-creation via Chatbot Manager)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Chatbot Builder Wizard                         │
│   [URL] → [Crawl] → [Embedding] → [Config] → [Review/Test]        │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend APIs                              │
├─────────────────────────────────────────────────────────────────┤
│  /api/chatbots/wizard/*  /api/chatbots/*  /api/rag/*  /api/crawler/* │
│  Socket.IO Events: wizard:*  crawler:*  rag:*                      │
└─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database (MariaDB)                          │
├─────────────────────────────────────────────────────────────────┤
│  rag_documents ↔ rag_document_chunks                             │
│  rag_collections ↔ collection_document_links ↔ rag_documents      │
│  rag_collections ↔ collection_embeddings                          │
│  chatbots ↔ chatbot_collections                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Status (Short)

- DB extensions for build status and embedding tracking: done
- Wizard backend + Socket.IO progress: done
- Wizard frontend incl. resume: done
- Admin test dialog: done

## Differences to the old chatbot-rag concept

| Aspect | Old (chatbot-rag) | New (chatbot-builder) |
|--------|------------------|-----------------------|
| Focus | Separate chatbot + RAG management | Integrated builder workflow |
| Crawler | Manual start | Integrated into the wizard |
| Embedding progress | Not visible | Live via Socket.IO |
| Configuration | Manual fields | AI-assisted generation |
| Test page | Simple test dialog | Admin test dialog |
| Documents | Simple reference | Hash de-duplication + n:m |
