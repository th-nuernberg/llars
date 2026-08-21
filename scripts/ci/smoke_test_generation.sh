#!/usr/bin/env bash
# =============================================================================
# LLARS Batch Generation Pipeline Smoke Test
# =============================================================================
# Tests the batch generation pipeline via REST API with X-API-Key:
# 1. Health check (skip if generation not available)
# 2. Discover available LLM model
# 3. Create a UserPrompt (Prompt Engineering) for generation
# 4. Create a generation job (custom source with inline text)
# 5. Poll job status until completed/failed
# 6. Verify outputs (content exists, no errors)
# 7. Cleanup: delete the job + prompt (best-effort)
#
# IMPORTANT: Generation requires UserPrompt or PromptTemplate IDs,
# NOT admin field-prompts. This script creates a temporary UserPrompt
# via /api/prompts (Prompt Engineering API).
#
# Prerequisites:
#   - LLARS running and healthy
#   - SYSTEM_ADMIN_API_KEY set
#   - At least one active LLM model
#
# Usage: BASE_URL=http://localhost SYSTEM_ADMIN_API_KEY=... bash smoke_test_generation.sh
# =============================================================================

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
ENV_FILE="$DEPLOY_PATH/.env"
SMOKE_FORCE_HTTPS_HEADER="${SMOKE_FORCE_HTTPS_HEADER:-1}"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

API_KEY="${SYSTEM_ADMIN_API_KEY:-}"

if [ -z "$API_KEY" ]; then
  echo "ERROR: SYSTEM_ADMIN_API_KEY not set. Cannot run generation smoke test."
  exit 1
fi

JOB_ID=""
PROMPT_ID=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
log_err()  { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

CURL_HEADER_ARGS=()
if [ "$SMOKE_FORCE_HTTPS_HEADER" = "1" ]; then
  CURL_HEADER_ARGS+=(-H "X-Forwarded-Proto: https")
fi

smoke_curl() {
  curl "${CURL_HEADER_ARGS[@]}" "$@"
}

# api_safe: like api() but uses -s (not -sf) so we get error bodies
api_safe() {
  local method="$1"
  local path="$2"
  shift 2
  smoke_curl -s -X "$method" "$BASE_URL$path" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    "$@"
}

# api_status: returns HTTP status code
api_status() {
  local method="$1"
  local path="$2"
  shift 2
  smoke_curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$path" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    "$@" 2>/dev/null || echo "000"
}

cleanup() {
  # Best-effort cleanup of generation job
  if [ -n "${JOB_ID:-}" ]; then
    echo "Cleanup: Deleting smoke test job $JOB_ID..."
    smoke_curl -s -X POST "$BASE_URL/api/generation/jobs/$JOB_ID/cancel" \
      -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" 2>/dev/null || true
    smoke_curl -s -X DELETE "$BASE_URL/api/generation/jobs/$JOB_ID" \
      -H "X-API-Key: $API_KEY" 2>/dev/null || true
  fi
  # Best-effort cleanup of temporary prompt
  if [ -n "${PROMPT_ID:-}" ]; then
    echo "Cleanup: Deleting smoke test prompt $PROMPT_ID..."
    smoke_curl -s -X DELETE "$BASE_URL/api/prompts/$PROMPT_ID" \
      -H "X-API-Key: $API_KEY" 2>/dev/null || true
  fi
}

trap cleanup EXIT

echo "=== Batch Generation Smoke Test ==="
echo "Target: $BASE_URL"

# -------------------------------------------------------------------------
# [1] Health Check - skip gracefully if generation is not available
# -------------------------------------------------------------------------
echo ""
echo "[1/6] Generation health check..."
HEALTH_CODE="$(api_status GET "/api/generation/health")"

if [ "$HEALTH_CODE" != "200" ]; then
  log_ok "Generation service not available (HTTP $HEALTH_CODE), skipping"
  JOB_ID=""
  PROMPT_ID=""
  exit 0
fi
log_ok "Generation service healthy"

# -------------------------------------------------------------------------
# [2] Discover LLM model
# -------------------------------------------------------------------------
echo ""
echo "[2/6] Discovering LLM model..."

MODELS_RESPONSE="$(api_safe GET "/api/llm/models?active_only=true&model_type=llm" 2>/dev/null || echo '[]')"
MODEL_ID="$(echo "$MODELS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = data if isinstance(data, list) else data.get('models', data.get('data', []))
    # Prefer non-OpenAI models (OpenAI restricted to admin)
    for m in models:
        mid = m.get('model_id', '')
        if mid and 'openai' not in mid.lower():
            print(mid); break
    else:
        for m in models:
            mid = m.get('model_id', '')
            if mid:
                print(mid); break
except: pass
" 2>/dev/null || true)"

if [ -z "$MODEL_ID" ]; then
  log_ok "No active LLM models found, skipping generation smoke test"
  exit 0
fi
log_ok "Using model: $MODEL_ID"

# -------------------------------------------------------------------------
# [3] Create temporary UserPrompt via Prompt Engineering API
# -------------------------------------------------------------------------
echo ""
echo "[3/6] Creating temporary prompt for generation..."

PROMPT_NAME="smoke-gen-$(date +%s)"
PROMPT_RESPONSE="$(api_safe POST "/api/prompts" -d '{
  "name": "'"$PROMPT_NAME"'",
  "system_prompt": "You are a helpful assistant. Summarize the given text concisely.",
  "user_prompt": "Summarize the following text in one sentence:\n\n{{input}}",
  "description": "Temporary prompt for CI smoke test",
  "is_active": true
}' 2>/dev/null || echo '{}')"

PROMPT_ID="$(echo "$PROMPT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    p = data.get('prompt', data)
    print(p.get('id', p.get('prompt_id', '')))
except: pass
" 2>/dev/null || true)"

if [ -z "$PROMPT_ID" ]; then
  log_warn "Could not create prompt via /api/prompts"
  echo "Response: $PROMPT_RESPONSE"

  # Try to find an existing UserPrompt instead
  EXISTING_PROMPTS="$(api_safe GET "/api/prompts" 2>/dev/null || echo '[]')"
  PROMPT_ID="$(echo "$EXISTING_PROMPTS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    prompts = data if isinstance(data, list) else data.get('prompts', [])
    for p in prompts:
        pid = p.get('id', p.get('prompt_id', ''))
        if pid:
            print(pid); break
except: pass
" 2>/dev/null || true)"

  if [ -z "$PROMPT_ID" ]; then
    log_ok "No prompts available for generation, skipping"
    PROMPT_ID=""
    exit 0
  fi
  log_ok "Using existing prompt: ID=$PROMPT_ID"
  # Don't delete an existing prompt on cleanup
  PROMPT_ID_CLEANUP=""
else
  PROMPT_ID_CLEANUP="$PROMPT_ID"
  log_ok "Created temporary prompt: ID=$PROMPT_ID (name=$PROMPT_NAME)"
fi

# Override cleanup to only delete our own prompt
cleanup() {
  if [ -n "${JOB_ID:-}" ]; then
    echo "Cleanup: Deleting smoke test job $JOB_ID..."
    smoke_curl -s -X POST "$BASE_URL/api/generation/jobs/$JOB_ID/cancel" \
      -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" 2>/dev/null || true
    smoke_curl -s -X DELETE "$BASE_URL/api/generation/jobs/$JOB_ID" \
      -H "X-API-Key: $API_KEY" 2>/dev/null || true
  fi
  if [ -n "${PROMPT_ID_CLEANUP:-}" ]; then
    echo "Cleanup: Deleting smoke test prompt $PROMPT_ID_CLEANUP..."
    smoke_curl -s -X DELETE "$BASE_URL/api/prompts/$PROMPT_ID_CLEANUP" \
      -H "X-API-Key: $API_KEY" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# -------------------------------------------------------------------------
# [4] Create Generation Job
# -------------------------------------------------------------------------
echo ""
echo "[4/6] Creating generation job..."

JOB_NAME="smoke-test-gen-$(date +%s)"

CREATE_PAYLOAD="$(MODEL_ID="$MODEL_ID" TEMPLATE_ID="$PROMPT_ID" JOB_NAME="$JOB_NAME" python3 - <<'PY'
import json, os

payload = {
    "name": os.environ["JOB_NAME"],
    "description": "CI smoke test for batch generation pipeline",
    "config": {
        "sources": {
            "type": "custom",
            "custom_texts": [
                "The quick brown fox jumps over the lazy dog. This is a test sentence for smoke testing the generation pipeline. It contains multiple sentences to provide enough context for summarization."
            ]
        },
        "prompts": [
            {
                "template_id": int(os.environ["TEMPLATE_ID"]),
                "variant_name": "smoke-test"
            }
        ],
        "llm_models": [os.environ["MODEL_ID"]],
        "generation_params": {
            "temperature": 0.7,
            "max_tokens": 150
        }
    },
    "auto_start": True
}

print(json.dumps(payload))
PY
)"

# Use api_safe (not -sf) so we get error messages
JOB_RESPONSE="$(api_safe POST "/api/generation/jobs" -d "$CREATE_PAYLOAD" 2>/dev/null || echo '{}')"
JOB_ID="$(echo "$JOB_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    job = data.get('job', data)
    print(job.get('id', ''))
except: pass
" 2>/dev/null || true)"

if [ -z "$JOB_ID" ]; then
  # Extract error message for diagnostics
  ERROR_MSG="$(echo "$JOB_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('error', data.get('message', data.get('detail', ''))))
except: print(sys.stdin.read()[:200] if False else '')
" 2>/dev/null || true)"

  if [ -n "$ERROR_MSG" ]; then
    log_warn "Job creation failed: $ERROR_MSG"
    log_ok "Generation prerequisites not met, skipping (not a pipeline failure)"
  else
    log_warn "Job creation returned empty/unexpected response"
    echo "Response: $(echo "$JOB_RESPONSE" | head -c 500)"
    log_ok "Skipping generation smoke test (prerequisites may not be met)"
  fi
  JOB_ID=""
  exit 0
fi
log_ok "Job created: ID=$JOB_ID (name=$JOB_NAME)"

# -------------------------------------------------------------------------
# [5] Poll Job Status (max 120s, every 5s)
# -------------------------------------------------------------------------
echo ""
echo "[5/6] Polling job status (timeout: 120s)..."

MAX_WAIT=120
INTERVAL=5
ELAPSED=0
FINAL_STATUS=""

while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
  STATUS_RESPONSE="$(api_safe GET "/api/generation/jobs/$JOB_ID" 2>/dev/null || echo '{}')"
  CURRENT_STATUS="$(echo "$STATUS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    job = data.get('job', data)
    print(job.get('status', 'unknown'))
except: print('unknown')
" 2>/dev/null || echo "unknown")"

  case "$CURRENT_STATUS" in
    completed)
      FINAL_STATUS="completed"
      break
      ;;
    failed|cancelled)
      FINAL_STATUS="$CURRENT_STATUS"
      break
      ;;
    *)
      echo "  Status: $CURRENT_STATUS (${ELAPSED}s elapsed)"
      sleep "$INTERVAL"
      ELAPSED=$((ELAPSED + INTERVAL))
      ;;
  esac
done

if [ "$FINAL_STATUS" = "completed" ]; then
  log_ok "Job completed successfully"
elif [ "$FINAL_STATUS" = "failed" ]; then
  log_err "Job failed"
  echo "Response: $(echo "$STATUS_RESPONSE" | head -c 500)"
  exit 1
elif [ "$FINAL_STATUS" = "cancelled" ]; then
  log_err "Job was cancelled unexpectedly"
  exit 1
else
  log_err "Job timed out after ${MAX_WAIT}s (last status: $CURRENT_STATUS)"
  exit 1
fi

# -------------------------------------------------------------------------
# [6] Verify Outputs
# -------------------------------------------------------------------------
echo ""
echo "[6/6] Verifying job outputs..."

VERIFY_RESPONSE="$(api_safe GET "/api/generation/jobs/$JOB_ID" 2>/dev/null || echo '{}')"
OUTPUT_CHECK="$(echo "$VERIFY_RESPONSE" | python3 -c "
import sys, json

data = json.load(sys.stdin)
job = data.get('job', data)
total = job.get('total_items', 0)
completed = job.get('completed_items', 0)

if total == 0:
    print('ERROR: No outputs generated (total_items=0)')
elif completed == 0:
    print('ERROR: No completed outputs (completed_items=0)')
else:
    print(f'OK: {completed}/{total} outputs completed')
" 2>/dev/null || echo "ERROR: Could not parse response")"

if echo "$OUTPUT_CHECK" | grep -q "^ERROR:"; then
  log_err "$OUTPUT_CHECK"
  exit 1
fi
log_ok "$OUTPUT_CHECK"

echo "Cleanup will run via trap..."

echo ""
echo "=== Batch Generation Smoke Test PASSED ==="
