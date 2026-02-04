# Authentik Setup for LLARS

LLARS uses **Authentik (OIDC)** and automatically provisions the required flows/clients on startup (container `llars_authentik_init`).

## Start (Development)

```bash
cp .env.template.development .env
./start_llars.sh
```

## URLs (Development Defaults)

- LLARS: `http://localhost:55080`
- Authentik UI (optional direct): `http://localhost:55095`
- Authentik via nginx: `http://localhost:55080/authentik/`

## Test Users (Development)

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| evaluator | admin123 | evaluator |

## Verify / Debug

```bash
docker compose -p llars ps
docker compose -p llars logs authentik-init --tail=200
docker compose -p llars logs authentik-server --tail=200
```

Optional:

```bash
./scripts/verify_authentik.sh
```

Manual fallback (if auto-setup fails):

```bash
./scripts/setup_authentik.sh
```

## Production Notes

- Set `PROJECT_URL`/`AUTHENTIK_PUBLIC_URL` correctly (HTTPS recommended)
- Set secrets in `.env` (see `.env.template.production`)
- Provide certificates under `docker/nginx/certs/` and use the nginx prod config
