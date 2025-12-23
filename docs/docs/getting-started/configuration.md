# Konfiguration

## .env (bewusst klein)

LLARS nutzt eine bewusst **kleine** `.env`:
- **Secrets + Infrastruktur** bleiben in `.env` (DB-Passwörter, Authentik/Matomo Secrets, API Keys).
- **App-Settings** sind in der **DB** konfigurierbar (z. B. Analytics/Tracking im Admin-Panel).

Setup:

```bash
cp .env.template.development .env   # oder .env.template.production
```

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
AUTHENTIK_PUBLIC_URL=http://localhost:55095
AUTHENTIK_BOOTSTRAP_EMAIL=admin@example.com
AUTHENTIK_BOOTSTRAP_PASSWORD=admin123

# Backend OAuth client secret (Client-ID ist invariant: llars-backend)
AUTHENTIK_BACKEND_CLIENT_SECRET=llars-backend-secret-change-in-production
AUTHENTIK_EXTERNAL_PORT=55095
```

## Analytics (Matomo)

- UI: `${PROJECT_URL}/analytics/`
- Tracking (first-party): `${PROJECT_URL}/metrics.js` und `${PROJECT_URL}/metrics.php`
- Runtime-Settings: **Admin → Analytics** (DB-basiert, kein `.env`)

## Docs (MkDocs)

- Dev via nginx: `${PROJECT_URL}/mkdocs/`
- Prod via nginx: `${PROJECT_URL}/docs/`
- Direkt (Host-Port): `http://localhost:${MKDOCS_EXTERNAL_PORT:-55800}`

### Datenschutz-Check (Code-Stand, keine Rechtsberatung)

- Erfasst: Pageviews (Route-URL + Titel), Link-Tracking, Klick-Events, optional Hover-Events, Heartbeat/Time-on-Page, optional User-ID (Authentik `preferred_username`/`sub`)
- Defaults: Cookies **an**, User-ID **an**, Consent **aus** → in EU-Kontext i. d. R. nur mit Einwilligung/anderer Rechtsgrundlage zulässig
- Consent-Flags vorhanden (`require_consent`/`require_cookie_consent`), aber es gibt aktuell **keine** Consent-UI/`setConsentGiven`-Integration
- Route-URLs enthalten dynamische IDs (z. B. `/Rater/123`) → potenziell personenbezogen; ggf. anonymisieren oder nur Routen-Namen tracken
- Event-Labels kommen aus UI-Text/ARIA/`data-*` (E-Mails/URLs/4+ Zahlen werden sanitisiert, aber User-Content kann dennoch enthalten sein) → sensible Bereiche mit `data-matomo-ignore` ausnehmen
- Serverseitige Privacy-Settings (IP-Anonymisierung, DNT, Retention) müssen in Matomo selbst konfiguriert werden

## Port-Belegung

```bash
# Extern (Host)
NGINX_EXTERNAL_PORT=55080      # Haupt-Einstieg (Frontend + API + Matomo + Docs Proxy)
AUTHENTIK_EXTERNAL_PORT=55095  # Optional direkt; zusätzlich via nginx `/authentik/`
DB_EXTERNAL_PORT=55306         # Optional direkt (nur Debugging)
MKDOCS_EXTERNAL_PORT=55800     # Optional direkt; via nginx `/mkdocs/` (Dev) / `/docs/` (Prod)
```

## CORS

```bash
# Normalerweise nicht nötig:
# ALLOWED_ORIGINS wird aus PROJECT_URL + localhost Defaults abgeleitet.
ALLOWED_ORIGINS=http://localhost:55080,http://127.0.0.1:55080
```

Mehrere Einträge mit Komma trennen.

## LLM-Konfiguration

```bash
OPENAI_API_KEY=sk-...
LITELLM_API_KEY=...
LITELLM_BASE_URL=https://kiz1.in.ohmportal.de/llmproxy/v1
```

Standardmodelle werden aus der DB (`llm_models`) geladen und beim Start gesät (siehe `app/db/models/llm_model.py`).

## RAG-Pipeline

- Embeddings: Default aus `llm_models` (aktuell `llamaindex/vdr-2b-multi-v1`), Fallback `sentence-transformers/all-MiniLM-L6-v2`
- Vector Store: ChromaDB
- Chunk Size: 1000 Zeichen, Overlap: 200 Zeichen
- Speicherpfad: `/app/storage/vectorstore`

Einstellungen: `app/rag_pipeline.py`

## Volumes

```bash
REMOVE_LLARS_VOLUMES=False   # True löscht Daten beim nächsten Start
```

- `llars_llarsdb` – MariaDB-Daten
- `llars_model_volume` – Modelle/Embeddings
- `llars_authentikdb` – Authentik-PostgreSQL

## Development vs Production

```bash
PROJECT_STATE=development   # oder production
FLASK_ENV=development       # optional; wird i. d. R. automatisch gesetzt
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
3. `PROJECT_URL`/`AUTHENTIK_PUBLIC_URL` auf HTTPS umstellen (z. B. `https://llars.example.de`)

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
