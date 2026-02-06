# Authentik Authentication Setup

## Overview

LLARS uses Authentik as the OIDC provider for authentication. Configuration is performed automatically on startup via the `authentik-init` container (script: `docker/authentik/init-authentik.sh`).

## Automatic Configuration

The `authentik-init` container runs on every `docker compose up` and configures:

1. **Authentication Flow** (`llars-api-authentication`)
2. **Provider Authorization Flow** (default or `llars-provider-authorization`)
3. **OAuth2 Providers** (`llars-backend`, `llars-matomo` including Matomo redirects)
4. **Applications** (`llars-backend`, `AUTHENTIK_MATOMO_APP_SLUG`)
5. **Users** (admin always, `researcher`/`evaluator`/`chatbot_manager` only in development)
6. **Admin API Token** (`llars-admin-api-token`) for user management

## User Creation by Environment

### Production (`PROJECT_STATE=production`)

| User | Password | Created |
|------|----------|---------|
| admin | `LLARS_ADMIN_PASSWORD` | ✅ |
| researcher | - | ❌ |
| evaluator | - | ❌ |
| chatbot_manager | - | ❌ |

### Development (`PROJECT_STATE=development`)

| User | Password | Created |
|------|----------|---------|
| admin | `LLARS_ADMIN_PASSWORD` | ✅ |
| researcher | `LLARS_ADMIN_PASSWORD` | ✅ |
| evaluator | `LLARS_ADMIN_PASSWORD` | ✅ |
| chatbot_manager | `LLARS_ADMIN_PASSWORD` | ✅ |

**Note:** The admin password is set on every start. Development users are created only if missing.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_STATE` | `production` or `development` | `development` |
| `PROJECT_URL` | Explicit base URL (overrides host/port) | (empty) |
| `PROJECT_HOST` | Hostname used to build base URL | `localhost` |
| `NGINX_EXTERNAL_PORT` | Port for base URL in development | `80` |
| `LLARS_ADMIN_PASSWORD` | Password for LLARS users | `admin123` |
| `AUTHENTIK_BOOTSTRAP_PASSWORD` | Authentik `akadmin` password (fallback) | `admin123` |
| `AUTHENTIK_BACKEND_CLIENT_ID` | Backend client ID (do not change) | `llars-backend` |
| `AUTHENTIK_BACKEND_CLIENT_SECRET` | Backend OAuth2 client secret | `llars-backend-secret-change-in-production` |
| `AUTHENTIK_MATOMO_CLIENT_ID` | Matomo client ID | `llars-matomo` |
| `AUTHENTIK_MATOMO_CLIENT_SECRET` | Matomo client secret | `llars-matomo-secret-change-in-production` |
| `AUTHENTIK_MATOMO_APP_SLUG` | Matomo app slug | `llars-matomo` |
| `AUTHENTIK_API_TOKEN` | Fixed admin API token (optional) | (generated) |

**Base URL logic:** If `PROJECT_URL` is set, it is used. Otherwise `https://$PROJECT_HOST` in production and `http://$PROJECT_HOST:$NGINX_EXTERNAL_PORT` in development.

## Password Priority

The init script uses the following password priority:

```
LLARS_ADMIN_PASSWORD → AUTHENTIK_BOOTSTRAP_PASSWORD → "admin123"
```

## Behavior on Restart

- **Admin password is set on every start** (from `.env`)
- **Development users are created only if missing** (passwords remain unchanged)
- **Users are not deleted** - existing users stay
- **Backend provider is only created if missing** - existing providers stay unchanged
- **Matomo provider is updated** (e.g. redirect URIs, secret)
- **Applications are created or re-linked** if needed
- **Admin API token is replaced** (stable tokens via `AUTHENTIK_API_TOKEN`)

## Manual Setup

If the automatic setup does not work, use the manual setup script:

```bash
./scripts/setup_authentik.sh
```

This script is environment-aware and uses `PROJECT_STATE`, `PROJECT_URL`, `LLARS_ADMIN_PASSWORD`, and `AUTHENTIK_BACKEND_CLIENT_SECRET`.
It sets up **backend + frontend providers** (legacy flow) but **no Matomo OIDC** configuration.
Details: `scripts/README_AUTHENTIK_SETUP.md`.

## Adding Additional Users

- Use **Admin Dashboard → Users** (permission: `admin:users:manage`).
- Alternatively create users in Authentik. On first login, LLARS creates the local user automatically.

## Troubleshooting

### Login does not work

1. Check Authentik is running: `docker compose ps | grep authentik`
2. Check logs: `docker compose logs authentik-server`
3. Verify client secrets: `.env` vs Authentik providers (`llars-backend`, `llars-matomo`)

### User does not exist

1. Check init container logs: `docker compose logs authentik-init`
2. Create user manually: Admin Panel → Users → Create User

### Wrong password

Passwords are loaded from `.env` on every start. Check:

```bash
grep LLARS_ADMIN_PASSWORD .env
```
