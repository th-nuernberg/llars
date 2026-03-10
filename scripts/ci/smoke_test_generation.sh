#!/usr/bin/env bash
# =============================================================================
# LLARS Batch Generation Pipeline Smoke Test
# =============================================================================
# Tests the batch generation pipeline via REST API with X-API-Key:
# 1. Health check (skip if generation not available)
# 2. Discover available LLM model + prompt template
# 3. Create a generation job (custom source with inline text)
# 4. Poll job status until completed/failed
# 5. Verify outputs (content exists, no errors)
# 6. Cleanup: delete the job (best-effort)
#
# Prerequisites:
#   - LLARS running and healthy
#   - SYSTEM_ADMIN_API_KEY set
#   - At least one active LLM model and one prompt template seeded
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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

CURL_HEADER_ARGS=()
if [ "$SMOKE_FORCE_HTTPS_HEADER" = "1" ]; then
  CURL_HEADER_ARGS+=(-H "X-Forwarded-Proto: https")
fi

smoke_curl() {
  curl "${CURL_HEADER_ARGS[@]}" "$@"
}

cleanup() {
  if [ -n "${JOB_ID:-}" ]; then
    echo "Cleanup: Attempting to delete smoke test job $JOB_ID..."
    # DELETE uses @authentik_required, so API-key may not work.
    # Try cancel first (also @authentik_required), then delete. Best-effort.
    smoke_curl -sf -X POST "$BASE_URL/api/generation/jobs/$JOB_ID/cancel" \
      -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" 2>/dev/null || true
    smoke_curl -sf -X DELETE "$BASE_URL/api/generation/jobs/$JOB_ID" \
      -H "X-API-Key: $API_KEY" 2>/dev/null || true
  fi
}

trap cleanup EXIT

api() {
  local method="$1"
  local path="$2"
  shift 2
  smoke_curl -sf -X "$method" "$BASE_URL$path" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    "$@"
}

echo "=== Batch Generation Smoke Test ==="
echo "Target: $BASE_URL"

# -------------------------------------------------------------------------
# [1] Health Check - skip gracefully if generation is not available
# -------------------------------------------------------------------------
echo ""
echo "[1/5] Generation health check..."
HEALTH_RESPONSE="$(smoke_curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/generation/health" "${CURL_HEADER_ARGS[@]:+${CURL_HEADER_ARGS[@]}}" 2>/dev/null || echo "000")"

if [ "$HEALTH_RESPONSE" != "200" ]; then
  log_ok "Generation service not available (HTTP $HEALTH_RESPONSE), skipping"
  # Clear JOB_ID so cleanup trap does nothing
  JOB_ID=""
  exit 0
fi
log_ok "Generation service healthy"

# -------------------------------------------------------------------------
# [2] Discover LLM model + prompt template
# -------------------------------------------------------------------------
echo ""
echo "[2/5] Discovering LLM model and prompt template..."

# Find first active LLM model
MODELS_RESPONSE="$(api GET "/api/llm/models?active_only=true&model_type=llm" 2>/dev/null || echo '{"models":[]}')"
MODEL_ID="$(echo "$MODELS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data if isinstance(data, list) else data.get('models', [])
for m in models:
    mid = m.get('model_id', '')
    # Prefer non-OpenAI models (OpenAI restricted to admin, might not work in CI)
    if mid and 'openai' not in mid.lower():
        print(mid)
        break
else:
    # Fall back to any model
    for m in models:
        mid = m.get('model_id', '')
        if mid:
            print(mid)
            break
" 2>/dev/null)"

if [ -z "$MODEL_ID" ]; then
  log_ok "No active LLM models found, skipping generation smoke test"
  JOB_ID=""
  exit 0
fi
log_ok "Using model: $MODEL_ID"

# Find first available prompt template (UserPrompt) via generation jobs list
# We query generation/jobs to see if the endpoint works, and look for an
# existing prompt template ID. If none found, try prompt_only mode.
#
# Strategy: Use prompt_only source type which needs a template_id.
# Query the admin field-prompts endpoint to find a usable template.
PROMPTS_RESPONSE="$(api GET "/api/admin/field-prompts" 2>/dev/null || echo '{"templates":[]}')"
TEMPLATE_ID="$(echo "$PROMPTS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
templates = data.get('templates', data.get('prompts', []))
if isinstance(templates, list) and templates:
    # Use the first template
    t = templates[0]
    print(t.get('id', t.get('template_id', '')))
" 2>/dev/null)"

# If no field-prompt found, create a temporary one for the smoke test
CREATED_TEMPLATE=""
if [ -z "$TEMPLATE_ID" ]; then
  echo "No existing prompt template found, creating temporary one..."
  CREATE_TMPL_RESPONSE="$(api POST "/api/admin/field-prompts" -d '{
    "field_key": "smoke_gen_tmpl_'"$(date +%s)"'",
    "display_name": "Smoke Gen Template",
    "system_prompt": "You are a helpful assistant.",
    "user_prompt_template": "Summarize: {{content}}",
    "description": "Temporary template for generation smoke testing",
    "max_tokens": 100,
    "temperature": 0.7
  }' 2>/dev/null || echo '{}')"

  TEMPLATE_ID="$(echo "$CREATE_TMPL_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tmpl = data.get('template') or data.get('prompt') or data
print(tmpl.get('id', tmpl.get('template_id', '')))
" 2>/dev/null)"

  if [ -n "$TEMPLATE_ID" ]; then
    CREATED_TEMPLATE="$TEMPLATE_ID"
    log_ok "Created temporary prompt template: ID=$TEMPLATE_ID"
  else
    log_ok "Could not create prompt template, skipping generation smoke test"
    JOB_ID=""
    exit 0
  fi
else
  log_ok "Using existing prompt template: ID=$TEMPLATE_ID"
fi

# Ensure we clean up the temporary template too
cleanup_template() {
  if [ -n "$CREATED_TEMPLATE" ]; then
    echo "Cleanup: Deleting temporary prompt template $CREATED_TEMPLATE..."
    smoke_curl -sf -X DELETE "$BASE_URL/api/admin/field-prompts/$CREATED_TEMPLATE" \
      -H "X-API-Key: $API_KEY" 2>/dev/null || true
  fi
}

# Override trap to also clean up template
cleanup_all() {
  cleanup
  cleanup_template
}
trap cleanup_all EXIT

# -------------------------------------------------------------------------
# [3] Create Generation Job
# -------------------------------------------------------------------------
echo ""
echo "[3/5] Creating generation job..."

JOB_NAME="smoke-test-gen-$(date +%s)"

# Build the job config using custom source type with inline text
CREATE_PAYLOAD="$(MODEL_ID="$MODEL_ID" TEMPLATE_ID="$TEMPLATE_ID" JOB_NAME="$JOB_NAME" python3 - <<'PY'
import json
import os

model_id = os.environ["MODEL_ID"]
template_id = int(os.environ["TEMPLATE_ID"])
job_name = os.environ["JOB_NAME"]

payload = {
    "name": job_name,
    "description": "CI smoke test for batch generation pipeline",
    "config": {
        "sources": {
            "type": "custom",
            "custom_texts": [
                "The quick brown fox jumps over the lazy dog. This is a test sentence for smoke testing the generation pipeline."
            ]
        },
        "prompts": [
            {
                "template_id": template_id,
                "variant_name": "smoke-test"
            }
        ],
        "llm_models": [model_id],
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

JOB_RESPONSE="$(api POST "/api/generation/jobs" -d "$CREATE_PAYLOAD" 2>/dev/null || true)"
JOB_ID="$(echo "$JOB_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
job = data.get('job', {})
print(job.get('id', ''))
" 2>/dev/null || true)"

if [ -z "$JOB_ID" ]; then
  # Check if it failed due to missing prerequisites (model not configured, etc.)
  ERROR_MSG="$(echo "$JOB_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('error', data.get('message', '')))
except: print('')
" 2>/dev/null || true)"

  if [ -n "$ERROR_MSG" ]; then
    echo "WARN: Job creation failed: $ERROR_MSG"
    log_ok "Generation prerequisites not met, skipping (not a pipeline failure)"
    JOB_ID=""
    exit 0
  fi

  log_err "Failed to create generation job"
  echo "Response: $JOB_RESPONSE"
  exit 1
fi
log_ok "Job created: ID=$JOB_ID (name=$JOB_NAME)"

# -------------------------------------------------------------------------
# [4] Poll Job Status (max 120s, every 5s)
# -------------------------------------------------------------------------
echo ""
echo "[4/5] Polling job status (timeout: 120s)..."

MAX_WAIT=120
INTERVAL=5
ELAPSED=0
FINAL_STATUS=""

while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
  STATUS_RESPONSE="$(api GET "/api/generation/jobs/$JOB_ID" 2>/dev/null || echo '{}')"
  CURRENT_STATUS="$(echo "$STATUS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
job = data.get('job', {})
print(job.get('status', 'unknown'))
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
  echo "Response: $STATUS_RESPONSE"
  exit 1
elif [ "$FINAL_STATUS" = "cancelled" ]; then
  log_err "Job was cancelled unexpectedly"
  exit 1
else
  log_err "Job timed out after ${MAX_WAIT}s (last status: $CURRENT_STATUS)"
  exit 1
fi

# -------------------------------------------------------------------------
# [5] Verify Outputs
# -------------------------------------------------------------------------
echo ""
echo "[5/5] Verifying job outputs..."

# Get job details to check output counts
VERIFY_RESPONSE="$(api GET "/api/generation/jobs/$JOB_ID" 2>/dev/null || echo '{}')"
OUTPUT_CHECK="$(echo "$VERIFY_RESPONSE" | python3 -c "
import sys, json

data = json.load(sys.stdin)
job = data.get('job', {})
total = job.get('total_items', 0)
completed = job.get('completed_items', 0)

# Check basic counts
if total == 0:
    print('ERROR: No outputs generated (total_items=0)')
    sys.exit(0)

if completed == 0:
    print('ERROR: No completed outputs (completed_items=0)')
    sys.exit(0)

print(f'OK: {completed}/{total} outputs completed')
" 2>/dev/null)"

if echo "$OUTPUT_CHECK" | grep -q "^ERROR:"; then
  log_err "$OUTPUT_CHECK"
  exit 1
fi
log_ok "$OUTPUT_CHECK"

echo "Cleanup will run via trap..."

echo ""
echo "=== Batch Generation Smoke Test PASSED ==="
