# Authentik Authentication Setup

## Übersicht

LLARS verwendet Authentik als OIDC-Provider für die Authentifizierung. Die Konfiguration erfolgt automatisch beim Start basierend auf dem `PROJECT_STATE`.

## Automatische Konfiguration

Der `authentik-init` Container läuft bei jedem `docker compose up` und konfiguriert:

1. **Authentication Flow** (`llars-api-authentication`)
2. **OAuth2 Provider** (`llars-backend`, `llars-matomo`)
3. **Applications** (`llars-backend`, `llars-matomo`)
4. **Admin API Token** für User-Management

## User-Erstellung nach Environment

### Production (`PROJECT_STATE=production`)

| User | Passwort | Erstellt |
|------|----------|----------|
| admin | `LLARS_ADMIN_PASSWORD` | ✅ |
| researcher | - | ❌ |
| viewer | - | ❌ |

### Development (`PROJECT_STATE=development`)

| User | Passwort | Erstellt |
|------|----------|----------|
| admin | `LLARS_ADMIN_PASSWORD` | ✅ |
| researcher | `LLARS_ADMIN_PASSWORD` | ✅ |
| viewer | `LLARS_ADMIN_PASSWORD` | ✅ |

## Environment-Variablen

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `PROJECT_STATE` | `production` oder `development` | `development` |
| `LLARS_ADMIN_PASSWORD` | Passwort für LLARS-User | `admin123` |
| `AUTHENTIK_BACKEND_CLIENT_SECRET` | OAuth2 Client Secret | (generiert) |
| `AUTHENTIK_BOOTSTRAP_PASSWORD` | Authentik akadmin Passwort | `admin123` |

## Passwort-Priorität

Das Init-Skript verwendet folgende Priorität für Passwörter:

```
LLARS_ADMIN_PASSWORD → AUTHENTIK_BOOTSTRAP_PASSWORD → "admin123"
```

## Verhalten bei Neustart

- **Passwörter werden bei jedem Start aus `.env` geladen** und auf die User angewendet
- **User werden nicht gelöscht** - existierende User bleiben erhalten
- **OAuth Provider werden nur erstellt wenn sie fehlen** - existierende Provider werden nicht überschrieben

## Manuelles Setup

Falls das automatische Setup nicht funktioniert, kann das manuelle Setup-Skript verwendet werden:

```bash
./scripts/setup_authentik.sh
```

Dieses Skript ist ebenfalls environment-aware und verwendet `PROJECT_STATE` sowie `LLARS_ADMIN_PASSWORD`.

## Zusätzliche User anlegen

Für zusätzliche User (z.B. Projektmitarbeiter) siehe:

```bash
./scripts/provision_users.sh
```

## Troubleshooting

### Login funktioniert nicht

1. Prüfen ob Authentik läuft: `docker compose ps | grep authentik`
2. Logs prüfen: `docker compose logs authentik-server`
3. Client Secret prüfen: `.env` vs. Authentik Provider

### User existiert nicht

1. Init-Container Logs prüfen: `docker compose logs authentik-init`
2. Manuell User anlegen: Admin Panel → Users → Create User

### Passwort falsch

Das Passwort wird bei jedem Start aus `.env` geladen. Prüfen:

```bash
grep LLARS_ADMIN_PASSWORD .env
```
