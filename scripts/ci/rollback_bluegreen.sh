#!/usr/bin/env bash
# =============================================================================
# LLARS Blue-Green Instant Rollback
# =============================================================================
# Switches nginx back to the previous color for instant rollback (~2 seconds).
# Falls back to rollback_production.sh (DB restore + rebuild) if previous
# containers aren't available.
#
# Usage: bash scripts/ci/rollback_bluegreen.sh
# =============================================================================

set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
STATE_DIR="$DEPLOY_PATH/.deploy"

cd "$DEPLOY_PATH"

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

# =============================================================================
# Verify previous containers are still running
# =============================================================================

echo ""
echo "[1/4] Verifying $PREVIOUS containers..."

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

# =============================================================================
# Switch upstream back to previous color
# =============================================================================

echo ""
echo "[2/4] Updating upstream → $PREVIOUS"

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
echo "[3/4] Reloading nginx..."

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
echo "[4/4] Updating state..."

echo "$PREVIOUS" > "$STATE_DIR/active_color"
echo "$ACTIVE" > "$STATE_DIR/previous_color"

echo ""
echo "=== Rollback complete ==="
echo "Active: $PREVIOUS"
echo "Previous (failed): $ACTIVE (containers still running for debugging)"
echo ""
echo "Verify: curl -fsS http://localhost/auth/health_check"
