# Authentik Authentication Setup

## Übersicht

LLARS verwendet Authentik als OIDC-Provider für die Authentifizierung. Die Konfiguration erfolgt automatisch beim Start über den `authentik-init` Container (Script: `docker/authentik/init-authentik.sh`).

## Automatische Konfiguration

Der `authentik-init` Container läuft bei jedem `docker compose up` und konfiguriert:

1. **Authentication Flow** (`llars-api-authentication`)
2. **Provider Authorization Flow** (Default oder `llars-provider-authorization`)
3. **OAuth2 Provider** (`llars-backend`, `llars-matomo` inkl. Matomo-Redirects)
4. **Applications** (`llars-backend`, `AUTHENTIK_MATOMO_APP_SLUG`)
5. **User** (admin immer, `researcher`/`evaluator`/`chatbot_manager` nur in Development)
6. **Admin API Token** (`llars-admin-api-token`) für User-Management

## User-Erstellung nach Environment

### Production (`PROJECT_STATE=production`)

| User | Passwort | Erstellt |
|------|----------|----------|
| admin | `LLARS_ADMIN_PASSWORD` | ✅ |
| researcher | - | ❌ |
| evaluator | - | ❌ |
| chatbot_manager | - | ❌ |

### Development (`PROJECT_STATE=development`)

| User | Passwort | Erstellt |
|------|----------|----------|
| admin | `LLARS_ADMIN_PASSWORD` | ✅ |
| researcher | `LLARS_ADMIN_PASSWORD` | ✅ |
| evaluator | `LLARS_ADMIN_PASSWORD` | ✅ |
| chatbot_manager | `LLARS_ADMIN_PASSWORD` | ✅ |

**Hinweis:** Das Admin‑Passwort wird bei jedem Start gesetzt. Development‑User werden nur angelegt, falls sie fehlen.

## Environment-Variablen

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `PROJECT_STATE` | `production` oder `development` | `development` |
| `PROJECT_URL` | Explizite Base‑URL (überschreibt Host/Port) | (leer) |
| `PROJECT_HOST` | Hostname für Base‑URL‑Berechnung | `localhost` |
| `NGINX_EXTERNAL_PORT` | Port für Base‑URL in Development | `80` |
| `LLARS_ADMIN_PASSWORD` | Passwort für LLARS‑User | `admin123` |
| `AUTHENTIK_BOOTSTRAP_PASSWORD` | Authentik `akadmin` Passwort (Fallback) | `admin123` |
| `AUTHENTIK_BACKEND_CLIENT_ID` | Backend Client ID (nicht ändern) | `llars-backend` |
| `AUTHENTIK_BACKEND_CLIENT_SECRET` | Backend OAuth2 Client Secret | `llars-backend-secret-change-in-production` |
| `AUTHENTIK_MATOMO_CLIENT_ID` | Matomo Client ID | `llars-matomo` |
| `AUTHENTIK_MATOMO_CLIENT_SECRET` | Matomo Client Secret | `llars-matomo-secret-change-in-production` |
| `AUTHENTIK_MATOMO_APP_SLUG` | Matomo App Slug | `llars-matomo` |
| `AUTHENTIK_API_TOKEN` | Fixer Admin API Token (optional) | (generiert) |

**Base‑URL Logik:** Wenn `PROJECT_URL` gesetzt ist, wird es verwendet. Sonst `https://$PROJECT_HOST` in Production und `http://$PROJECT_HOST:$NGINX_EXTERNAL_PORT` in Development.

## Passwort-Priorität

Das Init-Skript verwendet folgende Priorität für Passwörter:

```
LLARS_ADMIN_PASSWORD → AUTHENTIK_BOOTSTRAP_PASSWORD → "admin123"
```

## Verhalten bei Neustart

- **Admin‑Passwort wird bei jedem Start gesetzt** (aus `.env`)
- **Development‑User werden nur angelegt, falls sie fehlen** (Passwörter bleiben unverändert)
- **User werden nicht gelöscht** - existierende User bleiben erhalten
- **Backend‑Provider wird nur erstellt wenn er fehlt** - existierende Provider bleiben unverändert
- **Matomo‑Provider wird aktualisiert** (z.B. Redirect URIs, Secret)
- **Applications werden erstellt oder neu verknüpft** falls nötig
- **Admin API Token wird ersetzt** (stabile Tokens via `AUTHENTIK_API_TOKEN`)

## Manuelles Setup

Falls das automatische Setup nicht funktioniert, kann das manuelle Setup-Skript verwendet werden:

```bash
./scripts/setup_authentik.sh
```

Dieses Skript ist ebenfalls environment-aware und verwendet u.a. `PROJECT_STATE`, `PROJECT_URL`, `LLARS_ADMIN_PASSWORD` und `AUTHENTIK_BACKEND_CLIENT_SECRET`.
Es richtet **Backend + Frontend Provider** (Legacy‑Flow) ein, aber **keine Matomo‑OIDC** Konfiguration.
Details: `scripts/README_AUTHENTIK_SETUP.md`.

## Zusätzliche User anlegen

- **Admin Dashboard → Users** verwenden (Recht: `admin:users:manage`).
- Alternativ User direkt in Authentik anlegen. Beim ersten Login erstellt LLARS den lokalen User automatisch.

## Troubleshooting

### Login funktioniert nicht

1. Prüfen ob Authentik läuft: `docker compose ps | grep authentik`
2. Logs prüfen: `docker compose logs authentik-server`
3. Client Secret prüfen: `.env` vs. Authentik Provider (`llars-backend`, `llars-matomo`)

### User existiert nicht

1. Init-Container Logs prüfen: `docker compose logs authentik-init`
2. Manuell User anlegen: Admin Panel → Users → Create User

### Passwort falsch

Das Passwort wird bei jedem Start aus `.env` geladen. Prüfen:

```bash
grep LLARS_ADMIN_PASSWORD .env
```
