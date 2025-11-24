# Authentik Integration (OIDC)

This repository now uses Authentik as the identity provider (no Keycloak needed). The Docker stack runs Authentik server, worker, Postgres, and Redis alongside the existing services.

## Services & Ports
- Authentik UI/API: `http://localhost:${AUTHENTIK_EXTERNAL_PORT}` (default 55090 in `.env`, 55095 in `.env.development`)
- Backend API: `http://localhost:${NGINX_EXTERNAL_PORT}/api`
- Frontend: `http://localhost:${NGINX_EXTERNAL_PORT}`
- Authentik is also proxied via Nginx at `/authentik/` on the frontend host/port.

## Environment Variables (see `.env` / `.env.development`)
- `AUTHENTIK_SECRET_KEY`: Shared secret for Authentik.
- `AUTHENTIK_DB_*`: Postgres settings for Authentik.
- `AUTHENTIK_INTERNAL_PORT` / `AUTHENTIK_EXTERNAL_PORT`: Container/host ports.
- `AUTHENTIK_BOOTSTRAP_EMAIL` / `AUTHENTIK_BOOTSTRAP_PASSWORD`: Initial admin.
- `AUTHENTIK_ISSUER_URL`: OIDC issuer for the backend (per Authentik Application).
- `AUTHENTIK_[FRONTEND|BACKEND]_CLIENT_ID` and `AUTHENTIK_BACKEND_CLIENT_SECRET`: OIDC clients.

## Authentik Setup (minimal)
1. Navigate to `http://localhost:${AUTHENTIK_EXTERNAL_PORT}/if/flow/initial-setup/` and create the admin.
2. Create an OIDC Application for the backend (`llars-backend`, confidential):
   - Redirect URIs: `http://localhost:${NGINX_EXTERNAL_PORT}/*`
   - Scopes: `openid profile email`
   - Copy the client secret; update `.env*`.
3. (Optional) Create a public OIDC Application for the frontend (`llars-frontend`, PKCE).
4. Create groups/roles (`admin`, `viewer`, `rater`) and map them into the `roles` claim (Property Mapping → include in Access/ID tokens).
5. Create users (e.g., `testadmin`) and assign groups.

## Backend Notes
- Token validation now reads `AUTHENTIK_ISSUER_URL`, `AUTHENTIK_BACKEND_CLIENT_ID`, `AUTHENTIK_BACKEND_CLIENT_SECRET`.
- Audience is checked against the configured client ID; issuer is matched loosely to allow proxied hosts.

## Running
```bash
./start_llars.sh dev
# Authentik UI: http://localhost:55095 (dev) or http://localhost:55090 (default)
```
