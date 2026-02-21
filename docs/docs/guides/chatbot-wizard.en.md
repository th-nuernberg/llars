# Chatbot Wizard

**Version:** 1.1 | **Date:** January 2026

The Chatbot Wizard is a 5‑step assistant for creating RAG‑based chatbots. It automatically crawls websites, creates vector embeddings, and AI‑generates names, icons, and system prompts.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Chatbot Wizard                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1      Step 2      Step 3      Step 4      Step 5                     │
│  [URL]    → [Crawling] → [Embedding] → [Config] → [Review]                  │
│    ●             ○              ○            ○         ○                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Step | Description |
|------|-------------|
| 1. Enter URL | Website address and crawler options |
| 2. Crawling | Automatic collection of website content |
| 3. Embedding | Create vector embeddings for RAG |
| 4. Configuration | Adjust name, system prompt, icon |
| 5. Finish | Review and activate chatbot |

---

## Quick Start

!!! tip "Create a chatbot in 5 minutes"
    1. **Enter URL** → e.g. `https://docs.example.com`
    2. **Start crawling** → wait until completed
    3. **Embedding** → runs automatically in background
    4. **Review config** → adjust AI‑generated fields
    5. **Finish** → chatbot is ready

---

## Step 1: Enter URL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Website URL                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  URL: [https://docs.example.com_______________________________]            │
│                                                                             │
│  Crawler settings:                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Max pages:        [50________]                                      │  │
│  │  Max depth:        [3_________]                                      │  │
│  │                                                                      │  │
│  │  ☑ Execute JavaScript (Playwright)                                   │  │
│  │  ☑ Create screenshots                                               │  │
│  │  ☐ Vision LLM for image analysis                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                                    [Next →]                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Crawler Options

| Option | Description | Default |
|--------|-------------|---------|
| **Max pages** | Maximum number of pages to crawl | 50 |
| **Max depth** | Link recursion depth | 3 |
| **Playwright** | JavaScript rendering for dynamic pages | On |
| **Screenshots** | Page images for vision analysis | On |
| **Vision LLM** | AI‑assisted image analysis | Off |

!!! info "URL Format"
    URLs are auto‑corrected: `example.com` → `https://example.com`

---

## Step 2: Crawling

The crawler collects content from the website:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Crawling...                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ████████████████████████░░░░░░░░░░  65%                                   │
│                                                                             │
│  Phase: Exploration → Crawling                                              │
│  Pages: 056/087                                                             │
│  Documents (Embeddings): 0048/0048                                          │
│  Media (Images/Screenshots): 0120/0234                                      │
│  Runtime: 03m 12s                                                           │
│                                                                             │
│  Recently processed:                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ✓ /mkdocs/getting-started                                             │  │
│  │  ✓ /mkdocs/api-reference                                               │  │
│  │  🔄 /mkdocs/tutorials/basics                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Crawling Phases

| Phase | Description |
|-------|-------------|
| **Exploration** | Build link graph / sitemap |
| **Crawling** | Download and process pages |

!!! warning "Real‑time updates"
    Progress is updated live via Socket.IO (wizard/crawler/RAG).
    If the connection drops, the wizard can be resumed.

---

## Step 3: Embedding

After crawling, vector embeddings are created:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Creating embeddings...                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ████████████████████░░░░░░░░░░░░░░  52%                                   │
│                                                                             │
│  Documents: 48                                                              │
│  Chunks created: 234                                                        │
│  Chunks processed: 122                                                      │
│                                                                             │
│  Embedding model: llamaindex/vdr-2b-multi-v1                               │
│  Dimensions: 1024                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Embedding Process

1. **Chunking**: Documents are split into smaller sections
2. **Embedding**: Each chunk is converted into a vector
3. **Storage**: Vectors are stored in ChromaDB

!!! tip "Background processing"
    Embedding continues in the background. You can move to configuration
    while processing is still running.

---

## Step 4: Configuration

AI‑generated fields can be adjusted:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Configure chatbot                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  General                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Name:         [docs_assistant_______________]  [🔄 Generate]        │  │
│  │  Display name: [Docs Assistant_______________]  [🔄 Generate]        │  │
│  │  LLM Model:    [gpt-4o______________________]  [↻ Sync]              │  │
│  │  Icon:         [📚 mdi-book-open_____________]  [🔄 Generate]        │  │
│  │  Color:        [#3498db__] ████                 [🔄 Generate]        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  System Prompt                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  You are a helpful assistant for the Example documentation.          │  │
│  │  Answer questions based on the provided documents.                   │  │
│  │  If you don't know the answer, say so honestly.                      │  │
│  │                                                         [🔄 Gen.]    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Welcome message                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Hi! I'm the Docs Assistant. How can I help you with the             │  │
│  │  Example documentation?                          [🔄 Generate]       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AI‑Generated Fields

| Field | Description | AI Analysis |
|-------|-------------|------------|
| **Name** | Internal name (snake_case) | Based on URL and content |
| **Display name** | User‑friendly name | Readable brand name |
| **Icon** | MDI icon | Matched to topic |
| **Color** | HEX color | Logo/branding analysis |
| **System prompt** | Behavior definition | RAG‑optimized prompt |
| **Welcome** | Greeting | Context‑aware |

!!! info "Regenerate fields"
    Click 🔄 to regenerate a field. Text fields are streamed.

**Note:** The **LLM model** is selected manually (with sync button).

### Icon Categories

The wizard chooses from curated icon categories:

| Category | Example icons |
|----------|---------------|
| General | robot, chat, message, assistant |
| Business | briefcase, domain, store, handshake |
| Education | school, book, graduation-cap |
| Technology | laptop, code-tags, cog, database |
| Support | help-circle, headset, phone, wrench |
| Health | hospital, medical-bag, heart-pulse |
| Finance | bank, credit-card, wallet, calculator |

---

## Step 5: Finish

Final review and activation:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Create chatbot                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Summary                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Name:           docs_assistant                                      │  │
│  │  Display name:   Docs Assistant                                      │  │
│  │  Icon:           📚 mdi-book-open                                    │  │
│  │  Color:          #3498db                                             │  │
│  │                                                                      │  │
│  │  Knowledge base:                                                     │  │
│  │  ├── 48 documents                                                   │  │
│  │  ├── 234 chunks                                                     │  │
│  │  └── Embedding: 100% ✓                                              │  │
│  │                                                                      │  │
│  │  RAG: Enabled (Top‑5 docs, Min relevance 0.3)                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                       [Test chatbot] [Finish]              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

After finishing:
- Chatbot is immediately available
- Appears in the chatbot list
- Can be used in the chat interface

---

## RAG Configuration (Advanced)

After creation, advanced RAG settings can be adjusted:

### Retrieval Settings

| Option | Description | Default |
|--------|-------------|---------|
| **RAG enabled** | Toggle RAG search | On |
| **Documents (k)** | Number of retrieved documents | 5 |
| **Min relevance** | Relevance threshold | 0.3 |
| **Include sources** | Include sources in response | On |

### Reranking (Optional)

| Option | Description |
|--------|-------------|
| **Cross‑encoder** | Rerank results with a reranker |
| **Reranker model** | Select a specific reranking model |

### Citation Settings

| Option | Description |
|--------|-------------|
| **Require citations** | Responses must cite sources |
| **Unknown answer** | Text when answer is not in sources |
| **Answer instructions** | Controls the response format |
| **Context prefix** | Heading before sources |
| **Context template** | Format of source blocks |

**Template placeholders:**
- `{{id}}` - Document ID
- `{{title}}` - Document title
- `{{excerpt}}` - Relevant excerpt
- `{{page_number}}` - Page number (PDFs)
- `{{chunk_index}}` - Chunk index
- `{{collection_name}}` - Collection name

---

## Agent Modes (Advanced)

For complex use cases, different agent modes are available:

### Standard Mode

```
Question → LLM → Answer
```
- Fastest response
- Direct RAG lookup
- For simple questions

### ACT Mode

```
Question → ACTION → OBSERVATION → Answer
```
- Tool calls possible
- For factual lookups
- 1‑2 LLM calls

### ReAct Mode

```
Question → THOUGHT → ACTION → OBSERVATION → ... → Answer
```
- Explicit reasoning
- Transparent steps
- For complex questions

### ReflAct Mode

```
Task → REFLECTION → ACTION → OBSERVATION → ... → Answer
```
- Self‑correction
- Goal‑oriented
- For multi‑step problems

---

## Resume Wizard

Interrupted wizard sessions can be resumed:

1. **Open chatbot list** → unfinished chatbots show “In progress”
2. Click **Resume wizard**
3. Server synchronizes the last state
4. Continue at the last step

!!! warning "Session timeout"
    Wizard sessions are cleaned up after long inactivity.
    Crawling progress is preserved.

---

## API Endpoints

### Wizard Lifecycle

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chatbots/wizard` | POST | Start wizard |
| `/api/chatbots/:id/wizard/crawl` | POST | Start crawling |
| `/api/chatbots/:id/wizard/generate-field` | POST | Generate field |
| `/api/chatbots/:id/wizard/status` | GET | Get status |
| `/api/chatbots/:id/wizard/finalize` | POST | Finalize wizard |
| `/api/chatbots/:id/wizard/pause` | POST | Pause wizard |
| `/api/chatbots/:id/cancel-build` | POST | Cancel wizard |
| `/api/chatbots/:id/resume-build` | POST | Resume wizard |
| `/api/chatbots/:id/admin-test` | GET | Admin test data |
| `/api/chatbots/:id/tweak` | PATCH | Save chatbot tweaks |
| `/api/chatbots/:id/wizard/collection-documents` | GET | Document preview |

### Session Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chatbots/wizard/sessions` | GET | Active sessions |
| `/api/chatbots/wizard/sessions/:id/join` | POST | Resume session |
| `/api/chatbots/wizard/sessions/:id/data` | PATCH | Update data |

---

## Socket.IO Events

### Wizard Events

| Event | Description |
|-------|-------------|
| `wizard:state` | Full session snapshot |
| `wizard:progress` | Progress update (crawl/embed) |
| `wizard:status_changed` | Status transition |
| `wizard:elapsed_time` | Server‑computed runtime |
| `wizard:error` | Error |

### Crawler Events

| Event | Description |
|-------|-------------|
| `crawler:progress` | Progress update |
| `crawler:status` | Current status |
| `crawler:page_crawled` | Page processed |
| `crawler:complete` | Crawling complete |
| `crawler:error` | Error |

### RAG Events

| Event | Description |
|-------|-------------|
| `rag:collection_status` | Current collection status |
| `rag:collection_progress` | Embedding progress |
| `rag:collection_completed` | Embedding complete |
| `rag:collection_error` | Embedding failed |
| `rag:collection_documents` | Document preview |
| `rag:document_processed` | Document processed |
| `rag:error` | Error |

---

## Permissions

| Permission | Description |
|------------|-------------|
| `feature:chatbots:edit` | Create chatbots, use wizard |
| `feature:chatbots:view` | View chatbots |
| `feature:chatbots:advanced` | Use agent modes |
| `feature:rag:share` | Share collections |

---

## FAQ

??? question "How long does crawling take?"
    Depends on number and size of pages. Typical: 1‑5 minutes for 100 pages.

??? question "Which websites can be crawled?"
    Publicly accessible sites. JavaScript‑heavy sites require Playwright.

??? question "Can I add documents later?"
    Yes, you can add documents anytime via the collection manager.

??? question "What happens on crawl errors?"
    Broken URLs are skipped. The wizard shows a summary of successful
    and failed URLs.

---

## See Also

- [Chatbot & RAG](../projekte/chatbot-builder/index.md) - Technical concept
- [RAG Pipeline](../agentic-ai/rag.md) - Retrieval‑Augmented Generation
- [Prompt Engineering](prompt-engineering.md) - Optimize system prompts
