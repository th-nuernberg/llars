# Konfiguration

## .env als zentrale Stelle

Alle Services lesen ihre Einstellungen aus `.env`. Kopiere dafür eine Vorlage (`.env.template.development` oder `.env.template.production`) nach `.env` und passe die Werte an.

## Datenbank (MariaDB)

```bash
MYSQL_ROOT_PASSWORD=...
MYSQL_DATABASE=database_llars
MYSQL_USER=dev_user
MYSQL_PASSWORD=...
```

**Verbindungen**
- Intern: Host `db-maria-service`, Port `3306`
- Extern (nur Debug): Port `55306`

## Authentik (OIDC)

```bash
AUTHENTIK_SECRET_KEY=...                # mind. 50 Zeichen
AUTHENTIK_DB_NAME=authentik_dev
AUTHENTIK_DB_USER=authentik_dev
AUTHENTIK_DB_PASSWORD=...
AUTHENTIK_BOOTSTRAP_EMAIL=admin@example.com
AUTHENTIK_BOOTSTRAP_PASSWORD=admin123

AUTHENTIK_FRONTEND_CLIENT_ID=llars-frontend
AUTHENTIK_BACKEND_CLIENT_ID=llars-backend
AUTHENTIK_BACKEND_CLIENT_SECRET=llars-backend-secret-change-in-production
AUTHENTIK_ISSUER_URL=http://authentik-server:9000/application/o/llars-backend/

AUTHENTIK_INTERNAL_PORT=9000
AUTHENTIK_EXTERNAL_PORT=55095
AUTHENTIK_DB_INTERNAL_PORT=5432
```

## Port-Belegung

```bash
# Extern (Host)
NGINX_EXTERNAL_PORT=55080      # Haupt-Einstieg (Frontend + API)
FLASK_EXTERNAL_PORT=55081      # Direkter Backend-Zugriff (Dev)
FRONTEND_EXTERNAL_PORT=55173   # Vite Dev Server
DB_EXTERNAL_PORT=55306         # MariaDB Debug
YJS_EXTERNAL_PORT=55082
AUTHENTIK_EXTERNAL_PORT=55095
MKDOCS_EXTERNAL_PORT=55800

# Intern (Container-zu-Container)
NGINX_INTERNAL_PORT=80
FLASK_INTERNAL_PORT=8081
FRONTEND_INTERNAL_PORT=5173
DB_INTERNAL_PORT=3306
YJS_INTERNAL_PORT=8082
```

## CORS

```bash
ALLOWED_ORIGINS=http://localhost,http://localhost:55080,http://localhost:55173,http://127.0.0.1,http://127.0.0.1:55080,http://127.0.0.1:55173
```

Mehrere Einträge mit Komma trennen.

## LLM-Konfiguration

```bash
OPENAI_API_KEY=sk-...
LITELLM_API_KEY=...
LITELLM_BASE_URL=https://kiz1.in.ohmportal.de/llmproxy/v1
```

Standardmodell: `mistralai/Mistral-Small-3.2-24B-Instruct-2506` (siehe `app/llm/litellm_client.py`).

## RAG-Pipeline

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Vector Store: ChromaDB
- Chunk Size: 1000 Zeichen, Overlap: 200 Zeichen
- Speicherpfad: `/app/storage/vectorstore`

Einstellungen: `app/rag_pipeline.py`

## Volumes

```bash
REMOVE_VOLUMES=False   # True löscht Daten beim nächsten Start
```

- `llars_llarsdb` – MariaDB-Daten
- `llars_model_volume` – Modelle/Embeddings
- `llars_authentikdb` – Authentik-PostgreSQL

## Development vs Production

```bash
PROJECT_STATE=development   # oder production
FLASK_ENV=development       # oder production
```

**Development**
- Hot-Reload (Frontend + Backend)
- Umfangreiches Logging
- Quellcode als Volumes gemountet

**Production**
- Optimierte Builds, kein Hot-Reload
- Reduziertes Logging
- Frontend statisch über nginx

## Sicherheit

### Standard-Passwörter ändern

```bash
MYSQL_ROOT_PASSWORD=<stark>
MYSQL_PASSWORD=<stark>
AUTHENTIK_DB_PASSWORD=<stark>
AUTHENTIK_BOOTSTRAP_PASSWORD=<stark>
AUTHENTIK_BACKEND_CLIENT_SECRET=<stark>
SYSTEM_ADMIN_API_KEY=<stark>
ADMIN_REGISTRATION_KEY=<uuid>
```

### SSL/TLS aktivieren

1. Zertifikate nach `docker/nginx/certs/` legen  
2. nginx-Konfiguration anpassen  
3. Authentik-URLs auf HTTPS umstellen (z. B. `AUTHENTIK_EXTERNAL_PORT=443`, `AUTHENTIK_ISSUER_URL=https://<domain>/application/o/llars-backend/`)

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

Authentik-Themes lassen sich über die Admin-UI konfigurieren (Flows/Branding). Eigene Logos/Farben können dort hinterlegt werden; kein separates Theme-Verzeichnis nötig.

### Nginx Custom Configuration

Edit `docker/nginx/nginx.conf` for:
- Custom routing rules
- Rate limiting
- Additional proxy settings
