---
name: ci-cd-debugging
description: Debug and monitor GitLab CI/CD pipelines for the LLARS project. Use when checking pipeline status, viewing job logs, troubleshooting failed pipelines, or when user mentions CI, CD, pipeline, GitLab, or deployment issues.
---

# CI/CD Debugging for LLARS

## GitLab Project Info

- **GitLab URL**: git.informatik.fh-nuernberg.de/kiz-nlp/llars/llars
- **Project ID**: 7123
- **Server**: 141.75.150.128 (internes Netz)
- **SSH Alias**: `ssh llars`

## Prerequisites

### API Token
The GitLab token must have **`api`** scope (not just `read_api`) to access job logs.

**IMPORTANT**: Do NOT use `source .env` - the .env has special chars that break bash parsing. Use:
```bash
GITLAB_TOKEN=$(grep '^GITLAB_TOKEN=' .env | cut -d= -f2-)
GITLAB_PROJECT_ID=$(grep '^GITLAB_PROJECT_ID=' .env | cut -d= -f2-)
```

### Server Access
SSH access via configured alias:
```bash
ssh llars
```

### Runners
- **Runner 515**: Docker runner (for lint, test, security, build jobs) - runs sequentially (only 1)
- **Runner 517**: Shell runner `llars-server-shell` (for deploy, smoke, rollback jobs) - direct server access

## API Commands

### List Recent Pipelines

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines?per_page=5" | \
  python3 -c "import sys,json; [print(f'#{p[\"id\"]}: {p[\"status\"]} ({p[\"source\"]}, {p[\"ref\"]})') for p in json.load(sys.stdin)]"
```

### Get Pipeline Jobs

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines/{PIPELINE_ID}/jobs?per_page=30" | \
  python3 -c "import sys,json; [print(f'{j[\"name\"]:25} {j[\"status\"]:10} {(j.get(\"duration\") or 0):.0f}s') for j in sorted(json.load(sys.stdin), key=lambda j: j['id'])]"
```

### Get Job Logs

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/jobs/{JOB_ID}/trace" | tail -50
```

### Validate CI Config

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/ci/lint?ref=main" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Valid: {d.get(\"valid\")}'); [print(f'Error: {e}') for e in d.get('errors',[])]"
```

### Trigger New Pipeline (with FORCE_DEPLOY)

```bash
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipeline" \
  -d '{"ref":"main","variables":[{"key":"FORCE_DEPLOY","value":"true"}]}'
```

### Cancel/Retry Pipeline

```bash
# Cancel
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines/{PIPELINE_ID}/cancel"

# Retry
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/$GITLAB_PROJECT_ID/pipelines/{PIPELINE_ID}/retry"
```

## Pipeline Architecture (since 2026-03-02)

### Stages & Jobs

| Stage | Jobs | Runner | Trigger |
|-------|------|--------|---------|
| lint | lint:backend, lint:frontend | Docker | Push/MR |
| test | test:unit:backend, test:unit:frontend, test:integration, metrics:collect | Docker | Push/MR |
| security | security:routes, security:scan | Docker | Push/MR |
| build | build:docker | Docker | main only |
| **deploy-staging** | deploy:staging | Shell | Schedule/Force/Manual |
| **test-staging** | test:e2e:staging, smoke:staging | Shell | After staging |
| **deploy** | deploy:production | Shell | After staging tests |
| **smoke** | smoke:production, metrics:update-docs | Shell | After prod deploy |
| rollback | rollback:production | Shell | Manual/Auto on smoke fail |

### Deployment Flow

```
Nightly 02:00 CET (or FORCE_DEPLOY=true):
  deploy:staging (Port 55080, separate containers)
    → test:e2e:staging (Playwright in smoke-test container)
    → smoke:staging (API-based evaluation + prompt engineering test)
    → deploy:production (Port 80/443)
    → smoke:production (health + wizard + evaluation + prompt eng)
    → [FAIL] → rollback:production (auto)
```

### Nightly Schedule
- **ID**: 8
- **Cron**: `0 2 * * 1-5` (Mon-Fri 02:00 CET)
- **Variable**: `SCHEDULED_DEPLOY=true`

### Key Scripts
| Script | Purpose |
|--------|---------|
| `scripts/ci/deploy_staging_bluegreen.sh` | Blue-green staging on :55080 |
| `scripts/ci/deploy_production.sh` | Prod deploy + health wait + staging cleanup |
| `scripts/ci/rollback_production.sh` | Rollback with DB restore timeout |
| `scripts/ci/smoke_test.sh` | Master smoke (calls sub-scripts) |
| `scripts/ci/smoke_test_evaluation.sh` | Evaluation pipeline CRUD test |
| `scripts/ci/smoke_test_prompt_eng.sh` | Prompt template CRUD test |
| `scripts/ci/wait_for_health.sh` | Health check waiter |
| `scripts/smoke_test_wizard.sh` | Chatbot wizard workflow test |

### Smoke Test Container
```bash
# Build
docker compose --profile testing build smoke-test-service

# Run smoke tests
docker compose --profile testing run --rm \
  -e BASE_URL=http://localhost:55080 \
  -e SYSTEM_ADMIN_API_KEY="..." \
  smoke-test-service bash /tests/smoke/smoke_test.sh

# Run E2E tests
docker compose --profile testing run --rm \
  -e PLAYWRIGHT_BASE_URL=http://localhost:55080 \
  smoke-test-service bash -c "cd /tests/e2e && npx playwright test --project=chromium --workers=1"
```

## Common Issues

### Pipeline has 0 jobs
- Check if another pipeline is running (auto-cancel might be active)
- Validate YAML: use the lint endpoint above
- Check rules conditions match the branch

### lint:backend fails with F402
- Usually a shadowed import in a loop
- Fix: remove the redundant inner import (top-level already has it)

### Deploy/smoke jobs stuck pending
- Shell runner (ID=517) might be busy with another job
- Cancel competing pipelines first
- Check runner: `ssh llars "sudo gitlab-runner status"`

### Smoke test fails: "SYSTEM_ADMIN_API_KEY not set"
- Shell runner jobs load it from `/var/llars/.env` via `grep '^SYSTEM_ADMIN_API_KEY=' .env | cut -d= -f2-`
- Verify key exists on server: `ssh llars "grep SYSTEM_ADMIN_API_KEY /var/llars/.env"`

### E2E tests fail in container
- Container uses `network_mode: host` to reach localhost:55080
- Staging must be running and healthy before E2E starts
- Check staging health: `curl http://localhost:55080/auth/health_check`

### Job logs return 401 Unauthorized
- Token needs `api` scope, not just `read_api`
- Create new token at: https://git.informatik.fh-nuernberg.de/-/user_settings/personal_access_tokens

## SSH Server Commands

### Check App Status
```bash
ssh llars "docker ps --format 'table {{.Names}}\t{{.Status}}'"
ssh llars "curl -s http://localhost/auth/health_check"
```

### Check Runner
```bash
ssh llars "sudo gitlab-runner status"
ssh llars "journalctl -u gitlab-runner --since '1 hour ago' | tail -50"
```

### Check Staging
```bash
ssh llars "curl -s http://localhost:55080/auth/health_check"
ssh llars "docker ps --filter name=staging"
```
