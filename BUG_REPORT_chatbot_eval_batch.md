# Bug Report: Chatbot Manager, Evaluation Metrics, Test-Button & Batch Generation

**Date:** 2026-04-30
**Branch:** `fix/chatbot-eval-batch` (rebased on `main`)
**Reporter:** philipp.steigerwald via Claude Code

This report consolidates findings on five user-reported issues. The branch
has been rebased on `main` so all already-merged fixes are picked up.
Where the root cause needed live diagnosis (server logs, DB queries,
ChromaDB state) and SSH access was unavailable, this report lists the
exact commands to run next.

---

## 1. Scenario Evaluation – Krippendorff α "wrong values"

### Status: **Already fixed on `main`**

`scenario_stats_service._calculate_ranking_agreement` previously called
the binary nominal `_calculate_krippendorff_alpha`, which is hardcoded
for two categories (`real=0`, `fake=1`). For ranking buckets (`0..k`)
and Likert ratings (`1..5`), the disagreement counter only incremented
by 1 instead of `(v−v')²`, and the expected disagreement formula was
binary. Result: meaningless α values for every ranking, rating, and
mail_rating scenario.

`main` now routes through `AgreementMetricsService._krippendorff_alpha`
with `metric="ordinal"` (squared-diff), see
`app/services/scenario_stats_service.py:_calculate_ranking_agreement`
(returns at the end of the function). This is the correct Krippendorff
implementation referenced in CLAUDE.md.

### Remaining concern: bucket ordinal value derivation

`scenario_stats_service.py` builds the bucket ordinal map from the
position in `_extract_ranking_bucket_config`:

```python
for idx, b in enumerate(bucket_config):
    bucket_ordinal[b["id"]] = idx
```

This is correct **only if** `bucket_config` comes back ordered along
the rank axis (best→worst or worst→best). `_extract_ranking_bucket_config`
preserves the configured order, so as long as the scenario was created
with monotone bucket order (the wizard does this), the values are
correct. If a scenario was hand-edited and the buckets ended up in
non-monotone order, α will be wrong.

**Diagnostic SQL:**

```sql
SELECT id, name, JSON_EXTRACT(config_json, '$.buckets'),
       JSON_EXTRACT(config_json, '$.eval_config.buckets')
FROM rating_scenarios WHERE id = 176;
```

Verify the buckets array is in monotone rank order (e.g. `gut, mittel,
neutral, schlecht`, not `gut, schlecht, mittel, neutral`).

### Live-update of values

The frontend (`useScenarioStats.js`) already:
- Joins room `scenario_stats_{id}` via `scenario:subscribe`
- Listens for `scenario:stats_updated`
- Has a polling fallback for missed events (line 445)
- Re-subscribes on tab-visibility change

Backend emits via `_emit_stats_update` in
`scenario_stats_cache_service.py:281`. The plumbing is in place.

If values appear stale on `/scenarios/176?tab=evaluation`, the most
likely cause is the cache TTL serving the previous snapshot while a
recompute runs in the background. **Diagnostic:**

```bash
# On the server: tail Flask logs while a new rating is submitted.
ssh llars "docker logs -f llars_flask_service 2>&1 | grep -E 'scenario_stats|krippendorff|emit_scenario_stats'"
```

Expect to see `_emit_stats_update` followed by the frontend receiving
the event. If recompute runs but emit doesn't fire, the bug is in
`scenario_stats_cache_service._emit_stats_update`.

---

## 2. Chatbot Manager Crawler – "Session beim Crawlen geht nicht"

### Status: **Backend already fixed; verify with live test**

Two main commits cover this: `867ecdaa` (persist crawl sessions across
workers) and `ac6cc85c` (treat missing live sessions as resyncable).

Code on `main`:
- `app/services/crawler/modules/crawler_state_store.py` — Redis-backed
  shared job state.
- `crawler_service.py` instantiates `self.state_store = CrawlerStateStore()`
  and threads it through every job lifecycle helper
  (`get_job_status`, `get_all_jobs`, `cancel_job`, `update_job_started`,
  `_persist_job_state`).
- `crawler_jobs.get_job_status` does hybrid lookup: in-memory →
  Redis → DB recovery.
- Frontend wizard (`ChatbotBuilderWizard.vue:846`) detects
  `session_available === false` / `live_updates_available === false` and
  calls `resyncAfterCrawlerSessionLoss()` to recover.

This is robust on paper. If users still see "session geht nicht"
after the crawl starts, suspects in order of likelihood:

### Suspect A: SocketIO room join race

`crawler_service._run_background_crawl:387` does `time.sleep(1.5)`
before emitting `planning`. Under prod load this may be too short —
the first `crawler:progress` is emitted before the frontend has
finished `crawler:join_session`. The frontend then never sees stage
transitions. The fix would be to drop the sleep and instead replay
the latest job state on `crawler:join_session` using
`crawler_service.get_job_status(session_id)`.

### Suspect B: Redis not reachable from worker

`CrawlerStateStore.__init__` uses `services.runtime_config.get_redis_client()`.
If Redis is unhealthy or `REDIS_URL` is wrong, every `state_store.persist_job`
silently raises and the job lives only in worker-local memory again.

**Diagnostic:**

```bash
ssh llars "docker logs llars_flask_service 2>&1 | grep -iE 'CrawlerStateStore|redis|state_store' | tail -50"
ssh llars "docker exec llars_flask_service python3 -c 'from services.runtime_config import get_redis_client; r=get_redis_client(); print(r.ping(), r.smembers(\"crawler:jobs:index\"))'"
```

### Suspect C: SocketIO event not reaching browser

If the frontend joins room `crawler_{job_id}` but emits go to a
different room name, no events arrive.

**Diagnostic:** Open `/chatbot-manager`, start a small crawl,
DevTools → Network → WS frame inspection. Verify events arriving:
- `crawler:joined` with the job's `session_id`
- `crawler:progress` with same `session_id`

If only `crawler:joined` arrives, room membership and emission
disagree. Likely the backend is emitting to `crawler_{collection_id}`
or similar.

---

## 3. Chatbot answers only "Das kann ich dir leider nicht beantworten."

### Status: **Almost certainly RAG runtime issue, not a code bug**

The fallback string is `DEFAULT_RAG_UNKNOWN_ANSWER` in
`app/db/models/chatbot.py`. It is returned by `chat_service.py:194`
when `_requires_sources()` is true and `sources == []`. The chain:

1. `chat_service.chat()` calls `_get_multi_collection_context(message)`
2. → `chat_rag_retrieval.get_multi_collection_context`
3. → `search_collection` (semantic) → 0 results
4. → `_lexical_fallback_search` → 0 results
5. → returns `("", [])`, fallback fires.

`chat_rag_retrieval.py` already has multiple fallbacks:
- `get_best_embedding_for_collection` → legacy resolver →
  `sentence-transformers/all-MiniLM-L6-v2`.
- Raw ChromaDB query if LangChain throws on `page_content=None`.
- Alternate `chroma_collection_name` resolution.
- Lexical fallback over `collection_chunks` if semantic returns 0.

So the runtime problem is one of:

1. **Embedding mismatch** — collection 64's docs were embedded with
   model X, but X is unavailable on the prod runtime, fallback model
   has different dimensions, ChromaDB returns 0 silently.
2. **ChromaDB collection points at empty store** — wrong
   `chroma_collection_name`, vectorstore_dir mismatch, or volume not
   mounted.
3. **No `collection_chunks` rows** for this collection — lexical
   fallback also empty.
4. **Min-relevance threshold too high** — `chatbot.rag_min_relevance`
   filters all hits out. Code does have a fallback to `filtered_results[:final_k]`
   if `relevance_filtered` is empty (line 516-517), so this is unlikely
   to be the sole cause but worth checking.

### Diagnostic queries (run via SSH)

```bash
# 1. Find the chatbot's collections
ssh llars "docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e \"
SELECT cb.id, cb.name, cb.rag_enabled, cb.rag_retrieval_k, cb.rag_min_relevance, cb.fallback_message
FROM chatbots cb WHERE cb.id = 64\\G
SELECT cc.collection_id, c.name, c.chroma_collection_name, c.embedding_status, c.embedding_error
FROM chatbot_collections cc JOIN rag_collections c ON c.id = cc.collection_id
WHERE cc.chatbot_id = 64\\G
\""

# 2. Embedding model registry for those collections
ssh llars "docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e \"
SELECT ce.collection_id, ce.model_id, ce.status, ce.dimensions, ce.chroma_collection_name
FROM collection_embeddings ce
WHERE ce.collection_id IN (SELECT collection_id FROM chatbot_collections WHERE chatbot_id = 64)\""

# 3. Chunk count per collection (lexical fallback availability)
ssh llars "docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e \"
SELECT collection_id, COUNT(*) AS chunks FROM collection_chunks
WHERE collection_id IN (SELECT collection_id FROM chatbot_collections WHERE chatbot_id = 64)
GROUP BY collection_id\""

# 4. Live RAG retrieval log when a query hits chatbot 64
ssh llars "docker logs llars_flask_service 2>&1 | grep -E 'ChatRAGRetrieval|chatbot.*64|chat_service' | tail -100"
```

### Possible code-side improvement

When the fallback fires in `chat_service.py:194`, log the diagnostic
context (collection ids, whether semantic returned, whether lexical
returned) so admins can see *why* without reading internal warnings.
That makes future debugging faster but does not fix the underlying
runtime issue.

---

## 4. Prompt Engineering `/promptengineering/89` Test-Button

### Status: **Code looks intact; runtime issue suspected**

Frontend (`TestPromptDialog.vue`):
- Initializes socket via `getSocket()`
- Emits `test_prompt_stream` with system/user prompts, model, temperature.
- Listens for `test_prompt_response` chunks.

Backend (`socketio_handlers/events_chat.py:232`):
- `handle_test_prompt_stream` resolves the LLM client through
  `LLMClientFactory.resolve_for_chat(model)`
- Streams via `client.chat.completions.create(stream=True)`
- Emits `test_prompt_response` per chunk plus a final `complete=True`.

Werkzeug is pinned at 3.0.6 in `requirements.txt` (commented as
critical), so the well-known Flask-SocketIO session crash is not at
play.

The most plausible runtime causes:

### Suspect A: Selected model resolves to no provider

If the chatbot test uses a `Global/...` or `user-provider:...` model
where the provider has no API key (or the key is encrypted with the
wrong key chain — see CLAUDE.md memory), `LLMClientFactory.resolve_for_chat`
raises and the handler emits an error string the popup may swallow.

### Suspect B: Stream completes immediately with empty content

LiteLLM occasionally returns an empty stream for a model whose
provider returns 401/403 silently. The popup then shows "no answer"
with no error.

### Diagnostic

```bash
# Open prompt eng test, send a prompt, then:
ssh llars "docker logs llars_flask_service 2>&1 | grep -E 'test_prompt|LLMClientFactory|secret_encryption' | tail -50"
ssh llars "docker logs llars_flask_service 2>&1 | grep -iE 'authentication|401|403|forbidden' | tail -20"
```

If `LLMClientFactory` errors out, fix is in the provider config:
re-enter the API key on `/settings/llm-providers` (which re-encrypts
with the current `LLM_PROVIDER_ENCRYPTION_KEY`).

---

## 5. Batch Generation `/generation/82` – LLMs do not respond

### Status: **Same LLM provider chain as Test-Button — most likely related**

`GenerationWorker._emit_event` runs in a background thread with
`socketio.emit(..., room=f'generation_job_{job_id}')`. The actual
LLM call goes through `LLMClientFactory` → `client.chat.completions.create`.
If the same LLM provider lookup fails as for the Test-Button, every
batch entry fails immediately and the worker logs errors but the
frontend shows the job as still pending.

### Diagnostic

```bash
ssh llars "docker logs llars_flask_service 2>&1 | grep -iE 'generation|GenerationWorker|batch.*82' | tail -100"
ssh llars "docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e \"
SELECT id, status, error, started_at, completed_at, updated_at FROM generation_jobs WHERE id = 82\""
ssh llars "docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e \"
SELECT entry_id, status, error FROM generation_entries WHERE job_id = 82 ORDER BY entry_id LIMIT 20\""
```

If many entries have the same error message, that is the root cause.
Most common: `Failed to decrypt API key` (the user-provider model
needs the same `LLM_PROVIDER_ENCRYPTION_KEY` env var as when it was
created — see CLAUDE.md memory entry on the encryption key chain).

---

## 6. Document upload/delete in Chatbot Manager

### Status: **Not analysed in code yet**

User uncertain whether upload/delete work. Code paths to check next:
- `app/routes/rag/` — collection document endpoints
- `llars-frontend/src/components/Admin/ChatbotAdmin/` —
  upload/delete UI
- Storage path: `/app/storage/rag_documents/`

Quick prod check:

```bash
ssh llars "docker exec llars_flask_service ls -la /app/storage/rag_documents/ | head -20"
ssh llars "docker logs llars_flask_service 2>&1 | grep -iE 'upload|document.*delete|rag_documents' | tail -30"
```

---

## 7. Chatbot UX bugs

### Status: **Not analysed; needs concrete examples from user**

The user mentioned "ein paar kleine buggy sachen" without specifics.
Without concrete reproductions there's nothing to fix here. Next step:
ask user for a list of UX issues observed in
`/chat?chatbot_id=64&chatbot=bewabeck_chatbot` (e.g. message ordering,
markdown rendering, source links, scroll behaviour, mobile layout).

---

## Next-step checklist (when SSH is available)

Order of operations:

1. **Run the chatbot 64 diagnostics** in §3 — this is the highest-impact
   issue (whole chatbot is unusable).
2. **Run the LLM provider diagnostic** in §4/§5 — if it points to
   decryption or auth errors, fix the provider key once and Test-Button
   + Batch Generation are likely both restored.
3. **Run the crawler Redis check** in §2 — verify state is shared.
4. **Browse `/scenarios/176?tab=evaluation`** with DevTools open and
   confirm `scenario:stats_updated` events arrive after a new rating
   is submitted.
5. **Ask user for concrete UX bugs** in §7.

Each diagnosis result feeds directly into a follow-up commit on this
branch.
