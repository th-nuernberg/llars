# Authentik Integration (OIDC)

LLARS nutzt **Authentik** als Identity Provider (Keycloak ist entfernt). In Development wird Authentik beim Start automatisch konfiguriert (Container `llars_authentik_init`).

## Services & URLs (Development Defaults)

- LLARS: `http://localhost:55080`
- Authentik UI (optional direkt): `http://localhost:55095`
- Authentik via nginx: `http://localhost:55080/authentik/`

## Wichtige Variablen (`.env`)

- `AUTHENTIK_SECRET_KEY` – Django Secret, ≥ 50 Zeichen
- `AUTHENTIK_DB_NAME`, `AUTHENTIK_DB_USER`, `AUTHENTIK_DB_PASSWORD` – PostgreSQL-Konfiguration
- `AUTHENTIK_PUBLIC_URL` – Public URL für Redirects (z. B. `http://localhost:55095` oder `https://<domain>/authentik`)
- `AUTHENTIK_INTERNAL_URL` – Interne URL für Services (Default: `http://authentik-server:9000`)
- `AUTHENTIK_ISSUER_URL` – OIDC Issuer für Token-Validierung (Default: `http://authentik-server:9000/application/o/llars-backend/`)
- `AUTHENTIK_BOOTSTRAP_EMAIL`, `AUTHENTIK_BOOTSTRAP_PASSWORD` – Admin beim Erststart
- `LLARS_ADMIN_PASSWORD` – Passwort für LLARS Test-User (admin, researcher, evaluator, chatbot_manager)
- `AUTHENTIK_BACKEND_CLIENT_SECRET` – Backend OAuth Secret (Client-ID ist invariant: `llars-backend`)
- `AUTHENTIK_API_TOKEN` – Admin API Token für Benutzerverwaltung (wird von `authentik-init` erzeugt)
- `AUTHENTIK_MATOMO_CLIENT_ID`, `AUTHENTIK_MATOMO_CLIENT_SECRET`, `AUTHENTIK_MATOMO_APP_SLUG` – Matomo OIDC (optional)

## Auto-Setup beim Start

Beim Start legt `authentik-init` u. a. an (idempotent):
- Authentication Flow: `llars-api-authentication`
- OAuth2 Provider + Application: `llars-backend`
- OAuth2 Provider + Application (Matomo SSO): `llars-matomo` inkl. Redirects für `/analytics/` (und Legacy `/matomo/`)
- Default-User (Development): `admin`, `researcher`, `evaluator`, `chatbot_manager` (Passwort: `LLARS_ADMIN_PASSWORD`)
- Admin API Token: `llars-admin-api-token` (auf User `akadmin` oder `admin`)

## Reset / Neuaufbau

```bash
REMOVE_LLARS_VOLUMES=True ./start_llars.sh
```

⚠️ Löscht alle Daten inkl. Authentik-DB.
