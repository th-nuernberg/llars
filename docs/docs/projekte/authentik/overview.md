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
- `AUTHENTIK_BOOTSTRAP_EMAIL`, `AUTHENTIK_BOOTSTRAP_PASSWORD` – Admin beim Erststart
- `AUTHENTIK_BACKEND_CLIENT_SECRET` – Backend OAuth Secret (Client-ID ist invariant: `llars-backend`)

## Auto-Setup beim Start

Beim Start legt `authentik-init` u. a. an (idempotent):
- Authentication Flow: `llars-api-authentication`
- OAuth2 Provider + Application: `llars-backend`
- OAuth2 Provider + Application (Matomo SSO): `llars-matomo` inkl. Redirects für `/analytics/` (und Legacy `/matomo/`)
- Default-User: `admin`, `researcher`, `evaluator` (Passwort: `admin123`)

## Reset / Neuaufbau

```bash
REMOVE_LLARS_VOLUMES=True ./start_llars.sh
```

⚠️ Löscht alle Daten inkl. Authentik-DB.
