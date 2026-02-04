# LLARS Login Guide (Authentik)

LLARS uses **Authentik (OIDC)** for login/SSO. The setup is performed automatically on startup by the `llars_authentik_init` container.

## Start (Development)

```bash
cp .env.template.development .env
./start_llars.sh
```

- LLARS: `http://localhost:55080`
- Authentik UI (optional direct): `http://localhost:55095`

## Test Users (Development)

| User | Password | Role |
|------|----------|------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| evaluator | admin123 | evaluator |

Roles/permissions are managed in the **LLARS database** (Admin -> Permissions).

## Troubleshooting

```bash
docker compose -p llars ps
docker compose -p llars logs authentik-server --tail=200
docker compose -p llars logs authentik-init --tail=200
docker compose -p llars logs backend-flask-service --tail=200
```

- **Login loop / stuck on login page:** Check browser storage/content blockers (especially Safari/extensions), then logout + reload.
- **Authentik not reachable:** Check health/logs, if needed run `REMOVE_LLARS_VOLUMES=True ./start_llars.sh` (deletes data!).
