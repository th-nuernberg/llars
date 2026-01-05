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
Token is stored in `.env`:

```bash
source .env
# GITLAB_TOKEN is now available
```

### Server Access
SSH access via configured alias:
```bash
ssh llars
```

### Server Environment (as of 2026-01-05)
- **Node.js**: v20.19.6 (installed at /usr/bin/node)
- **npm**: 10.8.2 (installed at /usr/bin/npm)
- **Playwright deps**: installed for chromium
- **gitlab-runner**: has access to node/npm

## API Commands

### List Recent Pipelines

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/7123/pipelines?per_page=5" | \
  python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'#{p[\"id\"]}: {p[\"status\"]} ({p[\"sha\"][:7]})') for p in data]"
```

### Get Pipeline Jobs

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/7123/pipelines/{PIPELINE_ID}/jobs" | \
  python3 -c "import sys,json; data=json.load(sys.stdin); [print(f'{j[\"name\"]}: {j[\"status\"]}') for j in data]"
```

### Get Job Logs

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/7123/jobs/{JOB_ID}/trace" | tail -50
```

### Validate CI Config

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/7123/ci/lint?ref=main" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Valid: {d.get(\"valid\")}'); [print(f'Error: {e}') for e in d.get('errors',[])]"
```

### Trigger New Pipeline

```bash
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/7123/pipeline?ref=main"
```

### Retry Failed Pipeline

```bash
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/7123/pipelines/{PIPELINE_ID}/retry"
```

### Cancel Running Pipeline

```bash
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://git.informatik.fh-nuernberg.de/api/v4/projects/7123/pipelines/{PIPELINE_ID}/cancel"
```

## Pipeline Stages

| Stage | Jobs |
|-------|------|
| lint | lint:backend, lint:frontend |
| test | test:unit:backend, test:unit:frontend, test:integration, test:e2e |
| build | build:docker |
| deploy | deploy:staging (develop), deploy:production (main) |

## Common Issues

### Pipeline fails with 0 jobs
- Check if another pipeline is running (auto-cancel might be active)
- Validate YAML syntax with the lint endpoint
- Check rules conditions match the branch

### E2E tests fail
- Tests run on shell runner against deployed app at localhost
- Ensure app is running on server: `ssh llars "docker ps"`
- Check PLAYWRIGHT_BASE_URL is correct (should be `http://localhost`)
- Verify npm is available: `ssh llars "which npm node"`

### "npm: command not found" in E2E
- Node.js must be installed globally on the server
- Install with: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt install -y nodejs`
- Install Playwright deps: `sudo npx playwright install-deps chromium`

### Job logs return 401 Unauthorized
- Token needs `api` scope, not just `read_api`
- Create new token at: https://git.informatik.fh-nuernberg.de/-/user_settings/personal_access_tokens
- Update token in `.env` file

### Job stuck pending
- Check runner availability with `tags: [shell]`
- Verify runner is online in GitLab Admin
- Check runner status: `ssh llars "sudo gitlab-runner status"`

## SSH Server Commands

### Check App Status
```bash
ssh llars "docker ps --format 'table {{.Names}}\t{{.Status}}'"
ssh llars "curl -s http://localhost | head -20"
```

### Check Runner Logs
```bash
ssh llars "journalctl -u gitlab-runner --since '1 hour ago' | tail -50"
```

### Check Build Directory
```bash
ssh llars "ls -la /home/gitlab-runner/builds/"
```

### Restart Services
```bash
ssh llars "cd /var/llars && docker compose restart"
```

## Deployment Flow

```
Push to develop -> deploy:staging (auto)
Push to main    -> lint -> test -> build -> deploy:production -> smoke tests
```
