# LLARS GitLab CI/CD Setup

**Version:** 3.0 | **Stand:** 18. März 2026

---

## Übersicht

Dieses Dokument beschreibt die Einrichtung der GitLab CI/CD Pipeline für automatisches Testing und Deployment.

**Wichtig:** LLARS verwendet ein **Two-Branch Blue-Green Deployment** mit Shell Runnern auf zwei Servern — kein SSH für Deployments nötig!

### Nightly Kachel- und Workflow-Regression

Der Nightly-Lauf enthält eine contract-basierte Playwright-Suite:

- Tile-Contract: `llars-frontend/src/config/home_tiles.contract.json`
- Workflow-Contract: `llars-frontend/e2e/nightly/nightly_workflows.contract.json`
- Activity-Contract: `llars-frontend/e2e/nightly/nightly_activities.contract.json`
- Tile-Tests: `llars-frontend/e2e/nightly/tile-regression.spec.js`
- Workflow-Tests: `llars-frontend/e2e/nightly/workflows.spec.js`
- Coverage-Gate: `scripts/testing/validate_nightly_coverage.py`
- Matrix-Doku: `docs/testing/nightly/NIGHTLY_TILE_MATRIX.md`
- Nightly-Accounts: `test_admin`, `test_researcher`, `test_evaluator`, `test_chatbot_manager`
- Laufkennzeichnung: `Nightly Test`

Regeln:

1. Testtitel müssen exakt den Kachelnamen bzw. Workflownamen entsprechen.
2. Bei Änderung an `Home.vue` oder am Tile-Contract sind Test- und Dokuänderungen Pflicht, sonst CI-Fehler.
3. Nightly schaltet Produktion nur nach erfolgreichem `test:e2e:nightly:tiles`.

Manueller Aufruf auf dem Server:

```bash
cd /var/llars
export E2E_TEST_PASSWORD=$(grep '^LLARS_ADMIN_PASSWORD=' .env | cut -d= -f2- || echo "admin123")
export E2E_RUN_TAG="Nightly Test"
export E2E_ADMIN_USER="test_admin"
export E2E_RESEARCHER_USER="test_researcher"
export E2E_EVALUATOR_USER="test_evaluator"
export E2E_CHATBOT_MANAGER_USER="test_chatbot_manager"
export E2E_BOOTSTRAP_ADMIN_USER="admin"
export E2E_BOOTSTRAP_TEST_USERS="true"
export E2E_KEEP_TEST_USERS="false"
export E2E_BOOTSTRAP_ADMIN_PASSWORD="${E2E_TEST_PASSWORD}"
docker compose --profile testing build smoke-test-service
python3 scripts/testing/validate_nightly_coverage.py
docker compose --profile testing run --rm --entrypoint "" \
  -e PLAYWRIGHT_BASE_URL=http://localhost:55080 \
  -e E2E_TEST_PASSWORD="${E2E_TEST_PASSWORD}" \
  -e E2E_RUN_TAG="${E2E_RUN_TAG}" \
  -e E2E_ADMIN_USER="${E2E_ADMIN_USER}" \
  -e E2E_RESEARCHER_USER="${E2E_RESEARCHER_USER}" \
  -e E2E_EVALUATOR_USER="${E2E_EVALUATOR_USER}" \
  -e E2E_CHATBOT_MANAGER_USER="${E2E_CHATBOT_MANAGER_USER}" \
  -e E2E_BOOTSTRAP_ADMIN_USER="${E2E_BOOTSTRAP_ADMIN_USER}" \
  -e E2E_BOOTSTRAP_ADMIN_PASSWORD="${E2E_BOOTSTRAP_ADMIN_PASSWORD}" \
  -e E2E_BOOTSTRAP_TEST_USERS="${E2E_BOOTSTRAP_TEST_USERS}" \
  -e E2E_KEEP_TEST_USERS="${E2E_KEEP_TEST_USERS}" \
  -e NODE_TLS_REJECT_UNAUTHORIZED=0 \
  smoke-test-service \
  bash -c "cd /tests/e2e && npx playwright test --project=chromium --workers=1 nightly/tile-regression.spec.js nightly/workflows.spec.js"
python3 scripts/testing/cleanup_nightly_test_users.py
```

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          LLARS CI/CD PIPELINE (Two-Branch Model)                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  dev Branch → llars-dev (141.75.150.86)     main Branch → Production (141.75.150.128)
│  Auto-deploy on every push                  Lint+Test on push, nightly deploy    │
│                                                                                  │
│  ┌──────┐   ┌──────┐   ┌────────┐          ┌──────┐   ┌──────┐   ┌────────┐    │
│  │ Lint │ → │ Test │ → │Security│          │ Lint │ → │ Test │ → │Security│    │
│  └──────┘   └──────┘   └───┬────┘          └──────┘   └──────┘   └───┬────┘    │
│                             │                                         │          │
│                             ▼                          (Nightly/Force) ▼          │
│                        ┌─────────┐                           ┌──────────────┐    │
│                        │Build:dev│                           │ Build:docker │    │
│                        │(shell-  │                           │  (shell)     │    │
│                        │  dev)   │                           └──────┬───────┘    │
│                        └───┬─────┘                                 │            │
│                            │                                       ▼            │
│                            ▼                              ┌──────────────┐      │
│                     ┌────────────┐                        │Deploy:staging│      │
│                     │ Deploy:dev │                        └──────┬───────┘      │
│                     └─────┬──────┘                               │              │
│                           │                                      ▼              │
│                     ┌─────┴──────┐                        ┌──────────────┐      │
│                     │  E2E:dev + │                        │ E2E + Smoke  │      │
│                     │ Smoke:dev  │                        │   :staging   │      │
│                     └─────┬──────┘                        └──────┬───────┘      │
│                           │                                      │              │
│                           ▼                                      ▼              │
│                     ┌────────────┐                        ┌──────────────┐      │
│                     │ Switch:dev │                        │   Deploy:    │      │
│                     └────────────┘                        │  production  │      │
│                                                           └──────┬───────┘      │
│                                                                  │              │
│                                                                  ▼              │
│                                                          ┌──────────────┐       │
│                                                          │    Smoke:    │       │
│                                                          │  production  │       │
│                                                          └──────┬───────┘       │
│                                                                 │               │
│                                                          FAIL → Rollback        │
│                                                                                  │
│  Workflow: dev → test on llars-dev → merge dev→main → nightly prod deploy       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Voraussetzungen

### GitLab Runners

LLARS verwendet drei Runner:

| Runner | ID | Tag | Server | Zweck |
|--------|----|-----|--------|-------|
| Docker | 515 | (shared) | GitLab shared | Lint, Test, Security |
| Shell (prod) | 517 | `shell` | 141.75.150.128 | Build + Deploy Production |
| Shell (dev) | 546 | `shell-dev` | 141.75.150.86 | Build + Deploy llars-dev |

Shell Runner laufen direkt auf dem jeweiligen Server. Damit entfaellt SSH-Konfiguration fuer Deployments.

### Production Runner Setup (141.75.150.128)

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

### Runner-Konfiguration (Production)

```toml
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

### Dev Runner Setup (141.75.150.86)

Der Dev-Server hat einen eigenen Shell Runner fuer automatische Deployments bei jedem Push auf `dev`.

```bash
# Runner registrieren (auf llars-dev Server)
sudo gitlab-runner register
# URL: https://git.informatik.fh-nuernberg.de/
# Token: aus GitLab → Settings → CI/CD → Runners
# Executor: shell
# Tags: shell-dev

# Runner zur docker Gruppe hinzufügen
sudo usermod -aG docker gitlab-runner
```

### Runner-Konfiguration (Dev)

```toml
# /home/master/.gitlab-runner/config.toml
[[runners]]
  name = "llars-dev-shell"
  url = "https://git.informatik.fh-nuernberg.de/"
  executor = "shell"
  tags = ["shell-dev"]
  [runners.custom_build_dir]
  [runners.cache]
```

**Systemd Service:** `/etc/systemd/system/gitlab-runner.service`

**Wichtig:** Die Dev-Server `.env` unter `/var/llars/.env` hat `LLARS_PRODUCTION_BRANCH=dev` gesetzt, damit `deploy_bluegreen.sh` den `dev` Branch auscheckt.

---

## 2. GitLab CI/CD Variables

Gehe zu: **Settings → CI/CD → Variables**

### Erforderliche Variablen

| Variable | Typ | Beschreibung | Protected | Masked |
|----------|-----|--------------|-----------|--------|
| `SYSTEM_ADMIN_API_KEY` | Variable | API Key fuer Smoke Tests (Backend System-Endpoints) | Yes | Yes |
| `E2E_TEST_PASSWORD` | Variable | Passwort fuer E2E/Nightly Test-User | Yes | Yes |

### Trigger-Variablen

| Variable | Typ | Beschreibung |
|----------|-----|--------------|
| `SCHEDULED_DEPLOY` | `true` | Nightly Production Deploy (gesetzt im Pipeline Schedule) |
| `FORCE_DEPLOY` | `true` | Sofortige volle Pipeline auf `main` (inkl. Production) |
| `FORCE_DEV_DEPLOY` | `true` | Force Dev-Deploy (auch ohne Code-Aenderungen) |
| `DRY_RUN` | `true` | Voller Staging-Flow ohne Production-Deploy |

### Optionale Variablen

| Variable | Typ | Beschreibung |
|----------|-----|--------------|
| `DEPLOY_TOKEN` | Variable | Fuer private Docker Registry |
| `SLACK_WEBHOOK` | Variable | Fuer Deployment-Benachrichtigungen |
| `SENTRY_DSN` | Variable | Fuer Error Tracking |

---

## Pipeline-Steuerung

Die Pipeline kann auf verschiedene Arten getriggert werden:

| Trigger | Lint | Tests | E2E | Staging | Smoke | Production | Dauer |
|---------|:----:|:-----:|:---:|:-------:|:-----:|:----------:|:-----:|
| Normaler Push (main/dev) | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ~5 min |
| `[dryrun]` in Commit-Message | ✓ | ✓ | ✓ | ✓ | ✓ | **✗** | ~15 min |
| `DRY_RUN=true` (CI Variable) | ✓ | ✓ | ✓ | ✓ | ✓ | **✗** | ~15 min |
| `FORCE_DEPLOY=true` (CI Variable) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~20 min |
| Nightly Schedule (Mo-Fr 02:00) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~20 min |

### Dry-Run: Staging-Pipeline ohne Production-Deploy

Mit `[dryrun]` in der Commit-Message kann der vollständige Staging-Flow getestet werden,
**ohne** dass Production deployed wird. Nützlich um vor dem Nightly-Lauf zu prüfen,
ob die Pipeline durchlaufen wird.

```bash
# Via Commit-Message (empfohlen)
git commit -m "chore: pre-release check [dryrun]"
git push origin main

# Via GitLab UI
# CI/CD → Pipelines → Run Pipeline → Variable: DRY_RUN=true
```

**Was läuft:** Lint → Test → Security → Build → Deploy:Staging → E2E → Smoke:Staging

**Was NICHT läuft:** Deploy:Production, Smoke:Production, Switch

### Sofort-Deploy

Für dringende Deployments kann über die GitLab UI eine Pipeline mit `FORCE_DEPLOY=true`
getriggert werden. Dies startet den vollen Pipeline-Flow inkl. Production-Deploy.

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
test:nightly:contracts: # Contract-Validator
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
build:docker:      # docker compose build (shell runner, Production-Server)
build:docker:dev:  # docker compose build (shell-dev runner, Dev-Server)
```

**Wann:**
- `build:docker` — Auf `main` bei Nightly Schedule oder `FORCE_DEPLOY=true`
- `build:docker:dev` — Auf `dev` bei jedem Push

### Stage 4-7: Deploy, Test-Staging, Production, Smoke

**Dev-Pipeline (auto, bei jedem Push auf `dev`):**

```yaml
deploy:dev:              # Blue-Green deploy auf llars-dev (shell-dev)
e2e:dev:                 # Playwright E2E Tests gegen llars-dev
smoke:dev:               # Smoke Tests gegen llars-dev
switch:dev:              # Blue-Green switch auf llars-dev
```

**Main-Pipeline (Nightly/Force auf `main`):**

```yaml
deploy:staging:          # Blue-Green staging deploy auf Production-Server (shell)
test:e2e:nightly:tiles:  # Contract-basierte Nightly Playwright-Suite
smoke:staging:           # Smoke Tests gegen Staging
deploy:production:       # Blue-Green switch auf Production (shell)
smoke:production:        # Smoke Tests gegen Production
maintenance:docker-cleanup:  # Entfernt ungenutzte Docker-Artefakte (>7 Tage)
rollback:production:     # Manuell bei Problemen (automatisch bei Smoke-Failure)
```

**Runner-Zuordnung:**
- `tags: [shell]` — Jobs auf dem Production-Server (141.75.150.128)
- `tags: [shell-dev]` — Jobs auf dem Dev-Server (141.75.150.86)
- Kein Tag — Docker Runner (shared, fuer Lint/Test/Security)

---

## 4. Deployment-Ablauf

### Dev-Pipeline (automatisch bei jedem Push auf `dev`)

```
Push → Lint → Test → Security → Build:docker:dev → Deploy:dev
  → E2E:dev + Smoke:dev → Switch:dev
```

1. Lint, Tests und Security laufen (Docker Runner)
2. `build:docker:dev` baut Images auf dem Dev-Server (shell-dev Runner)
3. `deploy:dev` deployt Blue-Green auf llars-dev (inaktive Farbe)
4. `e2e:dev` und `smoke:dev` testen parallel gegen die Staging-Instanz
5. `switch:dev` schaltet nginx auf die neue Farbe um

### Main-Pipeline (Nightly Schedule Mo-Fr 02:00 CET)

```
Schedule → Lint → Test → Security → Build:docker → Deploy:staging
  → E2E:nightly + Smoke:staging → Deploy:production → Smoke:production
```

1. Lint, Tests und Security laufen (Docker Runner)
2. `build:docker` baut Images auf dem Production-Server (shell Runner)
3. `deploy:staging` deployt Blue-Green auf Staging (:55080, inaktive Farbe)
4. `test:e2e:nightly:tiles` und `smoke:staging` testen gegen Staging
5. `deploy:production` schaltet nginx auf die neue Farbe um
6. `smoke:production` verifiziert die Live-Instanz

### Dryrun-Pipeline (Staging ohne Production)

```
Push [dryrun] → Lint → Test → Security → Build → Deploy:staging
  → E2E → Smoke:staging → STOP (kein Production-Deploy)
```

Nuetzlich um vor dem Nightly-Lauf zu pruefen, ob die Pipeline durchlaufen wird.

### Bei Fehlern

Blue-Green Deployment ermoeglicht sofortiges Rollback (~2 Sekunden):

```
Smoke:production FAIL → rollback_bluegreen.sh
  → nginx wird auf vorherige Farbe zurueckgeschaltet
  → Kein Datenverlust, alte Container laufen weiter
```

State-Dateien unter `.deploy/`:
- `active_color` — aktuell aktive Farbe (blue/green)
- `previous_color` — vorherige Farbe fuer Rollback
- `rollback.env` — Commit-SHA der vorherigen Version

### Manueller Rollback

```bash
# In GitLab: Pipeline → rollback:production → Play Button
# Oder auf dem Server:
cd /var/llars && bash scripts/ci/rollback_bluegreen.sh
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
# LLARS Ports
sudo ufw allow 55080/tcp  # HTTP (Staging)
sudo ufw allow 80/tcp     # HTTP (Production)
sudo ufw allow 443/tcp    # HTTPS (Production)
```

---

## 6. Erste Pipeline ausführen

### 1. Repository vorbereiten

```bash
# Lokale Entwicklung
git checkout dev
git add .gitlab-ci.yml docs/testing/CICD_SETUP.md
git commit -m "ci: add GitLab CI/CD pipeline for automated deployment"
git push origin dev
```

### 2. Pipeline prüfen

1. Gehe zu **CI/CD → Pipelines**
2. Pipeline sollte starten
3. Prüfe jeden Stage

### 3. Merge zu main (triggert Nightly Production Deploy)

```bash
git checkout main
git merge dev
git push origin main
# → Lint + Tests laufen sofort
# → Nightly Schedule (Mo-Fr 02:00) deployt auf Production
# → Oder: FORCE_DEPLOY=true in GitLab UI fuer sofortiges Deploy
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

dev:
  - Allowed to merge: Developers
  - Allowed to push: Developers
```

### Merge Request Workflow

1. Feature-Branch von `dev` erstellen
2. Entwickeln und committen
3. MR zu `dev` erstellen
4. Pipeline muss erfolgreich sein
5. Code Review
6. Merge zu `dev` → Auto-Deploy zu llars-dev (141.75.150.86)
7. Testen auf llars-dev
8. Wenn stabil: `dev` in `main` mergen
9. Nightly Schedule (02:00 CET) deployt automatisch auf Production
10. Bei Bedarf: `FORCE_DEPLOY=true` fuer sofortiges Production-Deploy

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

### Einmalige Einrichtung (Production-Server 141.75.150.128)

- [ ] GitLab Runner installiert (`gitlab-runner`)
- [ ] Runner registriert mit Shell Executor, Tag: `shell`
- [ ] Runner zur `docker` Gruppe hinzugefuegt
- [ ] `/var/llars` Verzeichnis erstellt
- [ ] Git Repository geklont
- [ ] `.env` Datei konfiguriert
- [ ] Berechtigungen: `gitlab-runner` Gruppe hat Schreibzugriff

### Einmalige Einrichtung (Dev-Server 141.75.150.86)

- [ ] GitLab Runner installiert (`gitlab-runner`)
- [ ] Runner registriert mit Shell Executor, Tag: `shell-dev`
- [ ] Runner zur `docker` Gruppe hinzugefuegt
- [ ] `/var/llars` Verzeichnis erstellt
- [ ] `.env` mit `LLARS_PRODUCTION_BRANCH=dev` konfiguriert
- [ ] Berechtigungen: `gitlab-runner` Gruppe hat Schreibzugriff

### GitLab Konfiguration

- [ ] Alle 3 Runner in GitLab sichtbar (Settings → CI/CD → Runners)
- [ ] Branch Protection konfiguriert (main: nur Maintainers)
- [ ] `requirements-test.txt` vorhanden (ohne torch/flair)
- [ ] Pipeline Schedule: Mo-Fr 02:00, Branch: main, `SCHEDULED_DEPLOY=true`
- [ ] CI Variables: `SYSTEM_ADMIN_API_KEY`, `E2E_TEST_PASSWORD`

### Test-Pipeline

- [ ] lint:backend/frontend erfolgreich (oder allow_failure)
- [ ] test:unit:backend erfolgreich
- [ ] test:unit:frontend erfolgreich
- [ ] test:integration erfolgreich
- [ ] test:nightly:contracts erfolgreich
- [ ] build:docker:dev erfolgreich (dev Branch)
- [ ] deploy:dev + smoke:dev + switch:dev erfolgreich
- [ ] build:docker erfolgreich (main Branch)
- [ ] deploy:staging + test:e2e:nightly:tiles + smoke:staging erfolgreich
- [ ] deploy:production + smoke:production erfolgreich

### Verifizierung

```bash
# Pipeline-Status prüfen
open "https://git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars/-/pipelines"

# Server-Health prüfen (auf dem Server)
curl http://localhost/auth/health_check
docker compose ps
```

---

**Letzte Aktualisierung:** 18. März 2026
