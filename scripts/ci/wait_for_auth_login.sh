#!/usr/bin/env bash
# =============================================================================
# Auth Login Readiness Waiter
# =============================================================================
# Waits until the LLARS login endpoint can complete a real authentication flow.
#
# Usage:
#   wait_for_auth_login.sh <base_url> <username> <password> [max_seconds] [interval]
# =============================================================================

set -euo pipefail

BASE_URL="${1:?Usage: wait_for_auth_login.sh <base_url> <username> <password> [max_seconds] [interval]}"
USERNAME="${2:?Usage: wait_for_auth_login.sh <base_url> <username> <password> [max_seconds] [interval]}"
PASSWORD="${3:?Usage: wait_for_auth_login.sh <base_url> <username> <password> [max_seconds] [interval]}"
MAX_WAIT="${4:-180}"
INTERVAL="${5:-15}"

BASE_URL="${BASE_URL%/}"
ELAPSED=0

probe_login() {
  local response_file http_code payload
  response_file="$(mktemp)"

  payload="$(
    AUTH_READY_USERNAME="$USERNAME" \
    AUTH_READY_PASSWORD="$PASSWORD" \
    python3 - <<'PY'
import json
import os

print(json.dumps({
    "username": os.environ["AUTH_READY_USERNAME"],
    "password": os.environ["AUTH_READY_PASSWORD"],
}))
PY
  )"

  http_code="$(
    curl -sS -o "$response_file" -w "%{http_code}" \
      -H "Content-Type: application/json" \
      --data-binary "$payload" \
      --max-time 20 \
      "${BASE_URL}/auth/login" || true
  )"

  if [ "$http_code" = "200" ]; then
    rm -f "$response_file"
    return 0
  fi

  local body_preview
  body_preview="$(tr '\n' ' ' < "$response_file" | head -c 160)"
  rm -f "$response_file"

  if [ -n "$body_preview" ]; then
    echo "Login not ready yet: HTTP ${http_code} ${body_preview}"
  else
    echo "Login not ready yet: HTTP ${http_code}"
  fi
  return 1
}

while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
  if probe_login; then
    echo "Login ready after ${ELAPSED}s: ${BASE_URL}/auth/login"
    exit 0
  fi

  ELAPSED=$((ELAPSED + INTERVAL))
  echo "Waiting... (${ELAPSED}/${MAX_WAIT}s) ${BASE_URL}/auth/login"
  sleep "$INTERVAL"
done

echo "ERROR: Login not ready after ${MAX_WAIT}s: ${BASE_URL}/auth/login"
exit 1
