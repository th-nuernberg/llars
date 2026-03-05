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
./start_llars.sh            # Schnellstart (nutzt gecachte Images)
```

### Start-Modi

| Befehl | Beschreibung | Dauer |
|--------|-------------|-------|
| `./start_llars.sh` | Startet mit gecachten Images, kein Rebuild | ~30s |
| `./start_llars.sh --build` | Prüft Dockerfiles auf Änderungen, baut bei Bedarf neu | ~70s |
| `./start_llars.sh --detach` | Startet im Hintergrund (ohne Watch-Modus) | ~30s |
| `./start_llars.sh --build --detach` | Rebuild-Check + Start im Hintergrund | ~70s |
| `./start_llars.sh dev` | Erzwingt Development-Modus | ~30s |
| `./start_llars.sh prod` | Erzwingt Production-Modus | ~70s |
| `./start_llars.sh --update` | Baut nur Backend + Frontend neu (schneller Update) | ~30s |

!!! tip "Wann welchen Modus?"
    **Normaler Start** (Code-Änderungen an Python/Vue/JS): `./start_llars.sh`
    Code-Änderungen werden über Volume-Mounts automatisch übernommen.

    **Nach Dependency-Änderungen** (requirements.txt, package.json): `./start_llars.sh --build`
    Docker erkennt die Änderung und baut nur die betroffenen Layer neu.

    **Nach Dockerfile/Compose-Änderungen**: `./start_llars.sh --build`

**Was das Skript macht:**

1. Prüft, ob Docker läuft (startet Docker falls nötig)
2. Stoppt nur LLARS-Container
3. Entfernt optional nur LLARS-Volumes (`REMOVE_LLARS_VOLUMES=True`)
4. Startet alle Services (mit oder ohne Rebuild)

**Volumes, die betroffen sind:**
`REMOVE_LLARS_VOLUMES=True` entfernt **alle** Docker-Volumes mit dem Präfix `llars_`, z. B.:

- `llars_llarsdb` (MariaDB)
- `llars_rag_storage` / `llars_rag_docs` (RAG Daten)
- `llars_authentikdb` / `llars_authentik_media` (Authentik)
- `llars_matomo_data` / `llars_matomodb` (Analytics)
- `llars_redis_data` (Redis)

Andere Projekt-Volumes ohne `llars_`‑Präfix bleiben unberührt.

### 4. Dienste aufrufen

Nach ca. 30 Sekunden (bei gecachten Images):

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik | http://localhost:55095 |
| Docs (direkt) | http://localhost:55800 |
| Docs (via nginx, dev) | http://localhost:55080/mkdocs/ |

### 5. Installation prüfen

```bash
docker compose -p llars ps
```

Alle Services sollten `running` oder `healthy` sein.

## Entwicklungsmodus

Standardmäßig aktiv (`PROJECT_STATE=development`):

- Hot-Reload für Frontend (Vite) via Docker Watch
- Backend mit gemountetem Code (`./app:/app`)
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

## Komplett-Neustart

Für einen sauberen Neustart mit Löschung aller Daten:

```bash
REMOVE_LLARS_VOLUMES=True ./start_llars.sh --build
```

Für eine komplette System-Bereinigung (Images, Volumes, Build-Cache):

```bash
PRUNE_LLARS_SYSTEM=True ./start_llars.sh --build
```

## Troubleshooting

### Service startet nicht

```bash
docker compose -p llars logs backend-flask-service --tail=50
docker compose -p llars logs frontend-vue-service --tail=50
```

### Portkonflikte

Ports in `.env` anpassen, z. B.:

```bash
NGINX_EXTERNAL_PORT=56080
AUTHENTIK_EXTERNAL_PORT=56095
```

### Datenbank-Probleme

**Löscht Daten:**

```bash
REMOVE_LLARS_VOLUMES=True ./start_llars.sh --build
```

### Docker läuft nicht

- macOS: `open /Applications/Docker.app`
- Linux: `sudo systemctl start docker`

## Nächste Schritte

- [Konfiguration](configuration.md)
- [Docker-Architektur & Build-Caching](../entwickler/docker-architektur.md)
- [Projektstatus umschalten](../guides/project-state.md)
- [Berechtigungssystem](../guides/permission-system.md)
