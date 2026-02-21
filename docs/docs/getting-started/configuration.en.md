# Configuration

## .env (intentionally small)

LLARS uses an intentionally **small** `.env`:
- **Secrets + infrastructure** stay in `.env` (DB passwords, Authentik/Matomo secrets, API keys).
- **App settings** are configurable in the **DB** (e.g., analytics/tracking in the admin panel).

Setup:

```bash
cp .env.template.development .env   # or .env.template.production
```

## Database (MariaDB)

```bash
MYSQL_ROOT_PASSWORD=...
MYSQL_DATABASE=database_llars
MYSQL_USER=dev_user
MYSQL_PASSWORD=...
```

**Connections**
- Internal: Host `db-maria-service`, Port `3306`
- External (debug only): Port `55306`

## Authentik (OIDC)

```bash
AUTHENTIK_SECRET_KEY=...                # at least 50 characters
AUTHENTIK_DB_NAME=authentik_dev
AUTHENTIK_DB_USER=authentik_dev
AUTHENTIK_DB_PASSWORD=...
AUTHENTIK_PUBLIC_URL=http://localhost:55095
AUTHENTIK_BOOTSTRAP_EMAIL=admin@example.com
AUTHENTIK_BOOTSTRAP_PASSWORD=admin123

# Backend OAuth client secret (Client ID is invariant: llars-backend)
AUTHENTIK_BACKEND_CLIENT_SECRET=llars-backend-secret-change-in-production
AUTHENTIK_EXTERNAL_PORT=55095
```

## Analytics (Matomo)

- UI: `${PROJECT_URL}/analytics/`
- Tracking (first-party): `${PROJECT_URL}/metrics.js` and `${PROJECT_URL}/metrics.php`
- Runtime settings: **Admin -> Analytics** (DB-based, not `.env`)

## Docs (MkDocs)

- Dev via nginx: `${PROJECT_URL}/mkdocs/`
- Prod via nginx: `${PROJECT_URL}/mkdocs/`
- Direct (host port): `http://localhost:${MKDOCS_EXTERNAL_PORT:-55800}`

### Privacy Check (current implementation, not legal advice)

- Captured: pageviews (route URL + title), link tracking, click events, optional hover events, heartbeat/time-on-page, optional user ID (Authentik `preferred_username`/`sub`)
- Defaults: cookies **on**, user ID **on**, consent **off** -> in EU contexts usually requires consent or another legal basis
- Consent flags exist (`require_consent`/`require_cookie_consent`), but there is currently **no** consent UI/`setConsentGiven` integration
- Route URLs include dynamic IDs (e.g., `/Rater/123`) -> potentially personal data; consider anonymizing or tracking only route names
- Event labels come from UI text/ARIA/`data-*` (emails/URLs/4+ digits are sanitized, but user content may still appear) -> exclude sensitive areas with `data-matomo-ignore`
- Server-side privacy settings (IP anonymization, DNT, retention) must be configured in Matomo itself

## Port Mapping

```bash
# External (host)
NGINX_EXTERNAL_PORT=55080      # Main entry (Frontend + API + Matomo + Docs Proxy)
AUTHENTIK_EXTERNAL_PORT=55095  # Optional direct; also via nginx `/authentik/`
DB_EXTERNAL_PORT=55306         # Optional direct (debug only)
MKDOCS_EXTERNAL_PORT=55800     # Optional direct; via nginx `/mkdocs/` (Dev) / `/mkdocs/` (Prod)
```

## CORS

```bash
# Usually not needed:
# ALLOWED_ORIGINS is derived from PROJECT_URL + localhost defaults.
ALLOWED_ORIGINS=http://localhost:55080,http://127.0.0.1:55080
```

Separate multiple entries with commas.

## LLM Configuration

```bash
OPENAI_API_KEY=sk-...
LITELLM_API_KEY=...
LITELLM_BASE_URL=https://kiz1.in.ohmportal.de/llmproxy/v1
```

Default models are loaded from the DB (`llm_models`) and seeded on startup (see `app/db/models/llm_model.py`).

## RAG Pipeline

- Embeddings: default from `llm_models` (currently `llamaindex/vdr-2b-multi-v1`), fallback `sentence-transformers/all-MiniLM-L6-v2`
- Vector store: ChromaDB
- Chunking: `app/rag_pipeline.py` uses 1500/300, `app/services/rag/embedding/collection_embedding_service.py` uses default 1000/200 (per collection configurable)
- Storage path: `/app/storage/vectorstore`

Settings: `app/rag_pipeline.py` and `app/services/rag/embedding/collection_embedding_service.py`

## Volumes

```bash
REMOVE_LLARS_VOLUMES=False   # True deletes data on next start
```

`REMOVE_LLARS_VOLUMES=True` removes **all** volumes with the `llars_` prefix, e.g.:

- `llars_llarsdb` - MariaDB data
- `llars_rag_storage` / `llars_rag_docs` - RAG data
- `llars_authentikdb` / `llars_authentik_media` - Authentik
- `llars_matomo_data` / `llars_matomodb` - Analytics
- `llars_redis_data` - Redis

## Development vs Production

```bash
PROJECT_STATE=development   # or production
FLASK_ENV=development       # optional; usually set automatically
```

**Development**
- Hot reload (frontend + backend)
- Verbose logging
- Source code mounted as volumes

**Production**
- Optimized builds, no hot reload
- Reduced logging
- Frontend served statically via nginx

## Security

### Change default passwords

```bash
MYSQL_ROOT_PASSWORD=<strong>
MYSQL_PASSWORD=<strong>
AUTHENTIK_DB_PASSWORD=<strong>
AUTHENTIK_BOOTSTRAP_PASSWORD=<strong>
AUTHENTIK_BACKEND_CLIENT_SECRET=<strong>
SYSTEM_ADMIN_API_KEY=<strong>
ADMIN_REGISTRATION_KEY=<uuid>
```

### Enable SSL/TLS

1. Place certificates under `docker/nginx/certs/`  
2. Adjust nginx configuration  
3. Switch `PROJECT_URL`/`AUTHENTIK_PUBLIC_URL` to HTTPS (e.g., `https://llars.example.de`)

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

### Authentik Theme/Branding

Authentik themes can be configured via the admin UI (flows/branding). Custom logos/colors can be set there; no separate theme directory is required.

### Nginx Custom Configuration

Edit `docker/nginx/nginx.conf` for:
- Custom routing rules
- Rate limiting
- Additional proxy settings
