# LLARS PROJECT_STATE Guide

## Overview

`PROJECT_STATE` controls whether LLARS runs in **development** or **production** mode. All services (Flask, Vue/Vite, Authentik, Yjs, nginx) receive this variable.

## Configuration

Set in `.env`:

```bash
# Development (default)
PROJECT_STATE=development

# Production
PROJECT_STATE=production
```

## Effects by Mode

### Development (`development`)
- Hot reload for frontend (Vite) and backend
- Entry via nginx (default: `http://localhost:55080`)
- MkDocs via nginx: `/mkdocs/` (dev)
- Optional direct access to Authentik/DB/MkDocs via external ports (defaults: 55095/55306/55800)
- Verbose logging
- Extended demo data (20-30 samples per scenario) is seeded automatically
- Debug ports only when needed (default compose keeps exposures minimal)

### Production (`production`)
- Optimized builds, no hot reload
- Less logging
- Access exclusively through nginx (80/443)
- Authentik expected behind nginx (HTTPS recommended)
- MkDocs via nginx: `/mkdocs/` (prod)

## Usage

### Start (Default: Development)
```bash
./start_llars.sh
# or explicitly
PROJECT_STATE=development ./start_llars.sh
```

### Switch to Production
1. Update `.env`:
   ```bash
   PROJECT_STATE=production
   ```
2. Restart:
   ```bash
   ./start_llars.sh prod
   ```

## Verify

```bash
docker compose ps
```

- Development: nginx (55080) and Authentik (55095) are reachable; frontend/backend run internally behind nginx.
- Production: only nginx port is exposed; all internal services run behind nginx (80/443).

## Troubleshooting

- **Wrong mode active?**  
  Check `.env` (`grep PROJECT_STATE .env`) and restart.

- **Authentik only reachable via HTTPS?**  
  In production, place Authentik behind nginx; for local tests use `development`.

- **Frontend without hot reload?**  
  Ensure `PROJECT_STATE=development` is active and the stack has been restarted (`./start_llars.sh`).

## Best Practices

- Development: `PROJECT_STATE=development`, use debug ports.
- Production: `PROJECT_STATE=production`, HTTPS in front of nginx, change default passwords.
- After changing the mode, always run `./start_llars.sh` again.

- [Authentik Setup](authentik-setup.md) - OIDC login with Authentik
- [Authentik Documentation](https://docs.goauthentik.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
