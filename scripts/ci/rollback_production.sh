#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"

# Mark deploy directory as safe for git (required when running as different user)
git config --global --add safe.directory "$DEPLOY_PATH" 2>/dev/null || true

ROLLBACK_ENV="$DEPLOY_PATH/.deploy/rollback.env"

if [ ! -f "$ROLLBACK_ENV" ]; then
  echo "ERROR: Rollback file not found: $ROLLBACK_ENV"
  exit 1
fi

set -a
. "$ROLLBACK_ENV"
set +a

if [ -z "${ROLLBACK_COMMIT:-}" ] || [ -z "${ROLLBACK_BACKUP:-}" ]; then
  echo "ERROR: Rollback metadata missing in $ROLLBACK_ENV"
  exit 1
fi

cd "$DEPLOY_PATH"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $DEPLOY_PATH is not a git repository."
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "WARNING: Working tree has uncommitted tracked changes."
  echo "Resetting tracked files while preserving .env/.deploy/backups."
  git status --short || true
  git reset --hard 2>/dev/null || true
  git clean -fd -e backups/ -e .deploy/ -e .env 2>/dev/null || true
fi

BACKUP_PATH="$ROLLBACK_BACKUP"
if [ "${BACKUP_PATH#/}" = "$BACKUP_PATH" ]; then
  BACKUP_PATH="$DEPLOY_PATH/$BACKUP_PATH"
fi

if [ ! -f "$BACKUP_PATH" ]; then
  echo "ERROR: Backup not found: $BACKUP_PATH"
  exit 1
fi

echo "[1/4] Checking out rollback commit $ROLLBACK_COMMIT"
git fetch origin main || true
git checkout "$ROLLBACK_COMMIT"

echo "[2/5] Restoring database from $BACKUP_PATH"
# Source .env to get database credentials
if [ -f "$DEPLOY_PATH/.env" ]; then
  set -a
  . "$DEPLOY_PATH/.env"
  set +a
fi
DB_USER="${MYSQL_USER:-dev_user}"
DB_PASS="${MYSQL_PASSWORD:-dev_password_change_me}"
DB_NAME="${MYSQL_DATABASE:-database_llars}"
DB_RESTORE_TIMEOUT="${DB_RESTORE_TIMEOUT:-600}"  # 10 minutes default

if ! timeout "$DB_RESTORE_TIMEOUT" docker exec -i llars_db_service mariadb -u "$DB_USER" "-p$DB_PASS" "$DB_NAME" < "$BACKUP_PATH"; then
  RESTORE_EXIT=$?
  if [ "$RESTORE_EXIT" -eq 124 ]; then
    echo "ERROR: DB restore timed out after ${DB_RESTORE_TIMEOUT}s"
  else
    echo "ERROR: DB restore failed with exit code $RESTORE_EXIT"
  fi
  exit 1
fi
echo "Database restored successfully"

echo "[3/5] Rebuilding and starting services (production mode)"
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans

echo "[4/5] Verifying rollback health..."
HEALTH_SCRIPT="$DEPLOY_PATH/scripts/ci/wait_for_health.sh"
if [ -f "$HEALTH_SCRIPT" ]; then
  bash "$HEALTH_SCRIPT" "http://localhost/auth/health_check" 120 5
else
  # Fallback: simple wait
  for i in $(seq 1 24); do
    if curl -fsS -o /dev/null --max-time 10 "http://localhost/auth/health_check" 2>/dev/null; then
      echo "Rollback healthy after $((i * 5))s"
      break
    fi
    if [ "$i" -eq 24 ]; then
      echo "WARNING: Rollback health check timed out after 120s"
    fi
    sleep 5
  done
fi

echo "[5/5] Rollback completed"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
