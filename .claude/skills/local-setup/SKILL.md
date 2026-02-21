---
name: local-setup
description: Start and manage LLARS locally. Use when starting, stopping, or troubleshooting the local development environment, or when user mentions docker, containers, local setup, or development server.
---

# LLARS Local Development Setup

## Quick Start

```bash
# Standard start
docker compose up -d

# Mit Logs
docker compose up

# Komplett-Neustart (LÖSCHT ALLE DATEN!)
docker compose down -v && docker compose up -d
```

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik (Auth) | http://localhost:55095 |
| MkDocs (Docs) | http://localhost:55080/docs |

## Test-Benutzer

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| evaluator | admin123 | evaluator |
| chatbot_manager | admin123 | chatbot_manager |

---

## Container Status

```bash
# Status aller Container
docker compose ps

# Nur LLARS Container
docker compose ps --format "table {{.Name}}\t{{.Status}}"

# Health Check
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(healthy|unhealthy)"
```

### Erwartete Container (16 Stück)

| Container | Funktion |
|-----------|----------|
| llars_nginx_service | Reverse Proxy |
| llars_frontend_service | Vue.js Frontend |
| llars_flask_service | Python Backend |
| llars_db_service | MariaDB (LLARS Daten) |
| llars_redis | Redis Cache |
| llars_yjs_service | YJS WebSocket (Collaboration) |
| llars_supervisor_service | Celery Worker |
| llars_authentik_server | Authentik Auth Server |
| llars_authentik_worker | Authentik Background Worker |
| llars_authentik_db | PostgreSQL (Authentik) |
| llars_authentik_redis | Redis (Authentik) |
| llars_authentik_init | Authentik Setup (exits after init) |
| llars_matomo_service | Matomo Analytics |
| llars_matomo_db_service | MariaDB (Matomo) |
| llars_matomo_init | Matomo Setup (exits after init) |
| llars_mkdocs_service | Documentation |

---

## Starten & Stoppen

### Starten

```bash
# Alle Services
docker compose up -d

# Einzelner Service
docker compose up -d llars_flask_service

# Mit Live-Logs
docker compose up
```

### Stoppen

```bash
# Alle stoppen (Daten bleiben erhalten)
docker compose down

# Alles stoppen + Volumes löschen (DATEN WEG!)
docker compose down -v
```

### Neustarten

```bash
# Einzelnen Service neustarten
docker compose restart llars_flask_service

# Alle neustarten
docker compose restart

# Frontend neu bauen und starten
docker compose up -d --build llars_frontend_service
```

---

## Logs

```bash
# Alle Logs (live)
docker compose logs -f

# Nur Backend
docker compose logs -f llars_flask_service

# Nur Frontend
docker compose logs -f llars_frontend_service

# Letzte 100 Zeilen
docker compose logs --tail=100 llars_flask_service

# Nur Fehler
docker compose logs -f 2>&1 | grep -i error
```

---

## Datenbank

### MariaDB (LLARS Daten)

```bash
# Shell öffnen
docker exec -it llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars

# SQL direkt ausführen
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e "SHOW TABLES;"

# Tabellen anzeigen
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e "SELECT * FROM users LIMIT 5;"
```

### Backup & Restore

```bash
# Backup erstellen
docker exec llars_db_service mysqldump -u dev_user -pdev_password_change_me database_llars > backup.sql

# Backup wiederherstellen
cat backup.sql | docker exec -i llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars
```

### PostgreSQL (Authentik)

```bash
# Shell öffnen
docker exec -it llars_authentik_db psql -U authentik -d authentik

# Benutzer anzeigen
docker exec llars_authentik_db psql -U authentik -d authentik -c "SELECT username FROM authentik_core_user;"
```

---

## Häufige Probleme

### Container startet nicht / "unhealthy"

```bash
# Logs prüfen
docker compose logs llars_flask_service

# Container neu bauen
docker compose up -d --build llars_flask_service

# Bei DB-Problemen: Volumes löschen
docker compose down -v && docker compose up -d
```

### "No space left on device"

```bash
# Docker aufräumen
docker system prune -af
docker builder prune -af

# Status prüfen
docker system df
```

### Port bereits belegt

```bash
# Wer nutzt Port 55080?
lsof -i :55080

# In .env anderen Port setzen
NGINX_EXTERNAL_PORT=55081
```

### Authentik Login schlägt fehl

```bash
# Authentik neu initialisieren
docker compose restart llars_authentik_init

# Oder: Volumes komplett neu
docker compose down -v && docker compose up -d
```

### Frontend zeigt alte Version

```bash
# Cache löschen und neu bauen
docker compose up -d --build --force-recreate llars_frontend_service
```

### "Access denied" bei Datenbank

Passiert wenn Volumes alte Credentials haben:

```bash
# Lösung: Volumes löschen
docker compose down -v
docker compose up -d
```

### .env Sonderzeichen-Problem

Passwörter mit `$`, `{`, `(` etc. müssen in einfache Anführungszeichen:

```bash
# Falsch
LLARS_SERVER_PASSWORD=abc$123{test}

# Richtig
LLARS_SERVER_PASSWORD='abc$123{test}'
```

---

## Entwicklung

### Frontend Hot-Reload

Das Frontend hat Hot-Reload - Änderungen werden automatisch übernommen.

```bash
# Frontend Logs beobachten
docker compose logs -f llars_frontend_service
```

### Backend Reload

Flask hat Auto-Reload in Development:

```bash
# Backend Logs beobachten
docker compose logs -f llars_flask_service
```

### Direkt in Container

```bash
# Shell im Backend-Container
docker exec -it llars_flask_service bash

# Shell im Frontend-Container
docker exec -it llars_frontend_service sh

# Python Shell mit App-Context
docker exec -it llars_flask_service flask shell
```

---

## Nützliche Befehle

### System-Übersicht

```bash
# Docker Ressourcen
docker system df

# Laufende Container
docker ps

# Alle Container (auch gestoppte)
docker ps -a

# Netzwerke
docker network ls
```

### Aufräumen

```bash
# Unbenutzte Images löschen
docker image prune -a

# Unbenutzte Volumes löschen
docker volume prune

# Alles aufräumen (Vorsicht!)
docker system prune -af --volumes
```

### Performance

```bash
# Container Ressourcen-Verbrauch
docker stats

# Einzelner Container
docker stats llars_flask_service
```

---

## Architektur

```
nginx (:55080) → Reverse Proxy
├── /          → Vue Frontend (:5173)
├── /api/      → Flask Backend (:8081)
├── /auth/     → Flask Auth Routes
├── /analytics/→ Matomo (:80)
├── /collab/   → YJS WebSocket (:8082)
└── /docs/     → MkDocs (:8000)

Intern:
├── MariaDB    → llars_db_service (:3306)
├── PostgreSQL → llars_authentik_db (:5432)
├── Redis      → llars_redis (:6379)
└── Redis      → llars_authentik_redis (:6379)
```

---

## Checkliste: Erster Start

1. [ ] `.env` vorhanden (kopieren von `.env.template.development`)
2. [ ] Docker Desktop läuft
3. [ ] Genug Speicherplatz (mind. 10 GB frei)
4. [ ] Ports frei (55080, 55095)
5. [ ] `docker compose up -d` ausführen
6. [ ] Warten bis alle Container "healthy" sind (~2 Minuten)
7. [ ] http://localhost:55080 öffnen
8. [ ] Login mit admin/admin123
