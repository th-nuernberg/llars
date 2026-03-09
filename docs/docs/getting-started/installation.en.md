# Installation

## Prerequisites

- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- Docker Compose v2+
- Git
- At least 8 GB RAM for the containers

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd llars
```

### 2. Create environment variables

```bash
cp .env.template.development .env
# Adjust values as needed
```

Key switches:

```bash
PROJECT_STATE=development   # or production
REMOVE_LLARS_VOLUMES=False        # True deletes data on next start
PROJECT_URL=http://localhost:55080   # Entry point for frontend + API

# Optional: Host port overrides (defaults are preconfigured)
NGINX_EXTERNAL_PORT=55080
AUTHENTIK_EXTERNAL_PORT=55095
DB_EXTERNAL_PORT=55306              # Debug only
MKDOCS_EXTERNAL_PORT=55800
```

### 3. Start LLARS

```bash
chmod +x start_llars.sh
./start_llars.sh            # Quick start (uses cached images)
```

### Start Modes

| Command | Description | Duration |
|---------|-------------|----------|
| `./start_llars.sh` | Starts with cached images, no rebuild | ~30s |
| `./start_llars.sh --build` | Checks Dockerfiles for changes, rebuilds if needed | ~70s |
| `./start_llars.sh --detach` | Starts in background (no watch mode) | ~30s |
| `./start_llars.sh --build --detach` | Rebuild check + start in background | ~70s |
| `./start_llars.sh dev` | Force development mode | ~30s |
| `./start_llars.sh prod` | Force production mode | ~70s |
| `./start_llars.sh --update` | Rebuild only backend + frontend (quick update) | ~30s |

!!! tip "When to use which mode?"
    **Normal start** (code changes in Python/Vue/JS): `./start_llars.sh`
    Code changes are picked up automatically via volume mounts.

    **After dependency changes** (requirements.txt, package.json): `./start_llars.sh --build`
    Docker detects the change and only rebuilds affected layers.

    **After Dockerfile/Compose changes**: `./start_llars.sh --build`

**What the script does:**

1. Checks whether Docker is running (starts Docker if needed)
2. Stops only LLARS containers
3. Optionally removes only LLARS volumes (`REMOVE_LLARS_VOLUMES=True`)
4. Starts all services (with or without rebuild)

**Volumes affected:**
`REMOVE_LLARS_VOLUMES=True` removes **all** Docker volumes with the `llars_` prefix, e.g.:

- `llars_llarsdb` (MariaDB)
- `llars_rag_storage` / `llars_rag_docs` (RAG data)
- `llars_authentikdb` / `llars_authentik_media` (Authentik)
- `llars_matomo_data` / `llars_matomodb` (Analytics)
- `llars_redis_data` (Redis)

Other project volumes without the `llars_` prefix remain untouched.

### 4. Open services

After about 30 seconds (with cached images):

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik | http://localhost:55095 |
| Docs (direct) | http://localhost:55800 |
| Docs (via nginx, dev) | http://localhost:55080/mkdocs/ |

### 5. Verify installation

```bash
docker compose -p llars ps
```

All services should be `running` or `healthy`.

## Development Mode

Enabled by default (`PROJECT_STATE=development`):

- Hot reload for frontend (Vite) via Docker Watch
- Backend with mounted code (`./app:/app`)
- Verbose logging
- Persistent development databases

## Production Mode

Set in `.env`:

```bash
PROJECT_STATE=production
```

Effect:

- Optimized builds, no hot reload
- Less logging
- Only nginx exposed externally
- Stricter security settings

Start:

```bash
./start_llars.sh prod
```

## Full Reset

For a clean restart with deletion of all data:

```bash
REMOVE_LLARS_VOLUMES=True ./start_llars.sh --build
```

For a complete system cleanup (images, volumes, build cache):

```bash
PRUNE_LLARS_SYSTEM=True ./start_llars.sh --build
```

## Troubleshooting

### Service does not start

```bash
docker compose -p llars logs backend-flask-service --tail=50
docker compose -p llars logs frontend-vue-service --tail=50
```

### Port conflicts

Adjust ports in `.env`, e.g.:

```bash
NGINX_EXTERNAL_PORT=56080
AUTHENTIK_EXTERNAL_PORT=56095
```

### Database problems

**Warning: deletes data**

```bash
REMOVE_LLARS_VOLUMES=True ./start_llars.sh --build
```

### Docker not running

- macOS: `open /Applications/Docker.app`
- Linux: `sudo systemctl start docker`

## Next Steps

- [Configuration](configuration.md)
- [Docker Architecture & Build Caching](../entwickler/docker-architektur.md)
- [Switch project state](../guides/project-state.md)
- [Permission system](../guides/permission-system.md)
