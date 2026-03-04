#!/usr/bin/env bash
# =============================================================================
# LLARS Blue-Green Deployment
# =============================================================================
# Combined deploy script for blue-green production deployments.
#
# Modes:
#   deploy  - Build + start inactive color containers (staging)
#   switch  - Switch production nginx to inactive color (instant cutover)
#   status  - Show current blue-green state
#
# Usage:
#   bash scripts/ci/deploy_bluegreen.sh deploy   # Build + start inactive color
#   bash scripts/ci/deploy_bluegreen.sh switch    # Switch production traffic
#   bash scripts/ci/deploy_bluegreen.sh status    # Show state
#
# State files (.deploy/):
#   active_color    - Currently active color (blue|green)
#   previous_color  - Previously active color (for instant rollback)
#   rollback.env    - Commit + backup info for full rollback
# =============================================================================

set -euo pipefail

MODE="${1:-deploy}"
DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
BRANCH="${LLARS_PRODUCTION_BRANCH:-main}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="$DEPLOY_PATH/.deploy"
BACKUP_DIR="$DEPLOY_PATH/backups"

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.prod-bluegreen.yml"
BG_SERVICES="backend-flask-service frontend-vue-service yjs-service backend-supervisor-service"

# Mark deploy directory as safe for git
git config --global --add safe.directory "$DEPLOY_PATH" 2>/dev/null || true

cd "$DEPLOY_PATH"
mkdir -p "$STATE_DIR" "$BACKUP_DIR"

# =============================================================================
# Helper functions
# =============================================================================

get_active_color() {
  cat "$STATE_DIR/active_color" 2>/dev/null || echo ""
}

get_inactive_color() {
  local active
  active=$(get_active_color)
  if [ -z "$active" ]; then
    echo "blue"  # First deploy
  elif [ "$active" = "blue" ]; then
    echo "green"
  else
    echo "blue"
  fi
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
  return 1
}

update_upstream_conf() {
  local color="$1"
  local conf_file="$DEPLOY_PATH/docker/nginx/active_upstream.conf"

  cat > "$conf_file" <<CONF
# Blue-Green active upstream (managed by deploy_bluegreen.sh)
# DO NOT EDIT MANUALLY - updated by deploy_bluegreen.sh
# Active color: $color (updated at $(date -u +"%Y-%m-%dT%H:%M:%SZ"))

upstream frontend {
    server llars_frontend_${color}:5173;
}

upstream backend {
    server llars_flask_${color}:8081;
}

upstream yjs {
    server llars_yjs_${color}:8082;
}
CONF

  echo "Updated active_upstream.conf → $color"
}

reload_nginx() {
  echo "Reloading nginx..."
  if docker exec llars_nginx_service nginx -t 2>&1; then
    docker exec llars_nginx_service nginx -s reload
    echo "Nginx reloaded successfully"
  else
    echo "ERROR: Nginx config test failed!"
    return 1
  fi
}

save_state() {
  local new_active="$1"
  local old_active="$2"

  echo "$new_active" > "$STATE_DIR/active_color"
  if [ -n "$old_active" ]; then
    echo "$old_active" > "$STATE_DIR/previous_color"
  fi
}

# =============================================================================
# MODE: status
# =============================================================================

cmd_status() {
  echo "=== LLARS Blue-Green Status ==="
  local active
  active=$(get_active_color)
  local previous
  previous=$(cat "$STATE_DIR/previous_color" 2>/dev/null || echo "none")

  if [ -z "$active" ]; then
    echo "State: No blue-green deployment yet"
    echo "Next deploy will use: blue"
  else
    echo "Active color:   $active"
    echo "Previous color: $previous"

    echo ""
    echo "--- Blue containers ---"
    for svc in flask frontend yjs supervisor; do
      local status
      status=$(docker inspect --format='{{.State.Status}} (health: {{.State.Health.Status}})' "llars_${svc}_blue" 2>/dev/null || echo "not running")
      echo "  llars_${svc}_blue: $status"
    done

    echo ""
    echo "--- Green containers ---"
    for svc in flask frontend yjs supervisor; do
      local status
      status=$(docker inspect --format='{{.State.Status}} (health: {{.State.Health.Status}})' "llars_${svc}_green" 2>/dev/null || echo "not running")
      echo "  llars_${svc}_green: $status"
    done
  fi

  echo ""
  echo "--- Nginx upstream ---"
  cat "$DEPLOY_PATH/docker/nginx/active_upstream.conf" 2>/dev/null || echo "(not configured)"
}

# =============================================================================
# MODE: deploy (build + start inactive color)
# =============================================================================

cmd_deploy() {
  echo "=========================================="
  echo "=== LLARS Blue-Green Deploy ============="
  echo "=========================================="

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: $DEPLOY_PATH is not a git repository."
    exit 1
  fi

  if [ ! -f .env ]; then
    echo "ERROR: .env not found in $DEPLOY_PATH"
    exit 1
  fi

  set -a
  . ./.env
  set +a

  local active
  active=$(get_active_color)
  local deploy_color
  deploy_color=$(get_inactive_color)

  if [ -z "$active" ]; then
    echo "First blue-green deployment → deploying as '$deploy_color'"
  else
    echo "Active: $active → Deploying inactive: $deploy_color"
  fi

  # -----------------------------------------------------------------------
  # [1/6] DB Backup
  # -----------------------------------------------------------------------
  echo ""
  echo "[1/6] Creating pre-deploy backup..."
  local db_user="${MYSQL_USER:-dev_user}"
  local db_pass="${MYSQL_PASSWORD:-dev_password_change_me}"
  local db_name="${MYSQL_DATABASE:-database_llars}"
  local backup_file="$BACKUP_DIR/bluegreen_pre_deploy_$(date +%Y%m%d_%H%M%S).sql"

  if docker inspect -f '{{.State.Running}}' llars_db_service >/dev/null 2>&1; then
    if timeout 300 docker exec llars_db_service mariadb-dump -u "$db_user" "-p$db_pass" --single-transaction --quick "$db_name" > "$backup_file" 2>/dev/null; then
      echo "Backup: $(du -h "$backup_file" | cut -f1)"
    else
      echo "WARNING: Backup failed, continuing."
      rm -f "$backup_file"
      backup_file=""
    fi
  else
    echo "WARNING: DB not running, skipping backup."
    backup_file=""
  fi

  # -----------------------------------------------------------------------
  # [2/6] Git pull
  # -----------------------------------------------------------------------
  echo ""
  echo "[2/6] Updating code (branch: $BRANCH)..."

  # Fix file ownership if needed
  docker run --rm -v "$DEPLOY_PATH:/work" alpine:3.19 sh -c "
    chown -R $(id -u):$(id -g) /work 2>/dev/null || true
  " 2>/dev/null || true

  # Clean dirty worktree
  if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    git reset --hard 2>/dev/null || true
    git clean -fd -e backups/ -e .deploy/ -e .env 2>/dev/null || true
  fi

  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"

  local deployed_commit
  deployed_commit="$(git rev-parse HEAD)"
  echo "Commit: $deployed_commit"

  # -----------------------------------------------------------------------
  # [3/6] Build images for inactive color
  # -----------------------------------------------------------------------
  echo ""
  echo "[3/6] Building $deploy_color Docker images..."

  DEPLOY_COLOR="$deploy_color" docker compose --project-name "llars-${deploy_color}" \
    $COMPOSE_FILES \
    build --parallel $BG_SERVICES

  # -----------------------------------------------------------------------
  # [4/6] Start inactive color containers
  # -----------------------------------------------------------------------
  echo ""
  echo "[4/6] Starting $deploy_color containers..."

  # Stop any previous containers of this color
  DEPLOY_COLOR="$deploy_color" docker compose --project-name "llars-${deploy_color}" \
    $COMPOSE_FILES \
    stop $BG_SERVICES 2>/dev/null || true

  DEPLOY_COLOR="$deploy_color" docker compose --project-name "llars-${deploy_color}" \
    $COMPOSE_FILES \
    up -d --no-deps $BG_SERVICES

  # -----------------------------------------------------------------------
  # [5/6] Wait for health
  # -----------------------------------------------------------------------
  echo ""
  echo "[5/6] Waiting for $deploy_color to be healthy..."

  wait_for_container_health "llars_flask_${deploy_color}" 180 5
  wait_for_container_health "llars_frontend_${deploy_color}" 120 5

  # Also verify via HTTP through the Docker network
  echo "Verifying HTTP health via Docker network..."
  if docker exec "llars_flask_${deploy_color}" curl -fsS -o /dev/null --max-time 10 "http://localhost:8081/auth/health_check" 2>/dev/null; then
    echo "HTTP health check passed (flask)"
  else
    echo "WARNING: HTTP health check failed (container may still be starting)"
  fi

  # -----------------------------------------------------------------------
  # [6/6] Update staging nginx to point to inactive color
  # -----------------------------------------------------------------------
  echo ""
  echo "[6/6] Starting staging nginx → $deploy_color on :55080"

  # Write staging upstream conf pointing to the inactive color
  local staging_conf="$DEPLOY_PATH/docker/nginx/active_upstream_staging.conf"
  cat > "$staging_conf" <<CONF
# Blue-Green staging upstream (managed by deploy_bluegreen.sh)
# DO NOT EDIT MANUALLY - updated by deploy_bluegreen.sh
# Staging color: $deploy_color (updated at $(date -u +"%Y-%m-%dT%H:%M:%SZ"))

upstream frontend {
    server llars_frontend_${deploy_color}:5173;
}

upstream backend {
    server llars_flask_${deploy_color}:8081;
}

upstream yjs {
    server llars_yjs_${deploy_color}:8082;
}
CONF

  # Start/restart staging nginx (port 55080) pointing to inactive color
  docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.staging.yml \
    stop nginx-service 2>/dev/null || true
  docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.staging.yml \
    up -d --no-deps nginx-service

  # Wait for staging to be accessible
  echo "Waiting for staging nginx..."
  local staging_health="$DEPLOY_PATH/scripts/ci/wait_for_health.sh"
  if [ -f "$staging_health" ]; then
    bash "$staging_health" "http://localhost:55080/auth/health_check" 120 5
  else
    sleep 10
    if curl -fsS -o /dev/null --max-time 10 "http://localhost:55080/auth/health_check" 2>/dev/null; then
      echo "Staging healthy on :55080"
    else
      echo "WARNING: Staging health check on :55080 failed"
    fi
  fi

  # Save rollback metadata
  local previous_commit
  previous_commit="$(git rev-parse HEAD~1 2>/dev/null || echo "")"
  cat > "$STATE_DIR/rollback.env" <<EOF
ROLLBACK_COMMIT=${previous_commit}
ROLLBACK_BACKUP=${backup_file}
DEPLOYED_COMMIT=${deployed_commit}
DEPLOYED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DEPLOY_COLOR=${deploy_color}
PREVIOUS_ACTIVE=${active}
EOF

  echo ""
  echo "=== Deploy complete ==="
  echo "Color: $deploy_color"
  echo "Commit: $deployed_commit"
  echo "Containers:"
  for svc in flask frontend yjs supervisor; do
    local status
    status=$(docker inspect --format='{{.State.Status}}' "llars_${svc}_${deploy_color}" 2>/dev/null || echo "not found")
    echo "  llars_${svc}_${deploy_color}: $status"
  done
  echo ""
  echo "Next step: Run tests, then 'deploy_bluegreen.sh switch' to cut over production"
}

# =============================================================================
# MODE: switch (instant production cutover)
# =============================================================================

cmd_switch() {
  echo "=========================================="
  echo "=== LLARS Production Switch ============="
  echo "=========================================="

  local active
  active=$(get_active_color)
  local deploy_color
  deploy_color=$(get_inactive_color)

  echo "Switching production: ${active:-none} → $deploy_color"

  # Verify inactive color containers are running and healthy
  for svc in flask frontend yjs supervisor; do
    local container="llars_${svc}_${deploy_color}"
    local status
    status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
    if [ "$status" != "running" ]; then
      echo "ERROR: $container is not running (status: $status)"
      echo "Run 'deploy_bluegreen.sh deploy' first to start the inactive color."
      exit 1
    fi
  done

  # Verify flask health
  local flask_health
  flask_health=$(docker inspect --format='{{.State.Health.Status}}' "llars_flask_${deploy_color}" 2>/dev/null || echo "unknown")
  if [ "$flask_health" != "healthy" ]; then
    echo "ERROR: llars_flask_${deploy_color} is not healthy (status: $flask_health)"
    exit 1
  fi

  # Switch upstream
  echo ""
  echo "[1/3] Updating upstream → $deploy_color"
  update_upstream_conf "$deploy_color"

  echo ""
  echo "[2/3] Reloading nginx..."
  reload_nginx

  echo ""
  echo "[3/3] Saving state..."
  save_state "$deploy_color" "$active"

  echo ""
  echo "=== Production switched to $deploy_color ==="
  echo "Previous color: ${active:-none} (containers still running for instant rollback)"
  echo ""
  echo "To rollback: bash scripts/ci/rollback_bluegreen.sh"
}

# =============================================================================
# Main
# =============================================================================

case "$MODE" in
  deploy)
    cmd_deploy
    ;;
  switch)
    cmd_switch
    ;;
  status)
    cmd_status
    ;;
  *)
    echo "Usage: $0 {deploy|switch|status}"
    echo ""
    echo "  deploy  - Build + start inactive color (staging)"
    echo "  switch  - Switch production nginx to inactive color"
    echo "  status  - Show current blue-green state"
    exit 1
    ;;
esac
