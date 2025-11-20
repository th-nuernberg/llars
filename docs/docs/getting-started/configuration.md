# Configuration

## Environment Variables

LLARS uses a `.env` file for configuration. All services read from this central configuration.

## Database Configuration

### MariaDB (Main Database)

```bash
MYSQL_ROOT_PASSWORD=root_password_feature
MYSQL_DATABASE=database_llars
MYSQL_USER=user_feature
MYSQL_PASSWORD=password_feature
```

**Internal Connection:**
- Host: `db-maria-service`
- Port: `3306` (internal)
- External Port: `55306` (for debugging only)

## Keycloak Authentication

### Database (PostgreSQL)

```bash
KEYCLOAK_DB_NAME=keycloak
KEYCLOAK_DB_USER=keycloak
KEYCLOAK_DB_PASSWORD=keycloak_db_secure_password_123
```

### Admin Access

```bash
KC_BOOTSTRAP_ADMIN_USERNAME=admin
KC_BOOTSTRAP_ADMIN_PASSWORD=admin_secure_password_123
```

Access admin console: http://localhost:55090/admin

### Realm Configuration

```bash
KEYCLOAK_REALM=llars
KEYCLOAK_HOSTNAME=localhost
KEYCLOAK_EXTERNAL_URL=http://localhost:55090
```

### Client Configuration

The realm is auto-imported from `docker/keycloak/realm-import.json`:

**Frontend Client:** `llars-frontend`
- Type: Public Client
- PKCE: Enabled (S256)
- Redirect URIs: `http://localhost:55080/*`, `http://localhost:55173/*`
- Web Origins: `+` (auto-allows all redirect URIs)

**Backend Client:** `llars-backend`
- Type: Confidential Client
- Service Account: Enabled
- Client Secret: `llars-backend-secret-change-in-production`

## CORS Configuration

```bash
ALLOWED_ORIGINS=http://localhost,http://localhost:55080,http://localhost:55173,http://127.0.0.1,http://127.0.0.1:55080,http://127.0.0.1:55173
```

Add additional origins as comma-separated values.

## Port Configuration

All LLARS ports are in the 55000 range to avoid conflicts:

```bash
# External Ports (exposed to host)
NGINX_EXTERNAL_PORT=55080      # Main entry point
FLASK_EXTERNAL_PORT=55081      # Backend API (direct access)
FRONTEND_EXTERNAL_PORT=55173   # Frontend dev server
DB_EXTERNAL_PORT=55306         # Database (debugging only)
KEYCLOAK_EXTERNAL_PORT=55090   # Authentication
YJS_EXTERNAL_PORT=55082        # Collaborative editing
SSH_PROXY_EXTERNAL_PORT=55093  # SSH tunnel
MKDOCS_EXTERNAL_PORT=55800     # Documentation

# Internal Ports (inside Docker network)
NGINX_INTERNAL_PORT=8100
FLASK_INTERNAL_PORT=8081
FRONTEND_INTERNAL_PORT=5173
DB_INTERNAL_PORT=3306
KEYCLOAK_INTERNAL_PORT=8080
YJS_INTERNAL_PORT=8082
```

## LLM Configuration

### OpenAI

```bash
OPENAI_API_KEY=sk-test-placeholder-replace-with-real-key
```

### RAG Pipeline

The RAG (Retrieval-Augmented Generation) pipeline uses:

- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store:** ChromaDB
- **Chunk Size:** 1000 characters
- **Chunk Overlap:** 200 characters
- **Storage:** `/app/storage/vectorstore`

Configuration in `app/rag_pipeline.py:22-36`

## Volume Management

```bash
REMOVE_VOLUMES=False  # Set to True to delete data on restart
```

**LLARS Volumes:**
- `llars_llarsdb` - Main database data
- `llars_keycloakdb` - Authentication data
- `llars_model_volume` - ML models and embeddings (~2GB)

## Development vs Production

```bash
PROJECT_STATE=development  # or production
FLASK_ENV=development      # or production
```

**Development Mode:**
- Hot-reload enabled
- Debug logs
- Source code mounted as volumes
- Vite dev server for frontend

**Production Mode:**
- Optimized builds
- Minimal logging
- No volume mounts
- Static frontend serving

## Security Considerations

### Change Default Passwords

Before production deployment:

```bash
# Database
MYSQL_ROOT_PASSWORD=<strong-password>
MYSQL_PASSWORD=<strong-password>

# Keycloak
KEYCLOAK_DB_PASSWORD=<strong-password>
KC_BOOTSTRAP_ADMIN_PASSWORD=<strong-password>
KEYCLOAK_BACKEND_CLIENT_SECRET=<strong-random-secret>

# Flask
JWT_SECRET_KEY=<strong-random-secret>
```

### SSL/TLS

For production, enable HTTPS:

1. Add SSL certificates to `docker/nginx/certs/`
2. Update Nginx configuration
3. Update Keycloak settings:
   ```bash
   KEYCLOAK_EXTERNAL_URL=https://your-domain.com
   KC_HOSTNAME=your-domain.com
   ```

### External Port Exposure

In production, consider:
- Exposing only `NGINX_EXTERNAL_PORT=80/443`
- Removing direct database/backend port mappings
- Using Docker networks for internal communication

## Advanced Configuration

### Custom Docker Compose

Create `docker-compose.override.yml` for local customizations:

```yaml
services:
  backend-flask-service:
    environment:
      - CUSTOM_VAR=value
```

### Keycloak Theme Customization

Place custom themes in `docker/keycloak/themes/` and mount in docker-compose.yml.

### Nginx Custom Configuration

Edit `docker/nginx/nginx.conf` for:
- Custom routing rules
- Rate limiting
- Additional proxy settings
