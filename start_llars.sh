#!/bin/bash
# ============================================
# LLARS Startup Script
# ============================================
# Intelligenter Start für Development oder Production basierend auf:
# 1. Kommandozeilenargument (dev/prod)
# 2. PROJECT_STATE in .env
# 3. .env.development/.env.production Template

set -e

# Bestimmen Sie das Verzeichnis, in dem sich das Skript befindet
SCRIPT_DIR=$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]:-${(%):-%x}}")")" && pwd)
BASE_DIR="$SCRIPT_DIR"

echo "============================================"
echo "LLARS Startup Script"
echo "============================================"
echo "Basisverzeichnis: $BASE_DIR"

# ============================================
# Schritt 1: Projekt-State ermitteln
# ============================================

# Default: development
PROJECT_STATE_ARG="${1:-}"

# Prüfe Kommandozeilenargument
if [ "$PROJECT_STATE_ARG" = "prod" ] || [ "$PROJECT_STATE_ARG" = "production" ]; then
    PROJECT_STATE="production"
    ENV_FILE="$BASE_DIR/.env.production"
    echo "Mode: PRODUCTION (via command line argument)"
elif [ "$PROJECT_STATE_ARG" = "dev" ] || [ "$PROJECT_STATE_ARG" = "development" ]; then
    PROJECT_STATE="development"
    ENV_FILE="$BASE_DIR/.env.development"
    echo "Mode: DEVELOPMENT (via command line argument)"
elif [ -f "$BASE_DIR/.env" ]; then
    # Lese PROJECT_STATE aus .env
    source "$BASE_DIR/.env"
    if [ "$PROJECT_STATE" = "production" ]; then
        ENV_FILE="$BASE_DIR/.env.production"
        echo "Mode: PRODUCTION (via .env)"
    else
        PROJECT_STATE="development"
        ENV_FILE="$BASE_DIR/.env.development"
        echo "Mode: DEVELOPMENT (via .env)"
    fi
else
    # Fallback: Development
    PROJECT_STATE="development"
    ENV_FILE="$BASE_DIR/.env.development"
    echo "Mode: DEVELOPMENT (fallback - no .env found)"
fi

# ============================================
# Schritt 2: Environment-Datei laden
# ============================================

if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from: $ENV_FILE"
    source "$ENV_FILE"
else
    echo "ERROR: Environment file not found: $ENV_FILE"
    echo ""
    echo "Please create one of:"
    echo "  - .env.development (for development)"
    echo "  - .env.production (for production)"
    echo ""
    echo "Templates are provided in the repository."
    exit 1
fi

# Exportiere PROJECT_STATE explizit
export PROJECT_STATE

# Anzahl der Versuche und Wartezeit in Sekunden zwischen den Versuchen
MAX_ATTEMPTS=10
SLEEP_DURATION=5

# Funktion zum Überprüfen des Betriebssystems und Ausgabe
get_os_type() {
    OS_TYPE=$(uname)
    case "$OS_TYPE" in
        Darwin)
            echo "Erkanntes Betriebssystem: MacOS"
            ;;
        Linux)
            echo "Erkanntes Betriebssystem: Linux"
            ;;
        *_NT-*)
            echo "Erkanntes Betriebssystem: Windows"
            ;;
        *)
            echo "Nicht unterstütztes Betriebssystem: $OS_TYPE"
            exit 1
            ;;
    esac
}

# Funktion zum Überprüfen, ob der Docker-Daemon läuft und ggf. starten
check_and_start_docker() {
    get_os_type
    if ! docker info >/dev/null 2>&1; then
        echo "Docker-Daemon läuft nicht. Versuche zu starten..."

        OS_TYPE=$(uname)
        case "$OS_TYPE" in
            Darwin)
                open /Applications/Docker.app
                ;;
            Linux)
                sudo systemctl start docker
                ;;
            *_NT-*)
                echo "Docker läuft nicht. Bitte Docker manuell starten!"
                exit 1
                ;;
            *)
                echo "Nicht unterstütztes Betriebssystem: $OS_TYPE"
                exit 1
                ;;
        esac

        for ((i=1; i<=MAX_ATTEMPTS; i++)); do
            sleep $SLEEP_DURATION
            if docker info >/dev/null 2>&1; then
                echo "Docker-Daemon erfolgreich gestartet."
                return 0
            fi
        done

        echo "Fehler beim Starten des Docker-Daemons. Bitte manuell überprüfen."
        exit 1
    else
        echo "Docker-Daemon läuft bereits."
    fi
}

# Überprüfen, ob der Docker-Daemon läuft und ggf. starten
check_and_start_docker

# Dienste herunterfahren (NUR LLARS Container stoppen und löschen)
cd "$BASE_DIR"
echo "Stoppe und entferne LLARS-Dienste..."
docker compose -p llars down

if [ "$REMOVE_VOLUMES" = "True" ]; then
  echo "Entferne NUR LLARS-Volumes..."
  # Explizit nur LLARS-Volumes löschen, um andere Projekte nicht zu beeinflussen
  LLARS_VOLUMES=("llars_llarsdb" "llars_keycloakdb" "llars_model_volume")

  for volume in "${LLARS_VOLUMES[@]}"; do
    if docker volume inspect "$volume" >/dev/null 2>&1; then
      echo "Lösche Volume: $volume"
      docker volume rm "$volume" || echo "Warnung: Konnte $volume nicht löschen (möglicherweise noch in Benutzung)"
    else
      echo "Volume $volume existiert nicht, überspringe."
    fi
  done

  echo "LLARS-Volumes entfernt."
fi

# ============================================
# Schritt 5: Docker Compose starten
# ============================================

cd "$BASE_DIR"

if [ "$PROJECT_STATE" = "production" ]; then
    echo ""
    echo "============================================"
    echo "Starting LLARS in PRODUCTION MODE"
    echo "============================================"
    echo "Using: docker-compose.yml + docker-compose.prod.yml"
    echo ""

    # Production: Use production override
    docker compose \
        -f docker-compose.yml \
        -f docker-compose.prod.yml \
        -p llars \
        up --build --detach

    echo ""
    echo "✓ LLARS started in PRODUCTION mode"
    echo ""
    echo "Access points:"
    echo "  - Frontend: https://${PROJECT_HOST}"
    echo "  - Backend API: https://${PROJECT_HOST}/api"
    echo "  - Keycloak: https://${PROJECT_HOST}/auth"
    echo ""
    echo "View logs: docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
    echo "============================================"

else
    echo ""
    echo "============================================"
    echo "Starting LLARS in DEVELOPMENT MODE"
    echo "============================================"
    echo "Using: docker-compose.yml (with --watch)"
    echo ""

    # Development: Use watch mode for hot-reload
    docker compose \
        -f docker-compose.yml \
        -p llars \
        up --build --watch

    echo ""
    echo "✓ LLARS started in DEVELOPMENT mode"
    echo ""
    echo "Access points:"
    echo "  - Frontend: http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}"
    echo "  - Backend API: http://${PROJECT_HOST}:${NGINX_EXTERNAL_PORT}/api"
    echo "  - Keycloak: http://${PROJECT_HOST}:${KEYCLOAK_EXTERNAL_PORT}"
    echo ""
    echo "============================================"
fi
