# Installation

## Voraussetzungen

- Docker Desktop (Mac/Windows) oder Docker Engine (Linux)
- Docker Compose v2+
- Git
- Mindestens 8 GB RAM für die Container

## Schnellstart

### 1. Repository klonen

```bash
git clone <repository-url>
cd llars
```

### 2. Umgebungsvariablen anlegen

```bash
cp .env.template.development .env
# Werte bei Bedarf anpassen
```

Wichtigste Schalter:

```bash
PROJECT_STATE=development   # oder production
REMOVE_LLARS_VOLUMES=False        # True löscht Daten beim nächsten Start
PROJECT_URL=http://localhost:55080   # Einstiegspunkt für Frontend + API

# Optional: Host-Port Overrides (Defaults sind vorkonfiguriert)
NGINX_EXTERNAL_PORT=55080
AUTHENTIK_EXTERNAL_PORT=55095
DB_EXTERNAL_PORT=55306              # Nur für Debugging
MKDOCS_EXTERNAL_PORT=55800
```

### 3. LLARS starten

```bash
chmod +x start_llars.sh
./start_llars.sh            # nutzt .env
```

**Was das Skript macht**
1. Prüft, ob Docker läuft
2. Stoppt nur LLARS-Container
3. Entfernt optional nur LLARS-Volumes (`REMOVE_LLARS_VOLUMES=True`)
4. Baut und startet alle Services

**Volumes, die betroffen sind**
- `llars_llarsdb` (MariaDB)
- `llars_model_volume` (Modelle/Embeddings)
- `llars_authentikdb` (PostgreSQL für Authentik)

Andere Projekt-Volumes bleiben unberührt.

### 4. Dienste aufrufen

Nach 2–3 Minuten (erstes Starten lädt Images):

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik | http://localhost:55095 |
| Docs (direkt) | http://localhost:55800 |
| Docs (via nginx, dev) | http://localhost:55080/mkdocs/ |

### 5. Installation prüfen

```bash
docker compose ps
```

Alle Services sollten `running` oder `healthy` sein.

## Entwicklungsmodus

Standardmäßig aktiv (`PROJECT_STATE=development`):
- Hot-Reload für Frontend (Vite)
- Backend mit gemountetem Code
- Ausführliches Logging
- Persistente Entwicklungsdatenbanken

## Produktionsmodus

In `.env` setzen:

```bash
PROJECT_STATE=production
```

Effekt:
- Optimierte Builds, kein Hot-Reload
- Weniger Logging
- Nur nginx nach außen exponiert
- Strengere Security-Einstellungen

Start:

```bash
./start_llars.sh prod
```

## Troubleshooting

### Service startet nicht

```bash
docker compose logs backend-flask-service --tail=50
docker compose logs frontend-vue-service --tail=50
```

### Portkonflikte

Ports in `.env` anpassen, z. B.:

```bash
NGINX_EXTERNAL_PORT=56080
AUTHENTIK_EXTERNAL_PORT=56095
```

### Datenbank-Probleme

**⚠️ Löscht Daten:**  
`REMOVE_LLARS_VOLUMES=True` in `.env` setzen und neu starten:

```bash
./start_llars.sh
```

### Docker läuft nicht

- macOS: `open /Applications/Docker.app`
- Linux: `sudo systemctl start docker`

## Nächste Schritte

- [Konfiguration](configuration.md)
- [Projektstatus umschalten](../guides/project-state.md)
- [Berechtigungssystem](../guides/permission-system.md)
