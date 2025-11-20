# Installation

## Prerequisites

- Docker Desktop (for Mac/Windows) or Docker Engine (for Linux)
- Docker Compose v2+
- Git
- At least 8GB RAM available for Docker

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd llars
```

### 2. Configure Environment

Copy the example environment file and adjust settings:

```bash
cp .env.example .env
```

**Important Environment Variables:**

```bash
# Project State
PROJECT_STATE=development  # or production

# Volume Management
REMOVE_VOLUMES=False  # Set to True to reset database on restart

# Ports (55000 range to avoid conflicts)
NGINX_EXTERNAL_PORT=55080
FLASK_EXTERNAL_PORT=55081
FRONTEND_EXTERNAL_PORT=55173
KEYCLOAK_EXTERNAL_PORT=55090
```

### 3. Start LLARS

Use the provided start script:

```bash
chmod +x start_llars.sh
./start_llars.sh
```

**What the script does:**

1. Checks if Docker is running (starts it if needed on Mac/Linux)
2. Stops and removes **only LLARS containers** (safe for multi-project environments)
3. Optionally removes **only LLARS volumes** if `REMOVE_VOLUMES=True`
4. Builds and starts all services

**Volume Safety:** The script explicitly targets only these volumes:
- `llars_llarsdb` (MariaDB database)
- `llars_keycloakdb` (Keycloak PostgreSQL)
- `llars_model_volume` (ML models and embeddings)

Other project volumes (Pitcho Hesh, KIA, etc.) remain untouched.

### 4. Access Services

After startup (may take 2-3 minutes for first run):

- **Frontend**: http://localhost:55173
- **API Docs**: http://localhost:55800
- **Nginx**: http://localhost:55080
- **Keycloak Admin**: http://localhost:55090/admin
  - Username: `admin`
  - Password: Check `.env` for `KEYCLOAK_ADMIN_PASSWORD`

### 5. Verify Installation

Check all services are healthy:

```bash
docker compose ps
```

Expected output: All services show `healthy` or `running` status.

## Development Mode

In development mode (default), the application runs with:

- Hot-reload for frontend (Vue + Vite)
- Hot-reload for backend (Flask with mounted volumes)
- Debug logging enabled
- Development database data persisted

## Production Mode

Set in `.env`:

```bash
PROJECT_STATE=production
```

This enables:
- Optimized builds
- Production logging
- No hot-reload (faster performance)
- Stricter security settings

## Troubleshooting

### Service Won't Start

```bash
# Check logs for specific service
docker compose logs backend-flask-service --tail=50

# Check all services
docker compose logs --tail=20
```

### Port Conflicts

If ports 55080-55173 are in use, adjust in `.env`:

```bash
NGINX_EXTERNAL_PORT=56080
FLASK_EXTERNAL_PORT=56081
# ... etc
```

### Database Issues

Reset database (⚠️ **deletes all data**):

```bash
# Set in .env
REMOVE_VOLUMES=True

# Restart
./start_llars.sh
```

### Docker Not Starting

**Mac:**
```bash
open /Applications/Docker.app
```

**Linux:**
```bash
sudo systemctl start docker
```

## Next Steps

- [Configuration Guide](configuration.md)
- [API Reference](../api/endpoints.md)
- [Architecture Overview](../architecture/overview.md)
