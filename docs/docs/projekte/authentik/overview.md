# Authentik Integration (OIDC)

LLARS nutzt Authentik als Identity Provider (Keycloak wird nicht mehr benötigt). Im Stack laufen Authentik-Server, Worker, PostgreSQL und Redis neben den bestehenden Services.

## Services & Ports
- Authentik UI/API: `http://localhost:${AUTHENTIK_EXTERNAL_PORT}` (Standard 55095 in Development)
- Frontend: `http://localhost:${NGINX_EXTERNAL_PORT}`
- Backend API: `http://localhost:${NGINX_EXTERNAL_PORT}/api`
- Authentik ist zusätzlich über nginx unter `/authentik/` erreichbar.

## Wichtige Variablen (`.env`)
- `AUTHENTIK_SECRET_KEY` – Django Secret, mind. 50 Zeichen
- `AUTHENTIK_DB_*` – PostgreSQL-Konfiguration für Authentik
- `AUTHENTIK_INTERNAL_PORT` / `AUTHENTIK_EXTERNAL_PORT`
- `AUTHENTIK_BOOTSTRAP_EMAIL` / `AUTHENTIK_BOOTSTRAP_PASSWORD` – Admin beim Erststart
- `AUTHENTIK_ISSUER_URL` – OIDC-Issuer für das Backend
- `AUTHENTIK_FRONTEND_CLIENT_ID`, `AUTHENTIK_BACKEND_CLIENT_ID`, `AUTHENTIK_BACKEND_CLIENT_SECRET`

## Kurzanleitung Setup
1. `http://localhost:${AUTHENTIK_EXTERNAL_PORT}/if/flow/initial-setup/` öffnen und Admin anlegen.
2. OIDC-Application Backend (`llars-backend`, confidential) erstellen:
   - Redirect URI: `http://localhost:${NGINX_EXTERNAL_PORT}/*`
   - Scopes: `openid profile email`
   - Client-Secret kopieren und in `.env` eintragen.
3. Optional: Public OIDC-Application für das Frontend (`llars-frontend`, PKCE).
4. Gruppen/Rollen (`admin`, `viewer`, `rater`) anlegen und im `roles`-Claim mappen.
5. Nutzer anlegen und Gruppen zuweisen.

## Backend-Hinweise
- Token-Validierung liest `AUTHENTIK_ISSUER_URL`, `AUTHENTIK_BACKEND_CLIENT_ID`, `AUTHENTIK_BACKEND_CLIENT_SECRET`.
- Audience-Check gegen Client-ID; Issuer wird tolerant gegenüber Proxy-Host geprüft.

## Start
```bash
./start_llars.sh dev
# Authentik UI: http://localhost:55095 (Dev-Default)
```
