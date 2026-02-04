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
./start_llars.sh            # uses .env
```

**What the script does**
1. Checks whether Docker is running
2. Stops only LLARS containers
3. Optionally removes only LLARS volumes (`REMOVE_LLARS_VOLUMES=True`)
4. Builds and starts all services

**Volumes affected**
- `llars_llarsdb` (MariaDB)
- `llars_model_volume` (models/embeddings)
- `llars_authentikdb` (PostgreSQL for Authentik)

Other project volumes remain untouched.

### 4. Open services

After 2-3 minutes (first start pulls images):

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik | http://localhost:55095 |
| Docs (direct) | http://localhost:55800 |
| Docs (via nginx, dev) | http://localhost:55080/mkdocs/ |

### 5. Verify installation

```bash
docker compose ps
```

All services should be `running` or `healthy`.

## Development Mode

Enabled by default (`PROJECT_STATE=development`):
- Hot reload for frontend (Vite)
- Backend with mounted code
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

## Troubleshooting

### Service does not start

```bash
docker compose logs backend-flask-service --tail=50
docker compose logs frontend-vue-service --tail=50
```

### Port conflicts

Adjust ports in `.env`, e.g.:

```bash
NGINX_EXTERNAL_PORT=56080
AUTHENTIK_EXTERNAL_PORT=56095
```

### Database problems

**Warning: deletes data**  
Set `REMOVE_LLARS_VOLUMES=True` in `.env` and restart:

```bash
./start_llars.sh
```

### Docker not running

- macOS: `open /Applications/Docker.app`
- Linux: `sudo systemctl start docker`

## Next Steps

- [Configuration](configuration.md)
- [Switch project state](../guides/project-state.md)
- [Permission system](../guides/permission-system.md)
