#!/usr/bin/env bash
# =============================================================================
# LLARS Nightly Maintenance (Docker cleanup + demo account lifecycle)
# =============================================================================
# Removes unused Docker resources to prevent disk space buildup from
# repeated builds and deployments, and runs the demo-account maintenance job.
#
# Triggered by llars-cleanup.timer (daily at 03:30) or manually.
# Safe to run at any time — only removes resources not used by running containers.
#
# What it cleans:
#   1. Dangling images (untagged, from old builds)
#   2. Stopped containers (exited, dead) older than 24h
#   3. Build cache older than 7 days
#   4. Unused networks (not attached to running containers)
#   5. Old DB backups (keeps newest 5)
#   6. Demo accounts: archives expired demo memberships and strips all
#      permissions from IJCAI conference accounts older than 7 days
#      (app/scripts/demo_cleanup.py — runs inside the active Flask container)
#
# Path resolution: derives LLARS_ROOT from own location (scripts/server/ → ../../)
# =============================================================================

set -uo pipefail

# --- Resolve LLARS_ROOT from script location or environment ---
if [ -z "${LLARS_ROOT:-}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LLARS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

BACKUP_DIR="${LLARS_ROOT}/backups"
# How many DB backups to keep
KEEP_BACKUPS="${LLARS_KEEP_BACKUPS:-5}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] CLEANUP: $*"; }

# Skip if Docker daemon is not ready
if ! docker info >/dev/null 2>&1; then
    log "Docker not ready, skipping cleanup."
    exit 0
fi

log "Starting Docker cleanup (LLARS_ROOT=${LLARS_ROOT})..."

# 1. Dangling images (untagged layers from old builds)
DANGLING=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l | tr -d ' ')
if [ "$DANGLING" -gt 0 ]; then
    log "Removing ${DANGLING} dangling images..."
    docker image prune -f 2>&1 | tail -1
fi

# 1b. Unused TAGGED images older than 7 days. Dangling-only pruning is not
#     enough: every deploy leaves the previous build as a tagged-but-unused
#     image, which filled the dev server's /var to 100% on 2026-08-16 (each
#     push to dev triggers a build). `image prune -a` only removes images no
#     container references, so the active AND the previous (rollback) color
#     stay — their containers exist.
log "Pruning unused tagged images older than 7 days..."
docker image prune -af --filter "until=168h" 2>&1 | tail -1

# 2. Stopped LLARS containers older than 24h
EXITED=$(docker ps -a --filter "status=exited" --filter "name=llars_" --format '{{.Names}}' 2>/dev/null || true)
if [ -n "$EXITED" ]; then
    # Only remove containers that have been stopped for >24h
    for container in $EXITED; do
        finished=$(docker inspect --format '{{.State.FinishedAt}}' "$container" 2>/dev/null || echo "")
        if [ -n "$finished" ]; then
            finished_epoch=$(date -d "$finished" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$finished" +%s 2>/dev/null || echo "0")
            now_epoch=$(date +%s)
            age_hours=$(( (now_epoch - finished_epoch) / 3600 ))
            if [ "$age_hours" -gt 24 ]; then
                log "Removing stopped container: ${container} (stopped ${age_hours}h ago)"
                docker rm "$container" 2>&1 || true
            fi
        fi
    done
fi

# 3. Build cache older than 7 days
log "Pruning build cache older than 7 days..."
docker builder prune -f --filter "until=168h" 2>&1 | tail -1

# 4. Unused networks (not attached to any running container)
UNUSED_NETS=$(docker network ls --filter "name=llars" --format '{{.Name}}' 2>/dev/null || true)
for net in $UNUSED_NETS; do
    # Only prune if no containers attached
    attached=$(docker network inspect "$net" --format '{{len .Containers}}' 2>/dev/null || echo "0")
    if [ "$attached" = "0" ]; then
        log "Removing unused network: ${net}"
        docker network rm "$net" 2>&1 || true
    fi
done

# 5. Old DB backups (keep newest KEEP_BACKUPS)
if [ -d "$BACKUP_DIR" ]; then
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.sql" -o -name "*.sql.gz" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$BACKUP_COUNT" -gt "$KEEP_BACKUPS" ]; then
        REMOVE_COUNT=$((BACKUP_COUNT - KEEP_BACKUPS))
        log "Removing ${REMOVE_COUNT} old backups (keeping newest ${KEEP_BACKUPS})..."
        find "$BACKUP_DIR" \( -name "*.sql" -o -name "*.sql.gz" \) -printf '%T+ %p\n' 2>/dev/null | \
            sort | head -n "$REMOVE_COUNT" | cut -d' ' -f2- | while read -r f; do
            log "  Deleting: $(basename "$f")"
            rm -f "$f"
        done
    fi
fi

# 6. Demo account maintenance (inside the ACTIVE flask container)
#    Expires demo memberships and IJCAI conference accounts (see
#    app/scripts/demo_cleanup.py). Purely best-effort: this script's job is
#    disk hygiene, so a missing container or a failing job must only warn —
#    never change the exit code (note the `set -uo pipefail` at the top; there
#    is no `-e`, but we still guard every command explicitly).
DEMO_CLEANUP_CONTAINER=""
ACTIVE_COLOR_FILE="${LLARS_ROOT}/.deploy/active_color"

container_running() {
    [ -n "$1" ] && [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || echo false)" = "true" ]
}

if [ -f "$ACTIVE_COLOR_FILE" ]; then
    ACTIVE_COLOR=$(tr -d '[:space:]' < "$ACTIVE_COLOR_FILE" 2>/dev/null || echo "")
    if container_running "llars_flask_${ACTIVE_COLOR}"; then
        DEMO_CLEANUP_CONTAINER="llars_flask_${ACTIVE_COLOR}"
    else
        log "WARNING: active color '${ACTIVE_COLOR}' has no running flask container, trying fallbacks..."
    fi
fi

# No/stale color file (dev machines use a different layout) — probe the known names.
if [ -z "$DEMO_CLEANUP_CONTAINER" ]; then
    for candidate in llars_flask_blue llars_flask_green llars_flask_service; do
        if container_running "$candidate"; then
            DEMO_CLEANUP_CONTAINER="$candidate"
            break
        fi
    done
fi

if [ -n "$DEMO_CLEANUP_CONTAINER" ]; then
    log "Running demo account maintenance in ${DEMO_CLEANUP_CONTAINER}..."
    if DEMO_OUTPUT=$(docker exec "$DEMO_CLEANUP_CONTAINER" python -m scripts.demo_cleanup 2>&1); then
        while IFS= read -r line; do
            [ -n "$line" ] && log "  ${line}"
        done <<< "$DEMO_OUTPUT"
    else
        log "WARNING: demo cleanup failed (non-fatal):"
        while IFS= read -r line; do
            [ -n "$line" ] && log "  ${line}"
        done <<< "$DEMO_OUTPUT"
    fi
else
    log "No running flask container found, skipping demo account maintenance."
fi

# Report disk usage
DOCKER_USAGE=$(docker system df --format 'Images: {{.Size}} ({{.Reclaimable}} reclaimable)' 2>/dev/null | head -1 || echo "unknown")
DISK_USAGE=$(df -h / 2>/dev/null | awk 'NR==2{print $3 " used / " $2 " total (" $5 " used)"}' || echo "unknown")

log "Docker: ${DOCKER_USAGE}"
log "Disk:   ${DISK_USAGE}"
log "Cleanup complete."
