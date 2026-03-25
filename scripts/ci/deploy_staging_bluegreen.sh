#!/usr/bin/env bash
# =============================================================================
# LLARS Blue-Green Staging Deployment
# =============================================================================
# Deploys staging containers on port 55080 alongside running production.
# Shared: DB, Redis, Authentik (production containers).
# Separate: Flask, Frontend, Nginx, Supervisor, YJS (staging containers).
#
# After successful E2E/smoke tests against staging, deploy_production.sh
# promotes the same code to production and stops staging containers.
#
# Usage: bash scripts/ci/deploy_staging_bluegreen.sh
# =============================================================================

set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
BRANCH="${LLARS_PRODUCTION_BRANCH:-main}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Mark deploy directory as safe for git
git config --global --add safe.directory "$DEPLOY_PATH" 2>/dev/null || true

cd "$DEPLOY_PATH"

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

BACKUP_DIR="$DEPLOY_PATH/backups"
mkdir -p "$BACKUP_DIR"

# -------------------------------------------------------------------------
# [1/5] DB Backup before migration (staging might run migrations)
# -------------------------------------------------------------------------
echo "[1/5] Creating pre-staging backup..."
DB_USER="${MYSQL_USER:-dev_user}"
DB_PASS="${MYSQL_PASSWORD:-dev_password_change_me}"
DB_NAME="${MYSQL_DATABASE:-database_llars}"
BACKUP_FILE="$BACKUP_DIR/staging_pre_deploy_$(date +%Y%m%d_%H%M%S).sql"

if docker inspect -f '{{.State.Running}}' llars_db_service >/dev/null 2>&1; then
  if timeout 300 docker exec llars_db_service mariadb-dump -u "$DB_USER" "-p$DB_PASS" --single-transaction --quick "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
    echo "Backup: $(du -h "$BACKUP_FILE" | cut -f1)"
  else
    echo "WARNING: Backup failed, continuing (production DB may not be running)."
    rm -f "$BACKUP_FILE"
  fi
else
  echo "WARNING: DB not running, skipping backup."
fi

# -------------------------------------------------------------------------
# [2/5] Git pull
# -------------------------------------------------------------------------
echo "[2/5] Updating code (branch: $BRANCH)..."

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

DEPLOYED_COMMIT="$(git rev-parse HEAD)"
echo "Deployed commit: $DEPLOYED_COMMIT"

# -------------------------------------------------------------------------
# [3/5] Build staging images
# -------------------------------------------------------------------------
echo "[3/5] Building staging Docker images..."
STAGING_SERVICES="nginx-service backend-flask-service frontend-vue-service backend-supervisor-service yjs-service"

# Compute semantic version from git tags for frontend build
COMMIT_HASH="$(git rev-parse --short HEAD)"
DESCRIBE="$(git describe --tags --long --match 'v*' 2>/dev/null || echo '')"
APP_VERSION="0.0.0"
if [[ "$DESCRIBE" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)-([0-9]+)-g ]]; then
  V_MAJOR="${BASH_REMATCH[1]}"; V_MINOR="${BASH_REMATCH[2]}"; V_PATCH="${BASH_REMATCH[3]}"; V_COMMITS="${BASH_REMATCH[4]}"
  if [ "$BRANCH" = "main" ]; then
    APP_VERSION="${V_MAJOR}.$(( V_MINOR + V_COMMITS )).0"
  else
    APP_VERSION="${V_MAJOR}.${V_MINOR}.$(( V_PATCH + V_COMMITS ))"
  fi
fi
export APP_VERSION APP_COMMIT_HASH="$COMMIT_HASH" APP_BRANCH="$BRANCH"
echo "Version: $APP_VERSION ($APP_BRANCH@$APP_COMMIT_HASH)"

docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.staging.yml \
  build --parallel $STAGING_SERVICES

# -------------------------------------------------------------------------
# [4/5] Start staging containers
# -------------------------------------------------------------------------
echo "[4/5] Starting staging containers (port 55080)..."

# Stop any previous staging containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.staging.yml \
  stop $STAGING_SERVICES 2>/dev/null || true

docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.staging.yml \
  up -d $STAGING_SERVICES

# -------------------------------------------------------------------------
# [5/5] Wait for staging to be healthy
# -------------------------------------------------------------------------
echo "[5/5] Waiting for staging to be healthy..."

HEALTH_SCRIPT="$SCRIPT_DIR/wait_for_health.sh"
if [ ! -f "$HEALTH_SCRIPT" ]; then
  HEALTH_SCRIPT="$DEPLOY_PATH/scripts/ci/wait_for_health.sh"
fi

if [ -f "$HEALTH_SCRIPT" ]; then
  bash "$HEALTH_SCRIPT" "http://localhost:55080/auth/health_check" 180 5
else
  # Fallback: simple wait loop
  for i in $(seq 1 36); do
    if curl -fsS -o /dev/null --max-time 10 "http://localhost:55080/auth/health_check" 2>/dev/null; then
      echo "Staging healthy after $((i * 5))s"
      break
    fi
    if [ "$i" -eq 36 ]; then
      echo "ERROR: Staging not healthy after 180s"
      docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.staging.yml \
        ps $STAGING_SERVICES
      exit 1
    fi
    sleep 5
  done
fi

AUTH_READY_SCRIPT="$SCRIPT_DIR/wait_for_auth_login.sh"
if [ ! -f "$AUTH_READY_SCRIPT" ]; then
  AUTH_READY_SCRIPT="$DEPLOY_PATH/scripts/ci/wait_for_auth_login.sh"
fi

AUTH_READY_PASSWORD="${LLARS_ADMIN_PASSWORD:-admin123}"
echo "Waiting for staging login readiness..."
if [ -f "$AUTH_READY_SCRIPT" ]; then
  bash "$AUTH_READY_SCRIPT" "http://localhost:55080" "admin" "$AUTH_READY_PASSWORD" 180 15
else
  echo "WARNING: Auth readiness script missing, skipping login probe."
fi

echo ""
echo "=== Staging deployment complete ==="
echo "Staging URL: http://localhost:55080"
echo "Commit: $DEPLOYED_COMMIT"
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.staging.yml \
  ps $STAGING_SERVICES
