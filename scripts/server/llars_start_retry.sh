#!/usr/bin/env bash
# =============================================================================
# LLARS Startup with Retry & Force-Start
# =============================================================================
# Ensures LLARS is fully running after a server reboot. Replaces the simple
# "docker compose up -d" with intelligent retry logic.
#
# Design principle:
#   Docker's restart policy (unless-stopped) handles most cases automatically.
#   This script is the FALLBACK for when auto-restart isn't enough:
#   - Containers stuck in "Created" (depends_on health failures)
#   - Containers that exited and didn't auto-restart
#   - nginx not running for any reason
#
# Blue-Green awareness:
#   Detects if blue-green is active from .deploy/active_color.
#   In blue-green mode: uses "docker start" for existing containers instead of
#   "docker compose up" to avoid project-name conflicts.
#   In standard mode: uses "docker compose up -d" normally.
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
[[ "$MAX_RETRIES" =~ ^[0-9]+$ ]] || MAX_RETRIES=5

RETRY_DELAY=15
DEPLOY_STATE_DIR="${LLARS_ROOT}/.deploy"
LOCK_FILE="${DEPLOY_STATE_DIR}/llars.lock"

COMPOSE_BASE="${LLARS_ROOT}/docker-compose.yml"
COMPOSE_PROD="${LLARS_ROOT}/docker-compose.prod.yml"

if [ ! -f "$COMPOSE_BASE" ]; then
    echo "ERROR: docker-compose.yml not found at ${COMPOSE_BASE}"
    exit 1
fi

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] START: $*"; }

# --- Detect if blue-green deployment is active ---
is_bluegreen() {
    [ -f "${DEPLOY_STATE_DIR}/active_color" ] && [ -s "${DEPLOY_STATE_DIR}/active_color" ]
}

get_active_color() {
    cat "${DEPLOY_STATE_DIR}/active_color" 2>/dev/null
}

# --- Check if the site is reachable (the ultimate success condition) ---
is_site_up() {
    # Read port from .env if available, otherwise try common ports
    local port=""
    if [ -f "${LLARS_ROOT}/.env" ]; then
        port=$(grep '^NGINX_EXTERNAL_PORT=' "${LLARS_ROOT}/.env" 2>/dev/null | cut -d= -f2- || true)
    fi

    # Try configured port, then common fallbacks
    for p in ${port:-80} 80 55080; do
        # Try /api/health first, then root (staging nginx may not proxy /api)
        if curl -fsS -o /dev/null --max-time 5 "http://127.0.0.1:${p}/api/health" 2>/dev/null; then
            return 0
        fi
        if curl -fsS -o /dev/null --max-time 5 "http://127.0.0.1:${p}/" 2>/dev/null; then
            return 0
        fi
    done

    # Fallback: check if key containers are running and healthy
    if is_bluegreen; then
        local color
        color=$(get_active_color)
        if docker inspect --format '{{.State.Health.Status}}' "llars_flask_${color}" 2>/dev/null | grep -q 'healthy'; then
            log "Site URL not reachable, but active flask container is healthy. Considering UP."
            return 0
        fi
    fi

    return 1
}

# --- Start all stopped/created LLARS containers (safe for any mode) ---
start_existing_containers() {
    local stopped
    stopped=$(docker ps -a --filter "status=exited" --filter "status=created" \
        --format '{{.Names}}' | grep '^llars_' || true)

    if [ -n "$stopped" ]; then
        log "Starting existing containers: $(echo "$stopped" | tr '\n' ' ')"
        echo "$stopped" | xargs docker start 2>&1 || true
    fi
}

# --- Bring up base infrastructure (DB, Redis, Authentik, etc.) ---
# After a reboot, containers with restart:no are REMOVED entirely (not just stopped).
# We use docker compose (BASE file only, no prod override) to recreate infrastructure,
# but SKIP app services that have blue-green variants (flask, worker, frontend, yjs, supervisor).
# nginx-service is also skipped here because compose depends_on chains would block on
# frontend_service healthcheck. Instead, nginx is force-started separately below.
# Using --scale=0: robust against new infrastructure services being added to compose.
start_infrastructure() {
    log "Starting infrastructure via docker compose (base file, skipping app services)..."
    docker compose -f "${COMPOSE_BASE}" up -d \
        --scale backend-flask-service=0 \
        --scale backend-worker-service=0 \
        --scale frontend-vue-service=0 \
        --scale backend-supervisor-service=0 \
        --scale yjs-service=0 \
        --scale nginx-service=0 \
        2>&1 || true

    # Create nginx container from prod override (port 80/443) WITHOUT starting it.
    # Must use --no-deps to skip depends_on chain (frontend_service healthcheck blocks).
    # start_existing_containers() will docker-start it in the next step.
    log "Ensuring nginx container exists (prod override for port 80/443)..."
    local compose_cmd="docker compose -f ${COMPOSE_BASE}"
    [ -f "$COMPOSE_PROD" ] && compose_cmd="${compose_cmd} -f ${COMPOSE_PROD}"
    $compose_cmd up --no-start --no-deps nginx-service 2>&1 || true

    # Give infrastructure containers time to become healthy (especially DB)
    log "Waiting 15s for infrastructure to initialize..."
    sleep 15
}

# --- Standard mode: use docker compose up ---
start_standard() {
    local cmd="docker compose -f ${COMPOSE_BASE}"
    [ -f "$COMPOSE_PROD" ] && cmd="${cmd} -f ${COMPOSE_PROD}"
    log "Standard mode: running docker compose up -d..."
    $cmd up -d 2>&1 || true
}

# --- Signal handler for clean interruption ---
trap 'log "Interrupted (signal received)"; exit 130' INT TERM

# --- Main ---

mkdir -p "$DEPLOY_STATE_DIR" 2>/dev/null || true

# Wait for any in-progress deployment to finish
if [ -f "$LOCK_FILE" ]; then
    log "Deploy lock exists. Waiting up to 5 minutes..."
    for _ in $(seq 1 30); do
        [ ! -f "$LOCK_FILE" ] && break
        sleep 10
    done
fi

if is_bluegreen; then
    MODE="bluegreen"
    ACTIVE_COLOR=$(get_active_color)
    log "LLARS_ROOT=${LLARS_ROOT} MODE=${MODE} ACTIVE_COLOR=${ACTIVE_COLOR}"
else
    MODE="standard"
    log "LLARS_ROOT=${LLARS_ROOT} MODE=${MODE}"
fi

for attempt in $(seq 1 "$MAX_RETRIES"); do
    log "Attempt ${attempt}/${MAX_RETRIES}: starting LLARS stack..."

    if [ "$MODE" = "bluegreen" ]; then
        # Blue-green two-step startup:
        # 1. Infrastructure (DB, Redis, Authentik, etc.) — these have restart:no and
        #    are REMOVED after reboot. Base compose file recreates them safely.
        # 2. App containers (flask, worker, frontend, yjs, supervisor) — these exist with
        #    blue/green suffixed names. Use "docker start" to avoid compose project-
        #    name conflicts.
        start_infrastructure
        start_existing_containers
    else
        # Standard: compose up handles creation + start
        start_standard
        # Also force-start anything stuck in "Created" (depends_on failures)
        start_existing_containers
    fi

    # Give containers time to settle (healthchecks have start_period + intervals)
    sleep 20

    if is_site_up; then
        log "LLARS is up — site reachable."
        exit 0
    fi

    # Not up yet. Check for specific issues.
    log "Site not reachable. Container status:"
    docker ps -a --filter "name=llars_" --format '  {{.Names}}: {{.Status}}' | head -20 >&2

    if [ "$attempt" -lt "$MAX_RETRIES" ]; then
        log "Retrying in ${RETRY_DELAY}s..."
        sleep "$RETRY_DELAY"
        RETRY_DELAY=$((RETRY_DELAY * 2))
    fi
done

log "ERROR: LLARS failed to start after ${MAX_RETRIES} attempts."
log "Container status:"
docker ps -a --filter "name=llars_" --format '  {{.Names}}: {{.Status}}' >&2
exit 1
