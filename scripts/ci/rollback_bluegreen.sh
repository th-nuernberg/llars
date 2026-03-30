#!/usr/bin/env bash
# =============================================================================
# LLARS Blue-Green Instant Rollback
# =============================================================================
# Switches nginx back to the previous color for instant rollback (~2 seconds).
# Falls back to rollback_production.sh (DB restore + rebuild) if previous
# containers aren't available.
#
# Usage: bash scripts/ci/rollback_bluegreen.sh
#
# LIMITATION: This rollback only switches nginx traffic. It does NOT revert
# database migrations. If the failed deploy included forward-only schema
# changes, the previous containers may encounter errors against the new schema.
# In that case, use rollback_production.sh for a full DB restore.
# =============================================================================

set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
STATE_DIR="$DEPLOY_PATH/.deploy"

cd "$DEPLOY_PATH"

ensure_production_nginx() {
  local state
  state=$(docker inspect --format='{{.State.Status}}' llars_nginx_service 2>/dev/null || echo "not_found")
  if [ "$state" = "running" ]; then
    return 0
  fi

  ensure_shared_authentik_services
  echo "llars_nginx_service is not running (status: $state). Starting production nginx..."
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps nginx-service

  local elapsed=0
  local max_wait=60
  while [ "$elapsed" -lt "$max_wait" ]; do
    state=$(docker inspect --format='{{.State.Status}}' llars_nginx_service 2>/dev/null || echo "not_found")
    if [ "$state" = "running" ]; then
      echo "llars_nginx_service started successfully."
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done

  echo "ERROR: llars_nginx_service did not start."
  docker ps -a --filter "name=llars_nginx_service" --format "table {{.Names}}\t{{.Status}}" || true
  return 1
}

wait_for_container_health() {
  local container="$1"
  local max_wait="${2:-180}"
  local interval="${3:-5}"
  local elapsed=0

  echo "Waiting for $container to be healthy..."
  while [ "$elapsed" -lt "$max_wait" ]; do
    local health
    health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "not_found")

    if [ "$health" = "healthy" ]; then
      echo "$container healthy after ${elapsed}s"
      return 0
    elif [ "$health" = "not_found" ]; then
      echo "ERROR: Container $container not found"
      return 1
    fi

    elapsed=$((elapsed + interval))
    echo "  Waiting... (${elapsed}/${max_wait}s) status=$health"
    sleep "$interval"
  done

  echo "ERROR: $container not healthy after ${max_wait}s"
  docker ps -a --filter "name=^/${container}$" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" || true
  docker logs --tail 120 "$container" 2>&1 || true
  return 1
}

wait_for_container_running() {
  local container="$1"
  local max_wait="${2:-120}"
  local interval="${3:-5}"
  local elapsed=0

  echo "Waiting for $container to be running..."
  while [ "$elapsed" -lt "$max_wait" ]; do
    local state
    state=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")

    if [ "$state" = "running" ]; then
      echo "$container running after ${elapsed}s"
      return 0
    elif [ "$state" = "not_found" ]; then
      echo "ERROR: Container $container not found"
      return 1
    fi

    elapsed=$((elapsed + interval))
    echo "  Waiting... (${elapsed}/${max_wait}s) status=$state"
    sleep "$interval"
  done

  echo "ERROR: $container not running after ${max_wait}s"
  docker ps -a --filter "name=^/${container}$" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" || true
  docker logs --tail 120 "$container" 2>&1 || true
  return 1
}

ensure_shared_authentik_services() {
  echo "Ensuring shared Authentik services are running..."
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d authentik-db authentik-redis authentik-server authentik-worker
  wait_for_container_health "llars_authentik_db" 180 5
  wait_for_container_health "llars_authentik_redis" 120 5
  wait_for_container_health "llars_authentik_server" 240 5
  wait_for_container_running "llars_authentik_worker" 120 5
}

# =============================================================================
# Read state
# =============================================================================

ACTIVE=$(cat "$STATE_DIR/active_color" 2>/dev/null || echo "")
PREVIOUS=$(cat "$STATE_DIR/previous_color" 2>/dev/null || echo "")

if [ -z "$PREVIOUS" ]; then
  echo "ERROR: No previous color found in $STATE_DIR/previous_color"
  echo "Cannot perform instant rollback. Falling back to full rollback..."
  exit 1
fi

if [ -z "$ACTIVE" ]; then
  echo "ERROR: No active color found. Blue-green not initialized."
  exit 1
fi

echo "=== LLARS Blue-Green Instant Rollback ==="
echo "Current active: $ACTIVE"
echo "Rolling back to: $PREVIOUS"

PREVIOUS_WORKER_CONTAINER="llars_worker_${PREVIOUS}"
ACTIVE_WORKER_CONTAINER="llars_worker_${ACTIVE}"

# =============================================================================
# Verify previous containers are still running
# =============================================================================

echo ""
echo "[1/5] Verifying $PREVIOUS web containers..."

ALL_RUNNING=true
for svc in flask frontend yjs supervisor; do
  local_container="llars_${svc}_${PREVIOUS}"
  status=$(docker inspect --format='{{.State.Status}}' "$local_container" 2>/dev/null || echo "not_found")
  if [ "$status" = "running" ]; then
    echo "  $local_container: running"
  else
    echo "  $local_container: $status"
    ALL_RUNNING=false
  fi
done

if [ "$ALL_RUNNING" != "true" ]; then
  echo ""
  echo "ERROR: Not all $PREVIOUS containers are running."
  echo "Cannot perform instant rollback. Falling back to full rollback..."
  exit 1
fi

# Verify flask health
flask_health=$(docker inspect --format='{{.State.Health.Status}}' "llars_flask_${PREVIOUS}" 2>/dev/null || echo "unknown")
if [ "$flask_health" != "healthy" ]; then
  echo ""
  echo "ERROR: llars_flask_${PREVIOUS} is not healthy (status: $flask_health)"
  echo "Cannot perform instant rollback. Falling back to full rollback..."
  exit 1
fi

previous_worker_status=$(docker inspect --format='{{.State.Status}}' "$PREVIOUS_WORKER_CONTAINER" 2>/dev/null || echo "not_found")
echo "  $PREVIOUS_WORKER_CONTAINER: $previous_worker_status"

# =============================================================================
# Hand worker ownership back to previous color
# =============================================================================

echo ""
echo "[2/5] Handing over worker ownership..."

active_worker_status=$(docker inspect --format='{{.State.Status}}' "$ACTIVE_WORKER_CONTAINER" 2>/dev/null || echo "not_found")
if [ "$active_worker_status" = "running" ]; then
  docker stop "$ACTIVE_WORKER_CONTAINER" >/dev/null
fi

if [ "$previous_worker_status" = "not_found" ]; then
  echo "WARNING: $PREVIOUS_WORKER_CONTAINER does not exist. Continuing rollback without a background worker."
else
  docker start "$PREVIOUS_WORKER_CONTAINER" >/dev/null || true
  previous_worker_health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$PREVIOUS_WORKER_CONTAINER" 2>/dev/null || echo "unknown")
  if [ "$previous_worker_health" != "none" ]; then
    elapsed=0
    max_wait=120
    while [ "$elapsed" -lt "$max_wait" ]; do
      previous_worker_health=$(docker inspect --format='{{.State.Health.Status}}' "$PREVIOUS_WORKER_CONTAINER" 2>/dev/null || echo "unknown")
      if [ "$previous_worker_health" = "healthy" ]; then
        echo "  $PREVIOUS_WORKER_CONTAINER: healthy"
        break
      fi
      sleep 5
      elapsed=$((elapsed + 5))
    done
    if [ "$previous_worker_health" != "healthy" ]; then
      echo "WARNING: $PREVIOUS_WORKER_CONTAINER did not become healthy (status: $previous_worker_health)"
    fi
  fi
fi

# =============================================================================
# Switch upstream back to previous color
# =============================================================================

echo ""
echo "[3/5] Updating upstream → $PREVIOUS"

CONF_FILE="$DEPLOY_PATH/docker/nginx/active_upstream.conf"
cat > "$CONF_FILE" <<CONF
# Blue-Green active upstream (managed by deploy_bluegreen.sh)
# DO NOT EDIT MANUALLY - updated by rollback_bluegreen.sh
# Active color: $PREVIOUS (ROLLBACK at $(date -u +"%Y-%m-%dT%H:%M:%SZ"))

upstream frontend {
    server llars_frontend_${PREVIOUS}:5173;
}

upstream backend {
    server llars_flask_${PREVIOUS}:8081;
}

upstream yjs {
    server llars_yjs_${PREVIOUS}:8082;
}
CONF

# =============================================================================
# Reload nginx
# =============================================================================

echo ""
echo "[4/5] Reloading nginx..."

ensure_production_nginx
ensure_shared_authentik_services

if docker exec llars_nginx_service nginx -t 2>&1; then
  docker exec llars_nginx_service nginx -s reload
  echo "Nginx reloaded successfully"
else
  echo "ERROR: Nginx config test failed!"
  exit 1
fi

# =============================================================================
# Update state files
# =============================================================================

echo ""
echo "[5/5] Updating state..."

echo "$PREVIOUS" > "$STATE_DIR/active_color"
echo "$ACTIVE" > "$STATE_DIR/previous_color"
rm -f "$STATE_DIR/pending_switch.env" 2>/dev/null || true

ACTIVE_COMMIT_FILE="$STATE_DIR/active_commit"
PREVIOUS_COMMIT_FILE="$STATE_DIR/previous_commit"
if [ -f "$ACTIVE_COMMIT_FILE" ] && [ -f "$PREVIOUS_COMMIT_FILE" ]; then
  ACTIVE_COMMIT=$(cat "$ACTIVE_COMMIT_FILE" 2>/dev/null || echo "")
  PREVIOUS_COMMIT=$(cat "$PREVIOUS_COMMIT_FILE" 2>/dev/null || echo "")
  if [ -n "$PREVIOUS_COMMIT" ]; then
    echo "$PREVIOUS_COMMIT" > "$ACTIVE_COMMIT_FILE"
  fi
  if [ -n "$ACTIVE_COMMIT" ]; then
    echo "$ACTIVE_COMMIT" > "$PREVIOUS_COMMIT_FILE"
  fi
fi

echo ""
echo "=== Rollback complete ==="
echo "Active: $PREVIOUS"
echo "Previous (failed): $ACTIVE (containers still running for debugging)"
echo ""
echo "Verify: curl -fsS http://localhost/auth/health_check"
