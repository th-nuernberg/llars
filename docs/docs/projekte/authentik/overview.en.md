# Authentik Integration (OIDC)

LLARS uses **Authentik** as its identity provider (Keycloak has been removed). In development, Authentik is automatically configured on startup (container `llars_authentik_init`).

## Services & URLs (development defaults)

- LLARS: `http://localhost:55080`
- Authentik UI (optional direct): `http://localhost:55095`
- Authentik via nginx: `http://localhost:55080/authentik/`

## Important variables (`.env`)

- `AUTHENTIK_SECRET_KEY` - Django secret, >= 50 characters
- `AUTHENTIK_DB_NAME`, `AUTHENTIK_DB_USER`, `AUTHENTIK_DB_PASSWORD` - PostgreSQL configuration
- `AUTHENTIK_PUBLIC_URL` - public URL for redirects (e.g. `http://localhost:55095` or `https://<domain>/authentik`)
- `AUTHENTIK_INTERNAL_URL` - internal URL for services (default: `http://authentik-server:9000`)
- `AUTHENTIK_ISSUER_URL` - OIDC issuer for token validation (default: `http://authentik-server:9000/application/o/llars-backend/`)
- `AUTHENTIK_BOOTSTRAP_EMAIL`, `AUTHENTIK_BOOTSTRAP_PASSWORD` - admin on first start
- `LLARS_ADMIN_PASSWORD` - password for LLARS test users (admin, researcher, evaluator, chatbot_manager)
- `AUTHENTIK_BACKEND_CLIENT_SECRET` - backend OAuth secret (client ID is invariant: `llars-backend`)
- `AUTHENTIK_API_TOKEN` - admin API token for user management (created by `authentik-init`)
- `AUTHENTIK_MATOMO_CLIENT_ID`, `AUTHENTIK_MATOMO_CLIENT_SECRET`, `AUTHENTIK_MATOMO_APP_SLUG` - Matomo OIDC (optional)

## Auto-setup on start

On startup, `authentik-init` creates (idempotent):
- Authentication flow: `llars-api-authentication`
- OAuth2 provider + application: `llars-backend`
- OAuth2 provider + application (Matomo SSO): `llars-matomo` with redirects for `/analytics/` (and legacy `/matomo/`)
- Default users (development): `admin`, `researcher`, `evaluator`, `chatbot_manager` (password: `LLARS_ADMIN_PASSWORD`)
- Admin API token: `llars-admin-api-token` (on user `akadmin` or `admin`)

## Reset / rebuild

```bash
REMOVE_LLARS_VOLUMES=True ./start_llars.sh
```

Warning: deletes all data including the Authentik DB.
