#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
BRANCH="${LLARS_PRODUCTION_BRANCH:-main}"

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

if [ ! -f .env ]; then
  echo "ERROR: .env not found in $DEPLOY_PATH"
  exit 1
fi

PREVIOUS_COMMIT="$(git rev-parse HEAD)"
BACKUP_DIR="$DEPLOY_PATH/backups"
ROLLBACK_DIR="$DEPLOY_PATH/.deploy"
mkdir -p "$BACKUP_DIR" "$ROLLBACK_DIR"

BACKUP_FILE="$BACKUP_DIR/pre_deploy_$(date +%Y%m%d_%H%M%S).sql"

echo "[1/6] Creating pre-deploy backup: $BACKUP_FILE"
if ! docker exec llars_db_service mysqldump -u dev_user -pdev_password_change_me database_llars > "$BACKUP_FILE"; then
  echo "ERROR: Backup failed. Aborting deploy."
  exit 1
fi

echo "[2/6] Updating code (branch: $BRANCH)"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

DEPLOYED_COMMIT="$(git rev-parse HEAD)"

echo "[3/6] Building Docker images"
docker compose build --parallel

echo "[4/6] Starting services"
docker compose up -d --remove-orphans

cat > "$ROLLBACK_DIR/rollback.env" <<EOF
ROLLBACK_COMMIT=$PREVIOUS_COMMIT
ROLLBACK_BACKUP=$BACKUP_FILE
DEPLOYED_COMMIT=$DEPLOYED_COMMIT
DEPLOYED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

echo "[5/6] Deployment complete"

echo "[6/6] Current status"
docker compose ps
