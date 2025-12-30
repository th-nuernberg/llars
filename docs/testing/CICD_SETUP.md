# LLARS GitLab CI/CD Setup

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt die Einrichtung der GitLab CI/CD Pipeline für automatisches Testing und Deployment.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LLARS CI/CD PIPELINE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  develop Branch                    main Branch                       │
│  ┌──────────┐                     ┌──────────┐                      │
│  │  Push    │                     │  Push    │                      │
│  └────┬─────┘                     └────┬─────┘                      │
│       │                                │                             │
│       ▼                                ▼                             │
│  ┌──────────┐                     ┌──────────┐                      │
│  │   Lint   │                     │   Lint   │                      │
│  └────┬─────┘                     └────┬─────┘                      │
│       │                                │                             │
│       ▼                                ▼                             │
│  ┌──────────┐                     ┌──────────┐                      │
│  │  Tests   │                     │  Tests   │                      │
│  │  (Unit)  │                     │  (All)   │                      │
│  └────┬─────┘                     └────┬─────┘                      │
│       │                                │                             │
│       ▼                                ▼                             │
│  ┌──────────┐                     ┌──────────┐                      │
│  │  Build   │                     │  Build   │                      │
│  └────┬─────┘                     └────┬─────┘                      │
│       │                                │                             │
│       ▼                                ▼                             │
│  ┌──────────┐                     ┌──────────┐                      │
│  │ Deploy   │                     │ Deploy   │                      │
│  │ STAGING  │                     │   PROD   │                      │
│  └──────────┘                     └────┬─────┘                      │
│                                        │                             │
│                                        ▼                             │
│                                   ┌──────────┐                      │
│                                   │  Smoke   │                      │
│                                   │  Tests   │                      │
│                                   └──────────┘                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Voraussetzungen

### Auf dem LLARS Server

```bash
# 1. SSH User erstellen (falls nicht vorhanden)
sudo useradd -m -s /bin/bash llars
sudo usermod -aG docker llars

# 2. SSH Key für GitLab CI generieren
sudo -u llars ssh-keygen -t ed25519 -C "gitlab-ci-deploy" -f /home/llars/.ssh/gitlab_deploy
# KEIN Passwort setzen!

# 3. Public Key zu authorized_keys hinzufügen
sudo -u llars bash -c 'cat ~/.ssh/gitlab_deploy.pub >> ~/.ssh/authorized_keys'
sudo chmod 600 /home/llars/.ssh/authorized_keys

# 4. Private Key anzeigen (für GitLab)
sudo cat /home/llars/.ssh/gitlab_deploy
# Diesen Key in GitLab eintragen (siehe unten)

# 5. Projekt-Verzeichnis vorbereiten
sudo mkdir -p /var/llars/backups
sudo chown -R llars:llars /var/llars

# 6. Git Repository klonen
sudo -u llars git clone git@gitlab.example.com:team/llars.git /var/llars
cd /var/llars
sudo -u llars cp .env.template.production .env
# .env anpassen!
```

### Known Hosts ermitteln

```bash
# Auf dem lokalen Rechner oder einem CI Runner
ssh-keyscan -H llars.example.com

# Ausgabe kopieren für SSH_KNOWN_HOSTS Variable
```

---

## 2. GitLab CI/CD Variables

Gehe zu: **Settings → CI/CD → Variables**

### Erforderliche Variablen

| Variable | Typ | Wert | Protected | Masked |
|----------|-----|------|-----------|--------|
| `SSH_PRIVATE_KEY` | Variable | Inhalt von `gitlab_deploy` (Private Key) | ✓ | ✓ |
| `SSH_KNOWN_HOSTS` | Variable | Ausgabe von `ssh-keyscan` | ✓ | ✗ |
| `LLARS_SERVER_HOST` | Variable | `llars.example.com` oder IP | ✓ | ✗ |
| `LLARS_SERVER_USER` | Variable | `llars` | ✓ | ✗ |
| `LLARS_DEPLOY_PATH` | Variable | `/var/llars` | ✓ | ✗ |

### Optionale Variablen

| Variable | Typ | Beschreibung |
|----------|-----|--------------|
| `DEPLOY_TOKEN` | Variable | Für private Docker Registry |
| `SLACK_WEBHOOK` | Variable | Für Deployment-Benachrichtigungen |
| `SENTRY_DSN` | Variable | Für Error Tracking |

### Variable einrichten (Schritt für Schritt)

1. **SSH_PRIVATE_KEY:**
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   b3BlbnNzaC1rZXktdjEAAAAABG5vbmU...
   ...
   -----END OPENSSH PRIVATE KEY-----
   ```

2. **SSH_KNOWN_HOSTS:**
   ```
   llars.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...
   ```

3. **LLARS_SERVER_HOST:**
   ```
   llars.example.com
   ```
   oder
   ```
   192.168.1.100
   ```

---

## 3. Pipeline-Stages

### Stage 1: Lint (~30 Sekunden)

```yaml
lint:backend:   # Python: flake8, black, isort
lint:frontend:  # JavaScript: eslint
```

**Wann:** Bei jedem Push und Merge Request
**Failure:** Erlaubt (allow_failure: true)

### Stage 2: Test (~5-15 Minuten)

```yaml
test:unit:backend:     # pytest tests/unit/
test:unit:frontend:    # npm run test:run
test:integration:      # pytest tests/integration/
test:e2e:              # playwright (nur main)
security:scan:         # pip-audit, npm audit
```

**Wann:**
- Unit Tests: Immer
- Integration: Bei MRs und main
- E2E: Nur main

### Stage 3: Build (~5 Minuten)

```yaml
build:docker:   # docker compose build
```

**Wann:** Nur auf main Branch

### Stage 4: Deploy (~2-5 Minuten)

```yaml
deploy:staging:     # Automatisch bei develop
deploy:production:  # Automatisch bei main
smoke:test:         # Nach Production Deploy
rollback:production: # Manuell bei Problemen
```

---

## 4. Deployment-Ablauf

### Automatisches Production Deployment

Bei Push zu `main`:

```
1. Lint & Tests laufen
2. Docker Images werden gebaut
3. SSH Verbindung zum Server
4. Pre-Deployment Backup
5. Git Pull (main)
6. Docker Compose Build
7. Rolling Update der Container
8. Health Checks
9. Smoke Tests
```

### Bei Fehlern

Die Pipeline führt automatisch ein Rollback durch:

```bash
# Automatischer Rollback bei fehlgeschlagenem Health Check:
1. Datenbank aus Backup wiederherstellen
2. Git auf vorherigen Commit zurücksetzen
3. Container neu starten
```

### Manueller Rollback

```bash
# In GitLab: Pipeline → rollback:production → Play Button
```

---

## 5. Server-Konfiguration

### Verzeichnisstruktur auf dem Server

```
/var/llars/
├── .env                    # Produktions-Konfiguration
├── docker-compose.yml
├── backups/                # Automatische Backups
│   ├── pre_deploy_20251230_120000.sql
│   └── ...
├── app/                    # Backend
├── llars-frontend/         # Frontend
└── ...
```

### Erforderliche Server-Pakete

```bash
# Auf dem LLARS Server:
sudo apt update
sudo apt install -y \
  docker.io \
  docker-compose-plugin \
  git \
  curl

# Docker für llars User
sudo usermod -aG docker llars
```

### Firewall-Regeln

```bash
# SSH Zugang für GitLab Runner
sudo ufw allow from <GITLAB_RUNNER_IP> to any port 22

# LLARS Ports (falls nötig)
sudo ufw allow 55080/tcp  # HTTP
sudo ufw allow 443/tcp    # HTTPS (Produktion)
```

---

## 6. Erste Pipeline ausführen

### 1. Repository vorbereiten

```bash
# Lokale Entwicklung
git checkout develop
git add .gitlab-ci.yml docs/testing/CICD_SETUP.md
git commit -m "ci: add GitLab CI/CD pipeline for automated deployment"
git push origin develop
```

### 2. Pipeline prüfen

1. Gehe zu **CI/CD → Pipelines**
2. Pipeline sollte starten
3. Prüfe jeden Stage

### 3. Merge zu main für Production Deploy

```bash
git checkout main
git merge develop
git push origin main
```

---

## 7. Troubleshooting

### SSH Verbindung schlägt fehl

```bash
# Prüfe SSH Key Format
# Der Key muss mit "-----BEGIN" beginnen und mit "-----END" enden

# Teste manuell:
ssh -i /path/to/key llars@llars.example.com

# Prüfe Berechtigungen auf Server:
ls -la /home/llars/.ssh/
# authorized_keys muss 600 sein
```

### Docker Build schlägt fehl

```bash
# Auf dem Server:
cd /var/llars
docker compose build --no-cache

# Prüfe Disk Space:
df -h
docker system prune -a  # Vorsicht: löscht alle ungenutzten Images!
```

### Health Check schlägt fehl

```bash
# Auf dem Server:
docker compose ps
docker compose logs flask-service --tail 100

# Manueller Health Check:
curl http://localhost:55080/api/health
```

### Pipeline hängt

```bash
# In GitLab: Pipeline → Cancel

# Prüfe Runner Status:
# Settings → CI/CD → Runners
```

---

## 8. Best Practices

### Branch Protection

```
Settings → Repository → Protected Branches

main:
  - Allowed to merge: Maintainers
  - Allowed to push: No one
  - Require pipeline success: ✓

develop:
  - Allowed to merge: Developers
  - Allowed to push: Developers
```

### Merge Request Workflow

1. Feature-Branch von `develop` erstellen
2. Entwickeln und committen
3. MR zu `develop` erstellen
4. Pipeline muss erfolgreich sein
5. Code Review
6. Merge zu `develop` → Auto-Deploy zu Staging
7. Testen auf Staging
8. MR von `develop` zu `main`
9. Merge zu `main` → Auto-Deploy zu Production

### Backup-Strategie

```bash
# Backups werden automatisch erstellt:
# - Vor jedem Production Deployment
# - Die letzten 10 Backups werden behalten

# Manuelles Backup:
ssh llars@llars.example.com
cd /var/llars
docker exec llars_db_service mysqldump -u dev_user -pdev_password_change_me database_llars > backups/manual_$(date +%Y%m%d_%H%M%S).sql
```

---

## 9. Monitoring

### Pipeline Status Badge

```markdown
[![Pipeline Status](https://gitlab.example.com/team/llars/badges/main/pipeline.svg)](https://gitlab.example.com/team/llars/-/pipelines)
```

### Slack/Teams Benachrichtigungen

```yaml
# In .gitlab-ci.yml hinzufügen:
notify:success:
  stage: .post
  script:
    - 'curl -X POST -H "Content-type: application/json" --data "{\"text\":\"✅ LLARS Deployment erfolgreich!\"}" $SLACK_WEBHOOK'
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  when: on_success

notify:failure:
  stage: .post
  script:
    - 'curl -X POST -H "Content-type: application/json" --data "{\"text\":\"❌ LLARS Deployment fehlgeschlagen!\"}" $SLACK_WEBHOOK'
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  when: on_failure
```

---

## 10. Checkliste: CI/CD Einrichtung

### Einmalige Einrichtung

- [ ] SSH User `llars` auf Server erstellt
- [ ] SSH Key generiert (ohne Passwort)
- [ ] Public Key zu authorized_keys hinzugefügt
- [ ] `/var/llars` Verzeichnis erstellt
- [ ] Git Repository geklont
- [ ] `.env` Datei konfiguriert
- [ ] Docker läuft auf Server

### GitLab Konfiguration

- [ ] `SSH_PRIVATE_KEY` Variable gesetzt
- [ ] `SSH_KNOWN_HOSTS` Variable gesetzt
- [ ] `LLARS_SERVER_HOST` Variable gesetzt
- [ ] `LLARS_SERVER_USER` Variable gesetzt
- [ ] `LLARS_DEPLOY_PATH` Variable gesetzt
- [ ] Branch Protection konfiguriert

### Test-Pipeline

- [ ] Erste Pipeline auf develop erfolgreich
- [ ] Staging Deployment funktioniert
- [ ] Erste Pipeline auf main erfolgreich
- [ ] Production Deployment funktioniert
- [ ] Smoke Tests bestanden
- [ ] Rollback getestet

---

**Letzte Aktualisierung:** 30. Dezember 2025
