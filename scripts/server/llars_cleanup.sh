#!/usr/bin/env bash
# =============================================================================
# LLARS Docker Cleanup
# =============================================================================
# Removes unused Docker resources to prevent disk space buildup from
# repeated builds and deployments.
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

# Report disk usage
DOCKER_USAGE=$(docker system df --format 'Images: {{.Size}} ({{.Reclaimable}} reclaimable)' 2>/dev/null | head -1 || echo "unknown")
DISK_USAGE=$(df -h / 2>/dev/null | awk 'NR==2{print $3 " used / " $2 " total (" $5 " used)"}' || echo "unknown")

log "Docker: ${DOCKER_USAGE}"
log "Disk:   ${DISK_USAGE}"
log "Cleanup complete."
