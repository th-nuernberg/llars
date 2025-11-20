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
echo "============================================"
echo "SICHERHEITSCHECK: Zeige betroffene Container"
echo "============================================"
cd "$BASE_DIR"
echo "Folgende LLARS Container werden gestoppt und entfernt:"
docker compose -p llars ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || echo "  Keine LLARS Container laufen aktuell."
echo ""
echo "Andere laufende Container (bleiben unberührt):"
docker ps --format "table {{.Names}}\t{{.Image}}" | grep -v "^llars" | head -6 || echo "  Keine anderen Container."
echo "============================================"
echo ""
read -p "Fortfahren? Die obigen LLARS Container werden gestoppt. (j/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi
echo ""
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

# Überprüfe den Projektzustand und starte die entsprechenden Dienste
if [ "$PROJECT_STATE" = "production" ]; then
    docker compose -f "$BASE_DIR/docker-compose.yml" -p llars --profile backend --profile frontend up --build --detach
    echo "LLARS Backend und Frontend im Produktionsmodus gestartet."
else
    docker compose -f "$BASE_DIR/docker-compose.yml" -p llars --profile backend --profile frontend up --build --watch
    echo "LLARS Backend und Frontend im Entwicklungsmodus gestartet."
fi
