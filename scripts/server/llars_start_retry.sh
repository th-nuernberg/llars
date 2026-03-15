#!/usr/bin/env bash
# =============================================================================
# LLARS Startup with Retry & Force-Start
# =============================================================================
# Replaces the simple "docker compose up -d" in llars.service with a resilient
# startup that handles transient failures (unhealthy dependencies, slow DB, etc).
#
# Strategy:
#   1. Run docker compose up -d
#   2. Wait for nginx (the final link in the dependency chain) to be running
#   3. If nginx is stuck in "Created" (depends_on health failure), force-start it
#   4. Retry with exponential backoff up to MAX_RETRIES times
#
# Why force-start works:
#   docker compose up -d honours depends_on conditions and blocks if a dependency
#   is unhealthy. But "docker start <container>" bypasses depends_on entirely.
#   By the time we force-start, the dependency is likely healthy (just slow).
#
# Path resolution: derives LLARS_ROOT from own location (scripts/server/ → ../../)
# Usage: Called by llars.service ExecStart, or: LLARS_ROOT=/var/llars bash llars_start_retry.sh
# =============================================================================

set -uo pipefail

# --- Resolve LLARS_ROOT from script location or environment ---
if [ -z "${LLARS_ROOT:-}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LLARS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

MAX_RETRIES="${LLARS_START_RETRIES:-5}"
RETRY_DELAY=15

# Compose files: base + prod override (both must exist in LLARS_ROOT)
COMPOSE_BASE="${LLARS_ROOT}/docker-compose.yml"
COMPOSE_PROD="${LLARS_ROOT}/docker-compose.prod.yml"

if [ ! -f "$COMPOSE_BASE" ]; then
    echo "ERROR: docker-compose.yml not found at ${COMPOSE_BASE}"
    exit 1
fi

COMPOSE_CMD="docker compose -f ${COMPOSE_BASE}"
[ -f "$COMPOSE_PROD" ] && COMPOSE_CMD="${COMPOSE_CMD} -f ${COMPOSE_PROD}"

CRITICAL_CONTAINER="llars_nginx_service"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

is_nginx_running() {
    docker ps --format '{{.Names}}' | grep -q "^${CRITICAL_CONTAINER}$"
}

force_start_stuck_containers() {
    # Find LLARS containers stuck in "Created" state (never started due to depends_on)
    local stuck
    stuck=$(docker ps -a --filter "status=created" --format '{{.Names}}' | grep '^llars_' || true)

    if [ -n "$stuck" ]; then
        log "Force-starting stuck containers: $(echo "$stuck" | tr '\n' ' ')"
        echo "$stuck" | xargs docker start 2>&1 || true
        sleep 10
    fi
}

# --- Main loop ---

log "LLARS_ROOT=${LLARS_ROOT}"

for attempt in $(seq 1 "$MAX_RETRIES"); do
    log "Attempt ${attempt}/${MAX_RETRIES}: starting LLARS stack..."

    # Standard compose up (may fail if healthchecks are slow)
    $COMPOSE_CMD up -d 2>&1 || true

    # Give containers time to settle (healthchecks need start_period + interval)
    sleep 20

    if is_nginx_running; then
        log "LLARS is up — nginx running."
        exit 0
    fi

    # Nginx not running — likely blocked by depends_on. Force-start stuck containers.
    log "nginx not running after compose up. Checking for stuck containers..."
    force_start_stuck_containers

    if is_nginx_running; then
        log "LLARS is up after force-start — nginx running."
        exit 0
    fi

    if [ "$attempt" -lt "$MAX_RETRIES" ]; then
        log "Retrying in ${RETRY_DELAY}s..."
        sleep "$RETRY_DELAY"
        RETRY_DELAY=$((RETRY_DELAY * 2))
    fi
done

log "ERROR: LLARS failed to start after ${MAX_RETRIES} attempts. nginx is not running."
log "Manual intervention required: docker start ${CRITICAL_CONTAINER}"
exit 1
