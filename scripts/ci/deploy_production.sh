#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${LLARS_DEPLOY_PATH:-/var/llars}"
BRANCH="${LLARS_PRODUCTION_BRANCH:-main}"
BACKUP_DIR="$DEPLOY_PATH/backups"
ROLLBACK_DIR="$DEPLOY_PATH/.deploy"

cd "$DEPLOY_PATH"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $DEPLOY_PATH is not a git repository."
  exit 1
fi

mkdir -p "$BACKUP_DIR" "$ROLLBACK_DIR"

# Fix file ownership - Docker may have created files as root
# Use docker to run chown as root to fix permissions
echo "[0/6] Fixing file ownership for deployment..."
docker run --rm -v "$DEPLOY_PATH:/work" alpine:3.19 sh -c "
  chown -R $(id -u):$(id -g) /work 2>/dev/null || true
  chmod -R u+rw /work 2>/dev/null || true
" || echo "WARN: Could not fix all file permissions, continuing..."

if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  CLEAN_TS="$(date +%Y%m%d_%H%M%S)"
  CLEAN_DIR="$BACKUP_DIR/dirty_worktree_$CLEAN_TS"
  mkdir -p "$CLEAN_DIR"

  git status --short > "$CLEAN_DIR/status.txt" || true
  git diff --binary > "$CLEAN_DIR/working_tree.patch" || true
  git diff --cached --binary > "$CLEAN_DIR/index.patch" || true

  git ls-files --others --exclude-standard -z > "$CLEAN_DIR/untracked.zlist" || true
if [ -s "$CLEAN_DIR/untracked.zlist" ]; then
  tr '\0' '\n' < "$CLEAN_DIR/untracked.zlist" > "$CLEAN_DIR/untracked.txt"
  tar --null \
      --exclude="backups/*" \
      --exclude=".deploy/*" \
      --exclude=".env" \
      -czf "$CLEAN_DIR/untracked.tar.gz" \
      --files-from="$CLEAN_DIR/untracked.zlist" || true
fi

  echo "INFO: Working tree dirty. Backup saved to $CLEAN_DIR"
  git reset --hard
  git clean -fd -e backups/ -e .deploy/ -e .env
fi

if [ ! -f .env ]; then
  echo "ERROR: .env not found in $DEPLOY_PATH"
  exit 1
fi

set -a
. ./.env
set +a

PREVIOUS_COMMIT="$(git rev-parse HEAD)"
BACKUP_FILE="$BACKUP_DIR/pre_deploy_$(date +%Y%m%d_%H%M%S).sql"

echo "[1/6] Creating pre-deploy backup: $BACKUP_FILE"
DB_USER="${MYSQL_USER:-dev_user}"
DB_PASS="${MYSQL_PASSWORD:-dev_password_change_me}"
DB_NAME="${MYSQL_DATABASE:-database_llars}"

if ! docker inspect -f '{{.State.Running}}' llars_db_service >/dev/null 2>&1; then
  echo "ERROR: llars_db_service is not running. Aborting deploy."
  docker ps -a
  exit 1
fi

if ! docker exec llars_db_service mysqldump -u "$DB_USER" "-p$DB_PASS" "$DB_NAME" > "$BACKUP_FILE"; then
  echo "ERROR: Backup failed. Aborting deploy."
  docker logs --tail 200 llars_db_service || true
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
