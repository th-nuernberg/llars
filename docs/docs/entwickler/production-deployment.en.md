# Production Deployment Guide

This guide describes how to deploy LLARS in a production environment.

!!! warning "Security note"
    Production deployments require additional security measures.
    This guide is a starting point — adapt it to your requirements.

---

## Prerequisites

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32+ GB |
| Storage | 100 GB SSD | 500+ GB NVMe |
| Network | 100 Mbit/s | 1 Gbit/s |

### Software

- Docker 24.0+
- Docker Compose 2.20+
- Git
- SSL certificate (Let's Encrypt or custom)

---

## 1. Prepare server

### System updates

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 git curl
```

### Docker without sudo

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## 2. Install LLARS

### Clone repository

```bash
cd /var
sudo mkdir llars
sudo chown $USER:$USER llars
cd llars
git clone https://git.your-server.de/llars/llars.git .
```

### Create production .env

```bash
cp .env.template.production .env
```

**Important settings in `.env`:**

```bash
# === PRODUCTION SETTINGS ===
FLASK_ENV=production
FLASK_DEBUG=False

# === SECRETS (CHANGE!) ===
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# === DATABASE ===
MARIADB_USER=llars_prod
MARIADB_PASSWORD=$(openssl rand -hex 24)
MARIADB_ROOT_PASSWORD=$(openssl rand -hex 24)
MARIADB_DATABASE=llars_production

# === AUTHENTIK ===
AUTHENTIK_SECRET_KEY=$(openssl rand -hex 32)
AUTHENTIK_BOOTSTRAP_PASSWORD=$(openssl rand -hex 16)
AUTHENTIK_PUBLIC_URL=https://auth.your-domain.com

# === EXTERNAL ACCESS ===
NGINX_EXTERNAL_PORT=80
VITE_API_BASE_URL=https://llars.your-domain.com/api

# === LLM API ===
LITELLM_API_KEY=your-litellm-key
LITELLM_BASE_URL=https://your-litellm-proxy.com

# === PERFORMANCE ===
GUNICORN_WORKERS=4
GUNICORN_THREADS=4
```

---

## 3. SSL with reverse proxy

### Option A: External reverse proxy (recommended)

If an external Nginx/Traefik/Caddy is available:

```bash
# In .env
NGINX_EXTERNAL_PORT=80
```

**Nginx config on the proxy:**

```nginx
server {
    listen 443 ssl http2;
    server_name llars.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/llars.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/llars.your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://llars-server:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_read_timeout 86400;
    }
}

server {
    listen 80;
    server_name llars.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Option B: Internal SSL within LLARS

For standalone deployments without an external proxy:

```bash
# Install certbot
sudo apt install certbot

# Obtain certificate
sudo certbot certonly --standalone -d llars.your-domain.com

# Copy certificates into LLARS
sudo cp /etc/letsencrypt/live/llars.your-domain.com/fullchain.pem /var/llars/ssl/
sudo cp /etc/letsencrypt/live/llars.your-domain.com/privkey.pem /var/llars/ssl/
```

---

## 4. Start

### First start

```bash
cd /var/llars
./start_llars.sh
```

### Check status

```bash
docker compose ps
docker compose logs -f --tail=100
```

### Health check

```bash
curl -s http://localhost/api/health | jq
```

---

## 5. Set up Authentik

### 1. Open Authentik admin panel

```
https://auth.your-domain.com/
```

Login: `akadmin` / `AUTHENTIK_BOOTSTRAP_PASSWORD` from `.env`

### 2. Create LLARS application

1. **Admin → Applications → Create**
2. Name: `LLARS`
3. Slug: `llars`
4. Create provider:
   - Type: OAuth2/OpenID Provider
   - Client ID: `llars-frontend`
   - Client Secret: (generate and store in `.env`)
   - Redirect URIs:
     ```
     https://llars.your-domain.com/auth/callback
     https://llars.your-domain.com/
     ```

### 3. Create backend provider

1. **Admin → Providers → Create**
2. Type: OAuth2/OpenID Provider
3. Client ID: `llars-backend`
4. For service account/API access

---

## 6. Set up backups

### Automated database backup

```bash
# /var/llars/scripts/backup.sh
#!/bin/bash
BACKUP_DIR=/var/llars/backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker exec llars_db_service mysqldump -u root -p$MARIADB_ROOT_PASSWORD \
  --all-databases > $BACKUP_DIR/db_$DATE.sql

# Compress
gzip $BACKUP_DIR/db_$DATE.sql

# ChromaDB backup
tar -czf $BACKUP_DIR/chroma_$DATE.tar.gz /var/llars/app/storage/chroma

# Uploads backup
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /var/llars/app/storage/uploads

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Cron job

```bash
# Daily backup at 3:00 AM
echo "0 3 * * * /var/llars/scripts/backup.sh >> /var/log/llars-backup.log 2>&1" | crontab -
```

---

## 7. Monitoring

### Docker stats

```bash
docker stats --no-stream
```

### Log aggregation

```bash
# All logs into one file
docker compose logs -f > /var/log/llars/all.log 2>&1 &

# Errors only
docker compose logs -f 2>&1 | grep -i error > /var/log/llars/errors.log &
```

### Matomo analytics

Already integrated in LLARS. Access via:

```
https://llars.your-domain.com/analytics/
```

---

## 8. Updates

### Standard update

```bash
cd /var/llars

# Pull changes
git pull origin main

# Rebuild containers
docker compose build

# Restart
docker compose up -d

# Check logs
docker compose logs -f --tail=100
```

### Update with downtime

```bash
cd /var/llars

# Enable maintenance mode (optional)
docker exec llars_flask_service flask maintenance on

# Create backup
./scripts/backup.sh

# Stop containers
docker compose down

# Update
git pull origin main

# Restart
docker compose up -d --build

# Disable maintenance mode
docker exec llars_flask_service flask maintenance off
```

---

## 9. Troubleshooting

### 502 Bad Gateway

```bash
# Check if containers are running
docker compose ps

# Check Nginx logs
docker logs llars_nginx_service

# Check Flask logs
docker logs llars_flask_service
```

### Database connection failed

```bash
# MariaDB status
docker logs llars_db_service

# Connection test
docker exec llars_flask_service python -c "from db.db import db; print('OK')"
```

### Authentik login fails

1. Check `AUTHENTIK_PUBLIC_URL` in `.env`
2. Check client ID and secret
3. Check redirect URIs in Authentik

### ChromaDB errors

```bash
# ChromaDB logs
docker logs llars_chromadb_service

# Check vector store
ls -la /var/llars/app/storage/chroma/
```

---

## 10. Security checklist

- [ ] All default passwords in `.env` changed
- [ ] SSL/TLS enabled
- [ ] Firewall configured
- [ ] Regular backups configured
- [ ] Log rotation enabled
- [ ] Authentik admin password changed
- [ ] Docker socket access restricted to admins
- [ ] No debug logs in production
- [ ] Rate limiting configured (reverse proxy)
- [ ] Security headers set

---

## 11. WSGI Server (Gunicorn + Gevent)

In production, LLARS uses **Gunicorn with gevent-websocket** for:

- Real WebSocket support (no polling fallback)
- Better Docker DNS compatibility than eventlet
- Low idle resource usage (~0.04% CPU, ~380 MB RAM)

### Development vs production mode

The `PROJECT_STATE` environment variable controls the mode:

| Mode | Server | WebSocket | Auto-reload |
|------|--------|-----------|-------------|
| `development` | Flask dev server | Polling (threading) | ✓ |
| `production` | Gunicorn + gevent | Real WebSockets | ✗ |

```bash
# In .env
PROJECT_STATE=production  # or development
```

### Gunicorn configuration

Configuration is in `docker/flask/gunicorn.conf.py`:

```python
# Server
bind = '0.0.0.0:8081'
workers = 1  # With gevent: 1 worker, greenlets handle concurrency

# Worker class for real WebSocket support
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'

# Timeouts for long LLM requests
timeout = 300  # 5 minutes
graceful_timeout = 30

# Memory leak prevention
max_requests = 1000
max_requests_jitter = 50
```

### WSGI entry points

| File | Usage |
|------|-------|
| `wsgi_gevent.py` | Production (Gunicorn + gevent) |
| `wsgi.py` | Eventlet (not recommended for Docker) |

**Important:** `gevent.monkey.patch_all()` MUST be called before any other imports.

```python
# wsgi_gevent.py
from gevent import monkey
monkey.patch_all()

from main import app, socketio
```

### Async mode

Flask-SocketIO detects `async_mode` automatically via environment variable:

```bash
# Set in start_flask.sh
export SOCKETIO_ASYNC_MODE="gevent"    # Production
export SOCKETIO_ASYNC_MODE="threading" # Development
```

---

## 12. Performance tuning

### Gunicorn workers

```bash
# In .env (for sync workers, not with gevent)
GUNICORN_WORKERS=4        # CPU cores * 2 + 1
GUNICORN_THREADS=4        # Per worker
GUNICORN_TIMEOUT=120      # For long requests
```

### MariaDB

```bash
# my.cnf adjustments
innodb_buffer_pool_size = 4G      # 50-70% of RAM
innodb_log_file_size = 1G
max_connections = 200
```

### ChromaDB

```bash
# For large collections
CHROMA_PERSIST_DIRECTORY=/fast-ssd/chroma
```

---

## 13. Load testing

LLARS includes a load test script at `scripts/load_test.py`.

### Quick test

```bash
# Local
python scripts/load_test.py --quick --host localhost --port 8081

# In Docker container
docker exec llars_flask_service python3 /app/scripts/load_test.py --quick
```

### Heavy load test

```bash
# 100 concurrent users, 20 requests per user, 50 WebSocket connections
python scripts/load_test.py \
  --users 100 \
  --requests 20 \
  --ws-connections 50 \
  --duration 60
```

### Test types

| Parameter | Description |
|-----------|-------------|
| `--test http` | HTTP API endpoints only |
| `--test websocket` | WebSocket connections only |
| `--test sustained` | Sustained load over time |
| `--test all` | All tests (default) |

### Benchmark results (as of January 2026)

**Server:** Production with Gunicorn + gevent-websocket

| Metric | Value |
|--------|-------|
| **HTTP Response Time (avg)** | 8-80 ms |
| **HTTP Response Time (p95)** | 164 ms |
| **HTTP Response Time (p99)** | 349 ms |
| **Throughput** | ~100 req/s |
| **WebSocket Connect Time** | 135-272 ms |
| **WebSocket Success Rate** | 100% |

**Resources after heavy load (9,600 requests):**

| Container | CPU | RAM |
|-----------|-----|-----|
| Flask | 0.04% | 380 MB |
| MariaDB | 0.02% | 112 MB |
| nginx | 0.00% | 8 MB |
| Redis | 0.63% | 7 MB |

### Rate limiting

Flask-Limiter protects the API automatically:

- **Default:** 1000 requests/hour per endpoint
- **Status code:** `429 Too Many Requests`
- **Log:** `ratelimit exceeded at endpoint: ...`

---

## 14. Troubleshooting production

### Eventlet DNS issues

**Problem:** With eventlet in Docker:
```
Can't connect to MySQL server on 'db-maria-service' ([Errno -3] Lookup timed out)
```

**Solution:** Use gevent instead of eventlet (already standard):
```bash
# In .env
PROJECT_STATE=production
# Automatically uses wsgi_gevent.py
```

### WebSocket fallback to polling

**Problem:** Browser uses polling instead of WebSocket.

**Check:**
```python
# In container
docker exec llars_flask_service python3 -c "
import socketio
sio = socketio.Client()
sio.connect('http://localhost:8081', transports=['websocket'])
print('Transport:', sio.transport())  # Should be 'websocket'
sio.disconnect()
"
```

**Solution:** Ensure `PROJECT_STATE=production` and Gunicorn runs with gevent.

### Container does not start after update

**Problem:** Permission denied for start_flask.sh.

**Solution:**
```bash
docker compose build --no-cache llars_flask_service
docker compose up -d llars_flask_service
```

---

## Next steps

1. [Set up users](../guides/login-anleitung.md)
2. [Create first chatbots](../projekte/chatbot-builder/index.md)
3. [Configure RAG pipeline](../agentic-ai/rag.md)
