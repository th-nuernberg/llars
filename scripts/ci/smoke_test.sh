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

echo "Running basic smoke checks against $BASE_URL"

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

if [ "$SMOKE_WIZARD" != "0" ]; then
  echo "Running wizard smoke test"
  BASE_URL="$BASE_URL" SYSTEM_ADMIN_API_KEY="$SYSTEM_ADMIN_API_KEY" \
    bash "$DEPLOY_PATH/scripts/smoke_test_wizard.sh"
else
  echo "Skipping wizard smoke test (SMOKE_WIZARD=0)"
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
