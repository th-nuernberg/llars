#!/usr/bin/env bash
# =============================================================================
# LLARS Health Monitor
# =============================================================================
# Periodic health check triggered by llars-healthcheck.timer (every 3 min).
# Detects and recovers from container crashes or stuck containers at runtime.
#
# Blue-Green awareness:
#   Reads .deploy/active_color to check the correct container names.
#   Will NOT start containers from the inactive color.
#   Skips recovery if a deployment is in progress (lock file).
#
# Deploy safety:
#   Uses flock to prevent conflicts with concurrent deployments.
#   If deploy_bluegreen.sh is running, the healthcheck exits silently.
#
# Path resolution: derives LLARS_ROOT from own location (scripts/server/ → ../../)
# Exit codes: 0 = healthy or recovered, 1 = unrecoverable (needs manual fix)
# =============================================================================

set -uo pipefail

# --- Resolve LLARS_ROOT from script location or environment ---
if [ -z "${LLARS_ROOT:-}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LLARS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

DEPLOY_STATE_DIR="${LLARS_ROOT}/.deploy"
LOCK_FILE="${DEPLOY_STATE_DIR}/llars.lock"

# Health endpoint port: read from .env or default to 80 (production)
if [ -f "${LLARS_ROOT}/.env" ]; then
    HEALTH_PORT=$(grep '^NGINX_EXTERNAL_PORT=' "${LLARS_ROOT}/.env" 2>/dev/null | cut -d= -f2- || echo "80")
    [ -z "$HEALTH_PORT" ] && HEALTH_PORT=80
else
    HEALTH_PORT=80
fi
HEALTH_URL="http://127.0.0.1:${HEALTH_PORT}/api/health"

# All output to stderr so systemd journal captures recovery messages
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] HEALTHCHECK: $*" >&2; }

# --- Pre-checks ---

# Skip if Docker daemon is not ready (e.g. Docker restarting, updating)
if ! docker info >/dev/null 2>&1; then
    exit 0
fi

# Skip if a deployment is in progress (lock file held by deploy_bluegreen.sh)
if [ -f "$LOCK_FILE" ]; then
    exit 0
fi

# --- Quick check: is the site reachable? If yes, nothing to do. ---
if curl -fsS -o /dev/null --max-time 10 "$HEALTH_URL" 2>/dev/null; then
    exit 0
fi

# Site not reachable — investigate
log "Health check failed for ${HEALTH_URL}. Investigating..."

# --- Detect blue-green mode and get correct container names ---
detect_containers() {
    # nginx is always the same
    echo "llars_nginx_service"

    if [ -f "${DEPLOY_STATE_DIR}/active_color" ]; then
        local color
        color=$(cat "${DEPLOY_STATE_DIR}/active_color" 2>/dev/null || echo "")
        if [ -n "$color" ]; then
            # Blue-green mode: check active color containers
            echo "llars_flask_${color}"
            echo "llars_frontend_${color}"
            echo "llars_yjs_${color}"
            return
        fi
    fi

    # Standard mode (no blue-green)
    echo "llars_flask_service"
    echo "llars_frontend_service"
    echo "llars_db_service"
}

NEEDS_RECOVERY=false
CONTAINERS=$(detect_containers)

for container in $CONTAINERS; do
    state=$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || echo "missing")

    case "$state" in
        running)
            ;;
        created)
            log "${container} is stuck in 'created' state — force-starting..."
            docker start "$container" 2>&1 || true
            NEEDS_RECOVERY=true
            ;;
        exited|dead)
            log "${container} is ${state} — restarting..."
            docker start "$container" 2>&1 || true
            NEEDS_RECOVERY=true
            ;;
        restarting)
            log "${container} is in restart loop — waiting..."
            NEEDS_RECOVERY=true
            ;;
        missing)
            # Container doesn't exist — this requires a full compose up.
            # Only safe in standard mode. In blue-green, the deploy script handles this.
            if [ ! -f "${DEPLOY_STATE_DIR}/active_color" ]; then
                log "${container} does not exist — running compose up..."
                local compose_cmd="docker compose -f ${LLARS_ROOT}/docker-compose.yml"
                [ -f "${LLARS_ROOT}/docker-compose.prod.yml" ] && compose_cmd="${compose_cmd} -f ${LLARS_ROOT}/docker-compose.prod.yml"
                $compose_cmd up -d 2>&1 || true
                NEEDS_RECOVERY=true
                break
            else
                log "${container} does not exist (blue-green mode) — skipping compose up. Manual deploy needed."
                NEEDS_RECOVERY=true
            fi
            ;;
    esac
done

# Also check shared infrastructure that never changes name
for container in llars_db_service llars_redis_service; do
    state=$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || echo "missing")
    if [ "$state" = "exited" ] || [ "$state" = "dead" ] || [ "$state" = "created" ]; then
        log "Infrastructure container ${container} is ${state} — starting..."
        docker start "$container" 2>&1 || true
        NEEDS_RECOVERY=true
    fi
done

if [ "$NEEDS_RECOVERY" = false ]; then
    # All containers running but site unreachable — likely internal issue (nginx config, network)
    log "All containers running but site unreachable. Restarting nginx..."
    docker restart llars_nginx_service 2>&1 || true
fi

# Wait and verify recovery
sleep 15

if curl -fsS -o /dev/null --max-time 10 "$HEALTH_URL" 2>/dev/null; then
    log "Recovery successful — site is back online."
    exit 0
fi

log "WARNING: Recovery attempt failed. Site still unreachable. Manual intervention may be needed."
exit 1
