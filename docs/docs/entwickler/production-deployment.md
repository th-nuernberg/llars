# Production Deployment Guide

Diese Anleitung beschreibt das Deployment von LLARS in einer Produktionsumgebung.

!!! warning "Sicherheitshinweis"
    Produktionsdeployments erfordern zusätzliche Sicherheitsmaßnahmen.
    Diese Anleitung dient als Ausgangspunkt - passe sie an deine Anforderungen an.

---

## Voraussetzungen

### Hardware

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| CPU | 4 Cores | 8+ Cores |
| RAM | 16 GB | 32+ GB |
| Storage | 100 GB SSD | 500+ GB NVMe |
| Netzwerk | 100 Mbit/s | 1 Gbit/s |

### Software

- Docker 24.0+
- Docker Compose 2.20+
- Git
- SSL-Zertifikat (Let's Encrypt oder eigenes)

---

## 1. Server vorbereiten

### System-Updates

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 git curl
```

### Docker ohne sudo

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

## 2. LLARS installieren

### Repository klonen

```bash
cd /var
sudo mkdir llars
sudo chown $USER:$USER llars
cd llars
git clone https://git.your-server.de/llars/llars.git .
```

### Produktions-.env erstellen

```bash
cp .env.template.production .env
```

**Wichtige Einstellungen in `.env`:**

```bash
# === PRODUCTION SETTINGS ===
FLASK_ENV=production
FLASK_DEBUG=False

# === SECRETS (ÄNDERN!) ===
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

## 3. SSL mit Reverse Proxy

### Option A: Externer Reverse Proxy (empfohlen)

Wenn ein externer Nginx/Traefik/Caddy vorhanden ist:

```bash
# In .env
NGINX_EXTERNAL_PORT=80
```

**Nginx-Konfiguration auf dem Proxy:**

```nginx
server {
    listen 443 ssl http2;
    server_name llars.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/llars.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/llars.your-domain.com/privkey.pem;

    # Security Headers
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

        # WebSocket Support
        proxy_read_timeout 86400;
    }
}

server {
    listen 80;
    server_name llars.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Option B: LLARS-internes SSL

Für eigenständiges Deployment ohne externen Proxy:

```bash
# Certbot installieren
sudo apt install certbot

# Zertifikat holen
sudo certbot certonly --standalone -d llars.your-domain.com

# Zertifikate nach LLARS kopieren
sudo cp /etc/letsencrypt/live/llars.your-domain.com/fullchain.pem /var/llars/ssl/
sudo cp /etc/letsencrypt/live/llars.your-domain.com/privkey.pem /var/llars/ssl/
```

---

## 4. Starten

### Erster Start

```bash
cd /var/llars
./start_llars.sh
```

### Status prüfen

```bash
docker compose ps
docker compose logs -f --tail=100
```

### Health Check

```bash
curl -s http://localhost/api/health | jq
```

---

## 5. Authentik einrichten

### 1. Authentik Admin-Panel öffnen

```
https://auth.your-domain.com/
```

Login: `akadmin` / `AUTHENTIK_BOOTSTRAP_PASSWORD` aus `.env`

### 2. LLARS-Anwendung erstellen

1. **Admin → Applications → Create**
2. Name: `LLARS`
3. Slug: `llars`
4. Provider erstellen:
   - Type: OAuth2/OpenID Provider
   - Client ID: `llars-frontend`
   - Client Secret: (generieren und in `.env` speichern)
   - Redirect URIs:
     ```
     https://llars.your-domain.com/auth/callback
     https://llars.your-domain.com/
     ```

### 3. Backend-Provider erstellen

1. **Admin → Providers → Create**
2. Type: OAuth2/OpenID Provider
3. Client ID: `llars-backend`
4. Für Service-Account/API-Zugriff

---

## 6. Backup einrichten

### Automatisches Datenbank-Backup

```bash
# /var/llars/scripts/backup.sh
#!/bin/bash
BACKUP_DIR=/var/llars/backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database Backup
docker exec llars_db_service mysqldump -u root -p$MARIADB_ROOT_PASSWORD \
  --all-databases > $BACKUP_DIR/db_$DATE.sql

# Compress
gzip $BACKUP_DIR/db_$DATE.sql

# ChromaDB Backup
tar -czf $BACKUP_DIR/chroma_$DATE.tar.gz /var/llars/app/storage/chroma

# Uploads Backup
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /var/llars/app/storage/uploads

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Cron-Job

```bash
# Tägliches Backup um 3:00 Uhr
echo "0 3 * * * /var/llars/scripts/backup.sh >> /var/log/llars-backup.log 2>&1" | crontab -
```

---

## 7. Monitoring

### Docker-Stats

```bash
docker stats --no-stream
```

### Log-Aggregation

```bash
# Alle Logs in eine Datei
docker compose logs -f > /var/log/llars/all.log 2>&1 &

# Nur Fehler
docker compose logs -f 2>&1 | grep -i error > /var/log/llars/errors.log &
```

### Matomo Analytics

Bereits in LLARS integriert. Zugriff über:

```
https://llars.your-domain.com/analytics/
```

---

## 8. Updates

### Standard-Update

```bash
cd /var/llars

# Änderungen pullen
git pull origin main

# Container neu bauen
docker compose build

# Neustart
docker compose up -d

# Logs prüfen
docker compose logs -f --tail=100
```

### Update mit Downtime

```bash
cd /var/llars

# Wartungsmodus aktivieren (optional)
docker exec llars_flask_service flask maintenance on

# Backup erstellen
./scripts/backup.sh

# Container stoppen
docker compose down

# Update
git pull origin main

# Neu starten
docker compose up -d --build

# Wartungsmodus deaktivieren
docker exec llars_flask_service flask maintenance off
```

---

## 9. Troubleshooting

### 502 Bad Gateway

```bash
# Prüfe ob Container laufen
docker compose ps

# Prüfe Nginx-Logs
docker logs llars_nginx_service

# Prüfe Flask-Logs
docker logs llars_flask_service
```

### Datenbank-Verbindung fehlgeschlagen

```bash
# MariaDB-Status
docker logs llars_db_service

# Verbindungstest
docker exec llars_flask_service python -c "from db.db import db; print('OK')"
```

### Authentik-Login schlägt fehl

1. Prüfe `AUTHENTIK_PUBLIC_URL` in `.env`
2. Prüfe Client-ID und Secret
3. Prüfe Redirect-URIs in Authentik

### ChromaDB-Fehler

```bash
# ChromaDB-Logs
docker logs llars_chromadb_service

# Vectorstore prüfen
ls -la /var/llars/app/storage/chroma/
```

---

## 10. Sicherheits-Checkliste

- [ ] Alle Standard-Passwörter in `.env` geändert
- [ ] SSL/TLS aktiviert
- [ ] Firewall konfiguriert
- [ ] Regelmäßige Backups eingerichtet
- [ ] Log-Rotation aktiviert
- [ ] Authentik Admin-Passwort geändert
- [ ] Docker-Socket nur für Admins zugänglich
- [ ] Keine Debug-Logs in Produktion
- [ ] Rate-Limiting konfiguriert (Reverse Proxy)
- [ ] Security Headers gesetzt

---

## 11. WSGI Server (Gunicorn + Gevent)

LLARS verwendet in Production **Gunicorn mit gevent-websocket** für:

- Echte WebSocket-Unterstützung (kein Polling-Fallback)
- Bessere Docker DNS-Kompatibilität als eventlet
- Geringer Ressourcenverbrauch im Idle (~0.04% CPU, ~380 MB RAM)

### Development vs Production Mode

Die Umgebungsvariable `PROJECT_STATE` steuert den Modus:

| Modus | Server | WebSocket | Auto-Reload |
|-------|--------|-----------|-------------|
| `development` | Flask Dev Server | Polling (threading) | ✓ |
| `production` | Gunicorn + gevent | Echte WebSockets | ✗ |

```bash
# In .env
PROJECT_STATE=production  # oder development
```

### Gunicorn-Konfiguration

Die Konfiguration liegt in `docker/flask/gunicorn.conf.py`:

```python
# Server
bind = '0.0.0.0:8081'
workers = 1  # Bei gevent: 1 Worker, Greenlets übernehmen Concurrency

# Worker-Klasse für echte WebSocket-Unterstützung
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'

# Timeouts für lange LLM-Requests
timeout = 300  # 5 Minuten
graceful_timeout = 30

# Memory-Leak-Prävention
max_requests = 1000
max_requests_jitter = 50
```

### WSGI Entry Points

| Datei | Verwendung |
|-------|------------|
| `wsgi_gevent.py` | Production (Gunicorn + gevent) |
| `wsgi.py` | Eventlet (nicht empfohlen für Docker) |

**Wichtig:** `gevent.monkey.patch_all()` MUSS vor allen anderen Imports aufgerufen werden!

```python
# wsgi_gevent.py
from gevent import monkey
monkey.patch_all()

from main import app, socketio
```

### Async Mode

Flask-SocketIO erkennt den async_mode automatisch via Umgebungsvariable:

```bash
# Wird in start_flask.sh gesetzt
export SOCKETIO_ASYNC_MODE="gevent"    # Production
export SOCKETIO_ASYNC_MODE="threading" # Development
```

---

## 12. Performance-Tuning

### Gunicorn-Worker

```bash
# In .env (für sync workers, nicht bei gevent)
GUNICORN_WORKERS=4        # CPU-Cores * 2 + 1
GUNICORN_THREADS=4        # Pro Worker
GUNICORN_TIMEOUT=120      # Für lange Requests
```

### MariaDB

```bash
# my.cnf Anpassungen
innodb_buffer_pool_size = 4G      # 50-70% des RAM
innodb_log_file_size = 1G
max_connections = 200
```

### ChromaDB

```bash
# Für große Collections
CHROMA_PERSIST_DIRECTORY=/fast-ssd/chroma
```

---

## 13. Load Testing

LLARS enthält ein integriertes Load-Test-Skript unter `scripts/load_test.py`.

### Quick Test

```bash
# Lokal
python scripts/load_test.py --quick --host localhost --port 8081

# Im Docker-Container
docker exec llars_flask_service python3 /app/scripts/load_test.py --quick
```

### Heavy Load Test

```bash
# 100 gleichzeitige User, 20 Requests pro User, 50 WebSocket-Verbindungen
python scripts/load_test.py \
  --users 100 \
  --requests 20 \
  --ws-connections 50 \
  --duration 60
```

### Test-Arten

| Parameter | Beschreibung |
|-----------|--------------|
| `--test http` | Nur HTTP API-Endpunkte |
| `--test websocket` | Nur WebSocket-Verbindungen |
| `--test sustained` | Dauerlast über Zeit |
| `--test all` | Alle Tests (Standard) |

### Benchmark-Ergebnisse (Stand: Januar 2026)

**Server:** Production mit Gunicorn + gevent-websocket

| Metrik | Wert |
|--------|------|
| **HTTP Response Time (avg)** | 8-80 ms |
| **HTTP Response Time (p95)** | 164 ms |
| **HTTP Response Time (p99)** | 349 ms |
| **Throughput** | ~100 req/s |
| **WebSocket Connect Time** | 135-272 ms |
| **WebSocket Success Rate** | 100% |

**Ressourcen nach Heavy Load (9.600 Requests):**

| Container | CPU | RAM |
|-----------|-----|-----|
| Flask | 0.04% | 380 MB |
| MariaDB | 0.02% | 112 MB |
| nginx | 0.00% | 8 MB |
| Redis | 0.63% | 7 MB |

### Rate-Limiting

Flask-Limiter schützt die API automatisch:

- **Standard:** 1000 Requests/Stunde pro Endpoint
- **Status-Code:** `429 Too Many Requests`
- **Log:** `ratelimit exceeded at endpoint: ...`

---

## 14. Troubleshooting Production

### Eventlet DNS-Probleme

**Problem:** Mit eventlet in Docker:
```
Can't connect to MySQL server on 'db-maria-service' ([Errno -3] Lookup timed out)
```

**Lösung:** Gevent statt eventlet verwenden (bereits Standard):
```bash
# In .env
PROJECT_STATE=production
# Verwendet automatisch wsgi_gevent.py
```

### WebSocket-Fallback auf Polling

**Problem:** Browser nutzt Polling statt WebSocket.

**Prüfen:**
```python
# Im Container
docker exec llars_flask_service python3 -c "
import socketio
sio = socketio.Client()
sio.connect('http://localhost:8081', transports=['websocket'])
print('Transport:', sio.transport())  # Sollte 'websocket' sein
sio.disconnect()
"
```

**Lösung:** Sicherstellen dass `PROJECT_STATE=production` und Gunicorn mit gevent läuft.

### Container startet nicht nach Update

**Problem:** Permission denied bei start_flask.sh.

**Lösung:**
```bash
docker compose build --no-cache llars_flask_service
docker compose up -d llars_flask_service
```

---

## Nächste Schritte

1. [Benutzer einrichten](../guides/login-anleitung.md)
2. [Erste Chatbots erstellen](../projekte/chatbot-builder/index.md)
3. [RAG-Pipeline konfigurieren](../agentic-ai/rag.md)
