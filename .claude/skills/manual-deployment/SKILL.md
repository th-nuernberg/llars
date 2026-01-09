# Manual Deployment for LLARS

## Quick Deploy (One-Liner from Local Machine)

```bash
# Recommended: Pull and restart with start_llars.sh
ssh llars "cd /var/llars && git pull origin main && ./start_llars.sh"
```

This pulls the latest code and restarts all services with health checks.

## Quick Deploy (Step by Step on Server)

```bash
# 1. SSH to server
ssh llars

# 2. Navigate to project
cd /var/llars

# 3. Pull latest code
git pull origin main

# 4. Restart LLARS (rebuilds containers if needed)
./start_llars.sh
```

## Fix Permissions (if git pull fails)

```bash
ssh llars "cd /var/llars && docker run --rm -v /var/llars:/work alpine:3.19 chown -R 1002:1002 /work"
```

## Full Deployment Steps

### 1. Connect to Server

```bash
# Using SSH config (recommended)
ssh llars

# Or directly
ssh master@llars.informatik.fh-nuernberg.de -i ~/.ssh/id_ed25519_llars
```

### 2. Fix File Permissions

Docker creates files as root, which can block git operations.

```bash
cd /var/llars

# Fix .git permissions only
docker run --rm -v /var/llars:/work alpine:3.19 chown -R 1002:1002 /work/.git

# Fix all permissions (slower but thorough)
docker run --rm -v /var/llars:/work alpine:3.19 chown -R 1002:1002 /work
```

### 3. Update Code

```bash
cd /var/llars

# If working tree is dirty, reset first
git reset --hard
git clean -fd -e .env -e backups/ -e .deploy/

# Pull latest changes
git pull origin main
```

### 4. Restart Services

**Option A: Full restart with start script (recommended)**
```bash
cd /var/llars
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
./start_llars.sh
```

**Option B: Quick restart (keeps volumes)**
```bash
cd /var/llars
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Option C: Rebuild and restart**
```bash
cd /var/llars
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 5. Verify Deployment

```bash
# Check container status
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Check Flask logs
docker logs llars_flask_service --tail 50

# Check for errors
docker logs llars_flask_service 2>&1 | grep -i error | tail -20
```

## Production Environment

| Setting | Value |
|---------|-------|
| Server | llars.informatik.fh-nuernberg.de (141.75.150.128) |
| SSH User | master |
| Deploy Path | /var/llars |
| Branch | main |
| Mode | Production |

### URLs

| Service | URL |
|---------|-----|
| Frontend | https://llars.e-beratungsinstitut.de |
| Backend API | https://llars.e-beratungsinstitut.de/api |
| Authentik | https://llars.e-beratungsinstitut.de/authentik |
| Matomo | https://llars.e-beratungsinstitut.de/analytics/ |

## Database Operations

### Get Production Credentials

```bash
ssh llars "grep -E '^MYSQL_(USER|PASSWORD|DATABASE)=' /var/llars/.env"
```

### Connect to Database

```bash
# On server
ssh llars

# Then run
source /var/llars/.env
docker exec -it llars_db_service mariadb -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE
```

### Create Backup Before Deploy

```bash
ssh llars "cd /var/llars && source .env && \
  docker exec llars_db_service mariadb-dump -u \$MYSQL_USER -p\$MYSQL_PASSWORD \$MYSQL_DATABASE > backups/pre_deploy_\$(date +%Y%m%d_%H%M%S).sql"
```

### Restore Backup

```bash
ssh llars "cd /var/llars && source .env && \
  cat backups/BACKUP_FILE.sql | docker exec -i llars_db_service mariadb -u \$MYSQL_USER -p\$MYSQL_PASSWORD \$MYSQL_DATABASE"
```

## Troubleshooting

### Permission Denied on Git Pull

```bash
# Fix with docker
docker run --rm -v /var/llars:/work alpine:3.19 chown -R 1002:1002 /work/.git
```

### Container Won't Start

```bash
# Check logs
docker logs llars_flask_service --tail 100

# Check if ports are in use
sudo netstat -tulpn | grep -E '80|443|5432|3306'

# Force remove and restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Database Connection Failed

```bash
# Check if DB is running
docker ps | grep llars_db

# Restart DB
docker restart llars_db_service

# Wait for healthy status
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### Flask Not Starting

```bash
# Check logs for import errors
docker logs llars_flask_service 2>&1 | grep -i "import\|error\|traceback" | head -30

# Rebuild Flask container
docker compose -f docker-compose.yml -f docker-compose.prod.yml build flask_service
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d flask_service
```

## Rollback

### Quick Rollback

```bash
ssh llars "cd /var/llars && \
  git checkout HEAD~1 && \
  docker compose -f docker-compose.yml -f docker-compose.prod.yml down && \
  ./start_llars.sh"
```

### Rollback to Specific Commit

```bash
ssh llars "cd /var/llars && \
  git checkout COMMIT_HASH && \
  docker compose -f docker-compose.yml -f docker-compose.prod.yml down && \
  ./start_llars.sh"
```

### Rollback with Database Restore

```bash
ssh llars "cd /var/llars && source .env && \
  git checkout COMMIT_HASH && \
  cat backups/BACKUP_FILE.sql | docker exec -i llars_db_service mariadb -u \$MYSQL_USER -p\$MYSQL_PASSWORD \$MYSQL_DATABASE && \
  docker compose -f docker-compose.yml -f docker-compose.prod.yml down && \
  ./start_llars.sh"
```

## CI/CD Pipeline

The GitLab CI/CD pipeline automatically deploys on push to main:

```
Push to main → lint → test → security → build → deploy:production → smoke:production
```

To check pipeline status:

```bash
source .env
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines?per_page=3" | \
  python3 -c "import sys,json; [print(f'Pipeline #{p[\"id\"]}: {p[\"status\"]}') for p in json.load(sys.stdin)]"
```

## Key Files

| File | Purpose |
|------|---------|
| `/var/llars/.env` | Production environment variables |
| `/var/llars/start_llars.sh` | Main startup script |
| `/var/llars/docker-compose.yml` | Base Docker config |
| `/var/llars/docker-compose.prod.yml` | Production overrides |
| `/var/llars/scripts/ci/deploy_production.sh` | CI deployment script |
| `/var/llars/backups/` | Database backups |
