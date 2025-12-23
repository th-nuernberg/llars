# Authentik Setup für LLARS

LLARS nutzt **Authentik (OIDC)** und richtet die benötigten Flows/Clients beim Start automatisch ein (Container `llars_authentik_init`).

## Start (Development)

```bash
cp .env.template.development .env
./start_llars.sh
```

## URLs (Development Defaults)

- LLARS: `http://localhost:55080`
- Authentik UI (optional direkt): `http://localhost:55095`
- Authentik via nginx: `http://localhost:55080/authentik/`

## Test-User (Development)

| Username | Passwort | Rolle |
|----------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| viewer | admin123 | viewer |

## Verifizieren / Debug

```bash
docker compose -p llars ps
docker compose -p llars logs authentik-init --tail=200
docker compose -p llars logs authentik-server --tail=200
```

Optional:

```bash
./scripts/verify_authentik.sh
```

Manueller Fallback (falls Auto-Setup fehlschlägt):

```bash
./scripts/setup_authentik.sh
```

## Production Hinweise

- `PROJECT_URL`/`AUTHENTIK_PUBLIC_URL` korrekt setzen (HTTPS empfohlen)
- Secrets in `.env` setzen (siehe `.env.template.production`)
- Zertifikate unter `docker/nginx/certs/` bereitstellen und nginx-prod Config nutzen
