#!/usr/bin/env bash
# =============================================================================
# LLARS Health Monitor
# =============================================================================
# Periodic health check triggered by llars-healthcheck.timer (every 3 min).
# Detects and recovers from container crashes or stuck containers at runtime,
# not just at boot.
#
# Checks:
#   1. Critical containers are running (nginx, flask, db, frontend)
#   2. HTTP health endpoint is reachable
#   3. If not: restart stopped/crashed containers, force-start stuck ones
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

# Compose command built from LLARS_ROOT
COMPOSE_BASE="${LLARS_ROOT}/docker-compose.yml"
COMPOSE_PROD="${LLARS_ROOT}/docker-compose.prod.yml"

COMPOSE_CMD="docker compose -f ${COMPOSE_BASE}"
[ -f "$COMPOSE_PROD" ] && COMPOSE_CMD="${COMPOSE_CMD} -f ${COMPOSE_PROD}"

# Health endpoint: nginx listens on :80 in production
HEALTH_URL="http://127.0.0.1:80/api/health"
CRITICAL_CONTAINERS="llars_nginx_service llars_flask_service llars_db_service llars_frontend_service"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] HEALTHCHECK: $*"; }

# Quick check: is the site reachable? If yes, nothing to do.
if curl -fsS -o /dev/null --max-time 10 "$HEALTH_URL" 2>/dev/null; then
    exit 0
fi

# Site not reachable — investigate
log "Health check failed for ${HEALTH_URL}. Investigating..."

NEEDS_RECOVERY=false

for container in $CRITICAL_CONTAINERS; do
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
            log "${container} does not exist — running compose up..."
            $COMPOSE_CMD up -d 2>&1 || true
            NEEDS_RECOVERY=true
            break
            ;;
    esac
done

if [ "$NEEDS_RECOVERY" = false ]; then
    # All containers running but site unreachable — likely internal issue
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
