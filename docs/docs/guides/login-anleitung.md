# LLARS Login-Anleitung (Authentik)

LLARS nutzt **Authentik (OIDC)** für Login/SSO. Das Setup erfolgt beim Start automatisch über den Container `llars_authentik_init`.

## Start (Development)

```bash
cp .env.template.development .env
./start_llars.sh
```

- LLARS: `http://localhost:55080`
- Authentik UI (optional direkt): `http://localhost:55095`

## Test-User (Development)

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| viewer | admin123 | viewer |

Die Rollen/Berechtigungen werden in der **LLARS-Datenbank** verwaltet (Admin → Berechtigungen).

## Troubleshooting

```bash
docker compose -p llars ps
docker compose -p llars logs authentik-server --tail=200
docker compose -p llars logs authentik-init --tail=200
docker compose -p llars logs backend-flask-service --tail=200
```

- **Login-Loop / bleibt auf Login-Seite:** Browser-Storage/Content-Blocker prüfen (insb. bei Safari/Extensions), danach Logout + Reload.
- **Authentik nicht erreichbar:** Health/Logs prüfen, ggf. `REMOVE_LLARS_VOLUMES=True ./start_llars.sh` (löscht Daten!).
