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
#   pending_switch.env - Candidate color/commit prepared by deploy mode
#   active_commit   - Commit currently serving production traffic
#   rollback.env    - Commit + backup info for full rollback
# =============================================================================

set -euo pipefail

MODE="${1:-deploy}"
DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
BRANCH="${LLARS_PRODUCTION_BRANCH:-main}"
STAGING_PROJECT_NAME="${LLARS_STAGING_PROJECT_NAME:-llars-staging}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="$DEPLOY_PATH/.deploy"
BACKUP_DIR="$DEPLOY_PATH/backups"
PENDING_SWITCH_FILE="$STATE_DIR/pending_switch.env"
ACTIVE_COMMIT_FILE="$STATE_DIR/active_commit"
PREVIOUS_COMMIT_FILE="$STATE_DIR/previous_commit"

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.prod-bluegreen.yml"
BG_BUILD_SERVICES="backend-flask-service backend-worker-service frontend-vue-service yjs-service backend-supervisor-service"
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

print_container_diagnostics() {
  local container="$1"

  echo ""
  echo "--- Diagnostics for $container ---"
  docker ps -a --filter "name=^/${container}$" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" || true
  docker inspect --format='state={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}} exit_code={{.State.ExitCode}} started={{.State.StartedAt}} finished={{.State.FinishedAt}}' "$container" 2>/dev/null || true
  echo "--- Last logs ($container) ---"
  docker logs --tail 120 "$container" 2>&1 || true
  echo "--- End diagnostics ($container) ---"
  echo ""
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
  print_container_diagnostics "$container"
  return 1
}

wait_for_http_health() {
  local container="$1"
  local url="$2"
  local max_wait="${3:-240}"
  local interval="${4:-5}"
  local elapsed=0

  echo "Waiting for HTTP health on $container ($url)..."
  while [ "$elapsed" -lt "$max_wait" ]; do
    if docker exec "$container" curl -fsS -o /dev/null --max-time 10 "$url" 2>/dev/null; then
      echo "HTTP health check passed for $container after ${elapsed}s"
      return 0
    fi

    local state
    state=$(docker inspect --format='{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container" 2>/dev/null || echo "not_found")
    elapsed=$((elapsed + interval))
    echo "  Waiting... (${elapsed}/${max_wait}s) state=$state"
    sleep "$interval"
  done

  echo "ERROR: HTTP health check failed for $container after ${max_wait}s"
  print_container_diagnostics "$container"
  return 1
}

get_admin_password() {
  if [ -n "${LLARS_ADMIN_PASSWORD:-}" ]; then
    echo "$LLARS_ADMIN_PASSWORD"
    return 0
  fi

  if [ -f "$DEPLOY_PATH/.env" ]; then
    grep '^LLARS_ADMIN_PASSWORD=' "$DEPLOY_PATH/.env" | cut -d= -f2- || true
  fi
}

verify_flask_storage() {
  local container="$1"

  echo "Verifying writable storage in $container..."
  if docker exec "$container" sh -lc '
    set -eu
    mkdir -p \
      /app/storage \
      /app/storage/rag_images \
      /app/storage/screenshots \
      /app/storage/models \
      /app/storage/vectorstore
    test -w /app/storage
    test -w /app/storage/rag_images
    test -w /app/storage/models
  ' >/dev/null 2>&1; then
    echo "Writable storage verified for $container"
    return 0
  fi

  echo "ERROR: Writable storage verification failed for $container"
  docker exec "$container" sh -lc '
    id || true
    echo "--- /proc/mounts (/app*) ---"
    grep /app /proc/mounts || true
    echo "--- storage permissions ---"
    ls -ld /app /app/storage /app/storage/rag_images /app/storage/models 2>&1 || true
  ' || true
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
  local container="${1:-llars_nginx_service}"
  echo "Reloading nginx in $container..."
  if docker exec "$container" nginx -t 2>&1; then
    docker exec "$container" nginx -s reload
    echo "Nginx reloaded successfully"
    return 0
  fi

  echo "ERROR: Nginx config test failed in $container!"
  return 1
}

ensure_nginx_upstream_mount_synced() {
  local host_conf="$DEPLOY_PATH/docker/nginx/active_upstream.conf"
  local container_conf="/etc/nginx/active_upstream.conf"

  if [ ! -f "$host_conf" ]; then
    echo "ERROR: Host upstream config not found: $host_conf"
    return 1
  fi

  local container_state
  container_state=$(docker inspect --format='{{.State.Status}}' llars_nginx_service 2>/dev/null || echo "not_found")
  if [ "$container_state" != "running" ]; then
    return 0
  fi

  local host_hash container_hash
  host_hash=$(sha256sum "$host_conf" | awk '{print $1}')
  container_hash=$(docker exec llars_nginx_service sh -lc "sha256sum \"$container_conf\" | awk '{print \\\$1}'" 2>/dev/null || echo "")

  if [ -z "$container_hash" ] || [ "$host_hash" != "$container_hash" ]; then
    echo "Detected stale nginx file bind mount for active_upstream.conf (host != container)."
    echo "Recreating llars_nginx_service to refresh file mount..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --force-recreate nginx-service
  fi
}

ensure_production_nginx() {
  local state
  state=$(docker inspect --format='{{.State.Status}}' llars_nginx_service 2>/dev/null || echo "not_found")
  if [ "$state" = "running" ]; then
    return 0
  fi

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
  local active_commit
  active_commit=$(cat "$ACTIVE_COMMIT_FILE" 2>/dev/null || echo "unknown")

  if [ -z "$active" ]; then
    echo "State: No blue-green deployment yet"
    echo "Next deploy will use: blue"
  else
    echo "Active color:   $active"
    echo "Previous color: $previous"
    echo "Active commit:  $active_commit"

    echo ""
    echo "--- Blue containers ---"
    for svc in flask worker frontend yjs supervisor; do
      local status
      status=$(docker inspect --format='{{.State.Status}} (health: {{.State.Health.Status}})' "llars_${svc}_blue" 2>/dev/null || echo "not running")
      echo "  llars_${svc}_blue: $status"
    done

    echo ""
    echo "--- Green containers ---"
    for svc in flask worker frontend yjs supervisor; do
      local status
      status=$(docker inspect --format='{{.State.Status}} (health: {{.State.Health.Status}})' "llars_${svc}_green" 2>/dev/null || echo "not running")
      echo "  llars_${svc}_green: $status"
    done
  fi

  if [ -f "$PENDING_SWITCH_FILE" ]; then
    # shellcheck disable=SC1090
    . "$PENDING_SWITCH_FILE"
    echo ""
    echo "--- Pending switch ---"
    echo "Color:  ${PENDING_COLOR:-unknown}"
    echo "Commit: ${PENDING_COMMIT:-unknown}"
    echo "From:   ${PENDING_CREATED_AT:-unknown}"
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

  # Read env vars safely (avoids source failures with special chars in passwords)
  _env() { grep "^${1}=" .env 2>/dev/null | head -1 | cut -d= -f2-; }

  # Force production runtime semantics during blue-green deploy, independent of .env drift.
  export PROJECT_STATE=production
  export FLASK_ENV=production

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
  local db_user="$(_env MYSQL_USER)" ; db_user="${db_user:-dev_user}"
  local db_pass="$(_env MYSQL_PASSWORD)" ; db_pass="${db_pass:-dev_password_change_me}"
  local db_name="$(_env MYSQL_DATABASE)" ; db_name="${db_name:-database_llars}"
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

  # Rotate backups: keep only the 5 newest
  local old_backups
  old_backups=$(ls -t "$BACKUP_DIR"/*.sql 2>/dev/null | tail -n +6)
  if [ -n "$old_backups" ]; then
    echo "$old_backups" | xargs rm -f
    echo "Rotated backups, kept newest 5."
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

  git fetch origin "$BRANCH" --tags
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"

  local deployed_commit
  deployed_commit="$(git rev-parse HEAD)"
  echo "Commit: $deployed_commit"

  # Git checkout can replace bind-mounted files by inode and leave the running nginx
  # process with a stale /etc/nginx/active_upstream.conf. Re-apply active upstream now.
  if [ -n "$active" ]; then
    echo "Re-applying production upstream to active color '$active' after git update..."
    update_upstream_conf "$active"
    ensure_production_nginx
    ensure_nginx_upstream_mount_synced
    reload_nginx llars_nginx_service
  fi

  # -----------------------------------------------------------------------
  # [3/6] Build images for inactive color
  # -----------------------------------------------------------------------
  echo ""
  echo "[3/6] Building $deploy_color Docker images..."

  # Compute semantic version from git tags using `git describe`.
  # Formula: v1.5.0-N-gabcdef → N=0: exact tag, N>0: major.minor.(patch+N)
  # Uses --first-parent to avoid merge-commit inflation, with fallback for main.
  local describe commit_hash
  commit_hash="$(git rev-parse --short HEAD)"
  describe="$(git describe --tags --match 'v*' --first-parent 2>/dev/null || git describe --tags --match 'v*' 2>/dev/null || echo '')"
  local app_version="0.0.0"
  if [[ "$describe" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)(-([0-9]+)-g[0-9a-f]+)?$ ]]; then
    local major="${BASH_REMATCH[1]}" minor="${BASH_REMATCH[2]}" patch="${BASH_REMATCH[3]}" commits="${BASH_REMATCH[5]:-0}"
    if [ "$commits" -eq 0 ]; then
      app_version="${major}.${minor}.${patch}"
    else
      app_version="${major}.${minor}.$(( patch + commits ))"
    fi
  fi
  export APP_VERSION="$app_version"
  export APP_COMMIT_HASH="$commit_hash"
  export APP_BRANCH="$BRANCH"
  echo "Version: $APP_VERSION ($APP_BRANCH@$APP_COMMIT_HASH)"

  # CACHE_BUST (= commit hash) invalidates frontend source COPY + build layers.
  # npm ci layer stays cached unless package*.json changes. This ensures
  # source code changes are always picked up without rebuilding everything.
  DEPLOY_COLOR="$deploy_color" docker compose --project-name "llars-${deploy_color}" \
    $COMPOSE_FILES \
    build --parallel $BG_BUILD_SERVICES

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

  # Prepare the worker container for this color without starting it.
  DEPLOY_COLOR="$deploy_color" docker compose --project-name "llars-${deploy_color}" \
    $COMPOSE_FILES \
    up --no-start --no-deps backend-worker-service

  # -----------------------------------------------------------------------
  # [5/6] Wait for health
  # -----------------------------------------------------------------------
  echo ""
  echo "[5/6] Waiting for $deploy_color to be healthy..."

  wait_for_http_health "llars_flask_${deploy_color}" "http://localhost:8081/auth/health_check" 420 5
  verify_flask_storage "llars_flask_${deploy_color}"
  wait_for_container_health "llars_frontend_${deploy_color}" 180 5

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

  # Start/restart staging nginx (port 55080) pointing to inactive color.
  # Use a dedicated compose project so staging never replaces production nginx.
  # IMPORTANT: Do not include docker-compose.prod.yml here, otherwise staging nginx may
  # inherit production 80/443 bindings and hijack public traffic.
  local staging_compose_files="-f docker-compose.yml -f docker-compose.staging.yml"
  NGINX_EXTERNAL_PORT=55080 docker compose --project-name "$STAGING_PROJECT_NAME" $staging_compose_files \
    up -d --force-recreate --no-deps nginx-service

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

  local auth_ready_script="$DEPLOY_PATH/scripts/ci/wait_for_auth_login.sh"
  local auth_ready_password
  auth_ready_password="$(get_admin_password)"
  if [ -n "$auth_ready_password" ] && [ -f "$auth_ready_script" ]; then
    echo "Waiting for staging login readiness..."
    bash "$auth_ready_script" "http://localhost:55080" "admin" "$auth_ready_password" 180 15
  else
    echo "WARNING: Skipping staging login readiness probe (missing password or helper script)."
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

  # Save pending switch candidate (consumed by switch mode)
  cat > "$PENDING_SWITCH_FILE" <<EOF
PENDING_COLOR=${deploy_color}
PENDING_COMMIT=${deployed_commit}
PENDING_CREATED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

  echo ""
  echo "=== Deploy complete ==="
  echo "Color: $deploy_color"
  echo "Commit: $deployed_commit"
  echo "Containers:"
  for svc in flask worker frontend yjs supervisor; do
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

  if [ ! -f "$PENDING_SWITCH_FILE" ]; then
    echo "No pending deployment candidate found. Nothing to switch."
    exit 0
  fi

  # shellcheck disable=SC1090
  . "$PENDING_SWITCH_FILE"

  local deploy_color="${PENDING_COLOR:-}"
  local candidate_commit="${PENDING_COMMIT:-}"
  if [ -z "$deploy_color" ] || [ -z "$candidate_commit" ]; then
    echo "ERROR: Invalid pending switch file: $PENDING_SWITCH_FILE"
    exit 1
  fi

  local active
  active=$(get_active_color)
  local expected_inactive
  expected_inactive=$(get_inactive_color)

  if [ "$deploy_color" != "$expected_inactive" ]; then
    echo "ERROR: Pending color '$deploy_color' does not match expected inactive color '$expected_inactive'."
    echo "Run 'deploy_bluegreen.sh deploy' again to prepare a fresh candidate."
    exit 1
  fi

  local active_commit
  active_commit=$(cat "$ACTIVE_COMMIT_FILE" 2>/dev/null || echo "")
  if [ -n "$active_commit" ] && [ "$active_commit" = "$candidate_commit" ]; then
    echo "Candidate commit is already active ($candidate_commit); switching anyway to refresh production on $deploy_color."
  fi

  echo "Switching production: ${active:-none} → $deploy_color ($candidate_commit)"

  # Verify inactive color web containers are running and healthy
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

  echo ""
  echo "[1/6] Handing over worker ownership..."
  if [ -n "$active" ]; then
    docker stop "llars_worker_${active}" 2>/dev/null || true
  fi
  docker start "llars_worker_${deploy_color}" 2>/dev/null || true
  wait_for_container_health "llars_worker_${deploy_color}" 180 5

  # Switch upstream
  echo ""
  echo "[2/6] Updating upstream → $deploy_color"
  update_upstream_conf "$deploy_color"

  echo ""
  echo "[3/6] Ensuring production nginx is running..."
  ensure_production_nginx
  ensure_nginx_upstream_mount_synced

  echo ""
  echo "[4/6] Reloading nginx..."
  reload_nginx llars_nginx_service

  echo ""
  echo "[5/6] Saving state..."
  save_state "$deploy_color" "$active"
  if [ -n "$active_commit" ]; then
    echo "$active_commit" > "$PREVIOUS_COMMIT_FILE"
  fi
  echo "$candidate_commit" > "$ACTIVE_COMMIT_FILE"

  echo ""
  echo "[6/6] Clearing pending switch state..."
  rm -f "$PENDING_SWITCH_FILE"

  echo ""
  echo "=== Production switched to $deploy_color ==="
  echo "Active commit: $candidate_commit"
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
