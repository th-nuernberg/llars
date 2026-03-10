#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
BASE_URL="${BASE_URL:-http://localhost}"
ENV_FILE="$DEPLOY_PATH/.env"
SMOKE_WIZARD="${SMOKE_WIZARD:-1}"
SMOKE_FORCE_HTTPS_HEADER="${SMOKE_FORCE_HTTPS_HEADER:-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read env vars safely (avoids source failures with special chars in passwords)
_env() { [ -f "$ENV_FILE" ] && grep "^${1}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- || true; }

SYSTEM_ADMIN_API_KEY="${SYSTEM_ADMIN_API_KEY:-$(_env SYSTEM_ADMIN_API_KEY)}"
DB_USER="${MYSQL_USER:-$(_env MYSQL_USER)}" ; DB_USER="${DB_USER:-dev_user}"
DB_PASS="${MYSQL_PASSWORD:-$(_env MYSQL_PASSWORD)}" ; DB_PASS="${DB_PASS:-dev_password_change_me}"
DB_NAME="${MYSQL_DATABASE:-$(_env MYSQL_DATABASE)}" ; DB_NAME="${DB_NAME:-database_llars}"

CURL_HEADER_ARGS=()
if [ "$SMOKE_FORCE_HTTPS_HEADER" = "1" ]; then
  # Production nginx on :80 redirects to HTTPS unless proxied as HTTPS.
  # CI smoke jobs run locally on the server and should emulate proxy headers.
  CURL_HEADER_ARGS+=(-H "X-Forwarded-Proto: https")
fi

smoke_curl() {
  if [ "${#CURL_HEADER_ARGS[@]}" -gt 0 ]; then
    curl "${CURL_HEADER_ARGS[@]}" "$@"
  else
    curl "$@"
  fi
}

assert_status() {
  local url="$1"
  shift
  local expected=("$@");
  local code
  # Follow redirects (-L) to get final status code
  code=$(smoke_curl -sL -o /dev/null -w "%{http_code}" "$url" || true)

  for exp in "${expected[@]}"; do
    if [ "$code" = "$exp" ]; then
      echo "OK $url -> $code"
      return 0
    fi
  done

  echo "ERROR: $url -> $code (expected: ${expected[*]})"
  return 1
}

assert_status_with_api_key() {
  local url="$1"
  shift
  local expected=("$@");
  local code
  # Follow redirects (-L) to get final status code
  code=$(smoke_curl -sL -o /dev/null -w "%{http_code}" -H "X-API-Key: $SYSTEM_ADMIN_API_KEY" "$url" || true)

  for exp in "${expected[@]}"; do
    if [ "$code" = "$exp" ]; then
      echo "OK (api key) $url -> $code"
      return 0
    fi
  done

  echo "ERROR: (api key) $url -> $code (expected: ${expected[*]})"
  return 1
}

assert_system_settings_schema() {
  echo "Checking required system_settings columns"

  local required_columns=(
    "default_referral_role"
    "communication_enabled"
    "ai_assistant_enabled"
    "ai_assistant_color"
    "ai_assistant_username"
  )

  # Preferred check in CI/smoke containers: validate keys via admin API.
  # This avoids relying on Docker CLI access from inside the smoke container.
  if [ -n "$SYSTEM_ADMIN_API_KEY" ]; then
    local settings_json
    settings_json=$(smoke_curl -sS -H "X-API-Key: $SYSTEM_ADMIN_API_KEY" "$BASE_URL/api/admin/system/settings" || true)

    if [ -n "$settings_json" ]; then
      local missing_api
      missing_api=$(python3 - "$settings_json" <<'PY'
import json
import sys

required = [
    "default_referral_role",
    "communication_enabled",
    "ai_assistant_enabled",
    "ai_assistant_color",
    "ai_assistant_username",
]

raw = sys.argv[1]
try:
    payload = json.loads(raw)
except Exception:
    print("__invalid_json__")
    sys.exit(0)

settings = payload.get("settings") if isinstance(payload, dict) else None
if not isinstance(settings, dict):
    print("__missing_settings__")
    sys.exit(0)

missing = [key for key in required if key not in settings]
for key in missing:
    print(key)
PY
)

      if [ "$missing_api" = "__invalid_json__" ] || [ "$missing_api" = "__missing_settings__" ]; then
        echo "WARNING: /api/admin/system/settings returned invalid payload. Falling back to DB check."
      else
        if [ -n "$missing_api" ]; then
          while IFS= read -r column; do
            [ -z "$column" ] && continue
            echo "ERROR: Missing required field in system settings API: $column"
          done <<< "$missing_api"
          return 1
        fi

        echo "OK system_settings schema (API)"
        return 0
      fi
    fi
  fi

  echo "WARNING: API-based schema check unavailable; trying DB fallback."
  if ! command -v docker >/dev/null 2>&1; then
    echo "WARNING: docker CLI unavailable; skipping DB schema fallback."
    return 0
  fi

  local columns
  columns=$(docker exec llars_db_service \
    mariadb -N -u "$DB_USER" "-p$DB_PASS" "$DB_NAME" \
    -e "SHOW COLUMNS FROM system_settings;" 2>/dev/null | awk '{print $1}' || true)

  if [ -z "$columns" ]; then
    echo "WARNING: Could not read columns from system_settings via DB fallback."
    return 0
  fi

  local missing=0
  for column in "${required_columns[@]}"; do
    if ! grep -qx "$column" <<< "$columns"; then
      echo "ERROR: Missing required column in system_settings: $column"
      missing=1
    fi
  done

  if [ "$missing" -ne 0 ]; then
    return 1
  fi

  echo "OK system_settings schema"
}

echo "Running basic smoke checks against $BASE_URL"

assert_system_settings_schema

assert_status "$BASE_URL/auth/health_check" 200
assert_status "$BASE_URL/auth/authentik/health_check" 200
assert_status "$BASE_URL/" 200

# Protected endpoints should not be reachable without auth
assert_status "$BASE_URL/api/admin/users" 401 403
assert_status "$BASE_URL/api/llm/models" 401 403
assert_status "$BASE_URL/api/permissions/my-permissions" 401 403

if [ -n "$SYSTEM_ADMIN_API_KEY" ]; then
  assert_status_with_api_key "$BASE_URL/api/permissions/roles" 200
  assert_status_with_api_key "$BASE_URL/api/llm/models?active_only=true&model_type=llm" 200
else
  echo "WARNING: SYSTEM_ADMIN_API_KEY not set; skipping privileged smoke checks."
fi

if [ "$SMOKE_WIZARD" != "0" ] && [ -n "$SYSTEM_ADMIN_API_KEY" ]; then
  echo ""
  echo "Running wizard smoke test..."
  WIZARD_SCRIPT="${SCRIPT_DIR}/smoke_test_wizard.sh"
  if [ ! -f "$WIZARD_SCRIPT" ]; then
    WIZARD_SCRIPT="$DEPLOY_PATH/scripts/smoke_test_wizard.sh"
  fi
  if [ -f "$WIZARD_SCRIPT" ]; then
    BASE_URL="$BASE_URL" SYSTEM_ADMIN_API_KEY="$SYSTEM_ADMIN_API_KEY" \
      bash "$WIZARD_SCRIPT"
  else
    echo "WARNING: smoke_test_wizard.sh not found; skipping."
  fi
else
  echo "Skipping wizard smoke test (SMOKE_WIZARD=0 or no API key)"
fi

# --- Evaluation Pipeline Smoke Test ---
SMOKE_EVALUATION="${SMOKE_EVALUATION:-1}"
if [ "$SMOKE_EVALUATION" != "0" ] && [ -n "$SYSTEM_ADMIN_API_KEY" ]; then
  echo ""
  echo "Running evaluation pipeline smoke test..."
  EVAL_SCRIPT="${SCRIPT_DIR}/smoke_test_evaluation.sh"
  if [ ! -f "$EVAL_SCRIPT" ]; then
    EVAL_SCRIPT="$DEPLOY_PATH/scripts/ci/smoke_test_evaluation.sh"
  fi
  if [ -f "$EVAL_SCRIPT" ]; then
    BASE_URL="$BASE_URL" SYSTEM_ADMIN_API_KEY="$SYSTEM_ADMIN_API_KEY" \
      bash "$EVAL_SCRIPT"
  else
    echo "WARNING: smoke_test_evaluation.sh not found; skipping."
  fi
else
  echo "Skipping evaluation smoke test (SMOKE_EVALUATION=0 or no API key)"
fi

# --- Prompt Engineering Smoke Test ---
SMOKE_PROMPT_ENG="${SMOKE_PROMPT_ENG:-1}"
if [ "$SMOKE_PROMPT_ENG" != "0" ] && [ -n "$SYSTEM_ADMIN_API_KEY" ]; then
  echo ""
  echo "Running prompt engineering smoke test..."
  PROMPT_SCRIPT="${SCRIPT_DIR}/smoke_test_prompt_eng.sh"
  if [ ! -f "$PROMPT_SCRIPT" ]; then
    PROMPT_SCRIPT="$DEPLOY_PATH/scripts/ci/smoke_test_prompt_eng.sh"
  fi
  if [ -f "$PROMPT_SCRIPT" ]; then
    BASE_URL="$BASE_URL" SYSTEM_ADMIN_API_KEY="$SYSTEM_ADMIN_API_KEY" \
      bash "$PROMPT_SCRIPT"
  else
    echo "WARNING: smoke_test_prompt_eng.sh not found; skipping."
  fi
else
  echo "Skipping prompt engineering smoke test (SMOKE_PROMPT_ENG=0 or no API key)"
fi

# --- Batch Generation Smoke Test ---
SMOKE_GENERATION="${SMOKE_GENERATION:-1}"
if [ "$SMOKE_GENERATION" != "0" ] && [ -n "$SYSTEM_ADMIN_API_KEY" ]; then
  echo ""
  echo "Running batch generation smoke test..."
  GEN_SCRIPT="${SCRIPT_DIR}/smoke_test_generation.sh"
  if [ ! -f "$GEN_SCRIPT" ]; then
    GEN_SCRIPT="$DEPLOY_PATH/scripts/ci/smoke_test_generation.sh"
  fi
  if [ -f "$GEN_SCRIPT" ]; then
    BASE_URL="$BASE_URL" SYSTEM_ADMIN_API_KEY="$SYSTEM_ADMIN_API_KEY" \
      bash "$GEN_SCRIPT"
  else
    echo "WARNING: smoke_test_generation.sh not found; skipping."
  fi
else
  echo "Skipping batch generation smoke test (SMOKE_GENERATION=0 or no API key)"
fi

# --- LLM Response Smoke Test (Socket.IO test_prompt_stream) ---
SMOKE_LLM_RESPONSE="${SMOKE_LLM_RESPONSE:-1}"
if [ "$SMOKE_LLM_RESPONSE" != "0" ]; then
  echo ""
  echo "Running LLM response smoke test..."
  LLM_SCRIPT="${SCRIPT_DIR}/smoke_test_llm_response.py"
  if [ ! -f "$LLM_SCRIPT" ]; then
    LLM_SCRIPT="$DEPLOY_PATH/scripts/ci/smoke_test_llm_response.py"
  fi
  if [ -f "$LLM_SCRIPT" ]; then
    BASE_URL="$BASE_URL" SYSTEM_ADMIN_API_KEY="${SYSTEM_ADMIN_API_KEY:-}" \
      SMOKE_FORCE_HTTPS_HEADER="$SMOKE_FORCE_HTTPS_HEADER" \
      python3 "$LLM_SCRIPT"
  else
    echo "WARNING: smoke_test_llm_response.py not found; skipping."
  fi
else
  echo "Skipping LLM response smoke test (SMOKE_LLM_RESPONSE=0)"
fi

ROLLBACK_ENV="$DEPLOY_PATH/.deploy/rollback.env"
if [ -f "$ROLLBACK_ENV" ]; then
  set -a
  . "$ROLLBACK_ENV"
  set +a
  if [ -n "${DEPLOYED_COMMIT:-}" ]; then
    cat > "$DEPLOY_PATH/.deploy/last_good.env" <<EOF
LAST_GOOD_COMMIT=$DEPLOYED_COMMIT
LAST_GOOD_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF
  fi
fi

echo "Smoke tests completed successfully."
