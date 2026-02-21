# LLARS GitLab CI/CD Setup

**Version:** 2.0 | **Stand:** 1. Januar 2026

---

## Übersicht

Dieses Dokument beschreibt die Einrichtung der GitLab CI/CD Pipeline für automatisches Testing und Deployment.

**Wichtig:** LLARS verwendet einen **Shell Runner direkt auf dem Server** - kein SSH für Deployments nötig!

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

### GitLab Shell Runner auf dem Server

LLARS verwendet einen Shell Runner, der direkt auf dem LLARS Server läuft. Damit entfällt SSH-Konfiguration für Deployments.

```bash
# 1. GitLab Runner installieren
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner

# 2. Runner registrieren
sudo gitlab-runner register
# URL: https://git.informatik.fh-nuernberg.de/
# Token: aus GitLab → Settings → CI/CD → Runners
# Executor: shell
# Tags: shell

# 3. Runner zur docker Gruppe hinzufügen
sudo usermod -aG docker gitlab-runner

# 4. Projekt-Berechtigungen setzen
sudo chown -R :gitlab-runner /var/llars
sudo chmod -R g+rwX /var/llars
sudo find /var/llars -type d -exec chmod g+s {} \;  # SetGID für neue Dateien
```

### Runner-Konfiguration

```bash
# /etc/gitlab-runner/config.toml
[[runners]]
  name = "llars-server-shell"
  url = "https://git.informatik.fh-nuernberg.de/"
  executor = "shell"
  [runners.custom_build_dir]
  [runners.cache]
    [runners.cache.s3]
    [runners.cache.gcs]
    [runners.cache.azure]
```

**Wichtig:** Der Shell Runner muss mit `tags = ["shell"]` und `run_untagged = false` konfiguriert werden, damit er nur Jobs mit dem `shell` Tag annimmt.

---

## 2. GitLab CI/CD Variables

Gehe zu: **Settings → CI/CD → Variables**

### Erforderliche Variablen (für Shell Runner)

Bei Shell Runner auf dem Server sind **keine SSH-Variablen nötig**! Die Deploy-Jobs laufen direkt auf dem Server.

| Variable | Typ | Beschreibung | Protected | Masked |
|----------|-----|--------------|-----------|--------|
| (keine) | - | Shell Runner benötigt keine Variablen | - | - |

### Optionale Variablen

| Variable | Typ | Beschreibung |
|----------|-----|--------------|
| `DEPLOY_TOKEN` | Variable | Für private Docker Registry |
| `SLACK_WEBHOOK` | Variable | Für Deployment-Benachrichtigungen |
| `SENTRY_DSN` | Variable | Für Error Tracking |

---

## 3. Pipeline-Stages

### Stage 1: Lint (~30 Sekunden)

```yaml
lint:backend:   # Python: flake8, black, isort
lint:frontend:  # JavaScript: eslint
```

**Wann:** Bei jedem Push und Merge Request
**Failure:** Erlaubt (allow_failure: true)

### Stage 2: Test (~3-5 Minuten)

```yaml
test:unit:backend:     # pytest tests/unit/
test:unit:frontend:    # npm run test:run (vitest)
test:integration:      # pytest tests/integration/
test:e2e:              # playwright (nur main)
security:scan:         # pip-audit, npm audit
```

**Wann:**
- Unit Tests: Immer
- Integration: Bei MRs und main
- E2E: Nur main

**Wichtig: Lightweight Test Requirements**

Die Python-Tests verwenden `app/requirements-test.txt` statt `app/requirements.txt`:

```
Ausgeschlossene Pakete (~3GB gespart):
- torch
- transformers
- sentence-transformers
- flair
- langchain-huggingface
```

Diese schweren ML-Pakete werden in Tests gemockt und sind für Unit/Integration Tests nicht nötig.

**System Dependencies für Python Tests:**

```yaml
before_script:
  - apt-get update && apt-get install -y --no-install-recommends build-essential libffi-dev libssl-dev pkg-config
  - pip install --upgrade pip
```

### Stage 3: Build (~5 Minuten)

```yaml
build:docker:   # docker compose build
```

**Wann:** Nur auf main Branch (nach erfolgreichen Tests)

### Stage 4: Deploy (~2-5 Minuten)

```yaml
deploy:staging:     # Automatisch bei develop (Shell Runner)
deploy:production:  # Automatisch bei main (Shell Runner)
smoke:test:         # Nach Production Deploy
rollback:production: # Manuell bei Problemen
```

**Shell Runner Jobs:**
Die Deploy-Jobs laufen mit `tags: [shell]` direkt auf dem LLARS Server.

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

### Runner offline

```bash
# Auf dem Server:
sudo gitlab-runner status
sudo systemctl restart gitlab-runner

# Logs prüfen
sudo journalctl -u gitlab-runner -f
```

### test:unit:backend schlägt fehl

```bash
# Prüfe ob requirements-test.txt verwendet wird (nicht requirements.txt!)
# Die schweren ML-Pakete (torch, flair) dürfen NICHT installiert werden

# Lokal testen:
pip install -r app/requirements-test.txt
pytest tests/unit/ -v
```

### Permission denied bei Deploy

```bash
# Berechtigungen für gitlab-runner setzen
sudo chown -R :gitlab-runner /var/llars
sudo chmod -R g+rwX /var/llars
sudo find /var/llars -type d -exec chmod g+s {} \;
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
docker compose logs backend-flask-service --tail 100

# Manueller Health Check:
curl http://localhost/auth/health_check
```

### pip install timeout

Die ML-Pakete (torch ~2GB, flair, transformers) sollten in `requirements-test.txt` ausgeschlossen sein. Falls nicht:

```bash
# requirements-test.txt neu generieren:
cat app/requirements.txt | grep -vE "^(torch|flair|sentence-transformers|transformers|langchain-huggingface)==" > app/requirements-test.txt
```

### Pipeline hängt

```bash
# In GitLab: Pipeline → Cancel

# Prüfe Runner Status:
sudo gitlab-runner list
sudo gitlab-runner verify
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
[![Pipeline Status](https://git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars/badges/main/pipeline.svg)](https://git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars/-/pipelines)
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

### Einmalige Einrichtung (Server)

- [ ] GitLab Runner installiert (`gitlab-runner`)
- [ ] Runner registriert mit Shell Executor
- [ ] Runner-Tags: `shell`, `run_untagged = false`
- [ ] Runner zur `docker` Gruppe hinzugefügt
- [ ] `/var/llars` Verzeichnis erstellt
- [ ] Git Repository geklont
- [ ] `.env` Datei konfiguriert
- [ ] Berechtigungen: `gitlab-runner` Gruppe hat Schreibzugriff

### GitLab Konfiguration

- [ ] Runner in GitLab sichtbar (Settings → CI/CD → Runners)
- [ ] Branch Protection konfiguriert (main: nur Maintainers)
- [ ] `requirements-test.txt` vorhanden (ohne torch/flair)

### Test-Pipeline

- [ ] lint:backend/frontend erfolgreich (oder allow_failure)
- [ ] test:unit:backend erfolgreich
- [ ] test:unit:frontend erfolgreich
- [ ] test:integration erfolgreich
- [ ] test:e2e erfolgreich
- [ ] build:docker erfolgreich
- [ ] deploy:production erfolgreich
- [ ] smoke:test erfolgreich

### Verifizierung

```bash
# Pipeline-Status prüfen
open "https://git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars/-/pipelines"

# Server-Health prüfen (auf dem Server)
curl http://localhost/auth/health_check
docker compose ps
```

---

**Letzte Aktualisierung:** 1. Januar 2026
