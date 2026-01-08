#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
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
  echo "ERROR: Working tree has uncommitted changes."
  git status --short
  exit 1
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

echo "[2/4] Restoring database from $BACKUP_PATH"
docker exec -i llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars < "$BACKUP_PATH"

echo "[3/4] Rebuilding and starting services (production mode)"
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans

echo "[4/4] Rollback completed"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
