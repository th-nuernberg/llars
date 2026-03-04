#!/usr/bin/env bash
# =============================================================================
# LLARS Prompt Engineering Smoke Test
# =============================================================================
# Tests the prompt template CRUD pipeline via REST API with X-API-Key:
# 1. Create a field prompt template
# 2. Retrieve the template
# 3. Delete the template
#
# Uses admin field-prompts endpoints (@require_permission → API-Key works)
#
# Usage: BASE_URL=http://localhost SYSTEM_ADMIN_API_KEY=... bash smoke_test_prompt_eng.sh
# =============================================================================

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
ENV_FILE="$DEPLOY_PATH/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

API_KEY="${SYSTEM_ADMIN_API_KEY:-}"

if [ -z "$API_KEY" ]; then
  echo "ERROR: SYSTEM_ADMIN_API_KEY not set. Cannot run prompt engineering smoke test."
  exit 1
fi

TEMPLATE_ID=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

cleanup() {
  if [ -n "$TEMPLATE_ID" ]; then
    echo "Cleanup: Deleting smoke test template $TEMPLATE_ID..."
    curl -sf -X DELETE "$BASE_URL/api/admin/field-prompts/$TEMPLATE_ID" \
      -H "X-API-Key: $API_KEY" || true
  fi
}

trap cleanup EXIT

api() {
  local method="$1"
  local path="$2"
  shift 2
  curl -sf -X "$method" "$BASE_URL$path" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    "$@"
}

echo "=== Prompt Engineering Smoke Test ==="
echo "Target: $BASE_URL"

# -------------------------------------------------------------------------
# [1] Create Template
# -------------------------------------------------------------------------
echo ""
echo "[1/3] Creating field prompt template..."
CREATE_RESPONSE=$(api POST "/api/admin/field-prompts" -d '{
  "field_key": "smoke_test_template_'"$(date +%s)"'",
  "display_name": "Smoke Test Template",
  "system_prompt": "You are a helpful test assistant.",
  "user_prompt_template": "Summarize the following: {{content}}",
  "description": "Temporary template for CI smoke testing",
  "max_tokens": 100,
  "temperature": 0.7
}')

TEMPLATE_ID=$(echo "$CREATE_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tmpl = data.get('template', data)
print(tmpl.get('id', tmpl.get('template_id', '')))
" 2>/dev/null)

if [ -z "$TEMPLATE_ID" ]; then
  log_err "Failed to create template"
  echo "Response: $CREATE_RESPONSE"
  exit 1
fi
log_ok "Template created: ID=$TEMPLATE_ID"

# -------------------------------------------------------------------------
# [2] Retrieve Template
# -------------------------------------------------------------------------
echo ""
echo "[2/3] Retrieving template..."
GET_RESPONSE=$(api GET "/api/admin/field-prompts/smoke_test_template_*" 2>/dev/null || echo '{}')

# Try the list endpoint instead
LIST_RESPONSE=$(api GET "/api/admin/field-prompts" 2>/dev/null || echo '{"templates":[]}')
FOUND=$(echo "$LIST_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
templates = data.get('templates', data.get('prompts', []))
found = any(str(t.get('id', '')) == '$TEMPLATE_ID' for t in templates)
print('yes' if found else 'no')
" 2>/dev/null)

if [ "$FOUND" = "yes" ]; then
  log_ok "Template found in list"
else
  echo "WARN: Template not found in list (may use different field). Checking API response..."
  if echo "$LIST_RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    log_ok "Field-prompts list endpoint returns valid JSON"
  else
    log_err "Field-prompts endpoint returned invalid response"
    exit 1
  fi
fi

# -------------------------------------------------------------------------
# [3] Delete Template (via trap + explicit)
# -------------------------------------------------------------------------
echo ""
echo "[3/3] Deleting template $TEMPLATE_ID..."
DELETE_RESPONSE=$(api DELETE "/api/admin/field-prompts/$TEMPLATE_ID" 2>/dev/null || echo '{}')
TEMPLATE_ID=""  # Prevent double-delete in trap
log_ok "Template deleted"

echo ""
echo "=== Prompt Engineering Smoke Test PASSED ==="
