#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
BASE_URL="${BASE_URL:-http://localhost}"
ENV_FILE="$DEPLOY_PATH/.env"
SMOKE_WIZARD="${SMOKE_WIZARD:-1}"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

SYSTEM_ADMIN_API_KEY="${SYSTEM_ADMIN_API_KEY:-}"
DB_USER="${MYSQL_USER:-dev_user}"
DB_PASS="${MYSQL_PASSWORD:-dev_password_change_me}"
DB_NAME="${MYSQL_DATABASE:-database_llars}"

assert_status() {
  local url="$1"
  shift
  local expected=("$@");
  local code
  # Follow redirects (-L) to get final status code
  code=$(curl -sL -o /dev/null -w "%{http_code}" "$url" || true)

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
  code=$(curl -sL -o /dev/null -w "%{http_code}" -H "X-API-Key: $SYSTEM_ADMIN_API_KEY" "$url" || true)

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

  local columns
  columns=$(docker exec llars_db_service \
    mariadb -N -u "$DB_USER" "-p$DB_PASS" "$DB_NAME" \
    -e "SHOW COLUMNS FROM system_settings;" 2>/dev/null | awk '{print $1}')

  if [ -z "$columns" ]; then
    echo "ERROR: Could not read columns from system_settings."
    return 1
  fi

  local required_columns=(
    "default_referral_role"
    "communication_enabled"
    "ai_assistant_enabled"
    "ai_assistant_color"
    "ai_assistant_username"
  )

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
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
