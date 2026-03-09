#!/usr/bin/env bash
# =============================================================================
# Health Check Waiter
# =============================================================================
# Waits for a service to become healthy by polling a URL.
# Used by deploy and smoke test scripts.
#
# Usage: wait_for_health.sh <url> [max_seconds] [interval]
#   url          - URL to check (e.g., http://localhost/auth/health_check)
#   max_seconds  - Maximum wait time (default: 180)
#   interval     - Polling interval in seconds (default: 5)
#
# Exit codes: 0 = healthy, 1 = timeout
# =============================================================================

set -euo pipefail

URL="${1:?Usage: wait_for_health.sh <url> [max_seconds] [interval]}"
MAX_WAIT="${2:-180}"
INTERVAL="${3:-5}"

ELAPSED=0

while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
  if curl -fsS -o /dev/null --max-time 10 "$URL" 2>/dev/null; then
    echo "Service healthy after ${ELAPSED}s: $URL"
    exit 0
  fi

  ELAPSED=$((ELAPSED + INTERVAL))
  echo "Waiting... (${ELAPSED}/${MAX_WAIT}s) $URL"
  sleep "$INTERVAL"
done

echo "ERROR: Service not healthy after ${MAX_WAIT}s: $URL"
exit 1
