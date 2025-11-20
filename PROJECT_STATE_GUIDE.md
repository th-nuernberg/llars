# LLARS PROJECT_STATE Guide

## Übersicht

`PROJECT_STATE` ist die zentrale Umgebungsvariable, die alle LLARS-Services steuert, ob sie im **Development** oder **Production** Modus laufen.

## Konfiguration

Die Variable wird in der `.env`-Datei gesetzt:

```bash
# Development-Modus (Standard)
PROJECT_STATE=development

# Production-Modus
PROJECT_STATE=production
```

## Services-Verhalten

### Keycloak

#### Development-Modus (`PROJECT_STATE=development`)

- ✅ **HTTP akzeptiert** (`sslRequired: none`)
- ✅ **KC_HTTP_ENABLED=true**
- ✅ **KC_HOSTNAME_STRICT=false**
- ✅ Lockere Sicherheitseinstellungen für Entwicklung
- ✅ Einfacherer Zugriff über `http://localhost:55090`

#### Production-Modus (`PROJECT_STATE=production`)

- 🔒 **HTTPS erforderlich** (`sslRequired: external`)
- 🔒 **KC_HTTP_ENABLED=false**
- 🔒 **KC_HOSTNAME_STRICT=true**
- 🔒 Strikte Sicherheitseinstellungen
- 🔒 Nur über HTTPS-Proxy erreichbar

### Andere Services

Alle Services erhalten die `PROJECT_STATE`-Variable und können entsprechend reagieren:

- **Flask Backend** (`llars_flask_service`)
- **Vue Frontend** (`llars_frontend_service`) - nutzt `VITE_PROJECT_STATE`
- **Nginx** (`llars_nginx_service`)
- **YJS Server** (`llars_yjs_service`)
- **Supervisor** (`llars_supervisor_service`)
- **MariaDB** (`llars_db_service`)
- **PostgreSQL** (`llars_keycloak_db_service`)
- **MkDocs** (`llars_mkdocs_service`)

## Technische Implementierung

### Keycloak Entrypoint-Script

Das Script `/opt/keycloak/entrypoint.sh` wird beim Container-Start ausgeführt:

1. Liest `PROJECT_STATE` aus der Umgebung
2. Lädt das Realm-Template `/opt/keycloak/import-config/realm-import-template.json`
3. Ersetzt den Platzhalter `__SSL_REQUIRED__` mit dem entsprechenden Wert:
   - `"none"` für Development
   - `"external"` für Production
4. Schreibt die generierte Konfiguration nach `/opt/keycloak/data/import/realm-import.json`
5. Startet Keycloak mit den angepassten Einstellungen

### Dockerfile-Änderungen

**Keycloak Dockerfile** (`docker/keycloak/Dockerfile-keycloak`):
```dockerfile
USER root
COPY --chmod=755 docker/keycloak/entrypoint.sh /opt/keycloak/entrypoint.sh
RUN chown 1000:1000 /opt/keycloak/entrypoint.sh
USER 1000
ENTRYPOINT ["/opt/keycloak/entrypoint.sh"]
```

### docker-compose.yml

Alle Services erhalten die Variable via:
```yaml
environment:
  - PROJECT_STATE=${PROJECT_STATE}
```

## Verwendung

### System starten

```bash
# Mit Development-Einstellungen (Standard)
./start_llars.sh

# Oder manuell
PROJECT_STATE=development docker compose -p llars up -d --build
```

### Auf Production umschalten

1. Bearbeite `.env`:
   ```bash
   PROJECT_STATE=production
   ```

2. Starte Services neu:
   ```bash
   ./start_llars.sh
   ```

### Verifizierung

Überprüfe die Keycloak-Logs:
```bash
docker logs llars_keycloak_service | head -20
```

Erwartete Ausgabe für Development:
```
======================================
Keycloak Entrypoint - PROJECT_STATE: development
======================================
Konfiguriere Keycloak für DEVELOPMENT...
  - sslRequired: none
  - KC_HOSTNAME_STRICT: false
  - KC_HTTP_ENABLED: true
✓ Realm-Konfiguration erstellt
======================================
Starte Keycloak...
======================================
```

## Benutzer erstellen

Das Script `create_keycloak_user.sh` funktioniert in beiden Modi:

```bash
# Standard-Benutzer erstellen
./create_keycloak_user.sh

# Benutzer mit Custom-Daten erstellen
./create_keycloak_user.sh myuser MyPass123! user@example.com FirstName LastName
```

## Troubleshooting

### Problem: Keycloak akzeptiert kein HTTP

**Lösung:**
1. Überprüfe `.env`: `PROJECT_STATE=development`
2. Stoppe alle Services: `docker compose -p llars down`
3. Entferne Keycloak-Datenbank: `docker volume rm llars_keycloakdb`
4. Starte neu: `./start_llars.sh`

### Problem: Realm-Import schlägt fehl

**Lösung:**
1. Überprüfe, ob Template existiert:
   ```bash
   ls -la docker/keycloak/realm-import-template.json
   ```
2. Überprüfe Keycloak-Logs:
   ```bash
   docker logs llars_keycloak_service
   ```

### Problem: Services erkennen PROJECT_STATE nicht

**Lösung:**
1. Überprüfe `.env`-Datei: `cat .env | grep PROJECT_STATE`
2. Rebuild aller Services: `docker compose -p llars up -d --build`

## Best Practices

### Development

- ✅ Nutze `PROJECT_STATE=development`
- ✅ HTTP ist aktiviert für einfachen Zugriff
- ✅ Nutze `http://localhost:55173` für Frontend
- ✅ Nutze `http://localhost:55090` für Keycloak Admin

### Production

- 🔒 Setze `PROJECT_STATE=production`
- 🔒 Verwende HTTPS-Proxy (nginx/traefik)
- 🔒 Ändere Standard-Passwörter in `.env`
- 🔒 Aktiviere Firewall-Regeln
- 🔒 Sichere Secrets (nicht in Git committen)
- 🔒 Nutze Docker Secrets statt `.env` für sensitive Daten

## Dateien

- **Konfiguration**: `.env`
- **Entrypoint-Script**: `docker/keycloak/entrypoint.sh`
- **Realm-Template**: `docker/keycloak/realm-import-template.json`
- **Dockerfile**: `docker/keycloak/Dockerfile-keycloak`
- **Docker Compose**: `docker-compose.yml`
- **User-Script**: `create_keycloak_user.sh`
- **Start-Script**: `start_llars.sh`

## Weitere Informationen

- [Keycloak Login Guide](KEYCLOAK_LOGIN_GUIDE.md) - Erklärt die duale Authentifizierung
- [Keycloak Dokumentation](https://www.keycloak.org/documentation)
- [Docker Compose Dokumentation](https://docs.docker.com/compose/)
