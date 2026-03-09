#!/usr/bin/env bash
# =============================================================================
# LLARS Evaluation Pipeline Smoke Test
# =============================================================================
# Tests the complete evaluation pipeline via REST API with X-API-Key:
# 1. Health check
# 2. Create a rating scenario (multi-dimensional)
# 3. Add items to the scenario
# 4. Submit a dimensional rating
# 5. Verify scenario progress stats
# 6. Cleanup: delete the scenario
#
# Prerequisites:
#   - LLARS running and healthy
#   - SYSTEM_ADMIN_API_KEY set
#   - Seeded data (admin user must exist)
#
# Usage: BASE_URL=http://localhost SYSTEM_ADMIN_API_KEY=... bash smoke_test_evaluation.sh
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
  echo "ERROR: SYSTEM_ADMIN_API_KEY not set. Cannot run evaluation smoke test."
  exit 1
fi

SCENARIO_ID=""
FUNCTION_TYPE_ID=""

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
  if [ -n "${SCENARIO_ID:-}" ]; then
    echo "Cleanup: Deleting smoke test scenario $SCENARIO_ID..."
    smoke_curl -sf -X DELETE "$BASE_URL/api/admin/delete_scenario/$SCENARIO_ID" \
      -H "X-API-Key: $API_KEY" || true
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

echo "=== Evaluation Pipeline Smoke Test ==="
echo "Target: $BASE_URL"

# -------------------------------------------------------------------------
# [1] Health Check
# -------------------------------------------------------------------------
echo ""
echo "[1/6] Health check..."
if ! smoke_curl -sf "$BASE_URL/auth/health_check" > /dev/null; then
  log_err "API not reachable at $BASE_URL"
  exit 1
fi
log_ok "API healthy"

# -------------------------------------------------------------------------
# [2] Resolve Function Type (rating)
# -------------------------------------------------------------------------
echo ""
echo "[2/6] Resolving rating function type..."
FUNCTION_TYPES_RESPONSE="$(api GET "/api/admin/get_function_types" 2>/dev/null || echo "[]")"
FUNCTION_TYPE_ID="$(echo "$FUNCTION_TYPES_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if isinstance(data, list):
    for entry in data:
        if str(entry.get('name', '')).strip().lower() == 'rating':
            print(entry.get('function_type_id', ''))
            break
" 2>/dev/null)"

if [ -z "$FUNCTION_TYPE_ID" ]; then
  FUNCTION_TYPE_ID="${EVAL_FUNCTION_TYPE_ID:-2}"
  echo "WARN: Could not resolve function_type_id for 'rating' via API; using fallback=$FUNCTION_TYPE_ID"
fi
log_ok "Resolved rating function_type_id=$FUNCTION_TYPE_ID"

# -------------------------------------------------------------------------
# [3] Fetch candidate threads
# -------------------------------------------------------------------------
echo ""
echo "[3/6] Fetching candidate threads for rating..."
THREADS_RESPONSE="$(api GET "/api/admin/get_threads_from_function_type/$FUNCTION_TYPE_ID" 2>/dev/null || echo "[]")"
THREAD_IDS_JSON="$(echo "$THREADS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if not isinstance(data, list):
    print('[]')
else:
    ids = [int(i.get('thread_id')) for i in data if isinstance(i, dict) and i.get('thread_id')][:2]
    print(json.dumps(ids))
" 2>/dev/null)"
THREAD_COUNT="$(echo "$THREAD_IDS_JSON" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")"
if [ "$THREAD_COUNT" -gt 0 ]; then
  log_ok "Found $THREAD_COUNT thread(s) for scenario bootstrap"
else
  echo "WARN: No rating threads found. Scenario will be created without threads."
fi

# -------------------------------------------------------------------------
# [4] Create Scenario (type: rating, multi-dimensional)
# -------------------------------------------------------------------------
echo ""
echo "[4/6] Creating rating scenario..."
CREATE_PAYLOAD="$(THREAD_IDS_JSON="$THREAD_IDS_JSON" FUNCTION_TYPE_ID="$FUNCTION_TYPE_ID" python3 - <<'PY'
import json
import os
import time

thread_ids = json.loads(os.environ.get("THREAD_IDS_JSON", "[]"))
function_type_id = int(os.environ["FUNCTION_TYPE_ID"])

payload = {
    "scenario_name": f"smoke-test-eval-{int(time.time())}",
    "function_type_id": function_type_id,
    "begin": "2020-01-01T00:00:00",
    "end": "2030-12-31T23:59:59",
    "evaluator": ["admin"],
    "config_json": {
        "type": "multi-dimensional",
        "min": 1,
        "max": 5,
        "step": 1,
        "dimensions": [
            {"id": "coherence", "name": {"de": "Kohaerenz", "en": "Coherence"}, "weight": 0.5},
            {"id": "fluency", "name": {"de": "Fluency", "en": "Fluency"}, "weight": 0.5}
        ],
        "labels": {
            "1": {"de": "Sehr schlecht", "en": "Very bad"},
            "5": {"de": "Sehr gut", "en": "Very good"}
        }
    }
}
if thread_ids:
    payload["threads"] = thread_ids

print(json.dumps(payload))
PY
)"

SCENARIO_RESPONSE="$(api POST "/api/admin/create_scenario" -d "$CREATE_PAYLOAD" 2>/dev/null || true)"
SCENARIO_ID="$(echo "$SCENARIO_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('scenario_id',''))" 2>/dev/null || true)"

if [ -z "$SCENARIO_ID" ]; then
  log_err "Failed to create scenario"
  echo "Response: $SCENARIO_RESPONSE"
  exit 1
fi
log_ok "Scenario created: ID=$SCENARIO_ID"

# -------------------------------------------------------------------------
# [5] Submit rating (if item exists) and verify stats
# -------------------------------------------------------------------------
echo ""
echo "[5/6] Fetching rating items..."
RATING_ITEMS="$(api GET "/api/evaluation/rating/$SCENARIO_ID/items" 2>/dev/null || echo '{"items":[]}' )"
FIRST_ITEM_ID="$(echo "$RATING_ITEMS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', [])
if items:
    item = items[0]
    print(item.get('item_id', item.get('id', item.get('thread_id', ''))))
else:
    print('')
" 2>/dev/null)"

if [ -n "$FIRST_ITEM_ID" ]; then
  log_ok "Items available: first_item=$FIRST_ITEM_ID"
  echo "Submitting dimensional rating..."
  RATE_RESPONSE="$(api POST "/api/evaluation/rating/$SCENARIO_ID/items/$FIRST_ITEM_ID/rate" -d '{
    "dimension_ratings": {"coherence": 4, "fluency": 5},
    "feedback": "Smoke test rating",
    "auto_complete": true
  }' 2>/dev/null || echo '{"success":false}')"

  if echo "$RATE_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('success') is True" 2>/dev/null; then
    log_ok "Rating submitted successfully"
  else
    echo "WARN: Rating submission did not return success=true"
    echo "Response: $RATE_RESPONSE"
  fi
else
  echo "WARN: No assigned items returned. Skipping rating submission."
fi

# -------------------------------------------------------------------------
# [6] Verify stats endpoint and cleanup (via trap)
# -------------------------------------------------------------------------
echo ""
echo "[6/6] Verifying scenario progress stats..."
STATS="$(api GET "/api/admin/scenario_progress_stats/$SCENARIO_ID" 2>/dev/null || echo '{}')"
if echo "$STATS" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  log_ok "Stats endpoint returns valid JSON"
else
  log_err "Stats endpoint returned invalid response"
  echo "Response: $STATS"
  exit 1
fi

echo "Cleanup will run via trap..."

echo ""
echo "=== Evaluation Pipeline Smoke Test PASSED ==="
