#!/bin/bash

# Bestimmen Sie das Verzeichnis, in dem sich das Skript befindet
SCRIPT_DIR=$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]:-${(%):-%x}}")")" && pwd)
echo "Skriptverzeichnis: $SCRIPT_DIR"

# Überprüfen, ob das Skript im richtigen Verzeichnis liegt oder angepasst werden muss
if [[ "$SCRIPT_DIR" == */llars ]]; then
    SCRIPT_DIR="$SCRIPT_DIR/scripts"
    echo "Warnung: SCRIPT_DIR wurde auf '$SCRIPT_DIR' angepasst."
elif [[ "$SCRIPT_DIR" != */llars/scripts ]]; then
    echo "Das Skript muss im Verzeichnis 'llars/scripts' liegen."
    exit 1
fi

# Basisverzeichnis ermitteln (alles vor /llars/scripts)
BASE_DIR=$(dirname "$SCRIPT_DIR")
echo "Basisverzeichnis: $BASE_DIR"

# Überprüfen, ob das Basisverzeichnis mit 'llars' endet
if [[ "$BASE_DIR" != */llars ]]; then
    echo "Das Basisverzeichnis muss 'llars' sein."
    exit 1
fi

# Überprüfen, ob die .env-Datei vorhanden ist
if [ ! -f "$BASE_DIR/.env" ]; then
    echo "Fehler: Die .env-Datei wurde nicht gefunden."
    exit 1
fi

# Lade Umgebungsvariablen
source "$BASE_DIR/.env"

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

        # Überprüfen, auf welchem Betriebssystem das Skript läuft
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

# Dienste herunterfahren
echo "Stopping services..."
if [ "$REMOVE_VOLUMES" = "True" ]; then
  echo "Removing volumes..."
  docker compose -p llars down --volumes --remove-orphans
  echo "Successfully removed volumes."
  echo "Services stopped."
else
  docker compose -p llars down --remove-orphans
  echo "Services stopped."
fi

# Überprüfe den Projektzustand und starte die entsprechenden Dienste
if [ "$PROJECT_STATE" = "production" ]; then
    docker compose -f "$BASE_DIR/docker-compose.yml" -p llars --profile backend --profile frontend up --build --detach
    echo "LLARS Backend und Frontend im Produktionsmodus gestartet."
else
    docker compose -f "$BASE_DIR/docker-compose.yml" -p llars --profile backend --profile frontend up --build --watch
    echo "LLARS Backend und Frontend im Entwicklungsmodus gestartet."
fi
